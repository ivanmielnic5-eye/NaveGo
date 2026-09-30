/**
 * processFix — nucleo de dominio puro del tracker.
 *
 * Recibe un fix crudo + el estado anterior.
 * Devuelve un resultado determinista.
 *
 * NO toca: React, SQLite, timers, logs, red.
 * NO sabe como se va a dibujar el resultado.
 *
 * Fase 0 del plan de migracion a background location.
 */

import type {
  ProcessInput,
  ProcessResult,
  ProcessState,
  RejectReason,
  FixQuality,
  GapAction,
} from './types';

// --- Constantes (mismas que el tracker actual, sin cambios) ---
const MAX_JUMP_DISTANCE_M = 15;
const MIN_DISTANCE_DELTA_M = 0.8;
const MAX_ACCURACY_M = 20;
const MIN_SPEED_FOR_COG_UPDATE = 0.3;

// Umbral adaptativo de salto: a mayor velocidad, mas distancia
// entre fixes es normal. Antes era fijo en 15m, lo que descartaba
// los fixes de cualquier vehiculo rapido (auto a 80+ km/h).
const JUMP_FACTOR_SPEED = 2.0;
const JUMP_FACTOR_ACCURACY = 3.0;

const EARTH_RADIUS_M = 6371000;

function toRadians(deg: number): number {
  return (deg * Math.PI) / 180;
}

function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const rLat1 = toRadians(lat1);
  const rLat2 = toRadians(lat2);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(rLat1) * Math.cos(rLat2) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return EARTH_RADIUS_M * c;
}

function calculateHeading(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const rLat1 = toRadians(lat1);
  const rLat2 = toRadians(lat2);
  const dLon = toRadians(lon2 - lon1);

  const y = Math.sin(dLon) * Math.cos(rLat2);
  const x =
    Math.cos(rLat1) * Math.sin(rLat2) -
    Math.sin(rLat1) * Math.cos(rLat2) * Math.cos(dLon);

  const bearingRad = Math.atan2(y, x);
  return ((bearingRad * 180) / Math.PI + 360) % 360;
}

function classifyQuality(accuracy: number): FixQuality {
  if (accuracy <= 10) return 'GOOD';
  if (accuracy <= 50) return 'SUSPECT';
  return 'REJECTED';
}

/**
 * Procesa un fix y devuelve el resultado deterministico.
 */
export function processFix(
  input: ProcessInput,
  state: ProcessState,
): ProcessResult {
  const quality = classifyQuality(input.accuracy);

  // Telemetria viva derivada (siempre)
  const livePosition = { lat: input.lat, lon: input.lon };

  let liveSog = 0;
  if (
    input.speed !== null &&
    Number.isFinite(input.speed) &&
    input.speed >= 0
  ) {
    liveSog = input.speed;
  }

  let liveCog = state.lastCog;
  if (
    input.heading !== null &&
    Number.isFinite(input.heading) &&
    input.heading >= 0
  ) {
    liveCog = input.heading;
  }

  // Si no esta grabando o esta pausado: no se procesa nada mas.
  if (!state.isRecording || state.isPaused) {
    return {
      persist: false,
      quality,
      rejectForNavigation: null,
      isGapRestart: false,
      gapAction: 'NONE',
      distanceDelta: 0,
      rawDistanceDelta: 0,
      nextState: {
        ...state,
        lastCog: liveCog,
      },
      livePosition,
      liveSog,
      liveCog,
      newPoint: null,
    };
  }

  // --- Desde aca, se graba (BLOQUE 2) ---

  // Gap: si habia uno abierto, este fix lo cierra.
  const gapAction: GapAction = state.hasOpenGap ? 'CLOSE' : 'NONE';

  // Filtro por accuracy (para navegacion, no para persistencia).
  if (input.accuracy > MAX_ACCURACY_M) {
    return {
      persist: true,
      quality,
      rejectForNavigation: 'ACCURACY',
      isGapRestart: false,
      gapAction,
      distanceDelta: 0,
      rawDistanceDelta: 0,
      nextState: {
        ...state,
        lastCog: liveCog,
      },
      livePosition,
      liveSog,
      liveCog,
      newPoint: null,
    };
  }

  // Distancia al punto anterior.
  const rawDistanceDelta = state.lastPoint
    ? calculateDistance(
        state.lastPoint.lat,
        state.lastPoint.lon,
        input.lat,
        input.lon,
      )
    : 0;

  // Gap restart: umbral adaptativo segun velocidad y accuracy.
  // A mayor velocidad, mayor distancia entre fixes es normal.
  const dtSec = state.lastPoint
    ? Math.max((input.measuredAt - state.lastPoint.timestamp) / 1000, 1)
    : 1;
  const speedMs = input.speed ?? 0;
  const accuracyM = input.accuracy ?? 0;
  const adaptiveThreshold = Math.max(
    MAX_JUMP_DISTANCE_M,
    speedMs * dtSec * JUMP_FACTOR_SPEED + accuracyM * JUMP_FACTOR_ACCURACY,
  );

  let isGapRestart = false;
  let distanceIncrement = rawDistanceDelta;
  if (rawDistanceDelta > adaptiveThreshold) {
    isGapRestart = true;
    distanceIncrement = 0;
  }

  // Delta minimo: si el movimiento es muy chico, no se actualiza el track.
  if (
    !isGapRestart &&
    distanceIncrement < MIN_DISTANCE_DELTA_M &&
    state.lastPoint
  ) {
    return {
      persist: true,
      quality,
      rejectForNavigation: 'MIN_DELTA',
      isGapRestart,
      gapAction,
      distanceDelta: 0,
      rawDistanceDelta,
      nextState: {
        ...state,
        lastCog: liveCog,
      },
      livePosition,
      liveSog,
      liveCog,
      newPoint: null,
    };
  }

  // SOG calculado: si el GPS no reporta speed, derivar de distancia.
  let calculatedSog = liveSog;
  if (calculatedSog === 0 && state.lastPoint) {
    const timeDiffSecs = state.lastPoint.timestamp
      ? (input.measuredAt - state.lastPoint.timestamp) / 1000
      : 1;
    if (timeDiffSecs > 0 && distanceIncrement > 0) {
      calculatedSog = distanceIncrement / timeDiffSecs;
    }
  }

  // COG calculado: si el barco se mueve lo suficiente, recalcular rumbo.
  // Ademas, si vamos a agregar un newPoint (movimiento > MIN_DELTA),
  // calcular COG por geometria aunque el speed sea bajo (movimiento
  // real del track sin velocidad reportada por el GPS).
  let calculatedCog = liveCog;
  if (calculatedSog >= MIN_SPEED_FOR_COG_UPDATE && state.lastPoint) {
    calculatedCog = calculateHeading(
      state.lastPoint.lat,
      state.lastPoint.lon,
      input.lat,
      input.lon,
    );
  } else if (state.lastPoint && distanceIncrement >= MIN_DISTANCE_DELTA_M) {
    // Hay movimiento geometrico suficiente: rumbo por geometria.
    calculatedCog = calculateHeading(
      state.lastPoint.lat,
      state.lastPoint.lon,
      input.lat,
      input.lon,
    );
  }

  // Punto nuevo para el track.
  const newPoint = {
    lat: input.lat,
    lon: input.lon,
    sog: calculatedSog,
    cog: calculatedCog,
    timestamp: input.measuredAt,
  };

  return {
    persist: true,
    quality,
    rejectForNavigation: null,
    isGapRestart,
    gapAction,
    distanceDelta: distanceIncrement,
    rawDistanceDelta,
    nextState: {
      lastPoint: {
        lat: input.lat,
        lon: input.lon,
        timestamp: input.measuredAt,
      },
      lastCog: calculatedCog,
      isRecording: state.isRecording,
      isPaused: state.isPaused,
      hasOpenGap: false,
    },
    livePosition,
    liveSog,
    liveCog: calculatedCog,
    newPoint,
  };
}
