#!/usr/bin/env python3
"""
validacion_oraculo.py - Oracle Validation 001 (memo 61).

10 estados controlados. 4 horizontes (5/15/30/45s).
Criterios de PASS/FAIL definidos antes de correr.

Criterios (de memo 61 seccion 6):
1. frenar no gana en horizonte 45s en mas de 1 de los 10 estados.
2. Ganador en horizonte 5s y 45s coincide en >=70% de los estados,
   o la transicion es monotona.
3. Cero INVALID en estados sin riesgo evidente.
"""

import math
from simulador_polaris import Barco
from oraculo import Oracle, HORIZONTES_S


# Los 10 estados de prueba
# Barco en (0,0) heading 0 (norte) quieto sin viento, salvo indicacion.
ESTADOS = [
    {"nombre": "meta_norte_100m",      "meta": (0, -100),    "yaw": 0,       "sog": 0, "viento": (0, 0)},
    {"nombre": "meta_este_100m",       "meta": (100, 0),     "yaw": 0,       "sog": 0, "viento": (0, 0)},
    {"nombre": "meta_sur_100m",        "meta": (0, 100),     "yaw": 0,       "sog": 0, "viento": (0, 0)},
    {"nombre": "meta_oeste_100m",      "meta": (-100, 0),    "yaw": 0,       "sog": 0, "viento": (0, 0)},
    {"nombre": "meta_noreste_141m",    "meta": (100, -100),  "yaw": 0,       "sog": 0, "viento": (0, 0)},
    {"nombre": "meta_noroeste_141m",   "meta": (-100, -100), "yaw": 0,       "sog": 0, "viento": (0, 0)},
    {"nombre": "meta_sureste_141m",    "meta": (100, 100),   "yaw": 0,       "sog": 0, "viento": (0, 0)},
    {"nombre": "meta_suroeste_141m",   "meta": (-100, 100),  "yaw": 0,       "sog": 0, "viento": (0, 0)},
    {"nombre": "meta_cerca_20m",       "meta": (0, -20),     "yaw": 0,       "sog": 0, "viento": (0, 0)},
    {"nombre": "meta_lejos_300m",      "meta": (300, 0),     "yaw": 0,       "sog": 0, "viento": (0, 0)},
]


def crear_barco(estado):
    b = Barco()
    b.pos_x, b.pos_z = 0.0, 0.0
    b.yaw = math.radians(estado["yaw"])
    b.vel_x, b.vel_z = 0.0, 0.0
    b.viento_intensidad_kn = estado["viento"][0]
    b.viento_direccion_deg = estado["viento"][1]
    return b


def correr_validacion():
    orac = Oracle()
    resultados = []

    print("=== ORACLE VALIDATION 001 ===")
    print("10 estados x 4 horizontes = " + str(len(ESTADOS) * len(HORIZONTES_S)) + " mediciones")
    print()

    for est in ESTADOS:
        b = crear_barco(est)
        meta_x, meta_z = est["meta"]
        detalle = orac.elegir_con_detalle(b, meta_x, meta_z)
        ganadores = {}
        for h in HORIZONTES_S:
            h_key = round(h, 1)
            mejor_h = None
            mejor_p = -999999.0
            for d in detalle["detalle"]:
                p = d["progreso_por_horizonte"].get(h_key, 0.0)
                if p > mejor_p:
                    mejor_p = p
                    mejor_h = d["receta"]
            ganadores[h_key] = mejor_h
        resultados.append({
            "estado": est["nombre"],
            "ganador_5s": ganadores[5.0],
            "ganador_15s": ganadores[15.0],
            "ganador_30s": ganadores[30.0],
            "ganador_45s": ganadores[45.0],
            "detalle": detalle["detalle"],
        })
        print(est["nombre"] + ": 5s=" + ganadores[5.0] + " 15s=" + ganadores[15.0]
              + " 30s=" + ganadores[30.0] + " 45s=" + ganadores[45.0])

    return resultados


def aplicar_criterios(resultados):
    print()
    print("=== CRITERIOS PASS/FAIL ===")
    print()

    # Criterio 1: frenar no gana en 45s en mas de 1/10 estados
    gana_frenar_45 = sum(1 for r in resultados if r["ganador_45s"] == "frenar")
    crit1 = gana_frenar_45 <= 1
    print("Criterio 1: frenar gana en 45s en " + str(gana_frenar_45) + "/10 estados")
    print("  Requerido: <= 1. Resultado: " + ("PASS" if crit1 else "FAIL"))
    print()

    # Criterio 2: coincidencia 5s vs 45s >= 70% O transicion monotona
    coincidencias = sum(1 for r in resultados if r["ganador_5s"] == r["ganador_45s"])
    ratio = coincidencias / len(resultados)
    crit2a = ratio >= 0.70
    print("Criterio 2a (coincidencia 5s vs 45s): " + str(coincidencias) + "/10 = "
          + str(round(ratio * 100, 1)) + "%")
    print("  Requerido: >= 70%. Resultado: " + ("PASS" if crit2a else "NO"))

    # Criterio 2b: transicion monotona
    def es_monotona(g5, g15, g30, g45):
        # Armar la secuencia sin duplicados consecutivos
        seq = [g5]
        for g in [g15, g30, g45]:
            if g != seq[-1]:
                seq.append(g)
        # Monotona = ninguna receta reaparece despues de haber cambiado a otra
        vistos = set()
        anterior = None
        for receta in seq:
            if receta in vistos and receta != anterior:
                return False
            vistos.add(receta)
            anterior = receta
        return True

    monotonos = 0
    for r in resultados:
        if es_monotona(r["ganador_5s"], r["ganador_15s"], r["ganador_30s"], r["ganador_45s"]):
            monotonos += 1

    ratio_mono = monotonos / len(resultados)
    crit2b = ratio_mono >= 0.80
    print()
    print("Criterio 2b (transicion monotona): " + str(monotonos) + "/10 = "
          + str(round(ratio_mono * 100, 1)) + "%")
    print("  Requerido: >= 80%. Resultado: " + ("PASS" if crit2b else "FAIL"))
    print()

    crit2 = crit2a or crit2b
    print("Criterio 2 (global): " + ("PASS" if crit2 else "FAIL"))
    print()

    # Criterio 3: cero safety_violation en estados sin riesgo evidente
    total_invalid = 0
    for r in resultados:
        for d in r["detalle"]:
            if d["seguro"] is False:
                total_invalid += 1
    crit3 = total_invalid == 0
    print("Criterio 3: safety_violation en estados sin riesgo = " + str(total_invalid))
    print("  Requerido: 0. Resultado: " + ("PASS" if crit3 else "FAIL"))

    print()
    veredicto = "PASS" if (crit1 and crit2 and crit3) else "FAIL"
    print("=== VEREDICTO: " + veredicto + " ===")
    return veredicto


if __name__ == "__main__":
    resultados = correr_validacion()
    veredicto = aplicar_criterios(resultados)
