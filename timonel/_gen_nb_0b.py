#!/usr/bin/env python3
"""_gen_nb_0b.py - Genera el notebook de evaluacion de la etapa 0b."""
import json


def md(t):
    return {"cell_type": "markdown", "metadata": {},
            "source": t.splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": t.splitlines(keepends=True)}


celdas = [
    md("# Timonel Etapa 0b - Controles del probe F2\n\n"
       "Evalua SFT vs base sobre 4 bloques:\n"
       "- B1 placebo: v visible, sin clausula.\n"
       "- B2 v_max variable: con clausula, 5 v_max, contra-prior.\n"
       "- B3 contrafactual: mismo d/T/v, cambia v_max.\n"
       "- B4 vecindad del fallo Q2."),
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
    md("## 5. Evaluacion por bloque (SFT y base)"),
    code("""import numpy as np

def wilson(k, n, z=1.96):
    p = k/n; den = 1+z*z/n
    c = (p+z*z/(2*n))/den
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return c-h, c+h

def evaluar(base):
    name = "BASE" if base else "SFT"
    print(f"=== {name} ===")
    res = {}
    for b in ["B1_placebo", "B2_vmax_var", "B3_contrafactual", "B4_vecindad"]:
        ix = [i for i,c in enumerate(probe) if c["bloque"] == b]
        diffs = np.array([score(probe[i], base=base) for i in ix])
        pred = np.array(["terminar" if x > 0 else "ir_a" for x in diffs])
        real = np.array([probe[i]["label"] for i in ix])
        k = int((pred == real).sum())
        n = len(ix)
        l, h = wilson(k, n)
        print(f"  {b}: n={n} acc={k/n:.3f} IC95=[{l:.3f},{h:.3f}]")
        res[b] = {"ix": ix, "diffs": diffs, "pred": pred, "real": real}
    return res

res_sft = evaluar(base=False)
print()
res_base = evaluar(base=True)"""),
]

celdas += [
    md("## 6. Analisis especifico por bloque"),
    code("""# B1 placebo: si el modelo usa v como cautela, falla en (d<T, v alta)
print("=== B1 placebo: (d<T, v alta) ===")
for name, res in [("SFT", res_sft), ("BASE", res_base)]:
    ix = [i for i in res["B1_placebo"]["ix"]
          if probe[i]["sub"] == "d_menor_v_alta"]
    pred = np.array(["terminar" if score(probe[i], base=(name=="BASE")) > 0 else "ir_a" for i in ix])
    real = np.array([probe[i]["label"] for i in ix])
    k = int((pred == real).sum())
    n = len(ix)
    print(f"  {name}: acc={k/n:.3f} ({k}/{n})  pred_terminar={int((pred=='terminar').sum())}")

print()
print("=== B2 contra-prior: (d<T, v dentro de v_max, v>0.5) ===")
for name, res in [("SFT", res_sft), ("BASE", res_base)]:
    ix = [i for i in res["B2_vmax_var"]["ix"]
          if probe[i]["sub"] == "contra_prior"]
    pred = np.array(["terminar" if score(probe[i], base=(name=="BASE")) > 0 else "ir_a" for i in ix])
    real = np.array([probe[i]["label"] for i in ix])
    k = int((pred == real).sum())
    n = len(ix)
    l, h = wilson(k, n)
    print(f"  {name}: acc={k/n:.3f} ({k}/{n}) IC95=[{l:.3f},{h:.3f}]")

print()
print("=== B3 contrafactual: cambio correcto al cambiar v_max ===")
ix_b3 = res_sft["B3_contrafactual"]["ix"]
pares = {}
for i in ix_b3:
    c = probe[i]
    par_id = c["sub"].rsplit("_", 1)[0]
    pares.setdefault(par_id, []).append(i)
for name, base in [("SFT", False), ("BASE", True)]:
    ok = 0
    total = 0
    for pid, idxs in pares.items():
        if len(idxs) != 2:
            continue
        d0 = score(probe[idxs[0]], base=base)
        d1 = score(probe[idxs[1]], base=base)
        p0 = "terminar" if d0 > 0 else "ir_a"
        p1 = "terminar" if d1 > 0 else "ir_a"
        r0 = probe[idxs[0]]["label"]
        r1 = probe[idxs[1]]["label"]
        if p0 != p1 and (p0 == r0) and (p1 == r1):
            ok += 1
        total += 1
    print(f"  {name}: pares con cambio correcto = {ok}/{total} = {ok/max(total,1):.3f}")"""),
]


celdas += [
    md("## 7. Veredicto (seccion 25.9 del memo 89)"),
    code("""def acc_sub(res, bloque, sub, base):
    ix = [i for i in res[bloque]["ix"] if probe[i]["sub"] == sub]
    if not ix:
        return float("nan")
    pred = np.array(["terminar" if score(probe[i], base=base) > 0 else "ir_a" for i in ix])
    real = np.array([probe[i]["label"] for i in ix])
    return float((pred == real).mean())

# Criterios
b1_acc_sft = acc_sub(res_sft, "B1_placebo", "d_menor_v_alta", False)
b1_acc_base = acc_sub(res_base, "B1_placebo", "d_menor_v_alta", True)
b2_cp_sft = acc_sub(res_sft, "B2_vmax_var", "contra_prior", False)
b2_cp_base = acc_sub(res_base, "B2_vmax_var", "contra_prior", True)

# B3 pares
ix_b3 = res_sft["B3_contrafactual"]["ix"]
pares = {}
for i in ix_b3:
    par_id = probe[i]["sub"].rsplit("_", 1)[0]
    pares.setdefault(par_id, []).append(i)
b3_ok = 0
for pid, idxs in pares.items():
    if len(idxs) != 2: continue
    d0 = score(probe[idxs[0]], base=False)
    d1 = score(probe[idxs[1]], base=False)
    p0 = "terminar" if d0 > 0 else "ir_a"
    p1 = "terminar" if d1 > 0 else "ir_a"
    if p0 != p1 and p0 == probe[idxs[0]]["label"] and p1 == probe[idxs[1]]["label"]:
        b3_ok += 1
b3_rate = b3_ok / max(len(pares), 1)

print(f"B1 SFT (d<T, v alta): acc={b1_acc_sft:.3f}")
print(f"B1 BASE(d<T, v alta): acc={b1_acc_base:.3f}")
print(f"B2 SFT contra-prior : acc={b2_cp_sft:.3f}")
print(f"B2 BASE contra-prior: acc={b2_cp_base:.3f}")
print(f"B3 SFT pares correctos: {b3_ok}/{len(pares)} = {b3_rate:.3f}")
print()

pasa_b1 = b1_acc_sft >= 0.95
pasa_b2 = b2_cp_sft >= 0.90
print(f"pasa B1 (>=0.95): {pasa_b1}")
print(f"pasa B2 contra-prior (>=0.90): {pasa_b2}")

if pasa_b1 and pasa_b2:
    v = "PASA 0b. El SFT ignora v sin clausula y respeta v_max variable con contra-prior. A2 congelado = brazo H1a de etapa 1."
elif not pasa_b1:
    v = "FALLA B1: usa v como senal de cautela sin que el contrato la mencione. Probe F2 se reinterpreta como heuristica."
else:
    v = "FALLA B2: usa magnitud de v e ignora v_max. Probe F2 se reinterpreta como heuristica."
print()
print(f"VEREDICTO 0b: {v}")"""),
]

nb = {"cells": celdas,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python", "version": "3.10"},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 5}

with open("timonel_0b_kaggle.ipynb", "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("[OK] Notebook 0b generado")
