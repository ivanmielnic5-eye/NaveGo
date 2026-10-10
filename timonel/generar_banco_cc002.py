#!/usr/bin/env python3
import argparse, hashlib, json, math, random, sys
from collections import Counter
from datetime import datetime
from pathlib import Path
sys.path.insert(0, '.')
from simulador_polaris import Barco
from oraculo import Oracle

UMBRAL_UNICIDAD_M = 2.0
TOL_TERMINAL = 15.0
FAMILIAS = {"terminal": (0.0, 15.0), "cerca": (15.0, 50.0), "medio": (50.0, 150.0), "lejos": (150.0, 300.0)}
N_DESARROLLO_POR_ACCION = 75
N_CONFIRMATORIO_POR_ACCION = 75

def clasificar_familia(dist):
    for nombre, (dmin, dmax) in FAMILIAS.items():
        if dmin <= dist < dmax:
            return nombre
    return "lejos"

def generar_candidato(rng):
    # 25% de las veces, forzar distancia corta (para cubrir familia terminal)
    # El resto: distribucion uniforme del espacio
    if rng.random() < 0.25:
        dist = rng.uniform(5.0, 20.0)
    else:
        dist = rng.uniform(15.0, 250.0)
    ang_meta = rng.uniform(0.0, 360.0)
    meta_x = round(dist * math.sin(math.radians(ang_meta)), 2)
    meta_z = round(-dist * math.cos(math.radians(ang_meta)), 2)
    hdg = round(rng.uniform(0.0, 360.0), 2)
    sog = round(rng.uniform(0.0, 8.0), 2)
    v_kn = rng.choice([0.0, 5.0, 10.0, 15.0])
    v_dir = round(rng.uniform(0.0, 360.0), 1) if v_kn > 0 else 0.0
    return {"pos_x": 0.0, "pos_z": 0.0, "hdg": hdg, "sog": sog, "meta_x": meta_x, "meta_z": meta_z, "viento_kn": round(v_kn, 1), "viento_dir": v_dir}

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

def state_hash(state):
    return "sha256:" + hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()[:16]


def evaluar_candidato(state, orac):
    b = barco_desde_state(state)
    resultados = orac.evaluar_todas(b, state["meta_x"], state["meta_z"])
    mejor = resultados[0]
    margen_vs_segunda = None
    for r in resultados[1:]:
        if r.mission_complete != mejor.mission_complete:
            continue
        if r.boundary_violation != mejor.boundary_violation:
            continue
        margen_vs_segunda = round(mejor.progreso_medio - r.progreso_medio, 3)
        break
    scores = {}
    for r in resultados:
        scores[r.receta] = {"progreso_medio": r.progreso_medio, "mission_complete": r.mission_complete, "boundary_violation": r.boundary_violation, "parametro": r.parametro}
    return {"accion_optima": mejor.receta, "parametro_oraculo": mejor.parametro, "scores_por_accion": scores, "margen_vs_segunda": margen_vs_segunda, "boundary_violation": mejor.boundary_violation, "mission_complete": mejor.mission_complete}

def aceptar(resultado, dist):
    if resultado["boundary_violation"]:
        return False, "boundary_violation"
    if resultado["accion_optima"] == "terminar" and dist >= TOL_TERMINAL:
        return False, "terminal_invalido"
    if resultado["accion_optima"] != "terminar" and dist < TOL_TERMINAL:
        return False, "terminal_ambiguo"
    if resultado["margen_vs_segunda"] is not None and resultado["margen_vs_segunda"] < UMBRAL_UNICIDAD_M:
        return False, "margen_insuficiente"
    return True, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    orac = Oracle()
    print("[banco] generando " + str(args.n) + " candidatos (seed=" + str(args.seed) + ")")
    print("[banco] umbral unicidad: " + str(UMBRAL_UNICIDAD_M) + "m")

    candidatos = []
    descartes = Counter()
    hashes_vistos = set()
    t0 = datetime.now()

    for i in range(args.n):
        state = generar_candidato(rng)
        dist = math.sqrt(state["meta_x"] ** 2 + state["meta_z"] ** 2)
        sh = state_hash(state)
        if sh in hashes_vistos:
            descartes["duplicado"] += 1
            continue
        hashes_vistos.add(sh)
        try:
            resultado = evaluar_candidato(state, orac)
        except Exception as e:
            descartes["exception"] += 1
            print("  [" + str(i+1) + "] ERROR: " + str(e))
            continue
        ok, razon = aceptar(resultado, dist)
        if not ok:
            descartes[razon] += 1
            continue
        familia = clasificar_familia(dist)
        candidatos.append({"context_id": "CC002-" + str(len(candidatos)+1).zfill(6), "state": state, "state_hash": sh, "familia": familia, "accion_optima": resultado["accion_optima"], "parametro_oraculo": resultado["parametro_oraculo"], "scores_por_accion": resultado["scores_por_accion"], "margen_vs_segunda": resultado["margen_vs_segunda"], "mission_complete": resultado["mission_complete"]})
        if (i + 1) % 10 == 0:
            elapsed = (datetime.now() - t0).total_seconds()
            print("  [" + str(i+1) + "/" + str(args.n) + "] aceptados=" + str(len(candidatos)) + " elapsed=" + str(round(elapsed, 1)) + "s")

    elapsed = (datetime.now() - t0).total_seconds()
    print("\n[banco] terminado en " + str(round(elapsed, 1)) + "s")
    print("[banco] aceptados: " + str(len(candidatos)))
    print("[banco] descartes: " + str(dict(descartes)))
    accion_count = Counter(c["accion_optima"] for c in candidatos)
    familia_count = Counter(c["familia"] for c in candidatos)
    print("[banco] por accion: " + str(dict(accion_count)))
    print("[banco] por familia: " + str(dict(familia_count)))

    if args.dry_run:
        print("\n[DRY-RUN] no se escriben archivos.")
        if candidatos:
            print("\n=== EJEMPLO (primer contexto) ===")
            print(json.dumps(candidatos[0], indent=2, default=str))
        return

    por_accion = {}
    for c in candidatos:
        por_accion.setdefault(c["accion_optima"], []).append(c)

    desarrollo = []
    confirmatorio = []
    for accion, lista in por_accion.items():
        rng.shuffle(lista)
        n_dev = min(N_DESARROLLO_POR_ACCION, len(lista) // 2)
        n_conf = min(N_CONFIRMATORIO_POR_ACCION, len(lista) - n_dev)
        desarrollo.extend(lista[:n_dev])
        confirmatorio.extend(lista[n_dev:n_dev + n_conf])

    print("\n[banco] desarrollo: " + str(len(desarrollo)))
    print("[banco] confirmatorio: " + str(len(confirmatorio)))

    out_dir = Path("banco_cc002")
    out_dir.mkdir(exist_ok=True)

    with open(out_dir / "banco_contextos.jsonl", "w") as f:
        for c in desarrollo + confirmatorio:
            f.write(json.dumps({"context_id": c["context_id"], "state": c["state"], "schema_version": "1.0", "state_hash": c["state_hash"]}) + "\n")

    with open(out_dir / "banco_etiquetas.jsonl", "w") as f:
        for c in desarrollo + confirmatorio:
            split = "desarrollo" if c in desarrollo else "confirmatorio"
            f.write(json.dumps({"context_id": c["context_id"], "oracle_version": "2.0", "accion_optima": c["accion_optima"], "parametro_oraculo": c["parametro_oraculo"], "scores_por_accion": c["scores_por_accion"], "margen_vs_segunda": c["margen_vs_segunda"], "label_status": "UNIQUE", "familia": c["familia"], "split": split}) + "\n")

    manifiesto = {"version": "CC002-1.0", "fecha_generacion": datetime.now().isoformat(), "seed": args.seed, "oracle_version": "2.0", "umbral_unicidad_m": UMBRAL_UNICIDAD_M, "n_candidatos_generados": args.n, "n_contextos_finales": len(desarrollo) + len(confirmatorio), "n_descartados": dict(descartes), "split_counts": {"desarrollo": len(desarrollo), "confirmatorio": len(confirmatorio)}, "accion_counts": dict(accion_count), "familia_counts": dict(familia_count)}
    with open(out_dir / "banco_manifiesto.json", "w") as f:
        json.dump(manifiesto, f, indent=2)

    print("\n[banco] archivos escritos en " + str(out_dir) + "/")


if __name__ == "__main__":
    main()
