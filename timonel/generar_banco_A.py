#!/usr/bin/env python3
"""generar_banco_A.py - Banco A: generalizacion del umbral T.

Diseno cerrado por Luna (2026-10-12):
- Train: T en {10, 15, 20, 25}, 5 bandas, 30 por estrato = 600.
- Validacion: 10 por estrato = 200.
- Confirmatorio: T en {12.5, 17.5, 22.5} (NO vistos), 5 bandas, 50 por estrato = 750.
- Etiqueta: d < T -> terminar; d >= T -> ir_a.
- Distancia calculada SIN redondeo previo.
"""
import argparse
import json
import math
import random
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, ".")

T_TRAIN = [10.0, 15.0, 20.0, 25.0]
T_CONF = [12.5, 17.5, 22.5]

N_PILOTO = 10
N_TRAIN = 30
N_VAL = 10
N_CONF = 50

# Bandas: (nombre, offset_min_desde_T, offset_max_desde_T, incluye_igual_T)
BANDAS = [
    ("muy_cerca", -10.0, -5.0),
    ("cerca",     -5.0,  -2.0),
    ("critica",   -2.0,   2.0),
    ("lejos",      2.0,   5.0),
    ("muy_lejos",  5.0,  10.0),
]


def sample_in_band(rng, T, banda):
    nombre, lo, hi = banda
    if nombre == "critica":
        # Simetrico a ambos lados de T, con casos exactamente en T
        lado = rng.choice(["abajo", "arriba", "exacto"])
        if lado == "abajo":
            d = rng.uniform(T - 2.0, T - 0.001)
        elif lado == "arriba":
            d = rng.uniform(T + 0.001, T + 2.0)
        else:
            d = T
    else:
        d = rng.uniform(T + lo, T + hi)
    # Distancia minima absoluta: no permitir negativos
    return max(0.1, d)


def make_estado(rng, T, banda):
    """Genera un estado con distancia d en la banda dada."""
    d = sample_in_band(rng, T, banda)
    # Rumbo hacia meta (relativo) y heading: se usan solo en banco completo
    ang_meta = rng.uniform(0.0, 360.0)
    meta_x = round(d * math.sin(math.radians(ang_meta)), 4)
    meta_z = round(-d * math.cos(math.radians(ang_meta)), 4)
    return {
        "pos_x": 0.0, "pos_z": 0.0,
        "hdg": 0.0, "sog": 0.0,
        "meta_x": meta_x, "meta_z": meta_z,
        "viento_kn": 0.0, "viento_dir": 0.0,
        "T": T,
        "banda": banda[0],
        "d": d,
    }


def etiqueta(d, T):
    return "terminar" if d < T else "ir_a"


def generar_bloque(rng, T_values, n_por_estrato):
    """Genera n por cada (T, banda)."""
    out = []
    for T in T_values:
        for banda in BANDAS:
            for _ in range(n_por_estrato):
                e = make_estado(rng, T, banda)
                e["accion_optima"] = etiqueta(e["d"], T)
                out.append(e)
    rng.shuffle(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261012)
    ap.add_argument("--out-dir", default="banco_A")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    out = Path(args.out_dir)
    out.mkdir(exist_ok=True)

    # Piloto: 10 por estrato, T de train
    piloto = generar_bloque(rng, T_TRAIN, N_PILOTO)

    # Train: 30 por estrato, T de train
    train = generar_bloque(rng, T_TRAIN, N_TRAIN)

    # Validacion: 10 por estrato, T de train, semilla distinta
    rng2 = random.Random(args.seed + 1)
    val = generar_bloque(rng2, T_TRAIN, N_VAL)

    # Confirmatorio: 50 por estrato, T NO vistos
    rng3 = random.Random(args.seed + 2)
    conf = generar_bloque(rng3, T_CONF, N_CONF)

    with open(out / "piloto.jsonl", "w") as f:
        for e in piloto:
            f.write(json.dumps(e) + "\n")
    with open(out / "train.jsonl", "w") as f:
        for e in train:
            f.write(json.dumps(e) + "\n")
    with open(out / "val.jsonl", "w") as f:
        for e in val:
            f.write(json.dumps(e) + "\n")
    with open(out / "confirmatorio.jsonl", "w") as f:
        for e in conf:
            f.write(json.dumps(e) + "\n")

    print(f"[A] piloto:        {len(piloto)}")
    print(f"[A] train:         {len(train)}")
    print(f"[A] val:           {len(val)}")
    print(f"[A] confirmatorio: {len(conf)}")
    print()
    print("=== Distribucion de etiquetas ===")
    for nombre, bloque in [("train", train), ("conf", conf)]:
        c = Counter(e["accion_optima"] for e in bloque)
        print(f"  {nombre}: {dict(c)}")
    print()
    print("=== Distribucion por banda (train) ===")
    c = Counter(e["banda"] for e in train)
    print(f"  {dict(c)}")
    print()
    print("=== Distribucion por T (conf) ===")
    c = Counter(e["T"] for e in conf)
    print(f"  {dict(c)}")

    manifiesto = {
        "fecha": datetime.now().isoformat(),
        "seed": args.seed,
        "T_train": T_TRAIN,
        "T_conf": T_CONF,
        "n_por_estrato": {"train": N_TRAIN, "val": N_VAL, "conf": N_CONF, "piloto": N_PILOTO},
        "totales": {"train": len(train), "val": len(val), "conf": len(conf), "piloto": len(piloto)},
    }
    with open(out / "manifiesto.json", "w") as f:
        json.dump(manifiesto, f, indent=2)
    print()
    print(f"[A] archivos en {out}/")


if __name__ == "__main__":
    main()
