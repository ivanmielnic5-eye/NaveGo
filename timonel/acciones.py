#!/usr/bin/env python3
"""acciones.py - Interfaz de alto nivel del LLM.

Reemplaza las "recetas" (corregir_rumbo, ir_a_punto, frenar, terminar)
por acciones como setpoints que el PID ejecuta internamente.

Acciones:
- rumbo(theta): mantener un rumbo dado.
- ir_a(punto): navegar a un punto. LOS genera el rumbo, PID ejecuta.
- frenar: reducir velocidad.
- terminar: accion logica (solo si dist < 15m).

Diferencia con v1:
- v1: el LLM emitia "corregir_rumbo a 90, timon_ms=500".
  Mezclaba intencion (ir a rumbo 90) con ejecucion (mover timon).
- v2: el LLM emite solo el setpoint. El PID decide como mover el timon.

Referencia: EXPEDIENTE/89, respuesta de Claude.
"""

import math
from simulador_polaris import Barco, DT
from controlador_pid import PIDRumbo, delta_angulo, rumbo_a_meta


# ============================================================
# UTILIDADES
# ============================================================

def _distancia(b: Barco, meta_x: float, meta_z: float) -> float:
    dx = meta_x - b.pos_x
    dz = meta_z - b.pos_z
    return math.sqrt(dx*dx + dz*dz)


# ============================================================
# ACCION 1: rumbo(theta)
# ============================================================

def accion_rumbo(b: Barco, theta: float, horizonte_s: float,
                 pid: PIDRumbo = None) -> tuple[bool, dict]:
    """Mantiene el rumbo theta durante TODO el horizonte.

    El PID ejecuta internamente. Avance siempre activo (1.0) para
    tener gobierno.
    """
    if pid is None:
        pid = PIDRumbo()
    else:
        pid.reset()

    t0 = b.t
    total_steps = int(round(horizonte_s / DT))

    for _ in range(total_steps):
        timon = pid.paso(b, theta)
        b.aplicar_comando(timon=timon, timon_ms=100,
                          avance=1.0, avance_ms=100)
        b.paso()

    hdg_final = b.heading_deg()
    err_final = delta_angulo(hdg_final, theta)
    dist_final = _distancia(b, 0.0, 0.0)  # sin meta, solo informativo

    return True, {
        "t_total": round(b.t - t0, 2),
        "hdg_final": round(hdg_final, 1),
        "error_final": round(err_final, 2),
    }


# ============================================================
# ACCION 2: ir_a(punto)
# ============================================================

def accion_ir_a(b: Barco, meta_x: float, meta_z: float,
                horizonte_s: float, pid: PIDRumbo = None) -> tuple[bool, dict]:
    """Navega hacia la meta durante TODO el horizonte.

    A cada ciclo (0.5s), calcula el rumbo hacia la meta y se lo pasa
    al PID. El PID ejecuta el timon.
    """
    if pid is None:
        pid = PIDRumbo()
    else:
        pid.reset()

    t0 = b.t
    total_steps = int(round(horizonte_s / DT))
    steps_per_ciclo = int(0.5 / DT)  # recalcular rumbo cada 0.5s
    steps_done = 0

    while steps_done < total_steps:
        rumbo_obj = rumbo_a_meta(b, meta_x, meta_z)
        pasos_este_ciclo = min(steps_per_ciclo, total_steps - steps_done)

        for _ in range(pasos_este_ciclo):
            timon = pid.paso(b, rumbo_obj)
            b.aplicar_comando(timon=timon, timon_ms=100,
                              avance=1.0, avance_ms=100)
            b.paso()

        steps_done += pasos_este_ciclo

    dist_final = _distancia(b, meta_x, meta_z)
    return True, {
        "t_total": round(b.t - t0, 2),
        "dist_final": round(dist_final, 2),
        "hdg_final": round(b.heading_deg(), 1),
    }


# ============================================================
# ACCION 3: frenar
# ============================================================

def accion_frenar(b: Barco, horizonte_s: float,
                  sog_objetivo_kn: float = 0.3) -> tuple[bool, dict]:
    """Reduce velocidad a sog_objetivo durante TODO el horizonte.

    Estrategia: control proporcional de avance.
    """
    t0 = b.t
    total_steps = int(round(horizonte_s / DT))
    steps_per_ciclo = int(0.5 / DT)
    steps_done = 0

    while steps_done < total_steps:
        sog_actual = b.sog_kn()
        # Control proporcional simple
        if sog_actual > sog_objetivo_kn:
            # Avance en contra proporcional a la velocidad
            factor = min(1.0, (sog_actual - sog_objetivo_kn) / 3.0)
            avance = -factor
        else:
            avance = 0.0

        pasos_este_ciclo = min(steps_per_ciclo, total_steps - steps_done)
        b.aplicar_comando(timon=0.0, timon_ms=0,
                          avance=avance, avance_ms=500)
        for _ in range(pasos_este_ciclo):
            b.paso()
        steps_done += pasos_este_ciclo

    return True, {
        "t_total": round(b.t - t0, 2),
        "sog_final": round(b.sog_kn(), 3),
    }


# ============================================================
# ACCION 4: terminar
# ============================================================

def accion_terminar(b: Barco, meta_x: float, meta_z: float,
                    horizonte_s: float) -> tuple[bool, dict]:
    """Accion logica terminal. No ejecuta maniobra.

    Valida solo si dist < 15m. No consume horizonte.
    """
    dist = _distancia(b, meta_x, meta_z)
    if dist < 15.0:
        return True, {
            "t_total": 0.0,
            "dist_final": round(dist, 2),
            "mission_complete": True,
        }
    return False, {
        "t_total": 0.0,
        "dist_final": round(dist, 2),
        "motivo": "terminar_invalido_dist_" + str(round(dist, 1)),
    }


# ============================================================
# MAPA DE ACCIONES (para el Entrenador)
# ============================================================

ACCIONES = {
    "rumbo": accion_rumbo,
    "ir_a": accion_ir_a,
    "frenar": accion_frenar,
    "terminar": accion_terminar,
}
