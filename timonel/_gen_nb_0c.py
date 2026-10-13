#!/usr/bin/env python3
"""_gen_nb_0c.py - Genera el notebook del paso 0c.

Desglose de errores de B2, invariancia al orden invertido, y
guardado de diffs crudos para analisis posterior.
"""
import json


def md(t):
    return {"cell_type": "markdown", "metadata": {},
            "source": t.splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": t.splitlines(keepends=True)}


celdas = [
    md("# Timonel Paso 0c - Diagnostico de 0b\n\n"
       "Desglose de errores de B2, invariancia al orden, diffs crudos."),
    md("## 1. Instalar dependencias"),
    code("""!pip install -q unsloth
!pip install -q --no-deps trl peft accelerate bitsandbytes
!pip install -q datasets"""),
]

celdas += [
    md("## 2. Cargar modelo + adaptador A2"),
    code("""from unsloth import FastLanguageModel
import torch, glob, os

max_seq_length = 1024
_ads = glob.glob("/kaggle/input/**/adapter_config.json", recursive=True)
_ads = [a for a in _ads if "lora-a2" in a.lower() or "banco_A2" in a]
assert _ads, "No encontre adaptador A2"
ADAPTER_PATH = os.path.dirname(_ads[0])
print(f"ADAPTER_PATH = {ADAPTER_PATH}")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = ADAPTER_PATH,
    max_seq_length = max_seq_length,
    load_in_4bit = True,
)
print("[OK] Modelo + adaptador cargado")"""),

    md("## 3. Cargar banco 0b"),
    code("""import json
from collections import Counter
_ps = glob.glob("/kaggle/input/**/probe_0b.jsonl", recursive=True)
assert _ps, "No encontre probe_0b.jsonl"
PROBE_PATH = _ps[0]
probe = [json.loads(l) for l in open(PROBE_PATH)]
print(f"probe_0b: {len(probe)} contextos")
print(Counter(c["bloque"] for c in probe))"""),
]

celdas += [
    md("## 4. Score forzado con y sin orden invertido"),
    code("""import contextlib
from unsloth import FastLanguageModel
FastLanguageModel.for_inference(model)

SYSTEM = ("Sos el timonel de un velero autonomo. Respondes "
          "UNICAMENTE con el JSON pedido, sin texto adicional.")

@torch.no_grad()
def seq_lp(prompt, completion):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    p = tokenizer(text, add_special_tokens=False, return_tensors="pt").input_ids
    c = tokenizer(completion, add_special_tokens=False, return_tensors="pt").input_ids
    ids = torch.cat([p, c], dim=1).to(model.device)
    logits = model(ids).logits[0, p.shape[1]-1:-1].float()
    lp = torch.log_softmax(logits, dim=-1)
    return float(lp.gather(1, ids[0, p.shape[1]:].unsqueeze(1)).sum())

def score_normal(ctx):
    return seq_lp(ctx["prompt"], '{"accion": "terminar"}') - seq_lp(ctx["prompt"], '{"accion": "ir_a"}')

# Para invertir el orden: modificamos el prompt intercambiando las dos lineas de ACCIONES.
import re
def invertir_prompt(prompt):
    lineas = prompt.split("\\n")
    idx = [i for i, l in enumerate(lineas) if l.strip().startswith("- ir_a:") or l.strip().startswith("- terminar:")]
    if len(idx) == 2:
        lineas[idx[0]], lineas[idx[1]] = lineas[idx[1]], lineas[idx[0]]
    return "\\n".join(lineas)

def score_invertido(ctx):
    p = invertir_prompt(ctx["prompt"])
    return seq_lp(p, '{"accion": "terminar"}') - seq_lp(p, '{"accion": "ir_a"}')

print("[OK] Funciones listas")"""),
]

celdas += [
    md("## 5. Evaluacion: orden normal, invertido, invariancia"),
    code("""import numpy as np

# Orden normal
diffs_normal = np.array([score_normal(c) for c in probe])
pred_normal = np.array(["terminar" if x > 0 else "ir_a" for x in diffs_normal])
real = np.array([c["label"] for c in probe])

# Orden invertido
diffs_inv = np.array([score_invertido(c) for c in probe])
pred_inv = np.array(["terminar" if x > 0 else "ir_a" for x in diffs_inv])

# Invariancia
identicos = (pred_normal == pred_inv)
print(f"Invariancia al orden: {identicos.sum()}/{len(probe)} = {identicos.mean():.3f}")
print()

# Guardar diffs crudos
with open("/kaggle/working/0c_diffs.jsonl", "w") as f:
    for i, c in enumerate(probe):
        row = dict(c)
        row["diff_normal"] = float(diffs_normal[i])
        row["diff_invertido"] = float(diffs_inv[i])
        row["pred_normal"] = str(pred_normal[i])
        row["pred_invertido"] = str(pred_inv[i])
        row["identico"] = bool(identicos[i])
        row["acierto"] = bool(pred_normal[i] == real[i])
        f.write(json.dumps(row) + "\\n")
print("[OK] diffs guardados en 0c_diffs.jsonl")"""),
]

celdas += [
    md("## 6. Desglose de errores de B2 por margen |v - v_max|"),
    code("""# Solo bloque B2, con v_max definido
ix_b2 = [i for i, c in enumerate(probe) if c["bloque"] == "B2_vmax_var"]
print(f"B2 total: {len(ix_b2)}")
print()

print("=== Errores de B2 por margen |v - v_max| ===")
buckets = [(0, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 0.5), (0.5, 99)]
for lo, hi in buckets:
    ix = [i for i in ix_b2 if lo <= abs(probe[i]["v"] - probe[i]["v_max"]) < hi]
    if not ix:
        continue
    aciertos = sum(1 for i in ix if pred_normal[i] == real[i])
    print(f"  |v-vmax| en [{lo}, {hi}): n={len(ix)} acc={aciertos/len(ix):.3f}")

print()
print("=== Errores de B2 contra-prior por margen ===")
ix_cp = [i for i in ix_b2 if probe[i]["sub"] == "contra_prior"]
print(f"contra-prior total: {len(ix_cp)}")
for lo, hi in buckets:
    ix = [i for i in ix_cp if lo <= abs(probe[i]["v"] - probe[i]["v_max"]) < hi]
    if not ix:
        continue
    aciertos = sum(1 for i in ix if pred_normal[i] == real[i])
    print(f"  |v-vmax| en [{lo}, {hi}): n={len(ix)} acc={aciertos/len(ix):.3f}")

print()
print("=== B2 contra-prior: errores con margen grande (>=0.2) ===")
ix_err = [i for i in ix_cp if abs(probe[i]["v"] - probe[i]["v_max"]) >= 0.2 and pred_normal[i] != real[i]]
for i in ix_err[:10]:
    c = probe[i]
    print(f"  d={c['d']} T={c['T']} v={c['v']} v_max={c['v_max']} real={c['label']} pred={pred_normal[i]}")"""),
]

celdas += [
    md("## 7. Veredicto 0c"),
    code("""# Resumen
print("=== Resumen 0c ===")
print(f"Invariancia al orden: {identicos.sum()}/{len(probe)} = {identicos.mean():.3f}")

# B2 global
ix_b2_all = [i for i in ix_b2]
acc_b2 = np.mean([pred_normal[i] == real[i] for i in ix_b2_all])
print(f"B2 SFT (orden normal): acc={acc_b2:.3f}")

# B2 contra-prior
acc_cp = np.mean([pred_normal[i] == real[i] for i in ix_cp])
print(f"B2 contra-prior: acc={acc_cp:.3f} (n={len(ix_cp)})")

# Margen de errores
err_cp = [i for i in ix_cp if pred_normal[i] != real[i]]
if err_cp:
    margenes = [abs(probe[i]["v"] - probe[i]["v_max"]) for i in err_cp]
    print(f"Errores contra-prior: {len(err_cp)}")
    print(f"  margenes |v-vmax|: min={min(margenes):.2f} max={max(margenes):.2f} media={sum(margenes)/len(margenes):.2f}")
    print(f"  errores con margen < 0.1: {sum(1 for m in margenes if m < 0.1)}")
    print(f"  errores con margen >= 0.1: {sum(1 for m in margenes if m >= 0.1)}")
else:
    print("Sin errores en contra-prior")

print()
if len(err_cp) > 0 and sum(1 for m in margenes if m >= 0.1) > len(err_cp) / 2:
    v = "SESGO con margen grande: el modelo falla lejos del limite, no solo en frontera"
elif len(err_cp) > 0:
    v = "FRONTERA: los errores se concentran cerca del margen (|v-vmax| chico)"
else:
    v = "SIN ERRORES en contra-prior"
print(f"VEREDICTO 0c: {v}")"""),
]

nb = {"cells": celdas,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python", "version": "3.10"},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 5}

with open("timonel_0c_kaggle.ipynb", "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("[OK] Notebook 0c generado")
