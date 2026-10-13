#!/usr/bin/env python3
"""Genera el notebook probe F2 v2: compara SFT vs BASE sobre el mismo banco.

Si el base sin adaptador tambien saca >=0.95 en Q2, el SFT no aporta.
Si el base falla, el SFT si aporta.
"""
import json


def md(t):
    return {"cell_type": "markdown", "metadata": {},
            "source": t.splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": t.splitlines(keepends=True)}


celdas = [
    md("# Timonel Probe F2 v2 - SFT vs BASE\n\n"
       "Prueba si el adaptador de A2 lee el contrato F2 mejor que el\n"
       "Llama 3.1 8B base sin entrenar.\n\n"
       "Cuadrante clave: Q2 (d<T, v>v_max), etiqueta correcta = ir_a."),
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
assert _ads, f"No encontre adapter. Encontrados: {glob.glob('/kaggle/input/**/adapter_config.json', recursive=True)}"
ADAPTER_PATH = os.path.dirname(_ads[0])
print(f"ADAPTER_PATH = {ADAPTER_PATH}")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = ADAPTER_PATH,
    max_seq_length = max_seq_length,
    load_in_4bit = True,
)
print("[OK] Modelo + adaptador cargado")"""),

    md("## 3. Cargar banco probe"),
    code("""import json
from collections import Counter
_ps = glob.glob("/kaggle/input/**/probe.jsonl", recursive=True)
assert _ps, "No encontre probe.jsonl"
PROBE_PATH = _ps[0]
probe = [json.loads(l) for l in open(PROBE_PATH)]
print(f"probe: {len(probe)} contextos")
print(Counter(c["cuadrante"] for c in probe))"""),

    md("## 4. Score forzado (con y sin adaptador)"),
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
    md("## 5. Evaluacion SFT vs BASE por cuadrante"),
    code("""import numpy as np

def wilson(k, n, z=1.96):
    p = k/n; den = 1+z*z/n
    c = (p+z*z/(2*n))/den
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return c-h, c+h

def evaluar(base):
    name = "BASE (sin adaptador)" if base else "SFT (con adaptador A2)"
    diff = np.array([score(c, base=base) for c in probe])
    pred = np.array(["terminar" if x > 0 else "ir_a" for x in diff])
    real = np.array([c["label"] for c in probe])
    cuad = np.array([c["cuadrante"] for c in probe])
    print(f"=== {name} ===")
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        ix = cuad == q
        k = int((pred[ix] == real[ix]).sum())
        n = int(ix.sum())
        l, h = wilson(k, n)
        pt = int((pred[ix] == "terminar").sum())
        print(f"  {q}: n={n} acc={k/n:.3f} IC95=[{l:.3f},{h:.3f}]  pred_terminar={pt}/{n}")
    k = int((pred == real).sum())
    l, h = wilson(k, len(pred))
    print(f"  GLOBAL: {k}/{len(pred)} = {k/len(pred):.3f} IC95=[{l:.3f},{h:.3f}]")
    return pred, real, cuad

pred_sft, real, cuad = evaluar(base=False)
print()
pred_base, _, _ = evaluar(base=True)"""),

    md("## 6. Veredicto del probe"),
    code("""q2 = cuad == "Q2"

acc_sft_q2 = (pred_sft[q2] == real[q2]).mean()
acc_base_q2 = (pred_base[q2] == real[q2]).mean()
acc_sft_glob = (pred_sft == real).mean()
acc_base_glob = (pred_base == real).mean()

print(f"Q2 SFT : {acc_sft_q2:.3f}")
print(f"Q2 BASE: {acc_base_q2:.3f}")
print(f"GLOBAL SFT : {acc_sft_glob:.3f}")
print(f"GLOBAL BASE: {acc_base_glob:.3f}")
print()

if acc_base_q2 >= 0.95 and abs(acc_sft_q2 - acc_base_q2) < 0.03:
    v = "BASE YA LEE EL CONTRATO. El SFT no aporta en F2."
elif acc_sft_q2 >= 0.95 and acc_base_q2 < 0.80:
    v = "SFT APORTA: lee contrato F2 donde el base falla."
elif acc_sft_q2 >= 0.95:
    v = "SFT LEE EL CONTRATO, pero la base tambien responde bien. Diferencia poco clara."
else:
    v = "INCONCLUSO. Revisar por cuadrante."

print(f"VEREDICTO PROBE v2: {v}")"""),
]

nb = {"cells": celdas,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python", "version": "3.10"},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 5}

with open("timonel_probe_A2_v2_kaggle.ipynb", "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("[OK] Notebook probe v2 generado")
