import { useEffect, useRef, useState } from 'react';
import * as Location from 'expo-location';
import * as SQLite from 'expo-sqlite';
import { startSession, endSession, insertGpsFix } from './db/journal';
import { initDatabase } from './db/schema';
import type { GPSFix } from './types/journal';

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

  // === Estados de grabación (controlados por botones) ===
  const [isRecording, setIsRecording] = useState(false);
  const [isTracking, setIsTracking] = useState(false); // alias por compat con App.tsx
  const [isPaused, setIsPaused] = useState(false);
  const [routePoints, setRoutePoints] = useState<Coordinate[]>([]);
  const [totalDistance, setTotalDistance] = useState(0);

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
  const sequenceNoRef = useRef(0);
  const totalDistanceRef = useRef(0);
  const lastCogRef = useRef(0);
  const lastFixTimestampRef = useRef<number | null>(null);
  const lastFixAccuracyRef = useRef<number | null>(null);

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
    if (!timestamp) {
      setNavigationStatus('NO_DISPONIBLE');
      return;
    }
    const ageMs = Math.max(0, Date.now() - timestamp);
    if (ageMs > GNSS_LOST_AFTER_MS) {
      setNavigationStatus('GNSS_PERDIDO');
    } else if (ageMs > GNSS_RECOVERING_AFTER_MS) {
      setNavigationStatus('RECUPERANDO');
    } else if (accuracy !== undefined && accuracy > MAX_ACCURACY_M) {
      setNavigationStatus('DEGRADADO');
    } else if (ageMs > GNSS_DEGRADED_AFTER_MS) {
      setNavigationStatus('RECUPERANDO');
    } else if (accuracy !== undefined && accuracy > 10) {
      setNavigationStatus('DEGRADADO');
    } else {
      setNavigationStatus('CONFIABLE');
    }
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
  ) => {
    if (!dbRef.current) return;
    const fix: GPSFix = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
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
    };
    try {
      await insertGpsFix(dbRef.current, fix);
    } catch (error) {
      console.warn('[DB] Error al guardar fix:', error);
    }
  };

  const syncTrajectoryToPC = async (points: Coordinate[]) => {
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
    }, GNSS_WATCHDOG_INTERVAL_MS);
  };

  // =========================================================================
  // TELEMETRÍA VIVA — arranca al montar, muere al desmontar.
  // NO depende de botones.
  // =========================================================================
  useEffect(() => {
    let mounted = true;
    let localSubscription: Location.LocationSubscription | null = null;

    const initTelemetry = async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          console.error('[TRACKER] Permiso de ubicación denegado');
          return;
        }
        if (!mounted) return;

        setIsTelemetryActive(true);
        startWatchdog();

        localSubscription = await Location.watchPositionAsync(
          {
            accuracy: Location.Accuracy.High,
            timeInterval: 1000,
            distanceInterval: 0,
          },
          (location) => {
            if (!mounted) return;

            const currentTimestamp = location.timestamp || Date.now();
            const accuracy = location.coords.accuracy ?? 999;
            const gpsSpeed = location.coords.speed;
            const gpsHeading = location.coords.heading;

            // === BLOQUE 1: TELEMETRÍA VIVA (siempre) ===
            lastFixTimestampRef.current = currentTimestamp;
            lastFixAccuracyRef.current = accuracy;
            setLastFixTimestamp(currentTimestamp);
            setLastFixAccuracy(accuracy);
            updateNavigationStatus(currentTimestamp, accuracy);
            setActiveHazards(evaluateHazards(location.coords.latitude, location.coords.longitude));

            let liveSog = 0;
            if (gpsSpeed !== null && gpsSpeed !== undefined && Number.isFinite(gpsSpeed) && gpsSpeed >= 0) {
              liveSog = gpsSpeed;
            }
            setCurrentSog(liveSog);

            let liveCog = lastCogRef.current;
            if (gpsHeading !== null && gpsHeading !== undefined && Number.isFinite(gpsHeading) && gpsHeading >= 0) {
              liveCog = gpsHeading;
              lastCogRef.current = liveCog;
            }
            setCurrentCog(liveCog);

            // === BLOQUE 2: GRABACIÓN (solo si isRecordingRef.current) ===
            if (!isRecordingRef.current) return;
            if (isPausedRef.current) return;

            const quality: GPSFix['quality'] = accuracy <= 10 ? 'GOOD' : accuracy <= 50 ? 'SUSPECT' : 'REJECTED';

            if (sessionIdRef.current) {
              void persistRawFix(location, quality, sessionIdRef.current);
            }

            if (accuracy > MAX_ACCURACY_M) return;

            let distanceIncrement = 0;
            if (lastPointRef.current) {
              distanceIncrement = calculateDistance(
                lastPointRef.current.lat,
                lastPointRef.current.lon,
                location.coords.latitude,
                location.coords.longitude,
              );
            }

            if (distanceIncrement > MAX_JUMP_DISTANCE_M) return;
            if (distanceIncrement < MIN_DISTANCE_DELTA_M && lastPointRef.current) return;

            let calculatedSog = liveSog;
            if (calculatedSog === 0 && lastPointRef.current) {
              const timeDiffSecs = lastPointRef.current.timestamp
              ? (currentTimestamp - lastPointRef.current.timestamp) / 1000
              : 1;
              if (timeDiffSecs > 0 && distanceIncrement > 0) {
                calculatedSog = distanceIncrement / timeDiffSecs;
              }
            }

            let calculatedCog = lastCogRef.current;
            if (calculatedSog >= MIN_SPEED_FOR_COG_UPDATE && lastPointRef.current) {
              calculatedCog = calculateHeading(
                lastPointRef.current.lat,
                lastPointRef.current.lon,
                location.coords.latitude,
                location.coords.longitude,
              );
              lastCogRef.current = calculatedCog;
              setCurrentCog(calculatedCog);
            }

            const newPoint: Coordinate = {
              lat: location.coords.latitude,
              lon: location.coords.longitude,
              sog: calculatedSog,
              cog: calculatedCog,
              timestamp: currentTimestamp,
            };

            lastPointRef.current = newPoint;
            routePointsRef.current = [...routePointsRef.current, newPoint];
            totalDistanceRef.current += distanceIncrement;

            setRoutePoints(routePointsRef.current);
            setTotalDistance(totalDistanceRef.current);
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

    try {
      if (!dbRef.current) {
        dbRef.current = await SQLite.openDatabaseAsync('navego.db');
        await initDatabase(dbRef.current);
      }
      const sessionId = await startSession(dbRef.current, 'Sesión NaveGo');
      sessionIdRef.current = sessionId;
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
    setIsRecording(true);
    setIsTracking(true);
    setIsPaused(false);
    isPausedRef.current = false;
    setSyncState('SIN_INTENTAR');
  };

  const stopTracking = () => {
    isRecordingRef.current = false;
    setIsRecording(false);
    setIsTracking(false);
    setIsPaused(false);
    isPausedRef.current = false;

    if (dbRef.current && sessionIdRef.current) {
      void endSession(dbRef.current, sessionIdRef.current, totalDistanceRef.current).catch(() => {});
      sessionIdRef.current = null;
    }
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
      return next;
    });
  };

  const nav = {
    distanceMeters: totalDistance,
    sog: currentSog,
    cog: currentCog,
    gpsStatus: navigationStatus,
  };

  return {
    nav,
    routePoints,
    totalDistance,
    currentSog,
    currentCog,
    isTracking,
    isRecording,
    isTelemetryActive,
    isPaused,
    syncOk,
    syncState,
    activeHazards,
    lastFixTimestamp,
    lastFixAccuracy,
    navigationStatus,
    startTracking,
    stopTracking,
    togglePause,
    resetTracking,
    resetDistance: resetTracking,
  };
}
