#!/usr/bin/env python3
"""
Ground truth para EXP RUIDO VS GAP.

Pregunta: el ruido de posicion genera saltos >15 m entre fixes
consecutivos (dt=1 s). El tracker los trata como isGapRestart
(linea 401 de useNaveGoTracker.ts): corta la distancia y NO abre
gap_events.

Diseno (fijado en la tarea):
  - 5 min (300 s) a 5 nudos = 2.5722 m/s, recta rumbo 90.
  - SIN cut_windows: aisla el ruido. Ningun gap programado.
  - 1 Hz, misma base temporal que los GT existentes.
Salida: gt_ruido_5min_5kn.jsonl
"""
import json
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "gt_ruido_5min_5kn.jsonl")

LAT0 = -31.648
DURATION_S = 300
SPEED_KN = 5.0
SPEED_MS = SPEED_KN * 0.514444  # 2.5722 m/s
T0 = 1790279042897


def main():
    rows = []
    for i in range(DURATION_S):
        elapsed = float(i)
        x = SPEED_MS * elapsed
        rows.append({
            "timestamp": T0 + i * 1000,
            "elapsed_s": elapsed,
            "pos_x": round(x, 6),
            "pos_y": 0.0,
            "pos_z": 0.0,
            "sog_kn": SPEED_KN,
            "cog_deg": 90.0,
            "hdg_deg": 90.0,
            "roll_deg": 0.0,
            "pitch_deg": 0.0,
            "yaw_deg": 90.0,
        })
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    total = rows[-1]["pos_x"] - rows[0]["pos_x"]
    print(f"GT: {len(rows)} muestras, {DURATION_S}s, {SPEED_KN}kn "
          f"({SPEED_MS:.4f} m/s), camino real={total:.2f} m")
    print(f"Salida: {OUT}")


if __name__ == "__main__":
    main()
