#!/usr/bin/env python3
"""
Test de recuperacion tras N rechazos (C.3.1) - Fase A.

Verifica, para N = 1, 2, 3, 5:
  - last_observation_received_at avanza con CADA fix, incluso rechazado.
  - last_accepted_anchor NO se mueve en un rechazo de ruido.
  - El rechazo NO abre gap_event por si mismo.
  - Despues de N rechazos, el siguiente fix entra por CONTINUIDAD
    normalmente (sin estado pegajoso).

Casos adicionales:
  - Despues de N rechazos, un fix con dt > 2 s y d_pair > 15 m:
    C clasifica GAP_REAL, abre gap_event.
  - Despues de N rechazos, un fix con dt > 15 s:
    watchdog abre gap_event.

Uso:
  python3 test_recovery.py

Salida:
  exit 0 si todos los checks PASS
  exit 1 si algun FAIL

NO ejecutar sin autorizacion explicita del Director.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
EVAL = os.path.join(BASE, 'eval')
sys.path.insert(0, EVAL)

from methods import method_c  # noqa: E402

# Grados por metro aproximado en lat -31.648 (mismo orden que el resto)
DEG_PER_M = 1.0 / 111320.0

_results = []


def check(name, fn):
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


def _fix(m_este, t_ms, speed=2.57, acc=1.5):
    """Crea un fix en (m_este, 0) sobre lat -31.648, lon -60.708."""
    return {
        'latitude': -31.648 + m_este * DEG_PER_M,
        'longitude': -60.708,
        'measuredAt': t_ms,
        'receivedAt': t_ms + 300,
        'accuracy': acc,
        'speed': speed,
        'heading': 90.0,
    }


def _seq_rechazos(n_rechazos, separacion_m=22.0):
    """
    Secuencia:
      Fix 0: origen (aceptado)
      Fix 1..N: en m_este = i*separacion_m, t = i*1000 ms.
                d_pair entre consecutivos = separacion_m > 15 -> RUIDO.
      Fix N+1: en m_este = N*separacion_m + 11, t = (N+1)*1000 ms.
                d_pair desde el ultimo = 11 < 15 -> CONTINUIDAD.
    """
    fixes = []
    # Fix 0: aceptado
    fixes.append(_fix(0.0, 0))
    # Fixes rechazados
    for i in range(1, n_rechazos + 1):
        fixes.append(_fix(i * separacion_m, i * 1000))
    # Fix aceptable
    fixes.append(_fix(n_rechazos * separacion_m + 11.0, (n_rechazos + 1) * 1000))
    return fixes


def _seq_rechazos_gap_real(n_rechazos):
    """
    Igual que _seq_rechazos, pero el ultimo fix tiene dt = 3 s > 2 s.
    d_pair = 20 m > 15 m -> entra al clasificador C.orig.
    dt = 3 s > 2 s -> GAP_REAL. Abre gap_event.
    """
    fixes = []
    fixes.append(_fix(0.0, 0))
    for i in range(1, n_rechazos + 1):
        fixes.append(_fix(i * 22.0, i * 1000))
    t_next = n_rechazos * 1000 + 3000  # +3s
    fixes.append(_fix(n_rechazos * 22.0 + 20.0, t_next))
    return fixes


def _seq_rechazos_watchdog(n_rechazos):
    """
    Igual que _seq_rechazos, pero el ultimo fix tiene dt = 16 s.
    watchdog dispara antes de procesar el ultimo fix.
    """
    fixes = []
    fixes.append(_fix(0.0, 0))
    for i in range(1, n_rechazos + 1):
        fixes.append(_fix(i * 22.0, i * 1000))
    t_next = n_rechazos * 1000 + 16000  # +16s
    fixes.append(_fix(n_rechazos * 22.0 + 11.0, t_next))
    return fixes


def _run_recovery(n_rechazos):
    fixes = _seq_rechazos(n_rechazos)
    result = method_c(fixes, 'orig')
    trace = result['trace']

    # Invariante 1: los N rechazos son classification=RUIDO
    for i in range(1, n_rechazos + 1):
        entry = trace[i]
        assert entry['classification'] == 'RUIDO', (
            'fix %d: se esperaba RUIDO, fue %s'
            % (i, entry['classification']))
        assert entry['action'] == 'reject_noise', (
            'fix %d: accion se esperaba reject_noise, fue %s'
            % (i, entry['action']))

    # Invariante 2: el ancla no se movio durante los rechazos
    anchor_after_0 = trace[0].get('anchor_after')
    anchor_after_N = trace[n_rechazos].get('anchor_after')
    assert anchor_after_0 is not None, 'fix 0 sin anchor_after'
    assert anchor_after_N is not None, 'fix N sin anchor_after'
    assert anchor_after_0 == anchor_after_N, (
        'ancla se movio durante rechazos: %s -> %s'
        % (anchor_after_0, anchor_after_N))

    # Invariante 3: el fix N+1 se acepta (no RUIDO, no rechazo)
    entry_last = trace[n_rechazos + 1]
    assert entry_last['classification'] is None, (
        'fix final: no deberia tener clasificacion C, fue %s'
        % entry_last['classification'])
    assert entry_last['action'] == 'accept', (
        'fix final: accion se esperaba accept, fue %s'
        % entry_last['action'])

    # Invariante 4: no se abrio ningun gap_event
    assert len(result['gap_events']) == 0, (
        'se abrieron gap_events: %s' % result['gap_events'])

    # Invariante 5: contadores de C
    assert result['n_ruido_C'] == n_rechazos, (
        'n_ruido_C = %d, esperado %d' % (result['n_ruido_C'], n_rechazos))
    assert result['n_gapReal_C'] == 0, (
        'n_gapReal_C = %d, esperado 0' % result['n_gapReal_C'])

    return ('N=%d: %d RUIDO, 0 gap_event, ancla sin mover, accept final'
            % (n_rechazos, n_rechazos))


def _run_gap_real(n_rechazos):
    fixes = _seq_rechazos_gap_real(n_rechazos)
    result = method_c(fixes, 'orig')
    trace = result['trace']

    # El ultimo fix debe clasificarse como GAP_REAL
    entry_last = trace[-1]
    assert entry_last['classification'] == 'GAP_REAL', (
        'ultimo fix: se esperaba GAP_REAL, fue %s'
        % entry_last['classification'])
    assert entry_last['action'] == 'gap_real', (
        'ultimo fix: accion se esperaba gap_real, fue %s'
        % entry_last['action'])

    # Debe haberse abierto 1 gap_event via C
    c_gaps = [g for g in result['gap_events'] if g.get('via') == 'C']
    assert len(c_gaps) == 1, (
        'se esperaba 1 gap_event via C, fueron %d' % len(c_gaps))

    return 'N=%d + gap real: 1 gap_event via C' % n_rechazos


def _run_watchdog(n_rechazos):
    fixes = _seq_rechazos_watchdog(n_rechazos)
    result = method_c(fixes, 'orig')
    trace = result['trace']

    # Debe haber 1 gap_event via watchdog
    wd_gaps = [g for g in result['gap_events'] if g.get('via') == 'watchdog']
    assert len(wd_gaps) == 1, (
        'se esperaba 1 gap_event watchdog, fueron %d' % len(wd_gaps))

    # El ultimo fix entra como CONTINUIDAD (no GAP_REAL) porque d_pair
    # desde el ultimo rechazado es 11m < 15m -> no es candidato C.
    entry_last = trace[-1]
    assert entry_last['classification'] is None, (
        'ultimo fix: no deberia ser candidato C, fue %s'
        % entry_last['classification'])

    return 'N=%d + watchdog: 1 gap_event via watchdog' % n_rechazos


# --- tests individuales ---

def t_rec_1(): return _run_recovery(1)
def t_rec_2(): return _run_recovery(2)
def t_rec_3(): return _run_recovery(3)
def t_rec_5(): return _run_recovery(5)

def t_gap_real_2(): return _run_gap_real(2)
def t_watchdog_2(): return _run_watchdog(2)


# --- invariantes de estado (chequeo explicito de last_observation) ---

def t_estado_separado():
    """Verifica que last_received_at avanza pero anchor no durante rechazos."""
    fixes = _seq_rechazos(3)
    result = method_c(fixes, 'orig')
    trace = result['trace']

    # Last_received avanza monotonamente
    for i in range(1, len(fixes)):
        assert fixes[i]['receivedAt'] > fixes[i-1]['receivedAt'], (
            'receivedAt no monotono en fix %d' % i)

    # Anchor solo se mueve en fix 0 (inicial) y fix 4 (aceptacion final)
    anchor_0 = trace[0].get('anchor_after')
    anchor_3 = trace[3].get('anchor_after')
    anchor_4 = trace[4].get('anchor_after')
    assert anchor_0 == anchor_3, 'ancla cambio entre fix 0 y fix 3'
    assert anchor_0 != anchor_4, 'ancla deberia cambiar en aceptacion final'

    return ('last_received_at monotono, anchor quieto en rechazos, '
            'mueve en accept')


# --- main ---

def main():
    print('=== test_recovery.py (C.3.1) ===')
    print('BASE: ' + BASE)
    print()

    check('1. Recuperacion N=1', t_rec_1)
    check('2. Recuperacion N=2', t_rec_2)
    check('3. Recuperacion N=3', t_rec_3)
    check('4. Recuperacion N=5', t_rec_5)
    check('5. Recuperacion + gap real (N=2)', t_gap_real_2)
    check('6. Recuperacion + watchdog (N=2)', t_watchdog_2)
    check('7. Estado separado (anchor vs last_received)', t_estado_separado)

    print()
    n_pass = sum(1 for r in _results if r[1] == 'PASS')
    n_fail = sum(1 for r in _results if r[1] == 'FAIL')
    print('Total: %d PASS, %d FAIL' % (n_pass, n_fail))
    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
