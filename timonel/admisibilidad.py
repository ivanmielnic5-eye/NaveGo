#!/usr/bin/env python3
"""admisibilidad.py - Capa 1 del sistema hibrido.

Dado un estado del barco, computa el conjunto de acciones legalmente
admisibles. Deterministico y auditable.

Reglas:
- corregir_rumbo: SIEMPRE admisible.
- ir_a_punto: SIEMPRE admisible.
- frenar: admisible si sog > 0.5 kn (si ya esta parado, no hace falta).
- terminar: admisible SOLO si dist < 15m (radio de llegada).

Referencia: EXPEDIENTE/80 seccion 2 (capa 1).
"""

TOL_TERMINAL = 15.0
SOG_MIN_FRENAR = 0.5

ACCIONES = ["corregir_rumbo", "ir_a_punto", "frenar", "terminar"]


def acciones_admisibles(dist_a_meta, sog_kn):
    """Devuelve la lista de acciones admisibles dado el estado.

    Args:
        dist_a_meta: distancia a la meta en metros.
        sog_kn: speed over ground en nudos.

    Returns:
        Lista de strings con las acciones admisibles.
    """
    admisibles = ["corregir_rumbo", "ir_a_punto"]
    if sog_kn > SOG_MIN_FRENAR:
        admisibles.append("frenar")
    if dist_a_meta < TOL_TERMINAL:
        admisibles.append("terminar")
    return admisibles


def es_admisible(accion, dist_a_meta, sog_kn):
    """Devuelve True si la accion es admisible en el estado dado."""
    return accion in acciones_admisibles(dist_a_meta, sog_kn)


def validar_parametro(accion, parametro):
    """Valida el parametro de una accion. Devuelve (ok, motivo).

    Reglas:
    - corregir_rumbo: parametro numerico en [0, 360].
    - ir_a_punto: parametro lista/tuple de 2 numericos.
    - frenar: parametro None o ignorado.
    - terminar: parametro None o ignorado.
    """
    if accion == "corregir_rumbo":
        if parametro is None:
            return False, "corregir_rumbo sin parametro"
        if isinstance(parametro, bool) or not isinstance(parametro, (int, float)):
            return False, "corregir_rumbo parametro no numerico"
        if not (0.0 <= float(parametro) <= 360.0):
            return False, "corregir_rumbo parametro fuera de [0,360]"
        return True, None
    if accion == "ir_a_punto":
        if not isinstance(parametro, (list, tuple)) or len(parametro) != 2:
            return False, "ir_a_punto sin [x, z]"
        for v in parametro:
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                return False, "ir_a_punto coordenada no numerica"
        return True, None
    if accion in ("frenar", "terminar"):
        return True, None
    return False, "accion desconocida: " + str(accion)
