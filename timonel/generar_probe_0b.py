#!/usr/bin/env python3
"""generar_probe_0b.py - Etapa 0b del protocolo A3.

Cuatro bloques, solo puntuar (sin entrenar), adaptador A2 congelado.

- B1 placebo: v visible, contrato SIN clausula de velocidad.
- B2 v_max variable: contrato CON clausula, v_max en 5 valores,
  incluye casos contra-prior.
- B3 contrafactual: mismo (d,T,v), cambia solo v_max.
- B4 vecindad: vecindad del fallo unico del probe F2.
"""
import json
from pathlib import Path

import numpy as np

SEED = 20261014
rng = np.random.default_rng(SEED)
OUT = "bancoA2_0b"
T_FIJO = 15.0

# Plantilla SIN clausula de velocidad (B1 placebo).
PROMPT_SIN_VEL = """=== PROPOSITO ===
Llevar el barco hasta la meta.
La mision se considera completa cuando la distancia a la meta es menor que {T} metros.

=== ESTADO ACTUAL ===
- Distancia a la meta: {d} metros
- Velocidad: {v} nudos

=== ACCIONES DISPONIBLES ===
- ir_a: seguir navegando hacia la meta.
- terminar: declarar la mision como cumplida.

=== TAREA ===
Elegi la accion que mejor contribuya al proposito.
Responde UNICAMENTE con JSON: {{"accion": "<nombre>"}}"""

# Plantilla CON clausula de velocidad (B2, B3, B4).
PROMPT_CON_VEL = """=== PROPOSITO ===
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

def fmt1(x):
    return f"{x:.1f}"


def _ctx_b1(d, v, label, sub):
    return {
        "bloque": "B1_placebo", "sub": sub,
        "T": T_FIJO, "d": d, "v": v, "v_max": None,
        "label": label,
        "prompt": PROMPT_SIN_VEL.format(T=f"{T_FIJO:g}",
                                        d=f"{d:.1f}", v=f"{v:.2f}"),
    }


def make_B1_placebo():
    ctxs = []
    for _ in range(25):
        d = round(float(rng.uniform(2.0, T_FIJO - 1.0)), 1)
        v = round(float(rng.uniform(0.0, 0.3)), 2)
        ctxs.append(_ctx_b1(d, v, "terminar", "d_menor_v_baja"))
    for _ in range(25):
        d = round(float(rng.uniform(2.0, T_FIJO - 1.0)), 1)
        v = round(float(rng.uniform(2.0, 5.0)), 2)
        ctxs.append(_ctx_b1(d, v, "terminar", "d_menor_v_alta"))
    for _ in range(25):
        d = round(float(rng.uniform(T_FIJO + 1.0, 40.0)), 1)
        v = round(float(rng.uniform(0.0, 0.3)), 2)
        ctxs.append(_ctx_b1(d, v, "ir_a", "d_mayor_v_baja"))
    for _ in range(25):
        d = round(float(rng.uniform(T_FIJO + 1.0, 40.0)), 1)
        v = round(float(rng.uniform(2.0, 5.0)), 2)
        ctxs.append(_ctx_b1(d, v, "ir_a", "d_mayor_v_alta"))
    return ctxs

def _ctx_b2(d, v, v_max, label, sub, bloque="B2_vmax_var"):
    return {
        "bloque": bloque, "sub": sub,
        "T": T_FIJO, "d": d, "v": v, "v_max": v_max,
        "label": label,
        "prompt": PROMPT_CON_VEL.format(T=f"{T_FIJO:g}", vmax=f"{v_max:g}",
                                        d=f"{d:.1f}", v=f"{v:.2f}"),
    }


def make_B2_vmax_var():
    """Casos contra-prior: v moderada con v_max alto -> terminar.
    Casos pro-prior: v alta con v_max bajo -> ir_a.
    """
    ctxs = []
    v_maxs = [0.3, 0.6, 1.0, 2.0, 4.0]
    # Contra-prior: d<T, v dentro de v_max, pero v > 0.5 (barco moviendose).
    for vm in v_maxs:
        if vm < 0.5:
            continue  # v_max muy bajo: v no puede quedar adentro y ser "moderada"
        for _ in range(6):
            d = round(float(rng.uniform(2.0, T_FIJO - 1.0)), 1)
            v = round(float(rng.uniform(0.5, min(vm, 2.0))), 2)
            label = "terminar"
            ctxs.append(_ctx_b2(d, v, vm, label, "contra_prior"))
    # Pro-prior: d<T, v > v_max -> ir_a.
    for vm in v_maxs:
        for _ in range(6):
            d = round(float(rng.uniform(2.0, T_FIJO - 1.0)), 1)
            v = round(float(rng.uniform(vm + 0.1, vm + 1.0)), 2)
            label = "ir_a"
            ctxs.append(_ctx_b2(d, v, vm, label, "pro_prior"))
    # Fuera de rango: d>=T, v<=v_max -> ir_a.
    for vm in v_maxs:
        for _ in range(4):
            d = round(float(rng.uniform(T_FIJO + 1.0, 40.0)), 1)
            v = round(float(rng.uniform(0.0, vm)), 2)
            label = "ir_a"
            ctxs.append(_ctx_b2(d, v, vm, label, "d_mayor"))
    # Fuera de rango: d>=T, v>v_max -> ir_a.
    for vm in v_maxs:
        for _ in range(4):
            d = round(float(rng.uniform(T_FIJO + 1.0, 40.0)), 1)
            v = round(float(rng.uniform(vm + 0.1, vm + 1.0)), 2)
            label = "ir_a"
            ctxs.append(_ctx_b2(d, v, vm, label, "d_mayor_v_alta"))
    return ctxs

def make_B3_contrafactual():
    """Pares: mismo d, T, v. Cambia solo v_max. La etiqueta puede
    cambiar segun v_max, lo que prueba lectura del contrato.
    """
    ctxs = []
    pares = 50
    for i in range(pares):
        d = round(float(rng.uniform(2.0, T_FIJO - 1.0)), 1)
        # v moderada, elegida para que quede entre dos v_max distintos
        v = round(float(rng.uniform(0.5, 1.5)), 2)
        # Dos umbrales: uno por debajo de v (ir_a) y uno por encima (terminar)
        vm_bajo = round(max(0.3, v - 0.5), 1)
        vm_alto = round(v + 0.5, 1)
        ctxs.append(_ctx_b2(d, v, vm_bajo, "ir_a", f"par{i}_bajo", "B3_contrafactual"))
        ctxs.append(_ctx_b2(d, v, vm_alto, "terminar", f"par{i}_alto", "B3_contrafactual"))
    return ctxs

def make_B4_vecindad():
    """Vecindad del fallo de Q2: d cerca de T, v cerca de v_max.
    Zona de frontera, descriptivo.
    """
    ctxs = []
    v_max = 0.3
    for _ in range(15):
        d = round(float(rng.uniform(T_FIJO - 1.0, T_FIJO + 1.0)), 1)
        v = round(float(rng.uniform(v_max - 0.1, v_max + 0.1)), 2)
        v = max(0.0, v)
        label = "terminar" if (d < T_FIJO and v <= v_max) else "ir_a"
        ctxs.append(_ctx_b2(d, v, v_max, label, "vecindad_q2", "B4_vecindad"))
    for _ in range(15):
        d = round(float(rng.uniform(T_FIJO - 0.5, T_FIJO + 0.5)), 1)
        v = round(float(rng.uniform(v_max + 0.01, v_max + 0.3)), 2)
        label = "ir_a"
        ctxs.append(_ctx_b2(d, v, v_max, label, "vecindad_q2_alta", "B4_vecindad"))
    return ctxs

def main():
    Path(OUT).mkdir(exist_ok=True)
    ctxs = []
    ctxs += make_B1_placebo()
    ctxs += make_B2_vmax_var()
    ctxs += make_B3_contrafactual()
    ctxs += make_B4_vecindad()
    rng.shuffle(ctxs)

    path = f"{OUT}/probe_0b.jsonl"
    with open(path, "w") as f:
        for c in ctxs:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    from collections import Counter
    print(f"[OK] {len(ctxs)} contextos -> {path}")
    print()
    print("=== Distribucion por bloque ===")
    cb = Counter(c["bloque"] for c in ctxs)
    for k in sorted(cb):
        print(f"  {k}: {cb[k]}")
    print()
    print("=== Distribucion por etiqueta ===")
    cl = Counter(c["label"] for c in ctxs)
    print(f"  {dict(cl)}")
    print()
    print("=== B3 contrafactuales: verificacion de pares ===")
    b3 = [c for c in ctxs if c["bloque"] == "B3_contrafactual"]
    for par in ["par0", "par1"]:
        sub = sorted([c for c in b3 if c["sub"].startswith(par)],
                     key=lambda x: x["v_max"])
        if len(sub) == 2:
            a, b = sub
            print(f"  {par}: v={a['v']} v_max={a['v_max']}->{a['label']} | "
                  f"v_max={b['v_max']}->{b['label']}")


if __name__ == "__main__":
    main()