#!/usr/bin/env python3
"""
Experimento de distancia GNSS para NaveGo.

Pregunta: NaveGo mide bien la distancia recorrida bajo ruido GNSS?

Metodo A (NaveGo, useNaveGoTracker.ts): suma de haversine entre fixes
  consecutivos, con reset de gap si d > MAX_JUMP_DISTANCE_M (15 m) y
  descarte si d < MIN_DISTANCE_DELTA_M (0.8 m).
Metodo B (alternativo): integracion de speed (m/s) x dt.

Corre los 4 escenarios de corte (04, 05, 06, 07) sobre el GT nuevo
ground_truth_synthetic_5min.jsonl, barriendo sigma y semillas.

Referencia (ground truth de distancia): NO se usa la suma polilinea del
GT completo (que suma el tramo faltante durante los cortes). Se usa
sog_kn integrado sobre las muestras que el receptor SI reporto, que es
la distancia realmente recorrida en el tramo cubierto.
"""
import json, math, os, subprocess, statistics

GT_PATH = 'docs/gnss/ground_truth_synthetic_5min.jsonl'
SIM_PATH = 'tools/gnss_simulator.py'
OUT_DIR = 'docs/gnss/exp_dist'

SCENARIOS = {
    '04_corte_corto': 'docs/gnss/04_escenario_corte_corto.json',
    '05_corte_largo': 'docs/gnss/05_escenario_corte_largo.json',
    '06_tres_cortes': 'docs/gnss/06_escenario_tres_cortes.json',
    '07_giro_en_corte': 'docs/gnss/07_escenario_giro_durante_corte.json',
}

SIGMAS = [0.5, 1.5, 3.0, 5.0]
SEEDS = list(range(2000, 2010))

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


def load_gt():
    pts = []
    with open(GT_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                pts.append(json.loads(line))
    return pts


def load_fixes(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def method_a(fixes):
    """Replica exacta de la logica de distancia de NaveGo."""
    dist = 0.0
    n_desc = 0
    n_gap = 0
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
    """Integracion de speed (m/s) x dt sobre fixes reportados."""
    dist = 0.0
    for i in range(1, len(fixes)):
        dt = (fixes[i]['receivedAt'] - fixes[i - 1]['receivedAt']) / 1000.0
        if dt <= 0:
            continue
        v = fixes[i].get('speed') or 0.0
        dist += v * dt
    return dist


def gt_reference(gt_pts, present_ts):
    """Distancia GT sobre el tramo efectivamente reportado.

    Integra sog_kn del GT solo en las muestras que el receptor reporto,
    para no acreditar el tramo perdido durante un corte.
    """
    dist = 0.0
    prev = None
    for p in gt_pts:
        if p['timestamp'] not in present_ts:
            prev = None
            continue
        if prev is not None:
            dt = p['elapsed_s'] - prev['elapsed_s']
            if dt > 0:
                dist += (p['sog_kn'] + prev['sog_kn']) / 2.0 * KNOT_TO_MS * dt
        prev = p
    return dist


def run_scenario(sigma, seed, name, scen_file, gt_pts):
    scen_path = f'{OUT_DIR}/_tmp_scen.json'
    fixes_path = f'{OUT_DIR}/_tmp_fixes.jsonl'
    with open(scen_file) as f:
        sc = json.load(f)
    sc['scenario_id'] = f'EXP_DIST_{name}_{sigma}_{seed}'
    sc['seed'] = seed
    sc['gnss']['noise_sigma_m'] = sigma
    with open(scen_path, 'w') as f:
        json.dump(sc, f, indent=2)

    r = subprocess.run(['python3', SIM_PATH, GT_PATH, scen_path, fixes_path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f'ERROR {name} sigma={sigma} seed={seed}: {r.stderr}')
        return None

    fixes = load_fixes(fixes_path)
    present = set(f['measuredAt'] for f in fixes)
    ref = gt_reference(gt_pts, present)
    A, n_desc, n_gap = method_a(fixes)
    B = method_b(fixes)
    return {
        'scenario': name, 'sigma': sigma, 'seed': seed,
        'gt_ref_m': ref, 'A_m': A, 'B_m': B,
        'err_A_m': A - ref, 'err_B_m': B - ref,
        'er_A_pct': (A - ref) / ref * 100.0,
        'er_B_pct': (B - ref) / ref * 100.0,
        'n_desc': n_desc, 'n_gap': n_gap, 'n_fixes': len(fixes),
    }


def summarize(results, key):
    vals = [r[key] for r in results]
    return {
        'mean': statistics.mean(vals),
        'median': statistics.median(vals),
        'min': min(vals),
        'max': max(vals),
    }


def main():
    gt_pts = load_gt()
    results = []
    for name, scen_file in SCENARIOS.items():
        for sigma in SIGMAS:
            for seed in SEEDS:
                r = run_scenario(sigma, seed, name, scen_file, gt_pts)
                if r:
                    results.append(r)

    # ---- Resumen global por sigma ----
    print(f'=== METODO A (NaveGo) POR SIGMA (4 escenarios x {len(SEEDS)} semillas c/u) ===')
    for sigma in SIGMAS:
        lvl = [r for r in results if r['sigma'] == sigma]
        sA = summarize(lvl, 'er_A_pct')
        sB = summarize(lvl, 'er_B_pct')
        over10 = sum(1 for r in lvl if abs(r['er_A_pct']) > 10.0)
        print(f'sigma={sigma}: A err% med={sA["median"]:7.2f} mean={sA["mean"]:7.2f} '
              f'[{sA["min"]:7.2f},{sA["max"]:7.2f}] >10%%: {over10}/{len(lvl)} | '
              f'B err% med={sB["median"]:6.2f}')

    # ---- Por escenario y sigma ----
    print()
    print('=== ERROR % MEDIO DE A POR ESCENARIO/SIGMA ===')
    for name in SCENARIOS:
        row = []
        for sigma in SIGMAS:
            lvl = [r for r in results if r['scenario'] == name and r['sigma'] == sigma]
            row.append(f's{sigma}={statistics.mean(x["er_A_pct"] for x in lvl):7.2f}%')
        print(f'{name:20s} ' + '  '.join(row))

    # ---- Hipotesis ----
    print()
    print('=== VERIFICACION DE HIPOTESIS ===')

    # H1: A infla significativamente bajo sigma>=1.5 (error > 10%)
    lvl15 = [r for r in results if r['sigma'] == 1.5]
    mean15 = sum(r['er_A_pct'] for r in lvl15) / len(lvl15)
    frac15 = sum(1 for r in lvl15 if abs(r['er_A_pct']) > 10.0) / len(lvl15)
    h1 = 'CONFIRMADA' if (mean15 > 10.0 and frac15 >= 0.5) else \
         'REFUTADA' if abs(mean15) <= 10.0 else 'INCONCLUSA'
    print(f'H1 (A infla >10% con sigma=1.5): err medio={mean15:.2f}%, '
          f'>{10}% en {frac15*100:.0f}% de corridas -> {h1}')

    # H2: A funciona bien (error < 5%) bajo sigma=0.5
    lvl05 = [r for r in results if r['sigma'] == 0.5]
    mean05 = sum(r['er_A_pct'] for r in lvl05) / len(lvl05)
    frac05 = sum(1 for r in lvl05 if abs(r['er_A_pct']) < 5.0) / len(lvl05)
    h2 = 'CONFIRMADA' if (abs(mean05) < 5.0 and frac05 >= 0.5) else 'REFUTADA'
    print(f'H2 (A error <5% con sigma=0.5): err medio={mean05:.2f}%, '
          f'<5% en {frac05*100:.0f}% de corridas -> {h2}')

    # H3: B reduce el error >=50% respecto de A en sigma=3.0
    lvl30 = [r for r in results if r['sigma'] == 3.0]
    eA = sum(abs(r['er_A_pct']) for r in lvl30) / len(lvl30)
    eB = sum(abs(r['er_B_pct']) for r in lvl30) / len(lvl30)
    red = (eA - eB) / eA * 100.0 if eA else 0.0
    h3 = 'CONFIRMADA' if red >= 50.0 else 'REFUTADA'
    print(f'H3 (B reduce >=50% el error de A con sigma=3.0): '
          f'|err| A={eA:.2f}% B={eB:.2f}% reduccion={red:.1f}% -> {h3}')

    print()
    print('=== DETALLE POR ESCENARIO (sigma=1.5 y 3.0) ===')
    for name in SCENARIOS:
        for sigma in (1.5, 3.0):
            lvl = [r for r in results if r['scenario'] == name and r['sigma'] == sigma]
            eA = sum(r['er_A_pct'] for r in lvl) / len(lvl)
            eB = sum(r['er_B_pct'] for r in lvl) / len(lvl)
            gaps = sum(r['n_gap'] for r in lvl) / len(lvl)
            ref = sum(r['gt_ref_m'] for r in lvl) / len(lvl)
            print(f'{name:20s} s={sigma}: ref={ref:7.2f}m A={eA:8.2f}% B={eB:7.2f}% '
                  f'gaps/corrida={gaps:.1f}')

    for tmp in ('_tmp_scen.json', '_tmp_fixes.jsonl'):
        p = os.path.join(OUT_DIR, tmp)
        if os.path.exists(p):
            os.remove(p)

    with open(f'{OUT_DIR}/resultados.json', 'w') as f:
        json.dump({'gt_full_polyline_m': 693.215, 'results': results}, f, indent=2)
    print()
    print(f'Resultados guardados en {OUT_DIR}/resultados.json ({len(results)} corridas)')


if __name__ == '__main__':
    main()
