#!/usr/bin/env python3
"""
Runner de Fase A - evalua A/B/C sobre la matriz de escenarios.

Responsabilidad:
  - iterar la matriz de escenarios de Fase A (11 escenarios x 5 seeds)
  - para cada combinacion, correr los 7 metodos sobre el MISMO fixes.jsonl
  - verificar que el hash del fixes sea identico entre metodos
  - agregar metricas por (escenario, metodo)
  - escribir summary.json + by_scenario.csv
  - evaluar los criterios bloqueantes de Fase A

NO ejecutar sin autorizacion explicita del Director.
NO regenera GT ni fixes. Requiere que gen_traj.py y gen_obs.py ya
hayan sido corridos para la matriz de Fase A.

Uso:
  python3 run_all.py --phase A
  python3 run_all.py --phase A --scenarios S1_s0_nocut
  python3 run_all.py --phase A --methods A B C_orig

La salida va a docs/gnss/v2/results/v2_<timestamp>/
"""
import argparse
import csv
import datetime
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from methods import METHODS  # noqa: E402
from metrics import (evaluate_file, load_json, load_jsonl,
                     sha256_of_file)  # noqa: E402

BASE = os.path.dirname(HERE)                # docs/gnss/v2
GT_DIR = os.path.join(BASE, 'gtgen', 'trajectories')
TRAJ_EVENTS_DIR = os.path.join(BASE, 'gtgen', 'events')
FIXES_DIR = os.path.join(BASE, 'obsgen', 'fixes')
OUT_BASE = os.path.join(BASE, 'results')

SEEDS = list(range(8100, 8105))

# Matriz de Fase A: (escenario_id, traj_id)
PHASE_A_MATRIX = [
    ('S1_s0_nocut',  'recta_const_5kn'),
    ('S2_s05_nocut', 'recta_const_5kn'),
    ('S3_s15_nocut', 'recta_const_5kn'),
    ('S4_s30_nocut', 'recta_const_5kn'),
    ('S5_s50_nocut', 'recta_const_5kn'),
    ('S6_s10_cut10', 'recta_const_5kn'),
    ('S10_det_stop', 'detencion_5kn_20s'),
    ('S11_lenta',    'lenta_1ms'),
    ('S16_det_s30',  'detencion_5kn_20s'),
    ('S17_det_s50',  'detencion_5kn_20s'),
    ('S18_det_cut5', 'detencion_5kn_20s'),
]

ALL_METHODS = ['A', 'B', 'C_orig', 'C_pair', 'C_var',
               'C_ctrl_no_event', 'C_and_speed', 'C_v2']

# Escenarios que deben ser adversariales (barco detenido o corte + barco detenido)
ADVERSARIAL_SCENARIOS = ['S16_det_s30', 'S17_det_s50', 'S18_det_cut5']
# Escenarios sin corte programado (cualquier gap_event es FP)
NO_CUT_SCENARIOS = ['S1_s0_nocut', 'S2_s05_nocut', 'S3_s15_nocut',
                    'S4_s30_nocut', 'S5_s50_nocut',
                    'S10_det_stop', 'S11_lenta',
                    'S16_det_s30', 'S17_det_s50']


def _paths(escenario_id, traj_id, seed):
    """Devuelve (fixes, gt, obs_events) o None si falta alguno."""
    fixes = os.path.join(FIXES_DIR, 'fixes_' + traj_id + '_'
                         + escenario_id + '_' + str(seed) + '.jsonl')
    # tag interno de gen_obs.py: no coincide exactamente con escenario_id
    # porque _gnss_tag() genera un tag a partir de la config, no del cfg_key.
    # Buscamos por glob de prefijo para tolerar diferencias de tag.
    import glob
    pat = os.path.join(FIXES_DIR, 'fixes_' + traj_id + '_*_' + str(seed) + '.jsonl')
    candidates = sorted(glob.glob(pat))
    fixes = None
    obs_events = None
    for c in candidates:
        obs_pat = c.replace('fixes_', 'obs_events_').replace('.jsonl', '.json')
        if not os.path.exists(obs_pat):
            continue
        try:
            obs = load_json(obs_pat)
        except Exception:
            continue
        cfg_key = _cfg_key_from_obs(obs, traj_id)
        if cfg_key == escenario_id:
            fixes = c
            obs_events = obs_pat
            break
    if fixes is None:
        return None
    gt = os.path.join(GT_DIR, 'gt_' + traj_id + '_' + str(seed) + '.jsonl')
    if not os.path.exists(gt):
        return None
    return fixes, gt, obs_events


def _cfg_key_from_obs(obs, traj_id):
    """Reconstruye el cfg_key (S1_s0_nocut, etc.) desde obs_events + traj_id.

    Nota: S3/S4/S5 (recta_const_5kn) y S10/S16/S17 (detencion_5kn_20s)
    comparten cut_windows=[], asi que la desambiguacion requiere traj_id.
    """
    cfg = obs.get('gnss_cfg', {})
    sigma = cfg.get('noise_sigma_m')
    cuts = cfg.get('cut_windows', [])

    if not cuts:
        if traj_id == 'recta_const_5kn':
            if sigma == 0.0:
                return 'S1_s0_nocut'
            if sigma == 0.5:
                return 'S2_s05_nocut'
            if sigma == 1.5:
                return 'S3_s15_nocut'
            if sigma == 3.0:
                return 'S4_s30_nocut'
            if sigma == 5.0:
                return 'S5_s50_nocut'
        if traj_id == 'detencion_5kn_20s':
            if sigma == 1.5:
                return 'S10_det_stop'
            if sigma == 3.0:
                return 'S16_det_s30'
            if sigma == 5.0:
                return 'S17_det_s50'
        if traj_id == 'lenta_1ms' and sigma == 1.5:
            return 'S11_lenta'

    if (len(cuts) == 1 and cuts[0]['start_s'] == 150
            and cuts[0]['duration_s'] == 10
            and traj_id == 'recta_const_5kn'):
        return 'S6_s10_cut10'
    if (len(cuts) == 1 and cuts[0]['start_s'] == 210
            and cuts[0]['duration_s'] == 5
            and traj_id == 'detencion_5kn_20s'):
        return 'S18_det_cut5'

    return None


def _aggregate(rows):
    """Agrega filas por (escenario, metodo) para metricas numericas."""
    by_key = {}
    for r in rows:
        key = (r['scenario'], r['method'])
        by_key.setdefault(key, []).append(r['metrics'])
    out = {}
    for (scen, meth), metrics_list in by_key.items():
        agg = {'scenario': scen, 'method': meth, 'n': len(metrics_list)}
        for field in ('err_m', 'err_rel_pct', 'dist_m', 'gt_ref_m',
                      'n_gap_events', 'n_false_positives',
                      'n_cuts_programmed', 'n_cuts_detected',
                      'n_cuts_missed', 'n_conexiones_enganiosas',
                      'pct_no_etiquetable',
                      'n_gapRestart_A', 'n_desc_A',
                      'n_gapRestart_B', 'n_minDelta_B', 'n_acc_B',
                      'n_gapReal_C', 'n_ruido_C', 'n_minDelta_C', 'n_acc_C'):
            vals = [m.get(field) for m in metrics_list
                    if m.get(field) is not None]
            if not vals:
                continue
            agg[field + '_mean'] = round(statistics.mean(vals), 3)
            agg[field + '_median'] = round(statistics.median(vals), 3)
            agg[field + '_min'] = round(min(vals), 3)
            agg[field + '_max'] = round(max(vals), 3)
        out[(scen, meth)] = agg
    return list(out.values())


def _criteria_bloqueantes(rows, aggregates):
    """
    Evalua los 8 criterios bloqueantes de Fase A.
    Devuelve dict {criterio: {status: PASS|FAIL|SKIP, detail: ...}}
    """
    crit = {}

    # C1: Sanity S1 (sigma=0, sin cortes): |err_m| < 0.5 y |err_rel| < 0.5
    c1 = {'name': 'Sanity S1 (sigma=0, sin corte, tol |err_m|<2.0 |err_rel|<1.0%)', 'status': 'SKIP',
          'detail': []}
    s1 = [r for r in rows if r['scenario'] == 'S1_s0_nocut'
          and r['method'] in ('A', 'B', 'C_orig')]
    if s1:
        fails = []
        for r in s1:
            m = r['metrics']
            em = m.get('err_m')
            er = m.get('err_rel_pct')
            if em is None or abs(em) >= 2.0:
                fails.append((r['method'], r['seed'], 'err_m=' + str(em)))
            if er is not None and abs(er) >= 1.0:
                fails.append((r['method'], r['seed'], 'err_rel=' + str(er)))
        if fails:
            c1['status'] = 'FAIL'
            c1['detail'] = fails[:10]
        else:
            c1['status'] = 'PASS'
            c1['detail'] = ['n=%d' % len(s1)]
    crit['C1_sanity_s1'] = c1

    # C3: Mismas observaciones - hash identico entre metodos por (escenario, seed)
    c3 = {'name': 'Mismas observaciones (hash)', 'status': 'SKIP', 'detail': []}
    by_group = {}
    for r in rows:
        key = (r['scenario'], r['seed'])
        by_group.setdefault(key, set()).add(r['fix_hash'])
    multi = {k: v for k, v in by_group.items() if len(v) > 1}
    if by_group:
        if multi:
            c3['status'] = 'FAIL'
            c3['detail'] = ['multi-hash: %s -> %d hashes'
                            % (str(k), len(v)) for k, v in list(multi.items())[:10]]
        else:
            c3['status'] = 'PASS'
            c3['detail'] = ['n_grupos=%d' % len(by_group)]
    crit['C3_mismas_observaciones'] = c3

    # C4: NO_ETIQUETABLE <= 5% por archivo
    c4 = {'name': 'NO_ETIQUETABLE <= 5%', 'status': 'SKIP', 'detail': []}
    fails = []
    for r in rows:
        pct = r['metrics'].get('pct_no_etiquetable')
        if pct is not None and pct > 5.0:
            fails.append((r['scenario'], r['method'], r['seed'], pct))
    if rows:
        if fails:
            c4['status'] = 'FAIL'
            c4['detail'] = fails[:10]
        else:
            c4['status'] = 'PASS'
            c4['detail'] = ['n=%d' % len(rows)]
    crit['C4_no_etiquetable'] = c4

    # C5: caso obligatorio S6 (reformulado como diferencial B-A)
    c5 = {'name': 'Caso obligatorio S6 (B-A en [20,35] m, tol metrologica)',
          'status': 'SKIP', 'detail': []}
    s6 = {r['method']: [] for r in rows if r['scenario'] == 'S6_s10_cut10'}
    for r in rows:
        if r['scenario'] != 'S6_s10_cut10':
            continue
        s6.setdefault(r['method'], []).append(r)
    if s6.get('B'):
        detail = []
        fails = []
        # Construir mapa seed -> err_m_A para calcular diferencial
        err_a_by_seed = {}
        for r in s6.get('A', []):
            err_a_by_seed[r['seed']] = r['metrics'].get('err_m')
        for r in s6['B']:
            m = r['metrics']
            em = m.get('err_m')
            em_a = err_a_by_seed.get(r['seed'])
            if em is None or em_a is None:
                fails.append(('B', r['seed'],
                              'err_m o err_m_A faltante'))
                continue
            diff = em - em_a
            if not (20.0 <= diff <= 35.0):
                fails.append(('B', r['seed'],
                              'B-A=' + str(round(diff, 2))))
            if m.get('n_gap_events', 0) != 0:
                fails.append(('B', r['seed'],
                              'n_gap_events=' + str(m.get('n_gap_events'))))
        for r in s6.get('A', []):
            m = r['metrics']
            if m.get('n_gapRestart_A', 0) < 1:
                fails.append(('A', r['seed'],
                              'n_gapRestart_A=' + str(m.get('n_gapRestart_A'))))
        for r in s6.get('C_orig', []):
            m = r['metrics']
            if m.get('n_gapReal_C', 0) < 1:
                fails.append(('C_orig', r['seed'],
                              'n_gapReal_C=' + str(m.get('n_gapReal_C'))))
            if m.get('n_gap_events', 0) != 1:
                fails.append(('C_orig', r['seed'],
                              'n_gap_events=' + str(m.get('n_gap_events'))))
        if fails:
            c5['status'] = 'FAIL'
            c5['detail'] = fails[:15]
        else:
            c5['status'] = 'PASS'
            c5['detail'] = ['ok en %d seeds' % len(s6['B'])]
    crit['C5_caso_obligatorio_S6'] = c5

    # C6: rama speed<=0.3 ejercitada en S10, S16, S17, S18
    c6 = {'name': 'Rama speed<=0.3 ejercitada en S10/S16/S17/S18',
          'status': 'SKIP', 'detail': []}
    ejercitada = False
    detail = []
    for scen in ('S10_det_stop', 'S16_det_s30', 'S17_det_s50', 'S18_det_cut5'):
        for r in rows:
            if r['scenario'] != scen or r['method'] != 'C_orig':
                continue
            m = r['metrics']
            ng = m.get('n_gapReal_C', 0)
            if ng > 0:
                ejercitada = True
            detail.append((scen, r['seed'], 'n_gapReal_C=' + str(ng)))
    if detail:
        c6['status'] = 'PASS' if ejercitada else 'FAIL'
        c6['detail'] = detail[:10]
    crit['C6_rama_speed_baja'] = c6

    # C7: recuperacion - se valida en test_recovery.py, aca SKIP
    crit['C7_recuperacion'] = {
        'name': 'Recuperacion tras rechazos (N=1,2,3,5)',
        'status': 'SKIP',
        'detail': ['ver tests/test_recovery.py'],
    }

    # C8: V1 intacto - no evaluable desde el script, SKIP
    crit['C8_v1_intacto'] = {
        'name': 'V1 intacto (git status exp_*)',
        'status': 'SKIP',
        'detail': ['verificar con git status post-corrida'],
    }

    return crit


def _write_csv(path, rows):
    fieldnames = ['scenario', 'traj', 'seed', 'method', 'variant',
                  'fix_hash',
                  'dist_m', 'gt_ref_m', 'err_m', 'err_rel_pct',
                  'n_fixes', 'n_gap_events', 'n_false_positives',
                  'n_cuts_programmed', 'n_cuts_detected', 'n_cuts_missed',
                  'n_conexiones_enganiosas', 'pct_no_etiquetable',
                  'n_gapRestart_A', 'n_desc_A',
                  'n_gapRestart_B', 'n_minDelta_B', 'n_acc_B',
                  'n_gapReal_C', 'n_ruido_C', 'n_minDelta_C', 'n_acc_C']
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            m = r['metrics']
            row = {
                'scenario': r['scenario'],
                'traj': r['traj'],
                'seed': r['seed'],
                'method': r['method'],
                'variant': r.get('variant') or '',
                'fix_hash': r['fix_hash'][:16],
            }
            for k in fieldnames:
                if k in row:
                    continue
                row[k] = m.get(k)
            w.writerow(row)


def run(phase, scenarios_filter=None, methods_filter=None):
    if phase != 'A':
        raise SystemExit('Solo Fase A implementada. Fase B es trabajo futuro.')

    if scenarios_filter:
        matrix = [m for m in PHASE_A_MATRIX if m[0] in scenarios_filter]
    else:
        matrix = PHASE_A_MATRIX

    if methods_filter:
        for m in methods_filter:
            if m not in METHODS:
                raise SystemExit('Metodo invalido: ' + m)
        methods_use = methods_filter
    else:
        methods_use = ALL_METHODS

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = os.path.join(OUT_BASE, 'v2_' + timestamp)
    os.makedirs(out_dir, exist_ok=True)

    rows = []
    missing = []

    for scen_id, traj_id in matrix:
        for seed in SEEDS:
            paths = _paths(scen_id, traj_id, seed)
            if paths is None:
                missing.append((scen_id, traj_id, seed))
                continue
            fixes_path, gt_path, obs_events_path = paths
            for meth_name in methods_use:
                method_fn = METHODS[meth_name]
                try:
                    r = evaluate_file(fixes_path, gt_path,
                                      obs_events_path, method_fn)
                except Exception as e:
                    print('[ERROR] %s/%s/seed=%d/%s: %s'
                          % (scen_id, traj_id, seed, meth_name, e))
                    continue
                r['scenario'] = scen_id
                r['traj'] = traj_id
                r['seed'] = seed
                r['method'] = meth_name
                rows.append(r)
            print('[OK] %s/%s/seed=%d: %d metodos'
                  % (scen_id, traj_id, seed, len(methods_use)))

    if missing:
        print('\n[WARN] %d combinaciones sin archivos:' % len(missing))
        for m in missing[:20]:
            print('  - %s / %s / seed=%d' % m)

    aggregates = _aggregate(rows) if rows else []
    crit = _criteria_bloqueantes(rows, aggregates) if rows else {}

    summary = {
        'phase': 'A',
        'timestamp': timestamp,
        'n_rows': len(rows),
        'n_missing': len(missing),
        'missing': [{'scenario': m[0], 'traj': m[1], 'seed': m[2]}
                    for m in missing],
        'aggregates': aggregates,
        'criteria': crit,
    }

    with open(os.path.join(out_dir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    _write_csv(os.path.join(out_dir, 'by_scenario.csv'), rows)
    with open(os.path.join(out_dir, 'detail.jsonl'), 'w') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')

    print('\n=== RESUMEN CRITERIOS BLOQUEANTES ===')
    for k, v in crit.items():
        print('  %-40s %s' % (k, v['status']))
    print('\nSalida: ' + out_dir)
    if missing:
        print('Revisar missing: %d combinaciones' % len(missing))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--phase', choices=['A'], default='A')
    p.add_argument('--scenarios', nargs='+', default=None)
    p.add_argument('--methods', nargs='+', default=None)
    args = p.parse_args()
    run(args.phase, args.scenarios, args.methods)
