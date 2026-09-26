#!/usr/bin/env python3
"""
EXP RUIDO VS GAP — el ruido de posicion se disfraza de gap?

Replica el loop de grabacion de useNaveGoTracker.ts (revision actual,
lineas citadas) y mide cuantos isGapRestart son causados por ruido
cuando NO hay ningun gap programado.

Fidelidad (identica a docs/gnss/exp_gaps_avance/run_gaps_avance.py,
que ya fue validada contra el comportamiento de la app):
  - persistRawFix ANTES del filtro de accuracy.
  - Filtro accuracy > 20 -> return.
  - distanceIncrement = haversine(lastPointRef, fix).
  - MAX_JUMP_DISTANCE_M = 15 -> isGapRestart, distanceIncrement = 0,
    el punto IGUAL se agrega al track (linea 399-405).
  - MIN_DISTANCE_DELTA_M = 0.8 -> el punto NO se agrega.
  - Watchdog: abre gap si last_fix_ts tiene >2000 ms, cada 1000 ms.

El simulador tools/gnss_simulator.py se usa SIN MODIFICAR.

NO repite el bug del watchdog en el conteo de "falsos gaps": el
watchdog solo abre gap si pasan >2 s sin fix; con dt=1 s nunca
dispara. Los falsos gaps medidos son exclusivamente isGapRestart.
"""
import json
import math
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))
SIM_PATH = os.path.join(ROOT, "tools", "gnss_simulator.py")
GT_PATH = os.path.join(BASE, "gt_ruido_5min_5kn.jsonl")

MAX_JUMP_DISTANCE_M = 15.0
MAX_ACCURACY_M = 20.0
MIN_DISTANCE_DELTA_M = 0.8
GNSS_DEGRADED_AFTER_MS = 2000
WATCHDOG_INTERVAL_MS = 1000
LATENCY_MS = 300
REPORT_INTERVAL_MS = 1000

SIGMAS = [0.5, 1.5, 3.0, 5.0]
SEEDS = [7100, 7101, 7102, 7103, 7104]
# Gap real de control: 10 s de corte, barco a 5 kn avanza ~25.7 m.
GAP_DUR_S = 10
GAP_START_S = 150
SPEED_MS = 5.0 * 0.514444
DT_UMBRAL_S = 2.0       # H2: dt > 2 s => gap real
SPEED_ZERO_MS = 0.3     # H2: speed <= 0.3 m/s => barco detenido


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


def gen_fixes(out_path, seed, sigma_m, cut_windows, spikes=None):
    """Corre el simulador real SIN modificar."""
    scenario = {
        "seed": seed,
        "duration_s": 300,
        "report_interval_ms": REPORT_INTERVAL_MS,
        "gnss": {
            "noise_sigma_m": sigma_m,
            "latency_ms": LATENCY_MS,
            "cut_windows": cut_windows,
            "spikes": spikes or {"probability": 0.0, "min_jump_m": 0,
                                 "max_jump_m": 0},
        },
        "hydro": {"wind_strength": 0.0, "wind_direction_deg": 0},
        "initial_state": {"lat": -31.648, "lon": -60.708},
        "scenario_id": f"RUIDO_sigma{sigma_m}_S{seed}",
    }
    sc_path = out_path.replace(".jsonl", "_scenario.json")
    with open(sc_path, "w") as f:
        json.dump(scenario, f, indent=2)
    subprocess.run([sys.executable, SIM_PATH, GT_PATH, sc_path, out_path],
                   check=True, capture_output=True)
    return load_jsonl(out_path)


def run_tracker(fixes):
    """Replica del loop de grabacion de useNaveGoTracker.ts.

    Devuelve ademas, por cada isGapRestart, el dt y el speed del fix
    y la distancia del fix siguiente al punto pre-salto (H3).
    """
    route_points = []
    total_distance = 0.0
    last_point = None
    last_fix_ts = None
    last_fix_id = None
    open_gap_id = None
    gaps = []
    n_jump = 0
    n_jump_real = 0        # isGapRestart con dt > umbral o speed ~0
    jump_events = []       # detalle de cada isGapRestart (ruido puro)

    def watchdog_tick(now_ms):
        nonlocal open_gap_id
        if (open_gap_id is None and last_fix_id is not None
                and last_fix_ts is not None
                and now_ms - last_fix_ts > GNSS_DEGRADED_AFTER_MS):
            gid = f"gap_{now_ms}"
            open_gap_id = gid
            gaps.append({"id": gid, "start_fix_id": last_fix_id,
                         "start_at_ms": last_fix_ts,
                         "detected_at_ms": now_ms, "status": "OPEN"})

    prev_recv = None
    for idx, f in enumerate(fixes):
        if prev_recv is not None:
            t = prev_recv + WATCHDOG_INTERVAL_MS
            while t <= f["receivedAt"]:
                watchdog_tick(t)
                t += WATCHDOG_INTERVAL_MS
        prev_recv = f["receivedAt"]

        current_ts = f["receivedAt"]
        lat, lon = f["latitude"], f["longitude"]
        accuracy = f["accuracy"]
        fix_id = f"fix_{idx}"
        dt_s = ((current_ts - last_fix_ts) / 1000.0
                if last_fix_ts is not None else None)

        last_fix_id = fix_id
        last_fix_ts = current_ts

        if open_gap_id is not None:
            g = next(x for x in gaps if x["id"] == open_gap_id)
            g["end_fix_id"] = fix_id
            g["end_at_ms"] = current_ts
            g["duration_ms"] = max(0, current_ts - g["start_at_ms"])
            g["status"] = "CLOSED"
            open_gap_id = None

        if accuracy > MAX_ACCURACY_M:
            continue

        distance_increment = 0.0
        if last_point is not None:
            distance_increment = haversine(last_point["lat"],
                                           last_point["lon"], lat, lon)

        is_gap_restart = False
        if distance_increment > MAX_JUMP_DISTANCE_M:
            n_jump += 1
            jump_speed = f.get("speed", 0.0)
            is_real_gap_like = (dt_s is not None and dt_s > DT_UMBRAL_S) or \
                               (jump_speed <= SPEED_ZERO_MS)
            if is_real_gap_like:
                n_jump_real += 1
            else:
                jump_events.append({
                    "idx": idx, "dt_s": dt_s, "jump_m": distance_increment,
                    "speed_ms": jump_speed, "speed_real_ms": SPEED_MS,
                    "accuracy_m": accuracy,
                })
            is_gap_restart = True
            distance_increment = 0.0

        if (not is_gap_restart and distance_increment < MIN_DISTANCE_DELTA_M
                and last_point is not None):
            continue

        new_point = {"lat": lat, "lon": lon, "timestamp": current_ts}
        last_point = new_point
        route_points.append(new_point)
        total_distance += distance_increment

    return {
        "route_points": route_points,
        "total_distance": total_distance,
        "gaps": gaps,
        "n_jump_rejected": n_jump,
        "n_jump_real_gap_like": n_jump_real,
        "jump_events": jump_events,
        "open_gap_at_end": open_gap_id,
    }


def measure_h3(fixes):
    """H3 directo sobre los fixes crudos: para cada salto >15 m entre
    fixes consecutivos (el que el tracker veria), mide la distancia
    del fix N+1 al fix N-1 (dos fixes despues).

    Si el salto fue ruido, N+1 vuelve cerca de N-1. Si fue gap real,
    N+1 continua lejos.
    """
    big = []
    for i in range(1, len(fixes)):
        a, b = fixes[i - 1], fixes[i]
        d = haversine(a["latitude"], a["longitude"],
                      b["latitude"], b["longitude"])
        if d <= MAX_JUMP_DISTANCE_M:
            continue
        if i + 1 < len(fixes):
            c = fixes[i + 1]
            back = haversine(a["latitude"], a["longitude"],
                             c["latitude"], c["longitude"])
        else:
            back = None
        big.append({"idx": i, "jump_m": d, "back_to_prev_m": back})
    return big


def main():
    if not os.path.exists(GT_PATH):
        print("Falta el GT. Corre gen_gt_ruido.py primero.")
        sys.exit(1)

    gt = load_jsonl(GT_PATH)
    dist_real = gt[-1]["pos_x"] - gt[0]["pos_x"]
    print(f"GT: {len(gt)} muestras, camino real={dist_real:.2f} m")
    print(f"Umbral MAX_JUMP_DISTANCE_M={MAX_JUMP_DISTANCE_M} m, "
          f"dt nominal=1 s, paso real={SPEED_MS:.3f} m\n")

    results = {"ruido": [], "gap_real": [], "resumen": {}}

    # --- Barrido de ruido, SIN gaps programados ---
    print("=== RUIDO (sin gaps programados) ===")
    for sigma in SIGMAS:
        total_falsos = 0
        detalle = []
        for seed in SEEDS:
            path = os.path.join(BASE, f"fixes_ruido_sigma{sigma}_S{seed}.jsonl")
            fixes = gen_fixes(path, seed, sigma, cut_windows=[])
            st = run_tracker(fixes)
            h3 = measure_h3(fixes)
            n = st["n_jump_rejected"]
            total_falsos += n
            detalle.append({
                "seed": seed, "n_fixes": len(fixes),
                "n_falsos_gaps": n,
                "max_jump_m": (round(max((e["jump_m"] for e in
                                          st["jump_events"]), default=0.0), 2)),
                "gaps_watchdog": len(st["gaps"]),
                "dist_app_m": round(st["total_distance"], 2),
                "error_pct": round(100.0 * (st["total_distance"] - dist_real)
                                   / dist_real, 2),
                "jumps_todos": len(h3),
                "back_to_prev_m": [round(b["back_to_prev_m"], 2)
                                   for b in h3
                                   if b["back_to_prev_m"] is not None],
            })
        results["ruido"].append({"sigma": sigma, "seeds": detalle,
                                 "total_falsos_5x5min": total_falsos})
        print(f"sigma={sigma:>4} m -> falsos gaps (5 semillas x 5 min): "
              f"{total_falsos}  | {[d['n_falsos_gaps'] for d in detalle]}")

    # --- Gap real de control ---
    print("\n=== GAP REAL (10 s programado, barco a 5 kn) ===")
    for seed in SEEDS[:3]:
        path = os.path.join(BASE, f"fixes_gapreal10s_S{seed}.jsonl")
        fixes = gen_fixes(path, seed, 1.0,
                          cut_windows=[{"start_s": GAP_START_S,
                                        "duration_s": GAP_DUR_S}])
        st = run_tracker(fixes)
        h3 = measure_h3(fixes)
        g = st["gaps"][0] if st["gaps"] else None
        results["gap_real"].append({
            "seed": seed, "n_fixes": len(fixes),
            "duration_ms": g["duration_ms"] if g else None,
            "n_jump": st["n_jump_rejected"],
            "jumps": [{"idx": b["idx"], "jump_m": round(b["jump_m"], 2),
                       "back_to_prev_m": (round(b["back_to_prev_m"], 2)
                                          if b["back_to_prev_m"] is not None
                                          else None),
                       "dt_s": round((fixes[b["idx"]]["receivedAt"]
                                      - fixes[b["idx"] - 1]["receivedAt"])
                                     / 1000.0, 2)}
                      for b in h3],
        })
        print(f"seed={seed}: gap dur={g['duration_ms'] if g else None} ms, "
              f"salto={[round(b['jump_m'],1) for b in h3]} m, "
              f"dt={[round((fixes[b['idx']]['receivedAt']-fixes[b['idx']-1]['receivedAt'])/1000.0,1) for b in h3]} s, "
              f"back_to_prev={[round(b['back_to_prev_m'],1) for b in h3 if b['back_to_prev_m'] is not None]} m")

    with open(os.path.join(BASE, "resultados_ruido_vs_gap.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("\nSalida: resultados_ruido_vs_gap.json")


if __name__ == "__main__":
    main()
