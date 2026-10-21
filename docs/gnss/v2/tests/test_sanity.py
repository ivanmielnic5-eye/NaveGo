#!/usr/bin/env python3
"""
Sanity checks de Fase A (V2).

Estos tests NO corren el pipeline completo. Verifican:
  1. Que los imports funcionen y las constantes coincidan.
  2. Que V1 este intacto (git status docs/gnss/exp_* vacio).
  3. Que los archivos generados por gen_traj.py / gen_obs.py sean validos
     (si existen; si no, se saltean con SKIP).
  4. Que A, B, C_orig den 0 en sigma=0 sin cortes (sanity S1).
  5. Que el hash del fixes.jsonl sea identico entre los 3 metodos.

Uso:
  python3 test_sanity.py            # todo (SKIP si no hay datos)
  python3 test_sanity.py --no-git   # salta el check de git

Salida:
  exit 0 si todos los checks PASS o SKIP
  exit 1 si alguno FAIL

NO ejecutar sin autorizacion explicita del Director.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                    # docs/gnss/v2
EVAL = os.path.join(BASE, 'eval')
sys.path.insert(0, EVAL)

from methods import (  # noqa: E402
    METHODS, MAX_JUMP_DISTANCE_M, MIN_DISTANCE_DELTA_M,
    MAX_ACCURACY_M, GAP_THRESHOLD_MS,
    JUMP_FACTOR_SPEED, JUMP_FACTOR_ACCURACY,
    DT_UMBRAL_S, SPEED_ZERO_MS,
)
from metrics import (  # noqa: E402
    evaluate_file, load_json, load_jsonl, sha256_of_file,
)

FIXES_DIR = os.path.join(BASE, 'obsgen', 'fixes')
GT_DIR = os.path.join(BASE, 'gtgen', 'trajectories')
V1_DIRS = ['docs/gnss/exp_dist', 'docs/gnss/exp_ruido_vs_gap',
           'docs/gnss/exp_gaps_avance']


_results = []


def check(name, fn, skip_reason=None):
    if skip_reason is not None:
        _results.append((name, 'SKIP', skip_reason))
        print('SKIP  ' + name + ' :: ' + skip_reason)
        return
    try:
        detail = fn()
        _results.append((name, 'PASS', detail))
        print('PASS  ' + name + ' :: ' + str(detail))
    except AssertionError as e:
        _results.append((name, 'FAIL', str(e)))
        print('FAIL  ' + name + ' :: ' + str(e))
    except Exception as e:
        _results.append((name, 'FAIL', 'excepcion: ' + str(e)))
        print('FAIL  ' + name + ' :: excepcion: ' + str(e))


# --- 1. Constantes ---

def t_constants():
    assert MAX_JUMP_DISTANCE_M == 15.0, 'MAX_JUMP != 15'
    assert MIN_DISTANCE_DELTA_M == 0.8, 'MIN_DELTA != 0.8'
    assert MAX_ACCURACY_M == 20.0, 'MAX_ACCURACY != 20'
    assert GAP_THRESHOLD_MS == 15000, 'GAP_THRESHOLD != 15000'
    assert JUMP_FACTOR_SPEED == 2.0, 'JUMP_FACTOR_SPEED != 2'
    assert JUMP_FACTOR_ACCURACY == 3.0, 'JUMP_FACTOR_ACCURACY != 3'
    assert DT_UMBRAL_S == 2.0, 'DT_UMBRAL != 2'
    assert SPEED_ZERO_MS == 0.3, 'SPEED_ZERO != 0.3'
    return 'todas las constantes coinciden con ca0168a y eval_regla.py'


# --- 2. V1 intacto ---

def t_v1_intacto():
    repo_root = os.path.abspath(os.path.join(BASE, '..', '..', '..'))
    if not os.path.isdir(os.path.join(repo_root, '.git')):
        raise AssertionError('no hay repo git en ' + repo_root)
    r = subprocess.run(['git', 'status', '--porcelain'] + V1_DIRS,
                       cwd=repo_root, capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError('git status fallo: ' + r.stderr)
    if r.stdout.strip():
        raise AssertionError('V1 modificado:\n' + r.stdout)
    return 'git status vacio sobre ' + ', '.join(V1_DIRS)


# --- 3. Archivos de Fase A existen ---

def _lookup_fase_a():
    """Devuelve lista de (scenario, traj, seed, fixes, gt, obs) existentes."""
    found = []
    if not os.path.isdir(FIXES_DIR):
        return found
    for fn in sorted(os.listdir(FIXES_DIR)):
        if not fn.startswith('fixes_') or not fn.endswith('.jsonl'):
            continue
        fixes_path = os.path.join(FIXES_DIR, fn)
        obs_fn = fn.replace('fixes_', 'obs_events_').replace('.jsonl', '.json')
        obs_path = os.path.join(FIXES_DIR, obs_fn)
        if not os.path.exists(obs_path):
            continue
        try:
            obs = load_json(obs_path)
        except Exception:
            continue
        traj_id = obs.get('traj_id')
        seed = obs.get('seed')
        if not traj_id or seed is None:
            continue
        gt_path = os.path.join(GT_DIR,
                               'gt_' + traj_id + '_' + str(seed) + '.jsonl')
        if not os.path.exists(gt_path):
            continue
        found.append((traj_id, seed, fixes_path, gt_path, obs_path))
    return found


def t_archivos_fase_a():
    found = _lookup_fase_a()
    if not found:
        raise AssertionError('no hay archivos fixes_/gt_ generados')
    return '%d archivos validos' % len(found)


# --- 4. Sanity S1 (sigma=0, sin cortes) ---

def t_sanity_s1():
    fixes_list = _lookup_fase_a()
    s1 = [f for f in fixes_list if _es_s1(f)]
    if not s1:
        raise AssertionError('no hay ningun archivo S1 (sigma=0, recta, sin corte)')
    fails = []
    for (traj, seed, fx, gt, obs) in s1:
        for meth in ('A', 'B', 'C_orig'):
            r = evaluate_file(fx, gt, obs, METHODS[meth])
            em = r['metrics']['err_m']
            er = r['metrics']['err_rel_pct']
            if em is None or abs(em) >= 0.5:
                fails.append((meth, seed, 'err_m=' + str(em)))
            if er is not None and abs(er) >= 0.5:
                fails.append((meth, seed, 'err_rel=' + str(er)))
    if fails:
        raise AssertionError('fallas: ' + str(fails[:5]))
    return '%d archivos S1 x 3 metodos OK' % len(s1)


def _es_s1(f):
    traj, seed, fx, gt, obs = f
    if traj != 'recta_const_5kn':
        return False
    o = load_json(obs)
    cfg = o.get('gnss_cfg', {})
    return cfg.get('noise_sigma_m') == 0.0 and not cfg.get('cut_windows')


# --- 5. Hash identico entre metodos ---

def t_hash_identico():
    fixes_list = _lookup_fase_a()
    if not fixes_list:
        raise AssertionError('no hay archivos para chequear hash')
    # Tomar el primer archivo y correr A/B/C, verificar que fix_hash coincide
    traj, seed, fx, gt, obs = fixes_list[0]
    hashes = {}
    for meth in ('A', 'B', 'C_orig'):
        r = evaluate_file(fx, gt, obs, METHODS[meth])
        hashes[meth] = r['fix_hash']
    unique = set(hashes.values())
    if len(unique) != 1:
        raise AssertionError('hashes distintos: ' + str(hashes))
    return 'hash unico en ' + os.path.basename(fx)


# --- main ---

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--no-git', action='store_true',
                   help='salta el check de V1 intacto')
    args = p.parse_args()

    print('=== test_sanity.py (Fase A) ===')
    print('BASE: ' + BASE)
    print()

    check('1. Constantes coinciden', t_constants)
    check('2. V1 intacto (git status)',
          t_v1_intacto,
          skip_reason='--no-git' if args.no_git else None)
    check('3. Archivos de Fase A existen',
          t_archivos_fase_a,
          skip_reason=None if _lookup_fase_a() else 'sin archivos generados')
    check('4. Sanity S1 (sigma=0, sin corte)',
          t_sanity_s1,
          skip_reason=None if _lookup_fase_a() else 'sin archivos generados')
    check('5. Hash identico entre A/B/C',
          t_hash_identico,
          skip_reason=None if _lookup_fase_a() else 'sin archivos generados')

    print()
    n_pass = sum(1 for r in _results if r[1] == 'PASS')
    n_fail = sum(1 for r in _results if r[1] == 'FAIL')
    n_skip = sum(1 for r in _results if r[1] == 'SKIP')
    print('Total: %d PASS, %d FAIL, %d SKIP' % (n_pass, n_fail, n_skip))
    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
