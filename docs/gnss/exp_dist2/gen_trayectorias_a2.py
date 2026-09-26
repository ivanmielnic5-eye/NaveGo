#!/usr/bin/env python3
"""
FASE A2 - Trayectorias adicionales para el experimento de Doppler imperfecto.

Reutiliza el integrador de gen_trayectorias.py (mismo T0, 60 Hz, mismas
unidades: pos_x/pos_z en metros, sog_kn en nudos, timestamp en ms).

T4_LENTA:  1 nudo constante. Velocidad baja: el error de speed domina.
T5_VARIABLE: 0 -> 6 -> 0.5 nudos con rampas (escala de 1 nudo incluida).
"""
import json
import os

from gen_trayectorias import generate, true_polyline_m

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DURATION_S = 300


def _speed_heading_lenta(t):
    """1 nudo constante (con arranque suave de 10 s). Rumbo 40 grados."""
    if t < 10:
        return 1.0 * t / 10.0, 40.0
    return 1.0, 40.0


def _speed_heading_variable(t):
    """Rampa 0->6 kn, crucero, baja a 0.5 kn, sube a 4 kn. Cruza 1 nudo."""
    if t < 15:
        return 0.0, 30.0
    if t < 75:                        # 0 -> 6 kn
        return 6.0 * (t - 15) / 60.0, 30.0
    if t < 135:                       # crucero 6 kn
        return 6.0, 30.0
    if t < 225:                       # 6 -> 0.5 kn (cruza 1 kn)
        return 6.0 - 5.5 * (t - 135) / 90.0, 30.0
    if t < 255:                       # crucero lento 0.5 kn
        return 0.5, 30.0
    return 0.5 + 3.5 * (t - 255) / 45.0, 30.0  # 0.5 -> 4 kn


TRAJECTORIES = {
    'T4_lenta': _speed_heading_lenta,
    'T5_variable': _speed_heading_variable,
}


def main():
    summary = {}
    for name, fn in TRAJECTORIES.items():
        samples = generate(name, fn, duration_s=DURATION_S)
        path = os.path.join(OUT_DIR, f'tray_{name}.jsonl')
        with open(path, 'w') as f:
            for s in samples:
                f.write(json.dumps(s) + '\n')
        dist = true_polyline_m(samples)
        summary[name] = dist
        print(f'{name:16s} muestras={len(samples)} dist_real={dist:9.3f} m -> {path}')
    with open(os.path.join(OUT_DIR, 'trayectorias_gt_a2.json'), 'w') as f:
        json.dump(summary, f, indent=2)


if __name__ == '__main__':
    main()
