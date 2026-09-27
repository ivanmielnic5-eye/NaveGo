/**
 * Tipos compartidos para el procesamiento de fixes.
 *
 * Objetivo: que la logica de dominio (processFix) sea reutilizable
 * por el hook actual (foreground) y por la Task de background,
 * sin arrastrar React ni SQLite.
 *
 * Fase 0 del plan de migracion a background location.
 */

/** Entrada: fix crudo del proveedor de ubicacion. */
export interface ProcessInput {
  lat: number;
  lon: number;
  accuracy: number;
  speed: number | null;
  heading: number | null;
  measuredAt: number;
}

/** Estado necesario para procesar el proximo fix. */
export interface ProcessState {
  lastPoint: { lat: number; lon: number; timestamp: number } | null;
  lastCog: number;
  isRecording: boolean;
  isPaused: boolean;
  hasOpenGap: boolean;
}

/** Decision sobre el estado del gap. */
export type GapAction = 'NONE' | 'OPEN' | 'CLOSE';

/** Motivo de rechazo para navegacion (no para persistencia). */
export type RejectReason = 'ACCURACY' | 'MIN_DELTA' | null;

/** Calidad del fix (se persiste en la DB). */
export type FixQuality = 'GOOD' | 'SUSPECT' | 'REJECTED';

/** Resultado determinista del procesamiento de un fix. */
export interface ProcessResult {
  // Decisiones de dominio
  persist: boolean;
  quality: FixQuality;
  rejectForNavigation: RejectReason;
  isGapRestart: boolean;
  gapAction: GapAction;

  // Distancias
  /** Distancia aceptada para sumar (0 si isGapRestart). */
  distanceDelta: number;
  /** Distancia cruda entre el fix anterior y este (antes del reset por gap-restart). Solo para diagnostico. */
  rawDistanceDelta: number;

  // Estado siguiente
  nextState: ProcessState;

  // Telemetria derivada (para UI)
  livePosition: { lat: number; lon: number };
  liveSog: number;
  liveCog: number;
  newPoint: {
    lat: number;
    lon: number;
    sog: number;
    cog: number;
    timestamp: number;
  } | null;
}
