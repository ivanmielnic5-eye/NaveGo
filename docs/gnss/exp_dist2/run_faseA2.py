#!/usr/bin/env python3
"""
FASE A2 - B con Doppler imperfecto.

Pregunta: el metodo B (speed x dt) daba 0% en Fase 2 porque el simulador
generaba speed perfecta. Con error de Doppler realista de celular, B sigue
siendo mejor que A?

DISENO (criterios de refutacion fijados por el Director, NO modificables):
  Trayectorias: T1_recta (5 kn), T4_lenta (1 kn), T5_variable (0..6 kn)
  sigma_speed:  0.05, 0.1, 0.2, 0.5 m/s
  Semillas:     5 por celda -> 3 x 4 x 5 = 60 corridas
  Ruido GNSS de posicion fijo en sigma=1.5 m (escenario realista de Fase 2).

METODOS
  A        : polilinea haversine con logica real de useNaveGoTracker.ts
             (gap >15 m -> reset, descarte <0.8 m).
  B        : integracion de speed x dt (rectangular, extremo derecho).
  B*       : integracion trapezoidal.
  C        : combinado: B* si v >= 1 nudo, A si v < 1 nudo (umbral del
             Director). Es el candidato de H3.

REFERENCIA (GT): polilinea de las posiciones reales del GT restringida a
los instantes reportados. Es geometrica e independiente del speed
reportado: no favorece a B.

El speed medido lo genera gnss_simulator.py con
  speed_medido = speed_real + N(0, sigma_speed), acotado a >= 0.
B y B* usan el speed MEDIDO. El GT usa posiciones reales, no speed.
"""
import json
import math
import os
import statistics
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, '..', '..', '..'))
SIM_PATH = os.path.join(ROOT, 'tools', 'gnss_simulator.py')

TRAJS = ['T1_recta', 'T4_lenta', 'T5_variable']
SIGMA_SPEED = [0.05, 0.1, 0.2, 0.5]
SEEDS = list(range(4000, 4005))
SIGMA_POS_M = 1.5
V_LENTO_KN = 1.0

KNOT_TO_MS = 1.0 / 1.94384
MAX_JUMP_DISTANCE_M = 15.0
MIN_DISTANCE_DELTA_M = 0.8


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


def method_a(fixes):
    """Replica de la logica de distancia de useNaveGoTracker.ts."""
    dist = 0.0
    n_desc = n_gap = 0
    last = None
    for f in fixes:
        if last is not None:
            d = haversine(last['latitude'], last['longitude'],
                          f['latitude'], f['longitude'])
            if d > MAX_JUMP_DISTANCE_M:
                n_gap += 1
                d = 0.0
            elif d < MIN_DISTANCE_DELTA_M:
                n_desc += 1
                d = 0.0
            dist += d
        last = f
    return dist, n_desc, n_gap


def _dt(fixes, i):
    return (fixes[i]['receivedAt'] - fixes[i - 1]['receivedAt']) / 1000.0


def method_b(fixes):
    """Integracion speed x dt, rectangular extremo derecho."""
    dist = 0.0
    for i in range(1, len(fixes)):
        dt = _dt(fixes, i)
        if dt <= 0:
            continue
        dist += (fixes[i].get('speed') or 0.0) * dt
    return dist


def method_bt(fixes):
    """Integracion trapezoidal de speed x dt."""
    dist = 0.0
    for i in range(1, len(fixes)):
        dt = _dt(fixes, i)
        if dt <= 0:
            continue
        v0 = fixes[i - 1].get('speed') or 0.0
        v1 = fixes[i].get('speed') or 0.0
        dist += (v0 + v1) / 2.0 * dt
    return dist


def method_c(fixes):
    """Combinado H3: B* si v >= 1 kn, A (geometria) si v < 1 kn.

    La decision usa la velocidad media del intervalo. Bajo 1 nudo se
    asume que el error del Doppler domina y se usa la geometria.
    """
    dist = 0.0
    last = None
    for i, f in enumerate(fixes):
        if last is not None:
            dt = _dt(fixes, i)
            v0 = last.get('speed') or 0.0
            v1 = f.get('speed') or 0.0
            v_mean_kn = ((v0 + v1) / 2.0) / KNOT_TO_MS
            if dt > 0 and v_mean_kn >= V_LENTO_KN:
                dist += (v0 + v1) / 2.0 * dt          # tramo rapido: B*
            else:
                d = haversine(last['latitude'], last['longitude'],
                              f['latitude'], f['longitude'])
                if d > MAX_JUMP_DISTANCE_M or d < MIN_DISTANCE_DELTA_M:
                    d = 0.0
                dist += d                              # tramo lento: A
        last = f
    return dist


def gt_reference(gt_pts, present_ts):
    """Ground truth geometrico sobre el tramo efectivamente reportado."""
    idx = [i for i, p in enumerate(gt_pts) if p['timestamp'] in present_ts]
    dist = 0.0
    for a, b in zip(idx, idx[1:]):
        if b == a + 1:
            dx = gt_pts[b]['pos_x'] - gt_pts[a]['pos_x']
            dz = gt_pts[b]['pos_z'] - gt_pts[a]['pos_z']
            dist += math.sqrt(dx * dx + dz * dz)
    return dist


def run_cell(traj, sigma_speed, seed, tmp_scen, tmp_fixes):
    gt_path = os.path.join(BASE, f'tray_{traj}.jsonl')
    sc = {
        'scenario_id': f'A2_{traj}_{sigma_speed}_{seed}',
        'seed': seed,
        'duration_s': 300,
        'report_interval_ms': 1000,
        'gnss': {
            'noise_sigma_m': SIGMA_POS_M,
            'speed_sigma_ms': sigma_speed,
            'latency_ms': 0,
            'cut_windows': [],
            'spikes': {'probability': 0.0, 'min_jump_m': 50, 'max_jump_m': 500},
        },
        'hydro': {'wind_strength': 0.0, 'wind_direction_deg': 0.0},
        'initial_state': {'lat': -31.648, 'lon': -60.708},
    }
    with open(tmp_scen, 'w') as f:
        json.dump(sc, f, indent=2)

    r = subprocess.run(['python3', SIM_PATH, gt_path, tmp_scen, tmp_fixes],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'simulador fallo {traj} ss={sigma_speed} seed={seed}: {r.stderr}')

    fixes = load_jsonl(tmp_fixes)
    gt_pts = load_jsonl(gt_path)
    present = set(f['measuredAt'] for f in fixes)
    ref = gt_reference(gt_pts, present)
    A, n_desc, n_gap = method_a(fixes)
    B = method_b(fixes)
    Bt = method_bt(fixes)
    C = method_c(fixes)
    row = {'tray': traj, 'sigma_speed': sigma_speed, 'seed': seed, 'gt_ref_m': ref,
           'A_m': A, 'B_m': B, 'Bt_m': Bt, 'C_m': C,
           'n_desc': n_desc, 'n_gap': n_gap, 'n_fixes': len(fixes)}
    for name, val in (('A', A), ('B', B), ('Bt', Bt), ('C', C)):
        er = (val - ref) / ref * 100.0
        row[f'er_{name}'] = er
        row[f'abs_{name}'] = abs(er)
    return row


def mean(xs):
    return statistics.mean(xs) if xs else float('nan')


def main():
    tmp_scen = os.path.join(BASE, '_tmp_scen_a2.json')
    tmp_fixes = os.path.join(BASE, '_tmp_fixes_a2.jsonl')
    results = []
    for traj in TRAJS:
        for ss in SIGMA_SPEED:
            for seed in SEEDS:
                results.append(run_cell(traj, ss, seed, tmp_scen, tmp_fixes))

    lines = []
    p = lines.append
    p('=== FASE A2: ERROR RELATIVO (%) TRAZA x sigma_speed (media 5 semillas) ===')
    p(f'sigma_pos={SIGMA_POS_M} m fijo. A=polilinea, B=speed*dt rect, '
      f'B*=trapezoidal, C=combinado (B* si v>=1kn, A si v<1kn)')
    p('')
    p(f'{"trayectoria":14s} {"ss(m/s)":>7s} {"ref_m":>8s} '
      f'{"A%":>8s} {"B%":>8s} {"B*%":>8s} {"C%":>8s} '
      f'{"|A|%":>8s} {"|B|%":>8s} {"|C|%":>8s}')
    for traj in TRAJS:
        for ss in SIGMA_SPEED:
            cell = [r for r in results if r['tray'] == traj and r['sigma_speed'] == ss]
            p(f'{traj:14s} {ss:7.2f} {mean([c["gt_ref_m"] for c in cell]):8.2f} '
              f'{mean([c["er_A"] for c in cell]):8.2f} '
              f'{mean([c["er_B"] for c in cell]):8.2f} '
              f'{mean([c["er_Bt"] for c in cell]):8.2f} '
              f'{mean([c["er_C"] for c in cell]):8.2f} '
              f'{mean([c["abs_A"] for c in cell]):8.2f} '
              f'{mean([c["abs_B"] for c in cell]):8.2f} '
              f'{mean([c["abs_C"] for c in cell]):8.2f}')
        p('')

    p('=== VERIFICACION DE HIPOTESIS (criterios fijados) ===')
    p('')

    # H1: con sigma_speed=0.2 y T1_recta, |err B| < 10% en 4 de 5 corridas.
    h1_cell = [r for r in results if r['tray'] == 'T1_recta' and r['sigma_speed'] == 0.2]
    h1_ok = sum(1 for c in h1_cell if c['abs_B'] < 10.0)
    h1_bad = sum(1 for c in h1_cell if c['abs_B'] > 10.0)
    h1 = 'CONFIRMADA' if h1_ok >= 4 else ('REFUTADA' if h1_bad >= 2 else 'INCONCLUSA')
    p(f'H1 (T1_recta, ss=0.2, |B|<10% en 4/5): '
      f'ok={h1_ok}/5 bad={h1_bad}/5 '
      f'errores={[round(c["er_B"],3) for c in h1_cell]} -> {h1}')
    p('')

    # H2: T4_lenta (1 kn), ss=0.2, |err B| > |err A| en >= 3 de 5.
    h2_cell = [r for r in results if r['tray'] == 'T4_lenta' and r['sigma_speed'] == 0.2]
    h2_bworse = sum(1 for c in h2_cell if c['abs_B'] > c['abs_A'])
    h2 = 'CONFIRMADA' if h2_bworse >= 3 else 'REFUTADA'
    p(f'H2 (T4_lenta, ss=0.2, |B|>|A| en >=3/5): '
      f'B peor en {h2_bworse}/5 '
      f'|B|={[round(c["abs_B"],2) for c in h2_cell]} '
      f'|A|={[round(c["abs_A"],2) for c in h2_cell]} -> {h2}')
    p('')

    # H3: T5_variable, error maximo del combinado < max(A) y < max(B).
    h3_cells = {}
    for ss in SIGMA_SPEED:
        cell = [r for r in results if r['tray'] == 'T5_variable' and r['sigma_speed'] == ss]
        h3_cells[ss] = (max(c['abs_A'] for c in cell),
                        max(c['abs_B'] for c in cell),
                        max(c['abs_C'] for c in cell))
    h3_wins = sum(1 for ss, (ma, mb, mc) in h3_cells.items()
                  if mc < ma and mc < mb)
    h3 = 'CONFIRMADA' if h3_wins >= 4 else ('REFUTADA' if h3_wins <= 1 else 'INCONCLUSA')
    p(f'H3 (T5_variable, max|C| < max|A| y < max|B| por celda): '
      f'cumple en {h3_wins}/4 celdas -> {h3}')
    for ss in SIGMA_SPEED:
        ma, mb, mc = h3_cells[ss]
        p(f'    ss={ss:4.2f}  max|A|={ma:8.2f}  max|B|={mb:8.2f}  max|C|={mc:8.2f}')
    p('')

    for tmp in (tmp_scen, tmp_fixes):
        if os.path.exists(tmp):
            os.remove(tmp)

    with open(os.path.join(BASE, 'resultados_faseA2.json'), 'w') as f:
        json.dump({'results': results}, f, indent=2)

    report = '\n'.join(lines)
    print(report)
    with open(os.path.join(BASE, 'salida_faseA2.txt'), 'w') as f:
        f.write(report + '\n')
    print(f'\n[{len(results)} corridas] -> resultados_faseA2.json / salida_faseA2.txt')


if __name__ == '__main__':
    main()
