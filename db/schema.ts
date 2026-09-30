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
  console.log('[SCHEMA] initDatabase: currentVersion =', currentVersion);

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

  if (currentVersion === 1) {
    await db.withExclusiveTransactionAsync(async (txn) => {
      const columns = await txn.getAllAsync<{ name: string }>(
        `PRAGMA table_info(gps_fixes);`
      );
      const columnNames = new Set(columns.map((c) => c.name));

      if (!columnNames.has('received_at_ms')) {
        await txn.execAsync(`ALTER TABLE gps_fixes ADD COLUMN received_at_ms INTEGER;`);
      }
      if (!columnNames.has('source')) {
        await txn.execAsync(`ALTER TABLE gps_fixes ADD COLUMN source TEXT DEFAULT 'GNSS';`);
      }

      await txn.execAsync(`
        CREATE TABLE IF NOT EXISTS gap_events (
          id TEXT PRIMARY KEY NOT NULL,
          session_id TEXT NOT NULL,
          start_fix_id TEXT NOT NULL,
          end_fix_id TEXT,
          start_at_ms INTEGER NOT NULL,
          end_at_ms INTEGER,
          detected_at_ms INTEGER NOT NULL,
          duration_ms INTEGER,
          last_observed_sog_mps REAL,
          last_observed_cog_deg REAL,
          last_observed_accuracy_m REAL,
          status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','CLOSED')),
          reason TEXT NOT NULL DEFAULT 'GNSS_TIMEOUT' CHECK (reason IN ('GNSS_TIMEOUT','INVALID_FIX','PROVIDER_UNAVAILABLE','UNKNOWN')),
          created_at_ms INTEGER NOT NULL,
          updated_at_ms INTEGER NOT NULL,
          FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
          FOREIGN KEY (start_fix_id) REFERENCES gps_fixes(id),
          FOREIGN KEY (end_fix_id) REFERENCES gps_fixes(id)
        );

        CREATE INDEX IF NOT EXISTS idx_gap_events_session ON gap_events(session_id, start_at_ms);
        CREATE INDEX IF NOT EXISTS idx_gap_events_status ON gap_events(session_id, status);
        CREATE INDEX IF NOT EXISTS idx_gps_fixes_source ON gps_fixes(session_id, source);
      `);

      await txn.execAsync(`PRAGMA user_version = 2;`);

      // Post-check: verificar que todo quedo bien aplicado
      const versionCheck = await txn.getFirstAsync<{ user_version: number }>(
        `PRAGMA user_version;`
      );
      if (versionCheck?.user_version !== 2) {
        throw new Error('[MIGRATION] post-check fallo: user_version != 2');
      }

      const gpsColumns = await txn.getAllAsync<{ name: string }>(
        `PRAGMA table_info(gps_fixes);`
      );
      const gpsColNames = new Set(gpsColumns.map((c) => c.name));
      if (!gpsColNames.has('received_at_ms') || !gpsColNames.has('source')) {
        throw new Error('[MIGRATION] post-check fallo: columnas nuevas faltantes');
      }

      const gapTable = await txn.getFirstAsync<{ name: string }>(
        `SELECT name FROM sqlite_master WHERE type='table' AND name='gap_events';`
      );
      if (!gapTable) {
        throw new Error('[MIGRATION] post-check fallo: tabla gap_events no existe');
      }

      console.log('[MIGRATION] v1 -> v2 aplicada y verificada');
    });
  }

  if (currentVersion === 2) {
    await db.withExclusiveTransactionAsync(async (txn) => {
      const columns = await txn.getAllAsync<{ name: string }>(
        `PRAGMA table_info(sessions);`
      );
      const columnNames = new Set(columns.map((c) => c.name));

      if (!columnNames.has('is_paused')) {
        await txn.execAsync(`ALTER TABLE sessions ADD COLUMN is_paused INTEGER DEFAULT 0;`);
      }
      if (!columnNames.has('last_processed_seq')) {
        await txn.execAsync(`ALTER TABLE sessions ADD COLUMN last_processed_seq INTEGER DEFAULT -1;`);
      }

      await txn.execAsync(`PRAGMA user_version = 3;`);

      // Post-check
      const versionCheck = await txn.getFirstAsync<{ user_version: number }>(
        `PRAGMA user_version;`
      );
      if (versionCheck?.user_version !== 3) {
        throw new Error('[MIGRATION] post-check fallo: user_version != 3');
      }

      const sessionColumns = await txn.getAllAsync<{ name: string }>(
        `PRAGMA table_info(sessions);`
      );
      const sessionColNames = new Set(sessionColumns.map((c) => c.name));
      if (!sessionColNames.has('is_paused') || !sessionColNames.has('last_processed_seq')) {
        throw new Error('[MIGRATION] post-check fallo: columnas nuevas en sessions faltantes');
      }

      console.log('[MIGRATION] v2 -> v3 aplicada y verificada');
    });
  } else if (currentVersion > 3) {
    throw new Error(
      '[MIGRATION] DB en version ' + currentVersion +
      ', esta app solo conoce hasta v3. Actualizar app o restaurar DB.'
    );
  }

  // ===== NUEVAS TABLAS PARA REFERENCIAS =====
  await db.execAsync(`
    CREATE TABLE IF NOT EXISTS reference_routes (
      id TEXT PRIMARY KEY NOT NULL,
      name TEXT NOT NULL,
      source_session_id TEXT,
      distance_m REAL DEFAULT 0,
      duration_s INTEGER DEFAULT 0,
      created_at INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS reference_route_points (
      route_id TEXT NOT NULL,
      sequence_no INTEGER NOT NULL,
      lat REAL NOT NULL,
      lon REAL NOT NULL,
      PRIMARY KEY (route_id, sequence_no),
      FOREIGN KEY (route_id) REFERENCES reference_routes(id) ON DELETE CASCADE
    );
  `);
}