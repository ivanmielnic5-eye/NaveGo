#!/usr/bin/env python3
"""
Generador de observaciones GNSS - Componente B de V2.

Wrapper de tools/gnss_simulator.py (importado, no copiado).
Agrega: carga de traj_events, escritura de obs_events, hash del fixes.

NO ejecutar sin autorizacion explicita del Director.
"""
import hashlib
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "..", "..", "..", ".."))
SIM_PATH = os.path.join(ROOT, "tools", "gnss_simulator.py")

GT_DIR = os.path.join(BASE, "..", "gtgen", "trajectories")
TRAJ_EVENTS_DIR = os.path.join(BASE, "..", "gtgen", "events")
OUT_FIXES = os.path.join(BASE, "fixes")


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


def _sha256_json(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _gnss_tag(cfg):
    parts = ["s" + str(cfg["noise_sigma_m"])]
    if cfg.get("speed_sigma_ms", 0.0) > 0:
        parts.append("sp" + str(cfg["speed_sigma_ms"]))
    if cfg.get("cut_windows"):
        parts.append("cut")
    if cfg.get("spikes", {}).get("probability", 0.0) > 0:
        parts.append("spike")
    if cfg.get("batch_delivery_s", 0) > 0:
        parts.append("batch" + str(cfg["batch_delivery_s"]))
    if cfg.get("latency_jitter_ms", 0) > 0:
        parts.append("latjit" + str(cfg["latency_jitter_ms"]))
    return "_".join(parts)


def _extract_t0(gt_path):
    with open(gt_path) as f:
        first = json.loads(f.readline())
    return int(first["timestamp"])


def _build_scenario(traj_id, seed, cfg, initial_lat, initial_lon):
    return {
        "seed": seed,
        "duration_s": 300,
        "report_interval_ms": 1000,
        "gnss": {
            "noise_sigma_m": cfg["noise_sigma_m"],
            "latency_ms": cfg.get("latency_ms", 300),
            "latency_jitter_ms": cfg.get("latency_jitter_ms", 0),
            "cut_windows": cfg.get("cut_windows", []),
            "spikes": cfg.get("spikes",
                              {"probability": 0.0, "min_jump_m": 0, "max_jump_m": 0}),
            "speed_sigma_ms": cfg.get("speed_sigma_ms", 0.0),
            "batch_delivery_s": cfg.get("batch_delivery_s", 0),
        },
        "hydro": {"wind_strength": 0.0, "wind_direction_deg": 0},
        "initial_state": {"lat": initial_lat, "lon": initial_lon},
        "scenario_id": "V2_" + traj_id + "_" + _gnss_tag(cfg) + "_" + str(seed),
    }


def _build_obs_events(traj_id, seed, cfg, t0_ms):
    events = []
    for cut in cfg.get("cut_windows", []):
        advance_m = 2.572 * cut["duration_s"]
        events.append({"type": "cut", "start_s": cut["start_s"],
                       "duration_s": cut["duration_s"],
                       "advance_m": round(advance_m, 3)})
        events.append({"type": "missing_fix",
                       "timestamp_expected": t0_ms + int(cut["start_s"] * 1000),
                       "reason": "cut"})
    if cfg.get("spikes", {}).get("probability", 0.0) > 0:
        events.append({"type": "spike_config",
                       "probability": cfg["spikes"]["probability"],
                       "min_jump_m": cfg["spikes"]["min_jump_m"],
                       "max_jump_m": cfg["spikes"]["max_jump_m"]})
    if cfg.get("batch_delivery_s", 0) > 0:
        events.append({"type": "batch_config",
                       "period_s": cfg["batch_delivery_s"]})
    return {"traj_id": traj_id, "seed": seed, "T0_ms": t0_ms,
            "gnss_cfg": cfg, "events": events}


def gen_one(traj_id, seed, cfg, initial_lat=-31.648, initial_lon=-60.708):
    dataset_id = _dataset_id()
    suffix = ("_" + dataset_id) if dataset_id else ""
    gt_path = os.path.join(GT_DIR, "gt_" + traj_id + suffix + "_" + str(seed) + ".jsonl")
    if not os.path.exists(gt_path):
        raise FileNotFoundError("GT faltante: " + gt_path + ". Correr gen_traj.py primero.")

    gt_events_path = os.path.join(
        TRAJ_EVENTS_DIR, "traj_events_" + traj_id + suffix + "_" + str(seed) + ".json"
    )
    if not os.path.exists(gt_events_path):
        raise RuntimeError("Metadatos de procedencia GT ausentes: " + gt_events_path)
    with open(gt_events_path, encoding="utf-8") as f:
        gt_meta = json.load(f)
    gt_provenance = gt_meta.get("provenance", {})
    if gt_meta.get("traj_id") != traj_id or gt_meta.get("seed") != seed:
        raise RuntimeError("Identidad GT no coincide con trayectoria/semilla solicitadas")
    if gt_meta.get("dataset_id") != (dataset_id or None):
        raise RuntimeError("Dataset ID de GT no coincide con NAVEGO_DATASET_ID")
    if gt_provenance.get("gt_sha256") != _sha256_file(gt_path):
        raise RuntimeError("Hash GT ausente o distinto del registrado en traj_events")
    if not gt_provenance.get("generator_sha256"):
        raise RuntimeError("Hash del generador GT ausente; la procedencia no es verificable")
    tag = _gnss_tag(cfg)
    os.makedirs(OUT_FIXES, exist_ok=True)
    fixes_path = os.path.join(OUT_FIXES, "fixes_" + traj_id + suffix + "_" + tag + "_" + str(seed) + ".jsonl")
    scen_path = os.path.join(OUT_FIXES, "_scenario_" + traj_id + suffix + "_" + tag + "_" + str(seed) + ".json")
    obs_events_path = os.path.join(OUT_FIXES, "obs_events_" + traj_id + suffix + "_" + tag + "_" + str(seed) + ".json")
    if any(os.path.exists(p) for p in (fixes_path, scen_path, obs_events_path)):
        raise FileExistsError(
            "Se protege el dataset existente; no se sobrescribe: " + fixes_path
            + ". Usá un NAVEGO_DATASET_ID nuevo para generar otra copia."
        )

    scenario = _build_scenario(traj_id, seed, cfg, initial_lat, initial_lon)
    scenario["dataset_id"] = dataset_id or None
    with open(scen_path, "w") as f:
        json.dump(scenario, f, indent=2)

    r = subprocess.run([sys.executable, SIM_PATH, gt_path, scen_path, fixes_path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("Simulador fallo: " + r.stderr)

    with open(fixes_path, "rb") as f:
        fix_hash = hashlib.sha256(f.read()).hexdigest()

    t0 = _extract_t0(gt_path)
    obs_events = _build_obs_events(traj_id, seed, cfg, t0)
    obs_events["fixes_sha256"] = fix_hash
    obs_events["fixes_path"] = os.path.relpath(fixes_path, BASE)
    obs_events["dataset_id"] = dataset_id or None
    obs_events["provenance"] = {
        "schema_version": 1,
        "dataset_id": dataset_id or None,
        "gt_sha256": _sha256_file(gt_path),
        "gt_generator_sha256": gt_provenance["generator_sha256"],
        "obs_generator_sha256": _sha256_file(__file__),
        "simulator_sha256": _sha256_file(SIM_PATH),
        "effective_scenario": scenario,
        "effective_scenario_sha256": _sha256_json(scenario),
    }
    with open(obs_events_path, "w") as f:
        json.dump(obs_events, f, indent=2)

    os.remove(scen_path)

    return {"fixes_path": fixes_path, "obs_events_path": obs_events_path,
            "fix_hash": fix_hash,
            "n_fixes": sum(1 for _ in open(fixes_path))}


PHASE_A_CFGS = {
    "S1_s0_nocut":  {"noise_sigma_m": 0.0, "cut_windows": []},
    "S2_s05_nocut": {"noise_sigma_m": 0.5, "cut_windows": []},
    "S3_s15_nocut": {"noise_sigma_m": 1.5, "cut_windows": []},
    "S4_s30_nocut": {"noise_sigma_m": 3.0, "cut_windows": []},
    "S5_s50_nocut": {"noise_sigma_m": 5.0, "cut_windows": []},
    "S6_s10_cut10": {"noise_sigma_m": 1.0,
                     "cut_windows": [{"start_s": 150, "duration_s": 10}]},
    "S10_det_stop": {"noise_sigma_m": 1.5, "cut_windows": []},
    "S11_lenta":    {"noise_sigma_m": 1.5, "cut_windows": []},
    "S16_det_s30":  {"noise_sigma_m": 3.0, "cut_windows": []},
    "S17_det_s50":  {"noise_sigma_m": 5.0, "cut_windows": []},
    "S18_det_cut5": {"noise_sigma_m": 3.0,
                     "cut_windows": [{"start_s": 210, "duration_s": 5}]},
}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--traj", required=True)
    p.add_argument("--cfg", required=True, choices=list(PHASE_A_CFGS.keys()))
    p.add_argument("--seed", type=int, required=True)
    args = p.parse_args()
    info = gen_one(args.traj, args.seed, PHASE_A_CFGS[args.cfg])
    print(json.dumps(info, indent=2))
