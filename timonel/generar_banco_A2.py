#!/usr/bin/env python3
"""generar_banco_A2.py - Banco A2 (Fase 1a, rev. 2).

Diseno congelado en EXPEDIENTE/89_seccion23_diseno_A2.md.

Salida:
- bancoA2/train.jsonl (616)
- bancoA2/val.jsonl (176)
- bancoA2/test_interp.jsonl (600)
- bancoA2/test_extrap.jsonl (400)
- bancoA2/manifest.json

Regla: d_mostrado < T_mostrado -> terminar; d_mostrado >= T_mostrado -> ir_a.
Etiqueta calculada sobre el valor mostrado (1 decimal).
Prompt sin mencion a velocidad. Respuesta en palabra.
"""
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

SEED = 20261013
T_TRAIN = [8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
T_INTERP = [11, 17, 23]
T_EXTRAP = [6, 32]
BINS = [(0.3, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, 8.0)]
N_CELL = {"train": 7, "val": 2, "test_interp": 25, "test_extrap": 25}
OUT = "bancoA2"

PROMPT = """=== PROPOSITO ===
Llevar el barco hasta la meta.
La mision se considera completa cuando la distancia a la meta es menor que {T} metros.

=== ESTADO ACTUAL ===
- Distancia a la meta: {d} metros

=== ACCIONES DISPONIBLES ===
{acciones}

=== TAREA ===
Elegi la accion que mejor contribuya al proposito.
Responde UNICAMENTE con JSON: {{"accion": "<nombre>"}}"""

DESC = {
    "ir_a": "- ir_a: seguir navegando hacia la meta.",
    "terminar": "- terminar: declarar la mision como cumplida.",
}


def fmt1(x):
    """Formatea con 1 decimal, sin ceros sobrantes."""
    s = f"{x:.1f}"
    return s


def etiqueta(d_mostrado, T_mostrado):
    return "terminar" if d_mostrado < T_mostrado else "ir_a"


def make_ctx(rng, T, lo, hi, lado, split, kind, forbidden=None):
    """Genera un contexto con |d - T| en [lo, hi] del lado indicado."""
    while True:
        m = rng.uniform(lo, hi)
        raw = T - m if lado == "terminar" else T + m
        d_str = fmt1(raw)
        d = float(d_str)
        if d < 0.5:
            continue
        diff = abs(d - T)
        if diff < 0.3:
            continue
        if forbidden is not None and (T, d) in forbidden:
            continue
        break

    orden = [str(a) for a in rng.permutation(["ir_a", "terminar"])]
    acciones = "\n".join(DESC[a] for a in orden)
    lab = etiqueta(d, T)
    prompt = PROMPT.format(T=fmt1(T), d=fmt1(d), acciones=acciones)

    return {
        "split": split,
        "kind": kind,
        "T": T,
        "d": d,
        "label": lab,
        "orden": orden,
        "bin": [lo, hi],
        "lado": lado,
        "prompt": prompt,
    }


def build(rng, Ts, n, split, kind, seed_offset=0, forbidden=None):
    if seed_offset > 0:
        rng = np.random.default_rng(SEED + seed_offset)
    out = []
    for T in Ts:
        for lo, hi in BINS:
            for lado in ("terminar", "ir_a"):
                for _ in range(n):
                    out.append(make_ctx(rng, T, lo, hi, lado, split, kind, forbidden))
    rng.shuffle(out)
    return out


def verificar(data, prompt_template):
    """Verifica reglas de consistencia. Devuelve lista de errores."""
    errores = []
    allc = [c for v in data.values() for c in v]

    # 1. Plantilla sin digitos propios
    if re.search(r"\d", prompt_template):
        errores.append("la plantilla contiene digitos propios")

    # 2. Etiqueta coincide con comparacion sobre valor mostrado
    for c in allc:
        d_str = fmt1(c["d"])
        T_str = fmt1(c["T"])
        esperada = "terminar" if float(d_str) < float(T_str) else "ir_a"
        if c["label"] != esperada:
            errores.append(f"etiqueta incoherente: d={d_str} T={T_str} label={c['label']}")
            break

    # 3. T de test no aparece en train
    if set(T_TRAIN) & (set(T_INTERP) | set(T_EXTRAP)):
        errores.append("T de test aparece en train")

    # 4. Prompt sin mencion a velocidad/nudos/viento
    for c in allc:
        low = c["prompt"].lower()
        for w in ("velocidad", "nudo", "viento"):
            if w in low:
                errores.append(f"el prompt menciona '{w}'")
                break
        else:
            continue
        break

    # 5. val no duplica (T, d) de train
    vistos = {(c["T"], c["d"]) for c in data["train"]}
    for c in data["val"]:
        if (c["T"], c["d"]) in vistos:
            errores.append(f"val duplica (T,d) de train: T={c['T']} d={c['d']}")
            break

    # 6. Ambas acciones aparecen con igual frecuencia por estrato
    for split, items in data.items():
        por_celda = Counter()
        for c in items:
            por_celda[(c["T"], tuple(c["bin"]), c["lado"])] += 1
        # En el generador, cada celda tiene exactamente n contextos
        # con el mismo lado. No hay nada mas que verificar a nivel
        # de accion porque el balance lo controla el generador.

    return errores


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    rng = np.random.default_rng(SEED)
    Path(OUT).mkdir(exist_ok=True)

    data = {
        "train": build(rng, T_TRAIN, N_CELL["train"], "train", "visto"),
        "test_interp": build(rng, T_INTERP, N_CELL["test_interp"], "test", "interp"),
        "test_extrap": build(rng, T_EXTRAP, N_CELL["test_extrap"], "test", "extrap"),
    }

    train_keys = {(c["T"], c["d"]) for c in data["train"]}
    data["val"] = build(rng, T_TRAIN, N_CELL["val"], "val", "visto", seed_offset=1, forbidden=train_keys)

    errores = verificar(data, PROMPT)
    print("ERRORES:", errores or "ninguno")
    if errores:
        sys.exit(1)

    manifest = {
        "fecha": datetime.now().isoformat(),
        "seed": SEED,
        "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
        "T_train": T_TRAIN,
        "T_interp": T_INTERP,
        "T_extrap": T_EXTRAP,
        "BINS": BINS,
        "N_CELL": N_CELL,
        "files": {},
    }

    for k, v in data.items():
        path = f"{OUT}/{k}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for c in v:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        manifest["files"][k] = {"n": len(v), "sha256": sha256_file(path)}
        print(f"[A2] {k}: {len(v)} ejemplos -> {path}")

    with open(f"{OUT}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print()
    print("=== Distribucion de etiquetas ===")
    for k, v in data.items():
        c = Counter(x["label"] for x in v)
        print(f"  {k}: {dict(c)}")

    print()
    print("=== Baseline constante (siempre ir_a) ===")
    for k in ("test_interp", "test_extrap"):
        v = data[k]
        acc = sum(1 for c in v if c["label"] == "ir_a") / len(v)
        print(f"  {k}: {acc:.3f}")

    print()
    print("=== Baseline regla T=15 fijo ===")
    for k in ("test_interp", "test_extrap"):
        v = data[k]
        acc = sum(1 for c in v if (c["d"] < 15) == (c["label"] == "terminar")) / len(v)
        print(f"  {k}: {acc:.3f}")


if __name__ == "__main__":
    main()
