import { useCallback, useEffect, useRef, useState } from 'react';
import { DeviceMotion } from 'expo-sensors';

export type HeadingQuality =
  | 'NO_DISPONIBLE'
  | 'INICIALIZANDO'
  | 'CONFIABLE'
  | 'DEGRADADO';

export interface NaveGoHeadingState {
  heading: number;
  rawHeading: number | null;
  quality: HeadingQuality;
  isAvailable: boolean;
  isEnabled: boolean;
  orientation: number;
  lastUpdateTimestamp: number | null;
}

const UPDATE_INTERVAL_MS = 50; // ~20 Hz

// Suavizado visual.
// Más alto = responde más rápido, menos suavizado.
// Más bajo = más estable, pero más lento.
const SMOOTHING_ALPHA = 0.18;

// Máximo desplazamiento visual por actualización.
// Evita que una lectura defectuosa haga girar violentamente la carta.
const MAX_STEP_DEGREES = 8;

// Si dejamos de recibir datos durante este tiempo,
// la orientación pasa a DEGRADADO.
const STALE_TIMEOUT_MS = 1200;

const INITIAL_HEADING = 0;

function normalizeHeading(degrees: number): number {
  const normalized = degrees % 360;
  return normalized < 0 ? normalized + 360 : normalized;
}

/**
 * Diferencia angular mínima entre dos rumbos.
 *
 * Ejemplo:
 * 359 -> 1 = +2°
 * 1 -> 359 = -2°
 */
function shortestAngleDelta(from: number, to: number): number {
  return ((to - from + 540) % 360) - 180;
}

/**
 * Interpolación circular.
 *
 * Evita el error clásico:
 * 359° -> 1°
 * que no debe atravesar 180°.
 */
function smoothCircularHeading(
  current: number,
  target: number,
  alpha: number
): number {
  const delta = shortestAngleDelta(current, target);
  return normalizeHeading(current + delta * alpha);
}

/**
 * Limita cuánto puede cambiar visualmente el heading
 * en una sola actualización.
 */
function limitHeadingStep(
  current: number,
  target: number,
  maxStep: number
): number {
  const delta = shortestAngleDelta(current, target);

  if (Math.abs(delta) <= maxStep) {
    return normalizeHeading(target);
  }

  return normalizeHeading(
    current + Math.sign(delta) * maxStep
  );
}

/**
 * Primera versión del subsistema de orientación de NaveGo.
 *
 * Responsabilidades:
 * - obtener orientación del dispositivo;
 * - normalizar heading 0..359.999°;
 * - compensar wrap 359°/0°;
 * - suavizar;
 * - limitar saltos visuales;
 * - informar calidad del dato;
 * - permitir activar/desactivar el sistema.
 *
 * NO modifica:
 * - GPS;
 * - SOG;
 * - COG;
 * - SQLite;
 * - sesiones;
 * - sincronización;
 * - hazards.
 */
export function useNaveGoHeading() {
  const [heading, setHeading] = useState<number>(INITIAL_HEADING);
  const [rawHeading, setRawHeading] = useState<number | null>(null);

  const [quality, setQuality] =
    useState<HeadingQuality>('INICIALIZANDO');

  const [isAvailable, setIsAvailable] = useState<boolean>(false);

  const [isEnabled, setIsEnabled] = useState<boolean>(true);

  const [orientation, setOrientation] = useState<number>(0);

  const [lastUpdateTimestamp, setLastUpdateTimestamp] =
    useState<number | null>(null);

  const subscriptionRef = useRef<ReturnType<
    typeof DeviceMotion.addListener
  > | null>(null);

  const headingRef = useRef<number>(INITIAL_HEADING);

  const lastUpdateRef = useRef<number | null>(null);

  const mountedRef = useRef<boolean>(true);

  const setEnabled = useCallback((enabled: boolean) => {
    setIsEnabled(enabled);

    if (!enabled) {
      setQuality('NO_DISPONIBLE');
    } else {
      setQuality('INICIALIZANDO');
    }
  }, []);

  const toggleEnabled = useCallback(() => {
    setIsEnabled((previous) => {
      const next = !previous;

      setQuality(
        next ? 'INICIALIZANDO' : 'NO_DISPONIBLE'
      );

      return next;
    });
  }, []);

  useEffect(() => {
    mountedRef.current = true;

    let cancelled = false;

    const initialize = async () => {
      try {
        const available =
          await DeviceMotion.isAvailableAsync();

        if (cancelled || !mountedRef.current) {
          return;
        }

        setIsAvailable(available);

        if (!available) {
          setQuality('NO_DISPONIBLE');
          return;
        }

        DeviceMotion.setUpdateInterval(
          UPDATE_INTERVAL_MS
        );

        subscriptionRef.current =
          DeviceMotion.addListener((motion) => {
            if (
              !mountedRef.current ||
              cancelled ||
              !isEnabled
            ) {
              return;
            }

            const rotation = motion.rotation;

            if (!rotation) {
              return;
            }

            /**
             * Expo entrega alpha como rotación alrededor
             * del eje Z.
             *
             * En esta primera fase usamos esa señal como
             * referencia de orientación.
             *
             * La calibración/fusión avanzada será una
             * segunda capa, después de probar el comportamiento
             * real en el dispositivo.
             */
            const alphaDegrees =
              (rotation.alpha * 180) / Math.PI;

            const targetHeading =
              normalizeHeading(alphaDegrees);

            const previousHeading =
              headingRef.current;

            const limitedTarget =
              limitHeadingStep(
                previousHeading,
                targetHeading,
                MAX_STEP_DEGREES
              );

            const smoothedHeading =
              smoothCircularHeading(
                previousHeading,
                limitedTarget,
                SMOOTHING_ALPHA
              );

            headingRef.current =
              smoothedHeading;

            const now = Date.now();

            lastUpdateRef.current = now;

            setHeading(smoothedHeading);
            setRawHeading(targetHeading);
            setLastUpdateTimestamp(now);

            /**
             * Una lectura válida y continua no significa
             * necesariamente "perfectamente calibrada".
             *
             * Por ahora clasificamos como CONFIABLE la
             * disponibilidad continua del sensor.
             *
             * La detección de interferencia magnética se
             * incorporará después, cuando tengamos mediciones
             * específicas del hardware.
             */
            setQuality('CONFIABLE');

            if (
              typeof motion.orientation === 'number'
            ) {
              setOrientation(
                motion.orientation
              );
            }
          });
      } catch (error) {
        console.warn(
          '[SOE] Error inicializando orientación:',
          error
        );

        if (!cancelled && mountedRef.current) {
          setIsAvailable(false);
          setQuality('NO_DISPONIBLE');
        }
      }
    };

    initialize();

    return () => {
      cancelled = true;
      mountedRef.current = false;

      if (subscriptionRef.current) {
        subscriptionRef.current.remove();
        subscriptionRef.current = null;
      }
    };
  }, [isEnabled]);

  /**
   * Watchdog de señal.
   *
   * Si el sensor deja de actualizar, no seguimos
   * presentando el heading como perfectamente válido.
   */
  useEffect(() => {
    if (!isEnabled || !isAvailable) {
      return;
    }

    const timer = setInterval(() => {
      const lastUpdate =
        lastUpdateRef.current;

      if (!lastUpdate) {
        return;
      }

      const age =
        Date.now() - lastUpdate;

      if (age > STALE_TIMEOUT_MS) {
        setQuality('DEGRADADO');
      }
    }, 500);

    return () => {
      clearInterval(timer);
    };
  }, [isEnabled, isAvailable]);

  return {
    heading,
    rawHeading,
    quality,
    isAvailable,
    isEnabled,
    orientation,
    lastUpdateTimestamp,

    setEnabled,
    toggleEnabled,
  };
}

