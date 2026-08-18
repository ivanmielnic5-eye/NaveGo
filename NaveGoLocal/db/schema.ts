// db/schema.ts
import type { SQLiteDatabase } from 'expo-sqlite';

export async function initDatabase(db: SQLiteDatabase): Promise<void> {
  await db.execAsync(`
    PRAGMA journal_mode = WAL;
    PRAGMA foreign_keys = ON;
  `);

  const result = await db.getFirstAsync<{ user_version: number }>(
    'PRAGMA user_version;'
  );
  const currentVersion = result?.user_version ?? 0;

  if (currentVersion < 1) {
    await db.execAsync(`
      BEGIN TRANSACTION;

      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY NOT NULL,
        start_time INTEGER NOT NULL,
        end_time INTEGER,
        title TEXT,
        total_distance REAL DEFAULT 0,
        status TEXT DEFAULT 'ACTIVE'
      );

      CREATE TABLE IF NOT EXISTS gps_fixes (
        id TEXT PRIMARY KEY NOT NULL,
        session_id TEXT NOT NULL,
        sequence_no INTEGER NOT NULL,
        timestamp INTEGER NOT NULL,
        lat_raw REAL NOT NULL,
        lon_raw REAL NOT NULL,
        alt REAL,
        accuracy REAL,
        speed REAL,
        heading REAL,
        quality TEXT NOT NULL CHECK (quality IN ('GOOD','SUSPECT','REJECTED')),
        satellites INTEGER DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_gps_fixes_session ON gps_fixes(session_id, sequence_no);

      PRAGMA user_version = 1;
      COMMIT;
    `);
  }
}