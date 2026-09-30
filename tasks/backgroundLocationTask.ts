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

  let contenido = '';
  try {
    const info = await FileSystem.getInfoAsync(FILE_PATH);
    if (info.exists) {
      contenido = await FileSystem.readAsStringAsync(FILE_PATH);
    }
  } catch {
    contenido = '';
  }

  let nuevasLineas = '';
  for (const loc of locations) {
    const entry = {
      source: 'task',
      t: loc.timestamp || Date.now(),
      lat: loc.coords.latitude,
      lon: loc.coords.longitude,
      accuracy: loc.coords.accuracy ?? null,
      speed: loc.coords.speed ?? null,
      heading: loc.coords.heading ?? null,
    };
    nuevasLineas += JSON.stringify(entry) + '\n';
  }

  try {
    await FileSystem.writeAsStringAsync(FILE_PATH, contenido + nuevasLineas);
    console.log(`[TASK-BG] +${locations.length} fixes escritos`);
  } catch (e) {
    console.warn('[TASK-BG] error escribiendo:', String(e));
  }

  // PRUEBA A (TEMPORAL): abrir DB nueva, SELECT 1, cerrar.
  // Aisla: expo-sqlite funciona en Headless JS?
  try {
    const testDb = await SQLite.openDatabaseAsync('test_prueba_a.db');
    const result = await testDb.getFirstAsync<{ x: number }>('SELECT 1 as x');
    console.log('[TASK-BG] PRUEBA A OK:', JSON.stringify(result));
    await testDb.closeAsync();
  } catch (e) {
    console.warn('[TASK-BG] PRUEBA A FALLO:', String(e));
  }

  // FASE 3+4 DOC 46: procesar batch en DB si hay sesion TASK_TEST activa.
  try {
    const db = await SQLite.openDatabaseAsync('navego.db', { useNewConnection: true });

    const testSession = await db.getFirstAsync<{ id: string }>(
      `SELECT id FROM sessions WHERE title = 'TASK_TEST' AND status = 'ACTIVE' LIMIT 1`,
    );

    if (testSession?.id) {
      const items: OrchestratorInput[] = locations.map((loc) => ({
        sessionId: testSession.id,
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

      const result = await processBatchInDb(db, testSession.id, items);
      console.log('[TASK-BG] DB: procesados=' + result.processed + ' skipped=' + result.skipped);
    } else {
      console.log('[TASK-BG] DB: sin sesion TASK_TEST activa, skip');
    }

    await db.closeAsync();
  } catch (e) {
    console.warn('[TASK-BG] DB error:', String(e));
  }
});

export const BACKGROUND_TEST_FILE = FILE_PATH;
