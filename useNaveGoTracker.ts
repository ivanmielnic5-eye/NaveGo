import { useEffect, useRef, useState } from 'react';
import * as Location from 'expo-location';
import { AppState } from 'react-native';
import * as SQLite from 'expo-sqlite';
import * as FileSystem from 'expo-file-system/legacy';
import { StorageAccessFramework } from 'expo-file-system/legacy';
import { startSession, endSession, insertGpsFix, getSessionFixes, openGap, closeGap, abandonGap, findOrCreateTestSession, getProcessedPointsSince, saveIsPaused, getActiveSession, getProcessedRoutePoints } from './db/journal';
import { initDatabase } from './db/schema';
import { REPLAY_ENABLED, BACKGROUND_TEST_ENABLED, TASK_PRODUCER_ENABLED } from './devConfig';
import { realLocationProvider } from './LocationProvider';
import { replayLocationProvider } from './ReplayLocationProvider';
import type { GPSFix } from './types/journal';
import { processFix } from './tracker/processFix';
import { BACKGROUND_LOCATION_TASK, BACKGROUND_TEST_FILE } from './tasks/backgroundLocationTask';
import type { ProcessInput, ProcessState, ProcessResult } from './tracker/types';

const PC_BRIDGE_URL = 'http://192.168.100.106:8084/update-trajectory';
const SYNC_INTERVAL_MS = 10000;
const GNSS_WATCHDOG_INTERVAL_MS = 1000;

const MAX_JUMP_DISTANCE_M = 15;
const MAX_ACCURACY_M = 20;
const MIN_DISTANCE_DELTA_M = 0.8;
const MIN_SPEED_FOR_COG_UPDATE = 0.3;
const GNSS_DEGRADED_AFTER_MS = 2000;
const GNSS_RECOVERING_AFTER_MS = 5000;
const GNSS_LOST_AFTER_MS = 10000;

export interface Coordinate {
  lat: number;
  lon: number;
  sog?: number;
  cog?: number;
  timestamp?: number;
}

export interface HazardZone {
  id: string;
  name: string;
  lat: number;
  lon: number;
  radiusMeters: number;
  source?: string;
  lastReportedAt?: number;
}

export interface ActiveHazard extends HazardZone {
  distance: number;
  confidence: 'CONFIRMADO' | 'ULTIMA_INFORMACION' | 'NO_DISPONIBLE';
  ageSeconds?: number;
}

export type NavigationStatus =
| 'CONFIABLE'
| 'DEGRADADO'
| 'NO_CONFIABLE'
| 'NO_DISPONIBLE'
| 'GNSS_PERDIDO'
| 'RECUPERANDO';

export type SyncState = 'SIN_INTENTAR' | 'SINCRONIZADO' | 'NO_DISPONIBLE' | 'ERROR';

const DEFAULT_HAZARD_ZONES: HazardZone[] = [
  {
    id: 'h1',
    name: 'Banco de arena simulado',
    lat: -31.634,
    lon: -60.6995,
    radiusMeters: 50,
    source: 'LOCAL_DEMO',
  },
{
  id: 'h2',
  name: 'Tronco flotante simulado',
  lat: -31.6335,
  lon: -60.7005,
  radiusMeters: 30,
  source: 'LOCAL_DEMO',
},
];

export function useNaveGoTracker() {
  // === Estados de telemetría (siempre vivos) ===
  const [currentSog, setCurrentSog] = useState(0);
  const [currentCog, setCurrentCog] = useState(0);
  const [lastFixTimestamp, setLastFixTimestamp] = useState<number | null>(null);
  const [lastFixAccuracy, setLastFixAccuracy] = useState<number | null>(null);
  const [navigationStatus, setNavigationStatus] = useState<NavigationStatus>('NO_DISPONIBLE');
  const [activeHazards, setActiveHazards] = useState<ActiveHazard[]>([]);
  const [isTelemetryActive, setIsTelemetryActive] = useState(false);
  const [livePosition, setLivePosition] = useState<{ lat: number; lon: number } | null>(null);

  // === Estados de grabación (controlados por botones) ===
  const [isRecording, setIsRecording] = useState(false);
  const [isTracking, setIsTracking] = useState(false); // alias por compat con App.tsx
  const [isPaused, setIsPaused] = useState(false);
  const [routePoints, setRoutePoints] = useState<Coordinate[]>([]);
  const [totalDistance, setTotalDistance] = useState(0);
  const [gapCount, setGapCount] = useState(0);
  const [gapTotalDurationMs, setGapTotalDurationMs] = useState(0);
  const [gapActive, setGapActive] = useState(false);
  const [gapMarkers, setGapMarkers] = useState<Array<{startLat:number;startLon:number;endLat:number;endLon:number;durationMs:number}>>([]);

  // === Estados de sync (con PC) ===
  const [syncOk, setSyncOk] = useState<boolean | null>(null);
  const [syncState, setSyncState] = useState<SyncState>('SIN_INTENTAR');

  // === Refs ===
  const isPausedRef = useRef(false);
  const isRecordingRef = useRef(false);
  const subscriptionRef = useRef<Location.LocationSubscription | null>(null);
  const lastPointRef = useRef<Coordinate | null>(null);
  const routePointsRef = useRef<Coordinate[]>([]);
  const syncTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const watchdogTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const dbRef = useRef<SQLite.SQLiteDatabase | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const testSessionIdRef = useRef<string | null>(null);
  const lastProcessedCursorRef = useRef<number>(-1);
  const sequenceNoRef = useRef(0);
  const totalDistanceRef = useRef(0);
  const lastCogRef = useRef(0);
  const lastFixTimestampRef = useRef<number | null>(null);
  const lastFixAccuracyRef = useRef<number | null>(null);
  const lastFixIdRef = useRef<string | null>(null);
  const lastSogRef = useRef<number>(0);
  const openGapIdRef = useRef<string | null>(null);
  const lastDistanceLogRef = useRef<number>(0);
  const fieldTestLogRef = useRef<string[]>([]);
  const safDirUriRef = useRef<string | null>(null);
  const gapStartAtMsRef = useRef<number | null>(null);
  const gapStartPosRef = useRef<{lat:number;lon:number} | null>(null);

  // === Helpers ===
  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    const R = 6371e3;
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * (Math.PI / 180)) *
    Math.cos(lat2 * (Math.PI / 180)) *
    Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  };

  const calculateHeading = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const y = Math.sin(dLon) * Math.cos(lat2 * (Math.PI / 180));
    const x =
    Math.cos(lat1 * (Math.PI / 180)) * Math.sin(lat2 * (Math.PI / 180)) -
    Math.sin(lat1 * (Math.PI / 180)) *
    Math.cos(lat2 * (Math.PI / 180)) *
    Math.cos(dLon);
    return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
  };

  const updateNavigationStatus = (timestamp: number | null, accuracy?: number) => {
    let nextStatus: NavigationStatus;
    let reason: string;
    if (!timestamp) {
      nextStatus = 'NO_DISPONIBLE';
      reason = 'sin timestamp';
    } else {
      const ageMs = Math.max(0, Date.now() - timestamp);
      if (ageMs > GNSS_LOST_AFTER_MS) {
        nextStatus = 'GNSS_PERDIDO';
        reason = 'age=' + ageMs + 'ms';
      } else if (ageMs > GNSS_RECOVERING_AFTER_MS) {
        nextStatus = 'RECUPERANDO';
        reason = 'age=' + ageMs + 'ms';
      } else if (accuracy !== undefined && accuracy > MAX_ACCURACY_M) {
        nextStatus = 'DEGRADADO';
        reason = 'acc=' + accuracy;
      } else if (ageMs > GNSS_DEGRADED_AFTER_MS) {
        nextStatus = 'RECUPERANDO';
        reason = 'age=' + ageMs + 'ms';
      } else if (accuracy !== undefined && accuracy > 10) {
        nextStatus = 'DEGRADADO';
        reason = 'acc=' + accuracy;
      } else {
        nextStatus = 'CONFIABLE';
        reason = 'age=' + ageMs + 'ms';
      }
    }
    console.log('[STATE] t=' + Date.now() + ' -> ' + nextStatus + ' (' + reason + ')');
    setNavigationStatus(nextStatus);
  };

  const evaluateHazards = (lat: number, lon: number): ActiveHazard[] => {
    const now = Date.now();
    return DEFAULT_HAZARD_ZONES
    .map((hazard) => {
      const distance = calculateDistance(lat, lon, hazard.lat, hazard.lon);
      const ageSeconds = hazard.lastReportedAt
      ? Math.max(0, Math.floor((now - hazard.lastReportedAt) / 1000))
      : undefined;
      const confidence: ActiveHazard['confidence'] = hazard.lastReportedAt
      ? 'CONFIRMADO'
      : 'ULTIMA_INFORMACION';
      return { ...hazard, distance, ageSeconds, confidence };
    })
    .filter((hazard) => hazard.distance <= hazard.radiusMeters);
  };

  const persistRawFix = async (
    location: Location.LocationObject,
    quality: GPSFix['quality'],
    sessionId: string,
    explicitId?: string,
  ) => {
    if (!dbRef.current) return;
    const fix: GPSFix = {
      id: explicitId ?? `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
      session_id: sessionId,
      sequence_no: sequenceNoRef.current++,
      timestamp: location.timestamp || Date.now(),
      lat_raw: location.coords.latitude,
      lon_raw: location.coords.longitude,
      alt: location.coords.altitude ?? null,
      accuracy: location.coords.accuracy ?? null,
      speed: location.coords.speed ?? null,
      heading: location.coords.heading ?? null,
      quality,
      satellites: 0,
      received_at_ms: Date.now(),
      source: REPLAY_ENABLED ? 'REPLAY' : 'GNSS',
    };
    // LOG TEMPORAL para verificar Problem 3 (source + received_at_ms)
    console.log('[FIX-SRC] source=' + fix.source + ' recv_at=' + fix.received_at_ms + ' id=' + fix.id);
    console.log('[FIX-CAMP] dt_calc lat=' + fix.lat_raw.toFixed(6) + ' lon=' + fix.lon_raw.toFixed(6) + ' acc=' + fix.accuracy + ' spd=' + fix.speed + ' head=' + fix.heading + ' t=' + fix.timestamp);
    try {
      await insertGpsFix(dbRef.current, fix);
    } catch (error) {
      console.warn('[DB] Error al guardar fix:', error);
    }
  };

  const syncTrajectoryToPC = async (points: Coordinate[]) => {
    if (REPLAY_ENABLED) return;
    if (!points.length) return;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      const response = await fetch(PC_BRIDGE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(points),
                                   signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!response.ok) throw new Error(`PC bridge HTTP ${response.status}`);
      setSyncOk(true);
      setSyncState('SINCRONIZADO');
    } catch {
      setSyncOk(false);
      setSyncState('NO_DISPONIBLE');
    }
  };

  const scheduleSync = () => {
    if (syncTimerRef.current) clearTimeout(syncTimerRef.current);
    syncTimerRef.current = setTimeout(() => {
      if (isRecordingRef.current && routePointsRef.current.length > 0 && !isPausedRef.current) {
        void syncTrajectoryToPC(routePointsRef.current);
      }
      scheduleSync();
    }, SYNC_INTERVAL_MS);
  };

  const startWatchdog = () => {
    if (watchdogTimerRef.current) clearInterval(watchdogTimerRef.current);
    watchdogTimerRef.current = setInterval(() => {
      updateNavigationStatus(lastFixTimestampRef.current, lastFixAccuracyRef.current ?? undefined);

      // Abrir gap si: hay sesion activa, no pausada, no hay gap ya abierto,
      // y el ultimo fix tiene mas de GNSS_DEGRADED_AFTER_MS de antiguedad.
      if (
        !openGapIdRef.current &&
        isRecordingRef.current &&
        !isPausedRef.current &&
        sessionIdRef.current &&
        dbRef.current &&
        lastFixIdRef.current &&
        lastFixTimestampRef.current &&
        Date.now() - lastFixTimestampRef.current > GNSS_DEGRADED_AFTER_MS
      ) {
        const gapStartAt = lastFixTimestampRef.current;
        gapStartAtMsRef.current = gapStartAt;
        if (lastPointRef.current) {
          gapStartPosRef.current = { lat: lastPointRef.current.lat, lon: lastPointRef.current.lon };
        }
        const fixIdAtGapStart = lastFixIdRef.current;
        const sessionIdAtGapStart = sessionIdRef.current;
        const sogAtGapStart = lastSogRef.current;
        const cogAtGapStart = lastCogRef.current;
        const accAtGapStart = lastFixAccuracyRef.current;
        console.log('[GAP] abriendo gap desde fix ' + fixIdAtGapStart);
        void openGap(
          dbRef.current,
          sessionIdAtGapStart,
          fixIdAtGapStart,
          sogAtGapStart,
          cogAtGapStart,
          accAtGapStart,
          'GNSS_TIMEOUT',
          gapStartAt,
        ).then((gapId) => {
          openGapIdRef.current = gapId;
          setGapActive(true);
          console.log('[GAP] abierto id=' + gapId);
        }).catch((e) => {
          console.warn('[GAP] error abriendo:', String(e));
        });
      }
    }, GNSS_WATCHDOG_INTERVAL_MS);
  };

  // === Helpers de efectos (Fase 0 del plan de background) ===

  const publishUiResult = (result: ProcessResult, location: Location.LocationObject) => {
    const now = Date.now();
    const fixTimestamp = location.timestamp || now;
    const fixAccuracy = location.coords.accuracy ?? 999;

    lastFixTimestampRef.current = fixTimestamp;
    lastFixAccuracyRef.current = fixAccuracy;
    lastCogRef.current = result.nextState.lastCog;

    setLastFixTimestamp(fixTimestamp);
    setLastFixAccuracy(fixAccuracy);
    updateNavigationStatus(fixTimestamp, fixAccuracy);
    setActiveHazards(evaluateHazards(result.livePosition.lat, result.livePosition.lon));
    setLivePosition(result.livePosition);
    setCurrentSog(result.liveSog);
    setCurrentCog(result.liveCog);

    if (result.newPoint) {
      lastPointRef.current = {
        lat: result.newPoint.lat,
        lon: result.newPoint.lon,
        sog: result.newPoint.sog,
        cog: result.newPoint.cog,
        timestamp: result.newPoint.timestamp,
      };
      routePointsRef.current = [...routePointsRef.current, lastPointRef.current];
      totalDistanceRef.current += result.distanceDelta;
      setRoutePoints(routePointsRef.current);
      setTotalDistance(totalDistanceRef.current);
    }

    const nowLog = Date.now();
    if (nowLog - lastDistanceLogRef.current >= 10000) {
      lastDistanceLogRef.current = nowLog;
      console.log('[DIST] t=' + nowLog + ' total=' + totalDistanceRef.current.toFixed(2) + 'm puntos=' + routePointsRef.current.length);
    }
  };

  const persistFixResult = async (result: ProcessResult, location: Location.LocationObject) => {
    if (!result.persist) return;
    if (!sessionIdRef.current) return;
    if (!dbRef.current) return;

    const fixId = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    lastFixIdRef.current = fixId;
    lastSogRef.current = result.liveSog;

    fieldTestLogRef.current.push(JSON.stringify({
      measuredAt: location.timestamp || Date.now(),
      receivedAt: Date.now(),
      lat: location.coords.latitude,
      lon: location.coords.longitude,
      accuracy: location.coords.accuracy,
      speed: location.coords.speed,
      heading: location.coords.heading,
    }));

    await persistRawFix(location, result.quality, sessionIdRef.current, fixId);

    if (result.gapAction === 'CLOSE' && openGapIdRef.current && dbRef.current) {
      const gapId = openGapIdRef.current;
      const nowMs = location.timestamp || Date.now();
      const realGapDurMs = nowMs - (gapStartAtMsRef.current ?? nowMs);
      try {
        await closeGap(dbRef.current, gapId, fixId, nowMs);
        console.log('[GAP] cerrado id=' + gapId + ' duracion=' + realGapDurMs + 'ms');
        setGapCount((prev) => prev + 1);
        setGapTotalDurationMs((prev) => prev + realGapDurMs);
        setGapActive(false);
        if (gapStartPosRef.current) {
          const startPos = gapStartPosRef.current;
          setGapMarkers((prev) => [...prev, {
            startLat: startPos.lat,
            startLon: startPos.lon,
            endLat: location.coords.latitude,
            endLon: location.coords.longitude,
            durationMs: realGapDurMs,
          }]);
          gapStartPosRef.current = null;
        }
        gapStartAtMsRef.current = null;
        openGapIdRef.current = null;
      } catch (e) {
        console.warn('[GAP] error cerrando:', String(e));
      }
    }

    if (result.rejectForNavigation === 'ACCURACY') {
      console.log('[FILTER] t=' + Date.now() + ' acc=' + location.coords.accuracy + ' > ' + MAX_ACCURACY_M);
    }
    if (result.isGapRestart) {
      console.log('[FILTER] t=' + Date.now() + ' jump=' + result.rawDistanceDelta.toFixed(2) + 'm > ' + MAX_JUMP_DISTANCE_M + 'm');
    }
  };

  // =========================================================================
  // FASE 2 DOC 46 — Task de background en modo observador.
  // Escribe a JSONL, no toca SQLite. Solo activa con flag explicito.
  // watchPositionAsync sigue activo en paralelo.
  // =========================================================================
  useEffect(() => {
    if (!BACKGROUND_TEST_ENABLED && !TASK_PRODUCER_ENABLED) return;
    if (REPLAY_ENABLED) return;

    const startBgTask = async () => {
      try {
        const hasStarted = await Location.hasStartedLocationUpdatesAsync(
          BACKGROUND_LOCATION_TASK,
        );
        if (hasStarted) {
          console.log('[TRACKER] Task background ya estaba activa');
          return;
        }

        await Location.requestBackgroundPermissionsAsync();

        await Location.startLocationUpdatesAsync(BACKGROUND_LOCATION_TASK, {
          accuracy: Location.Accuracy.High,
          timeInterval: 1000,
          distanceInterval: 0,
          foregroundService: {
            notificationTitle: 'NaveGo grabando',
            notificationBody: 'Capturando ubicacion en segundo plano',
            notificationColor: '#0af',
          },
        });

        console.log('[TRACKER] Task background iniciada');
      } catch (e) {
        console.warn('[TRACKER] Error iniciando task background:', String(e));
      }
    };

    startBgTask();
  }, []);

  // =========================================================================
  // FASE 6 DOC 46: recuperacion de sesion ACTIVE al abrir la app.
  // Solo activo con TASK_PRODUCER_ENABLED (sin REPLAY).
  // Si hay sesion ACTIVE, la retoma: carga refs y routePoints
  // desde SQLite. El HUD muestra el trayecto previo.
  // =========================================================================
  useEffect(() => {
    if (!TASK_PRODUCER_ENABLED) return;
    if (REPLAY_ENABLED) return;

    let mounted = true;

    const recoverSession = async () => {
      try {
        if (!dbRef.current) {
          dbRef.current = await SQLite.openDatabaseAsync('navego.db');
          await initDatabase(dbRef.current);
        }
        const active = await getActiveSession(dbRef.current);
        if (!mounted || !active) {
          console.log('[TRACKER] sin sesion ACTIVE para recuperar');
          return;
        }

        const puntos = await getProcessedRoutePoints(dbRef.current, active.id);
        if (!mounted) return;

        sessionIdRef.current = active.id;
        totalDistanceRef.current = active.total_distance ?? 0;
        routePointsRef.current = puntos.map(p => ({ lat: p.lat, lon: p.lon }));
        lastProcessedCursorRef.current = active.last_processed_seq ?? -1;
        isRecordingRef.current = true;

        setRoutePoints(routePointsRef.current);
        setTotalDistance(totalDistanceRef.current);
        setIsRecording(true);
        setIsTracking(true);
        setIsPaused(false);
        isPausedRef.current = false;

        console.log('[TRACKER] Sesion retomada: ' + active.id +
          ' puntos=' + puntos.length +
          ' distancia=' + (active.total_distance ?? 0).toFixed(2) + 'm');
      } catch (e) {
        console.warn('[TRACKER] recoverSession fallo:', String(e));
      }
    };

    void recoverSession();
  }, []);

  // =========================================================================
  // FASE 4 DOC 46: CONSUMIDOR — polling de processed_points.
  // Solo activo con TASK_PRODUCER_ENABLED (sin REPLAY). El hook no
  // captura; lee lo que la Task escribio y actualiza el HUD.
  // =========================================================================
  useEffect(() => {
    if (!TASK_PRODUCER_ENABLED) return;
    if (REPLAY_ENABLED) return;

    let mounted = true;

    const pollInterval = setInterval(async () => {
      if (!mounted) return;
      if (!dbRef.current || !sessionIdRef.current) return;
      if (!isRecordingRef.current || isPausedRef.current) return;

      try {
        const rows = await getProcessedPointsSince(
          dbRef.current,
          sessionIdRef.current,
          lastProcessedCursorRef.current,
        );
        if (!mounted || rows.length === 0) return;

        let addedPoints: Coordinate[] = [];
        let addedDistance = 0;
        let lastRow = null;
        for (const r of rows) {
          lastRow = r;
          if (r.has_new_point === 1) {
            addedPoints.push({ lat: r.lat, lon: r.lon });
            addedDistance += r.distance_delta;
          }
        }
        if (!lastRow) return;

        lastProcessedCursorRef.current = lastRow.sequence_no;

        // Actualizar timestamp + accuracy + estado GNSS en cada ciclo.
        const acc = lastRow.accuracy ?? 999;
        lastFixTimestampRef.current = lastRow.timestamp;
        lastFixAccuracyRef.current = acc;
        updateNavigationStatus(lastRow.timestamp, acc);
        setLastFixTimestamp(lastRow.timestamp);
        setLastFixAccuracy(acc);

        if (addedPoints.length > 0) {
          routePointsRef.current = [...routePointsRef.current, ...addedPoints];
          totalDistanceRef.current += addedDistance;
          setRoutePoints(routePointsRef.current);
          setTotalDistance(totalDistanceRef.current);
          setLivePosition({ lat: lastRow.lat, lon: lastRow.lon });
          setCurrentSog(lastRow.sog);
          setCurrentCog(lastRow.cog);
        }
      } catch (e) {
        console.warn('[POLL] error:', String(e));
      }
    }, 1500);

    return () => {
      mounted = false;
      clearInterval(pollInterval);
    };
  }, []);

  // =========================================================================
  // TELEMETRÍA VIVA — arranca al montar, muere al desmontar.
  // NO depende de botones.
  // =========================================================================
  useEffect(() => {
    if (TASK_PRODUCER_ENABLED && !REPLAY_ENABLED) {
      console.log('[TRACKER] TASK_PRODUCER_ENABLED: watchPosition OFF');
      return;
    }

    let mounted = true;
    let localSubscription: { remove: () => void } | null = null;
    const locationProvider = REPLAY_ENABLED
      ? replayLocationProvider
      : realLocationProvider;

    const initTelemetry = async () => {
      try {
        const { status } = await locationProvider.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          console.error('[TRACKER] Permiso de ubicación denegado');
          return;
        }
        if (!mounted) return;

        setIsTelemetryActive(true);
        startWatchdog();

        localSubscription = await locationProvider.watchPositionAsync(
          {
            accuracy: Location.Accuracy.High,
            timeInterval: 1000,
            distanceInterval: 0,
          },
          (location) => {
            if (!mounted) return;

            console.log('[FIX] t=' + Date.now() + ' lat=' + location.coords.latitude.toFixed(6) + ' lon=' + location.coords.longitude.toFixed(6) + ' acc=' + location.coords.accuracy);

            const input: ProcessInput = {
              lat: location.coords.latitude,
              lon: location.coords.longitude,
              accuracy: location.coords.accuracy ?? 999,
              speed: location.coords.speed,
              heading: location.coords.heading,
              measuredAt: location.timestamp || Date.now(),
            };

            const currentState: ProcessState = {
              lastPoint: lastPointRef.current
                ? {
                    lat: lastPointRef.current.lat,
                    lon: lastPointRef.current.lon,
                    timestamp: lastPointRef.current.timestamp ?? 0,
                  }
                : null,
              lastCog: lastCogRef.current,
              isRecording: isRecordingRef.current,
              isPaused: isPausedRef.current,
              hasOpenGap: openGapIdRef.current !== null,
            };

            const result = processFix(input, currentState);

            publishUiResult(result, location);
            void persistFixResult(result, location);
          },
        );

        subscriptionRef.current = localSubscription;
      } catch (error) {
        console.warn('[TRACKER] Error al iniciar telemetría:', error);
      }
    };

    initTelemetry();
    scheduleSync();

    return () => {
      mounted = false;
      localSubscription?.remove();
      subscriptionRef.current = null;
      if (watchdogTimerRef.current) {
        clearInterval(watchdogTimerRef.current);
        watchdogTimerRef.current = null;
      }
      if (syncTimerRef.current) {
        clearTimeout(syncTimerRef.current);
        syncTimerRef.current = null;
      }
      if (dbRef.current && sessionIdRef.current) {
        void endSession(dbRef.current, sessionIdRef.current, totalDistanceRef.current).catch(() => {});
        sessionIdRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // =========================================================================
  // GRABACIÓN — abrir/cerrar sesión. NO toca la telemetría.
  // =========================================================================
  const startTracking = async () => {
    if (isRecordingRef.current) return;

    // Pedir carpeta SAF si no la tenemos (test de campo)
    if (!safDirUriRef.current) {
      try {
        const perm = await StorageAccessFramework.requestDirectoryPermissionsAsync();
        if (perm.granted) {
          safDirUriRef.current = perm.directoryUri;
          console.log('[FIELD-LOG] carpeta elegida: ' + perm.directoryUri);
        } else {
          console.log('[FIELD-LOG] permiso denegado');
        }
      } catch (e) {
        console.warn('[FIELD-LOG] error pidiendo carpeta:', String(e));
      }
    }

    try {
      if (!dbRef.current) {
        dbRef.current = await SQLite.openDatabaseAsync('navego.db');
        await initDatabase(dbRef.current);
      }
      // Cerrar sesiones huérfanas que quedaron ACTIVE de sesiones anteriores
      try {
        const orphans = await dbRef.current.getAllAsync<{ id: string; total_distance: number | null }>(
          "SELECT id, total_distance FROM sessions WHERE status = 'ACTIVE'"
        );
        for (const o of orphans) {
          await endSession(dbRef.current, o.id, o.total_distance ?? 0);
        }
        if (orphans.length > 0) {
          console.log('[TRACKER] Cerradas ' + orphans.length + ' sesiones huérfanas');
        }
      } catch (e) {
        console.warn('[TRACKER] Error cerrando huérfanas:', e);
      }
      // Fase 4: si bootstrap ya creo una sesion, reusarla.
      if (!sessionIdRef.current) {
        const sessionId = await startSession(dbRef.current, 'Sesión NaveGo');
        sessionIdRef.current = sessionId;
        console.log('[TRACKER] startTracking creo sesion:', sessionId);
      } else {
        console.log('[TRACKER] startTracking reusa sesion bootstrap:', sessionIdRef.current);
      }

      // Fase 3+4 DOC 46: sesion paralela para la Task de background.
      // Solo activa con el flag de test. Si no esta activa, se limpia.
      if (BACKGROUND_TEST_ENABLED) {
        const testSessionId = await findOrCreateTestSession(dbRef.current, 'TASK_TEST');
        testSessionIdRef.current = testSessionId;
        console.log('[TRACKER] sesion test para Task:', testSessionId);
      } else {
        testSessionIdRef.current = null;
      }
      sequenceNoRef.current = 0;
      totalDistanceRef.current = 0;
      routePointsRef.current = [];
      lastPointRef.current = null;
      setRoutePoints([]);
      setTotalDistance(0);
    } catch (error) {
      console.warn('[DB] Error al abrir/iniciar base local:', error);
    }

    isRecordingRef.current = true;
    setGapCount(0);
    setGapTotalDurationMs(0);
    setGapActive(false);
    setGapMarkers([]);
    gapStartPosRef.current = null;
    gapStartAtMsRef.current = null;
    setIsRecording(true);
    setIsTracking(true);
    setIsPaused(false);
    isPausedRef.current = false;
    setSyncState('SIN_INTENTAR');
  };

  const stopTracking = async () => {
    isRecordingRef.current = false;
    setIsRecording(false);
    setIsTracking(false);
    setIsPaused(false);
    isPausedRef.current = false;

    if (dbRef.current && sessionIdRef.current) {
      // FIX H-2026-0004: abandonar gap abierto antes de cerrar la sesion
      if (openGapIdRef.current) {
        try {
          await abandonGap(dbRef.current, openGapIdRef.current, Date.now());
          console.log('[FIX-H0004] gap abandonado:', openGapIdRef.current);
          openGapIdRef.current = null;
          setGapActive(false);
        } catch (e) {
          console.warn('[FIX-H0004] error abandonando gap:', String(e));
        }
      }

      // LOG FINAL de distancia (temporal para tests)
      const gapsOpen = openGapIdRef.current ? 1 : 0;
      console.log('[DIST-FINAL] total=' + totalDistanceRef.current.toFixed(2) + 'm puntos=' + routePointsRef.current.length + ' gap_abierto=' + gapsOpen);

      // FIELD LOG: escribir buffer via SAF (test de campo TCL)
      if (fieldTestLogRef.current.length > 0) {
        try {
          if (safDirUriRef.current) {
            const fileName = 'tcl_field_' + Date.now() + '.jsonl';
            const fileUri = await StorageAccessFramework.createFileAsync(
              safDirUriRef.current,
              fileName,
              'application/jsonl'
            );
            await FileSystem.writeAsStringAsync(fileUri, fieldTestLogRef.current.join('\n'));
            console.log('[FIELD-LOG] ' + fieldTestLogRef.current.length + ' fixes guardados en ' + fileName);
          } else {
            console.warn('[FIELD-LOG] no hay carpeta elegida, no se guardo el log');
          }
        } catch (e) {
          console.warn('[FIELD-LOG] error:', String(e));
        }
        fieldTestLogRef.current = [];
      }

      // FASE 2 DOC 46: copiar el archivo de la Task de background al SAF
      if (BACKGROUND_TEST_ENABLED && safDirUriRef.current) {
        try {
          const bgInfo = await FileSystem.getInfoAsync(BACKGROUND_TEST_FILE);
          if (bgInfo.exists) {
            const bgFileName = 'tcl_bgtask_' + Date.now() + '.jsonl';
            const bgFileUri = await StorageAccessFramework.createFileAsync(
              safDirUriRef.current,
              bgFileName,
              'application/jsonl'
            );
            const bgContent = await FileSystem.readAsStringAsync(BACKGROUND_TEST_FILE);
            await FileSystem.writeAsStringAsync(bgFileUri, bgContent);
            console.log('[BG-LOG] copiado al SAF: ' + bgFileName);
          } else {
            console.log('[BG-LOG] sin archivo de background task');
          }
        } catch (e) {
          console.warn('[BG-LOG] error copiando:', String(e));
        }
      }

      try {
        await endSession(dbRef.current, sessionIdRef.current, totalDistanceRef.current);
        console.log('[TRACKER] Sesion cerrada OK');
      } catch (e) {
        console.warn('[TRACKER] endSession fallo:', e);
      }

      sessionIdRef.current = null;
    }

    // Fase 4: la Task sigue corriendo (sin sesion activa, solo JSONL).
    // Al apretar INICIAR de nuevo, va a encontrar la nueva sesion.
  };

  const resetTracking = async () => {
    if (dbRef.current && sessionIdRef.current) {
      await endSession(dbRef.current, sessionIdRef.current, totalDistanceRef.current).catch(() => {});
      sessionIdRef.current = null;
    }

    setRoutePoints([]);
    routePointsRef.current = [];
    setTotalDistance(0);
    totalDistanceRef.current = 0;
    lastPointRef.current = null;
    sequenceNoRef.current = 0;

    if (isRecordingRef.current && dbRef.current) {
      try {
        const sessionId = await startSession(dbRef.current, 'Sesión NaveGo');
        sessionIdRef.current = sessionId;
      } catch (error) {
        console.warn('[DB] Error al reiniciar sesión:', error);
      }
    }
  };

  const togglePause = () => {
    setIsPaused((prev) => {
      const next = !prev;
      isPausedRef.current = next;
      // Fase 4: persistir is_paused para que la Task lo lea
      if (TASK_PRODUCER_ENABLED && dbRef.current && sessionIdRef.current) {
        void saveIsPaused(dbRef.current, sessionIdRef.current, next).catch(() => {});
      }
      return next;
    });
  };

  // FASE 1: al volver al primer plano, releer los puntos desde SQLite
  useEffect(() => {
    const sub = AppState.addEventListener('change', async (nextState) => {
      if (nextState !== 'active') return;
      if (!sessionIdRef.current) return;
      if (!dbRef.current) return;
      try {
        const fixes = await getSessionFixes(dbRef.current, sessionIdRef.current);
        const pts = fixes
          .map((f) => ({ lat: f.lat_raw, lon: f.lon_raw }))
          .filter((p) => Number.isFinite(p.lat) && Number.isFinite(p.lon));
        routePointsRef.current = pts;
        setRoutePoints(pts);
        if (pts.length > 0) {
          lastPointRef.current = pts[pts.length - 1];
        }
      } catch (e) {
        console.warn('[TRACKER] Error releyendo fixes:', e);
      }
    });
    return () => sub.remove();
  }, []);

  const nav = {
    distanceMeters: totalDistance,
    sog: currentSog,
    cog: currentCog,
    gpsStatus: navigationStatus,
  };

  const exportDatabaseToSAF = async (): Promise<void> => {
    if (!dbRef.current) {
      console.warn('[EXPORT] DB no abierta');
      return;
    }
    if (!safDirUriRef.current) {
      console.warn('[EXPORT] no hay carpeta SAF elegida');
      return;
    }
    try {
      // Checkpoint WAL to main db para que el archivo este completo
      await dbRef.current.execAsync('PRAGMA wal_checkpoint(TRUNCATE);');
      const dbPath = FileSystem.documentDirectory + 'SQLite/navego.db';
      const info = await FileSystem.getInfoAsync(dbPath);
      if (!info.exists) {
        console.warn('[EXPORT] archivo de DB no encontrado:', dbPath);
        return;
      }
      const base64 = await FileSystem.readAsStringAsync(dbPath, {
        encoding: FileSystem.EncodingType.Base64,
      });
      const fileName = `navego_export_${Date.now()}.db`;
      const fileUri = await StorageAccessFramework.createFileAsync(
        safDirUriRef.current,
        fileName,
        'application/octet-stream'
      );
      await FileSystem.writeAsStringAsync(fileUri, base64, {
        encoding: FileSystem.EncodingType.Base64,
      });
      console.log('[EXPORT] DB exportada:', fileName);
    } catch (e) {
      console.warn('[EXPORT] error:', String(e));
    }
  };

  return {
    nav,
    routePoints,
    totalDistance,
    gapCount,
    gapTotalDurationMs,
    gapActive,
    gapMarkers,
    currentSog,
    currentCog,
    isTracking,
    isRecording,
    isTelemetryActive,
    livePosition,
    isPaused,
    syncOk,
    syncState,
    activeHazards,
    lastFixTimestamp,
    lastFixAccuracy,
    navigationStatus,
    startTracking,
    stopTracking,
    exportDatabaseToSAF,
    togglePause,
    resetTracking,
    resetDistance: resetTracking,
  };
}
