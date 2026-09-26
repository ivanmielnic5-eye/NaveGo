#!/usr/bin/env python3
"""
PASO 1 — FIXTURE para el Fix P1 (rutas de referencia suman gaps).

Problema 1: `createReferenceRouteFromSession` (db/journal.ts:115-123)
suma haversine entre TODOS los fixes consecutivos, incluido el par
pre-gap / post-gap. El tracker, en cambio, corta ese salto
(`MAX_JUMP_DISTANCE_M=15` -> isGapRestart, incremento=0). Resultado:
la distancia de la ruta de referencia > distancia de la sesion.

Este generador NO modifica nada: usa evidencia ya congelada del
experimento `exp_gaps_avance` (simulador real, semilla fija) y produce
un fixture JSON con: session, fixes y gap_events (start_fix_id /
end_fix_id), calculando:
  - session_distance  = suma del tracker (con corte de gap)
  - reference_distance = suma ingenua de journal.ts (SIN corte) => bug
  - gap_advance        = avance real durante el gap (ground truth)

Uso:  python3 gen_fixture.py
Salida: fixture.json
"""
import json
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))
GAPS_DIR = os.path.abspath(os.path.join(BASE, "..", "exp_gaps_avance"))

# Escenario base: corte corto, semilla fija, sigma=1.0 (aisla el gap del ruido).
SCENARIO = "gap_corto_10s_30m"
SEED = 7000
SIGMA_TAG = "sigma1.0"
TRAJ = "tray_gap_corto_10s_30m.jsonl"
FIXES = f"fixes_{SCENARIO}_{SIGMA_TAG}_S{SEED}.jsonl"

# Constantes replicadas de useNaveGoTracker.ts
MAX_JUMP_DISTANCE_M = 15.0
MAX_ACCURACY_M = 20.0
MIN_DISTANCE_DELTA_M = 0.8
GNSS_DEGRADED_AFTER_MS = 2000
WATCHDOG_INTERVAL_MS = 1000


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dLon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def load_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def build_session(fixes):
    """Replica del loop de grabacion del tracker: devuelve fixes con id,
    distancia de sesion (con corte de gap) y los gap_events detectados."""
    session_fixes = []
    gaps = []
    session_distance = 0.0
    last_point = None
    last_fix_ts = None
    last_fix_id = None
    open_gap_id = None

    def watchdog_tick(now_ms):
        nonlocal open_gap_id
        if (open_gap_id is None and last_fix_id is not None
                and last_fix_ts is not None
                and now_ms - last_fix_ts > GNSS_DEGRADED_AFTER_MS):
            gap_id = f"gap_{now_ms}"
            open_gap_id = gap_id
            gaps.append({
                "id": gap_id,
                "start_fix_id": last_fix_id,
                "start_at_ms": last_fix_ts,
                "detected_at_ms": now_ms,
                "status": "OPEN",
            })

    prev_recv = None
    seq = 0
    for f in fixes:
        if prev_recv is not None:
            t = prev_recv + WATCHDOG_INTERVAL_MS
            while t <= f["receivedAt"]:
                watchdog_tick(t)
                t += WATCHDOG_INTERVAL_MS
        prev_recv = f["receivedAt"]

        current_ts = f["receivedAt"]
        lat, lon = f["latitude"], f["longitude"]
        accuracy = f["accuracy"]
        fix_id = f"fix_{f['receivedAt']}"
        last_fix_id = fix_id
        last_fix_ts = current_ts

        if open_gap_id is not None:
            g = next(x for x in gaps if x["id"] == open_gap_id)
            g["end_fix_id"] = fix_id
            g["end_at_ms"] = current_ts
            g["duration_ms"] = max(0, current_ts - g["start_at_ms"])
            g["status"] = "CLOSED"
            open_gap_id = None

        session_fixes.append({
            "id": fix_id,
            "session_id": "SESSION_FIXTURE_P1",
            "sequence_no": seq,
            "timestamp": current_ts,
            "lat_raw": lat,
            "lon_raw": lon,
            "accuracy": accuracy,
            "speed": f.get("speed"),
            "heading": f.get("heading"),
            "quality": "GOOD" if accuracy <= 10 else ("SUSPECT" if accuracy <= 50 else "REJECTED"),
            "received_at_ms": current_ts,
            "source": "REPLAY",
        })
        seq += 1

        if accuracy > MAX_ACCURACY_M:
            continue

        distance_increment = 0.0
        if last_point is not None:
            distance_increment = haversine(
                last_point["lat"], last_point["lon"], lat, lon)

        is_gap_restart = False
        if distance_increment > MAX_JUMP_DISTANCE_M:
            is_gap_restart = True
            distance_increment = 0.0

        if (not is_gap_restart and distance_increment < MIN_DISTANCE_DELTA_M
                and last_point is not None):
            continue

        last_point = {"lat": lat, "lon": lon}
        session_distance += distance_increment

    return session_fixes, gaps, session_distance


def naive_reference_distance(fixes):
    """Copia literal de db/journal.ts:115-123 (fuente del bug)."""
    distance = 0.0
    for i in range(1, len(fixes)):
        distance += haversine(
            fixes[i - 1]["lat_raw"], fixes[i - 1]["lon_raw"],
            fixes[i]["lat_raw"], fixes[i]["lon_raw"])
    return distance


def main():
    fixes = load_jsonl(os.path.join(GAPS_DIR, FIXES))
    gt = load_jsonl(os.path.join(GAPS_DIR, TRAJ))

    session_fixes, gaps, session_distance = build_session(fixes)
    reference_distance = naive_reference_distance(session_fixes)

    # avance real durante el gap (ground truth, recta => desplazamiento).
    # gt.elapsed_s es relativo a su propio inicio, no epoch: convertir.
    if gaps:
        g = gaps[0]
        gt0_ms = gt[0]["timestamp"]
        s = (g["start_at_ms"] - gt0_ms) / 1000.0
        e = (g["end_at_ms"] - gt0_ms) / 1000.0
        gap_pts = [r for r in gt if s <= r["elapsed_s"] <= e]
        gap_advance = abs(gap_pts[-1]["pos_x"] - gap_pts[0]["pos_x"]) if gap_pts else None
    else:
        gap_advance = None

    divergence = reference_distance - session_distance

    fixture = {
        "meta": {
            "purpose": "P1: rutas de referencia suman gaps (Fix A)",
            "source_scenario": SCENARIO,
            "seed": SEED,
            "sigma_tag": SIGMA_TAG,
            "note": "sesion reconstruida replicando useNaveGoTracker.ts; "
                    "reference_distance = copia literal de journal.ts (naive)",
        },
        "session": {
            "id": "SESSION_FIXTURE_P1",
            "start_time": session_fixes[0]["timestamp"] if session_fixes else 0,
            "end_time": session_fixes[-1]["timestamp"] if session_fixes else 0,
            "title": "Fixture P1",
            "total_distance": round(session_distance, 6),
            "status": "COMPLETED",
        },
        "fixes": session_fixes,
        "gap_events": gaps,
        "expected": {
            "session_distance_m": round(session_distance, 3),
            "reference_distance_naive_m": round(reference_distance, 3),
            "divergence_m": round(divergence, 3),
            "gap_advance_gt_m": round(gap_advance, 3) if gap_advance is not None else None,
            "n_fixes": len(session_fixes),
            "n_gaps": len(gaps),
        },
    }

    out = os.path.join(BASE, "fixture.json")
    with open(out, "w") as f:
        json.dump(fixture, f, indent=2)

    print(f"Fixture: {out}")
    print(f"  fixes: {len(session_fixes)}  gaps: {len(gaps)}")
    print(f"  session_distance          = {session_distance:.3f} m")
    print(f"  reference_distance (naive)= {reference_distance:.3f} m")
    print(f"  divergencia               = {divergence:.3f} m")
    print(f"  avance real del gap (GT)  = {gap_advance:.3f} m"
          if gap_advance is not None else "  avance gap: n/a")


if __name__ == "__main__":
    main()
