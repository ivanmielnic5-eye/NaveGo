#!/usr/bin/env python3
"""test_oraculo_300.py - Audita el oraculo sobre los 300 contextos de desarrollo.

Para cada contexto donde el oraculo dice corregir_rumbo:
- Simular corregir_rumbo (hacia la meta)
- Simular ir_a_punto (hacia la meta)
- Comparar distancia final

Reporta: en cuantos casos tiene razon el oraculo vs el modelo.
"""
import copy
import json
import math
import sys
from collections import Counter
from datetime import datetime
sys.path.insert(0, ".")

from simulador_polaris import Barco
from recetas_navegacion import corregir_rumbo, ir_a_punto


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


def simular_accion(barco_base, meta_x, meta_z, accion, timeout_s=60.0):
    import copy
    b = copy.deepcopy(barco_base)
    try:
        if accion == "corregir_rumbo":
            dx = meta_x - b.pos_x
            dz = meta_z - b.pos_z
            rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
            corregir_rumbo(b, objetivo_deg=rumbo, timeout_s=timeout_s)
        elif accion == "ir_a_punto":
            ir_a_punto(b, meta_x, meta_z, tol_dist=15.0, timeout_s=timeout_s)
    except Exception as e:
        return None
    dist_final = math.sqrt((b.pos_x - meta_x)**2 + (b.pos_z - meta_z)**2)
    return round(dist_final, 2)


def main():
    items = cargar_desarrollo()
    casos_cr = [(c, l) for c, l in items if l["accion_optima"] == "corregir_rumbo"]
    print(f"[audit] contextos desarrollo: {len(items)}")
    print(f"[audit] con accion_optima=corregir_rumbo: {len(casos_cr)}")
    print()

    resultados = []
    t0 = datetime.now()

    for i, (ctx, lbl) in enumerate(casos_cr):
        state = ctx["state"]
        b = barco_desde_state(state)
        mx = state["meta_x"]
        mz = state["meta_z"]

        d_cr = simular_accion(b, mx, mz, "corregir_rumbo", timeout_s=60.0)
        d_iap = simular_accion(b, mx, mz, "ir_a_punto", timeout_s=60.0)

        if d_cr is None or d_iap is None:
            continue

        dx = mx - state["pos_x"]
        dz = mz - state["pos_z"]
        dist0 = math.sqrt(dx*dx + dz*dz)
        rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
        desv = abs((rumbo - state["hdg"] + 540) % 360 - 180)

        ganador = "corregir_rumbo" if d_cr < d_iap else ("ir_a_punto" if d_iap < d_cr else "empate")

        resultados.append({
            "context_id": ctx["context_id"],
            "dist_inicial": round(dist0, 2),
            "desv": round(desv, 1),
            "d_corregir": d_cr,
            "d_ir_a_punto": d_iap,
            "ganador": ganador,
            "familia": lbl["familia"],
        })

        if (i + 1) % 20 == 0:
            elapsed = (datetime.now() - t0).total_seconds()
            print(f"  [{i+1}/{len(casos_cr)}] elapsed={elapsed:.1f}s")

    elapsed = (datetime.now() - t0).total_seconds()
    print(f"\n[audit] terminado en {elapsed:.1f}s")

    # Estadisticas
    ganadores = Counter(r["ganador"] for r in resultados)
    print(f"\n=== RESULTADO GLOBAL ===")
    print(f"  Ganador corregir_rumbo (oraculo OK): {ganadores.get('corregir_rumbo', 0)}")
    print(f"  Ganador ir_a_punto (MODELO OK):      {ganadores.get('ir_a_punto', 0)}")
    print(f"  Empates:                             {ganadores.get('empate', 0)}")
    print(f"  Total:                               {len(resultados)}")

    # Analisis por desvio
    print(f"\n=== POR RANGO DE DESVIO ===")
    rangos = [(0, 30), (30, 45), (45, 60), (60, 90), (90, 180)]
    for lo, hi in rangos:
        subset = [r for r in resultados if lo <= r["desv"] < hi]
        if not subset:
            continue
        gc = sum(1 for r in resultados if lo <= r["desv"] < hi and r["ganador"] == "corregir_rumbo")
        gi = sum(1 for r in resultados if lo <= r["desv"] < hi and r["ganador"] == "ir_a_punto")
        print(f"  desv {lo:3d}-{hi:3d}°: corregir_rumbo gana {gc:3d} | ir_a_punto gana {gi:3d} (n={len(subset)})")

    # Guardar
    with open("test_oraculo_300.json", "w") as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "total": len(resultados),
            "ganadores": dict(ganadores),
            "resultados": resultados,
        }, f, indent=2)
    print(f"\n[audit] resultados en test_oraculo_300.json")


if __name__ == "__main__":
    main()
