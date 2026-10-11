#!/usr/bin/env python3
"""test_convergencia.py - Busca el horizonte donde el oraculo se estabiliza.

Corre el oraculo sobre los 75 casos corregir_rumbo con horizontes crecientes:
45, 60, 90, 120, 180, 240, 360.
"""
import json
import math
import sys
from collections import Counter
from datetime import datetime
sys.path.insert(0, ".")

from simulador_polaris import Barco
from entrenador import Entrenador


CONFIGS = {
    "45s":  [5.0, 15.0, 30.0, 45.0],
    "60s":  [5.0, 15.0, 30.0, 45.0, 60.0],
    "90s":  [5.0, 15.0, 30.0, 45.0, 60.0, 90.0],
    "120s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0],
    "180s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0],
    "240s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 240.0],
    "360s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 240.0, 360.0],
}


def cargar_desarrollo():
    ctxs = [json.loads(l) for l in open("banco_cc002/banco_contextos.jsonl")]
    lbls = [json.loads(l) for l in open("banco_cc002/banco_etiquetas.jsonl")]
    by_id = {l["context_id"]: l for l in lbls}
    return [(c, by_id[c["context_id"]]) for c in ctxs
            if by_id.get(c["context_id"], {}).get("split") == "desarrollo"]


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
    items = cargar_desarrollo()
    casos_cr = [(c, l) for c, l in items if l["accion_optima"] == "corregir_rumbo"]
    print(f"[test] contextos corregir_rumbo: {len(casos_cr)}")
    print()

    resultados = {}
    for nombre, horiz in CONFIGS.items():
        print(f"[test] corriendo {nombre}...")
        orac = Entrenador(horizontes=horiz)
        res = []
        for ctx, lbl in casos_cr:
            state = ctx["state"]
            b = barco_desde_state(state)
            mx, mz = state["meta_x"], state["meta_z"]
            try:
                eval_todas = orac.evaluar_todas(b, mx, mz)
                res.append(eval_todas[0].receta)
            except Exception:
                res.append("_error_")
        resultados[nombre] = res

    print()
    print("=== DISTRIBUCION DE GANADORAS ===")
    for nombre, res in resultados.items():
        c = Counter(res)
        iap = c.get("ir_a_punto", 0)
        cr = c.get("corregir_rumbo", 0)
        print(f"  {nombre:6s}: ir_a_punto={iap:3d} | corregir_rumbo={cr:3d}")

    print()
    print("=== CAMBIOS ENTRE CONFIGS CONSECUTIVAS ===")
    nombres = list(CONFIGS.keys())
    for i in range(1, len(nombres)):
        prev = resultados[nombres[i-1]]
        curr = resultados[nombres[i]]
        cambios = sum(1 for a, b in zip(prev, curr) if a != b)
        print(f"  {nombres[i-1]:6s} -> {nombres[i]:6s}: {cambios:3d} cambios")

    print()
    print("=== COMPARACION CON LA CONFIG ORIGINAL (45s) ===")
    orig = resultados["45s"]
    for nombre in nombres[1:]:
        curr = resultados[nombre]
        cambios = sum(1 for a, b in zip(orig, curr) if a != b)
        print(f"  45s -> {nombre:6s}: {cambios:3d} cambios")

    # Guardar
    with open("test_convergencia.json", "w") as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "configs": {k: v for k, v in CONFIGS.items()},
            "distribucion": {k: dict(Counter(v)) for k, v in resultados.items()},
            "resultados": resultados,
        }, f, indent=2)
    print()
    print("[OK] test_convergencia.json guardado")


if __name__ == "__main__":
    main()
