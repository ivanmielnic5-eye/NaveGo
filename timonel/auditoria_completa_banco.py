#!/usr/bin/env python3
"""auditoria_completa_banco.py - Audita las 4 clases del banco con 240s.

Para cada uno de los 300 contextos del split desarrollo:
- Corre el oraculo original (45s).
- Corre el oraculo convergido (240s).
- Compara la etiqueta.

Reporta por clase: cuantos cambios hay.
"""
import json
import math
import sys
from collections import Counter
from datetime import datetime
sys.path.insert(0, ".")

from simulador_polaris import Barco
from entrenador import Entrenador


HORIZ_ORIG = [5.0, 15.0, 30.0, 45.0]
HORIZ_240 = [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 240.0]
ACCIONES = ["corregir_rumbo", "ir_a_punto", "frenar", "terminar"]


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
    print(f"[audit] contextos desarrollo: {len(items)}")
    print()

    orac_orig = Entrenador(horizontes=HORIZ_ORIG)
    orac_240 = Entrenador(horizontes=HORIZ_240)

    resultados = []
    t0 = datetime.now()

    for i, (ctx, lbl) in enumerate(items):
        state = ctx["state"]
        b = barco_desde_state(state)
        mx, mz = state["meta_x"], state["meta_z"]

        try:
            g_orig = orac_orig.evaluar_todas(b, mx, mz)[0].receta
            g_240 = orac_240.evaluar_todas(b, mx, mz)[0].receta
        except Exception as e:
            print(f"  ERROR {ctx['context_id']}: {e}")
            continue

        etiqueta_original = lbl["accion_optima"]

        resultados.append({
            "context_id": ctx["context_id"],
            "etiqueta_original": etiqueta_original,
            "ganadora_45s": g_orig,
            "ganadora_240s": g_240,
            "cambia": etiqueta_original != g_240,
            "familia": lbl["familia"],
        })

        if (i + 1) % 50 == 0:
            elapsed = (datetime.now() - t0).total_seconds()
            print(f"  [{i+1}/{len(items)}] elapsed={elapsed:.1f}s")

    elapsed = (datetime.now() - t0).total_seconds()
    print(f"\n[audit] terminado en {elapsed:.1f}s")

    # Por clase
    print("\n=== CAMBIOS POR CLASE ORIGINAL ===")
    for accion in ACCIONES:
        subset = [r for r in resultados if r["etiqueta_original"] == accion]
        if not subset:
            continue
        cambios = sum(1 for r in subset if r["cambia"])
        print(f"  {accion:18s}: {cambios:3d}/{len(subset):3d} cambios ({100*cambios/len(subset):.1f}%)")

    # Distribucion total
    print("\n=== DISTRIBUCION TOTAL ===")
    etiq_orig = Counter(r["etiqueta_original"] for r in resultados)
    gan_240 = Counter(r["ganadora_240s"] for r in resultados)
    print(f"  Etiqueta original:  {dict(etiq_orig)}")
    print(f"  Ganadora 240s:      {dict(gan_240)}")

    # Matriz de confusion
    print("\n=== MATRIZ DE CONFUSION (etiqueta orig -> ganadora 240s) ===")
    matriz = {a: Counter() for a in ACCIONES}
    for r in resultados:
        matriz[r["etiqueta_original"]][r["ganadora_240s"]] += 1

    print(f"{'ETIQUETA':18s} -> " + " | ".join([f"{a[:12]:12s}" for a in ACCIONES]))
    for v in ACCIONES:
        fila = " | ".join([f"{matriz[v].get(p, 0):12d}" for p in ACCIONES])
        print(f"{v:18s} -> {fila}")

    # Guardar
    with open("auditoria_completa_banco.json", "w") as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "total": len(resultados),
            "resultados": resultados,
        }, f, indent=2)
    print()
    print("[OK] auditoria_completa_banco.json guardado")


if __name__ == "__main__":
    main()
