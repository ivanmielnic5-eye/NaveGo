#!/usr/bin/env python3
"""test_horizonte_extendido.py - Test A: extender el horizonte del entrenador.

Corre los 30 casos discrepantes (donde el modelo dijo ir_a_punto pero
el oraculo dijo corregir_rumbo) con horizontes extendidos.

Compara: decision con [5, 15, 30, 45] vs [5, 15, 30, 45, 60, 90].
"""
import copy
import json
import math
import sys
from collections import Counter
from datetime import datetime
sys.path.insert(0, ".")

from simulador_polaris import Barco
from recetas_navegacion import corregir_rumbo, ir_a_punto, frenar
from entrenador import Entrenador


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


def simular_receta_60_90(barco_base, meta_x, meta_z, receta, timeout_s):
    """Simula una receta hasta timeout y devuelve progreso a 60 y 90s."""
    b = copy.deepcopy(barco_base)
    try:
        if receta == "corregir_rumbo":
            dx = meta_x - b.pos_x
            dz = meta_z - b.pos_z
            rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
            corregir_rumbo(b, objetivo_deg=rumbo, timeout_s=timeout_s)
        elif receta == "ir_a_punto":
            ir_a_punto(b, meta_x, meta_z, tol_dist=15.0, timeout_s=timeout_s)
        elif receta == "frenar":
            frenar(b, timeout_s=timeout_s)
    except Exception:
        pass
    dist_final = math.sqrt((b.pos_x - meta_x)**2 + (b.pos_z - meta_z)**2)
    return round(dist_final, 2)


def decidir_con_horizontes(barco, meta_x, meta_z, horizontes):
    """Corre el oraculo con horizontes custom y devuelve la ganadora."""
    orac = Entrenador(horizontes=horizontes)
    resultados = orac.evaluar_todas(barco, meta_x, meta_z)
    return resultados[0].receta


def main():
    items = cargar_desarrollo()
    casos_cr = [(c, l) for c, l in items if l["accion_optima"] == "corregir_rumbo"]
    print(f"[test] contextos corregir_rumbo: {len(casos_cr)}")

    # Primero: identificar los 30 discrepantes
    print("[test] identificando discrepantes...")
    discrepantes = []
    orac_orig = Entrenador()
    orac_ext = Entrenador(horizontes=[5.0, 15.0, 30.0, 45.0, 60.0, 90.0])

    for ctx, lbl in casos_cr:
        state = ctx["state"]
        b = barco_desde_state(state)
        mx, mz = state["meta_x"], state["meta_z"]

        # Con horizonte original
        res_orig = orac_orig.evaluar_todas(b, mx, mz)
        ganadora_orig = res_orig[0].receta

        # Con horizonte extendido
        res_ext = orac_ext.evaluar_todas(b, mx, mz)
        ganadora_ext = res_ext[0].receta

        # Chequear si es discrepante (usando el metodo original)
        d_cr = simular_receta_60_90(b, mx, mz, "corregir_rumbo", 60.0)
        d_iap = simular_receta_60_90(b, mx, mz, "ir_a_punto", 60.0)
        es_discrepante = d_iap < d_cr

        if es_discrepante:
            discrepantes.append({
                "context_id": ctx["context_id"],
                "ganadora_orig": ganadora_orig,
                "ganadora_ext": ganadora_ext,
                "d_corregir_60s": d_cr,
                "d_ir_a_punto_60s": d_iap,
                "dist": round(math.sqrt(mx*mx + mz*mz), 2),
                "hdg": state["hdg"],
            })

    print(f"[test] discrepantes: {len(discrepantes)}")
    print()

    # Analisis
    cambiaron = sum(1 for d in discrepantes if d["ganadora_orig"] != d["ganadora_ext"])
    siguen_igual = len(discrepantes) - cambiaron

    print("=== RESULTADO ===")
    print(f"  Discrepantes totales: {len(discrepantes)}")
    print(f"  Oráculo CAMBIA con horizonte extendido: {cambiaron}")
    print(f"  Oráculo NO cambia (sigue corregir_rumbo): {siguen_igual}")

    # Detalle
    print()
    print("=== DETALLE (primeros 15) ===")
    for d in discrepantes[:15]:
        cambio = "CAMBIO" if d["ganadora_orig"] != d["ganadora_ext"] else "igual"
        print(f"  {d['context_id']} orig={d['ganadora_orig']:18s} ext={d['ganadora_ext']:18s} [{cambio}]")

    # Guardar
    with open("test_horizonte_extendido.json", "w") as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "total_discrepantes": len(discrepantes),
            "cambiaron": cambiaron,
            "siguen_igual": siguen_igual,
            "detalle": discrepantes,
        }, f, indent=2)


if __name__ == "__main__":
    main()
