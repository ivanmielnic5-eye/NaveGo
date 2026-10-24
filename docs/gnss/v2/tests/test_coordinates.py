#!/usr/bin/env python3
"""Pruebas ENU del GT y el simulador. No genera datasets."""

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "docs/gnss/v2/gtgen"))

import gen_traj
from gen_traj import (
    KNOT_TO_MS,
    gen_recta_const_5kn,
    gen_virada_5kn_90_150s,
)
from gnss_simulator import meters_to_latlon

TOL = 5e-6
LAT0 = -31.648


def check_step(rows, i):
    a, b = rows[i], rows[i + 1]
    theta = math.radians(a["cog_deg"])
    speed = a["sog_kn"] * KNOT_TO_MS
    dx, dy = b["pos_x"] - a["pos_x"], b["pos_y"] - a["pos_y"]
    assert abs(dx - speed * math.sin(theta)) <= TOL, f"dx en t={i}"
    assert abs(dy - speed * math.cos(theta)) <= TOL, f"dy en t={i}"


def geographic_cardinals():
    for x, y, lat_sign, lon_sign in (
        (10, 0, 0, 1), (-10, 0, 0, -1),
        (0, 10, 1, 0), (0, -10, -1, 0),
    ):
        dlat, dlon = meters_to_latlon(x, y, LAT0)
        assert (dlat == 0 if lat_sign == 0 else dlat * lat_sign > 0)
        assert (dlon == 0 if lon_sign == 0 else dlon * lon_sign > 0)


def gt_cardinals():
    east, _ = gen_recta_const_5kn(0)
    north, _ = gen_virada_5kn_90_150s(
        0, turn_start_s=0, turn_duration_s=1, angle_deg=-90
    )
    south, _ = gen_virada_5kn_90_150s(
        0, turn_start_s=0, turn_duration_s=1, angle_deg=90
    )
    west, _ = gen_virada_5kn_90_150s(
        0, turn_start_s=0, turn_duration_s=1, angle_deg=180
    )
    for name, rows, heading in (
        ("Este", east, 90), ("Norte", north, 0),
        ("Sur", south, 180), ("Oeste", west, 270),
    ):
        assert rows[1]["cog_deg"] == heading, name
        check_step(rows, 1)


def complete_turn():
    rows, meta = gen_virada_5kn_90_150s(0)
    assert meta["events"][-1] == {
        "type": "turn", "t_start_s": 140,
        "t_end_s": 160, "angle_deg": 90.0,
    }
    assert rows[140]["cog_deg"] == 90
    assert rows[160]["cog_deg"] == 180
    assert all(r["cog_deg"] == r["hdg_deg"] for r in rows)
    for i in range(len(rows) - 1):
        check_step(rows, i)


def phase_a_unchanged():
    count = 0
    for name in gen_traj.PHASE_A_TRAJS:
        rows, _ = gen_traj.TRAJECTORIES[name](0)
        for r in rows:
            assert r["pos_y"] == r["pos_z"] == 0, name
            assert meters_to_latlon(r["pos_x"], r["pos_z"], LAT0) == (
                meters_to_latlon(r["pos_x"], r["pos_y"], LAT0)
            ), name
            count += 1
    assert count == 900, f"Puntos examinados: {count}"


def simulator_wiring():
    source = (ROOT / "tools/gnss_simulator.py").read_text()
    assert 'meters_to_latlon(m["pos_x"], m["pos_y"], lat0)' in source


TESTS = [
    ("cardinales geográficos", geographic_cardinals),
    ("cardinales del GT", gt_cardinals),
    ("todos los intervalos de la virada", complete_turn),
    ("compatibilidad de Fase A (900 puntos)", phase_a_unchanged),
    ("conexión GT-GNSS", simulator_wiring),
]

if __name__ == "__main__":
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print("PASS", name)
        except Exception as exc:
            failed += 1
            print("FAIL", name, "-", repr(exc))
    print(f"RESULTADO: {len(TESTS) - failed}/{len(TESTS)} pruebas aprobadas")
    if failed:
        raise SystemExit(1)
