// db/journal.ts
import type { SQLiteDatabase } from 'expo-sqlite';
import type { GPSFix } from '../types/journal';
import type { ProcessState } from '../tracker/types';

export async function startSession(db: SQLiteDatabase, title?: string): Promise<string> {
  const sessionId = `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  await db.runAsync(
    `INSERT INTO sessions (id, start_time, title, total_distance, status)
    VALUES (?, ?, ?, 0, 'ACTIVE')`,
                    [sessionId, Date.now(), title ?? 'Sesión NaveGo']
  );
  return sessionId;
}

export async function insertGpsFix(db: SQLiteDatabase, fix: GPSFix): Promise<void> {
  const id = typeof fix.id === 'string' && fix.id.length > 0
  ? fix.id
  : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  const sessionId = fix.session_id ?? '';
  const sequenceNo = Number.isFinite(fix.sequence_no) ? Math.floor(fix.sequence_no) : 0;
  const timestamp = Number.isFinite(fix.timestamp) ? Math.floor(fix.timestamp) : Date.now();
  const latRaw = Number.isFinite(fix.lat_raw) ? fix.lat_raw : 0;
  const lonRaw = Number.isFinite(fix.lon_raw) ? fix.lon_raw : 0;
  const alt = (fix.alt !== undefined && fix.alt !== null && Number.isFinite(fix.alt)) ? Number(fix.alt) : null;
  const accuracy = (fix.accuracy !== undefined && fix.accuracy !== null && Number.isFinite(fix.accuracy)) ? Number(fix.accuracy) : null;
  const speed = (fix.speed !== undefined && fix.speed !== null && Number.isFinite(fix.speed)) ? Number(fix.speed) : null;
  const heading = (fix.heading !== undefined && fix.heading !== null && Number.isFinite(fix.heading)) ? Number(fix.heading) : null;
  const quality = (fix.quality === 'GOOD' || fix.quality === 'SUSPECT' || fix.quality === 'REJECTED') ? fix.quality : 'SUSPECT';
  const satellites = (typeof fix.satellites === 'number' && Number.isFinite(fix.satellites)) ? Math.floor(fix.satellites) : 0;
  const receivedAtMs = (typeof fix.received_at_ms === 'number' && Number.isFinite(fix.received_at_ms)) ? Math.floor(fix.received_at_ms) : null;
  const source = (fix.source === 'GNSS' || fix.source === 'REPLAY' || fix.source === 'TASK') ? fix.source : 'GNSS';

  await db.runAsync(
    `INSERT INTO gps_fixes
    (id, session_id, sequence_no, timestamp, lat_raw, lon_raw, alt,
     accuracy, speed, heading, quality, satellites, received_at_ms, source)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                    [
                      id, sessionId, sequenceNo, timestamp, latRaw, lonRaw, alt,
                    accuracy, speed, heading, quality, satellites, receivedAtMs, source,
                    ]
  );
}

export async function endSession(db: SQLiteDatabase, sessionId: string, totalDistance: number): Promise<void> {
  await db.runAsync(
    `UPDATE sessions SET end_time = ?, total_distance = ?, status = 'COMPLETED' WHERE id = ?`,
    [Date.now(), totalDistance, sessionId]
  );
}

export async function getSessionFixes(db: SQLiteDatabase, sessionId: string): Promise<GPSFix[]> {
  const rows = await db.getAllAsync<GPSFix>(
    `SELECT * FROM gps_fixes WHERE session_id = ? ORDER BY sequence_no ASC`,
    [sessionId]
  );
  return rows;
}

export async function getAllSessions(db: SQLiteDatabase): Promise<any[]> {
  return await db.getAllAsync<any>(`SELECT * FROM sessions ORDER BY start_time DESC`);
}

export async function getSessionDetail(db: SQLiteDatabase, sessionId: string): Promise<any> {
  const session = await db.getFirstAsync<any>(
    `SELECT * FROM sessions WHERE id = ?`,
    [sessionId]
  );
  if (!session) return null;

  const stats = await db.getFirstAsync<any>(
    `SELECT
    COUNT(*) as total_fixes,
                                            SUM(CASE WHEN quality = 'GOOD' THEN 1 ELSE 0 END) as good_fixes,
                                            SUM(CASE WHEN quality = 'SUSPECT' THEN 1 ELSE 0 END) as suspect_fixes,
                                            SUM(CASE WHEN quality = 'REJECTED' THEN 1 ELSE 0 END) as rejected_fixes,
                                            AVG(speed) as avg_speed,
                                            MAX(speed) as max_speed
                                            FROM gps_fixes
                                            WHERE session_id = ?`,
                                            [sessionId]
  );

  return { ...session, ...stats };
}

export async function getAllReferenceRoutes(db: SQLiteDatabase): Promise<any[]> {
  return await db.getAllAsync<any>(`SELECT * FROM reference_routes ORDER BY created_at DESC`);
}

function calculateDistanceFromCoords(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371e3;
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLon = (lon2 - lon1) * (Math.PI / 180);
  const a =
  Math.sin(dLat / 2) ** 2 +
  Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
  Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

export async function createReferenceRouteFromSession(
  db: SQLiteDatabase,
  sessionId: string,
  name: string
): Promise<string> {
  const session = await db.getFirstAsync<any>(
    `SELECT * FROM sessions WHERE id = ?`,
    [sessionId]
  );
  if (!session) throw new Error('Sesión no encontrada');

  const fixes = await getSessionFixes(db, sessionId);

  // Fix P1 (2026-09-25): no sumar el tramo puente de un gap GNSS.
  // El tracker corta ese salto (isGapRestart, incremento=0), pero este
  // calculo sumaba TODOS los pares consecutivos, incluyendo el par
  // pre-gap/post-gap. Se excluye el segmento entre start_fix_id y
  // end_fix_id de cada gap CLOSED de la sesion (fuente de verdad:
  // tabla gap_events). NO toca filtros de accuracy/quality/delta.
  const gapRows = await db.getAllAsync<{ start_fix_id: string; end_fix_id: string | null }>(
    `SELECT start_fix_id, end_fix_id FROM gap_events
     WHERE session_id = ? AND status = 'CLOSED' AND end_fix_id IS NOT NULL`,
    [sessionId]
  );
  const gapSegments = new Set(
    gapRows.map((g) => `${g.start_fix_id}->${g.end_fix_id}`)
  );

  let distance = 0;
  for (let i = 1; i < fixes.length; i++) {
    if (gapSegments.has(`${fixes[i - 1].id}->${fixes[i].id}`)) continue;
    distance += calculateDistanceFromCoords(
      fixes[i - 1].lat_raw,
      fixes[i - 1].lon_raw,
      fixes[i].lat_raw,
      fixes[i].lon_raw
    );
  }

  const firstTime = fixes[0]?.timestamp ?? session.start_time;
  const lastTime = fixes.length > 0 ? fixes[fixes.length - 1].timestamp : session.end_time ?? session.start_time;
  const durationS = Math.max(0, Math.floor((lastTime - firstTime) / 1000));

  const routeId = `route_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;

  await db.runAsync(
    `INSERT INTO reference_routes (id, name, source_session_id, distance_m, duration_s, created_at)
    VALUES (?, ?, ?, ?, ?, ?)`,
                    [routeId, name, sessionId, distance, durationS, Date.now()]
  );

  for (const fix of fixes) {
    await db.runAsync(
      `INSERT INTO reference_route_points (route_id, sequence_no, lat, lon)
      VALUES (?, ?, ?, ?)`,
                      [routeId, fix.sequence_no, fix.lat_raw, fix.lon_raw]
    );
  }

  return routeId;
}

export async function getReferenceRoutePoints(
  db: SQLiteDatabase,
  routeId: string
): Promise<{ lat: number; lon: number; sequence_no: number }[]> {
  return await db.getAllAsync<any>(
    `SELECT lat, lon, sequence_no FROM reference_route_points WHERE route_id = ? ORDER BY sequence_no ASC`,
    [routeId]
  );
}

export async function deleteReferenceRoute(
  db: SQLiteDatabase,
  routeId: string
): Promise<void> {
  await db.runAsync(
    `DELETE FROM reference_routes WHERE id = ?`,
    [routeId]
  );
  // CASCADE borra automáticamente los puntos en reference_route_points
}

// ============================================================
// NUEVO — Fix 2026-09-15: Borrado de sesiones individuales
// ============================================================

/**
 * Borra una sesión completa de la base de datos.
 * Los gps_fixes asociados se borran automáticamente
 * gracias a la cláusula ON DELETE CASCADE definida en el schema.
 */
export async function deleteSession(
  db: SQLiteDatabase,
  sessionId: string
): Promise<void> {
  await db.runAsync(
    `DELETE FROM sessions WHERE id = ?`,
    [sessionId]
  );
}

// ============================================================
// GAP EVENTS — Deteccion de perdida de senal GNSS (2026-09-25)
// ============================================================

export async function openGap(
  db: SQLiteDatabase,
  sessionId: string,
  startFixId: string,
  lastSogMps: number | null,
  lastCogDeg: number | null,
  lastAccuracyM: number | null,
  reason: 'GNSS_TIMEOUT' | 'PROVIDER_UNAVAILABLE' | 'INVALID_FIX' | 'UNKNOWN' = 'GNSS_TIMEOUT',
  startAtMs: number = Date.now(),
): Promise<string> {
  const id = `gap_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  const now = Date.now();
  await db.runAsync(
    `INSERT INTO gap_events
      (id, session_id, start_fix_id, start_at_ms, detected_at_ms,
       last_observed_sog_mps, last_observed_cog_deg, last_observed_accuracy_m,
       status, reason, created_at_ms, updated_at_ms)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?)`,
    [id, sessionId, startFixId, startAtMs, now,
     lastSogMps, lastCogDeg, lastAccuracyM,
     reason, now, now]
  );
  return id;
}

export async function closeGap(
  db: SQLiteDatabase,
  gapId: string,
  endFixId: string,
  endAtMs: number,
): Promise<void> {
  const now = Date.now();
  const row = await db.getFirstAsync<{ start_at_ms: number }>(
    `SELECT start_at_ms FROM gap_events WHERE id = ?`,
    [gapId]
  );
  const durationMs = row ? Math.max(0, endAtMs - row.start_at_ms) : null;
  await db.runAsync(
    `UPDATE gap_events
     SET end_fix_id = ?, end_at_ms = ?, duration_ms = ?,
         status = 'CLOSED', updated_at_ms = ?
     WHERE id = ?`,
    [endFixId, endAtMs, durationMs, now, gapId]
  );
}

export async function getOpenGap(
  db: SQLiteDatabase,
  sessionId: string,
): Promise<{ id: string; start_fix_id: string; start_at_ms: number } | null> {
  return await db.getFirstAsync<{ id: string; start_fix_id: string; start_at_ms: number }>(
    `SELECT id, start_fix_id, start_at_ms FROM gap_events
     WHERE session_id = ? AND status = 'OPEN'
     ORDER BY start_at_ms DESC LIMIT 1`,
    [sessionId]
  );
}


/**
 * Abandona un gap que estaba abierto cuando la sesion termino.
 * A diferencia de closeGap, no requiere un end_fix_id (no llego
 * ningun fix). Se usa cuando el usuario finaliza la sesion
 * durante un corte de senal.
 */
export async function abandonGap(
  db: SQLiteDatabase,
  gapId: string,
  abandonedAtMs: number,
): Promise<void> {
  const now = Date.now();
  const row = await db.getFirstAsync<{ start_at_ms: number }>(
    `SELECT start_at_ms FROM gap_events WHERE id = ?`,
    [gapId]
  );
  const durationMs = row ? Math.max(0, abandonedAtMs - row.start_at_ms) : null;
  await db.runAsync(
    `UPDATE gap_events
     SET end_at_ms = ?, duration_ms = ?, status = 'CLOSED', updated_at_ms = ?
     WHERE id = ? AND status = 'OPEN'`,
    [abandonedAtMs, durationMs, now, gapId]
  );
}

// =========================================================================
// FASE 3+4 DOC 46 — Estado persistente para la Task de background
// =========================================================================

/**
 * Reconstruye el ProcessState leyendo de SQLite.
 * Lo usa la Task para procesar fixes sin depender de React.
 */
export async function loadProcessStateFromDb(
  db: SQLiteDatabase,
  sessionId: string,
): Promise<ProcessState> {
  // Session: status, is_paused, last_processed_seq
  const session = await db.getFirstAsync<{
    status: string;
    is_paused: number | null;
    last_processed_seq: number | null;
  }>(
    `SELECT status, is_paused, last_processed_seq FROM sessions WHERE id = ?`,
    [sessionId],
  );

  const isRecording = session?.status === 'ACTIVE';
  const isPaused = (session?.is_paused ?? 0) === 1;
  const cursorSeq = session?.last_processed_seq ?? -1;

  // Ultimo punto procesado (segun el cursor)
  const lastPoint = await db.getFirstAsync<{
    lat_raw: number;
    lon_raw: number;
    timestamp: number;
  }>(
    `SELECT lat_raw, lon_raw, timestamp FROM gps_fixes
     WHERE session_id = ? AND sequence_no <= ?
     ORDER BY sequence_no DESC LIMIT 1`,
    [sessionId, cursorSeq],
  );

  // Ultimo COG valido (heading > 0)
  const lastCogRow = await db.getFirstAsync<{ heading: number }>(
    `SELECT heading FROM gps_fixes
     WHERE session_id = ? AND sequence_no <= ?
       AND heading IS NOT NULL AND heading > 0
     ORDER BY sequence_no DESC LIMIT 1`,
    [sessionId, cursorSeq],
  );

  // Hay gap abierto?
  const openGap = await db.getFirstAsync<{ id: string }>(
    `SELECT id FROM gap_events
     WHERE session_id = ? AND status = 'OPEN'
     LIMIT 1`,
    [sessionId],
  );

  return {
    lastPoint: lastPoint
      ? { lat: lastPoint.lat_raw, lon: lastPoint.lon_raw, timestamp: lastPoint.timestamp }
      : null,
    lastCog: lastCogRow?.heading ?? 0,
    isRecording,
    isPaused,
    hasOpenGap: openGap != null,
  };
}

/**
 * Actualiza is_paused de la sesion.
 */
export async function saveIsPaused(
  db: SQLiteDatabase,
  sessionId: string,
  paused: boolean,
): Promise<void> {
  await db.runAsync(
    `UPDATE sessions SET is_paused = ? WHERE id = ?`,
    [paused ? 1 : 0, sessionId],
  );
}

/**
 * Actualiza el cursor de procesamiento.
 */
export async function saveLastProcessedSeq(
  db: SQLiteDatabase,
  sessionId: string,
  seq: number,
): Promise<void> {
  await db.runAsync(
    `UPDATE sessions SET last_processed_seq = ? WHERE id = ?`,
    [seq, sessionId],
  );
}

/**
 * Avanza el cursor solo si el nuevo seq es mayor al actual.
 * Idempotente: si lo llamas dos veces con el mismo seq, no cambia nada.
 */
export async function advanceLastProcessedSeq(
  db: SQLiteDatabase,
  sessionId: string,
  seq: number,
): Promise<void> {
  await db.runAsync(
    `UPDATE sessions SET last_processed_seq = ?
     WHERE id = ? AND (last_processed_seq IS NULL OR last_processed_seq < ?)`,
    [seq, sessionId, seq],
  );
}

/**
 * Estado completo que necesita el orquestador de la Task.
 * Incluye el ProcessState + metadatos de persistencia.
 */
export interface OrchestratorState {
  processState: ProcessState;
  lastFixId: string | null;
  lastSog: number | null;
  lastCog: number | null;
  lastAccuracy: number | null;
  openGapId: string | null;
  cursorSeq: number;
  lastReceivedAtMs: number;
}

export async function loadOrchestratorStateFromDb(
  db: SQLiteDatabase,
  sessionId: string,
): Promise<OrchestratorState> {
  const processState = await loadProcessStateFromDb(db, sessionId);

  const session = await db.getFirstAsync<{ last_processed_seq: number | null }>(
    `SELECT last_processed_seq FROM sessions WHERE id = ?`,
    [sessionId],
  );
  const cursorSeq = session?.last_processed_seq ?? -1;

  const lastFix = await db.getFirstAsync<{
    id: string;
    speed: number | null;
    heading: number | null;
    accuracy: number | null;
  }>(
    `SELECT id, speed, heading, accuracy FROM gps_fixes
     WHERE session_id = ? AND sequence_no <= ?
     ORDER BY sequence_no DESC LIMIT 1`,
    [sessionId, cursorSeq],
  );

  const openGapRow = await db.getFirstAsync<{ id: string }>(
    `SELECT id FROM gap_events
     WHERE session_id = ? AND status = 'OPEN'
     LIMIT 1`,
    [sessionId],
  );

  const lastReceived = await db.getFirstAsync<{ received_at_ms: number | null }>(
    `SELECT received_at_ms FROM gps_fixes
     WHERE session_id = ? AND sequence_no <= ? AND received_at_ms IS NOT NULL
     ORDER BY sequence_no DESC LIMIT 1`,
    [sessionId, cursorSeq],
  );

  return {
    processState,
    lastFixId: lastFix?.id ?? null,
    lastSog: lastFix?.speed ?? null,
    lastCog: lastFix?.heading ?? null,
    lastAccuracy: lastFix?.accuracy ?? null,
    openGapId: openGapRow?.id ?? null,
    cursorSeq,
    lastReceivedAtMs: lastReceived?.received_at_ms ?? 0,
  };
}

// =========================================================================
// FASE 3+4 DOC 46 — Sesion test paralela
// =========================================================================

/**
 * Busca una sesion ACTIVE con el titulo indicado. Si no existe,
 * la crea.
 *
 * Se usa para que la Task escriba a una sesion paralela
 * (session_id distinto) sin mezclarse con la sesion real de
 * watchPosition. Permite comparar ambos productores en las
 * mismas tablas sin migraciones.
 */
export async function findOrCreateTestSession(
  db: SQLiteDatabase,
  title: string,
): Promise<string> {
  const existing = await db.getFirstAsync<{ id: string }>(
    `SELECT id FROM sessions WHERE title = ? AND status = 'ACTIVE' LIMIT 1`,
    [title],
  );
  if (existing?.id) {
    return existing.id;
  }
  const sessionId = `session_test_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  await db.runAsync(
    `INSERT INTO sessions (id, start_time, title, total_distance, status)
     VALUES (?, ?, ?, 0, 'ACTIVE')`,
    [sessionId, Date.now(), title],
  );
  console.log('[JOURNAL] sesion test creada:', sessionId, title);
  return sessionId;
}

/**
 * Persiste el resultado derivado de processFix.
 * Lo usa el orquestador en modo produccion para que el hook
 * (consumidor) pueda leer los puntos procesados sin recalcular.
 */
export interface ProcessedPoint {
  id: string;
  session_id: string;
  sequence_no: number;
  timestamp: number;
  lat: number;
  lon: number;
  sog: number;
  cog: number;
  distance_delta: number;
  quality: string;
  reject_reason: string | null;
  is_gap_restart: number;
  gap_action: string | null;
  has_new_point: number;
  created_at_ms: number;
}

export async function insertProcessedPoint(
  db: SQLiteDatabase,
  pt: ProcessedPoint,
): Promise<void> {
  await db.runAsync(
    `INSERT INTO processed_points
      (id, session_id, sequence_no, timestamp, lat, lon, sog, cog,
       distance_delta, quality, reject_reason, is_gap_restart,
       gap_action, has_new_point, created_at_ms)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      pt.id, pt.session_id, pt.sequence_no, pt.timestamp, pt.lat, pt.lon,
      pt.sog, pt.cog, pt.distance_delta, pt.quality, pt.reject_reason,
      pt.is_gap_restart, pt.gap_action, pt.has_new_point, pt.created_at_ms,
    ],
  );
}

/**
 * Devuelve los processed_points de la sesion con sequence_no > cursor.
 * Lo usa el hook en modo consumidor (Fase 4).
 */
export interface ProcessedPointRow {
  id: string;
  sequence_no: number;
  timestamp: number;
  lat: number;
  lon: number;
  sog: number;
  cog: number;
  distance_delta: number;
  quality: string;
  has_new_point: number;
  accuracy: number | null;
}

export async function getProcessedPointsSince(
  db: SQLiteDatabase,
  sessionId: string,
  sinceSeq: number,
): Promise<ProcessedPointRow[]> {
  return await db.getAllAsync<ProcessedPointRow>(
    `SELECT pp.id, pp.sequence_no, pp.timestamp, pp.lat, pp.lon,
            pp.sog, pp.cog, pp.distance_delta, pp.quality,
            pp.has_new_point, gf.accuracy
     FROM processed_points pp
     LEFT JOIN gps_fixes gf
       ON gf.session_id = pp.session_id AND gf.sequence_no = pp.sequence_no
     WHERE pp.session_id = ? AND pp.sequence_no > ?
     ORDER BY pp.sequence_no ASC`,
    [sessionId, sinceSeq],
  );
}

// =========================================================================
// FASE 6 DOC 46 — Recuperacion de sesion ACTIVE al abrir la app
// =========================================================================

export interface ActiveSession {
  id: string;
  title: string | null;
  total_distance: number;
  last_processed_seq: number;
}

/**
 * Devuelve la sesion ACTIVE mas reciente, si existe.
 * Excluye TASK_TEST (esas son de modo test).
 */
export async function getActiveSession(
  db: SQLiteDatabase,
): Promise<ActiveSession | null> {
  return await db.getFirstAsync<ActiveSession>(
    `SELECT id, title, total_distance, last_processed_seq
     FROM sessions
     WHERE status = 'ACTIVE' AND (title IS NULL OR title != 'TASK_TEST')
     ORDER BY start_time DESC LIMIT 1`,
  );
}

/**
 * Devuelve los puntos con newPoint=1 de una sesion, ordenados.
 * Se usan para reconstruir el track al retomar.
 */
export interface RoutePointRow {
  sequence_no: number;
  lat: number;
  lon: number;
}

export async function getProcessedRoutePoints(
  db: SQLiteDatabase,
  sessionId: string,
): Promise<RoutePointRow[]> {
  return await db.getAllAsync<RoutePointRow>(
    `SELECT sequence_no, lat, lon
     FROM processed_points
     WHERE session_id = ? AND has_new_point = 1
     ORDER BY sequence_no ASC`,
    [sessionId],
  );
}
