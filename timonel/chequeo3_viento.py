#!/usr/bin/env python3
"""chequeo3_viento.py - Chequeo 3: el viento afecta la decision?

Parte A: corre los 50 casos que cambian con viento=0 y compara
         con los resultados originales (viento del contexto).
Parte B: analiza los 2 casos borderline (CC002-002124, CC002-000806).
"""
import json
import math
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


def barco_desde_state(state, viento_override=None):
    b = Barco()
    b.pos_x = state["pos_x"]
    b.pos_z = state["pos_z"]
    b.yaw = math.radians(state["hdg"])
    sog_ms = state["sog"] / 1.94384449
    b.vel_x = math.sin(b.yaw) * sog_ms
    b.vel_z = -math.cos(b.yaw) * sog_ms
    if viento_override is not None:
        b.viento_intensidad_kn = viento_override
        b.viento_direccion_deg = 0.0
    else:
        b.viento_intensidad_kn = state["viento_kn"]
        b.viento_direccion_deg = state["viento_dir"]
    return b


def main():
    auditoria = json.load(open("auditoria_completa_banco.json"))
    ctxs_by_id = cargar_desarrollo()

    casos = [r for r in auditoria["resultados"]
             if r["etiqueta_original"] == "corregir_rumbo" and r["cambia"]]
    print(f"[chk3] casos que cambian: {len(casos)}")
    print()

    orac = Entrenador(horizontes=HORIZ_240)

    # === PARTE A: viento=0 ===
    print("=== PARTE A: viento=0 vs viento original ===")
    resultados = []
    for r in casos:
        entry = ctxs_by_id.get(r["context_id"])
        if not entry:
            continue
        ctx, lbl = entry
        state = ctx["state"]

        # Con viento original
        b_orig = barco_desde_state(state)
        g_orig = orac.evaluar_todas(b_orig, state["meta_x"], state["meta_z"])[0].receta

        # Con viento 0
        b_zero = barco_desde_state(state, viento_override=0.0)
        g_zero = orac.evaluar_todas(b_zero, state["meta_x"], state["meta_z"])[0].receta

        cambio = g_orig != g_zero
        resultados.append({
            "context_id": r["context_id"],
            "g_con_viento": g_orig,
            "g_sin_viento": g_zero,
            "cambio": cambio,
            "viento_kn": state["viento_kn"],
            "viento_dir": state["viento_dir"],
        })

        if cambio:
            print(f"  {r['context_id']}: con_viento={g_orig} sin_viento={g_zero} | viento={state['viento_kn']}kn@{state['viento_dir']}deg")

    print()
    cambios = sum(1 for r in resultados if r["cambio"])
    print(f"  Total cambios por viento: {cambios}/{len(resultados)}")

    # Distribucion con/sin
    dist_orig = Counter(r["g_con_viento"] for r in resultados)
    dist_zero = Counter(r["g_sin_viento"] for r in resultados)
    print(f"  Con viento: {dict(dist_orig)}")
    print(f"  Sin viento: {dict(dist_zero)}")

    # === PARTE B: casos borderline ===
    print()
    print("=== PARTE B: casos borderline ===")
    borderline = ["CC002-002124", "CC002-000806"]
    for cid in borderline:
        entry = ctxs_by_id.get(cid)
        if not entry:
            continue
        ctx, lbl = entry
        state = ctx["state"]
        print(f"  {cid}:")
        print(f"    viento original: {state['viento_kn']}kn @ {state['viento_dir']}deg")

        for viento_label, viento_val in [("con_viento", None), ("sin_viento", 0.0)]:
            b = barco_desde_state(state, viento_override=viento_val)
            ganadora = orac.evaluar_todas(b, state["meta_x"], state["meta_z"])[0].receta
            print(f"    {viento_label}: {ganadora}")

    # === VEREDICTO ===
    print()
    print("=== VEREDICTO ===")
    n = len(resultados) or 1
    pct = 100 * cambios / n
    print(f"  Cambios por viento: {pct:.0f}%")
    if cambios == 0:
        print("  >>> El viento NO afecta la decision en estos casos.")
    elif cambios <= 3:
        print(f"  >>> El viento afecta marginalmente ({cambios} casos). No es critico.")
    else:
        print(f"  >>> El viento afecta {cambios} casos. Hay que analizar en detalle.")

    # Guardar
    with open("chequeo3_viento.json", "w") as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "cambios_totales": cambios,
            "resultados": resultados,
        }, f, indent=2)
    print()
    print("[OK] chequeo3_viento.json guardado")


if __name__ == "__main__":
    main()
