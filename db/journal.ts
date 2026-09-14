// db/journal.ts
import type { SQLiteDatabase } from 'expo-sqlite';
import type { GPSFix } from '../types/journal';

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

  await db.runAsync(
    `INSERT INTO gps_fixes
      (id, session_id, sequence_no, timestamp, lat_raw, lon_raw, alt,
       accuracy, speed, heading, quality, satellites)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      id, sessionId, sequenceNo, timestamp, latRaw, lonRaw, alt,
      accuracy, speed, heading, quality, satellites,
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

  let distance = 0;
  for (let i = 1; i < fixes.length; i++) {
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