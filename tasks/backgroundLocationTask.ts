/**
 * backgroundLocationTask — Fase 2 del Doc 46.
 *
 * Recibe ubicaciones en background y las escribe a un JSONL
 * de prueba (background_test.jsonl en documentDirectory).
 *
 * NO toca SQLite.
 * NO toca React.
 * NO procesa gaps ni distancia.
 *
 * En Fase 2 la Task es solo OBSERVADORA. watchPositionAsync
 * sigue activo en paralelo.
 *
 * El gate de exclusividad (Fase 2.5) valida que no haya
 * duplicados cuando ambos productores esten activos.
 */

import * as TaskManager from 'expo-task-manager';
import * as Location from 'expo-location';
import * as FileSystem from 'expo-file-system/legacy';
import * as SQLite from 'expo-sqlite';
import { processBatchInDb, type OrchestratorInput } from '../tracker/orchestrator';

export const BACKGROUND_LOCATION_TASK = 'NAVEGO_BACKGROUND_LOCATION';

const FILE_PATH = FileSystem.documentDirectory + 'background_test.jsonl';

TaskManager.defineTask(BACKGROUND_LOCATION_TASK, async ({ data, error }) => {
  if (error) {
    console.warn('[TASK-BG] error:', error.message);
    return;
  }
  if (!data) {
    console.warn('[TASK-BG] sin data');
    return;
  }

  const { locations } = data as { locations: Location.LocationObject[] };
  if (!locations || locations.length === 0) return;

  try {
    const db = await SQLite.openDatabaseAsync('navego.db', { useNewConnection: true });

    let targetSession = await db.getFirstAsync<{ id: string; title: string }>(
      `SELECT id, title FROM sessions WHERE title = 'TASK_TEST' AND status = 'ACTIVE' LIMIT 1`,
    );
    let selectedBy = 'TASK_TEST_ACTIVE';
    if (!targetSession) {
      targetSession = await db.getFirstAsync<{ id: string; title: string }>(
        `SELECT id, title FROM sessions WHERE title != 'TASK_TEST' AND status = 'ACTIVE' ORDER BY start_time DESC LIMIT 1`,
      );
      selectedBy = 'PRODUCTION_ACTIVE';
    }

    // [PIPE][TASK] — instrumentacion Fase 1: seleccion de sesion
    const counters = await db.getFirstAsync<{ n_active: number; n_task_test_active: number }>(
      `SELECT
         (SELECT COUNT(*) FROM sessions WHERE status='ACTIVE') AS n_active,
         (SELECT COUNT(*) FROM sessions WHERE title='TASK_TEST' AND status='ACTIVE') AS n_task_test_active`,
    );
    console.log(
      '[PIPE][TASK] n_active=' + (counters?.n_active ?? 0) +
      ' n_task_test_active=' + (counters?.n_task_test_active ?? 0) +
      ' selected_by=' + selectedBy +
      ' session_id=' + (targetSession?.id ?? 'none') +
      ' title=' + (targetSession?.title ?? 'none') +
      ' batch_size=' + locations.length,
    );

    if (targetSession?.id) {
      const items: OrchestratorInput[] = locations.map((loc) => ({
        sessionId: targetSession.id,
        fix: {
          lat: loc.coords.latitude,
          lon: loc.coords.longitude,
          accuracy: loc.coords.accuracy ?? 999,
          speed: loc.coords.speed ?? null,
          heading: loc.coords.heading ?? null,
          measuredAt: loc.timestamp || Date.now(),
        },
        receivedAtMs: Date.now(),
      }));

      const result = await processBatchInDb(db, targetSession.id, items);
      console.log('[TASK-BG] DB: procesados=' + result.processed + ' skipped=' + result.skipped);

      // [PIPE][TASK] — instrumentacion Fase 1: resultado del batch
      console.log(
        '[PIPE][TASK] wrote session_id=' + targetSession.id +
        ' procesados=' + result.processed +
        ' skipped=' + result.skipped,
      );
    } else {
      console.log('[TASK-BG] DB: skip reason=no_active_session');
      // [PIPE][TASK] — instrumentacion Fase 1: motivo de skip
      console.log('[PIPE][TASK] skip reason=no_active_session');
    }

    await db.closeAsync();
  } catch (e) {
    console.warn('[TASK-BG] DB error:', String(e));
  }
});

export const BACKGROUND_TEST_FILE = FILE_PATH;
