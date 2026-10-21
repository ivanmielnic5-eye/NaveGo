#!/usr/bin/env python3
"""
Metricas V2 - cinco familias separadas.

1. Distancia en tramos observados (gt_ref_m, err_m, err_rel_pct)
2. Discontinuidades (n_gap_event, n_gapRestart, n_min_delta, n_noise)
3. Falsos gaps (gap_events sin cut programado)
4. Cortes omitidos (cuts programados sin gap_event asociado)
5. Continuidad visual enganiosa (cuts sin gap_event = track conecta A-B)

Etiquetas por salto:
  INJECTED_CUT        - existe cut programado y el salto lo cruza
  INJECTED_SPIKE      - existe spike en fix[i]
  NO_INJECTED_EVENT   - no hay cut ni spike; NO significa "ruido"
  NO_ETIQUETABLE      - datos insuficientes

Reglas duras:
  - gt_ref_m usa measuredAt (no receivedAt)
  - tolerancia 2000 ms para asociar gap_event <-> cut
  - NO_ETIQUETABLE <= 5 % es criterio de aceptacion (lo chequea run_all.py)

NO ejecutar sin autorizacion explicita del Director.
"""
import hashlib
import json
import math
import os

# Constantes (deben coincidir con methods.py)
KNOT_TO_MS = 1.0 / 1.94384
MAX_JUMP_DISTANCE_M = 15.0
EARTH_RADIUS_M = 6371000.0
TOLERANCE_MS = 2000


def haversine(lat1, lon1, lat2, lon2):
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dLon / 2) ** 2)
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def load_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_json(path):
    with open(path) as f:
        return json.load(f)


def sha256_of_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def compute_gt_ref_m(gt_points, present_ts):
    """Integral de sog_kn SOLO sobre timestamps reportados. Reinicia en ausente."""
    dist = 0.0
    prev = None
    for p in gt_points:
        if p.get('timestamp') not in present_ts:
            prev = None
            continue
        if prev is not None:
            dt = p['elapsed_s'] - prev['elapsed_s']
            if dt > 0:
                dist += (p['sog_kn'] + prev['sog_kn']) / 2.0 * KNOT_TO_MS * dt
        prev = p
    return dist


def label_jumps(fixes, obs_events):
    """Etiqueta cada par (fix[i-1], fix[i]) con d_pair > 15 m."""
    t0 = obs_events.get('T0_ms', 0)
    cuts = []
    spikes = {}
    for ev in obs_events.get('events', []):
        if ev.get('type') == 'cut':
            cuts.append({
                'start_abs': t0 + ev['start_s'] * 1000,
                'end_abs': t0 + (ev['start_s'] + ev['duration_s']) * 1000,
            })
        elif ev.get('type') == 'spike':
            spikes[ev.get('fix_index')] = ev

    labels = []
    for i in range(1, len(fixes)):
        d = haversine(fixes[i-1]['latitude'], fixes[i-1]['longitude'],
                      fixes[i]['latitude'], fixes[i]['longitude'])
        if d <= MAX_JUMP_DISTANCE_M:
            continue
        m_prev = fixes[i-1].get('measuredAt')
        m_curr = fixes[i].get('measuredAt')
        if m_prev is None or m_curr is None:
            label = 'NO_ETIQUETABLE'
        else:
            label = 'NO_INJECTED_EVENT'
            for cut in cuts:
                if m_prev < cut['start_abs'] and m_curr > cut['end_abs']:
                    label = 'INJECTED_CUT'
                    break
            if label == 'NO_INJECTED_EVENT' and i in spikes:
                label = 'INJECTED_SPIKE'
        labels.append({
            'fix_index': i,
            'd_pair_m': round(d, 3),
            'label': label,
        })
    return labels


def _cuts_abs(obs_events):
    t0 = obs_events.get('T0_ms', 0)
    cuts = []
    for ev in obs_events.get('events', []):
        if ev.get('type') == 'cut':
            cuts.append({
                'start_abs': t0 + ev['start_s'] * 1000,
                'end_abs': t0 + (ev['start_s'] + ev['duration_s']) * 1000,
                'duration_s': ev['duration_s'],
            })
    return cuts


def _gap_interval(gap_event):
    s = gap_event.get('start_at_ms', 0)
    e = gap_event.get('end_at_ms')
    if e is None:
        e = gap_event.get('detected_at_received', s + 1)
    return s, e


def _overlaps(cut, gap_event, tol_ms):
    gs, ge = _gap_interval(gap_event)
    return gs <= cut['end_abs'] + tol_ms and ge >= cut['start_abs'] - tol_ms


def detect_cuts(gap_events, cuts_abs, tol_ms=TOLERANCE_MS):
    """Devuelve (n_detected, n_missed, associations, n_multi)."""
    detected = 0
    associations = []
    n_multi = 0
    for cut in cuts_abs:
        matching = []
        for g in gap_events:
            if _overlaps(cut, g, tol_ms):
                matching.append(g.get('id'))
        if matching:
            detected += 1
            associations.append({'cut_start_abs': cut['start_abs'],
                                 'gap_ids': matching})
            if len(matching) > 1:
                n_multi += 1
    return detected, len(cuts_abs) - detected, associations, n_multi


def false_positives(gap_events, cuts_abs, tol_ms=TOLERANCE_MS):
    """gap_events que no se asocian a ningun cut programado."""
    fps = []
    for g in gap_events:
        found = False
        for cut in cuts_abs:
            if _overlaps(cut, g, tol_ms):
                found = True
                break
        if not found:
            fps.append(g)
    return fps


def compute_metrics(result, fixes, gt_points, obs_events):
    present_ts = set(f.get('measuredAt') for f in fixes
                     if f.get('measuredAt') is not None)
    gt_ref_m = compute_gt_ref_m(gt_points, present_ts)
    dist_m = result.get('dist_m', 0.0)
    err_m = dist_m - gt_ref_m
    err_rel_pct = (err_m / gt_ref_m * 100.0) if gt_ref_m > 0 else None

    cuts_abs = _cuts_abs(obs_events)
    gap_events = result.get('gap_events', [])
    detected, missed, assoc, n_multi = detect_cuts(gap_events, cuts_abs)
    fps = false_positives(gap_events, cuts_abs)
    connections = len(cuts_abs) - detected

    labels = label_jumps(fixes, obs_events)
    n_labels = len(labels)
    n_no_etiq = sum(1 for l in labels if l['label'] == 'NO_ETIQUETABLE')
    pct_no_etiq = (n_no_etiq / n_labels * 100.0) if n_labels > 0 else 0.0

    metrics = {
        # 1. Distancia
        'gt_ref_m': round(gt_ref_m, 3),
        'dist_m': round(dist_m, 3),
        'err_m': round(err_m, 3),
        'err_rel_pct': round(err_rel_pct, 3) if err_rel_pct is not None else None,
        'n_fixes': len(fixes),
        # 2. Discontinuidades y conteos de metodo
        'n_gap_events': len(gap_events),
        'n_labels': n_labels,
        'n_labels_no_etiquetable': n_no_etiq,
        'pct_no_etiquetable': round(pct_no_etiq, 3),
        # 3. Falsos gaps
        'n_false_positives': len(fps),
        # 4. Cortes detectados / omitidos
        'n_cuts_programmed': len(cuts_abs),
        'n_cuts_detected': detected,
        'n_cuts_missed': missed,
        'n_multi_gap_events_per_cut': n_multi,
        # 5. Continuidad visual enganiosa
        'n_conexiones_enganiosas': connections,
        # Asociaciones (para auditoria)
        'cut_associations': assoc,
    }
    # Contadores por metodo (si estan en result)
    for k in ('n_gapRestart_A', 'n_desc_A',
              'n_gapRestart_B', 'n_minDelta_B', 'n_acc_B',
              'n_gapReal_C', 'n_ruido_C', 'n_minDelta_C', 'n_acc_C'):
        if k in result:
            metrics[k] = result[k]
    return metrics


def evaluate_file(fixes_path, gt_path, obs_events_path, method_fn):
    """
    Corre un metodo sobre un escenario. Verifica hash de fixes.

    method_fn: callable(fixes) -> result dict (method_a, method_b_prod, etc.)
    """
    fixes = load_jsonl(fixes_path)
    gt_points = load_jsonl(gt_path)
    obs_events = load_json(obs_events_path)

    actual_hash = sha256_of_file(fixes_path)
    expected_hash = obs_events.get('fixes_sha256')
    if expected_hash and actual_hash != expected_hash:
        raise ValueError(
            'Hash mismatch en %s: esperado %s, obtenido %s'
            % (fixes_path, expected_hash, actual_hash))

    result = method_fn(fixes)
    metrics = compute_metrics(result, fixes, gt_points, obs_events)
    return {
        'fixes_path': fixes_path,
        'gt_path': gt_path,
        'obs_events_path': obs_events_path,
        'fix_hash': actual_hash,
        'method': result.get('method'),
        'variant': result.get('variant'),
        'fidelity': result.get('fidelity'),
        'metrics': metrics,
    }


if __name__ == '__main__':
    import sys
    print('Uso: importar desde run_all.py. Este archivo no es ejecutable solo.')
    print('Funciones publicas: evaluate_file, compute_metrics, label_jumps,')
    print('  detect_cuts, false_positives, compute_gt_ref_m')
    sys.exit(0)
