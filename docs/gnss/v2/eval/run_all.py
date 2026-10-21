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
import hashlib
import datetime
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from methods import METHODS  # noqa: E402
from metrics import (evaluate_file, load_json, load_jsonl,
                     sha256_of_file)  # noqa: E402
from provenance import (capture_runtime_snapshot, create_manifest,
                        validate_manifest, ProvenanceError)  # noqa: E402

BASE = os.path.dirname(HERE)                # docs/gnss/v2
GT_DIR = os.path.join(BASE, 'gtgen', 'trajectories')
TRAJ_EVENTS_DIR = os.path.join(BASE, 'gtgen', 'events')
FIXES_DIR = os.path.join(BASE, 'obsgen', 'fixes')
OUT_BASE = os.path.join(BASE, 'results')
REPO_ROOT = os.path.abspath(os.path.join(BASE, '..', '..', '..'))
V1_DIRS = ['docs/gnss/exp_dist', 'docs/gnss/exp_ruido_vs_gap',
           'docs/gnss/exp_gaps_avance']

def _dataset_id():
    value = os.environ.get("NAVEGO_DATASET_ID", "").strip()
    if value and (len(value) > 64 or value.startswith(".") or any(
            not (ch.isascii() and (ch.isalnum() or ch in "._-")) for ch in value)):
        raise ValueError("NAVEGO_DATASET_ID inválido; usá letras, números, punto, guion o guion bajo (máx. 64)")
    return value


DATASET_ID = _dataset_id()
DATASET_SUFFIX = ("_" + DATASET_ID) if DATASET_ID else ""
_OBS_GEN_DIR = os.path.join(BASE, "obsgen")
if _OBS_GEN_DIR not in sys.path:
    sys.path.insert(0, _OBS_GEN_DIR)
from gen_obs import PHASE_A_CFGS as _PHASE_A_CFGS, _build_scenario as _build_effective_scenario  # noqa: E402

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
    pat = os.path.join(FIXES_DIR, 'fixes_' + traj_id + DATASET_SUFFIX + '_*_' + str(seed) + '.jsonl')
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
    gt = os.path.join(GT_DIR, 'gt_' + traj_id + DATASET_SUFFIX + '_' + str(seed) + '.jsonl')
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

    # C7: recuperacion tras rechazos (integra test_recovery.py como subprocess)
    c7 = {'name': 'Recuperacion tras rechazos (N=1,2,3,5)',
          'status': 'SKIP', 'detail': []}
    rec_test = os.path.join(BASE, 'tests', 'test_recovery.py')
    if not os.path.exists(rec_test):
        c7['detail'] = ['no existe ' + rec_test]
    else:
        r7 = subprocess.run([sys.executable, rec_test],
                            capture_output=True, text=True, cwd=REPO_ROOT)
        if r7.returncode == 0:
            c7['status'] = 'PASS'
            c7['detail'] = ['test_recovery.py exit 0']
        else:
            c7['status'] = 'FAIL'
            tail = (r7.stdout or '').strip().split('\n')[-3:]
            c7['detail'] = ['exit ' + str(r7.returncode)] + tail
    crit['C7_recuperacion'] = c7

    # C8: V1 intacto (git status --porcelain sobre V1_DIRS)
    c8 = {'name': 'V1 intacto (git status exp_*)',
          'status': 'SKIP', 'detail': []}
    try:
        r8 = subprocess.run(['git', 'status', '--porcelain'] + V1_DIRS,
                            capture_output=True, text=True, cwd=REPO_ROOT)
        if r8.returncode != 0:
            c8['status'] = 'FAIL'
            c8['detail'] = ['git fallo: ' + (r8.stderr or '').strip()[:200]]
        elif (r8.stdout or '').strip():
            c8['status'] = 'FAIL'
            c8['detail'] = (r8.stdout or '').strip().split('\n')[:5]
        else:
            c8['status'] = 'PASS'
            c8['detail'] = ['git status vacio en V1_DIRS']
    except Exception as e:
        c8['status'] = 'FAIL'
        c8['detail'] = ['excepcion: ' + str(e)]
    crit['C8_v1_intacto'] = c8

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


def _check_setup(matrix, allow_legacy=False):
    """Read-only startup check-in. Returns a structured report and allow flag."""
    import glob

    def file_sha256(path):
        digest = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def canonical_json_sha256(value):
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def is_sha256(value):
        return isinstance(value, str) and len(value) == 64 and all(
            char in "0123456789abcdef" for char in value.lower()
        )

    def rel(path):
        try:
            return os.path.relpath(path, REPO_ROOT)
        except ValueError:
            return str(path)

    errors = []
    legacy = []
    groups = []
    scenarios = []
    total_groups = len(matrix) * len(SEEDS)
    current_sources = {
        "gt_generator": os.path.join(BASE, "gtgen", "gen_traj.py"),
        "obs_generator": os.path.join(BASE, "obsgen", "gen_obs.py"),
        "simulator": os.path.join(REPO_ROOT, "tools", "gnss_simulator.py"),
        "evaluator": __file__,
    }
    current_hashes = {key: file_sha256(path) for key, path in current_sources.items() if os.path.isfile(path)}

    print("\n=== CHECK-IN DE ARRANQUE — NAVEGO GNSS V2 ===")
    print("Dataset ID: %s" % (DATASET_ID if DATASET_ID else "LEGACY (sin namespace)"))
    print("Modo: solo lectura; no genera datos, no ejecuta métodos y no escribe resultados.")
    print("Fuentes actuales (SHA-256):")
    for key, digest in current_hashes.items():
        print("  %s: %s" % (key, digest))

    if not matrix:
        errors.append("La selección de escenarios está vacía.")

    for scenario_id, traj_id in matrix:
        cfg = _PHASE_A_CFGS.get(scenario_id)
        if cfg is None:
            errors.append("%s: falta configuración declarada en PHASE_A_CFGS" % scenario_id)
            continue
        expected_cfg_scenario = _build_effective_scenario(traj_id, SEEDS[0], cfg, -31.648, -60.708)
        expected_cfg_scenario["dataset_id"] = DATASET_ID or None
        gnss = expected_cfg_scenario.get("gnss", {})
        cuts = cfg.get("cut_windows", [])
        print(
            "[SETUP] %s | traj=%s | seeds=%d..%d | sigma_m=%s | model=%s | rho=%s | "
            "speed_sigma_ms=%s | latency_ms=%s | cuts=%s | spikes=%s"
            % (
                scenario_id, traj_id, SEEDS[0], SEEDS[-1],
                gnss.get("noise_sigma_m", "DESCONOCIDO"),
                gnss.get("noise_model", "IID (predeterminado del simulador si se omite)"),
                gnss.get("noise_rho", 0.0), gnss.get("speed_sigma_ms", 0.0),
                gnss.get("latency_ms", "DESCONOCIDO"), cuts,
                gnss.get("spikes", {"probability": 0.0, "min_jump_m": 0, "max_jump_m": 0}),
            )
        )
        scenario_summary = {
            "scenario": scenario_id,
            "trajectory": traj_id,
            "declared_gnss_cfg": cfg,
            "effective_gnss": gnss,
            "seeds": list(SEEDS),
        }
        scenarios.append(scenario_summary)

        for seed in SEEDS:
            group_errors = []
            group_legacy = []
            pattern = os.path.join(FIXES_DIR, "fixes_" + traj_id + DATASET_SUFFIX + "_*_" + str(seed) + ".jsonl")
            matches = []
            for candidate in sorted(glob.glob(pattern)):
                candidate_obs = candidate.replace("fixes_", "obs_events_", 1).removesuffix(".jsonl") + ".json"
                if not os.path.isfile(candidate_obs):
                    continue
                try:
                    candidate_meta = load_json(candidate_obs)
                    if _cfg_key_from_obs(candidate_meta, traj_id) == scenario_id:
                        matches.append((candidate, candidate_obs, candidate_meta))
                except Exception as exc:
                    group_errors.append("metadatos obs_events ilegibles: %s" % exc)

            if len(matches) != 1:
                errors.append("%s/seed=%s: se esperaba un único par fixes/obs_events y se encontraron %d" % (scenario_id, seed, len(matches)))
                continue

            fixes_path, obs_path, obs_meta = matches[0]
            gt_path = os.path.join(GT_DIR, "gt_" + traj_id + DATASET_SUFFIX + "_" + str(seed) + ".jsonl")
            gt_events_path = os.path.join(TRAJ_EVENTS_DIR, "traj_events_" + traj_id + DATASET_SUFFIX + "_" + str(seed) + ".json")
            if not os.path.isfile(gt_path) or not os.path.isfile(gt_events_path):
                errors.append("%s/seed=%s: falta GT o metadatos de trayectoria para dataset=%s" % (scenario_id, seed, DATASET_ID or "LEGACY"))
                continue

            try:
                gt_meta = load_json(gt_events_path)
            except Exception as exc:
                errors.append("%s/seed=%s: metadatos GT ilegibles: %s" % (scenario_id, seed, exc))
                continue

            actual_fix_hash = file_sha256(fixes_path)
            actual_gt_hash = file_sha256(gt_path)
            expected_scenario = _build_effective_scenario(traj_id, seed, cfg, -31.648, -60.708)
            expected_scenario["dataset_id"] = DATASET_ID or None

            # Configuration and file identity mismatches are always hard failures.
            if obs_meta.get("traj_id") != traj_id or obs_meta.get("seed") != seed:
                group_errors.append("identidad de trayectoria/semilla incorrecta en obs_events")
            if obs_meta.get("dataset_id") != (DATASET_ID or None):
                group_errors.append("dataset_id de obs_events no coincide con el solicitado")
            if obs_meta.get("gnss_cfg") != cfg:
                group_errors.append("gnss_cfg de obs_events no coincide con la configuración declarada")
            recorded_fix_value = str(obs_meta.get("fixes_path", ""))
            # gen_obs.py registra la ruta relativa a <repo>/docs/gnss/v2/obsgen,
            # por ejemplo "fixes/fixes_...jsonl". BASE aquí es gnss/v2, por eso
            # la ruta debe resolverse desde el directorio padre de FIXES_DIR.
            if os.path.isabs(recorded_fix_value):
                recorded_fix_path = os.path.abspath(recorded_fix_value)
            else:
                recorded_fix_path = os.path.abspath(
                    os.path.join(os.path.dirname(FIXES_DIR), recorded_fix_value)
                )
            if recorded_fix_path != os.path.abspath(fixes_path):
                group_errors.append("fixes_path registrado no apunta al archivo seleccionado")
            if obs_meta.get("fixes_sha256") != actual_fix_hash:
                group_errors.append("SHA-256 de fixes no coincide con obs_events")
            if gt_meta.get("traj_id") != traj_id or gt_meta.get("seed") != seed:
                group_errors.append("identidad de trayectoria/semilla incorrecta en traj_events")
            if gt_meta.get("dataset_id") != (DATASET_ID or None):
                group_errors.append("dataset_id de traj_events no coincide con el solicitado")

            duration = int(expected_scenario.get("duration_s", 0))
            cut_seconds = {
                second
                for cut in cuts
                for second in range(int(cut.get("start_s", 0)), int(cut.get("start_s", 0)) + int(cut.get("duration_s", 0)))
            }
            expected_fix_count = duration - len(cut_seconds)
            with open(fixes_path, encoding="utf-8") as f:
                n_fixes = sum(1 for line in f if line.strip())
            with open(gt_path, encoding="utf-8") as f:
                n_gt = sum(1 for line in f if line.strip())
            if n_fixes != expected_fix_count:
                group_errors.append("cantidad fixes=%d; esperada=%d" % (n_fixes, expected_fix_count))
            if n_gt != duration:
                group_errors.append("cantidad GT=%d; esperada=%d" % (n_gt, duration))

            gt_prov = gt_meta.get("provenance")
            obs_prov = obs_meta.get("provenance")
            if not isinstance(gt_prov, dict):
                group_legacy.append("traj_events sin procedencia del productor GT")
            else:
                recorded_gt_hash = gt_prov.get("gt_sha256")
                producer_gt_hash = gt_prov.get("generator_sha256")
                if not recorded_gt_hash or not producer_gt_hash:
                    group_legacy.append("procedencia GT incompleta (falta hash GT o del generador)")
                if recorded_gt_hash and not is_sha256(recorded_gt_hash):
                    group_errors.append("formato inválido de hash GT en traj_events")
                elif recorded_gt_hash and recorded_gt_hash != actual_gt_hash:
                    group_errors.append("SHA-256 de GT no coincide con traj_events")
                if producer_gt_hash and not is_sha256(producer_gt_hash):
                    group_errors.append("formato inválido de hash del generador GT")
                if gt_prov.get("dataset_id") != (DATASET_ID or None):
                    group_errors.append("dataset_id de procedencia GT no coincide")

            if not isinstance(obs_prov, dict):
                group_legacy.append("obs_events sin procedencia del generador de observaciones/simulador")
            else:
                required_keys = (
                    "gt_sha256", "gt_generator_sha256", "obs_generator_sha256",
                    "simulator_sha256", "effective_scenario", "effective_scenario_sha256",
                )
                missing_keys = [key for key in required_keys if key not in obs_prov]
                if missing_keys:
                    group_legacy.append("procedencia obs incompleta: falta " + ", ".join(missing_keys))
                if obs_prov.get("dataset_id") != (DATASET_ID or None):
                    group_errors.append("dataset_id de procedencia obs no coincide")
                for hash_key in (
                    "gt_sha256", "gt_generator_sha256", "obs_generator_sha256",
                    "simulator_sha256", "effective_scenario_sha256",
                ):
                    if hash_key in obs_prov and not is_sha256(obs_prov.get(hash_key)):
                        group_errors.append("formato inválido de hash en procedencia obs: " + hash_key)
                if "gt_sha256" in obs_prov and obs_prov.get("gt_sha256") != actual_gt_hash:
                    group_errors.append("hash GT en procedencia obs no coincide con la entrada actual")
                if isinstance(gt_prov, dict) and "gt_generator_sha256" in obs_prov:
                    if obs_prov.get("gt_generator_sha256") != gt_prov.get("generator_sha256"):
                        group_errors.append("huella del productor GT no enlaza obs_events con traj_events")
                if "effective_scenario" in obs_prov and obs_prov.get("effective_scenario") != expected_scenario:
                    group_errors.append("escenario efectivo registrado no coincide con configuración/declaración/dataset ID")
                if "effective_scenario" in obs_prov and "effective_scenario_sha256" in obs_prov:
                    if obs_prov.get("effective_scenario_sha256") != canonical_json_sha256(obs_prov["effective_scenario"]):
                        group_errors.append("hash canónico del escenario efectivo no coincide")

            if group_errors:
                errors.extend("%s/seed=%s: %s" % (scenario_id, seed, msg) for msg in group_errors)
            if group_legacy:
                legacy.extend("%s/seed=%s: %s" % (scenario_id, seed, msg) for msg in group_legacy)

            groups.append({
                "scenario": scenario_id,
                "trajectory": traj_id,
                "seed": seed,
                "fixes_path": rel(fixes_path),
                "fixes_sha256": actual_fix_hash,
                "n_fixes": n_fixes,
                "gt_path": rel(gt_path),
                "gt_sha256": actual_gt_hash,
                "n_gt": n_gt,
                "obs_events_path": rel(obs_path),
                "gt_producer_sha256": (gt_prov or {}).get("generator_sha256") if isinstance(gt_prov, dict) else None,
                "obs_producer_sha256": (obs_prov or {}).get("obs_generator_sha256") if isinstance(obs_prov, dict) else None,
                "simulator_sha256": (obs_prov or {}).get("simulator_sha256") if isinstance(obs_prov, dict) else None,
                "integrity_errors": list(group_errors),
                "legacy_warnings": list(group_legacy),
            })

    status = "PASS"
    if errors:
        status = "BLOCKED_INTEGRITY_ERROR"
    elif legacy and allow_legacy:
        status = "LEGACY_EXPLICIT_OVERRIDE"
    elif legacy:
        status = "BLOCKED_LEGACY_PROVENANCE"

    report = {
        "schema_version": 1,
        "status": status,
        "dataset_id": DATASET_ID or None,
        "phase": "A",
        "selected_scenarios": [item[0] for item in matrix],
        "seeds": list(SEEDS),
        "current_source_sha256": current_hashes,
        "verified_input_groups": len(groups),
        "expected_input_groups": total_groups,
        "integrity_errors": errors,
        "legacy_provenance_warnings": legacy,
        "groups": groups,
        "declared_setup": scenarios,
        "legacy_override_requested": bool(allow_legacy),
    }
    allowed = (not errors) and (not legacy or allow_legacy)

    print("[CHECK-IN] Pares de entrada examinados: %d/%d" % (len(groups), total_groups))
    print("[CHECK-IN] Errores de integridad/configuración: %d" % len(errors))
    print("[CHECK-IN] Advertencias de procedencia histórica incompleta: %d" % len(legacy))
    for msg in errors[:10]:
        print("  [ERROR] " + msg)
    if len(errors) > 10:
        print("  ... y %d errores más" % (len(errors) - 10))
    for msg in legacy[:10]:
        print("  [LEGACY] " + msg)
    if len(legacy) > 10:
        print("  ... y %d advertencias de procedencia más" % (len(legacy) - 10))

    if errors:
        print("[CHECK-IN BLOCKED] Hay inconsistencias de integridad/configuración; el override no las saltea.")
    elif legacy and not allow_legacy:
        print("[CHECK-IN BLOCKED] Procedencia histórica incompleta. Para usar esos datos deliberadamente, hace falta --allow-legacy-inputs.")
    elif legacy and allow_legacy:
        print("[CHECK-IN LEGACY OVERRIDE] Integridad de archivos/configuración coherente; productor histórico no acreditado. Se deja constancia en summary.json.")
    else:
        print("[CHECK-IN PASS] Configuración, hashes de entrada y cadena de productores verificados.")
    return {"allowed": allowed, "report": report}


def run(phase, scenarios_filter=None, methods_filter=None, allow_legacy_inputs=False):
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

    checkin = _check_setup(matrix, allow_legacy=allow_legacy_inputs)
    if not checkin["allowed"]:
        raise SystemExit(2)

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = os.path.join(OUT_BASE, 'v2_' + timestamp)
    try:
        runtime_snapshot = capture_runtime_snapshot(
            Path(REPO_ROOT),
            run_id=os.path.basename(out_dir),
            phase=phase,
            command=sys.argv,
        )
    except (ProvenanceError, OSError) as exc:
        raise SystemExit('[PROVENANCE START FAIL] ' + str(exc))
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
        'setup_checkin': checkin['report'],
    }

    with open(os.path.join(out_dir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    _write_csv(os.path.join(out_dir, 'by_scenario.csv'), rows)
    with open(os.path.join(out_dir, 'detail.jsonl'), 'w') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')

    manifest_path = Path(out_dir) / 'provenance_manifest.json'
    try:
        create_manifest(
            Path(out_dir), manifest_path, Path(REPO_ROOT),
            runtime_snapshot=runtime_snapshot,
        )
        provenance_errors = validate_manifest(manifest_path, Path(REPO_ROOT))
        if provenance_errors:
            for error in provenance_errors:
                print('[PROVENANCE ERROR] ' + error, file=sys.stderr)
            raise ProvenanceError('La validación final del manifiesto no pasó')
        print('[PROVENANCE PASS] Manifiesto verificado: ' + str(manifest_path))
    except (ProvenanceError, OSError, ValueError) as exc:
        print('[PROVENANCE FAIL] ' + str(exc), file=sys.stderr)
        print('[PROVENANCE FAIL] Se conservaron las salidas experimentales para diagnóstico.', file=sys.stderr)
        raise SystemExit(2)

    print('\n=== RESUMEN CRITERIOS BLOQUEANTES ===')
    for k, v in crit.items():
        print('  %-40s %s' % (k, v['status']))
    print('\nSalida: ' + out_dir)
    if missing:
        print('Revisar missing: %d combinaciones' % len(missing))

    n_fail = sum(1 for v in crit.values() if v.get('status') == 'FAIL')
    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--phase', choices=['A'], default='A')
    p.add_argument('--scenarios', nargs='+', default=None)
    p.add_argument('--methods', nargs='+', default=None)
    p.add_argument('--check-setup', action='store_true',
                   help='Ejecuta solo el check-in; no corre métodos ni escribe resultados.')
    p.add_argument('--allow-legacy-inputs', action='store_true',
                   help='Excepción explícita para datos históricos sin hashes de productor; no saltea errores de integridad/configuración.')
    args = p.parse_args()
    if args.check_setup:
        selected = ([m for m in PHASE_A_MATRIX if m[0] in args.scenarios]
                    if args.scenarios else PHASE_A_MATRIX)
        result = _check_setup(selected, allow_legacy=args.allow_legacy_inputs)
        raise SystemExit(0 if result["allowed"] else 2)
    sys.exit(run(args.phase, args.scenarios, args.methods, args.allow_legacy_inputs))
