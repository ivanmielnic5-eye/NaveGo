#!/usr/bin/env python3
"""chequeo2_estabilidad.py - Chequeo 2: 240s es estable?

Corre los 50 casos que cambian con horizontes cercanos a 240s:
180s, 200s, 220s, 240s, 260s, 280s, 300s, 360s.

Si el ganador cambia entre esos horizontes, 240s no es la respuesta final.
Si es estable, si.
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
    "180s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0],
    "200s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 200.0],
    "220s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 200.0, 220.0],
    "240s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 200.0, 220.0, 240.0],
    "260s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 200.0, 220.0, 240.0, 260.0],
    "280s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0],
    "300s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0],
    "360s": [5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 360.0],
}


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

    casos = [r for r in auditoria["resultados"]
             if r["etiqueta_original"] == "corregir_rumbo" and r["cambia"]]
    print(f"[chk2] casos que cambian: {len(casos)}")
    print(f"[chk2] configs: {list(CONFIGS.keys())}")
    print()

    resultados = {}
    for nombre, horiz in CONFIGS.items():
        print(f"[chk2] corriendo {nombre}...")
        orac = Entrenador(horizontes=horiz)
        res = []
        for r in casos:
            entry = ctxs_by_id.get(r["context_id"])
            if not entry:
                res.append("_missing_")
                continue
            ctx, lbl = entry
            state = ctx["state"]
            b = barco_desde_state(state)
            try:
                ganadora = orac.evaluar_todas(b, state["meta_x"], state["meta_z"])[0].receta
                res.append(ganadora)
            except Exception as e:
                res.append("_error_")
        resultados[nombre] = res

    print()
    print("=== ESTABILIDAD ===")
    print(f"{'context_id':20s} | " + " | ".join([f"{n:>16s}" for n in CONFIGS.keys()]))
    cambios_totales = Counter()
    for i, r in enumerate(casos):
        cid = r["context_id"]
        ganadores = [resultados[n][i] for n in CONFIGS.keys()]
        # Solo imprimir si hay mas de una respuesta distinta
        if len(set(ganadores)) > 1:
            print(f"{cid:20s} | " + " | ".join([f"{g:>16s}" for g in ganadores]))
            for n, g in zip(CONFIGS.keys(), ganadores):
                cambios_totales[(n, g)] += 1

    print()
    print("=== DISTRIBUCION POR CONFIG ===")
    for nombre, res in resultados.items():
        c = Counter(res)
        print(f"  {nombre:6s}: {dict(c)}")

    print()
    print("=== CAMBIOS ENTRE CONFIGS CONSECUTIVAS ===")
    nombres = list(CONFIGS.keys())
    total_inestable = 0
    for i in range(1, len(nombres)):
        prev = resultados[nombres[i-1]]
        curr = resultados[nombres[i]]
        cambios = sum(1 for a, b in zip(prev, curr) if a != b)
        print(f"  {nombres[i-1]:6s} -> {nombres[i]:6s}: {cambios:3d} cambios")

    # Casos donde la respuesta final (360s) difiere de 240s
    r_240 = resultados["240s"]
    r_360 = resultados["360s"]
    dif_240_360 = sum(1 for a, b in zip(r_240, r_360) if a != b)
    print()
    print(f"  Cambios entre 240s y 360s: {dif_240_360}")
    print()

    print("=== VEREDICTO ===")
    # Contar casos donde todos los horizontes >= 180s dan lo mismo
    estables = 0
    for i in range(len(casos)):
        ganadores = set(resultados[n][i] for n in CONFIGS.keys())
        if len(ganadores) == 1:
            estables += 1
    print(f"  Casos con mismo ganador en TODOS los horizontes >= 180s: {estables}/{len(casos)}")

    if dif_240_360 == 0 and estables >= len(casos) * 0.9:
        print("  >>> 240s es ESTABLE. Podemos usarlo como horizonte final.")
    else:
        print(f"  >>> 240s NO es completamente estable. {len(casos) - estables} casos varian.")

    # Guardar
    with open("chequeo2_estabilidad.json", "w") as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "configs": {k: v for k, v in CONFIGS.items()},
            "resultados": resultados,
            "dif_240_360": dif_240_360,
            "estables": estables,
        }, f, indent=2)
    print()
    print("[OK] chequeo2_estabilidad.json guardado")


if __name__ == "__main__":
    main()
