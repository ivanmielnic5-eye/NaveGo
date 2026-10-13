#!/usr/bin/env python3
"""etiquetar.py - Funcion unica de etiquetado (F0 bloqueante 1).

Usada por banco, entrenador y acciones. Elimina el desalineamiento
entre T fijo y T variable.

Referencia: borradores/f0_diseno_v2.md, bloqueante 1.
"""


def _aplicar_operador(valor, op, umbral):
    """Aplica un operador declarado en el schema."""
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
    """Extrae valor y operador de un bloque del schema."""
    if bloque is None:
        return None, None
    if not isinstance(bloque, dict):
        return bloque, "<"
    return bloque.get("valor"), bloque.get("operador", "<")


def etiquetar(mision, estado):
    """Etiqueta un estado segun la mision.

    Args:
        mision: MisionConfig cargada (dict inmutable).
        estado: dict con 'd' (m) y opcionalmente 'v' (kn).

    Returns:
        str: 'terminar', 'ir_a', o 'abstenerse'.
    """
    goal = mision["goal"]

    # Distancia (siempre requerida)
    d_val, d_op = _extraer_valor_umbral(goal.get("arrival_distance_threshold"))
    # Velocidad (opcional, depende de la mision)
    v_val, v_op = _extraer_valor_umbral(goal.get("arrival_speed_limit"))

    d = estado.get("d")
    v = estado.get("v")

    if d is None:
        return "abstenerse"

    if d_val is not None:
        dist_ok = _aplicar_operador(d, d_op, d_val)
    else:
        dist_ok = True

    if v_val is not None:
        if v is None:
            return "abstenerse"
        vel_ok = _aplicar_operador(v, v_op, v_val)
    else:
        vel_ok = True

    if dist_ok and vel_ok:
        return "terminar"
    return "ir_a"


def etiquetar_por_T(d, T):
    """Helper para casos donde no hay una MisionConfig cargada.

    Reproduce el comportamiento del banco A2 (T variable, solo
    distancia). Usado para regenerar bancos historicos.
    """
    return "terminar" if d < T else "ir_a"


def etiquetar_por_T_v(d, T, v, v_max):
    """Helper para casos con velocidad (probe, 0b).

    Reproduce el comportamiento del probe y 0b.
    """
    if d < T and v <= v_max:
        return "terminar"
    return "ir_a"
