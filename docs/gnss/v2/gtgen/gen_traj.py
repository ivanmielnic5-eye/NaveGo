#!/usr/bin/env python3
"""
Generador de trayectorias verdaderas (GT) - Componente A de V2.

Responsabilidad unica: producir un GT reproducible con sus eventos de
trayectoria. NO conoce ruido GNSS. NO conoce A/B/C.

Salidas por trayectoria:
  trajectories/gt_<traj>_<seed>.jsonl
  events/traj_events_<traj>_<seed>.json

NO ejecutar sin autorizacion explicita del Director.
"""
import json
import hashlib
import math
import os

T0 = 1790279042897
DURATION_S = 300
KNOT_TO_MS = 1.0 / 1.94384

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_GT = os.path.join(BASE, "trajectories")
OUT_EVENTS = os.path.join(BASE, "events")


def _dataset_id():
    value = os.environ.get("NAVEGO_DATASET_ID", "").strip()
    if value and (len(value) > 64 or value.startswith(".") or any(
            not (ch.isascii() and (ch.isalnum() or ch in "._-")) for ch in value)):
        raise ValueError("NAVEGO_DATASET_ID inválido; usá letras, números, punto, guion o guion bajo (máx. 64)")
    return value


def _dataset_suffix():
    value = _dataset_id()
    return ("_" + value) if value else ""


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _emit_step(elapsed_s, v_ms, cog_deg, hdg_deg, pos_x, pos_y):
    return {
        "timestamp": T0 + int(round(elapsed_s * 1000)),
        "elapsed_s": float(elapsed_s),
        "pos_x": round(pos_x, 6),
        "pos_y": round(pos_y, 6),
        "pos_z": 0.0,
        "sog_kn": round(v_ms / KNOT_TO_MS if v_ms > 0 else 0.0, 6),
        "cog_deg": float(cog_deg),
        "hdg_deg": float(hdg_deg),
        "roll_deg": 0.0,
        "pitch_deg": 0.0,
        "yaw_deg": float(hdg_deg),
    }


def gen_recta_const_5kn(seed):
    v_ms = 5.0 * KNOT_TO_MS
    rows = []
    events = [{"type": "speed_change", "t_s": 0, "v_old_ms": None,
               "v_new_ms": round(v_ms, 6)}]
    for i in range(DURATION_S):
        t = float(i)
        rows.append(_emit_step(t, v_ms, 90.0, 90.0, v_ms * t, 0.0))
    return rows, {"traj_id": "recta_const_5kn", "seed": seed,
                  "duration_s": DURATION_S, "events": events}


def gen_detencion_5kn_20s(seed, stop_start_s=200, stop_duration_s=20):
    v_ms = 5.0 * KNOT_TO_MS
    stop_end_s = stop_start_s + stop_duration_s
    rows = []
    events = [
        {"type": "speed_change", "t_s": 0, "v_old_ms": None,
         "v_new_ms": round(v_ms, 6)},
        {"type": "stop", "t_start_s": stop_start_s, "t_end_s": stop_end_s},
        {"type": "speed_change", "t_s": stop_end_s, "v_old_ms": 0.0,
         "v_new_ms": round(v_ms, 6)},
    ]
    x = 0.0
    for i in range(DURATION_S):
        t = float(i)
        v_now = 0.0 if (stop_start_s <= t < stop_end_s) else v_ms
        rows.append(_emit_step(t, v_now, 90.0, 90.0, x, 0.0))
        x += v_now
    return rows, {"traj_id": "detencion_5kn_20s", "seed": seed,
                  "duration_s": DURATION_S, "events": events}


def gen_lenta_1ms(seed):
    v_ms = 1.0
    rows = []
    events = [{"type": "speed_change", "t_s": 0, "v_old_ms": None,
               "v_new_ms": v_ms}]
    for i in range(DURATION_S):
        t = float(i)
        rows.append(_emit_step(t, v_ms, 90.0, 90.0, v_ms * t, 0.0))
    return rows, {"traj_id": "lenta_1ms", "seed": seed,
                  "duration_s": DURATION_S, "events": events}


def gen_virada_5kn_90_150s(seed, turn_start_s=140, turn_duration_s=20,
                           angle_deg=90.0):
    v_ms = 5.0 * KNOT_TO_MS
    turn_end_s = turn_start_s + turn_duration_s
    rows = []
    events = [
        {"type": "speed_change", "t_s": 0, "v_old_ms": None,
         "v_new_ms": round(v_ms, 6)},
        {"type": "turn", "t_start_s": turn_start_s, "t_end_s": turn_end_s,
         "angle_deg": angle_deg},
    ]
    x, y, hdg = 0.0, 0.0, 90.0
    for i in range(DURATION_S):
        t = float(i)
        if turn_start_s <= t < turn_end_s:
            frac = (t - turn_start_s) / turn_duration_s
            hdg = 90.0 + angle_deg * frac
        elif t >= turn_end_s:
            hdg = 90.0 + angle_deg
        rad = math.radians(hdg)
        rows.append(_emit_step(t, v_ms, hdg, hdg, x, y))
        x += v_ms * math.sin(rad)
        y += v_ms * math.cos(rad)
    return rows, {"traj_id": "virada_5kn_90_150s", "seed": seed,
                  "duration_s": DURATION_S, "events": events}


TRAJECTORIES = {
    "recta_const_5kn": gen_recta_const_5kn,
    "detencion_5kn_20s": gen_detencion_5kn_20s,
    "lenta_1ms": gen_lenta_1ms,
    "virada_5kn_90_150s": gen_virada_5kn_90_150s,
}
PHASE_A_TRAJS = ["recta_const_5kn", "detencion_5kn_20s", "lenta_1ms"]
PHASE_B_TRAJS = ["virada_5kn_90_150s"]


def write_trajectory(traj_id, seed):
    if traj_id not in TRAJECTORIES:
        raise ValueError("Trayectoria desconocida: " + traj_id)
    rows, meta = TRAJECTORIES[traj_id](seed)
    os.makedirs(OUT_GT, exist_ok=True)
    os.makedirs(OUT_EVENTS, exist_ok=True)
    dataset_id = _dataset_id()
    suffix = ("_" + dataset_id) if dataset_id else ""
    gt_path = os.path.join(OUT_GT, "gt_" + traj_id + suffix + "_" + str(seed) + ".jsonl")
    ev_path = os.path.join(OUT_EVENTS, "traj_events_" + traj_id + suffix + "_" + str(seed) + ".json")
    if os.path.exists(gt_path) or os.path.exists(ev_path):
        raise FileExistsError(
            "Se protege el dataset existente; no se sobrescribe: " + gt_path + " / " + ev_path
            + ". Usá un NAVEGO_DATASET_ID nuevo para generar otra copia."
        )
    with open(gt_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    gt_sha256 = _sha256_file(gt_path)
    generator_sha256 = _sha256_file(__file__)
    meta["dataset_id"] = dataset_id or None
    meta["provenance"] = {
        "schema_version": 1,
        "dataset_id": dataset_id or None,
        "gt_sha256": gt_sha256,
        "generator_sha256": generator_sha256,
    }
    with open(ev_path, "w") as f:
        json.dump(meta, f, indent=2)
    return gt_path, ev_path


def main(argv):
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=["A", "B"], default=None)
    p.add_argument("--traj", default=None)
    p.add_argument("--seed-start", type=int, default=8100)
    p.add_argument("--seed-end", type=int, default=8104)
    args = p.parse_args(argv)

    if args.phase:
        trajs = PHASE_A_TRAJS if args.phase == "A" else PHASE_B_TRAJS
    elif args.traj:
        trajs = [args.traj]
    else:
        p.error("Debe especificar --phase o --traj")

    for traj_id in trajs:
        for seed in range(args.seed_start, args.seed_end + 1):
            gt_path, ev_path = write_trajectory(traj_id, seed)
            print("[OK] " + traj_id + " seed=" + str(seed) + " -> " + gt_path)


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
