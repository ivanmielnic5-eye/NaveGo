/**
 * orchestrator — Fase 3+4 del Doc 46.
 *
 * Recibe un batch de fixes crudos del OS, los procesa con
 * processFix() y persiste todo en SQLite. Lo llama la Task de
 * background (que no tiene acceso a React ni a refs).
 *
 * No importa React.
 * No importa el hook.
 * Solo SQLite + processFix + tipos.
 */

import type { SQLiteDatabase } from 'expo-sqlite';
import { processFix } from './processFix';
import type { ProcessInput, ProcessResult } from './types';
import {
  insertGpsFix,
  insertProcessedPoint,
  openGap,
  closeGap,
  loadOrchestratorStateFromDb,
  advanceLastProcessedSeq,
  type OrchestratorState,
} from '../db/journal';
import type { GPSFix } from '../types/journal';

const GAP_THRESHOLD_MS = 15000;

export interface OrchestratorInput {
  sessionId: string;
  fix: ProcessInput;
  receivedAtMs: number;
}

export interface OrchestratorResult {
  processed: number;
  skipped: number;
}

// =========================================================================
// Deteccion de gap por timestamp
// =========================================================================

/**
 * Si la diferencia entre el timestamp del ultimo fix procesado y el
 * fix actual supera GAP_THRESHOLD_MS, abre un gap retroactivo.
 *
 * No usa timers: la Task puede dormir. El gap se materializa cuando
 * llega el proximo fix.
 *
 * Devuelve el nuevo OrchestratorState con openGapId si se abrio.
 */
async function detectAndOpenGapIfNeeded(
  db: SQLiteDatabase,
  sessionId: string,
  state: OrchestratorState,
  currentReceivedAtMs: number,
): Promise<OrchestratorState> {
  // Sin lastPoint o sin lastFixId: no hay gap posible.
  if (!state.processState.lastPoint || !state.lastFixId) {
    return state;
  }

  // Ya hay un gap abierto: nada que hacer.
  if (state.openGapId) {
    return state;
  }

  // Sin recibido previo: primera entrega, no hay gap.
  if (state.lastReceivedAtMs <= 0) {
    return state;
  }

  // El gap se mide sobre RECEPCION, no sobre medicion GNSS.
  // El OS puede entregar fixes con measuredAt retrasado (batching);
  // pero receivedAt es siempre el momento en que nos llega.
  const elapsedMs = currentReceivedAtMs - state.lastReceivedAtMs;
  if (elapsedMs <= GAP_THRESHOLD_MS) {
    return state;
  }

  // Hay un hueco: abrir gap retroactivo desde el ultimo fix.
  const newGapId = await openGap(
    db,
    sessionId,
    state.lastFixId,
    state.lastSog,
    state.lastCog,
    state.lastAccuracy,
    'GNSS_TIMEOUT',
    state.processState.lastPoint.timestamp,
  );

  console.log(
    '[ORCH] gap abierto id=' + newGapId +
    ' desde fix ' + state.lastFixId +
    ' elapsed=' + elapsedMs + 'ms',
  );

  return {
    ...state,
    openGapId: newGapId,
    processState: {
      ...state.processState,
      hasOpenGap: true,
    },
  };
}

// =========================================================================
// Orquestador principal
// =========================================================================

/**
 * Procesa un batch de fixes del OS. Carga el estado UNA VEZ al
 * inicio y lo actualiza en memoria a medida que procesa.
 *
 * Todo el batch comparte el mismo OrchestratorState.
 */
export async function processBatchInDb(
  db: SQLiteDatabase,
  sessionId: string,
  fixes: OrchestratorInput[],
): Promise<OrchestratorResult> {
  if (fixes.length === 0) {
    return { processed: 0, skipped: 0 };
  }

  let processed = 0;
  let skipped = 0;

  // [PIPE][ORCH] — instrumentacion Fase 1: entrada
  console.log('[PIPE][ORCH] enter session_id=' + sessionId + ' batch_size=' + fixes.length);

  // Cargar estado una vez al inicio del batch.
  let state = await loadOrchestratorStateFromDb(db, sessionId);

  // [PIPE][ORCH] — instrumentacion Fase 1: estado cargado
  console.log(
    '[PIPE][ORCH] state session_id=' + sessionId +
    ' isRecording=' + state.processState.isRecording +
    ' isPaused=' + state.processState.isPaused +
    ' cursor_seq=' + state.cursorSeq +
    ' open_gap=' + (state.openGapId ?? 'none'),
  );

  // Si no esta grabando o esta pausado, no procesar nada.
  if (!state.processState.isRecording || state.processState.isPaused) {
    console.log(
      '[ORCH] batch skipped: isRecording=' +
      state.processState.isRecording +
      ' isPaused=' + state.processState.isPaused,
    );
    // [PIPE][ORCH] — instrumentacion Fase 1: motivo de skip
    console.log('[PIPE][ORCH] skip session_id=' + sessionId + ' reason=not_recording_or_paused');
    return { processed: 0, skipped: fixes.length };
  }

  for (const item of fixes) {
    try {
      // Cuerpo del loop: por cada fix.
      state = await processOneFix(db, sessionId, state, item);
      processed++;
    } catch (e) {
      console.warn('[ORCH] error procesando fix:', String(e));
      skipped++;
    }
  }

  // [PIPE][ORCH] — instrumentacion Fase 1: salida
  console.log(
    '[PIPE][ORCH] exit session_id=' + sessionId +
    ' processed=' + processed +
    ' skipped=' + skipped +
    ' final_cursor=' + state.cursorSeq,
  );

  return { processed, skipped };
}

// =========================================================================
// Procesamiento de un fix individual
// =========================================================================

async function processOneFix(
  db: SQLiteDatabase,
  sessionId: string,
  state: OrchestratorState,
  item: OrchestratorInput,
): Promise<OrchestratorState> {
  // 1. Detectar gap por RECEPCION (no por medicion GNSS).
  state = await detectAndOpenGapIfNeeded(
    db,
    sessionId,
    state,
    item.receivedAtMs,
  );

  // 2. Actualizar hasOpenGap del estado que va a ver processFix.
  const stateForProcess = {
    ...state.processState,
    hasOpenGap: state.openGapId != null,
  };

  // 3. Ejecutar la logica de dominio pura.
  const result = processFix(item.fix, stateForProcess);

  // 4. Si no hay que persistir, salir temprano.
  if (!result.persist) {
    return {
      ...state,
      processState: result.nextState,
    };
  }

  // 5. Calcular sequence_no = cursor + 1.
  const nextSeq = state.cursorSeq + 1;

  // 6. Construir el GPSFix para persistir.
  const rawFix: GPSFix = {
    id: `${item.fix.measuredAt}-${Math.random().toString(36).slice(2, 10)}`,
    session_id: sessionId,
    sequence_no: nextSeq,
    timestamp: item.fix.measuredAt,
    lat_raw: item.fix.lat,
    lon_raw: item.fix.lon,
    alt: null,
    accuracy: item.fix.accuracy,
    speed: item.fix.speed,
    heading: item.fix.heading,
    quality: result.quality,
    satellites: 0,
    received_at_ms: item.receivedAtMs,
    source: 'TASK',
  };

  // 7. Persistir el raw fix.
  await insertGpsFix(db, rawFix);

  // 7b. Persistir el punto procesado (resultado de processFix).
  //     Solo si hay newPoint (el fix fue aceptado para el track).
  if (result.newPoint) {
    const processedId = `pp_${item.fix.measuredAt}_${Math.random().toString(36).slice(2, 10)}`;
    await insertProcessedPoint(db, {
      id: processedId,
      session_id: sessionId,
      sequence_no: nextSeq,
      timestamp: item.fix.measuredAt,
      lat: result.newPoint.lat,
      lon: result.newPoint.lon,
      sog: result.newPoint.sog,
      cog: result.newPoint.cog,
      distance_delta: result.distanceDelta,
      quality: result.quality,
      reject_reason: result.rejectForNavigation,
      is_gap_restart: result.isGapRestart ? 1 : 0,
      gap_action: result.gapAction,
      has_new_point: 1,
      created_at_ms: Date.now(),
    });
  }

  // 8. Si hay que cerrar gap, cerrarlo.
  let newOpenGapId = state.openGapId;
  if (result.gapAction === 'CLOSE' && state.openGapId) {
    await closeGap(db, state.openGapId, rawFix.id, item.fix.measuredAt);
    console.log('[ORCH] gap cerrado id=' + state.openGapId);
    newOpenGapId = null;
  }

  // 9. Avanzar el cursor.
  await advanceLastProcessedSeq(db, sessionId, nextSeq);

  // 10. Devolver el nuevo estado.
  return {
    processState: {
      ...result.nextState,
      hasOpenGap: newOpenGapId != null,
    },
    lastFixId: rawFix.id,
    lastSog: item.fix.speed,
    lastCog: item.fix.heading,
    lastAccuracy: item.fix.accuracy,
    openGapId: newOpenGapId,
    cursorSeq: nextSeq,
    lastReceivedAtMs: item.receivedAtMs,
  };
}
