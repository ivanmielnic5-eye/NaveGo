#!/usr/bin/env python3
"""generar_fheld.py - Genera F-held desde el bruto de Perplexity.

F-held: formulaciones retenidas que ni P-text ni el LLM-A3 vieron
durante su desarrollo.

Estructura:
- F2: 300 items (60 formulaciones x 5). Balance 150/150.
- F1: 300 items (6 T nuevos x 50). Balance 150/150.
- Total: 600 items.

Autor de la generacion bruta: Perplexity, sesion aislada.
Consigna SHA256: 6ca5b526245f0d66e58edaa2bdd6d231e5949adeeb9da2a4e2d7e1574c128ab2
Bruto SHA256: 5b6d7171d9617de7d4a0dc32ff113dfb3a8bbae2eae06168d24ebe8bf2693471

Referencia: fheld_consigna.md, luna_criterio_contaminacion.md.
"""
import hashlib
import json
import random
from collections import Counter
from datetime import datetime
from pathlib import Path

from etiquetar import etiquetar_por_T, etiquetar_por_T_v

SEED = 20261014
OUT = "fheld"

# T y v_max no vistos por el modelo
T_F1_NUEVOS = [9.0, 13.0, 19.0, 21.0, 25.0, 27.0]
T_F2_INTERP = [11.0, 17.0, 23.0]
V_MAX_F2_INTERP = [0.4, 1.0, 1.6, 2.5]

# Item por formulacion (F2) y por T (F1)
N_POR_FORMULACION = 5
N_POR_T_F1 = 50

# Prompt base (F1, sin clausula de velocidad)
PROMPT_F1 = """=== PROPOSITO ===
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

# Prompt F2 con clausula insertada
PROMPT_F2 = """=== PROPOSITO ===
Llevar el barco hasta la meta.
La mision se considera completa cuando la distancia a la meta es
menor que {T} metros {clausula}.

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
# CARGA DEL BRUTO
# ============================================================

def cargar_formulaciones(path="fheld_generado_bruto.txt"):
    """Lee las 61 lineas del bruto y devuelve las 60 primeras."""
    with open(path, encoding="utf-8") as f:
        lineas = [l.strip() for l in f if l.strip()]
    if len(lineas) > 60:
        lineas = lineas[:60]
    return lineas


def fmt1(x):
    return f"{x:.1f}"


def fmt2(x):
    return f"{x:.2f}"


# ============================================================
# GENERADOR F2 (300 items)
# ============================================================

def generar_F2(rng, formulaciones):
    """300 items: 60 formulaciones x 5.

    Cada formulacion se usa 5 veces, alternando entre terminar e ir_a
    para balancear. T y v_max se sortean de T_F2_INTERP/V_MAX_F2_INTERP.
    """
    ctxs = []
    for idx_form, formulacion in enumerate(formulaciones):
        base_terminar = (idx_form % 2 == 0)
        for k in range(N_POR_FORMULACION):
            T = rng.choice(T_F2_INTERP)
            v_max = rng.choice(V_MAX_F2_INTERP)

            es_terminar = (k % 2 == 0) == base_terminar
            if es_terminar:
                d = round(float(rng.uniform(1.0, T - 0.5)), 1)
                v = round(float(rng.uniform(0.0, v_max)), 2)
            else:
                d = round(float(rng.uniform(1.0, T - 0.5)), 1)
                v = round(float(rng.uniform(v_max + 0.1, v_max + 2.0)), 2)

            label = etiquetar_por_T_v(d, T, v, v_max)
            clausula = formulacion.replace("{vmax}", fmt1(v_max))
            prompt = PROMPT_F2.format(
                T=fmt1(T), d=fmt1(d), v=fmt2(v), clausula=clausula,
            )
            ctxs.append({
                "familia": "F2",
                "formulacion_id": formulaciones.index(formulacion),
                "T": T, "d": d, "v": v, "v_max": v_max,
                "label": label, "prompt": prompt,
            })
    rng.shuffle(ctxs)
    return ctxs


# ============================================================
# GENERADOR F1 (300 items)
# ============================================================

def generar_F1(rng):
    """300 items: 6 T nuevos x 50 (25 terminar, 25 ir_a)."""
    ctxs = []
    for T in T_F1_NUEVOS:
        for _ in range(25):
            d = round(float(rng.uniform(1.0, T - 0.5)), 1)
            v = round(float(rng.uniform(0.0, 3.0)), 2)
            label = etiquetar_por_T(d, T)
            prompt = PROMPT_F1.format(T=fmt1(T), d=fmt1(d), v=fmt2(v))
            ctxs.append({
                "familia": "F1",
                "T": T, "d": d, "v": v, "v_max": None,
                "label": label, "prompt": prompt,
            })
        for _ in range(25):
            d = round(float(rng.uniform(T + 0.5, T + 8.0)), 1)
            v = round(float(rng.uniform(0.0, 3.0)), 2)
            label = etiquetar_por_T(d, T)
            prompt = PROMPT_F1.format(T=fmt1(T), d=fmt1(d), v=fmt2(v))
            ctxs.append({
                "familia": "F1",
                "T": T, "d": d, "v": v, "v_max": None,
                "label": label, "prompt": prompt,
            })
    rng.shuffle(ctxs)
    return ctxs


# ============================================================
# VERIFICACION Y ESCRITURA
# ============================================================

def verificar_etiquetas(ctxs):
    errores = []
    for i, c in enumerate(ctxs):
        if c["familia"] == "F1":
            esperada = etiquetar_por_T(c["d"], c["T"])
        else:
            esperada = etiquetar_por_T_v(c["d"], c["T"], c["v"], c["v_max"])
        if esperada != c["label"]:
            errores.append((i, c, esperada))
    return errores


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def escribir_jsonl(path, ctxs):
    with open(path, "w", encoding="utf-8") as f:
        for c in ctxs:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")


def reportar(nombre, ctxs):
    print(f"  {nombre}: {len(ctxs)}")
    print(f"    labels: {dict(Counter(c['label'] for c in ctxs))}")
    print(f"    familias: {dict(Counter(c['familia'] for c in ctxs))}")


def main():
    rng = random.Random(SEED)
    out = Path(OUT)
    out.mkdir(exist_ok=True)

    print("[F-held] Cargando formulaciones del bruto...")
    formulaciones = cargar_formulaciones()
    print(f"  Formulaciones: {len(formulaciones)}")
    if len(formulaciones) != 60:
        print(f"FALLO: se esperaban 60, hay {len(formulaciones)}")
        return 1

    print("[F-held] Generando F2...")
    f2 = generar_F2(rng, formulaciones)

    print("[F-held] Generando F1...")
    f1 = generar_F1(rng)

    # Verificar
    for nombre, ctxs in [("F2", f2), ("F1", f1)]:
        errs = verificar_etiquetas(ctxs)
        if errs:
            print(f"FALLO en {nombre}: {len(errs)} errores")
            for e in errs[:3]:
                print(f"  {e}")
            return 1

    # Escribir
    manifest = {
        "fecha": datetime.now().isoformat(),
        "seed": SEED,
        "autor_bruto": "Perplexity (sesion aislada)",
        "consigna_sha256": "6ca5b526245f0d66e58edaa2bdd6d231e5949adeeb9da2a4e2d7e1574c128ab2",
        "bruto_sha256": "5b6d7171d9617de7d4a0dc32ff113dfb3a8bbae2eae06168d24ebe8bf2693471",
        "T_F1_NUEVOS": T_F1_NUEVOS,
        "T_F2_INTERP": T_F2_INTERP,
        "V_MAX_F2_INTERP": V_MAX_F2_INTERP,
        "formulaciones_n": len(formulaciones),
        "files": {},
    }

    for nombre, ctxs in [("fheld_f2", f2), ("fheld_f1", f1)]:
        path = out / f"{nombre}.jsonl"
        escribir_jsonl(path, ctxs)
        manifest["files"][nombre] = {
            "n": len(ctxs),
            "sha256": _sha256_file(path),
        }
        reportar(nombre, ctxs)

    with open(out / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print()
    print(f"[F-held] archivos en {out}/")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
