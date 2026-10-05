#!/usr/bin/env python3
"""
context_sampler.py - Genera el banco COMMON-CONTEXT-001 (memo 62).

Cada contexto es (estado, historial) causalmente compatible.
Generados por mezcla de politicas (oraculo, Qwen, perturbado).
Estratificados por distancia, error angular, viento, fase.

Uso:
    python3 context_sampler.py --n 50 --politica oraculo
    python3 context_sampler.py --n 200 --politica mixta
"""

import argparse
import json
import math
import random
from datetime import datetime
from pathlib import Path

from simulador_polaris import Barco
from recetas_navegacion import corregir_rumbo, ir_a_punto, frenar
from oraculo import Oracle


MAX_PASOS = 20
TOL_LLEGADA_M = 15.0
K_HISTORIAL = 5


def distancia_a(b, mx, mz):
    return math.sqrt((b.pos_x - mx)**2 + (b.pos_z - mz)**2)


def ejecutar_receta(b, meta_x, meta_z, receta):
    if receta == "corregir_rumbo":
        dx = meta_x - b.pos_x
        dz = meta_z - b.pos_z
        rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
        corregir_rumbo(b, objetivo_deg=rumbo, timeout_s=60.0)
    elif receta == "ir_a_punto":
        ir_a_punto(b, meta_x, meta_z, tol_dist=TOL_LLEGADA_M, timeout_s=90.0)
    elif receta == "frenar":
        frenar(b, timeout_s=30.0)


def generar_mision(rng):
    dist = rng.uniform(80.0, 220.0)
    ang = rng.uniform(0.0, 360.0)
    mx = round(dist * math.sin(math.radians(ang)), 1)
    mz = round(-dist * math.cos(math.radians(ang)), 1)
    return (mx, mz)


def correr_trayectoria_oraculo(rng, viento_max=0.0):
    """Corre una mision con el oraculo puro. Devuelve lista de snapshots (estado + historial + decision)."""
    orac = Oracle()
    b = Barco()
    b.pos_x, b.pos_z = 0.0, 0.0
    b.yaw = 0.0
    if viento_max > 0.0:
        b.viento_intensidad_kn = rng.uniform(0.0, viento_max)
        b.viento_direccion_deg = rng.uniform(0.0, 360.0)
    mx, mz = generar_mision(rng)
    historial = []
    snapshots = []
    t_inicio = b.t
    pasos = 0

    while b.t - t_inicio < 300.0 and pasos < MAX_PASOS:
        dist = distancia_a(b, mx, mz)
        if dist < TOL_LLEGADA_M:
            break
        # Oráculo decide
        receta = orac.elegir(b, mx, mz)
        # Guardar snapshot antes de ejecutar (estado + historial + decisión)
        snapshots.append({
            "state": {
                "pos_x": round(b.pos_x, 3),
                "pos_z": round(b.pos_z, 3),
                "hdg": round(b.heading_deg(), 2),
                "sog": round(b.sog_kn(), 2),
                "meta_x": mx,
                "meta_z": mz,
                "dist_meta": round(dist, 2),
                "viento_kn": round(b.viento_intensidad_kn, 1),
                "viento_dir": round(b.viento_direccion_deg, 1),
            },
            "history": list(historial[-K_HISTORIAL:]),
            "decision": receta,
            "fuente": "oraculo",
        })
        # Registrar decisión en historial
        historial.append({
            "paso": pasos + 1,
            "pos_x": round(b.pos_x, 2),
            "pos_z": round(b.pos_z, 2),
            "hdg": round(b.heading_deg(), 1),
            "sog": round(b.sog_kn(), 2),
            "decision": receta,
        })
        ejecutar_receta(b, mx, mz, receta)
        pasos += 1

    return snapshots


def correr_trayectoria_qwen(rng, viento_max=0.0, usar_memoria=False, conn=None):
    """Corre una mision con Qwen (sin o con memoria). Devuelve snapshots (estado + historial + decision)."""
    from timonel_python import AgenteTimonel

    mx, mz = generar_mision(rng)
    agente = AgenteTimonel(
        meta_x=mx, meta_z=mz,
        timeout_s=300.0,
        usar_llm=True,
        conn=conn if usar_memoria else None,
        max_pasos=MAX_PASOS,
    )
    if viento_max > 0.0:
        agente.barco.viento_intensidad_kn = rng.uniform(0.0, viento_max)
        agente.barco.viento_direccion_deg = rng.uniform(0.0, 360.0)

    # Correr el agente
    corrida = agente.correr(verbose=False)

    # Convertir los pasos del agente en snapshots con historial
    snapshots = []
    historial = []
    for i, paso in enumerate(corrida.pasos):
        snapshots.append({
            "state": {
                "pos_x": paso.get("pos_x", 0.0),
                "pos_z": paso.get("pos_z", 0.0),
                "hdg": paso.get("hdg", 0.0),
                "sog": paso.get("sog", 0.0),
                "meta_x": mx,
                "meta_z": mz,
                "dist_meta": paso.get("dist_meta", 0.0),
                "viento_kn": round(agente.barco.viento_intensidad_kn, 1),
                "viento_dir": round(agente.barco.viento_direccion_deg, 1),
            },
            "history": list(historial[-K_HISTORIAL:]),
            "decision": paso.get("decision", "?"),
            "fuente": "qwen_con_memoria" if usar_memoria else "qwen_sin_memoria",
        })
        historial.append({
            "paso": i + 1,
            "pos_x": paso.get("pos_x", 0.0),
            "pos_z": paso.get("pos_z", 0.0),
            "hdg": paso.get("hdg", 0.0),
            "sog": paso.get("sog", 0.0),
            "decision": paso.get("decision", "?"),
        })

    return snapshots


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--viento-max", type=float, default=0.0)
    parser.add_argument("--politica", choices=["oraculo", "qwen_sin_memoria", "qwen_con_memoria", "mixta"],
                        default="oraculo")
    parser.add_argument("--output", type=str, default=None,
                        help="Si se especifica, guarda los snapshots en ese archivo JSON")
    args = parser.parse_args()

    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    conn = None
    if args.politica == "qwen_con_memoria":
        from memoria import conectar
        conn = conectar()

    todos = []
    for i in range(args.n):
        if args.politica == "mixta":
            # Mezcla: 20% oraculo, 80% qwen sin memoria
            # NO se incluye qwen_con_memoria para evitar leakage (memo 62 seccion 5)
            r = rng.random()
            if r < 0.20:
                snaps = correr_trayectoria_oraculo(rng, viento_max=args.viento_max)
                pol_usada = "oraculo"
            else:
                snaps = correr_trayectoria_qwen(rng, viento_max=args.viento_max, usar_memoria=False)
                pol_usada = "qwen_sin_memoria"
        elif args.politica == "oraculo":
            snaps = correr_trayectoria_oraculo(rng, viento_max=args.viento_max)
            pol_usada = "oraculo"
        elif args.politica == "qwen_sin_memoria":
            snaps = correr_trayectoria_qwen(rng, viento_max=args.viento_max, usar_memoria=False)
            pol_usada = "qwen_sin_memoria"
        elif args.politica == "qwen_con_memoria":
            snaps = correr_trayectoria_qwen(rng, viento_max=args.viento_max, usar_memoria=True, conn=conn)
            pol_usada = "qwen_con_memoria"
        todos.extend(snaps)
        print("mision " + str(i + 1) + ": " + str(len(snaps)) + " snapshots (politica=" + pol_usada + ")")

    print()
    print("Total de snapshots: " + str(len(todos)))
    print("Politica: " + args.politica)
    if todos:
        n_con_historial = sum(1 for s in todos if len(s["history"]) > 0)
        print("Snapshots con historial no vacio: " + str(n_con_historial) + "/" + str(len(todos)))
        print()
        print("Ejemplo de snapshot con historial:")
        for s in todos:
            if len(s["history"]) > 0:
                print(json.dumps(s, indent=2))
                break

    if args.output:
        out_path = Path(args.output)
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(todos, fh, indent=2, ensure_ascii=False)
        print()
        print("[sampler] Guardado en: " + str(out_path))
        print("[sampler] Total: " + str(len(todos)) + " snapshots")

    if conn is not None:
        conn.close()
