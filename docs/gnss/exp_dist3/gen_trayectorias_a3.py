#!/usr/bin/env python3
"""
FASE A3 - Generador de trayectorias (ground truth) para el experimento
A+Kalman vs B vs Hibrido por estado.

Reutiliza el integrador de exp_dist2/gen_trayectorias.py (mismo T0, 60 Hz,
mismas unidades: pos_x/pos_z en metros, sog_kn en nudos, timestamp en ms).

Trayectorias (las 5 del diseno del Director):
  T1_recta5     : recta a 5 nudos (referencia navegacion normal)
  T2_virada     : virada suave (la actual de NaveGo)
  T3_quieto_nav : quieto 60s + navegacion 5kn 120s + quieto 60s
  T4_garreo     : garreo: barco "parado" con micro-movimientos de +-0.5 m
  T5_variable   : velocidad variable 0 a 6 nudos (cruza el umbral 1 kn)

Duracion: 240 s (T1/T2 usan los primeros 240 s de su perfil de 300 s).
"""
import json
import math
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DURATION_S = 240
T0_MS = 1790279042897
KNOT_TO_MS = 1.0 / 1.94384


def _t1_recta5(t):
    """Acelera 0->5 kn entre t=20 y t=40, luego rumbo fijo 40 grados."""
    if t < 20:
        return 0.0, 0.0
    if t < 40:
        return 5.0 * (t - 20) / 20.0, 40.0
    return 5.0, 40.0


def _t2_virada(t):
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


def _t3_quieto_nav(t):
    """Quieto 0-60 s, navegacion 5 kn 60-180 s, quieto 180-240 s."""
    if t < 60:
        return 0.0, 40.0
    if t < 70:
        return 5.0 * (t - 60) / 10.0, 40.0   # arranque suave 10 s
    if t < 175:
        return 5.0, 40.0
    if t < 185:
        return 5.0 * (1.0 - (t - 175) / 10.0), 40.0  # frenada 10 s
    return 0.0, 40.0


def _t4_garreo(t):
    """Garreo simulado: posicion con micro-movimientos de 0.5 m.

    El barco esta amarrado/fondeado pero la posicion real oscila por
    cabeceo y por el ancla. Perfil de velocidad media ~0, desplazamiento
    real neto muy pequeno. La posicion se sintetiza en el integrador.
    """
    return 0.0, 40.0


def _t5_variable(t):
    """Rampa 0->6 kn, crucero, baja a 0.5 kn, sube a 4 kn. Cruza 1 nudo."""
    if t < 15:
        return 0.0, 30.0
    if t < 75:
        return 6.0 * (t - 15) / 60.0, 30.0
    if t < 135:
        return 6.0, 30.0
    if t < 200:
        return 6.0 - 5.5 * (t - 135) / 65.0, 30.0
    if t < 220:
        return 0.5, 30.0
    return 0.5 + 3.5 * (t - 220) / 20.0, 30.0


TRAJECTORIES = {
    'T1_recta5': _t1_recta5,
    'T2_virada': _t2_virada,
    'T3_quieto_nav': _t3_quieto_nav,
    'T4_garreo': _t4_garreo,
    'T5_variable': _t5_variable,
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
        if name == 'T4_garreo':
            # Micro-movimientos reales de +-0.5 m: ida y vuelta cada 5 s
            # (el barco no avanza; el GT refleja ese balanceo).
            phase = 2.0 * math.pi * (t % 5) / 5.0
            dx = 0.5 * math.cos(phase) * (2.0 * math.pi / 5.0)
            dz = 0.0
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
    with open(os.path.join(OUT_DIR, 'trayectorias_gt_a3.json'), 'w') as f:
        json.dump(summary, f, indent=2)


if __name__ == '__main__':
    main()
