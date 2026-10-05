#!/usr/bin/env python3
"""
recetas_navegacion.py - Recetas de maniobras para Polaris.

Cada receta es una funcion que:
- Recibe un Barco (de simulador_polaris.py).
- Lee su estado (heading, posicion, velocidad).
- Aplica comandos iterativamente.
- Retorna (exito, detalle).

Las recetas NO dependen de Qwen ni de Ollama.
Se pueden ejecutar solas para probar.

Basado en: EXPEDIENTE/58 (informe LLM Notebook) + EXPEDIENTE/59 (rubricas PNA).
"""

import math
from simulador_polaris import Barco, DT, GOAL_X, GOAL_Z


# ============================================================
# UTILIDADES
# ============================================================

def delta_angulo(actual_deg: float, objetivo_deg: float) -> float:
    """Diferencia angular signed. Rango [-180, 180]."""
    d = (objetivo_deg - actual_deg + 540.0) % 360.0 - 180.0
    return d


# ============================================================
# RECETA 1: Corregir rumbo
# ============================================================

def corregir_rumbo(b: Barco, objetivo_deg: float,
                   tol_deg: float = 8.0,
                   timeout_s: float = 60.0,
                   verbose: bool = False) -> tuple[bool, dict]:
    """
    Gira el barco hasta alcanzar el angulo objetivo.

    - Aplica timon + avance (para tener prop wash).
    - Predice el overshoot (~10 grados) y aplica contra-timon antes de llegar.
    - Termina cuando |delta| < tol_deg o por timeout.

    Returns:
        (exito: bool, detalle: dict con t_total, hdg_final, delta_final)
    """
    t0 = b.t
    pasos_por_pulso = int(0.5 / DT)   # medio segundo de comandos
    intentos = 0

    while b.t - t0 < timeout_s:
        hdg = b.heading_deg()
        delta = delta_angulo(hdg, objetivo_deg)

        if abs(delta) < tol_deg:
            return True, {
                "t_total": round(b.t - t0, 2),
                "hdg_final": round(hdg, 1),
                "delta_final": round(delta, 2),
                "intentos": intentos,
            }

        # Zona muerta: si esta muy cerca y no gira, no tocar timon
        if abs(delta) < 3.0 and abs(b.yaw_rate) < 0.01:
            b.aplicar_comando(timon=0, timon_ms=0, avance=1, avance_ms=500)
            for _ in range(pasos_por_pulso):
                b.paso()
            intentos += 1
            continue

        # Prediccion de overshoot (solo si estamos girando HACIA el objetivo)
        yaw_deg_s = math.degrees(b.yaw_rate)
        aproximando = (delta > 0 and yaw_deg_s > 0) or (delta < 0 and yaw_deg_s < 0)
        overshoot_est = abs(yaw_deg_s) * 1.5

        if aproximando and abs(delta) < overshoot_est + tol_deg:
            # Frenar la rotacion
            timon = -1 if delta > 0 else 1
        else:
            # Timon normal hacia el objetivo
            timon = 1 if delta > 0 else -1

        # Aplicar pulso corto. Avance=1 siempre para tener prop wash.
        b.aplicar_comando(timon=timon, timon_ms=500,
                          avance=1, avance_ms=500)

        # Avanzar fisica medio segundo
        for _ in range(pasos_por_pulso):
            b.paso()

        intentos += 1
        if verbose and intentos % 4 == 0:
            print(f"    t={b.t-t0:.1f}s hdg={hdg:.1f}° delta={delta:.1f}° timon={timon}")

    # Timeout
    return False, {
        "t_total": round(b.t - t0, 2),
        "hdg_final": round(b.heading_deg(), 1),
        "delta_final": round(delta_angulo(b.heading_deg(), objetivo_deg), 2),
        "intentos": intentos,
        "motivo": "timeout",
    }


# ============================================================
# RECETA 2: Ir a un punto
# ============================================================

def ir_a_punto(b: Barco, meta_x: float, meta_z: float,
               tol_dist: float = 15.0,
               timeout_s: float = 300.0,
               verbose: bool = False) -> tuple[bool, dict]:
    """
    Navega desde la posicion actual hasta (meta_x, meta_z).

    Estrategia:
    - Calcula el angulo hacia la meta.
    - Corrige el rumbo si esta muy desviado (>25 grados).
    - Avanza si esta bien orientado.
    - Termina cuando dist < tol_dist o por timeout.

    Returns:
        (exito: bool, detalle)
    """
    t0 = b.t
    pasos_por_ciclo = int(1.0 / DT)

    while b.t - t0 < timeout_s:
        # Calcular angulo hacia la meta
        dx = meta_x - b.pos_x
        dz = meta_z - b.pos_z
        dist = math.sqrt(dx * dx + dz * dz)

        if dist < tol_dist:
            return True, {
                "t_total": round(b.t - t0, 2),
                "dist_final": round(dist, 1),
                "pos_final": (round(b.pos_x, 1), round(b.pos_z, 1)),
            }

        # Angulo deseado: atan2(dx, -dz) porque nuestro heading es atan2(x, -z)
        objetivo_deg = math.degrees(math.atan2(dx, -dz)) % 360.0
        hdg = b.heading_deg()
        delta = delta_angulo(hdg, objetivo_deg)

        # Decision: corregir rumbo o avanzar
        if abs(delta) > 25.0:
            # Muy desviado: corregir con timon proporcional al error
            timon = 1 if delta > 0 else -1
            b.aplicar_comando(timon=timon, timon_ms=800,
                              avance=1, avance_ms=800)
        elif abs(delta) > 5.0:
            # Desviado: corregir suave
            timon = 1 if delta > 0 else -1
            b.aplicar_comando(timon=timon, timon_ms=500,
                              avance=1, avance_ms=1000)
        else:
            # En rumbo: avanzar recto
            b.aplicar_comando(timon=0, timon_ms=0,
                              avance=1, avance_ms=1000)

        for _ in range(pasos_por_ciclo):
            b.paso()

        if verbose:
            print(f"    t={b.t-t0:.1f}s dist={dist:.1f}m hdg={hdg:.1f}° obj={objetivo_deg:.1f}° delta={delta:.1f}°")

    # Timeout
    dx = meta_x - b.pos_x
    dz = meta_z - b.pos_z
    dist = math.sqrt(dx * dx + dz * dz)
    return False, {
        "t_total": round(b.t - t0, 2),
        "dist_final": round(dist, 1),
        "pos_final": (round(b.pos_x, 1), round(b.pos_z, 1)),
        "motivo": "timeout",
    }


# ============================================================
# RECETA 3: Frenar
# ============================================================

def frenar(b: Barco, sog_objetivo_kn: float = 0.3,
           timeout_s: float = 30.0,
           verbose: bool = False) -> tuple[bool, dict]:
    """
    Detiene el barco usando reversa.

    Estrategia (informe LLM Notebook):
    - Cortar avance.
    - Aplicar reversa durante un tiempo proporcional a la velocidad.
    - Esperar inercia.

    Returns:
        (exito: bool, detalle)
    """
    t0 = b.t
    pasos_por_ciclo = int(0.5 / DT)
    fase = "corte"
    t_corte = 0.0

    while b.t - t0 < timeout_s:
        sog = b.sog_kn()

        if sog < sog_objetivo_kn:
            return True, {
                "t_total": round(b.t - t0, 2),
                "sog_final": round(sog, 2),
            }

        if fase == "corte":
            # Primer 1 segundo: solo cortar avance
            b.aplicar_comando(timon=0, timon_ms=0, avance=0, avance_ms=500)
            if b.t - t0 > 1.0:
                fase = "reversa"
        elif fase == "reversa":
            # Aplicar reversa proporcional
            if sog > 2.0:
                b.aplicar_comando(timon=0, timon_ms=0, avance=-1, avance_ms=500)
            else:
                b.aplicar_comando(timon=0, timon_ms=0, avance=-1, avance_ms=300)

        for _ in range(pasos_por_ciclo):
            b.paso()

        if verbose:
            print(f"    t={b.t-t0:.1f}s sog={sog:.2f}kn fase={fase}")

    return False, {
        "t_total": round(b.t - t0, 2),
        "sog_final": round(b.sog_kn(), 2),
        "motivo": "timeout",
    }
