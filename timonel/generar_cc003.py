#!/usr/bin/env python3
"""generar_cc003.py - Genera banco CC003 estratificado.

Estrategia:
- 4 pools de candidatos, uno por zona del espacio de estados.
- Cada pool cubre la zona donde una accion especifica puede ganar.
- Etiquetado con Entrenador v2 (horizontes largos).
- Balance por accion (no por clase original).

Pools:
- A: terminal (dist 5-30m). Cubre terminar y frenar.
- B: cerca + rapido (dist 15-50m, sog 4-8kn). Cubre frenar.
- C: lejos (dist 150-400m). Cubre rumbo e ir_a.
- D: medio (dist 50-150m). Cubre ir_a.

Referencia: EXPEDIENTE/89, diagnostico_cc003.json.
"""
import argparse
import hashlib
import json
import math
import random
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, ".")

from simulador_polaris import Barco
from entrenador_v2 import Entrenador
from admisibilidad import acciones_admisibles


HORIZ_LARGOS = [5.0, 15.0, 30.0, 60.0, 120.0, 240.0]
UMBRAL_UNICIDAD_M = 2.0
N_POR_ACCION = 75


def clasificar_familia(dist):
    if dist < 15.0:
        return "terminal"
    elif dist < 50.0:
        return "cerca"
    elif dist < 150.0:
        return "medio"
    else:
        return "lejos"


def generar_pool_A_terminal(rng):
    """Terminal: dist 5-30m, cualquier heading y sog."""
    dist = rng.uniform(5.0, 30.0)
    return _candidato_desde_dist(rng, dist)


def generar_pool_B_cerca_rapido(rng):
    """Cerca + rapido: dist 15-50m, sog 4-8kn."""
    dist = rng.uniform(15.0, 50.0)
    return _candidato_desde_dist(rng, dist, sog_override=rng.uniform(4.0, 8.0))


def generar_pool_C_lejos(rng):
    """Lejos: dist 150-400m."""
    dist = rng.uniform(150.0, 400.0)
    return _candidato_desde_dist(rng, dist)


def generar_pool_D_medio(rng):
    """Medio: dist 50-150m."""
    dist = rng.uniform(50.0, 150.0)
    return _candidato_desde_dist(rng, dist)


def _candidato_desde_dist(rng, dist, sog_override=None):
    ang_meta = rng.uniform(0.0, 360.0)
    meta_x = round(dist * math.sin(math.radians(ang_meta)), 2)
    meta_z = round(-dist * math.cos(math.radians(ang_meta)), 2)
    hdg = round(rng.uniform(0.0, 360.0), 2)
    sog = round(sog_override, 2) if sog_override else round(rng.uniform(0.0, 8.0), 2)
    v_kn = rng.choice([0.0, 5.0, 10.0, 15.0])
    v_dir = round(rng.uniform(0.0, 360.0), 1) if v_kn > 0 else 0.0
    return {
        "pos_x": 0.0, "pos_z": 0.0,
        "hdg": hdg, "sog": sog,
        "meta_x": meta_x, "meta_z": meta_z,
        "viento_kn": round(v_kn, 1),
        "viento_dir": v_dir,
    }


def state_hash(state):
    s = json.dumps(state, sort_keys=True)
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()[:16]


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


def evaluar_candidato(state, entrenador):
    """Etiqueta un candidato con el Entrenador v2."""
    b = barco_desde_state(state)
    dist = math.sqrt(state["meta_x"]**2 + state["meta_z"]**2)

    det = entrenador.elegir_con_detalle(b, state["meta_x"], state["meta_z"], near_tie_m=1.0)
    mejor = det["mejor"]
    margen = det["margen_vs_segunda"]

    # Recolectar scores por accion
    scores = {}
    for d in det["detalle"]:
        scores[d["accion"]] = {
            "progreso_medio": d["progreso_medio"],
            "progreso_por_horizonte": d["progreso_por_horizonte"],
            "mission_complete": d["mission_complete"],
            "boundary_violation": not d["seguro"],
            "alineacion_deg": d["alineacion_deg"],
        }

    # Admisibilidad (para registrar)
    admisibles = acciones_admisibles(dist, state["sog"])

    # Mission complete si la accion optima es terminar y dist < 15m
    mission_complete = (mejor == "terminar" and dist < 15.0)

    return {
        "accion_optima": mejor,
        "parametro_oraculo": None,  # v2 no expone parametro directo, va en scores
        "scores_por_accion": scores,
        "margen_vs_segunda": margen,
        "mission_complete": mission_complete,
        "admisibles": admisibles,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--candidatos-por-pool", type=int, default=700)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    entrenador = Entrenador(horizontes=HORIZ_LARGOS)

    print(f"[cc003] seed={args.seed}")
    print(f"[cc003] horizontes: {HORIZ_LARGOS}")
    print(f"[cc003] candidatos por pool: {args.candidatos_por_pool}")
    print()

    pools = {
        "A_terminal": (generar_pool_A_terminal, args.candidatos_por_pool),
        "B_cerca_rapido": (generar_pool_B_cerca_rapido, args.candidatos_por_pool),
        "C_lejos": (generar_pool_C_lejos, args.candidatos_por_pool),
        "D_medio": (generar_pool_D_medio, args.candidatos_por_pool),
    }

    t0 = time.time()
    candidatos = []
    hashes_vistos = set()
    por_pool_aceptados = Counter()
    descartes = Counter()

    for pool_nombre, (gen_fn, n) in pools.items():
        print(f"[cc003] pool {pool_nombre}: {n} candidatos")
        for i in range(n):
            state = gen_fn(rng)
            sh = state_hash(state)
            if sh in hashes_vistos:
                descartes["duplicado"] += 1
                continue
            hashes_vistos.add(sh)

            try:
                resultado = evaluar_candidato(state, entrenador)
            except Exception as e:
                descartes["exception"] += 1
                continue

            # Filtrar por margen minimo de unicidad
            margen = resultado["margen_vs_segunda"]
            if margen is not None and margen < UMBRAL_UNICIDAD_M:
                descartes["margen_insuficiente"] += 1
                continue

            dist = math.sqrt(state["meta_x"]**2 + state["meta_z"]**2)
            fam = clasificar_familia(dist)

            candidatos.append({
                "state": state,
                "state_hash": sh,
                "pool_origen": pool_nombre,
                "familia": fam,
                "accion_optima": resultado["accion_optima"],
                "scores_por_accion": resultado["scores_por_accion"],
                "margen_vs_segunda": resultado["margen_vs_segunda"],
                "mission_complete": resultado["mission_complete"],
                "admisibles": resultado["admisibles"],
            })
            por_pool_aceptados[pool_nombre] += 1

            if (i+1) % 100 == 0:
                elapsed = time.time() - t0
                print(f"  [{i+1}/{n}] t={elapsed:.1f}s | total candidatos={len(candidatos)}")

    elapsed = time.time() - t0
    print()
    print(f"[cc003] etiquetado terminado en {elapsed:.1f}s")
    print(f"[cc003] candidatos aceptados: {len(candidatos)}")
    print(f"[cc003] descartes: {dict(descartes)}")
    print()

    # Distribucion por accion
    dist_accion = Counter(c["accion_optima"] for c in candidatos)
    print("=== DISTRIBUCION POR ACCION ===")
    for acc in ["rumbo", "ir_a", "frenar", "terminar"]:
        print(f"  {acc:10s}: {dist_accion.get(acc, 0)}")

    # Balance SOLO por las 2 acciones principales (ir_a, terminar).
    # rumbo y frenar quedan como marginales documentadas.
    ACCIONES_PRINCIPALES = ["ir_a", "terminar"]
    ACCIONES_MARGINALES = ["rumbo", "frenar"]

    min_casos = min(dist_accion.get(a, 0) for a in ACCIONES_PRINCIPALES)
    n_objetivo = min(N_POR_ACCION, min_casos)
    print()
    print(f"[cc003] accion principal mas rara tiene {min_casos} casos")
    print(f"[cc003] objetivo de balance: {n_objetivo} por accion principal")

    # Separar candidatos en principales y marginales
    por_accion = defaultdict(list)
    marginales = []
    for c in candidatos:
        if c["accion_optima"] in ACCIONES_PRINCIPALES:
            por_accion[c["accion_optima"]].append(c)
        else:
            marginales.append(c)

    seleccionados = []
    for accion, lista in por_accion.items():
        rng.shuffle(lista)
        seleccionados.extend(lista[:n_objetivo])

    rng.shuffle(seleccionados)
    print(f"[cc003] seleccionados (principales): {len(seleccionados)}")
    print(f"[cc003] marginales (rumbo/frenar):   {len(marginales)}")

    # Split estratificado por accion
    desarrollo = []
    confirmatorio = []
    for accion, lista in por_accion.items():
        # Ya estan shuffleadas. Tomar la primera mitad para desarrollo
        tomados = lista[:n_objetivo]
        rng.shuffle(tomados)
        n_mitad = len(tomados) // 2
        desarrollo.extend(tomados[:n_mitad])
        confirmatorio.extend(tomados[n_mitad:])

    rng.shuffle(desarrollo)
    rng.shuffle(confirmatorio)

    print(f"[cc003] desarrollo: {len(desarrollo)} | confirmatorio: {len(confirmatorio)}")
    # Verificar balance por accion en cada split
    import collections
    for nombre, split_list in [("desarrollo", desarrollo), ("confirmatorio", confirmatorio)]:
        c = collections.Counter(x["accion_optima"] for x in split_list)
        print(f"[cc003]   {nombre}: {dict(c)}")

    if args.dry_run:
        print()
        print("[DRY-RUN] no se escriben archivos")
        return

    # Escribir archivos
    out_dir = Path("banco_cc003")
    out_dir.mkdir(exist_ok=True)

    with open(out_dir / "banco_contextos.jsonl", "w") as f:
        for c in desarrollo + confirmatorio:
            f.write(json.dumps({
                "context_id": c["state_hash"][:12],
                "state": c["state"],
                "schema_version": "1.0",
                "state_hash": c["state_hash"],
            }, ensure_ascii=False) + "\n")

    with open(out_dir / "banco_etiquetas.jsonl", "w") as f:
        for c in desarrollo + confirmatorio:
            split = "desarrollo" if c in desarrollo else "confirmatorio"
            f.write(json.dumps({
                "context_id": c["state_hash"][:12],
                "entrenador_version": "v2",
                "horizontes": HORIZ_LARGOS,
                "accion_optima": c["accion_optima"],
                "scores_por_accion": c["scores_por_accion"],
                "margen_vs_segunda": c["margen_vs_segunda"],
                "admisibles": c["admisibles"],
                "mission_complete": c["mission_complete"],
                "familia": c["familia"],
                "pool_origen": c["pool_origen"],
                "split": split,
                "label_status": "UNIQUE",
            }, ensure_ascii=False) + "\n")

    # Escribir marginales en archivo aparte (evidencia, no benchmark)
    with open(out_dir / "cc003_marginales.jsonl", "w") as f:
        for c in marginales:
            f.write(json.dumps({
                "context_id": c["state_hash"][:12],
                "state": c["state"],
                "accion_optima": c["accion_optima"],
                "familia": c["familia"],
                "pool_origen": c["pool_origen"],
                "scores_por_accion": c["scores_por_accion"],
            }, ensure_ascii=False) + "\n")

    manifiesto = {
        "version": "CC003-1.0",
        "fecha_generacion": datetime.now().isoformat(),
        "seed": args.seed,
        "entrenador_version": "v2",
        "horizontes": HORIZ_LARGOS,
        "candidatos_por_pool": args.candidatos_por_pool,
        "n_candidatos_totales": len(candidatos),
        "n_seleccionados": len(seleccionados),
        "n_por_accion": n_objetivo,
        "split_counts": {"desarrollo": len(desarrollo), "confirmatorio": len(confirmatorio)},
        "distribucion_accion": dict(dist_accion),
        "distribucion_pool": dict(por_pool_aceptados),
    }
    with open(out_dir / "banco_manifiesto.json", "w") as f:
        json.dump(manifiesto, f, indent=2, ensure_ascii=False)

    print(f"[cc003] archivos en {out_dir}/")


if __name__ == "__main__":
    main()
