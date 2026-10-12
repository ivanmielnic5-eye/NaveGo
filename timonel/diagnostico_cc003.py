#!/usr/bin/env python3
"""diagnostico_cc003.py - Diagnostico para el nuevo banco CC003.

Genera 2000 candidatos, los etiqueta con el Entrenador v2 (horizontes largos)
y reporta la distribucion por accion y por familia. NO escribe archivos.
"""
import argparse
import hashlib
import json
import math
import random
import sys
import time
from collections import Counter
from datetime import datetime

sys.path.insert(0, ".")

from simulador_polaris import Barco
from entrenador_v2 import Entrenador


HORIZ_LARGOS = [5.0, 15.0, 30.0, 60.0, 120.0, 240.0]


def clasificar_familia(dist):
    if dist < 15.0:
        return "terminal"
    elif dist < 50.0:
        return "cerca"
    elif dist < 150.0:
        return "medio"
    else:
        return "lejos"


def generar_candidato(rng):
    # Sesgo: 30% a distancias cortas
    if rng.random() < 0.30:
        dist = rng.uniform(5.0, 30.0)
    else:
        dist = rng.uniform(15.0, 400.0)
    ang_meta = rng.uniform(0.0, 360.0)
    meta_x = round(dist * math.sin(math.radians(ang_meta)), 2)
    meta_z = round(-dist * math.cos(math.radians(ang_meta)), 2)
    hdg = round(rng.uniform(0.0, 360.0), 2)
    sog = round(rng.uniform(0.0, 8.0), 2)
    v_kn = rng.choice([0.0, 5.0, 10.0, 15.0])
    v_dir = round(rng.uniform(0.0, 360.0), 1) if v_kn > 0 else 0.0
    return {
        "pos_x": 0.0, "pos_z": 0.0,
        "hdg": hdg, "sog": sog,
        "meta_x": meta_x, "meta_z": meta_z,
        "viento_kn": round(v_kn, 1),
        "viento_dir": v_dir,
    }


def barco_desde_state(state):
    b = Barco()
    b.pos_x = state["pos_x"]
    b.pos_z = state["pos_z"]
    b.yaw = math.radians(state["hdg"])
    sog_ms = state["sog"] / 1.94384449
    b.vel_x = math.sin(b.yaw) * sog_ms
    b.vel_z = -math.cos(b.yaw) * sog_ms
    b.viento_intensidad_kn = state["viento_kn"]
    b.viento_direccion_deg = state["viento_dir"]
    return b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    entrenador = Entrenador(horizontes=HORIZ_LARGOS)

    print(f"[diag] generando {args.n} candidatos (seed={args.seed})")
    print(f"[diag] horizontes: {HORIZ_LARGOS}")
    print()

    t0 = time.time()
    distribucion_accion = Counter()
    distribucion_familia = Counter()
    por_accion_familia = {a: Counter() for a in ["rumbo", "ir_a", "frenar", "terminar"]}

    for i in range(args.n):
        state = generar_candidato(rng)
        b = barco_desde_state(state)
        try:
            mejor = entrenador.elegir(b, state["meta_x"], state["meta_z"])
        except Exception:
            continue
        dx = state["meta_x"] - state["pos_x"]
        dz = state["meta_z"] - state["pos_z"]
        dist = math.sqrt(dx*dx + dz*dz)
        fam = clasificar_familia(dist)

        distribucion_accion[mejor] += 1
        distribucion_familia[fam] += 1
        por_accion_familia[mejor][fam] += 1

        if (i+1) % 200 == 0:
            elapsed = time.time() - t0
            print(f"  [{i+1}/{args.n}] t={elapsed:.1f}s")

    print()
    print(f"[total] t={time.time()-t0:.1f}s")
    print()
    print("=== DISTRIBUCION POR ACCION ===")
    for acc in ["rumbo", "ir_a", "frenar", "terminar"]:
        n = distribucion_accion.get(acc, 0)
        pct = 100*n/args.n
        print(f"  {acc:10s}: {n:5d} ({pct:5.1f}%)")

    print()
    print("=== DISTRIBUCION POR FAMILIA ===")
    for fam in ["terminal", "cerca", "medio", "lejos"]:
        n = distribucion_familia.get(fam, 0)
        pct = 100*n/args.n
        print(f"  {fam:10s}: {n:5d} ({pct:5.1f}%)")

    print()
    print("=== CRUCE ACCION x FAMILIA ===")
    print(f"{'accion':10s} | {'terminal':>10s} | {'cerca':>10s} | {'medio':>10s} | {'lejos':>10s}")
    for acc in ["rumbo", "ir_a", "frenar", "terminar"]:
        fams = por_accion_familia[acc]
        print(f"{acc:10s} | {fams.get('terminal', 0):>10d} | {fams.get('cerca', 0):>10d} | {fams.get('medio', 0):>10d} | {fams.get('lejos', 0):>10d}")

    print()
    print("=== DIAGNOSTICO ===")
    accion_min = min(distribucion_accion.get(a, 0) for a in ["rumbo", "ir_a", "frenar", "terminar"])
    accion_max = max(distribucion_accion.get(a, 0) for a in ["rumbo", "ir_a", "frenar", "terminar"])
    print(f"  Accion menos frecuente: {accion_min}")
    print(f"  Accion mas frecuente:   {accion_max}")
    print(f"  Ratio max/min: {accion_max/max(accion_min,1):.1f}x")

    if accion_min < 75:
        print(f"  > La accion menos frecuente tiene < 75. No alcanza para 75 balanceado.")
        print(f"  > Habria que generar mas candidatos.")
    else:
        print(f"  > Se pueden tomar 75 por accion (o mas).")

    # Guardar
    with open("diagnostico_cc003.json", "w") as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "n_generados": args.n,
            "seed": args.seed,
            "distribucion_accion": dict(distribucion_accion),
            "distribucion_familia": dict(distribucion_familia),
            "por_accion_familia": {a: dict(c) for a, c in por_accion_familia.items()},
        }, f, indent=2)
    print()
    print("[diag] diagnostico_cc003.json guardado")


if __name__ == "__main__":
    main()
