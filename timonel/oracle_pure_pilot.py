#!/usr/bin/env python3
"""
oracle_pure_pilot.py - Oracle-Pure Pilot (memo 61).

Deja que el oraculo maneje misiones completas usando el controlador
determinista (las recetas). Sin Qwen. Sin memoria.

Mide: success_rate, time_to_goal, overshoot, path_efficiency.
"""

import argparse
import json
import math
import random
import time
from datetime import datetime
from pathlib import Path

from simulador_polaris import Barco, DT
from recetas_navegacion import corregir_rumbo, ir_a_punto, frenar
from oraculo import Oracle


MAX_PASOS = 20
TOL_LLEGADA_M = 15.0


def distancia_a(b, mx, mz):
    return math.sqrt((b.pos_x - mx)**2 + (b.pos_z - mz)**2)


def ejecutar_receta(b, meta_x, meta_z, receta):
    """Ejecuta una receta en el barco. Devuelve None."""
    if receta == "corregir_rumbo":
        dx = meta_x - b.pos_x
        dz = meta_z - b.pos_z
        rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
        corregir_rumbo(b, objetivo_deg=rumbo, timeout_s=60.0)
    elif receta == "ir_a_punto":
        ir_a_punto(b, meta_x, meta_z, tol_dist=TOL_LLEGADA_M, timeout_s=90.0)
    elif receta == "frenar":
        frenar(b, timeout_s=30.0)


def correr_episodio(meta_x, meta_z, timeout_s=300.0, verbose=False):
    """Corre un episodio completo con el oraculo pilotando."""
    orac = Oracle()
    b = Barco()
    t_inicio = b.t
    pasos = 0

    while b.t - t_inicio < timeout_s and pasos < MAX_PASOS:
        dist = distancia_a(b, meta_x, meta_z)
        if dist < TOL_LLEGADA_M:
            return {
                "resultado": "LLEGO",
                "dist_final": round(dist, 1),
                "t_total": round(b.t - t_inicio, 1),
                "pasos": pasos,
            }
        receta = orac.elegir(b, meta_x, meta_z)
        if verbose:
            print("  paso " + str(pasos + 1) + ": " + receta + " dist=" + str(round(dist, 1)))
        ejecutar_receta(b, meta_x, meta_z, receta)
        pasos += 1

    dist_final = distancia_a(b, meta_x, meta_z)
    return {
        "resultado": "TIMEOUT" if pasos < MAX_PASOS else "FRACASO",
        "dist_final": round(dist_final, 1),
        "t_total": round(b.t - t_inicio, 1),
        "pasos": pasos,
    }


def generar_meta(rng):
    dist = rng.uniform(80.0, 220.0)
    ang = rng.uniform(0.0, 360.0)
    return round(dist * math.sin(math.radians(ang)), 1), round(-dist * math.cos(math.radians(ang)), 1)


def correr_batch(n, seed=None, timeout_s=300.0):
    rng = random.Random(seed) if seed is not None else random.Random()
    resultados = []
    t0 = time.time()

    print("=== ORACLE-PURE PILOT ===")
    print("N=" + str(n) + " seed=" + str(seed))
    print()

    for i in range(n):
        mx, mz = generar_meta(rng)
        r = correr_episodio(mx, mz, timeout_s=timeout_s)
        r["meta"] = (mx, mz)
        resultados.append(r)
        print("[" + str(i + 1).rjust(3) + "/" + str(n) + "] meta=(" + str(mx) + "," + str(mz) + ")"
              + " -> " + r["resultado"] + " dist=" + str(r["dist_final"])
              + " t=" + str(r["t_total"]) + " pasos=" + str(r["pasos"]))

    exitos = sum(1 for r in resultados if r["resultado"] == "LLEGO")
    timeouts = sum(1 for r in resultados if r["resultado"] == "TIMEOUT")
    fracasos = sum(1 for r in resultados if r["resultado"] == "FRACASO")
    dist_prom = (sum(r["dist_final"] for r in resultados if r["resultado"] == "LLEGO") / exitos) if exitos > 0 else 0.0

    duracion = time.time() - t0
    print()
    print("=== RESUMEN ===")
    print("Corridas:     " + str(n))
    print("Exitos:       " + str(exitos) + " (" + str(round(100.0 * exitos / n, 1)) + "%)")
    print("Timeouts:     " + str(timeouts))
    print("Fracasos:     " + str(fracasos))
    print("Dist prom exito: " + str(round(dist_prom, 1)) + "m")
    print("Duracion real: " + str(round(duracion, 1)) + "s")
    print()
    if exitos / n >= 0.70:
        print("VEREDICTO: PASS (>=70% llegada)")
    else:
        print("VEREDICTO: FAIL (<70% llegada)")
    return resultados


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    correr_batch(args.n, seed=args.seed, timeout_s=args.timeout)
