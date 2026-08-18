// Tipos y máquina de estados de navegación de NaveGo.
// Fuente única de verdad para el vocabulario de estados que usan
// el hook de tracking (useNaveGoTracker) y la UI (HUD/Cockpit).

/** Estado de conectividad/calidad de la señal GPS. */
export type GPSStatus = 'INITIALIZING' | 'OK' | 'DEGRADED' | 'LOST' | 'RECOVERING';

/**
 * Estado de movimiento del dispositivo. 'UNKNOWN' existe para el
 * arranque y para cuando ninguna señal tiene todavía confianza
 * suficiente para clasificar — nunca se asume 'STATIC' por default
 * solo porque falta información (evidencia sobre certeza).
 */
export type MotionStatus = 'STATIC' | 'MOVING' | 'UNKNOWN';

/**
 * Qué sensores están efectivamente contribuyendo a la clasificación
 * de movimiento en este momento. Es distinto de gpsStatus: acá
 * importa la COMPOSICIÓN de sensores disponibles, no la calidad del
 * fix. GPS_DEGRADED específicamente significa "el acelerómetro no
 * está disponible Y además el GPS está en mala forma" — el peor caso,
 * dependiendo de una sola fuente ruidosa.
 */
export type SensorStatus = 'GPS_ONLY' | 'GPS_ACCEL' | 'GPS_DEGRADED';

export interface Position {
  latitude: number;
  longitude: number;
  accuracy: number | null;
  timestamp: number;
}

/**
 * Estado unificado de navegación. Cada dato "vivo" (sog, cog,
 * distancia) viaja siempre junto con su metadata de validez — la UI
 * nunca debería tener que adivinar si un número es una medición
 * actual o un valor viejo mostrado por inercia.
 */
export interface NavigationState {
  gpsStatus: GPSStatus;
  motionStatus: MotionStatus;
  sensorStatus: SensorStatus;

  /** Errores de la app en sí (permisos, fallo al iniciar el hook) —
   * deliberadamente separado de gpsStatus, que es sobre la señal. */
  appError: string | null;

  position: Position | null;
  lastValidPosition: Position | null;
  lastValidFixAt: number | null;

  /** Speed over ground, en nudos. null si no hay medición vigente (gpsStatus !== 'OK'). */
  sog: number | null;
  /** Course over ground, en grados. null si no hay medición vigente. */
  cog: number | null;

  /** Distancia acumulada CONFIRMADA, en metros. Nunca incluye estimaciones durante GPS_LOST. */
  distanceMeters: number;
  /** true mientras gpsStatus !== 'OK': la distancia no se está acumulando ahora mismo. */
  distancePaused: boolean;

  /** Auditabilidad rápida para el HUD ("142 fixes válidos"). */
  acceptedFixCount: number;
  suspectFixCount: number;
}

export const initialNavigationState: NavigationState = {
  gpsStatus: 'INITIALIZING',
  motionStatus: 'UNKNOWN',
  sensorStatus: 'GPS_ONLY',
  appError: null,
  position: null,
  lastValidPosition: null,
  lastValidFixAt: null,
  sog: null,
  cog: null,
  distanceMeters: 0,
  distancePaused: false,
  acceptedFixCount: 0,
  suspectFixCount: 0,
};
