// db/journal.ts
import type { SQLiteDatabase } from 'expo-sqlite';
import type { GPSFix } from '../types/journal';

/**
 * Inicia una nueva sesión de navegación y devuelve su ID.
 */
export async function startSession(
  db: SQLiteDatabase,
  title?: string
): Promise<string> {
  const sessionId = `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  await db.runAsync(
    `INSERT INTO sessions (id, start_time, title, total_distance, status)
     VALUES (?, ?, ?, 0, 'ACTIVE')`,
    [sessionId, Date.now(), title ?? 'Sesión NaveGo']
  );
  return sessionId;
}

/**
 * Inserta un fix GPS crudo en la base, sin modificar ni sobrescribir nada.
 */
export async function insertGpsFix(db: SQLiteDatabase, fix: GPSFix): Promise<void> {
  const id = typeof fix.id === 'string' && fix.id.length > 0
    ? fix.id
    : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  const sessionId = fix.session_id ?? '';
  const sequenceNo = Number.isFinite(fix.sequence_no) ? Math.floor(fix.sequence_no) : 0;
  const timestamp = Number.isFinite(fix.timestamp) ? Math.floor(fix.timestamp) : Date.now();
  const latRaw = Number.isFinite(fix.lat_raw) ? fix.lat_raw : 0;
  const lonRaw = Number.isFinite(fix.lon_raw) ? fix.lon_raw : 0;
  const alt = (fix.alt !== undefined && fix.alt !== null && Number.isFinite(fix.alt))
    ? Number(fix.alt) : null;
  const accuracy = (fix.accuracy !== undefined && fix.accuracy !== null && Number.isFinite(fix.accuracy))
    ? Number(fix.accuracy) : null;
  const speed = (fix.speed !== undefined && fix.speed !== null && Number.isFinite(fix.speed))
    ? Number(fix.speed) : null;
  const heading = (fix.heading !== undefined && fix.heading !== null && Number.isFinite(fix.heading))
    ? Number(fix.heading) : null;
  const quality = (fix.quality === 'GOOD' || fix.quality === 'SUSPECT' || fix.quality === 'REJECTED')
    ? fix.quality : 'SUSPECT';
const satellites = (typeof fix.satellites === 'number' && Number.isFinite(fix.satellites))
  ? Math.floor(fix.satellites)
  : 0;
  await db.runAsync(
    `INSERT INTO gps_fixes
      (id, session_id, sequence_no, timestamp, lat_raw, lon_raw, alt,
       accuracy, speed, heading, quality, satellites)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      id,
      sessionId,
      sequenceNo,
      timestamp,
      latRaw,
      lonRaw,
      alt,
      accuracy,
      speed,
      heading,
      quality,
      satellites,
    ]
  );
}

/**
 * Finaliza una sesión y guarda la distancia total.
 */
export async function endSession(
  db: SQLiteDatabase,
  sessionId: string,
  totalDistance: number
): Promise<void> {
  await db.runAsync(
    `UPDATE sessions SET end_time = ?, total_distance = ?, status = 'COMPLETED' WHERE id = ?`,
    [Date.now(), totalDistance, sessionId]
  );
}

/**
 * Obtiene todos los fixes de una sesión, ordenados por secuencia.
 */
export async function getSessionFixes(
  db: SQLiteDatabase,
  sessionId: string
): Promise<GPSFix[]> {
  const rows = await db.getAllAsync<GPSFix>(
    `SELECT * FROM gps_fixes WHERE session_id = ? ORDER BY sequence_no ASC`,
    [sessionId]
  );
  return rows;
}

/**
 * Obtiene todas las sesiones registradas.
 */
export async function getAllSessions(db: SQLiteDatabase): Promise<any[]> {
  return await db.getAllAsync<any>(`SELECT * FROM sessions ORDER BY start_time DESC`);
}