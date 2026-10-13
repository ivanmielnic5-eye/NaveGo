#!/usr/bin/env python3
"""criterios_mision.py - Criterio canonico de mision completa.

Definicion formal compartida por etiquetar() (offline) y
accion_terminar() (runtime). No los acopla: ambos importan de aca.

Referencia: borradores/f0_diseno_v2.md, bloqueante 1 parte 2.
"""


def _aplicar_operador(valor, op, umbral):
    if op == "<":
        return valor < umbral
    if op == "<=":
        return valor <= umbral
    if op == ">":
        return valor > umbral
    if op == ">=":
        return valor >= umbral
    if op == "==":
        return valor == umbral
    if op == "!=":
        return valor != umbral
    raise ValueError("Operador desconocido: " + str(op))


def _extraer_valor_umbral(bloque):
    if bloque is None:
        return None, None
    if not isinstance(bloque, dict):
        return bloque, "<"
    return bloque.get("valor"), bloque.get("operador", "<")


def mision_completa(mision, d, v=None):
    """Devuelve True si el estado satisface el criterio de mision.

    Args:
        mision: MisionConfig cargada.
        d: distancia (m). Requerida.
        v: velocidad (kn). Opcional, requerida solo si la mision la exige.

    Returns:
        True -> mision completa.
        False -> no completa.
        None -> falta informacion (abstencion).
    """
    goal = mision["goal"]
    d_val, d_op = _extraer_valor_umbral(goal.get("arrival_distance_threshold"))
    v_val, v_op = _extraer_valor_umbral(goal.get("arrival_speed_limit"))

    if d_val is None:
        return None
    if not _aplicar_operador(d, d_op, d_val):
        return False
    if v_val is not None:
        if v is None:
            return None
        if not _aplicar_operador(v, v_op, v_val):
            return False
    return True
