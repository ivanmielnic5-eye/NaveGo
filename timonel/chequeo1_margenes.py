#!/usr/bin/env python3
"""chequeo1_margenes.py - Chequeo 1: los cambios 45s->240s son reales?

Para cada uno de los 50 casos que cambian:
- Corre el oraculo a 240s.
- Extrae el margen entre 1ra (ir_a_punto) y 2da (corregir_rumbo).
- Extrae tambien el progreso de cada una.
- Reporta distribucion de margenes.

Si margen > 5m: cambio real.
Si margen < 1m: empate tecnico.
"""
import json
import math
import statistics
import sys
from collections import Counter
from datetime import datetime
sys.path.insert(0, ".")

from simulador_polaris import Barco
from entrenador import Entrenador


HORIZ_240 = [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 240.0]


def cargar_desarrollo():
    ctxs = [json.loads(l) for l in open("banco_cc002/banco_contextos.jsonl")]
    lbls = [json.loads(l) for l in open("banco_cc002/banco_etiquetas.jsonl")]
    by_id = {l["context_id"]: l for l in lbls}
    return {c["context_id"]: (c, by_id[c["context_id"]]) for c in ctxs
            if by_id.get(c["context_id"], {}).get("split") == "desarrollo"}


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
    auditoria = json.load(open("auditoria_completa_banco.json"))
    ctxs_by_id = cargar_desarrollo()

    # Solo los que cambian
    casos = [r for r in auditoria["resultados"]
             if r["etiqueta_original"] == "corregir_rumbo" and r["cambia"]]
    print(f"[chk1] casos que cambian: {len(casos)}")

    orac = Entrenador(horizontes=HORIZ_240)
    margenes = []
    detalles = []

    for r in casos:
        entry = ctxs_by_id.get(r["context_id"])
        if not entry:
            continue
        ctx, lbl = entry
        state = ctx["state"]
        b = barco_desde_state(state)

        detalle = orac.elegir_con_detalle(b, state["meta_x"], state["meta_z"], near_tie_m=1.0)
        mejor = detalle["mejor"]
        margen = detalle.get("margen_vs_segunda")

        # Extraer progresos de las dos principales
        progresos = {}
        for d in detalle["detalle"]:
            progresos[d["receta"]] = d["progreso_por_horizonte"].get(240.0, 0.0)

        p_mejor = progresos.get("ir_a_punto", 0.0)
        p_segunda = progresos.get("corregir_rumbo", 0.0)

        margenes.append(margen if margen is not None else 0.0)
        detalles.append({
            "context_id": r["context_id"],
            "mejor": mejor,
            "margen": margen,
            "p_ir_a_punto": p_mejor,
            "p_corregir_rumbo": p_segunda,
        })

    # Estadisticas
    print()
    print("=== MARGENES (1ra vs 2da) ===")
    if margenes:
        print(f"  n       : {len(margenes)}")
        print(f"  min     : {round(min(margenes), 2)}m")
        print(f"  max     : {round(max(margenes), 2)}m")
        print(f"  media   : {round(statistics.mean(margenes), 2)}m")
        print(f"  mediana : {round(statistics.median(margenes), 2)}m")

    # Distribucion por rango
    print()
    print("=== DISTRIBUCION DE MARGENES ===")
    bins = [(0, 0.5), (0.5, 1), (1, 5), (5, 20), (20, 100), (100, 1000)]
    contadores = Counter()
    for m in margenes:
        for lo, hi in bins:
            if lo <= m < hi:
                contadores[(lo, hi)] += 1
                break
    for lo, hi in bins:
        c = contadores.get((lo, hi), 0)
        barra = "#" * c
        print(f"  {lo:6.1f}-{hi:<6.1f}m: {c:3d}  {barra}")

    # Diagnostico
    print()
    print("=== DIAGNOSTICO ===")
    empate_tecnico = sum(1 for m in margenes if m < 1.0)
    cambio_debil = sum(1 for m in margenes if 1.0 <= m < 5.0)
    cambio_real = sum(1 for m in margenes if m >= 5.0)
    n = len(margenes) or 1
    print(f"  Empate tecnico (< 1m):   {empate_tecnico:3d} ({100*empate_tecnico/n:.0f}%)")
    print(f"  Cambio debil (1-5m):     {cambio_debil:3d} ({100*cambio_debil/n:.0f}%)")
    print(f"  Cambio real (>= 5m):     {cambio_real:3d} ({100*cambio_real/n:.0f}%)")
    print()
    if cambio_real / n > 0.7:
        print("  >>> Los cambios son REALES. El oraculo cambia de opinion por margen amplio.")
    elif empate_tecnico / n > 0.5:
        print("  >>> Los cambios son EMPATES TECNICOS. Puede no haber error real del entrenador.")
    else:
        print("  >>> Mixto. Hay cambios reales y empates. Analizar caso por caso.")

    # Guardar
    with open("chequeo1_margenes.json", "w") as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "margenes": margenes,
            "detalles": detalles,
        }, f, indent=2)
    print()
    print("[OK] chequeo1_margenes.json guardado")


if __name__ == "__main__":
    main()
