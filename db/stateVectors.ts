import type { SQLiteDatabase } from 'expo-sqlite';
import * as Crypto from 'expo-crypto';
import type { StateVector } from '../types/evidence';

export async function insertStateVector(
  db: SQLiteDatabase,
  sv: StateVector,
  sessionId: string | null
): Promise<string> {
  const id = Crypto.randomUUID();
  await db.runAsync(
    `INSERT INTO state_vectors 
      (id, timestamp, epoch, datum, lat, lon, alt, velocity, heading, covariance, 
       quality, gps_state, source, evidence_ref_source, evidence_ref_id, session_id) 
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      id,
      sv.timestamp,
      sv.epoch,
      sv.datum,
      sv.position.lat,
      sv.position.lon,
      sv.position.alt ?? null,
      sv.velocity,
      sv.heading,
      JSON.stringify(sv.covariance),
      sv.quality,
      sv.gpsState,
      sv.source,
      sv.evidence_ref.source,
      sv.evidence_ref.id,
      sessionId,
    ]
  );
  return id;
}

export async function getLatestStateVector(
  db: SQLiteDatabase,
  sessionId: string
): Promise<StateVector | null> {
  const row = await db.getFirstAsync<any>(
    `SELECT * FROM state_vectors WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1`,
    [sessionId]
  );
  if (!row) return null;
  return {
    timestamp: row.timestamp,
    epoch: row.epoch,
    datum: row.datum,
    position: { lat: row.lat, lon: row.lon, alt: row.alt ?? undefined },
    velocity: row.velocity,
    heading: row.heading,
    covariance: JSON.parse(row.covariance),
    quality: row.quality,
    gpsState: row.gps_state,
    source: row.source,
    evidence_ref: { source: row.evidence_ref_source, id: row.evidence_ref_id },
  };
}