#!/usr/bin/env python3
"""Prueba de integración GT-GNSS con virada sintética, sin ruido."""

import json
import math
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "docs/gnss/v2/gtgen"))

from gen_traj import gen_virada_5kn_90_150s
from gnss_simulator import run

def test_integration():
    lat0, lon0 = -31.648, -60.708
    rows, _ = gen_virada_5kn_90_150s(seed=0)

    with tempfile.TemporaryDirectory(prefix="gnss-enu-") as tmp:
        tmp = Path(tmp)
        gt, scenario_path, out = (
            tmp / "gt.jsonl",
            tmp / "scenario.json",
            tmp / "fixes.jsonl",
        )

        gt.write_text(
            "".join(json.dumps(r) + "\n" for r in rows),
            encoding="utf-8",
        )
        scenario = {
            "seed": 0,
            "report_interval_ms": 1000,
            "gnss": {
                "noise_sigma_m": 0.0,
                "latency_ms": 0,
                "cut_windows": [],
                "spikes": {
                    "probability": 0,
                    "min_jump_m": 0,
                    "max_jump_m": 0,
                },
            },
            "initial_state": {"lat": lat0, "lon": lon0},
        }
        scenario_path.write_text(json.dumps(scenario), encoding="utf-8")
        run(str(gt), str(scenario_path), str(out))

        fixes = [
            json.loads(line)
            for line in out.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(fixes) == len(rows) == 300

        for i, (g, f) in enumerate(zip(rows, fixes)):
            expected_lat = lat0 + g["pos_y"] / 110540.0
            expected_lon = lon0 + g["pos_x"] / (
                111320.0 * math.cos(math.radians(lat0))
            )
            assert abs(f["latitude"] - expected_lat) < 1e-12, (
                f"Latitud incorrecta en t={i}"
            )
            assert abs(f["longitude"] - expected_lon) < 1e-12, (
                f"Longitud incorrecta en t={i}"
            )
            assert f["heading"] == g["cog_deg"], (
                f"Rumbo incorrecto en t={i}"
            )

        assert fixes[200]["latitude"] < lat0

    print("PASS: 300 puntos GT-GNSS")
    print("PASS: latitud, longitud y rumbo")
    print("PASS: desplazamiento Sur reflejado en latitud")
    print("PASS: archivos temporales eliminados")

if __name__ == "__main__":
    test_integration()
    print("RESULTADO: integración GT-GNSS aprobada")
