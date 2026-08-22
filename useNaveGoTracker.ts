import { useState, useEffect, useRef } from 'react';
import * as Location from 'expo-location';
import * as SQLite from 'expo-sqlite';
import { startSession, endSession, insertGpsFix } from './db/journal';
import { initDatabase } from './db/schema';
import type { GPSFix } from './types/journal';

// ====== CONFIGURACIÓN ======
const PC_BRIDGE_URL = 'http://192.168.1.19:3000/update-trajectory';
const SYNC_INTERVAL_MS = 10000;
// ==========================

const MAX_JUMP_DISTANCE_M = 15;
const MAX_ACCURACY_M = 20;
const MIN_DISTANCE_DELTA_M = 0.8;
const MIN_SPEED_FOR_COG_UPDATE = 0.5; // m/s (~1.8 km/h)
const COG_SMOOTHING_ALPHA = 0.2; // menor = más suave

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
}

export interface ActiveHazard extends HazardZone {
  distance: number;
  lastReportedAt?: number;
  confidence: 'CONFIRMADO' | 'ULTIMA_INFORMACION' | 'NO_DISPONIBLE';
}

export type NavigationStatus =
  | 'CONFIABLE'
  | 'DEGRADADO'
  | 'NO_CONFIABLE'
  | 'NO_DISPONIBLE'
  | 'GNSS_PERDIDO'
  | 'RECUPERANDO';

const DEFAULT_HAZARD_ZONES: HazardZone[] = [
  { id: 'h1', name: 'Banco de arena simulado', lat: -31.634, lon: -60.6995, radiusMeters: 50 },
  { id: 'h2', name: 'Tronco flotante', lat: -31.6335, lon: -60.7005, radiusMeters: 30 },
];

function shortestAngleDelta(from: number, to: number): number {
  return ((to - from + 540) % 360) - 180;
}

function normalize360(deg: number): number {
  return ((deg % 360) + 360) % 360;
}

export function useNaveGoTracker() {
  const [routePoints, setRoutePoints] = useState<Coordinate[]>([]);
  const [totalDistance, setTotalDistance] = useState<number>(0);
  const [currentSog, setCurrentSog] = useState<number>(0);
  const [currentCog, setCurrentCog] = useState<number>(0);
  const [smoothedCog, setSmoothedCog] = useState<number | null>(null);
  const [isTracking, setIsTracking] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [syncOk, setSyncOk] = useState<boolean | null>(null);
  const [activeHazards, setActiveHazards] = useState<ActiveHazard[]>([]);
  const [lastFixTimestamp, setLastFixTimestamp] = useState<number | null>(null);
  const [lastFixAccuracy, setLastFixAccuracy] = useState<number | null>(null);
  const [navigationStatus, setNavigationStatus] = useState<NavigationStatus>('NO_DISPONIBLE');

  const isPausedRef = useRef<boolean>(false);
  const subscriptionRef = useRef<Location.LocationSubscription | null>(null);
  const lastPointRef = useRef<Coordinate | null>(null);
  const routePointsRef = useRef<Coordinate[]>([]);
  const syncTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const dbRef = useRef<SQLite.SQLiteDatabase | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const sequenceNoRef = useRef<number>(0);
  const totalDistanceRef = useRef<number>(0);

  const lastCogRef = useRef<number>(0);
  const smoothedCogRef = useRef<number | null>(null);

  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    const R = 6371e3;
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
      Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  };

  const calculateHeading = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const y = Math.sin(dLon) * Math.cos(lat2 * (Math.PI / 180));
    const x = Math.cos(lat1 * (Math.PI / 180)) * Math.sin(lat2 * (Math.PI / 180)) -
      Math.sin(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) * Math.cos(dLon);
    return normalize360(Math.atan2(y, x) * 180 / Math.PI + 180);
  };

  const syncTrajectoryToPC = async (points: Coordinate[]) => {
    if (!points || points.length === 0) return;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      await fetch(PC_BRIDGE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(points),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      setSyncOk(true);
    } catch {
      setSyncOk(false);
    }
  };

  const scheduleSync = () => {
    if (syncTimerRef.current) clearTimeout(syncTimerRef.current);
    syncTimerRef.current = setTimeout(() => {
      if (routePointsRef.current.length > 0 && !isPausedRef.current) {
        syncTrajectoryToPC(routePointsRef.current);
      }
      scheduleSync();
    }, SYNC_INTERVAL_MS);
  };

  const updateNavigationStatus = (timestamp: number | null, accuracy?: number) => {
    if (!timestamp) {
      setNavigationStatus('NO_DISPONIBLE');
      return;
    }
    const seconds = (Date.now() - timestamp) / 1000;
    if (seconds > 5) {
      setNavigationStatus('GNSS_PERDIDO');
    } else if (accuracy !== undefined && accuracy > MAX_ACCURACY_M) {
      setNavigationStatus('DEGRADADO');
    } else if (seconds > 2 && seconds <= 5) {
      setNavigationStatus('RECUPERANDO');
    } else if (seconds <= 2) {
      setNavigationStatus('CONFIABLE');
    } else {
      setNavigationStatus('NO_CONFIABLE');
    }
  };

  const evaluateHazards = (lat: number, lon: number): ActiveHazard[] => {
    const now = Date.now();
    return DEFAULT_HAZARD_ZONES.map((h) => {
      const distance = calculateDistance(lat, lon, h.lat, h.lon);
      let confidence: ActiveHazard['confidence'] = 'NO_DISPONIBLE';
      let lastReportedAt: number | undefined;

      if (distance <= h.radiusMeters) {
        lastReportedAt = now - 120000;
        confidence = 'CONFIRMADO';
      }

      return { ...h, distance, lastReportedAt, confidence };
    }).filter((h) => h.distance <= h.radiusMeters);
  };

  const startTracking = async () => {
    resetTracking();
    try {
      if (dbRef.current === null) {
        dbRef.current = await SQLite.openDatabaseAsync('navego.db');
        await initDatabase(dbRef.current);
      }
      const sessionId = await startSession(dbRef.current, 'Sesión NaveGo');
      sessionIdRef.current = sessionId;
      sequenceNoRef.current = 0;
    } catch (error) {
      console.warn('[DB] Error al abrir/iniciar base local:', error);
    }

    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      console.error('[TRACKER] Permiso de ubicación denegado');
      return;
    }

    setIsTracking(true);
    setIsPaused(false);
    isPausedRef.current = false;

    subscriptionRef.current = await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.High,
        timeInterval: 1000,
        distanceInterval: 0,
      },
      (location) => {
        if (isPausedRef.current) return;

        const currentTimestamp = location.timestamp || Date.now();
        const accuracy = location.coords.accuracy ?? 999;
        const gpsSpeed = location.coords.speed;

        if (accuracy > MAX_ACCURACY_M) return;

        let distanceIncrement = 0;
        if (lastPointRef.current) {
          distanceIncrement = calculateDistance(
            lastPointRef.current.lat,
            lastPointRef.current.lon,
            location.coords.latitude,
            location.coords.longitude
          );
        }

        if (distanceIncrement > MAX_JUMP_DISTANCE_M) return;
        if (distanceIncrement < MIN_DISTANCE_DELTA_M && lastPointRef.current) return;

        let calculatedSog = 0;
        if (gpsSpeed !== null && gpsSpeed !== undefined && Number.isFinite(gpsSpeed) && gpsSpeed >= 0) {
          calculatedSog = gpsSpeed;
        } else if (lastPointRef.current) {
          const timeDiffSecs = lastPointRef.current.timestamp
            ? (currentTimestamp - lastPointRef.current.timestamp) / 1000
            : 1;
          if (timeDiffSecs > 0 && distanceIncrement > 0) {
            calculatedSog = distanceIncrement / timeDiffSecs;
          }
        }

        let calculatedCog = lastCogRef.current;
        if (calculatedSog >= MIN_SPEED_FOR_COG_UPDATE && lastPointRef.current) {
          const newCog = calculateHeading(
            lastPointRef.current.lat,
            lastPointRef.current.lon,
            location.coords.latitude,
            location.coords.longitude
          );

          // Suavizado circular
          if (smoothedCogRef.current === null) {
            smoothedCogRef.current = newCog;
          } else {
            const delta = shortestAngleDelta(smoothedCogRef.current, newCog);
            smoothedCogRef.current = normalize360(smoothedCogRef.current + delta * COG_SMOOTHING_ALPHA);
          }

          calculatedCog = smoothedCogRef.current;
          lastCogRef.current = calculatedCog;
        }

        const newPoint: Coordinate = {
          lat: location.coords.latitude,
          lon: location.coords.longitude,
          sog: calculatedSog,
          cog: calculatedCog,
          timestamp: currentTimestamp,
        };

        if (dbRef.current && sessionIdRef.current) {
          const fix: GPSFix = {
            id: `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
            session_id: sessionIdRef.current,
            sequence_no: sequenceNoRef.current++,
            timestamp: currentTimestamp,
            lat_raw: location.coords.latitude,
            lon_raw: location.coords.longitude,
            alt: location.coords.altitude ?? null,
            accuracy: accuracy,
            speed: gpsSpeed ?? null,
            heading: location.coords.heading ?? null,
            quality: accuracy < 15 ? 'GOOD' : 'SUSPECT',
            satellites: 0,
          };
          insertGpsFix(dbRef.current, fix).catch((err) => console.warn('[DB] Error al guardar fix:', err));
        }

        lastPointRef.current = newPoint;
        routePointsRef.current = [...routePointsRef.current, newPoint];
        totalDistanceRef.current += distanceIncrement;

        setRoutePoints(routePointsRef.current);
        setTotalDistance(totalDistanceRef.current);
        setCurrentSog(calculatedSog);
        setCurrentCog(calculatedCog);
        setSmoothedCog(smoothedCogRef.current);
        setLastFixTimestamp(currentTimestamp);
        setLastFixAccuracy(accuracy);
        updateNavigationStatus(currentTimestamp, accuracy);
        setActiveHazards(evaluateHazards(location.coords.latitude, location.coords.longitude));
      }
    );

    scheduleSync();
  };

  const stopTracking = () => {
    if (subscriptionRef.current) {
      subscriptionRef.current.remove();
      subscriptionRef.current = null;
    }
    if (syncTimerRef.current) {
      clearTimeout(syncTimerRef.current);
      syncTimerRef.current = null;
    }
    if (dbRef.current && sessionIdRef.current) {
      endSession(dbRef.current, sessionIdRef.current, totalDistanceRef.current).catch((err) =>
        console.warn('[DB] Error al cerrar sesión:', err)
      );
      sessionIdRef.current = null;
    }
    setIsTracking(false);
    setIsPaused(false);
    isPausedRef.current = false;
    setNavigationStatus('NO_DISPONIBLE');
  };

  const togglePause = () => {
    setIsPaused((prev) => {
      const next = !prev;
      isPausedRef.current = next;
      return next;
    });
  };

  const resetTracking = () => {
    if (sessionIdRef.current && dbRef.current) {
      dbRef.current.withTransactionSync?.(() => {}) ?? null;
    }
    sessionIdRef.current = null;
    sequenceNoRef.current = 0;
    setRoutePoints([]);
    routePointsRef.current = [];
    setTotalDistance(0);
    totalDistanceRef.current = 0;
    setCurrentSog(0);
    setCurrentCog(0);
    setSmoothedCog(null);
    smoothedCogRef.current = null;
    setActiveHazards([]);
    lastPointRef.current = null;
    lastCogRef.current = 0;
    setLastFixTimestamp(null);
    setLastFixAccuracy(null);
    setNavigationStatus('NO_DISPONIBLE');
  };

  const resetDistance = resetTracking;

  useEffect(() => {
    return () => {
      if (subscriptionRef.current) subscriptionRef.current.remove();
      if (syncTimerRef.current) clearTimeout(syncTimerRef.current);
      if (dbRef.current && sessionIdRef.current) {
        endSession(dbRef.current, sessionIdRef.current, totalDistanceRef.current).catch(() => {});
      }
    };
  }, []);

  const nav = {
    distanceMeters: totalDistance,
    sog: currentSog,
    cog: currentCog,
    gpsStatus: isTracking ? 'OK' : 'BUSCANDO...',
  };

  return {
    nav,
    routePoints,
    totalDistance,
    currentSog,
    currentCog,
    smoothedCog,
    isTracking,
    isPaused,
    syncOk,
    activeHazards,
    lastFixTimestamp,
    lastFixAccuracy,
    navigationStatus,
    startTracking,
    stopTracking,
    togglePause,
    resetTracking,
    resetDistance,
  };
}








