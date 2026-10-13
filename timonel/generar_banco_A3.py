#!/usr/bin/env python3
"""generar_banco_A3.py - Banco A3 (Fase 1a, etapa 1).

Diseno en borradores/f0_diseno_v2.md y anexo L del memo 89.

Objetivo: medir si el LLM interpreta contratos y generaliza a
combinaciones (T, v_max) no vistas.

Diferencias con A2:
- Cláusula de velocidad (d<T Y v<=v_max).
- Contra-prior en Q1 (>=40% con v >= 1.0).
- Formulaciones F-train y F-dev (paráfrasis).
- v_max variable en train y test.

Uso:
  python3 generar_banco_A3.py --piloto   (genera 50 contextos)
  python3 generar_banco_A3.py            (genera el banco completo)
"""
import argparse
import hashlib
import json
import random
from collections import Counter
from datetime import datetime
from pathlib import Path

from etiquetar import etiquetar_por_T, etiquetar_por_T_v


# ============================================================
# CONSTANTES
# ============================================================

SEED = 20261014
T_TRAIN = [8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0]
T_INTERP = [11.0, 17.0, 23.0]
T_EXTRAP = [6.0, 32.0]
V_MAX_TRAIN = [0.3, 0.5, 0.8, 1.2, 2.0, 3.0]
V_MAX_INTERP = [0.4, 1.0, 1.6, 2.5]
V_MAX_EXTRAP = [0.15, 5.0]

OUT = "bancoA3"


# ============================================================
# PLANTILLAS DE PROMPT
# ============================================================

SYSTEM = ("Sos el timonel de un velero autonomo. Respondes "
          "UNICAMENTE con el JSON pedido, sin texto adicional.")

# F-train: clausula con "Y la velocidad es menor o igual a X nudos"
CLAUSULA_F_TRAIN = "Y la velocidad es menor o igual a {vmax} nudos"

# F-dev: 3 variantes semanticamente equivalentes
CLAUSULAS_F_DEV = [
    "siempre que la velocidad no supere los {vmax} nudos",
    "y no este navegando a mas de {vmax} nudos",
    "y la velocidad sea como maximo {vmax} nudos",
]

PROMPT_TEMPLATE = """=== PROPOSITO ===
Llevar el barco hasta la meta.
La mision se considera completa cuando la distancia a la meta es
menor que {T} metros {clausula_vel}.

=== ESTADO ACTUAL ===
- Distancia a la meta: {d} metros
- Velocidad: {v} nudos

=== ACCIONES DISPONIBLES ===
- ir_a: seguir navegando hacia la meta.
- terminar: declarar la mision como cumplida.

=== TAREA ===
Elegi la accion que mejor contribuya al proposito.
Responde UNICAMENTE con JSON: {{"accion": "<nombre>"}}"""

# F1: sin clausula de velocidad (solo distancia)
PROMPT_F1_TEMPLATE = """=== PROPOSITO ===
Llevar el barco hasta la meta.
La mision se considera completa cuando la distancia a la meta es
menor que {T} metros.

=== ESTADO ACTUAL ===
- Distancia a la meta: {d} metros
- Velocidad: {v} nudos

=== ACCIONES DISPONIBLES ===
- ir_a: seguir navegando hacia la meta.
- terminar: declarar la mision como cumplida.

=== TAREA ===
Elegi la accion que mejor contribuya al proposito.
Responde UNICAMENTE con JSON: {{"accion": "<nombre>"}}"""


# ============================================================
# UTILIDADES
# ============================================================

def fmt1(x):
    """Formatea con 1 decimal."""
    return f"{x:.1f}"


def fmt2(x):
    """Formatea con 2 decimales (para v)."""
    return f"{x:.2f}"


def _elegir_clausula(rng, formulacion):
    """Devuelve la clausula de velocidad segun formulacion."""
    if formulacion == "F_train":
        return CLAUSULA_F_TRAIN
    # F_dev: elegir una de las 3 variantes
    return rng.choice(CLAUSULAS_F_DEV)


def _armar_prompt_F1(T, d, v, formulacion, rng):
    """F1: solo distancia."""
    return PROMPT_F1_TEMPLATE.format(T=fmt1(T), d=fmt1(d), v=fmt2(v))


def _armar_prompt_F2(T, d, v, v_max, formulacion, rng):
    """F2: distancia + velocidad."""
    clausula = _elegir_clausula(rng, formulacion)
    clausula_final = clausula.format(vmax=fmt1(v_max))
    return PROMPT_TEMPLATE.format(
        T=fmt1(T), d=fmt1(d), v=fmt2(v),
        clausula_vel=clausula_final,
    )


def _asignar_formulacion(rng):
    """60% F_train, 40% F_dev."""
    return "F_train" if rng.random() < 0.60 else "F_dev"


# ============================================================
# GENERADOR F1 (solo distancia)
# ============================================================

def generar_F1(rng, T, n_por_lado):
    """Genera n_por_lado con d<T (terminar) y n_por_lado con d>=T (ir_a)."""
    ctxs = []
    # Lado terminar: d < T
    for _ in range(n_por_lado):
        d = round(float(rng.uniform(1.0, T - 0.5)), 1)
        v = round(float(rng.uniform(0.0, 3.0)), 2)
        formulacion = _asignar_formulacion(rng)
        label = etiquetar_por_T(d, T)
        prompt = _armar_prompt_F1(T, d, v, formulacion, rng)
        ctxs.append({
            "familia": "F1",
            "cuadrante": "Q1" if d < T else "Q3",
            "formulacion": formulacion,
            "T": T, "d": d, "v": v, "v_max": None,
            "label": label, "prompt": prompt,
        })
    # Lado ir_a: d >= T
    for _ in range(n_por_lado):
        d = round(float(rng.uniform(T + 0.5, T + 8.0)), 1)
        v = round(float(rng.uniform(0.0, 3.0)), 2)
        formulacion = _asignar_formulacion(rng)
        label = etiquetar_por_T(d, T)
        prompt = _armar_prompt_F1(T, d, v, formulacion, rng)
        ctxs.append({
            "familia": "F1",
            "cuadrante": "Q3",
            "formulacion": formulacion,
            "T": T, "d": d, "v": v, "v_max": None,
            "label": label, "prompt": prompt,
        })
    return ctxs


# ============================================================
# GENERADOR F2 (distancia + velocidad)
# ============================================================

def _generar_F2_cuadrante(rng, T, v_max, cuadrante, n, contra_prior=False):
    """Genera n contextos de F2 en un cuadrante dado.

    Q1: d<T y v<=v_max  -> terminar
    Q2: d<T y v>v_max   -> ir_a
    Q3: d>=T y v<=v_max -> ir_a
    Q4: d>=T y v>v_max  -> ir_a

    contra_prior=True (solo Q1): fuerza v >= 1.0 y v <= v_max.
    """
    ctxs = []
    for _ in range(n):
        if cuadrante == "Q1":
            d = round(float(rng.uniform(1.0, T - 0.5)), 1)
            if contra_prior:
                # v en la parte alta del rango permitido (relativo a v_max)
                v = round(float(rng.uniform(0.7 * v_max, v_max)), 2)
            else:
                v = round(float(rng.uniform(0.0, v_max)), 2)
        elif cuadrante == "Q2":
            d = round(float(rng.uniform(1.0, T - 0.5)), 1)
            v = round(float(rng.uniform(v_max + 0.1, v_max + 2.0)), 2)
        elif cuadrante == "Q3":
            d = round(float(rng.uniform(T + 0.5, T + 8.0)), 1)
            v = round(float(rng.uniform(0.0, v_max)), 2)
        else:  # Q4
            d = round(float(rng.uniform(T + 0.5, T + 8.0)), 1)
            v = round(float(rng.uniform(v_max + 0.1, v_max + 2.0)), 2)

        formulacion = _asignar_formulacion(rng)
        label = etiquetar_por_T_v(d, T, v, v_max)
        prompt = _armar_prompt_F2(T, d, v, v_max, formulacion, rng)
        ctxs.append({
            "familia": "F2",
            "cuadrante": cuadrante,
            "contra_prior": bool(contra_prior),
            "formulacion": formulacion,
            "T": T, "d": d, "v": v, "v_max": v_max,
            "label": label, "prompt": prompt,
        })
    return ctxs


def generar_F2(rng, T, v_max, n_por_cuadrante, contra_prior_Q1=0.4):
    """Genera F2 para un (T, v_max) con 4 cuadrantes.

    contra_prior_Q1: fraccion de Q1 que sera contra-prior.
    """
    n_cp = int(round(n_por_cuadrante * contra_prior_Q1))
    n_normal = n_por_cuadrante - n_cp

    ctxs = []
    ctxs += _generar_F2_cuadrante(rng, T, v_max, "Q1", n_normal, contra_prior=False)
    ctxs += _generar_F2_cuadrante(rng, T, v_max, "Q1", n_cp, contra_prior=True)
    ctxs += _generar_F2_cuadrante(rng, T, v_max, "Q2", n_por_cuadrante)
    ctxs += _generar_F2_cuadrante(rng, T, v_max, "Q3", n_por_cuadrante)
    ctxs += _generar_F2_cuadrante(rng, T, v_max, "Q4", n_por_cuadrante)
    return ctxs


# ============================================================
# VERIFICACION DE ETIQUETAS
# ============================================================



def verificar_etiquetas(ctxs):
    """Verifica que cada label coincida con etiquetar."""
    errores = []
    for i, c in enumerate(ctxs):
        if c["familia"] == "F1":
            esperada = etiquetar_por_T(c["d"], c["T"])
        else:
            esperada = etiquetar_por_T_v(c["d"], c["T"], c["v"], c["v_max"])
        if esperada != c["label"]:
            errores.append((i, c, esperada))
    return errores


def verificar_contra_prior(ctxs):
    """Verifica que los Q1 contra_prior cumplan v >= 1.0 y v <= v_max."""
    errores = []
    for i, c in enumerate(ctxs):
        if not c.get("contra_prior"):
            continue
        if c["d"] >= c["T"]:
            errores.append((i, "contra_prior con d>=T", c))
        if c["v"] < 0.7 * c["v_max"]:
            errores.append((i, "contra_prior con v < 0.7*v_max", c))
        if c["v"] > c["v_max"]:
            errores.append((i, "contra_prior con v>v_max", c))
    return errores


def generar_piloto(rng):
    """50 contextos para verificar el generador."""
    ctxs = []
    ctxs += generar_F1(rng, 15.0, 5)
    ctxs += generar_F2(rng, 15.0, 1.2, 8, contra_prior_Q1=0.4)
    rng.shuffle(ctxs)
    return ctxs


def generar_train(rng):
    """Train: 1200 (F1: 400, F2: 800)."""
    ctxs = []
    for T in T_TRAIN:
        ctxs += generar_F1(rng, T, 18)
    for T in T_TRAIN:
        for v_max in V_MAX_TRAIN:
            ctxs += generar_F2(rng, T, v_max, 3, contra_prior_Q1=0.4)
    return ctxs


def generar_val(rng):
    """Val: 300, misma composicion que train."""
    ctxs = []
    for T in T_TRAIN:
        ctxs += generar_F1(rng, T, 4)
    for T in T_TRAIN:
        for v_max in V_MAX_TRAIN:
            ctxs += generar_F2(rng, T, v_max, 1, contra_prior_Q1=0.4)
    return ctxs


def generar_test_interp(rng):
    """Test interp: 600 sobre T_INTERP y V_MAX_INTERP."""
    ctxs = []
    for T in T_INTERP:
        ctxs += generar_F1(rng, T, 20)
        for v_max in V_MAX_INTERP:
            ctxs += generar_F2(rng, T, v_max, 10, contra_prior_Q1=0.4)
    return ctxs


def generar_test_extrap(rng):
    """Test extrap: 400 sobre T_EXTRAP y V_MAX_EXTRAP."""
    ctxs = []
    for T in T_EXTRAP:
        ctxs += generar_F1(rng, T, 20)
        for v_max in V_MAX_EXTRAP:
            ctxs += generar_F2(rng, T, v_max, 20, contra_prior_Q1=0.4)
    return ctxs


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def escribir_split(path, ctxs):
    with open(path, "w", encoding="utf-8") as f:
        for c in ctxs:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")


def reportar(nombre, ctxs):
    print(f"  {nombre}: {len(ctxs)} ejemplos")
    labels = Counter(c["label"] for c in ctxs)
    print(f"    labels: {dict(labels)}")
    fams = Counter(c["familia"] for c in ctxs)
    print(f"    familias: {dict(fams)}")
    forms = Counter(c["formulacion"] for c in ctxs)
    print(f"    formulaciones: {dict(forms)}")
    cp = sum(1 for c in ctxs if c.get("contra_prior"))
    print(f"    contra_prior: {cp}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piloto", action="store_true")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    rng = random.Random(SEED)
    out = Path(args.out)
    out.mkdir(exist_ok=True)

    if args.piloto:
        print("[PILOTO] Generando 50 contextos...")
        ctxs = generar_piloto(rng)
        errs = verificar_etiquetas(ctxs)
        errs_cp = verificar_contra_prior(ctxs)
        print(f"  Generados: {len(ctxs)}")
        print(f"  Errores de etiqueta: {len(errs)}")
        print(f"  Errores de contra_prior: {len(errs_cp)}")
        for e in errs[:3]:
            print(f"    err: {e}")
        for e in errs_cp[:3]:
            print(f"    err_cp: {e}")
        print()
        reportar("piloto", ctxs)
        if errs or errs_cp:
            print()
            print("PILOTO FALLO")
            return 1
        print()
        print("PILOTO OK")
        return 0

    print("[A3] Generando splits...")
    splits = {
        "train": generar_train(rng),
        "val": generar_val(rng),
        "test_interp": generar_test_interp(rng),
        "test_extrap": generar_test_extrap(rng),
        "test_balanceado": generar_test_balanceado(rng),
    }

    for nombre, ctxs in splits.items():
        errs = verificar_etiquetas(ctxs)
        errs_cp = verificar_contra_prior(ctxs)
        if errs or errs_cp:
            print(f"FALLO en {nombre}: {len(errs)} etiqueta, {len(errs_cp)} contra_prior")
            for e in (errs + errs_cp)[:5]:
                print(f"  {e}")
            return 1

    manifest = {
        "fecha": datetime.now().isoformat(),
        "seed": SEED,
        "T_train": T_TRAIN,
        "T_interp": T_INTERP,
        "T_extrap": T_EXTRAP,
        "V_MAX_TRAIN": V_MAX_TRAIN,
        "V_MAX_INTERP": V_MAX_INTERP,
        "V_MAX_EXTRAP": V_MAX_EXTRAP,
        "files": {},
    }
    print()
    for nombre, ctxs in splits.items():
        path = out / f"{nombre}.jsonl"
        escribir_split(path, ctxs)
        manifest["files"][nombre] = {"n": len(ctxs), "sha256": _sha256_file(path)}
        reportar(nombre, ctxs)

    with open(out / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print()
    print(f"[A3] archivos en {out}/")
    return 0





def generar_test_balanceado(rng):
    """Test balanceado 50/50 (opcion D de Luna).

    Misma distribucion de (T, v_max) que test_interp, pero forzando
    50% terminar y 50% ir_a. Mide balanced accuracy sin ventaja por
    prevalencia.
    """
    ctxs = []
    # Para cada (T, v_max), 25 terminar (Q1) y 25 ir_a (Q2).
    # Total: 3 T * 4 v_max * 50 = 600.
    for T in T_INTERP:
        for v_max in V_MAX_INTERP:
            # 25 Q1 (terminar): d<T, v<=v_max
            ctxs += _generar_F2_cuadrante(rng, T, v_max, "Q1", 25, contra_prior=True)
            # 25 Q2 (ir_a): d<T, v>v_max
            ctxs += _generar_F2_cuadrante(rng, T, v_max, "Q2", 25, contra_prior=False)
    rng.shuffle(ctxs)
    return ctxs


if __name__ == "__main__":
    import sys
    sys.exit(main())
