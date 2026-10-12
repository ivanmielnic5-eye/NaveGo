#!/usr/bin/env python3
"""recetas_navegacion_v2.py - Recetas de maniobras para Polaris (version 2).

Principio: cada receta corre TODO EL HORIZONTE sin "terminar".
Nunca se detiene por alineacion, llegada o velocidad objetivo.
Lo que cambia entre recetas es el TIPO de maniobra, no la duracion.

Esto hace las comparaciones 100% justas por diseno.

Referencia: EXPEDIENTE/88.
"""

import math
from simulador_polaris import Barco, DT


# ============================================================
# UTILIDADES
# ============================================================

def delta_angulo(actual_deg: float, objetivo_deg: float) -> float:
    """Diferencia angular signed. Rango [-180, 180]."""
    d = (objetivo_deg - actual_deg + 540.0) % 360.0 - 180.0
    return d


def _rumbo_a_meta(b: Barco, meta_x: float, meta_z: float) -> float:
    """Rumbo en grados (0=norte) desde la posicion actual hacia la meta."""
    dx = meta_x - b.pos_x
    dz = meta_z - b.pos_z
    return math.degrees(math.atan2(dx, -dz)) % 360.0


# ============================================================
# RECETA 1: corregir_rumbo_v2
# ============================================================

def corregir_rumbo_v2(b: Barco, meta_x: float, meta_z: float,
                      horizonte_s: float) -> tuple[bool, dict]:
    """Gira la proa hacia la meta durante TODO el horizonte.

    No termina por alineacion. Si esta alineado, mantiene timon=0
    y sigue avanzando (avance=1) para tener prop wash.
    """
    t0 = b.t
    total_steps = int(round(horizonte_s / DT))
    steps_per_pulse = int(0.5 / DT)

    steps_done = 0
    intentos = 0
    while steps_done < total_steps:
        objetivo_deg = _rumbo_a_meta(b, meta_x, meta_z)
        hdg = b.heading_deg()
        delta = delta_angulo(hdg, objetivo_deg)

        # Timon proporcional simple (pulso)
        if abs(delta) < 3.0:
            timon = 0
        else:
            timon = 1 if delta > 0 else -1

        pasos_este_pulso = min(steps_per_pulse, total_steps - steps_done)

        b.aplicar_comando(timon=timon, timon_ms=500,
                          avance=1, avance_ms=500)

        for _ in range(pasos_este_pulso):
            b.paso()

        steps_done += pasos_este_pulso
        intentos += 1

    dist_final = math.sqrt((b.pos_x - meta_x)**2 + (b.pos_z - meta_z)**2)
    return True, {
        "t_total": round(b.t - t0, 2),
        "dist_final": round(dist_final, 2),
        "hdg_final": round(b.heading_deg(), 1),
        "intentos": intentos,
    }


# ============================================================
# RECETA 2: ir_a_punto_v2
# ============================================================

def ir_a_punto_v2(b: Barco, meta_x: float, meta_z: float,
                  horizonte_s: float) -> tuple[bool, dict]:
    """Navega hacia la meta durante TODO el horizonte.

    Corrige rumbo proporcional al delta mientras avanza.
    No termina por llegada.
    """
    t0 = b.t
    total_steps = int(round(horizonte_s / DT))
    steps_per_ciclo = int(1.0 / DT)  # ciclos de 1 segundo

    steps_done = 0
    intentos = 0
    while steps_done < total_steps:
        objetivo_deg = _rumbo_a_meta(b, meta_x, meta_z)
        hdg = b.heading_deg()
        delta = delta_angulo(hdg, objetivo_deg)

        # Decision de timon segun desvio
        if abs(delta) > 25.0:
            timon = 1 if delta > 0 else -1
            timon_ms = 800
            avance_ms = 800
        elif abs(delta) > 5.0:
            timon = 1 if delta > 0 else -1
            timon_ms = 500
            avance_ms = 1000
        else:
            timon = 0
            timon_ms = 0
            avance_ms = 1000

        pasos_este_ciclo = min(steps_per_ciclo, total_steps - steps_done)

        b.aplicar_comando(timon=timon, timon_ms=timon_ms,
                          avance=1, avance_ms=avance_ms)

        for _ in range(pasos_este_ciclo):
            b.paso()

        steps_done += pasos_este_ciclo
        intentos += 1

    dist_final = math.sqrt((b.pos_x - meta_x)**2 + (b.pos_z - meta_z)**2)
    return True, {
        "t_total": round(b.t - t0, 2),
        "dist_final": round(dist_final, 2),
        "hdg_final": round(b.heading_deg(), 1),
        "intentos": intentos,
    }


# ============================================================
# RECETA 3: frenar_v2
# ============================================================

def frenar_v2(b: Barco, horizonte_s: float,
              sog_objetivo_kn: float = 0.3) -> tuple[bool, dict]:
    """Reduce velocidad a ~0.3 kn durante TODO el horizonte.

    Una vez en la velocidad objetivo, mantiene.
    """
    t0 = b.t
    total_steps = int(round(horizonte_s / DT))
    steps_per_ciclo = int(1.0 / DT)

    steps_done = 0
    intentos = 0
    while steps_done < total_steps:
        sog = b.sog_kn()

        if sog > sog_objetivo_kn + 0.1:
            # Frenar: avance en contra
            timon = 0
            avance = -1
        elif sog > sog_objetivo_kn:
            # Mantener suave
            timon = 0
            avance = 0
        else:
            # Ya esta lento, mantener
            timon = 0
            avance = 0

        pasos_este_ciclo = min(steps_per_ciclo, total_steps - steps_done)

        b.aplicar_comando(timon=timon, timon_ms=0,
                          avance=avance, avance_ms=1000)

        for _ in range(pasos_este_ciclo):
            b.paso()

        steps_done += pasos_este_ciclo
        intentos += 1

    return True, {
        "t_total": round(b.t - t0, 2),
        "sog_final": round(b.sog_kn(), 2),
        "intentos": intentos,
    }


# ============================================================
# RECETA 4: terminar_v2
# ============================================================

def terminar_v2(b: Barco, meta_x: float, meta_z: float,
                horizonte_s: float) -> tuple[bool, dict]:
    """Accion logica terminal. NO ejecuta maniobra fisica.

    - Si dist < 15m: retorna exito=True, mission_complete.
    - Si dist >= 15m: retorna exito=False, invalido.

    NO consume tiempo simulado. Es un evento logico, no una maniobra.
    El Entrenador lo trata con la prioridad mission_complete.
    """
    dist = math.sqrt((b.pos_x - meta_x)**2 + (b.pos_z - meta_z)**2)
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
# TESTS
# ============================================================

if __name__ == "__main__":
    from simulador_polaris import Barco

    print("=== TESTS DE DURACION ===")
    print()

    horizonte = 10.0  # 10 segundos

    # Test 1: corregir_rumbo_v2 dura exactamente 10s
    b = Barco()
    b.pos_x, b.pos_z = 0.0, 0.0
    b.yaw = math.radians(90.0)
    t_inicial = b.t
    exito, detalle = corregir_rumbo_v2(b, 100.0, 100.0, horizonte)
    dur = b.t - t_inicial
    print(f"  corregir_rumbo_v2: duro {dur:.2f}s (esperado {horizonte})")
    print(f"    dist_final={detalle['dist_final']}m")

    # Test 2: ir_a_punto_v2
    b = Barco()
    b.pos_x, b.pos_z = 0.0, 0.0
    b.yaw = math.radians(45.0)
    t_inicial = b.t
    exito, detalle = ir_a_punto_v2(b, 100.0, 100.0, horizonte)
    dur = b.t - t_inicial
    print(f"  ir_a_punto_v2: duro {dur:.2f}s (esperado {horizonte})")
    print(f"    dist_final={detalle['dist_final']}m")

    # Test 3: frenar_v2
    b = Barco()
    b.pos_x, b.pos_z = 0.0, 0.0
    b.yaw = math.radians(45.0)
    sog_ms = 5.0 / 1.94384449
    b.vel_x = math.sin(b.yaw) * sog_ms
    b.vel_z = -math.cos(b.yaw) * sog_ms
    t_inicial = b.t
    exito, detalle = frenar_v2(b, horizonte)
    dur = b.t - t_inicial
    print(f"  frenar_v2: duro {dur:.2f}s (esperado {horizonte})")
    print(f"    sog_final={detalle['sog_final']}kn")

    # Test 4: terminar_v2 (no consume tiempo)
    b = Barco()
    b.pos_x, b.pos_z = 0.0, 0.0
    t_inicial = b.t
    exito, detalle = terminar_v2(b, 5.0, 5.0, horizonte)
    dur = b.t - t_inicial
    print(f"  terminar_v2 (cerca): duro {dur:.2f}s | exito={exito} | {detalle.get('motivo', 'mision_completa')}")

    b = Barco()
    b.pos_x, b.pos_z = 0.0, 0.0
    exito, detalle = terminar_v2(b, 100.0, 100.0, horizonte)
    print(f"  terminar_v2 (lejos): exito={exito} | {detalle.get('motivo', 'mision_completa')}")
