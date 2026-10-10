#!/usr/bin/env python3
import json
from collections import Counter

UMBRAL = 2.0
ACCIONES = ["corregir_rumbo", "ir_a_punto", "frenar", "terminar"]
SPLITS = ["desarrollo", "confirmatorio"]

ctxs = [json.loads(l) for l in open("banco_cc002/banco_contextos.jsonl")]
lbls = [json.loads(l) for l in open("banco_cc002/banco_etiquetas.jsonl")]

print("=== CHK 1: INTEGRIDAD ===")
campos_state = {"pos_x", "pos_z", "hdg", "sog", "meta_x", "meta_z", "viento_kn", "viento_dir"}
errores = 0
for c in ctxs:
    if set(c["state"].keys()) != campos_state:
        errores += 1
print("  contextos con esquema incorrecto:", errores)

print("\n=== CHK 3: COBERTURA ===")
for s in SPLITS:
    por_acc = Counter(l["accion_optima"] for l in lbls if l["split"] == s)
    faltan = [a for a in ACCIONES if por_acc.get(a, 0) == 0]
    print(f"  {s}: {dict(por_acc)}")
    if faltan:
        print(f"    FALTAN: {faltan}")

print("\n=== CHK 4: UNICIDAD ===")
violaciones = [l for l in lbls if l["margen_vs_segunda"] is not None and l["margen_vs_segunda"] < UMBRAL]
print(f"  labels con margen < {UMBRAL}: {len(violaciones)}")

print("\n=== CHK 5: DUPLICADOS ===")
hashes = [c["state_hash"] for c in ctxs]
dups = [h for h, n in Counter(hashes).items() if n > 1]
print(f"  state_hashes duplicados: {len(dups)}")


print("\n=== CHK 7: LEAKAGE ===")
# Chequear que los contextos visibles al LLM no contengan la respuesta
import sys
sys.path.insert(0, ".")
from agente_llm import armar_prompt
leaks = 0
ejemplos_leak = []
for i in range(min(5, len(ctxs))):
    c = ctxs[i]
    st = c["state"]
    p = armar_prompt(
        meta_x=st["meta_x"], meta_z=st["meta_z"],
        pos_x=st["pos_x"], pos_z=st["pos_z"],
        hdg=st["hdg"], sog=st["sog"],
        dist=0.0, rumbo_hacia_meta=0.0,
        viento_kn=st["viento_kn"], viento_dir=st["viento_dir"],
    )
    label = next(l for l in lbls if l["context_id"] == c["context_id"])
    accion = label["accion_optima"]
    # Buscar la accion en el prompt de forma que revele la respuesta
    if "Elegi " + accion in p or "deberias " + accion in p.lower():
        leaks += 1
        ejemplos_leak.append(c["context_id"])
print(f"  prompts con leakage explicito: {leaks}/5 muestreados")

print("\n=== CHK 10: BALANCE POR FAMILIA ===")
for s in SPLITS:
    fam = Counter(l["familia"] for l in lbls if l["split"] == s)
    print(f"  {s}: {dict(fam)}")

print("\n=== RESUMEN ===")
print(f"  total contextos: {len(ctxs)}")
print(f"  total labels: {len(lbls)}")
ids_ctx = set(c["context_id"] for c in ctxs)
ids_lbl = set(l["context_id"] for l in lbls)
print(f"  context_id en ctxs pero no en labels: {len(ids_ctx - ids_lbl)}")
print(f"  context_id en labels pero no en ctxs: {len(ids_lbl - ids_ctx)}")
