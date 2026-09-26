#!/usr/bin/env python3
"""
Genera ground truth para el experimento de GAPS CON AVANCE.

Pregunta: que hace NaveGo cuando pierde senal y la embarcacion
avanza durante el gap?

Diseno (fijado en la tarea, NO modificable):
  - Gap corto  con avance chico : 10 s sin senal, avance 30 m
  - Gap medio  con avance medio : 30 s sin senal, avance 100 m
  - Gap largo  con avance grande: 60 s sin senal, avance 200 m

La embarcacion se mueve en linea recta (rumbo 90) a velocidad
constante durante TODA la corrida, incluido el gap. El receptor
deja de reportar durante la ventana de corte: el avance ocurre
realmente, solo que no se observa.

Salida: tray_GAP*.jsonl (ground truth, 1 Hz) con el mismo formato
que espera tools/gnss_simulator.py.
"""
import json
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_GT_DIR = BASE

LAT0 = -31.648
LON0 = -60.708
M_LAT = 110540.0
M_LON = 111320.0 * math.cos(math.radians(LAT0))

# Trayectoria de 240 s a 1 Hz. Gap centrado en t=120 s.
DURATION_S = 240
GAP_START_S = 110

SCENARIOS = [
    # nombre,        dur_gap_s, avance_m
    ("gap_corto_10s_30m", 10, 30.0),
    ("gap_medio_30s_100m", 30, 100.0),
    ("gap_largo_60s_200m", 60, 200.0),
]


def build_gt(dur_gap_s, avance_m):
    """Recta a velocidad constante v = avance/dur_gap, todo el tiempo."""
    v = avance_m / dur_gap_s  # m/s
    rows = []
    t0 = 1790279042897  # mismo epoch base que los GT existentes
    for i in range(DURATION_S):
        elapsed = float(i)
        x = v * elapsed
        z = 0.0
        rows.append({
            "timestamp": t0 + i * 1000,
            "elapsed_s": elapsed,
            "pos_x": round(x, 6),
            "pos_y": 0.0,
            "pos_z": round(z, 6),
            "sog_kn": round(v / 0.514444, 6),  # m/s -> nudos
            "cog_deg": 90.0,
            "hdg_deg": 90.0,
            "roll_deg": 0.0,
            "pitch_deg": 0.0,
            "yaw_deg": 90.0,
        })
    return rows


def main():
    manifest = {}
    for name, dur_gap_s, avance_m in SCENARIOS:
        rows = build_gt(dur_gap_s, avance_m)
        path = os.path.join(OUT_GT_DIR, f"tray_{name}.jsonl")
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        # distancia real total observada del camino (recta)
        total_real = rows[-1]["pos_x"] - rows[0]["pos_x"]
        manifest[name] = {
            "gt_path": path,
            "gap_start_s": GAP_START_S,
            "gap_duration_s": dur_gap_s,
            "advance_during_gap_m": avance_m,
            "speed_ms": avance_m / dur_gap_s,
            "total_real_m": total_real,
        }
        print(f"{name}: v={avance_m/dur_gap_s:.3f} m/s, "
              f"camino_total={total_real:.1f} m, gap {dur_gap_s}s "
              f"-> avance {avance_m:.0f} m")

    with open(os.path.join(OUT_GT_DIR, "gt_gap_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    main()
