#!/usr/bin/env python3
"""
EXP GAPS CON AVANCE — replica fiel de useNaveGoTracker.ts frente a
perdida de GNSS con la embarcacion avanzando.

Replica (lineas citadas de useNaveGoTracker.ts, revision actual):
  - [FIX] processing: updateNavigationStatus; grabacion solo si recording.
  - persistRawFix: se guarda SIEMPRE (aunque accuracy > 20).
  - closeGap se dispara al llegar un fix si openGapIdRef != null
    (lineas 370-381). closeGap usa start_at_ms = timestamp del fix
    pre-gap (journal.ts:217-236).
  - Filtro accuracy > MAX_ACCURACY_M (20) -> return (linea 384-387).
  - distanceIncrement = haversine(lastPointRef, fix) (390-397).
  - MAX_JUMP_DISTANCE_M = 15: si el salto supera 15 m -> isGapRestart,
    distanceIncrement = 0 (399-405). El punto SE AGREGA igual al track.
  - MIN_DISTANCE_DELTA_M = 0.8: si el paso es menor, el punto NO se
    agrega (linea 406).
  - routePoints es una unica lista, sin marcadores (438-449).

Watchdog: abre gap si el ultimo fix tiene > GNSS_DEGRADED_AFTER_MS
(2000 ms) de antiguedad, hay sesion, grabando, no pausado, sin gap
abierto (256-297). Se evalua cada 1000 ms.

El simulador de GNSS calcula accuracy = sigma_m * 1.5. Se usa
sigma_pos = 3.0 m -> accuracy = 4.5 m (<= 20, no descarta).
"""
import json
import math
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))
SIM_PATH = os.path.join(ROOT, "tools", "gnss_simulator.py")

# --- Constantes replicadas de useNaveGoTracker.ts ---
MAX_JUMP_DISTANCE_M = 15.0
MAX_ACCURACY_M = 20.0
MIN_DISTANCE_DELTA_M = 0.8
GNSS_DEGRADED_AFTER_MS = 2000
WATCHDOG_INTERVAL_MS = 1000

# Sigma principal = 1.0 m: aísla el efecto del GAP del ruido de posicion.
# NOTA: con sigma=3.0 m y paso de 3 m el ruido domina la suma (ver INFORME,
# seccion ruido). Se corre un barrido de sigma para separar ambos efectos.
SIGMA_POS_M = 1.0
SIGMA_SWEEP_M = [0.0, 1.0, 3.0]
LATENCY_MS = 300
REPORT_INTERVAL_MS = 1000

SCENARIOS = [
    # nombre,               dur_gap_s, avance_m, seeds
    ("gap_corto_10s_30m", 10, 30.0, [7000, 7001, 7002, 7003, 7004]),
    ("gap_medio_30s_100m", 30, 100.0, [7000, 7001, 7002, 7003, 7004]),
    ("gap_largo_60s_200m", 60, 200.0, [7000, 7001, 7002, 7003, 7004]),
]
GAP_START_S = 110


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


def gen_fixes(gt_path, out_path, seed, dur_gap_s, sigma_m=SIGMA_POS_M):
    """Corre el simulador real (tools/gnss_simulator.py) SIN modificarlo."""
    scenario = {
        "seed": seed,
        "duration_s": 240,
        "report_interval_ms": REPORT_INTERVAL_MS,
        "gnss": {
            "noise_sigma_m": sigma_m,
            "latency_ms": LATENCY_MS,
            "cut_windows": [
                {"start_s": GAP_START_S, "duration_s": dur_gap_s}
            ],
            "spikes": {"probability": 0.0, "min_jump_m": 0, "max_jump_m": 0},
        },
        "hydro": {"wind_strength": 0.0, "wind_direction_deg": 0},
        "initial_state": {"lat": -31.648, "lon": -60.708},
        "scenario_id": f"GAP_{dur_gap_s}s",
    }
    sc_path = out_path.replace(".jsonl", "_scenario.json")
    with open(sc_path, "w") as f:
        json.dump(scenario, f, indent=2)
    subprocess.run(
        [sys.executable, SIM_PATH, gt_path, sc_path, out_path],
        check=True, capture_output=True,
    )
    return load_jsonl(out_path)


def run_tracker(fixes):
    """Replica del loop de grabacion de useNaveGoTracker.ts.

    Devuelve estado final: route_points, total_distance, gaps,
    rechazados por salto, descartados por delta minimo.
    """
    route_points = []
    total_distance = 0.0
    last_point = None
    last_fix_ts = None
    last_fix_id = None
    open_gap_id = None
    gaps = []

    n_jump_rejected = 0
    n_min_delta_skipped = 0
    n_accuracy_rejected = 0
    jump_distances = []

    # El watchdog corre cada 1000 ms. Para cada fix en receivedAt,
    # primero se evaluan los ticks del watchdog ocurridos entre el
    # fix anterior y este.
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
    for f in fixes:
        # ticks del watchdog entre fixes
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

        # persistRawFix: se guarda siempre (antes del filtro de accuracy)
        last_fix_id = fix_id
        last_fix_ts = current_ts

        # closeGap si habia un gap abierto (lineas 370-381)
        if open_gap_id is not None:
            g = next(x for x in gaps if x["id"] == open_gap_id)
            g["end_fix_id"] = fix_id
            g["end_at_ms"] = current_ts
            g["duration_ms"] = max(0, current_ts - g["start_at_ms"])
            g["status"] = "CLOSED"
            open_gap_id = None

        # filtro accuracy (linea 384)
        if accuracy > MAX_ACCURACY_M:
            n_accuracy_rejected += 1
            continue

        distance_increment = 0.0
        if last_point is not None:
            distance_increment = haversine(
                last_point["lat"], last_point["lon"], lat, lon)

        is_gap_restart = False
        if distance_increment > MAX_JUMP_DISTANCE_M:
            n_jump_rejected += 1
            jump_distances.append(distance_increment)
            is_gap_restart = True
            distance_increment = 0.0

        if (not is_gap_restart and distance_increment < MIN_DISTANCE_DELTA_M
                and last_point is not None):
            n_min_delta_skipped += 1
            continue

        new_point = {"lat": lat, "lon": lon, "timestamp": current_ts}
        last_point = new_point
        route_points.append(new_point)
        total_distance += distance_increment

    return {
        "route_points": route_points,
        "total_distance": total_distance,
        "gaps": gaps,
        "n_jump_rejected": n_jump_rejected,
        "n_min_delta_skipped": n_min_delta_skipped,
        "n_accuracy_rejected": n_accuracy_rejected,
        "jump_distances": jump_distances,
        "open_gap_at_end": open_gap_id,
    }


def first_geojson_segment_analysis(route_points, gap_ref):
    """H1: busca en routePoints el par de puntos consecutivos que cruza
    el gap. Si existe tal par, la linea visual lo une -> puente recto.

    gap_ref: dict con start_at_ms / end_at_ms del gap (o None).
    Devuelve el salto maximo entre puntos consecutivos del track.
    """
    if not route_points or gap_ref is None:
        return None
    max_jump = 0.0
    max_pair = None
    for a, b in zip(route_points, route_points[1:]):
        d = haversine(a["lat"], a["lon"], b["lat"], b["lon"])
        if d > max_jump:
            max_jump = d
            max_pair = (a, b)
    return {"max_consecutive_jump_m": max_jump, "pair": max_pair}


def run_case(name, dur_gap_s, avance_m, seed, sigma_m, gt, tag):
    gt_path = os.path.join(BASE, f"tray_{name}.jsonl")
    fixes_path = os.path.join(BASE, f"fixes_{name}_{tag}_S{seed}.jsonl")
    fixes = gen_fixes(gt_path, fixes_path, seed, dur_gap_s, sigma_m)
    st = run_tracker(fixes)

    real_pts = [(r["pos_x"], r["pos_z"]) for r in gt]
    dist_real = real_pts[-1][0] - real_pts[0][0]

    gap_gt = [r for r in gt
              if GAP_START_S <= r["elapsed_s"] < GAP_START_S + dur_gap_s]
    dist_gap = (gap_gt[-1]["pos_x"] - gap_gt[0]["pos_x"]) if gap_gt else 0.0

    gap = st["gaps"][0] if st["gaps"] else None
    geo = first_geojson_segment_analysis(
        st["route_points"],
        {"start_at_ms": gap["start_at_ms"],
         "end_at_ms": gap["end_at_ms"]} if gap else None)

    return {
        "scenario": name,
        "seed": seed,
        "sigma_m": sigma_m,
        "gap_duration_s": dur_gap_s,
        "advance_gap_m": avance_m,
        "distancia_real_m": round(dist_real, 3),
        "distancia_gap_real_m": round(dist_gap, 3),
        "distancia_app_m": round(st["total_distance"], 3),
        "error_abs_m": round(st["total_distance"] - dist_real, 3),
        "error_pct": round(
            100.0 * (st["total_distance"] - dist_real) / dist_real, 4),
        "n_gaps": len(st["gaps"]),
        "gap_duration_ms": gap["duration_ms"] if gap else None,
        "gap_status": gap["status"] if gap else None,
        "gap_esperado_ms": dur_gap_s * 1000,
        "n_fixes_totales": len(fixes),
        "n_puntos_track": len(st["route_points"]),
        "n_rechazados_salto": st["n_jump_rejected"],
        "max_jump_dist_m": (round(max(st["jump_distances"]), 3)
                            if st["jump_distances"] else 0.0),
        "max_salto_consecutivo_track_m": (
            round(geo["max_consecutive_jump_m"], 3) if geo else None),
        "open_gap_al_final": st["open_gap_at_end"],
    }


def main():
    results = []
    total_runs = 0

    # --- PASADA PRINCIPAL: sigma=1.0 m, aísla el efecto del gap ---
    for name, dur_gap_s, avance_m, seeds in SCENARIOS:
        gt = load_jsonl(os.path.join(BASE, f"tray_{name}.jsonl"))
        for seed in seeds:
            total_runs += 1
            results.append(run_case(name, dur_gap_s, avance_m, seed,
                                    SIGMA_POS_M, gt, "sigma1.0"))

    # --- BARRIDO DE RUIDO: sigma 0.0 y 3.0, una semilla por escenario ---
    for sigma in [0.0, 3.0]:
        tag = f"sigma{sigma}"
        for name, dur_gap_s, avance_m, seeds in SCENARIOS:
            gt = load_jsonl(os.path.join(BASE, f"tray_{name}.jsonl"))
            total_runs += 1
            results.append(run_case(name, dur_gap_s, avance_m, seeds[0],
                                    sigma, gt, tag))

    out_path = os.path.join(BASE, "resultados_gaps_avance.json")
    with open(out_path, "w") as f:
        json.dump({"total_runs": total_runs, "results": results}, f, indent=2)

    for r in results:
        pass

    print(f"Corridas totales: {total_runs}\n")
    print(f"{'escenario':20s} {'sig':>4s} {'real_m':>7s} {'app_m':>7s} "
          f"{'err%':>7s} {'gaps':>4s} {'dur_ms':>7s} {'esp_ms':>7s} "
          f"{'salto_max':>9s} {'salto_track':>11s}")
    for r in results:
        print(f"{r['scenario']:20s} {r['sigma_m']:4.1f} "
              f"{r['distancia_real_m']:7.1f} {r['distancia_app_m']:7.1f} "
              f"{r['error_pct']:7.2f} {r['n_gaps']:4d} "
              f"{str(r['gap_duration_ms']):>7s} {r['gap_esperado_ms']:7d} "
              f"{r['max_jump_dist_m']:9.1f} "
              f"{r['max_salto_consecutivo_track_m']:11.1f}")
    print(f"\nSalida: {out_path}")


if __name__ == "__main__":
    main()
