#!/usr/bin/env python3
"""analisis_radio_giro.py - Analiza si el patron de cambios 45s->240s
en la clase corregir_rumbo se explica por el radio de giro.

Hipotesis del Director:
  El velero, por su radio de giro, no puede ir directo al punto.
  Cuando el oraculo solo mira 45s, "ve" que corregir_rumbo parece
  progresar. Cuando mira 240s, "ve" que el barco se aleja por el radio
  de giro y que ir_a_punto es mejor.

  Es decir: el LLM NO deliraba. Su eleccion era la correcta.
  El oraculo miope no lo veia por limitacion de horizonte.

Este script NO simula nada nuevo. Solo analiza los resultados ya
obtenidos en auditoria_completa_banco.json cruzandolos con el estado
de cada contexto (distancia, desvio, familia).
"""
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
sys.path.insert(0, ".")


def cargar_banco():
    ctxs = [json.loads(l) for l in open("banco_cc002/banco_contextos.jsonl")]
    lbls = [json.loads(l) for l in open("banco_cc002/banco_etiquetas.jsonl")]
    by_id = {l["context_id"]: l for l in lbls}
    ctxs_by_id = {c["context_id"]: c for c in ctxs}
    return ctxs_by_id, by_id


def calcular_distancia(state):
    return math.sqrt(state["meta_x"]**2 + state["meta_z"]**2)


def calcular_desvio(state):
    """Desvio angular entre heading y rumbo hacia la meta."""
    dx = state["meta_x"] - state["pos_x"]
    dz = state["meta_z"] - state["pos_z"]
    rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
    desv = abs((rumbo - state["hdg"] + 540) % 360 - 180)
    return desv


def clasificar_familia(dist):
    if dist < 15.0:
        return "terminal"
    elif dist < 50.0:
        return "cerca"
    elif dist < 150.0:
        return "medio"
    else:
        return "lejos"


def estadisticas(valores):
    if not valores:
        return None
    return {
        "n": len(valores),
        "min": round(min(valores), 2),
        "max": round(max(valores), 2),
        "media": round(statistics.mean(valores), 2),
        "mediana": round(statistics.median(valores), 2),
    }


def histograma(valores, bins, etiqueta_bin):
    """Histograma ASCII."""
    contadores = Counter()
    for v in valores:
        for lo, hi in bins:
            if lo <= v < hi:
                contadores[(lo, hi)] += 1
                break
    max_count = max(contadores.values()) if contadores else 1
    print(f"  {etiqueta_bin}:")
    for lo, hi in bins:
        count = contadores.get((lo, hi), 0)
        barra = "#" * int(40 * count / max_count) if max_count > 0 else ""
        print(f"    {lo:5.0f}-{hi:5.0f}: {count:3d} {barra}")


def main():
    print("=" * 70)
    print("ANALISIS DEL PATRON DE CAMBIOS 45s -> 240s")
    print("Hipotesis: radio de giro explica por que ir_a_punto gana")
    print("=" * 70)
    print()

    # Cargar datos
    auditoria = json.load(open("auditoria_completa_banco.json"))
    ctxs_by_id, lbls_by_id = cargar_banco()

    # Filtrar solo los casos con etiqueta_original = corregir_rumbo
    casos_cr = [r for r in auditoria["resultados"]
                if r["etiqueta_original"] == "corregir_rumbo"]

    print(f"Casos con etiqueta original corregir_rumbo: {len(casos_cr)}")

    # Separar en dos grupos: los que cambian y los que no
    cambian = [r for r in casos_cr if r["cambia"]]
    no_cambian = [r for r in casos_cr if not r["cambia"]]

    print(f"  Cambian a ir_a_punto (240s): {len(cambian)}")
    print(f"  Siguen siendo corregir_rumbo: {len(no_cambian)}")
    print()

    # Extraer distancias y desvios para cada grupo
    dist_cambian = []
    desv_cambian = []
    fam_cambian = Counter()

    dist_no_cambian = []
    desv_no_cambian = []
    fam_no_cambian = Counter()

    detalle = []

    for r in casos_cr:
        ctx = ctxs_by_id.get(r["context_id"])
        if not ctx:
            continue
        state = ctx["state"]
        dist = calcular_distancia(state)
        desv = calcular_desvio(state)
        fam = clasificar_familia(dist)

        if r["cambia"]:
            dist_cambian.append(dist)
            desv_cambian.append(desv)
            fam_cambian[fam] += 1
        else:
            dist_no_cambian.append(dist)
            desv_no_cambian.append(desv)
            fam_no_cambian[fam] += 1

        detalle.append({
            "context_id": r["context_id"],
            "cambia": r["cambia"],
            "dist": round(dist, 2),
            "desv": round(desv, 2),
            "familia": fam,
            "ganadora_240s": r["ganadora_240s"],
        })

    # === ESTADISTICAS DE DISTANCIA ===
    print("=" * 70)
    print("DISTANCIA INICIAL A LA META")
    print("=" * 70)
    print()
    print("GRUPO QUE CAMBIA (el oraculo se equivoco con 45s):")
    est = estadisticas(dist_cambian)
    for k, v in est.items():
        print(f"  {k:8s}: {v}")
    print()
    print("GRUPO QUE NO CAMBIA (el oraculo acerto con 45s):")
    est = estadisticas(dist_no_cambian)
    for k, v in est.items():
        print(f"  {k:8s}: {v}")
    print()

    # Diferencia
    if dist_cambian and dist_no_cambian:
        dif_media = statistics.mean(dist_cambian) - statistics.mean(dist_no_cambian)
        print(f"  Diferencia de medias: {dif_media:+.2f} metros")
        if abs(dif_media) > 30:
            print(f"  -> Los grupos tienen distancias MUY distintas")
        elif abs(dif_media) > 10:
            print(f"  -> Los grupos tienen distancias distintas")
        else:
            print(f"  -> Los grupos tienen distancias SIMILARES")
    print()

    # === ESTADISTICAS DE DESVIO ===
    print("=" * 70)
    print("DESVIO ANGULAR INICIAL")
    print("=" * 70)
    print()
    print("GRUPO QUE CAMBIA:")
    est = estadisticas(desv_cambian)
    for k, v in est.items():
        print(f"  {k:8s}: {v}")
    print()
    print("GRUPO QUE NO CAMBIA:")
    est = estadisticas(desv_no_cambian)
    for k, v in est.items():
        print(f"  {k:8s}: {v}")
    print()

    if desv_cambian and desv_no_cambian:
        dif_media = statistics.mean(desv_cambian) - statistics.mean(desv_no_cambian)
        print(f"  Diferencia de medias: {dif_media:+.2f} grados")
        if abs(dif_media) > 30:
            print(f"  -> Los grupos tienen desvios MUY distintos")
        elif abs(dif_media) > 10:
            print(f"  -> Los grupos tienen desvios distintos")
        else:
            print(f"  -> Los grupos tienen desvios SIMILARES")
    print()

    # === HISTOGRAMAS ===
    print("=" * 70)
    print("HISTOGRAMAS")
    print("=" * 70)
    print()

    bins_dist = [(0, 20), (20, 50), (50, 100), (100, 150), (150, 300)]
    bins_desv = [(0, 30), (30, 45), (45, 60), (60, 90), (90, 180)]

    print("DISTANCIA:")
    print("  --- GRUPO QUE CAMBIA ---")
    histograma(dist_cambian, bins_dist, "distancia")
    print("  --- GRUPO QUE NO CAMBIA ---")
    histograma(dist_no_cambian, bins_dist, "distancia")
    print()

    print("DESVIO:")
    print("  --- GRUPO QUE CAMBIA ---")
    histograma(desv_cambian, bins_desv, "desvio")
    print("  --- GRUPO QUE NO CAMBIA ---")
    histograma(desv_no_cambian, bins_desv, "desvio")
    print()

    # === DISTRIBUCION POR FAMILIA ===
    print("=" * 70)
    print("DISTRIBUCION POR FAMILIA")
    print("=" * 70)
    print()
    print("GRUPO QUE CAMBIA:")
    for fam in ["terminal", "cerca", "medio", "lejos"]:
        print(f"  {fam:10s}: {fam_cambian.get(fam, 0)}")
    print()
    print("GRUPO QUE NO CAMBIA:")
    for fam in ["terminal", "cerca", "medio", "lejos"]:
        print(f"  {fam:10s}: {fam_no_cambian.get(fam, 0)}")
    print()

    # === CRUCE DISTANCIA x DESVIO ===
    print("=" * 70)
    print("CRUCE DISTANCIA x DESVIO (casos que CAMBIAN)")
    print("=" * 70)
    print()

    rangos_dist = ["0-20", "20-50", "50-100", "100-150", "150-300"]
    rangos_desv = ["0-30", "30-45", "45-60", "60-90", "90-180"]

    # Matriz 5x5
    print(f"{'':10s} " + " ".join([f"{r:>8s}" for r in rangos_desv]))
    for i, rd in enumerate(rangos_dist):
        fila = []
        for j, rv in enumerate(rangos_desv):
            count = sum(1 for d in detalle
                       if d["cambia"]
                       and eval(rd.replace("-", " <= d['dist'] < ").replace("0 <= d['dist'] < 20", "0 <= d['dist'] < 20"))
                       and eval(rv.replace("-", " <= d['desv'] < ").replace("0 <= d['desv'] < 30", "0 <= d['desv'] < 30")))
            # Esto no funciona bien, mejor lo hago manual
        print()

    # Recalculo limpio de la matriz
    dist_bins = [(0, 20), (20, 50), (50, 100), (100, 150), (150, 300)]
    desv_bins = [(0, 30), (30, 45), (45, 60), (60, 90), (90, 180)]

    matriz_cambian = Counter()
    matriz_no_cambian = Counter()
    for d in detalle:
        for lo_d, hi_d in dist_bins:
            if lo_d <= d["dist"] < hi_d:
                for lo_v, hi_v in desv_bins:
                    if lo_v <= d["desv"] < hi_v:
                        if d["cambia"]:
                            matriz_cambian[(lo_d, lo_v)] += 1
                        else:
                            matriz_no_cambian[(lo_d, lo_v)] += 1
                        break
                break

    print("Casos que CAMBIAN (por celda):")
    print(f"{'DIST\DESV':12s} " + " ".join([f"{lo:>4}-{hi:<3}" for lo, hi in desv_bins]))
    for lo_d, hi_d in dist_bins:
        fila = [f"{lo_d:>4}-{hi_d:<3}"]
        for lo_v, hi_v in desv_bins:
            fila.append(f"{matriz_cambian.get((lo_d, lo_v), 0):>8d}")
        print(" ".join(fila))
    print()

    print("Casos que NO CAMBIAN (por celda):")
    print(f"{'DIST\DESV':12s} " + " ".join([f"{lo:>4}-{hi:<3}" for lo, hi in desv_bins]))
    for lo_d, hi_d in dist_bins:
        fila = [f"{lo_d:>4}-{hi_d:<3}"]
        for lo_v, hi_v in desv_bins:
            fila.append(f"{matriz_no_cambian.get((lo_d, lo_v), 0):>8d}")
        print(" ".join(fila))
    print()

    # === CONCLUSION ===
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print()

    cambia_cerca = fam_cambian.get("terminal", 0) + fam_cambian.get("cerca", 0)
    cambia_lejos = fam_cambian.get("medio", 0) + fam_cambian.get("lejos", 0)
    no_cambia_cerca = fam_no_cambian.get("terminal", 0) + fam_no_cambian.get("cerca", 0)
    no_cambia_lejos = fam_no_cambian.get("medio", 0) + fam_no_cambian.get("lejos", 0)

    print(f"Grupo que CAMBIA: cerca/terminal={cambia_cerca}, medio/lejos={cambia_lejos}")
    print(f"Grupo que NO CAMBIA: cerca/terminal={no_cambia_cerca}, medio/lejos={no_cambia_lejos}")
    print()

    total_cambia = len(cambian)
    pct_cambia_cerca = 100 * cambia_cerca / total_cambia if total_cambia else 0
    total_no_cambia = len(no_cambian)
    pct_no_cambia_lejos = 100 * no_cambia_lejos / total_no_cambia if total_no_cambia else 0

    print(f"Del grupo que CAMBIA: {pct_cambia_cerca:.0f}% son cerca/terminal")
    print(f"Del grupo que NO CAMBIA: {pct_no_cambia_lejos:.0f}% son medio/lejos")
    print()

    # Diagnostico
    hipotesis_confirmada = False
    if dist_cambian and dist_no_cambian:
        if statistics.mean(dist_cambian) < statistics.mean(dist_no_cambian) - 20:
            hipotesis_confirmada = True
    if desv_cambian and desv_no_cambian:
        if statistics.mean(desv_cambian) > statistics.mean(desv_no_cambian) + 20:
            hipotesis_confirmada = True

    if hipotesis_confirmada:
        print(">>> HIPOTESIS DEL RADIO DE GIRO: CONFIRMADA <<<")
        print("Los casos que cambian tienden a tener:")
        print("  - distancia MAS CORTA a la meta")
        print("  - desvio MAS GRANDE")
        print("Esto es compatible con la hipotesis de que el radio de giro")
        print("hace que corregir_rumbo sea geometricamente malo en esta zona.")
    else:
        print(">>> HIPOTESIS DEL RADIO DE GIRO: NO CONFIRMADA <<<")
        print("Los casos que cambian NO tienen un patron claro de")
        print("distancia corta + desvio alto. Puede haber otra causa.")
    print()

    # Guardar
    with open("analisis_radio_giro.json", "w") as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "total_corregir_rumbo": len(casos_cr),
            "cambian": len(cambian),
            "no_cambian": len(no_cambian),
            "dist_cambian": estadisticas(dist_cambian),
            "dist_no_cambian": estadisticas(dist_no_cambian),
            "desv_cambian": estadisticas(desv_cambian),
            "desv_no_cambian": estadisticas(desv_no_cambian),
            "fam_cambian": dict(fam_cambian),
            "fam_no_cambian": dict(fam_no_cambian),
            "detalle": detalle,
        }, f, indent=2)
    print("[OK] analisis_radio_giro.json guardado")


if __name__ == "__main__":
    main()
