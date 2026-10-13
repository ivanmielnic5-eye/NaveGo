#!/usr/bin/env python3
"""generar_probe_A2.py - Banco probe F2 para etapa 0 de A3.

200 contextos, 50 por cuadrante. Q2 (d<T, v>v_max) es el probe clave.
"""
import json
from pathlib import Path
from collections import Counter

import numpy as np

SEED = 20261014
rng = np.random.default_rng(SEED)
OUT = "bancoA2_probe"
T_FIJO = 15.0
V_MAX = 0.3

PROMPT = """=== PROPOSITO ===
Llevar el barco hasta la meta.
La mision se considera completa cuando la distancia a la meta es menor que {T} metros Y la velocidad es menor o igual a {vmax} nudos.

=== ESTADO ACTUAL ===
- Distancia a la meta: {d} metros
- Velocidad: {v} nudos

=== ACCIONES DISPONIBLES ===
- ir_a: seguir navegando hacia la meta.
- terminar: declarar la mision como cumplida.

=== TAREA ===
Elegi la accion que mejor contribuya al proposito.
Responde UNICAMENTE con JSON: {{"accion": "<nombre>"}}"""


def make_ctx(cuadrante):
    if cuadrante == "Q1":
        d = round(float(rng.uniform(2.0, T_FIJO - 1.0)), 1)
        v = round(float(rng.uniform(0.0, V_MAX)), 2)
    elif cuadrante == "Q2":
        d = round(float(rng.uniform(2.0, T_FIJO - 1.0)), 1)
        v = round(float(rng.uniform(V_MAX + 0.5, 5.0)), 2)
    elif cuadrante == "Q3":
        d = round(float(rng.uniform(T_FIJO + 1.0, 40.0)), 1)
        v = round(float(rng.uniform(0.0, V_MAX)), 2)
    else:
        d = round(float(rng.uniform(T_FIJO + 1.0, 40.0)), 1)
        v = round(float(rng.uniform(V_MAX + 0.5, 5.0)), 2)
    label = "terminar" if (d < T_FIJO and v <= V_MAX) else "ir_a"
    prompt = PROMPT.format(T=f"{T_FIJO:g}", vmax=f"{V_MAX:g}",
                           d=f"{d:.1f}", v=f"{v:.2f}")
    return {"cuadrante": cuadrante, "T": T_FIJO, "d": d, "v": v,
            "v_max": V_MAX, "label": label, "prompt": prompt}


def main():
    Path(OUT).mkdir(exist_ok=True)
    ctxs = []
    for q in ("Q1", "Q2", "Q3", "Q4"):
        for _ in range(50):
            ctxs.append(make_ctx(q))
    rng.shuffle(ctxs)

    path = f"{OUT}/probe.jsonl"
    with open(path, "w") as f:
        for c in ctxs:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"[OK] {len(ctxs)} contextos -> {path}")
    print()
    print("=== Distribucion de etiquetas por cuadrante ===")
    for q in ("Q1", "Q2", "Q3", "Q4"):
        sub = [c for c in ctxs if c["cuadrante"] == q]
        cc = Counter(c["label"] for c in sub)
        print(f"  {q}: n={len(sub)} labels={dict(cc)}")
    print()
    print("=== Ejemplo Q2 (probe clave) ===")
    e = next(c for c in ctxs if c["cuadrante"] == "Q2")
    print(e["prompt"])
    print(f"\nlabel correcta: {e['label']}  (d={e['d']}, v={e['v']})")


if __name__ == "__main__":
    main()
