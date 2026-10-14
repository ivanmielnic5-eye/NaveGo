#!/usr/bin/env python3
"""_gen_nb_audit_A3.py - Genera el notebook de auditoria de errores A3.

Solo evalua fheld_f2 y test_balanceado, con logging individual.
Objetivo: ver los 7 errores de fheld_f2 y los 4 de test_balanceado.
"""
import json


def md(t):
    return {"cell_type": "markdown", "metadata": {},
            "source": t.splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": t.splitlines(keepends=True)}


celdas = [
    md("# Timonel Audit - Errores A3\n\n"
       "Evalua fheld_f2 y test_balanceado con logging individual.\n"
       "Guarda predicciones por item + audita los errores."),
    md("## 1. Instalar dependencias"),
    code("""!pip install -q unsloth
!pip install -q --no-deps trl peft accelerate bitsandbytes
!pip install -q datasets"""),

    md("## 2. Cargar modelo + LoRA A3"),
    code("""from unsloth import FastLanguageModel
import torch, glob, os

max_seq_length = 1024
_ads = glob.glob("/kaggle/input/**/adapter_config.json", recursive=True)
_ads = [a for a in _ads if "lora-a3" in a.lower()]
assert _ads, "No encontre adaptador A3"
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
    md("## 3. Cargar splits"),
    code("""import json

def cargar_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]

_cands_f2 = glob.glob("/kaggle/input/**/fheld_f2.jsonl", recursive=True)
_cands_tb = glob.glob("/kaggle/input/**/test_balanceado.jsonl", recursive=True)
assert _cands_f2, "No encontre fheld_f2.jsonl"
assert _cands_tb, "No encontre test_balanceado.jsonl"
F2_PATH = _cands_f2[0]
TB_PATH = _cands_tb[0]
print(f"F2_PATH = {F2_PATH}")
print(f"TB_PATH = {TB_PATH}")

fheld_f2 = cargar_jsonl(F2_PATH)
test_bal = cargar_jsonl(TB_PATH)
print(f"fheld_f2: {len(fheld_f2)}")
print(f"test_balanceado: {len(test_bal)}")"""),

    md("## 4. Puntaje forzado + auditoria con logging"),
    code("""from unsloth import FastLanguageModel
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

@torch.no_grad()
def gen_choice(prompt):
    import re
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    ids = tokenizer(text, return_tensors="pt").input_ids.to(model.device)
    out = model.generate(ids, max_new_tokens=16, do_sample=False)
    dec = tokenizer.decode(out[0, ids.shape[1]:], skip_special_tokens=True)
    m = re.search(r'"accion"\\s*:\\s*"(ir_a|terminar)"', dec)
    return m.group(1) if m else None

def auditar_split(nombre, ctxs):
    print(f"=== {nombre} ===")
    errores = []
    for i, c in enumerate(ctxs):
        dif = seq_lp(c["prompt"], '{"accion": "terminar"}') - seq_lp(c["prompt"], '{"accion": "ir_a"}')
        pred = "terminar" if dif > 0 else "ir_a"
        if pred != c["label"]:
            gen = gen_choice(c["prompt"])
            errores.append({
                "idx": i,
                "label_real": c["label"],
                "pred_fc": pred,
                "pred_gen": gen,
                "diff_lp": round(dif, 4),
                "T": c.get("T"),
                "d": c.get("d"),
                "v": c.get("v"),
                "v_max": c.get("v_max"),
                "familia": c.get("familia"),
                "formulacion_id": c.get("formulacion_id"),
                "prompt": c["prompt"],
            })
    print(f"  errores: {len(errores)}/{len(ctxs)}")
    for e in errores:
        print(f"    idx={e['idx']} real={e['label_real']} pred_fc={e['pred_fc']} "
              f"pred_gen={e['pred_gen']} diff={e['diff_lp']} "
              f"T={e['T']} d={e['d']} v={e['v']} v_max={e['v_max']}")
    return errores

err_f2 = auditar_split("fheld_f2", fheld_f2)
print()
err_tb = auditar_split("test_balanceado", test_bal)"""),

    md("## 5. Guardar errores como JSON"),
    code("""with open("/kaggle/working/audit_errores_f2.jsonl", "w") as f:
    for e in err_f2:
        f.write(json.dumps(e, ensure_ascii=False) + "\\n")
with open("/kaggle/working/audit_errores_tb.jsonl", "w") as f:
    for e in err_tb:
        f.write(json.dumps(e, ensure_ascii=False) + "\\n")
print("[OK] errores guardados")
print(f"  fheld_f2: {len(err_f2)} errores")
print(f"  test_balanceado: {len(err_tb)} errores")

# Resumen por familia y por formulacion
from collections import Counter
print()
print("fheld_f2: errores por formulacion_id")
print(dict(Counter(e["formulacion_id"] for e in err_f2)))
print()
print("fheld_f2: errores por (T, v_max)")
print(dict(Counter((e["T"], e["v_max"]) for e in err_f2)))"""),
]

nb = {"cells": celdas,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python", "version": "3.10"},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 5}

with open("timonel_audit_A3_kaggle.ipynb", "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("[OK] Notebook audit A3 generado")
