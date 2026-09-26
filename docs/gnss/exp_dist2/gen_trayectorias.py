#!/usr/bin/env python3
"""
FASE 2 - Generador de trayectorias (ground truth) para el experimento de distancia.

Genera 3 trayectorias de 300 s a 1 Hz con posicion real (pos_x, pos_z) y
velocidad (sog_kn, cog_deg). La distancia real se calcula por la polilinea
de las posiciones, que es el ground truth geometrico independiente.

T1 RECTA:      aceleracion inicial y luego rumbo constante (sin viradas).
T2 VIRADA:     replica de la trayectoria actual de NaveGo (1 virada suave
               de +40 a -40 grados entre t=140 y t=170).
T3 ACEL_DECEL: cambios de velocidad (aceleracion, crucero, desaceleracion,
               crucero), sin viradas.

Sub-muestreo a 60 Hz para integrar posicion con precision.
"""
import json
import math
import os

OUT_DIR = 'docs/gnss/exp_dist2'
DURATION_S = 300
T0_MS = 1790279042897


def _speed_heading_recta(t):
    """Acelera 0->5 kn entre t=20 y t=40, luego rumbo fijo 40 grados."""
    if t < 20:
        return 0.0, 0.0
    if t < 40:
        return 5.0 * (t - 20) / 20.0, 40.0
    return 5.0, 40.0


def _speed_heading_virada(t):
    """Trayectoria actual: borde +40, virada suave 140-170 s, borde -40."""
    if t < 20:
        return 0.0, 0.0
    if t < 40:
        return 5.0 * (t - 20) / 20.0, 40.0
    if t < 140:
        return 5.0, 40.0
    if t < 170:
        progress = (t - 140) / 30.0
        return 5.0, 40.0 - 80.0 * progress
    return 5.0, -40.0


def _speed_heading_acel_decel(t):
    """Rumbo fijo, pero con rampa de velocidad: 0 -> 6 kn -> 2 kn -> 5 kn."""
    if t < 20:
        return 0.0, 25.0
    if t < 50:                       # acelera 0 -> 6 kn
        return 6.0 * (t - 20) / 30.0, 25.0
    if t < 120:                      # crucero rapido
        return 6.0, 25.0
    if t < 160:                      # desacelera 6 -> 2 kn
        return 6.0 - 4.0 * (t - 120) / 40.0, 25.0
    if t < 220:                      # crucero lento
        return 2.0, 25.0
    # acelera 2 -> 5 kn
    return 2.0 + 3.0 * (t - 220) / 60.0, 25.0


TRAJECTORIES = {
    'T1_recta': _speed_heading_recta,
    'T2_virada': _speed_heading_virada,
    'T3_acel_decel': _speed_heading_acel_decel,
}


def generate(name, fn, duration_s=DURATION_S):
    samples = []
    pos_x = pos_z = 0.0
    for t in range(duration_s):
        speed_kn, heading = fn(t)
        speed_ms = speed_kn / 1.94384
        rad = math.radians(heading)
        dx = speed_ms * math.sin(rad)
        dz = -speed_ms * math.cos(rad)
        for _ in range(60):
            pos_x += dx / 60.0
            pos_z += dz / 60.0
        samples.append({
            'timestamp': T0_MS + t * 1000,
            'elapsed_s': float(t),
            'pos_x': round(pos_x, 6),
            'pos_y': 0.0,
            'pos_z': round(pos_z, 6),
            'sog_kn': round(speed_kn, 4),
            'cog_deg': round(heading, 4),
            'hdg_deg': round(heading, 4),
            'roll_deg': 0.0,
            'pitch_deg': 0.0,
            'yaw_deg': round(heading, 4),
        })
    return samples


def true_polyline_m(samples):
    d = 0.0
    for i in range(1, len(samples)):
        dx = samples[i]['pos_x'] - samples[i - 1]['pos_x']
        dz = samples[i]['pos_z'] - samples[i - 1]['pos_z']
        d += math.sqrt(dx * dx + dz * dz)
    return d


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    summary = {}
    for name, fn in TRAJECTORIES.items():
        samples = generate(name, fn)
        path = os.path.join(OUT_DIR, f'tray_{name}.jsonl')
        with open(path, 'w') as f:
            for s in samples:
                f.write(json.dumps(s) + '\n')
        dist = true_polyline_m(samples)
        summary[name] = dist
        print(f'{name:16s} muestras={len(samples)} dist_real={dist:9.3f} m -> {path}')
    with open(os.path.join(OUT_DIR, 'trayectorias_gt.json'), 'w') as f:
        json.dump(summary, f, indent=2)


if __name__ == '__main__':
    main()
