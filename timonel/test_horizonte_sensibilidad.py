#!/usr/bin/env python3
"""test_horizonte_sensibilidad.py - Analisis de sensibilidad al horizonte.

Corre el oraculo sobre los 75 casos corregir_rumbo con 3 configuraciones:
- Original:  [5, 15, 30, 45]
- Ext A:     [5, 15, 30, 45, 60, 90]
- Ext B:     [5, 15, 30, 45, 60, 90, 120]

Compara: cuantas veces cambia la etiqueta optima entre configs.
"""
import copy
import json
import math
import sys
from collections import Counter
from datetime import datetime
sys.path.insert(0, ".")

from simulador_polaris import Barco
from entrenador import Entrenador


CONFIGS = {
    "orig": [5.0, 15.0, 30.0, 45.0],
    "ext_90": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0],
    "ext_120": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0],
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
    print(f"[test] configuraciones: {list(CONFIGS.keys())}")
    print()

    # Crear los 3 oraculos
    oraculos = {k: Entrenador(horizontes=h) for k, h in CONFIGS.items()}

    # Correr cada uno sobre los 75 casos
    resultados = {}
    for k, orac in oraculos.items():
        print(f"[test] corriendo {k}...")
        res = []
        for ctx, lbl in casos_cr:
            state = ctx["state"]
            b = barco_desde_state(state)
            mx, mz = state["meta_x"], state["meta_z"]
            try:
                eval_todas = orac.evaluar_todas(b, mx, mz)
                ganadora = eval_todas[0].receta
                res.append({
                    "context_id": ctx["context_id"],
                    "ganadora": ganadora,
                })
            except Exception as e:
                print(f"  ERROR {ctx['context_id']}: {e}")
                res.append({"context_id": ctx["context_id"], "ganadora": "_error_"})
        resultados[k] = res
        print()

    # Comparar
    print("=== COMPARACION ===")
    print(f"{'context_id':18s} | {'orig':16s} | {'ext_90':16s} | {'ext_120':16s}")

    cambios_90 = 0
    cambios_120 = 0
    cambios_90_vs_120 = 0

    for i in range(len(casos_cr)):
        r_orig = resultados["orig"][i]["ganadora"]
        r_90 = resultados["ext_90"][i]["ganadora"]
        r_120 = resultados["ext_120"][i]["ganadora"]
        cid = resultados["orig"][i]["context_id"]

        cambio_90 = "SI" if r_orig != r_90 else "no"
        cambio_120 = "SI" if r_90 != r_120 else "no"

        if r_orig != r_90:
            cambios_90 += 1
        if r_orig != r_120:
            cambios_120 += 1
        if r_90 != r_120:
            cambios_90_vs_120 += 1

        # Solo imprimir si algo cambio
        if r_orig != r_90 or r_90 != r_120:
            print(f"{cid:18s} | {r_orig:16s} | {r_90:16s} | {r_120:16s}")

    print()
    print("=== RESUMEN ===")
    print(f"  Total contextos: {len(casos_cr)}")
    print(f"  Cambian de orig -> ext_90:     {cambios_90}")
    print(f"  Cambian de orig -> ext_120:    {cambios_120}")
    print(f"  Cambian de ext_90 -> ext_120:  {cambios_90_vs_120}")

    print()
    print("=== INTERPRETACION ===")
    if cambios_90_vs_120 == 0:
        print("  Con 90s el oraculo ya se estabiliza. No hace falta ir a 120s.")
    else:
        print(f"  Hay {cambios_90_vs_120} casos que aun cambian entre 90 y 120s.")
        print("  Vale la pena usar 120s en el oraculo corregido.")

    # Distribucion de ganadoras por config
    print()
    for k, res in resultados.items():
        c = Counter(r["ganadora"] for r in res)
        print(f"  {k}: {dict(c)}")

    # Guardar
    with open("test_horizonte_sensibilidad.json", "w") as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "configs": {k: v for k, v in CONFIGS.items()},
            "cambios_90": cambios_90,
            "cambios_120": cambios_120,
            "cambios_90_vs_120": cambios_90_vs_120,
            "resultados": resultados,
        }, f, indent=2)
    print()
    print("[OK] test_horizonte_sensibilidad.json guardado")


if __name__ == "__main__":
    main()
