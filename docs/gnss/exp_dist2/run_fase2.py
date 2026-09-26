#!/usr/bin/env python3
"""
FASE 2 - Experimento de distancia GNSS para NaveGo.

Pregunta: de los metodos disponibles para medir distancia, cual representa
mejor la distancia real navegada, bajo distintas trayectorias y ruido GNSS?

DISENO (criterios de refutacion fijados por el Director, NO modificables):
  Trayectorias: T1_recta, T2_virada, T3_acel_decel
  Ruido:        0.0, 0.5, 1.5, 3.0 m
  Semillas:     5 por celda  -> 3 x 4 x 5 = 60 corridas
  Sin cortes GNSS (cut_windows vacio) y sin spikes: se aisla el efecto
  del ruido y de la trayectoria, que es lo que piden H1/H2/H3.

METODOS EVALUADOS
  A  : suma polilinea de haversine entre fixes consecutivos, con la logica
       real de useNaveGoTracker.ts (reset de gap >15 m, descarte <0.8 m).
  B  : integracion de speed x dt  (rectangular, extremo derecho: v_i * dt).
  B* : integracion trapezoidal ((v_i + v_i-1)/2) * dt.
  C  : metodo combinado: elige B* cuando hay cobertura continua y usa la
       geometria de A solo donde A es fiable (ver docstring de method_c).

REFERENCIA (ground truth): polilinea de las posiciones reales del GT,
restringida a los instantes que el receptor reporto. Es geometrica e
independiente de la velocidad reportada, por lo que no favorece a B.
"""
import json
import math
import os
import statistics
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, '..', '..', '..'))
SIM_PATH = os.path.join(ROOT, 'tools', 'gnss_simulator.py')
OUT_DIR = BASE

TRAJS = ['T1_recta', 'T2_virada', 'T3_acel_decel']
SIGMAS = [0.0, 0.5, 1.5, 3.0]
SEEDS = list(range(3000, 3005))

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


# ---------------------------------------------------------------- metodos
def method_a(fixes):
    """Replica de la logica de distancia de NaveGo (useNaveGoTracker.ts)."""
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


def method_b(fixes):
    """Integracion de speed x dt, rectangular con extremo derecho (v_i)."""
    dist = 0.0
    for i in range(1, len(fixes)):
        dt = (fixes[i]['receivedAt'] - fixes[i - 1]['receivedAt']) / 1000.0
        if dt <= 0:
            continue
        dist += (fixes[i].get('speed') or 0.0) * dt
    return dist


def method_bt(fixes):
    """Integracion trapezoidal de speed x dt."""
    dist = 0.0
    for i in range(1, len(fixes)):
        dt = (fixes[i]['receivedAt'] - fixes[i - 1]['receivedAt']) / 1000.0
        if dt <= 0:
            continue
        v0 = fixes[i - 1].get('speed') or 0.0
        v1 = fixes[i].get('speed') or 0.0
        dist += (v0 + v1) / 2.0 * dt
    return dist


def method_c(fixes):
    """Combinado: particiona por consistencia geometria/velocidad.

    Para cada intervalo decide si la geometria de los fixes es consistente
    con la velocidad reportada. Si lo es, usa la velocidad (robusta al ruido);
    si no lo es (fix saltado, ruido extremo, corte), cae a la geometria
    filtrando saltos > MAX_JUMP. Tambien evita el doble conteo: la distancia
    se integra por velocidad y NO se suma polilinea en el mismo tramo.
    """
    dist = 0.0
    for i in range(1, len(fixes)):
        dt = (fixes[i]['receivedAt'] - fixes[i - 1]['receivedAt']) / 1000.0
        if dt <= 0:
            continue
        d_geo = haversine(fixes[i - 1]['latitude'], fixes[i - 1]['longitude'],
                          fixes[i]['latitude'], fixes[i]['longitude'])
        v0 = fixes[i - 1].get('speed') or 0.0
        v1 = fixes[i].get('speed') or 0.0
        v_trap = (v0 + v1) / 2.0
        d_vel = v_trap * dt
        # Consistencia: la geometria coincide con la velocidad dentro de un
        # margen que escala con el ruido declarado (accuracy del fix).
        acc = fixes[i].get('accuracy') or 0.0
        tol = max(2.0 * acc, 0.35 * d_vel, 1.0)
        if abs(d_geo - d_vel) <= tol and d_geo <= MAX_JUMP_DISTANCE_M:
            dist += d_vel
        elif d_geo > MAX_JUMP_DISTANCE_M:
            dist += d_vel          # salto: la geometria no es confiable
        else:
            dist += d_geo          # velocidad poco creible: usar geometria
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


# ------------------------------------------------------------- ejecucion
def run_cell(traj, sigma, seed, gt_pts, tmp_scen, tmp_fixes):
    gt_path = os.path.join(OUT_DIR, f'tray_{traj}.jsonl')
    sc = {
        'scenario_id': f'EXP2_{traj}_{sigma}_{seed}',
        'seed': seed,
        'duration_s': 300,
        'report_interval_ms': 1000,
        'gnss': {
            'noise_sigma_m': sigma,
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
        raise RuntimeError(f'simulador fallo {traj} s={sigma} seed={seed}: {r.stderr}')

    fixes = load_jsonl(tmp_fixes)
    present = set(f['measuredAt'] for f in fixes)
    ref = gt_reference(gt_pts, present)
    A, n_desc, n_gap = method_a(fixes)
    B = method_b(fixes)
    Bt = method_bt(fixes)
    C = method_c(fixes)
    return {
        'tray': traj, 'sigma': sigma, 'seed': seed, 'gt_ref_m': ref,
        'A_m': A, 'B_m': B, 'Bt_m': Bt, 'C_m': C,
        'er_A': (A - ref) / ref * 100.0,
        'er_B': (B - ref) / ref * 100.0,
        'er_Bt': (Bt - ref) / ref * 100.0,
        'er_C': (C - ref) / ref * 100.0,
        'abs_A': abs(A - ref) / ref * 100.0,
        'abs_B': abs(B - ref) / ref * 100.0,
        'abs_Bt': abs(Bt - ref) / ref * 100.0,
        'abs_C': abs(C - ref) / ref * 100.0,
        'bias_A': (A - ref) / ref * 100.0,
        'bias_B': (B - ref) / ref * 100.0,
        'bias_Bt': (Bt - ref) / ref * 100.0,
        'bias_C': (C - ref) / ref * 100.0,
        'n_desc': n_desc, 'n_gap': n_gap, 'n_fixes': len(fixes),
    }


def mean(xs):
    return statistics.mean(xs) if xs else float('nan')


def main():
    tmp_scen = os.path.join(OUT_DIR, '_tmp_scen.json')
    tmp_fixes = os.path.join(OUT_DIR, '_tmp_fixes.jsonl')
    results = []
    gt_cache = {}
    for traj in TRAJS:
        gt_cache[traj] = load_jsonl(os.path.join(OUT_DIR, f'tray_{traj}.jsonl'))
        for sigma in SIGMAS:
            for seed in SEEDS:
                results.append(run_cell(traj, sigma, seed,
                                        gt_cache[traj], tmp_scen, tmp_fixes))

    lines = []
    p = lines.append
    p('=== FASE 2: ERROR RELATIVO (%) POR TRAYECTORIA x RUIDO ===')
    p('(media de 5 semillas por celda; metodos A, B, B*=trapezoidal, C=combinado)')
    p('')
    p(f'{"trayectoria":16s} {"sigma":>5s} {"ref_m":>9s} '
      f'{"A%":>9s} {"B%":>9s} {"B*%":>9s} {"C%":>9s}')
    for traj in TRAJS:
        for sigma in SIGMAS:
            cell = [r for r in results if r['tray'] == traj and r['sigma'] == sigma]
            p(f'{traj:16s} {sigma:5.1f} {mean([c["gt_ref_m"] for c in cell]):9.2f} '
              f'{mean([c["er_A"] for c in cell]):9.2f} '
              f'{mean([c["er_B"] for c in cell]):9.2f} '
              f'{mean([c["er_Bt"] for c in cell]):9.2f} '
              f'{mean([c["er_C"] for c in cell]):9.2f}')
        p('')

    p('=== ERROR ABSOLUTO MEDIO (%) POR TRAYECTORIA x RUIDO ===')
    p(f'{"trayectoria":16s} {"sigma":>5s} {"|A|%":>9s} {"|B|%":>9s} '
      f'{"|B*|%":>9s} {"|C|%":>9s}')
    for traj in TRAJS:
        for sigma in SIGMAS:
            cell = [r for r in results if r['tray'] == traj and r['sigma'] == sigma]
            p(f'{traj:16s} {sigma:5.1f} '
              f'{mean([c["abs_A"] for c in cell]):9.2f} '
              f'{mean([c["abs_B"] for c in cell]):9.2f} '
              f'{mean([c["abs_Bt"] for c in cell]):9.2f} '
              f'{mean([c["abs_C"] for c in cell]):9.2f}')
        p('')

    # ---------------------------------------------------------- hipotesis
    p('=== VERIFICACION DE HIPOTESIS (criterios fijados) ===')
    p('')

    # H1: recta sin viradas -> |error de B| < 2%; refutada si >5% en 3/5.
    h1_bad = 0
    for traj in ('T1_recta',):
        for sigma in SIGMAS:
            cell = [r for r in results if r['tray'] == traj and r['sigma'] == sigma]
            bad = sum(1 for c in cell if c['abs_B'] > 5.0)
            h1_bad = max(h1_bad, bad)
    recta_cells = [r for r in results if r['tray'] == 'T1_recta']
    h1_mean = mean([r['abs_B'] for r in recta_cells])
    h1_max = max(r['abs_B'] for r in recta_cells)
    h1 = 'CONFIRMADA' if h1_max < 2.0 else ('REFUTADA' if h1_bad >= 3 else 'INCONCLUSA')
    p(f'H1 (B en recta cae <2%; refutada si >5% en 3/5): '
      f'|err B| en T1 medio={h1_mean:.3f}% max={h1_max:.3f}% -> {h1}')
    p(f'    celdas de T1 con >3/5 corridas sobre 5%: {h1_bad}')
    p('')

    # H2: algun metodo con error maximo <5% en las 4 (tray x ruido) realistas.
    # "realistas" = sigma >= 0.5; se evaluan las 12 celdas con ruido.
    best_name, best_worst = None, float('inf')
    for m, key in (('A', 'abs_A'), ('B', 'abs_B'), ('B*', 'abs_Bt'), ('C', 'abs_C')):
        worst = 0.0
        for traj in TRAJS:
            for sigma in (0.5, 1.5, 3.0):
                cell = [r for r in results if r['tray'] == traj and r['sigma'] == sigma]
                worst = max(worst, mean([c[key] for c in cell]))
        p(f'    {m:3s} peor celda (media) con ruido: {worst:8.2f}%')
        if worst < best_worst:
            best_name, best_worst = m, worst
    h2 = 'CONFIRMADA' if best_worst < 5.0 else 'REFUTADA'
    p(f'H2 (mejor metodo <5% en todas las celdas realistas): '
      f'mejor={best_name} peor celda={best_worst:.2f}% -> {h2}')
    p('')

    # H3: A en sigma=1.5 supera 20%.
    a15 = [r for r in results if r['sigma'] == 1.5]
    a15_mean = mean([r['er_A'] for r in a15])
    h3 = 'CONFIRMADA' if a15_mean > 20.0 else ('REFUTADA' if a15_mean < 10.0 else 'INCONCLUSA')
    p(f'H3 (A en sigma=1.5 supera 20%; refutada si <10%): '
      f'A err medio={a15_mean:.2f}% -> {h3}')
    p('')

    for tmp in (tmp_scen, tmp_fixes):
        if os.path.exists(tmp):
            os.remove(tmp)

    with open(os.path.join(OUT_DIR, 'resultados_fase2.json'), 'w') as f:
        json.dump({'results': results}, f, indent=2)

    report = '\n'.join(lines)
    print(report)
    with open(os.path.join(OUT_DIR, 'salida_fase2.txt'), 'w') as f:
        f.write(report + '\n')
    print(f'\n[{len(results)} corridas] -> resultados_fase2.json / salida_fase2.txt')


if __name__ == '__main__':
    main()
