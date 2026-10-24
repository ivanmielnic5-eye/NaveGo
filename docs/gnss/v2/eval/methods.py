#!/usr/bin/env python3
"""
Metodos A, B, C para V2 - Componente C de V2.

A  - filtro historico (15 m + 0,8 m)
B  - produccion real (orchestrator.ts + processFix.ts), VERIFICADO F.4/F.5
C  - clasificador experimental con accion

Variantes C:
  - orig:            receivedAt, OR, acumula d_anchor, abre gap_event
  - pair:            receivedAt, OR, acumula d_pair, abre gap_event
  - var:             measuredAt, OR, acumula d_anchor, abre gap_event
  - ctrl_no_event:   receivedAt, OR, acumula d_anchor, NO abre gap_event
  - and_speed:       receivedAt, AND, acumula d_anchor, abre gap_event

NO ejecutar sin autorizacion explicita del Director.
"""
import math

# Constantes de produccion (ca0168a)
MAX_JUMP_DISTANCE_M = 15.0
MIN_DISTANCE_DELTA_M = 0.8
MAX_ACCURACY_M = 20.0
GAP_THRESHOLD_MS = 15000
JUMP_FACTOR_SPEED = 2.0
JUMP_FACTOR_ACCURACY = 3.0

# Constantes de C (eval_regla.py de V1)
DT_UMBRAL_S = 2.0
SPEED_ZERO_MS = 0.3

# Geodesia
EARTH_RADIUS_M = 6371000.0


def haversine(lat1, lon1, lat2, lon2):
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dLon / 2) ** 2)
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _speed_of(fix):
    s = fix.get('speed')
    if s is None or not isinstance(s, (int, float)):
        return 0.0
    if not math.isfinite(s):
        return 0.0
    return float(s) if s > 0 else 0.0


def _accuracy_of(fix):
    a = fix.get('accuracy')
    if a is None or not isinstance(a, (int, float)):
        return 999.0
    if not math.isfinite(a):
        return 999.0
    return float(a)


# =========================================================================
# A - filtro historico
# =========================================================================

def method_a(fixes):
    """Haversine + reset 15 m + descarte 0,8 m. Sin tiempo ni accuracy."""
    dist = 0.0
    n_desc = 0
    n_gapRestart = 0
    trace = []
    prev = None
    for i, fix in enumerate(fixes):
        if prev is None:
            prev = fix
            trace.append({'fix_index': i, 'action': 'first',
                          'd_pair_m': 0.0, 'distance_cumulative': 0.0})
            continue
        d = haversine(prev['latitude'], prev['longitude'],
                      fix['latitude'], fix['longitude'])
        if d > MAX_JUMP_DISTANCE_M:
            n_gapRestart += 1
            action = 'gap_restart'
        elif d < MIN_DISTANCE_DELTA_M:
            n_desc += 1
            action = 'reject_min_delta'
        else:
            dist += d
            action = 'accept'
        trace.append({'fix_index': i, 'action': action,
                      'd_pair_m': d, 'distance_cumulative': dist})
        prev = fix
    return {
        'dist_m': dist,
        'n_gapRestart_A': n_gapRestart,
        'n_desc_A': n_desc,
        'gap_events': [],
        'trace': trace,
        'method': 'A',
    }


# =========================================================================
# B - produccion real (orchestrator + processFix)
# =========================================================================

def method_b_prod(fixes):
    """
    Replica de ca0168a. VERIFICADO contra F.4 + F.5.

    F.4 cerrado: processFix.ts 200-280 confirma que isGapRestart llega
    al retorno de aceptacion (newPoint != null, nextState.lastPoint =
    fix actual, distanceDelta = distanceIncrement = 0). MIN_DELTA
    retorna antes con newPoint=null y lastPoint sin tocar.

    F.5 cerrado: useNaveGoTracker.ts no tiene logica de gap/ruido fuera
    de processFix. Solo logging de [FILTER] acc y [FILTER] jump.

    Diferencia conocida (no afecta dist_m ni gap_events):
    processFix calcula calculatedSog (= distanceIncrement / dt si
    speed=0 y hay lastPoint) y calculatedCog (geometria si movimiento
    suficiente) para el newPoint visual (HUD y track). Esta replica NO
    calcula esos campos porque solo se usan en UI, no en la decision
    de distancia ni en la apertura de gap_event.

    Dos estados separados:
      - anchor: ultimo punto aceptado geometricamente
      - last_received_at_ms: ultima recepcion (para watchdog)

    isGapRestart: corta distancia pero NO abre gap_event (eso es watchdog).
    isGapRestart: SI actualiza anchor (newPoint en processFix.ts).
    """
    state = {
        'anchor': None,
        'last_accepted_anchor_at': None,
        'last_received_at_ms': 0,
        'last_fix_id': None,
        'open_gap_id': None,
        'gap_events': [],
    }
    dist = 0.0
    n_gapRestart = 0
    n_minDelta = 0
    n_acc = 0
    trace = []
    gap_counter = 0

    for i, fix in enumerate(fixes):
        # FASE 1: watchdog (orchestrator.detectAndOpenGapIfNeeded)
        if (state['anchor'] is not None
                and state['last_fix_id'] is not None
                and state['open_gap_id'] is None
                and state['last_received_at_ms'] > 0):
            elapsed = fix['receivedAt'] - state['last_received_at_ms']
            if elapsed > GAP_THRESHOLD_MS:
                gap_counter += 1
                gid = 'gap_wd_' + str(gap_counter)
                state['gap_events'].append({
                    'id': gid,
                    'via': 'watchdog',
                    'start_at_ms': state['anchor']['measuredAt'],
                    'end_at_ms': None,
                    'detected_at_received': fix['receivedAt'],
                    'elapsed_ms': elapsed,
                })
                state['open_gap_id'] = gid

        # FASE 2: processFix
        accuracy = _accuracy_of(fix)
        d_anchor = 0.0
        if state['anchor'] is not None:
            d_anchor = haversine(state['anchor']['lat'], state['anchor']['lon'],
                                 fix['latitude'], fix['longitude'])

        entry = {
            'fix_index': i,
            'd_anchor_m': d_anchor,
            'accuracy_m': accuracy,
            'action': None,
            'threshold_m': None,
        }

        if accuracy > MAX_ACCURACY_M:
            n_acc += 1
            entry['action'] = 'reject_accuracy'
        else:
            dtSec = 1.0
            if state['anchor'] is not None:
                dtSec = max((fix['measuredAt']
                             - state['anchor']['measuredAt']) / 1000.0, 1.0)
            speedMs = _speed_of(fix)
            threshold = max(MAX_JUMP_DISTANCE_M,
                            speedMs * dtSec * JUMP_FACTOR_SPEED
                            + accuracy * JUMP_FACTOR_ACCURACY)
            entry['threshold_m'] = threshold

            if d_anchor > threshold:
                n_gapRestart += 1
                entry['action'] = 'gap_restart'
                # TODO(F.4): confirmar con codigo. Auditoria dice:
                # "Genera newPoint y actualiza lastPoint al fix actual,
                #  aunque distanceIncrement sea cero."
                state['anchor'] = {
                    'lat': fix['latitude'],
                    'lon': fix['longitude'],
                    'measuredAt': fix['measuredAt'],
                }
                state['last_accepted_anchor_at'] = fix['measuredAt']
            elif (state['anchor'] is not None
                  and d_anchor < MIN_DISTANCE_DELTA_M):
                n_minDelta += 1
                entry['action'] = 'reject_min_delta'
            else:
                dist += d_anchor
                entry['action'] = 'accept'
                state['anchor'] = {
                    'lat': fix['latitude'],
                    'lon': fix['longitude'],
                    'measuredAt': fix['measuredAt'],
                }
                state['last_accepted_anchor_at'] = fix['measuredAt']

        entry['distance_cumulative'] = dist

        # FASE 3: cerrar gap_event si proceso un fix post-gap
        if state['open_gap_id'] is not None:
            for g in state['gap_events']:
                if g['id'] == state['open_gap_id']:
                    g['end_at_ms'] = fix['measuredAt']
                    g['closed_by'] = 'processFix_after_gap'
                    break
            state['open_gap_id'] = None

        # FASE 4: SIEMPRE actualizar recepcion
        state['last_received_at_ms'] = fix['receivedAt']
        state['last_fix_id'] = 'fix_' + str(i)

        trace.append(entry)

    return {
        'dist_m': dist,
        'n_gapRestart_B': n_gapRestart,
        'n_minDelta_B': n_minDelta,
        'n_acc_B': n_acc,
        'gap_events': state['gap_events'],
        'trace': trace,
        'method': 'B',
        'fidelity': 'VERIFICADO (F.4+F.5, calculatedSog/Cog no replicados - no afecta dist_m)',
    }


# =========================================================================
# C - clasificador experimental con accion
# =========================================================================

_VALID_C_VARIANTS = ('orig', 'pair', 'var', 'ctrl_no_event', 'and_speed', 'v2')


def method_c(fixes, variant='orig'):
    """
    C: clasifica d_pair > 15 m con regla (dt > 2s) OR/AND (speed <= 0.3).

    - GAP_REAL: anchor salta, distance += 0, abre gap_event (excepto ctrl).
    - RUIDO:    anchor NO se mueve, distance += 0.
    - None:     no hay candidato, se procesa como B (MIN_DELTA, accept).

    Gatillo siempre d_pair > 15 m (NO adaptiveThreshold de B). C.6.
    Variantes: orig (receivedAt, OR), pair (acumula d_pair), var
    (measuredAt), ctrl_no_event (no abre gap_event), and_speed (AND),
    v2 (solo dt > 2s, sin rama speed <= 0.3).
    """
    if variant not in _VALID_C_VARIANTS:
        raise ValueError('variant invalido: ' + variant)

    state = {
        'anchor': None,
        'last_accepted_anchor_at': None,
        'last_received_at_ms': 0,
        'last_fix_id': None,
        'open_gap_id': None,
        'gap_events': [],
    }
    dist = 0.0
    n_gapReal = 0
    n_ruido = 0
    n_minDelta = 0
    n_acc = 0
    trace = []
    gap_counter = 0
    prev_fix = None

    for i, fix in enumerate(fixes):
        # FASE 1: watchdog (compartido con B, C.7)
        if (state['anchor'] is not None
                and state['last_fix_id'] is not None
                and state['open_gap_id'] is None
                and state['last_received_at_ms'] > 0):
            elapsed = fix['receivedAt'] - state['last_received_at_ms']
            if elapsed > GAP_THRESHOLD_MS:
                gap_counter += 1
                gid = 'gap_wd_' + str(gap_counter)
                state['gap_events'].append({
                    'id': gid,
                    'via': 'watchdog',
                    'start_at_ms': state['anchor']['measuredAt'],
                    'end_at_ms': None,
                    'detected_at_received': fix['receivedAt'],
                    'elapsed_ms': elapsed,
                })
                state['open_gap_id'] = gid

        # FASE 2: filtro accuracy
        accuracy = _accuracy_of(fix)
        d_anchor = 0.0
        if state['anchor'] is not None:
            d_anchor = haversine(state['anchor']['lat'], state['anchor']['lon'],
                                 fix['latitude'], fix['longitude'])
        d_pair = 0.0
        if prev_fix is not None:
            d_pair = haversine(prev_fix['latitude'], prev_fix['longitude'],
                               fix['latitude'], fix['longitude'])

        entry = {
            'fix_index': i,
            'd_pair_m': d_pair,
            'd_anchor_m': d_anchor,
            'accuracy_m': accuracy,
            'classification': None,
            'action': None,
            'threshold_m': None,
        }

        if accuracy > MAX_ACCURACY_M:
            n_acc += 1
            entry['action'] = 'reject_accuracy'
        else:
            classification = None

            # FASE 3: clasificacion C sobre d_pair > 15 (C.6)
            if prev_fix is not None and d_pair > MAX_JUMP_DISTANCE_M:
                if variant == 'var':
                    dt_c = (fix['measuredAt']
                            - prev_fix['measuredAt']) / 1000.0
                else:
                    dt_c = (fix['receivedAt']
                            - prev_fix['receivedAt']) / 1000.0
                sp_c = _speed_of(fix)
                if variant == 'and_speed':
                    es_gap = (dt_c > DT_UMBRAL_S) and (sp_c <= SPEED_ZERO_MS)
                elif variant == 'v2':
                    # Opcion A: solo rama temporal. Elimina speed <= 0.3
                    # para evitar falsos gaps en barco detenido (S17).
                    es_gap = (dt_c > DT_UMBRAL_S)
                else:
                    es_gap = (dt_c > DT_UMBRAL_S) or (sp_c <= SPEED_ZERO_MS)

                if es_gap:
                    classification = 'GAP_REAL'
                    n_gapReal += 1
                    # C.5.1: reutilizar si ya hay; sino abrir (excepto ctrl)
                    if variant != 'ctrl_no_event':
                        if state['open_gap_id'] is None:
                            gap_counter += 1
                            gid = 'gap_c_' + str(gap_counter)
                            state['gap_events'].append({
                                'id': gid,
                                'via': 'C',
                                'start_at_ms': prev_fix['measuredAt'],
                                'end_at_ms': None,
                                'detected_at_received': fix['receivedAt'],
                            })
                            state['open_gap_id'] = gid
                    # C.2: anchor salta, distance += 0
                    dist += 0.0
                    state['anchor'] = {
                        'lat': fix['latitude'],
                        'lon': fix['longitude'],
                        'measuredAt': fix['measuredAt'],
                    }
                    state['last_accepted_anchor_at'] = fix['measuredAt']
                    entry['action'] = 'gap_real'
                    # cerrar gap_event
                    if state['open_gap_id'] is not None:
                        for g in state['gap_events']:
                            if g['id'] == state['open_gap_id']:
                                g['end_at_ms'] = fix['measuredAt']
                                g['closed_by'] = 'C'
                                break
                        state['open_gap_id'] = None
                else:
                    classification = 'RUIDO'
                    n_ruido += 1
                    entry['action'] = 'reject_noise'
                    # C.3: anchor NO se mueve

            if classification is None:
                # Sin candidato: MIN_DELTA (C.6: post-clasificacion)
                if (state['anchor'] is not None
                        and d_anchor < MIN_DISTANCE_DELTA_M):
                    n_minDelta += 1
                    entry['action'] = 'reject_min_delta'
                else:
                    if variant == 'pair':
                        dist += d_pair
                    else:
                        dist += d_anchor
                    entry['action'] = 'accept'
                    state['anchor'] = {
                        'lat': fix['latitude'],
                        'lon': fix['longitude'],
                        'measuredAt': fix['measuredAt'],
                    }
                    state['last_accepted_anchor_at'] = fix['measuredAt']

            entry['classification'] = classification

        entry['distance_cumulative'] = dist
        entry['anchor_after'] = dict(state['anchor']) if state['anchor'] else None

        # FASE 4: SIEMPRE actualizar recepcion
        state['last_received_at_ms'] = fix['receivedAt']
        state['last_fix_id'] = 'fix_' + str(i)
        prev_fix = fix

        trace.append(entry)

    return {
        'dist_m': dist,
        'n_gapReal_C': n_gapReal,
        'n_ruido_C': n_ruido,
        'n_minDelta_C': n_minDelta,
        'n_acc_C': n_acc,
        'gap_events': state['gap_events'],
        'trace': trace,
        'method': 'C',
        'variant': variant,
    }


# =========================================================================
# Registry
# =========================================================================

METHODS = {
    'A':                lambda fixes: method_a(fixes),
    'B':                lambda fixes: method_b_prod(fixes),
    'C_orig':           lambda fixes: method_c(fixes, 'orig'),
    'C_pair':           lambda fixes: method_c(fixes, 'pair'),
    'C_var':            lambda fixes: method_c(fixes, 'var'),
    'C_ctrl_no_event':  lambda fixes: method_c(fixes, 'ctrl_no_event'),
    'C_and_speed':      lambda fixes: method_c(fixes, 'and_speed'),
    'C_v2':             lambda fixes: method_c(fixes, 'v2'),
}


if __name__ == '__main__':
    import sys
    import json
    if len(sys.argv) < 2:
        print('Uso: python3 methods.py <fixes.jsonl> [method= A|B|C_orig|...]')
        sys.exit(1)
    fixes = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    m = sys.argv[2] if len(sys.argv) > 2 else 'A'
    if m not in METHODS:
        print('Metodo invalido. Opciones: ' + ', '.join(METHODS.keys()))
        sys.exit(1)
    result = METHODS[m](fixes)
    # No imprimir trace entero (puede ser enorme)
    print(json.dumps({
        'method': result['method'],
        'variant': result.get('variant'),
        'dist_m': round(result['dist_m'], 3),
        'n_gapRestart': result.get('n_gapRestart_A')
                         or result.get('n_gapRestart_B'),
        'n_gapReal_C': result.get('n_gapReal_C'),
        'n_ruido_C': result.get('n_ruido_C'),
        'n_gap_events': len(result.get('gap_events', [])),
        'fidelity': result.get('fidelity'),
    }, indent=2))
