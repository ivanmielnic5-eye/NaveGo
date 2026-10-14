#!/usr/bin/env python3
"""_gen_nb_eval_A3.py - Genera el notebook de evaluacion de A3."""
import json


def md(t):
    return {"cell_type": "markdown", "metadata": {},
            "source": t.splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": t.splitlines(keepends=True)}


celdas = [
    md("# Timonel Eval - Banco A3 + F-held\n\n"
       "Evalua LLM-A3 con puntaje forzado sobre:\n"
       "- bancoA3: 5 splits (train, val, test_interp, test_extrap, test_balanceado).\n"
       "- F-held: 2 splits (fheld_f1, fheld_f2).\n\n"
       "Comparacion contra baselines:\n"
       "- P-struct: 100% en todo (cota superior).\n"
       "- P-text: 100% en A3, 50% en F-held F2 (no reconoce formulaciones nuevas)."),
    md("## 1. Instalar dependencias"),
    code("""!pip install -q unsloth
!pip install -q --no-deps trl peft accelerate bitsandbytes
!pip install -q datasets"""),

    md("## 2. Cargar modelo + adaptador A3"),
    code("""from unsloth import FastLanguageModel
import torch, glob, os

max_seq_length = 1024

_ads = glob.glob("/kaggle/input/**/adapter_config.json", recursive=True)
_ads = [a for a in _ads if "lora-a3" in a.lower() or "lora_a3" in a.lower() or "A3" in a]
assert _ads, f"No encontre adaptador A3. Encontrados: {glob.glob('/kaggle/input/**/adapter_config.json', recursive=True)}"
ADAPTER_PATH = os.path.dirname(_ads[0])
print(f"ADAPTER_PATH = {ADAPTER_PATH}")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = ADAPTER_PATH,
    max_seq_length = max_seq_length,
    load_in_4bit = True,
)
print("[OK] Modelo + adaptador cargado")"""),
]


celdas += [
    md("## 3. Cargar splits de bancoA3 y F-held"),
    code("""import json
from datasets import load_dataset

def cargar_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]

# bancoA3: buscar los 5 splits
_bancos_a3 = {}
for nombre in ["train", "val", "test_interp", "test_extrap", "test_balanceado"]:
    _cands = glob.glob(f"/kaggle/input/**/{nombre}.jsonl", recursive=True)
    _cands = [c for c in _cands if "sft" not in c]
    if _cands:
        _bancos_a3[nombre] = cargar_jsonl(_cands[0])
        print(f"bancoA3/{nombre}: {len(_bancos_a3[nombre])}")

# F-held: 2 splits
_fheld = {}
for nombre in ["fheld_f1", "fheld_f2"]:
    _cands = glob.glob(f"/kaggle/input/**/{nombre}.jsonl", recursive=True)
    if _cands:
        _fheld[nombre] = cargar_jsonl(_cands[0])
        print(f"{nombre}: {len(_fheld[nombre])}")

print()
print(f"Total bancoA3: {sum(len(v) for v in _bancos_a3.values())}")
print(f"Total F-held:  {sum(len(v) for v in _fheld.values())}")"""),

    md("## 4. Score forzado"),
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

def score(ctx, base=False):
    cm = model.disable_adapter() if base else contextlib.nullcontext()
    with cm:
        lp_t = seq_lp(ctx["prompt"], '{"accion": "terminar"}')
        lp_i = seq_lp(ctx["prompt"], '{"accion": "ir_a"}')
    return lp_t - lp_i"""),
]


celdas += [
    md("## 5. Evaluacion por split (SFT vs BASE)"),
    code("""import numpy as np
from collections import Counter

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k/n; den = 1+z*z/n
    c = (p+z*z/(2*n))/den
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return c-h, c+h

def evaluar_split(nombre, ctxs, base=False):
    if not ctxs:
        return None
    diffs = np.array([score(c, base=base) for c in ctxs])
    pred = np.array(["terminar" if x > 0 else "ir_a" for x in diffs])
    real = np.array([c["label"] for c in ctxs])
    acc = float((pred == real).mean())
    # Balanced accuracy
    t_mask = real == "terminar"
    i_mask = real == "ir_a"
    acc_t = float((pred[t_mask] == real[t_mask]).mean()) if t_mask.any() else 0.0
    acc_i = float((pred[i_mask] == real[i_mask]).mean()) if i_mask.any() else 0.0
    bal = (acc_t + acc_i) / 2.0
    k = int((pred == real).sum())
    n = len(ctxs)
    l, h = wilson(k, n)
    return {
        "nombre": nombre, "n": n, "acc": acc, "bal": bal,
        "acc_term": acc_t, "acc_ir": acc_i,
        "wilson": (l, h),
        "pred_term": int((pred == "terminar").sum()),
        "pred_ir": int((pred == "ir_a").sum()),
    }

def reportar_splits(titulo, splits, base):
    print(f"=== {titulo} ===")
    print(f"  {'split':<18} {'n':>5} {'acc':>7} {'bal':>7} {'term':>7} {'ir_a':>7} {'pred_T':>8} {'pred_I':>8}")
    resultados = {}
    for nombre, ctxs in splits.items():
        r = evaluar_split(nombre, ctxs, base=base)
        if r:
            print(f"  {r['nombre']:<18} {r['n']:>5} {r['acc']:>7.3f} {r['bal']:>7.3f} "
                  f"{r['acc_term']:>7.3f} {r['acc_ir']:>7.3f} "
                  f"{r['pred_term']:>8} {r['pred_ir']:>8}")
            resultados[nombre] = r
    return resultados

res_a3_sft = reportar_splits("bancoA3 SFT", _bancos_a3, base=False)
print()
res_a3_base = reportar_splits("bancoA3 BASE", _bancos_a3, base=True)
print()
res_fheld_sft = reportar_splits("F-held SFT", _fheld, base=False)
print()
res_fheld_base = reportar_splits("F-held BASE", _fheld, base=True)"""),

    md("## 6. Comparacion con baselines (P-text, P-struct)"),
    code("""# Referencia de los baselines (medidos offline en el repo):
# - P-struct: 100% en todos los splits (usa v_max interno).
# - P-text: 100% en bancoA3 (parsea formulaciones de desarrollo),
#           50% en fheld_f2 (no reconoce formulaciones de Perplexity).

BASELINES = {
    "bancoA3/train":          {"pstruct": 1.0, "ptext": 1.0},
    "bancoA3/val":            {"pstruct": 1.0, "ptext": 1.0},
    "bancoA3/test_interp":    {"pstruct": 1.0, "ptext": 1.0},
    "bancoA3/test_extrap":    {"pstruct": 1.0, "ptext": 1.0},
    "bancoA3/test_balanceado":{"pstruct": 1.0, "ptext": 1.0},
    "fheld/fheld_f1":         {"pstruct": 1.0, "ptext": 1.0},
    "fheld/fheld_f2":         {"pstruct": 1.0, "ptext": 0.5},
}

print("=== Resumen: LLM-A3 vs baselines ===")
print(f"  {'split':<24} {'SFT':>7} {'P-text':>7} {'P-struct':>9} {'Δ(SFT-Ptext)':>13}")
all_res = {**res_a3_sft, **res_fheld_sft}
prefix_map = {
    "train": "bancoA3/train", "val": "bancoA3/val",
    "test_interp": "bancoA3/test_interp", "test_extrap": "bancoA3/test_extrap",
    "test_balanceado": "bancoA3/test_balanceado",
    "fheld_f1": "fheld/fheld_f1", "fheld_f2": "fheld/fheld_f2",
}
for nombre, r in all_res.items():
    key = prefix_map.get(nombre, nombre)
    bl = BASELINES.get(key, {})
    ptext = bl.get("ptext", 0.0)
    pstruct = bl.get("pstruct", 0.0)
    delta = r["acc"] - ptext
    print(f"  {key:<24} {r['acc']:>7.3f} {ptext:>7.3f} {pstruct:>9.3f} {delta:>+13.3f}")"""),
]

nb = {"cells": celdas,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python", "version": "3.10"},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 5}

with open("timonel_eval_A3_kaggle.ipynb", "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("[OK] Notebook eval A3 generado")
