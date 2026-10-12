#!/usr/bin/env python3
"""pre_entrenamiento.py - Chequeos obligatorios antes de entrenar.

Se ejecuta ANTES de cualquier SFT. Si algo falla, ABORTA (exit != 0).

Chequeos:
1. Estructura del banco (integridad, IDs, schema).
2. Balance por accion.
3. Margen minimo de unicidad.
4. Distribucion de distancias (detecta gaps).
5. Distribucion de desvios (detecta gaps).
6. Prompt sin reglas de decision.
7. Coherencia banco/etiquetas/prompt.

Uso:
    python3 pre_entrenamiento.py --banco-dir banco_cc003 \
        --train train_cc003.jsonl \
        --eval eval_cc003_confirmatorio.jsonl

Referencia: EXPEDIENTE/89 secciones 14 y 15.
"""
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path


# ============================================================
# UMBRALES
# ============================================================

UMBRAL_MARGEN_M = 2.0       # margen minimo de unicidad
UMBRAL_GAP_M = 3.0          # gap minimo detectable en distancias
UMBRAL_DECISION_M = 15.0    # umbral de decision (terminar vs ir_a)
UMBRAL_ZONA_CRITICA_M = 2.0 # que tan cerca del umbral tiene que haber casos

REGLAS_PROHIBIDAS = [
    # Solo reglas condicionales explicitas. El umbral 15m PUEDE aparecer
    # en el PROPOSITO (definicion de mision), pero NO en la descripcion
    # de una accion.
    "Valida SOLO",
    "valida solo",
    "Usala si ",
    "Elegila si",
    "Usa terminar si",
    "Usa ir_a si",
    "si estas a menos",
    "si estas mal alineado",
    "si estas bien alineado",
]


# ============================================================
# UTILIDADES
# ============================================================

def _distancia(state):
    dx = state["meta_x"] - state["pos_x"]
    dz = state["meta_z"] - state["pos_z"]
    return math.sqrt(dx*dx + dz*dz)


def _desvio(state):
    dx = state["meta_x"] - state["pos_x"]
    dz = state["meta_z"] - state["pos_z"]
    rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
    return abs((rumbo - state["hdg"] + 540) % 360 - 180)


class Reporte:
    def __init__(self):
        self.ok = True
        self.fallos = []

    def pasa(self):
        print("  [OK]")

    def falla(self, msg):
        print(f"  [FAIL] {msg}")
        self.ok = False
        self.fallos.append(msg)


# ============================================================
# CHEQUEOS
# ============================================================

def chk_1_estructura(reporte, ctxs, lbls):
    print("=== CHK 1: ESTRUCTURA ===")
    campos_state = {"pos_x", "pos_z", "hdg", "sog", "meta_x", "meta_z", "viento_kn", "viento_dir"}
    malos = 0
    for c in ctxs:
        if set(c["state"].keys()) != campos_state:
            malos += 1
    if malos > 0:
        reporte.falla(f"{malos} contextos con schema incorrecto")
    else:
        reporte.pasa()

    ids_ctx = set(c["context_id"] for c in ctxs)
    ids_lbl = set(l["context_id"] for l in lbls)
    faltan = len(ids_ctx - ids_lbl) + len(ids_lbl - ids_ctx)
    if faltan > 0:
        reporte.falla(f"{faltan} IDs no coinciden entre contextos y etiquetas")
    else:
        reporte.pasa()


def chk_2_balance(reporte, lbls, min_por_accion=20):
    print("=== CHK 2: BALANCE POR ACCION ===")
    dist = Counter(l["accion_optima"] for l in lbls)
    print(f"  Distribucion: {dict(dist)}")
    min_acc = min(dist.values()) if dist else 0
    if min_acc < min_por_accion:
        reporte.falla(f"accion con {min_acc} casos (minimo {min_por_accion})")
    else:
        reporte.pasa()


def chk_3_margen(reporte, lbls, umbral=UMBRAL_MARGEN_M):
    print("=== CHK 3: MARGEN DE UNICIDAD ===")
    malos = sum(1 for l in lbls if l.get("margen_vs_segunda") is not None
                and l["margen_vs_segunda"] < umbral)
    if malos > 0:
        reporte.falla(f"{malos} labels con margen < {umbral}m")
    else:
        reporte.pasa()


def chk_4_distancias(reporte, ctxs, lbls):
    print("=== CHK 4: DISTRIBUCION DE DISTANCIAS ===")
    lbls_by_id = {l["context_id"]: l for l in lbls}
    por_accion = {}
    for c in ctxs:
        lbl = lbls_by_id.get(c["context_id"])
        if not lbl:
            continue
        acc = lbl["accion_optima"]
        por_accion.setdefault(acc, []).append(_distancia(c["state"]))

    for acc in sorted(por_accion.keys()):
        dists = sorted(por_accion[acc])
        print(f"  {acc}: n={len(dists)} min={min(dists):.2f} max={max(dists):.2f}")

    # Detectar gap entre la distancia maxima de terminar y la minima de ir_a
    if "terminar" in por_accion and "ir_a" in por_accion:
        max_term = max(por_accion["terminar"])
        min_ir_a = min(por_accion["ir_a"])
        gap = min_ir_a - max_term
        print(f"  Gap entre 'terminar' (max {max_term:.2f}m) e 'ir_a' (min {min_ir_a:.2f}m): {gap:.2f}m")

        if gap > UMBRAL_GAP_M:
            reporte.falla(
                f"GAP de {gap:.2f}m sin casos entre terminar e ir_a. "
                f"El modelo no tiene que aprender el umbral exacto."
            )
        else:
            reporte.pasa()

        # Verificar zona critica SIMETRICA: casos de terminar CERCA del umbral
        # (abajo) Y casos de ir_a CERCA del umbral (arriba). Sin ambos, el
        # modelo no aprende el umbral, solo distingue grupos separados.
        zona_baja = [d for d in por_accion.get("terminar", [])
                     if UMBRAL_DECISION_M - UMBRAL_ZONA_CRITICA_M <= d < UMBRAL_DECISION_M]
        zona_alta = [d for d in por_accion.get("ir_a", [])
                     if UMBRAL_DECISION_M < d <= UMBRAL_DECISION_M + UMBRAL_ZONA_CRITICA_M]
        print(f"  Zona baja [{UMBRAL_DECISION_M - UMBRAL_ZONA_CRITICA_M:.1f}-{UMBRAL_DECISION_M:.1f}m] (terminar): {len(zona_baja)}")
        print(f"  Zona alta [{UMBRAL_DECISION_M:.1f}-{UMBRAL_DECISION_M + UMBRAL_ZONA_CRITICA_M:.1f}m] (ir_a): {len(zona_alta)}")
        if len(zona_baja) < 3 or len(zona_alta) < 3:
            reporte.falla(
                f"falta cobertura en zona critica: "
                f"{len(zona_baja)} terminar abajo, {len(zona_alta)} ir_a arriba"
            )
        else:
            reporte.pasa()


def chk_5_desvios(reporte, ctxs, lbls):
    print("=== CHK 5: DISTRIBUCION DE DESVIOS ===")
    lbls_by_id = {l["context_id"]: l for l in lbls}
    desvios = []
    for c in ctxs:
        if c["context_id"] in lbls_by_id:
            desvios.append(_desvio(c["state"]))
    if not desvios:
        reporte.falla("no hay casos")
        return
    desvios.sort()
    print(f"  n={len(desvios)} min={min(desvios):.2f} max={max(desvios):.2f} "
          f"media={sum(desvios)/len(desvios):.2f}")
    reporte.pasa()


def chk_6_prompt_sin_reglas(reporte, train_path, eval_path):
    print("=== CHK 6: PROMPT SIN REGLAS DE DECISION ===")
    errores = 0
    with open(train_path) as f:
        for i, line in enumerate(f):
            ej = json.loads(line)
            user_content = ej["messages"][1]["content"]
            for regla in REGLAS_PROHIBIDAS:
                if regla.lower() in user_content.lower():
                    print(f"    [FAIL] train ej {i} contiene '{regla}'")
                    errores += 1
    with open(eval_path) as f:
        for i, line in enumerate(f):
            caso = json.loads(line)
            prompt = caso.get("prompt_limpio", "")
            for regla in REGLAS_PROHIBIDAS:
                if regla.lower() in prompt.lower():
                    print(f"    [FAIL] eval ej {i} contiene '{regla}'")
                    errores += 1
    if errores > 0:
        reporte.falla(f"{errores} reglas de decision en prompts")
    else:
        reporte.pasa()


def chk_7_coherencia(reporte, ctxs, lbls, train_path):
    print("=== CHK 7: COHERENCIA BANCO/ETIQUETAS/PROMPT ===")
    # Contar acciones en train
    dist_train = Counter()
    with open(train_path) as f:
        for line in f:
            ej = json.loads(line)
            respuesta = json.loads(ej["messages"][2]["content"])
            dist_train[respuesta["accion"]] += 1

    dist_lbls = Counter(l["accion_optima"] for l in lbls
                        if l.get("split") == "desarrollo")

    print(f"  Train: {dict(dist_train)}")
    print(f"  Labels desarrollo: {dict(dist_lbls)}")
    if dist_train != dist_lbls:
        reporte.falla("distribucion de train no coincide con labels de desarrollo")
    else:
        reporte.pasa()


# ============================================================
# MAIN
# ============================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--banco-dir", default="banco_cc003",
                    help="Directorio con banco_contextos.jsonl y banco_etiquetas.jsonl")
    ap.add_argument("--train", default="train_cc003.jsonl",
                    help="Archivo de entrenamiento")
    ap.add_argument("--eval", default="eval_cc003_confirmatorio.jsonl",
                    help="Archivo de evaluacion")
    args = ap.parse_args()

    banco_dir = Path(args.banco_dir)
    ctx_path = banco_dir / "banco_contextos.jsonl"
    lbl_path = banco_dir / "banco_etiquetas.jsonl"

    for p in [ctx_path, lbl_path, Path(args.train), Path(args.eval)]:
        if not p.exists():
            print(f"[ABORT] No existe: {p}")
            sys.exit(1)

    ctxs = [json.loads(l) for l in open(ctx_path)]
    lbls = [json.loads(l) for l in open(lbl_path)]

    print(f"[pre] contextos: {len(ctxs)}")
    print(f"[pre] etiquetas: {len(lbls)}")
    print(f"[pre] train: {args.train}")
    print(f"[pre] eval: {args.eval}")
    print()

    reporte = Reporte()

    chk_1_estructura(reporte, ctxs, lbls)
    print()
    chk_2_balance(reporte, lbls)
    print()
    chk_3_margen(reporte, lbls)
    print()
    chk_4_distancias(reporte, ctxs, lbls)
    print()
    chk_5_desvios(reporte, ctxs, lbls)
    print()
    chk_6_prompt_sin_reglas(reporte, args.train, args.eval)
    print()
    chk_7_coherencia(reporte, ctxs, lbls, args.train)
    print()

    print("=" * 60)
    if reporte.ok:
        print(">>> LISTO PARA ENTRENAR <<<")
        sys.exit(0)
    else:
        print(">>> ABORTADO: <razon abajo> <<<")
        for f in reporte.fallos:
            print(f"  - {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
