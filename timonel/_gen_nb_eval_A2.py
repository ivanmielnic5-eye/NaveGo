#!/usr/bin/env python3
"""_gen_nb_eval_A2.py - Genera el notebook de evaluacion de A2.

Evalua base vs SFT sobre test_interp y test_extrap con puntaje forzado.
Estima T_efectivo por T no visto. Aplica veredicto de la seccion 23.8.
"""
import json


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(keepends=True)}


def code(t):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": t.splitlines(keepends=True),
    }


celdas = [
    md("# Timonel Eval - Banco A2 (Fase 1a, rev. 2)\n\n"
       "Evalua base vs SFT sobre test_interp y test_extrap.\n\n"
       "- Puntaje forzado: lp(terminar) - lp(ir_a).\n"
       "- Estimacion de T_efectivo por T no visto.\n"
       "- Analisis por estrato (|d-T|).\n"
       "- Veredicto segun memo 89 seccion 23.8."),
    md("## 1. Instalar dependencias"),
    code("""!pip install -q unsloth
!pip install -q --no-deps trl peft accelerate bitsandbytes
!pip install -q datasets scipy"""),
]

celdas += [
    md("## 2. Cargar modelo base + LoRA A2"),
    code("""from unsloth import FastLanguageModel
import torch, glob, os

max_seq_length = 1024

# Descubrir el adapter de A2
_ads = glob.glob("/kaggle/input/**/adapter_config.json", recursive=True)
_ads = [a for a in _ads if "a2" in a.lower() or "lora-a2" in a.lower()]
assert _ads, f"No encontre adapter_config.json. Encontrados: {glob.glob('/kaggle/input/**/adapter_config.json', recursive=True)}"
ADAPTER_PATH = os.path.dirname(_ads[0])
print(f"ADAPTER_PATH = {ADAPTER_PATH}")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = ADAPTER_PATH,
    max_seq_length = max_seq_length,
    load_in_4bit = True,
)
print("[OK] Modelo + LoRA cargado")"""),
]

celdas += [
    md("## 3. Cargar test_interp y test_extrap"),
    code("""import json
from datasets import load_dataset

_ts = glob.glob("/kaggle/input/**/test_interp.jsonl", recursive=True)
assert _ts, "No encontre test_interp.jsonl"
INTERP_PATH = _ts[0]
EXTRAP_PATH = os.path.join(os.path.dirname(INTERP_PATH), "test_extrap.jsonl")
print(f"INTERP: {INTERP_PATH}")
print(f"EXTRAP: {EXTRAP_PATH}")

test_interp = [json.loads(l) for l in open(INTERP_PATH)]
test_extrap = [json.loads(l) for l in open(EXTRAP_PATH)]
print(f"test_interp: {len(test_interp)} | test_extrap: {len(test_extrap)}")

# Ejemplo
e = test_interp[0]
print(f"T={e['T']} d={e['d']} label={e['label']} bin={e['bin']} lado={e['lado']}")"""),

    md("## 4. Funcion de puntaje forzado"),
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

def score(ctx, base=False):
    cm = model.disable_adapter() if base else __import__("contextlib").nullcontext()
    with cm:
        lp_t = seq_lp(ctx["prompt"], '{"accion": "terminar"}')
        lp_i = seq_lp(ctx["prompt"], '{"accion": "ir_a"}')
    return lp_t - lp_i"""),
]

celdas += [
    md("## 5. Evaluacion base vs SFT"),
    code("""import numpy as np
from scipy.stats import rankdata

def wilson(k, n, z=1.96):
    p = k/n; den = 1+z*z/n
    c = (p+z*z/(2*n))/den
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return c-h, c+h

def auc(x, y):
    x = np.asarray(x, float); y = np.asarray(y, bool)
    n1, n0 = y.sum(), (~y).sum()
    return (rankdata(x)[y].sum() - n1*(n1+1)/2)/(n1*n0) if n1*n0 else float("nan")

def evaluar(ctxs, name):
    print(f"=== {name} ===")
    diff_sft = np.array([score(c, base=False) for c in ctxs])
    diff_base = np.array([score(c, base=True) for c in ctxs])
    y = np.array([c["label"] == "terminar" for c in ctxs])
    pred_sft = diff_sft > 0
    pred_base = diff_base > 0
    acc_sft = np.mean(pred_sft == y)
    acc_base = np.mean(pred_base == y)
    print(f"  accuracy SFT : {acc_sft:.3f}")
    print(f"  accuracy base: {acc_base:.3f}")
    print(f"  AUC SFT      : {auc(diff_sft, y):.3f}")
    print(f"  AUC base     : {auc(diff_base, y):.3f}")
    print(f"  frac pred terminar SFT : {pred_sft.mean():.3f}")
    print(f"  frac pred terminar base: {pred_base.mean():.3f}")
    return diff_sft, diff_base, y

diff_interp_sft, diff_interp_base, y_interp = evaluar(test_interp, "test_interp")
print()
diff_extrap_sft, diff_extrap_base, y_extrap = evaluar(test_extrap, "test_extrap")"""),

    md("## 6. Accuracy por estrato (|d-T|)"),
    code("""def por_estrato(ctxs, diff, name):
    print(f"=== {name} ===")
    y = np.array([c["label"] == "terminar" for c in ctxs])
    pred = diff > 0
    for lo, hi in [(0.3,1.0),(1.0,2.0),(2.0,4.0),(4.0,8.0)]:
        ix = [i for i,c in enumerate(ctxs) if tuple(c["bin"])==(lo,hi)]
        if not ix: continue
        k = int((pred[ix] == y[ix]).sum())
        l, h = wilson(k, len(ix))
        print(f"  |d-T| en [{lo},{hi}): n={len(ix):3d} acc={k/len(ix):.3f} IC95=[{l:.3f},{h:.3f}]")

por_estrato(test_interp, diff_interp_sft, "test_interp SFT")
por_estrato(test_extrap, diff_extrap_sft, "test_extrap SFT")"""),
]

celdas += [
    md("## 7. T_efectivo por T no visto (interpolacion)"),
    code("""def t_efectivo(ctxs, diff, T, B=1000):
    ix = [i for i,c in enumerate(ctxs) if c["T"]==T and abs(c["d"]-T)<=4.0]
    if len(ix) < 5: return float("nan"), (float("nan"), float("nan"))
    d = np.array([ctxs[i]["d"] for i in ix])
    z = diff[ix]
    def fit(dd, zz):
        b, a = np.polyfit(dd, zz, 1)
        return (-a/b) if b < -1e-6 else float("nan")
    rng = np.random.default_rng(0)
    bs = []
    for _ in range(B):
        idx = rng.integers(0, len(d), len(d))
        bs.append(fit(d[idx], z[idx]))
    bs = np.array([x for x in bs if np.isfinite(x)])
    ci = np.percentile(bs, [2.5, 97.5]) if len(bs) else (float("nan"), float("nan"))
    return fit(d, z), (float(ci[0]), float(ci[1]))

print("=== T_efectivo (SFT) en test_interp ===")
hats = {}
for T in [11, 17, 23]:
    th, (lo, hi) = t_efectivo(test_interp, diff_interp_sft, T)
    hats[T] = th
    print(f"  T={T}: T_efectivo={th:.3f}  IC95=[{lo:.3f},{hi:.3f}]")

print()
print("=== T_efectivo (base) en test_interp ===")
for T in [11, 17, 23]:
    th, _ = t_efectivo(test_interp, diff_interp_base, T)
    print(f"  T={T}: T_efectivo={th:.3f}")"""),

    md("## 8. Verificacion de generacion (200 casos)"),
    code("""import re
@torch.no_grad()
def gen_choice(prompt):
    msgs = [{"role":"system","content":SYSTEM},{"role":"user","content":prompt}]
    text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    ids = tokenizer(text, return_tensors="pt").input_ids.to(model.device)
    out = model.generate(ids, max_new_tokens=16, do_sample=False)
    dec = tokenizer.decode(out[0, ids.shape[1]:], skip_special_tokens=True)
    m = re.search(r'"accion"\\s*:\\s*"(ir_a|terminar)"', dec)
    return m.group(1) if m else None

sample = test_interp[:200]
agr = 0; val = 0
for c, dif in zip(sample, diff_interp_sft[:200]):
    pred_gen = gen_choice(c["prompt"])
    if pred_gen is None: continue
    val += 1
    pred_fc = "terminar" if dif > 0 else "ir_a"
    if pred_gen == pred_fc: agr += 1
print(f"Generacion valida : {val}/{len(sample)}")
print(f"Acuerdo gen vs FC : {agr}/{val} = {agr/max(val,1):.3f}")"""),

    md("## 9. Veredicto (seccion 23.8 del memo 89)"),
    code("""# Compuertas tecnicas
y_interp_arr = np.array([c["label"]=="terminar" for c in test_interp])
far = np.array([c["bin"][0] >= 2.0 for c in test_interp])
acc_far_sft = np.mean((diff_interp_sft > 0)[far] == y_interp_arr[far])
acc_far_base = np.mean((diff_interp_base > 0)[far] == y_interp_arr[far])
n_far = int(far.sum())
lb_far = wilson(int(((diff_interp_sft>0)==y_interp_arr)[far].sum()), n_far)[0]

print(f"acc_far SFT : {acc_far_sft:.3f} (IC inf {lb_far:.3f}, n={n_far})")
print(f"acc_far base: {acc_far_base:.3f}")
print()

# Veredicto
if acc_far_base >= 0.95:
    veredicto = "SFT NO APORTA (base ya resuelve)"
elif sum(1 for T,h in hats.items() if np.isfinite(h) and min(abs(h-s) for s in [8,10,12,14,16,18,20,22,24,26,28])<=0.5 and abs(h-T)>=0.7) >= 2:
    veredicto = "NO APRENDIO (memoriza)"
elif acc_far_sft >= 0.95 and lb_far >= 0.90 and all(np.isfinite(h) and abs(h-T)<=1.0 for T,h in hats.items()):
    veredicto = "APRENDIO (Fase 1a, interpolacion)"
else:
    veredicto = "INCONCLUSO"

print(f"VEREDICTO: {veredicto}")"""),
]

nb = {"cells": celdas,
      "metadata": {"kernelspec": {"display_name":"Python 3","language":"python","name":"python3"},
                   "language_info": {"name":"python","version":"3.10"},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 5}

with open("timonel_eval_A2_kaggle.ipynb","w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("[OK] Notebook eval A2 generado")
