#!/usr/bin/env python3
"""
PASO 3/4 — TEST P1: rutas de referencia no deben sumar el tramo del gap.

Corre el CODIGO REAL de db/journal.ts contra una DB SQLite real.

Como corre:
  1. Compila db/journal.ts y types/journal.ts a JS con tsc
     (--module commonjs, outDir build_test/). El import de
     'expo-sqlite' es solo de tipo y se elimina al compilar.
  2. Arma la DB desde fixture.json (schema minimo: sessions,
     gps_fixes, gap_events, reference_routes, reference_route_points).
  3. Llama createReferenceRouteFromSession(db, SESSION, name).
  4. Compara distance_m de la ruta contra la distancia de la sesion.

Criterio (H3/H4):
  - Bug presente (pre-Fix A): reference_distance != session y
    reference_distance - session ~ avance del gap  => RED.
  - Fix A aplicado: |reference - session| <= residuo de borde
    (ruido/alineacion)                           => GREEN.

Uso:  python3 test_ref_route_no_gap.py
Exit: 0 = GREEN, 1 = RED.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))

# Residuo de borde tolerado: redondeo + efecto de alineacion de ventana
# del gap (documentado en INFORME_GAPS_AVANCE.md H2: +6.8/+7.4/+7.3 m).
# El bug aporta ~30 m (avance del gap); el residuo sano es < 8 m.
TOLERANCE_M = 8.0


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def compile_journal(outdir):
    """Compila db/journal.ts -> outdir/db/journal.js con tsc."""
    tsc = os.path.join(ROOT, "node_modules", ".bin", "tsc")
    if not os.path.exists(tsc):
        print("STOP: no se encontro tsc en node_modules/.bin", file=sys.stderr)
        sys.exit(2)
    sh([tsc,
        "--module", "commonjs",
        "--target", "es2019",
        "--moduleResolution", "node",
        "--esModuleInterop",
        "--skipLibCheck",
        "--outDir", outdir,
        "--rootDir", ROOT,
        os.path.join(ROOT, "db", "journal.ts")])
    out = os.path.join(outdir, "db", "journal.js")
    if not os.path.exists(out):
        print(f"STOP: tsc no genero {out}", file=sys.stderr)
        sys.exit(2)
    return out


RUNNER = r"""
const { DatabaseSync } = require('node:sqlite');
const fs = require('fs');
const journal = require(process.argv[2]);   // db/journal.js compilado
const fixture = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));

const db = new DatabaseSync(':memory:');
db.exec(`
  PRAGMA foreign_keys = ON;
  CREATE TABLE sessions (
    id TEXT PRIMARY KEY NOT NULL, start_time INTEGER NOT NULL,
    end_time INTEGER, title TEXT, total_distance REAL DEFAULT 0,
    status TEXT DEFAULT 'ACTIVE');
  CREATE TABLE gps_fixes (
    id TEXT PRIMARY KEY NOT NULL, session_id TEXT NOT NULL,
    sequence_no INTEGER NOT NULL, timestamp INTEGER NOT NULL,
    lat_raw REAL NOT NULL, lon_raw REAL NOT NULL, alt REAL,
    accuracy REAL, speed REAL, heading REAL, quality TEXT NOT NULL,
    satellites INTEGER DEFAULT 0, received_at_ms INTEGER,
    source TEXT DEFAULT 'GNSS',
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE);
  CREATE TABLE gap_events (
    id TEXT PRIMARY KEY NOT NULL, session_id TEXT NOT NULL,
    start_fix_id TEXT NOT NULL, end_fix_id TEXT,
    start_at_ms INTEGER NOT NULL, end_at_ms INTEGER,
    detected_at_ms INTEGER NOT NULL, duration_ms INTEGER,
    last_observed_sog_mps REAL, last_observed_cog_deg REAL,
    last_observed_accuracy_m REAL,
    status TEXT NOT NULL DEFAULT 'OPEN', reason TEXT NOT NULL DEFAULT 'GNSS_TIMEOUT',
    created_at_ms INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL);
  CREATE TABLE reference_routes (
    id TEXT PRIMARY KEY NOT NULL, name TEXT NOT NULL,
    source_session_id TEXT, distance_m REAL DEFAULT 0,
    duration_s INTEGER DEFAULT 0, created_at INTEGER NOT NULL);
  CREATE TABLE reference_route_points (
    route_id TEXT NOT NULL, sequence_no INTEGER NOT NULL,
    lat REAL NOT NULL, lon REAL NOT NULL,
    PRIMARY KEY (route_id, sequence_no),
    FOREIGN KEY (route_id) REFERENCES reference_routes(id) ON DELETE CASCADE);
`);

// Adaptador async sobre node:sqlite (misma interfaz que expo-sqlite).
const wrap = {
  runAsync: async (sql, params = []) => db.prepare(sql).run(...params),
  getAllAsync: async (sql, params = []) => db.prepare(sql).all(...params),
  getFirstAsync: async (sql, params = []) => db.prepare(sql).get(...params) ?? null,
  execAsync: async (sql) => db.exec(sql),
  withExclusiveTransactionAsync: async (fn) => fn(wrap),
};

(async () => {
  const s = fixture.session;
  await wrap.runAsync(
    `INSERT INTO sessions (id,start_time,end_time,title,total_distance,status)
     VALUES (?,?,?,?,?,?)`,
    [s.id, s.start_time, s.end_time, s.title, s.total_distance, s.status]);

  for (const f of fixture.fixes) {
    await wrap.runAsync(
      `INSERT INTO gps_fixes
       (id,session_id,sequence_no,timestamp,lat_raw,lon_raw,alt,accuracy,
        speed,heading,quality,satellites,received_at_ms,source)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
      [f.id, f.session_id, f.sequence_no, f.timestamp, f.lat_raw, f.lon_raw,
       f.alt ?? null, f.accuracy ?? null, f.speed ?? null, f.heading ?? null,
       f.quality, f.satellites ?? 0, f.received_at_ms ?? null, f.source ?? 'GNSS']);
  }
  for (const g of fixture.gap_events) {
    await wrap.runAsync(
      `INSERT INTO gap_events
       (id,session_id,start_fix_id,end_fix_id,start_at_ms,end_at_ms,
        detected_at_ms,duration_ms,status,reason,created_at_ms,updated_at_ms)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`,
      [g.id, s.id, g.start_fix_id, g.end_fix_id ?? null, g.start_at_ms,
       g.end_at_ms ?? null, g.detected_at_ms, g.duration_ms ?? null,
       g.status, 'GNSS_TIMEOUT', g.detected_at_ms, g.detected_at_ms]);
  }

  const routeId = await journal.createReferenceRouteFromSession(
    wrap, s.id, 'Fixture P1');
  const route = await wrap.getFirstAsync(
    'SELECT distance_m FROM reference_routes WHERE id = ?', [routeId]);
  const pts = await wrap.getAllAsync(
    'SELECT COUNT(*) n FROM reference_route_points WHERE route_id = ?', [routeId]);

  const reference = route.distance_m;
  const session = s.total_distance;
  const divergence = reference - session;
  const gapAdvance = fixture.expected.gap_advance_gt_m;
  const absDiv = Math.abs(divergence);

  console.log(JSON.stringify({
    reference_distance_m: Number(reference.toFixed(3)),
    session_distance_m: Number(session.toFixed(3)),
    divergence_m: Number(divergence.toFixed(3)),
    abs_divergence_m: Number(absDiv.toFixed(3)),
    gap_advance_gt_m: gapAdvance,
    n_points: pts.n,
    tolerance_m: Number(process.argv[4]),
  }));
})();
"""


def main():
    tmp = tempfile.mkdtemp(prefix="p1_test_")
    try:
        journal_js = compile_journal(tmp)
        runner = os.path.join(tmp, "runner.js")
        with open(runner, "w") as f:
            f.write(RUNNER)
        fixture = os.path.join(BASE, "fixture.json")
        r = sh(["node", runner, journal_js, fixture, str(TOLERANCE_M)])
        res = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(json.dumps(res, indent=2))

    # H3/H4: con el bug, reference supera a session en ~avance del gap.
    bug_present = res["abs_divergence_m"] > TOLERANCE_M

    if bug_present:
        print(f"\nRED: divergencia {res['divergence_m']:+.3f} m "
              f"(> tolerancia {TOLERANCE_M} m). Bug presente.")
        return 1
    print(f"\nGREEN: divergencia {res['divergence_m']:+.3f} m "
          f"(<= tolerancia {TOLERANCE_M} m). Gap no sumado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
