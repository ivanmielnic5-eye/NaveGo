# ANEXO E — CLAUDE / PROPUESTA DE IMPLEMENTACION FASE 1A (A2)

**Fecha:** 2026-10-12
**Origen:** consulta a Claude sobre el proximo paso tras el cierre de Banco A.
**Contenido:** respuesta completa de Claude, sin resumir.

---

# Propuesta de implementación: Fase 1a, corrida A2

Nada de lo que sigue está ejecutado. Todo queda sujeto a la aprobación del Director.

## 0. Hechos, inferencias y lo que no se puede decidir

**Hechos (del informe):** los de las secciones 2-5 del informe, en particular val 51,5% con todos los fallos `real='1' pred='2'`, base 52,3% con el mismo colapso, y `train_loss` 0,0539 / `eval_loss` 0,0529.

**Inferencias mías:**
1. **El loss de 0,05 no prueba que la decisión se aprendió.** Si la parte supervisada fueran ~13 tokens con la decisión a azar y el resto determinista, el loss medio sería ≈ ln 2 / 13 ≈ 0,053. El 13 es hipotético (no sé el formato real), pero muestra que ese loss es compatible con una decisión al azar. La caída a 0,05 en 20 steps parece haber sido el aprendizaje de formato y plantilla.
2. **El colapso ocurrió con T vistos (val tiene los mismos T que train).** No fue un fallo de generalización: la pregunta de la Fase 1a ni siquiera se alcanzó. Y el confirmatorio preregistrado nunca se evaluó con el SFT.
3. **Base y SFT colapsan igual a `ir_a`.** Dos modelos distintos con el mismo patrón hacen sospechar del pipeline de evaluación (parser con valor por defecto, plantilla distinta entre entrenamiento e inferencia), no solo del aprendizaje.
4. **La contradicción del prompt es contribuyente plausible, pero improbable como causa única.** Las etiquetas son deterministas en (d, T): si la optimización funcionara, el SFT las ajustaría igual.
5. **Con 4 valores de T en train, "regla" y "tabla de 4 umbrales" ajustan igual de bien.** Los T del confirmatorio (12,5; 17,5; 22,5) están dentro del rango, así que solo miden interpolación.

**No decidible sin más información:** si el adaptador LoRA de A1 está guardado; el formato real de salida (¿`'1'/'2'` son ids del parser o lo que genera el modelo?); épocas, learning rate y steps; y si "baja velocidad" pertenece al objetivo (decisión del Director).

## 1. Decisión sobre velocidad

- **Mi recomendación: fuera de la Fase 1a.** El constructo de 1a es aplicar un criterio escalar. Una condición no presente en el estado ni en la etiqueta lo contamina, y `sog≡0.0` es un campo muerto.
- **¿Pertenece al objetivo del proyecto?** Eso lo decide el Director. Técnicamente tiene sentido si "llegar" debe significar "llegar con velocidad controlada" (atraque, Fase 3).
- **Si entra, va en la 1b:** el estado incluye velocidad con variación real e independiente de la distancia; el contrato declara T y v_max (en nudos); acciones `{ir_a, frenar, terminar}`; etiqueta: `d<T y v≤v_max` → terminar, `d<T y v>v_max` → frenar, resto → ir_a. Sigue siendo una regla determinista (un árbol la resuelve): sirve como ABC, no como evidencia de derivación.

## 2. Prompt saneado

Difiero de Luna en un punto: **8 decimales no.** Agregan tokens de dígitos sin información y dificultan la comparación. Uso 1 decimal, con la etiqueta calculada sobre el valor **mostrado**, y excluyo del banco principal los casos con |d−T| < 0,3.

```
=== PROPÓSITO ===
Llevar el barco hasta la meta.
La misión se considera completa cuando la distancia a la meta es menor que {T} metros.

=== ESTADO ACTUAL ===
- Distancia a la meta: {d} metros

=== ACCIONES DISPONIBLES ===
{acciones}   ← ir_a: seguir navegando hacia la meta. / terminar: declarar la misión como cumplida. (orden aleatorizado por contexto)

=== TAREA ===
Elegí la acción que mejor contribuya al propósito.
Respondé únicamente con JSON: {"accion": "<nombre>"}
```

**Reglas de consistencia:**
- T aparece **una sola vez** (en el contrato), y la plantilla no contiene ningún dígito (se verifica por código).
- Cero mención a velocidad, nudos u otros campos.
- La respuesta usa **palabras** (`ir_a`/`terminar`), no ids.

**Caso d = T:** el contrato dice "menor que", así que d = T es `ir_a`. Queda fuera del banco principal; si lo quieren, como estrato diagnóstico aparte (convención del borde).

## 3. Verificación del enmascaramiento del loss

Para A1 es **inverificable** (el .ipynb no se recuperó). Para A2 se verifica por construcción con la Celda 2, antes de entrenar. Qué revisar:
- Que exista la llamada a `train_on_responses_only` (de `unsloth.chat_templates`) **después** de crear el trainer, con `instruction_part`/`response_part` iguales a las cabeceras exactas de Llama 3.1 (`<|start_header_id|>user<|end_header_id|>\n\n` y la de assistant; verificalo contra tu versión de Unsloth). Si no coinciden, el enmascaramiento falla en silencio.
- Que lo supervisado, decodificado, sea **solo** la respuesta JSON más el fin de turno.
- Que el número de tokens supervisados sea pequeño (la celda lo imprime junto con la referencia ln 2 / N).

Si no está enmascarado: aplicar la llamada, volver a correr la celda hasta que pase.

## 4. Comparación emparejada base vs SFT

- **Mismos contextos congelados, mismo prompt, mismo método.** En vez de generar y parsear, uso **puntaje forzado**: log-prob de cada respuesta completa (`{"accion": "terminar"}` vs `{"accion": "ir_a"}`) y diferencia de log-probs. Elimina el parser y la dependencia de generación.
- La base se puntúa con `model.disable_adapter()` sobre el mismo modelo.
- Una **verificación de generación** sobre 40 contextos comprueba que lo generado coincide con el puntaje forzado (compuerta).
- **Sets:** val (T vistos, solo para ajustar y diagnosticar), `test_interp` y `test_extrap` (T no vistos, intocables hasta el veredicto).
- **Métricas:** exactitud, AUC de la diferencia de log-probs, McNemar pareado opcional (`scipy.stats.binomtest`), todo por estrato con IC de Wilson.

## 5. Medición de generalización por T

Por cada T no visto: tasa de `terminar`, matriz de confusión, y **umbral efectivo T̂**: ajuste lineal de la diferencia de log-probs contra d en el rango |d−T| ≤ 4 m, T̂ = punto de cruce por cero, con IC por bootstrap. Si la pendiente no es negativa, T̂ queda indefinido ("sin umbral"). La Celda 3 lo hace todo.

## 6. Criterios preregistrados

Son **propuestas**: el Director las confirma antes de correr, y quedan codificados al inicio de la Celda 3.

**Compuertas (si alguna falla, el run es inválido, no refuta nada):**
- Enmascaramiento verificado.
- Exactitud en train (puntaje forzado, 200 ejemplos) ≥ 0,99.
- AUC en val ≥ 0,60.
- Acuerdo generación vs puntaje forzado ≥ 0,98.

**Veredictos (en este orden):**

| Veredicto | Condición |
|---|---|
| Inválido / sin señal | Falla una compuerta. No concluyente sobre el modelo |
| SFT no aporta | La base ya saca ≥ 0,95 en estrato lejano (criterio de falsación del memo 89) |
| No aprendió (memoriza) | En ≥2 de los 3 T de interpolación, T̂ cae a ≤0,5 m de algún T visto y a ≥0,7 m del T verdadero |
| **Aprendió (1a, interpolación)** | Exactitud ≥0,95 en estrato lejano (|d−T|≥2) con límite inferior Wilson ≥0,90, **y** |T̂−T| ≤ 1,0 m en cada T de interpolación |
| Inconcluso | Todo lo demás |

La extrapolación (T=6 y 32) se **reporta** pero no condiciona "aprendió". Con 3 semillas, el veredicto debe sostenerse en todas. Los hiperparámetros se ajustan **solo con val**, nunca con test.

## 7. Estructura del banco: A2, no B

**Corresponde rediseñar la 1a (A2), no pasar a B.** La Fase 1a no está demostrada; la 1b (velocidad, `frenar`) solo se abre con veredicto "Aprendió".

| Split | T | Tamaño |
|---|---|---|
| train | {8,10,12,14,16,18,20,22,24,26,28} | 616 |
| val | los mismos (d nuevos) | 176 |
| test_interp | {11,17,23} | 600 |
| test_extrap | {6,32} | 400 |

Cada celda (T × 4 bins de |d−T| × 2 lados) tiene igual cantidad por lado. **11 valores de T en train** (en vez de 4) hacen que "regla" sea la explicación más simple y no una tabla de umbrales. El confirmatorio de A1 puede conservarse como material legacy; A2 usa semillas nuevas.

## 8. Orden de ejecución

1. **Congelar evidencia** (tag, hashes) y registrar A1 como **"Fase 1a no respaldada: medición inválida"**. Coincido con Luna: no reclasificarlo como smoke test. El confirmatorio preregistrado nunca se evaluó con el SFT.
2. **Decisiones del Director** (sección 1, prompt, criterios). Bloquea 4 y 5.
3. **Diagnóstico de A1 sin reentrenar**, solo si existe el adaptador: puntaje forzado y generación sobre val de A1 con su prompt original. AUC alto con exactitud ≈51% indica problema de generación/parser; AUC≈0,5 indica que no aprendió. Se puede hacer en paralelo con el paso 2. Si no hay adaptador, se omite.
4. **Celda 1:** generar y congelar A2 y el manifiesto; commit del preregistro.
5. **Entrenar A2** con la Celda 2 pasando antes de `train()`; 3 semillas.
6. **Celda 3** por semilla → veredicto.
7. **Decisión:** "Aprendió" abre la 1b; "No aprendió" pide más diversidad de T o datos, sin avanzar; "Inválido" se corrige y se repite sin reinterpretar.

## 9. Riesgos y evidencia faltante

- Si no hay adaptador de A1, el diagnóstico del paso 3 no existe.
- El loss plano en 20 steps puede indicar pocos steps o learning rate insuficiente; la compuerta de train lo detecta.
- Plantilla de chat distinta entre entrenamiento e inferencia (típico con Unsloth): la verificación de generación la expone.
- Falta saber el formato real de salida, los hiperparámetros y el código del parser de A1.
- El resultado, aun con "Aprendió", seguirá siendo solo una **prueba unitaria** de aplicación de contrato (ver mis informes anteriores).

## Código

Tres celdas, cada una atómica. **No ejecutadas.** Las celdas 2 y 3 asumen un entorno Unsloth/PEFT con `trainer`, `model` y `tok` ya definidos; la 3 usa `T_TRAIN`, `T_INTERP` y `BINS` de la 1.

```python
# ===== CELDA 1: Banco A2 (Fase 1a, rev. 2) — generador + prompt + auditoría + manifiesto =====
import json, hashlib, os
import numpy as np
import re

SEED = 20261013
rng = np.random.default_rng(SEED)
OUT = "bancoA2"; os.makedirs(OUT, exist_ok=True)

T_TRAIN  = [8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]   # vistos
T_INTERP = [11, 17, 23]                                    # no vistos, dentro del rango
T_EXTRAP = [6, 32]                                         # no vistos, fuera del rango
BINS = [(0.3, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, 8.0)]   # |d - T| en metros
N_CELL = {"train": 7, "val": 2, "test_interp": 25, "test_extrap": 25}  # por (T, bin, lado)

PROMPT = """=== PROPÓSITO ===
Llevar el barco hasta la meta.
La misión se considera completa cuando la distancia a la meta es menor que {T} metros.

=== ESTADO ACTUAL ===
- Distancia a la meta: {d} metros

=== ACCIONES DISPONIBLES ===
{acciones}

=== TAREA ===
Elegí la acción que mejor contribuya al propósito.
Respondé únicamente con JSON: {{"accion": "<nombre>"}}"""
DESC = {"ir_a": "- ir_a: seguir navegando hacia la meta.",
        "terminar": "- terminar: declarar la misión como cumplida."}

def make_ctx(T, lo, hi, side, split, kind):
    while True:
        hi_eff = min(hi, T - 0.5) if side == "terminar" else hi
        m = rng.uniform(lo, hi_eff)
        d = round(float(T - m if side == "terminar" else T + m), 1)
        if abs(d - T) >= 0.3 and d >= 0.5:
            break
    orden = [str(a) for a in rng.permutation(["ir_a", "terminar"])]
    label = "terminar" if d < T else "ir_a"                    # etiqueta sobre el valor MOSTRADO
    prompt = PROMPT.format(T=f"{T:g}", d=f"{d:.1f}", acciones="\n".join(DESC[a] for a in orden))
    return dict(split=split, kind=kind, T=T, d=d, label=label, orden=orden,
                bin=[lo, hi], lado=side, prompt=prompt)

def build(Ts, n, split, kind):
    out = [make_ctx(T, lo, hi, s, split, kind)
           for T in Ts for lo, hi in BINS for s in ("terminar", "ir_a") for _ in range(n)]
    rng.shuffle(out)
    return out

data = {"train": build(T_TRAIN, N_CELL["train"], "train", "visto"),
        "val": build(T_TRAIN, N_CELL["val"], "val", "visto"),
        "test_interp": build(T_INTERP, N_CELL["test_interp"], "test", "interp"),
        "test_extrap": build(T_EXTRAP, N_CELL["test_extrap"], "test", "extrap")}

# ---- auditoría (errores bloquean) ----
errores = []
allc = [c for v in data.values() for c in v]
if re.search(r"\d", PROMPT): errores.append("la plantilla contiene dígitos propios")
if any((c["d"] < c["T"]) != (c["label"] == "terminar") for c in allc): errores.append("etiqueta incoherente con d mostrada")
if set(T_TRAIN) & (set(T_INTERP) | set(T_EXTRAP)): errores.append("T de test aparece en train")
if any(w in c["prompt"].lower() for c in allc for w in ("velocidad", "nudo")): errores.append("el prompt menciona velocidad")
vistos = {(c["T"], c["d"]) for c in data["train"]}
if any((c["T"], c["d"]) in vistos for c in data["val"]): errores.append("val duplica contextos de train")
print("ERRORES:", errores or "ninguno")
assert not errores, "No continuar"

for k in ("test_interp", "test_extrap"):
    v = data[k]
    const = np.mean([c["label"] == "ir_a" for c in v])
    fijo15 = np.mean([(c["d"] < 15) == (c["label"] == "terminar") for c in v])
    print(f"{k}: n={len(v)}  baseline const ir_a={const:.3f}  baseline regla T=15 fijo={fijo15:.3f}")

# ---- guardado + manifiesto ----
manifest = {"seed": SEED, "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(), "files": {}}
for k, v in data.items():
    path = f"{OUT}/{k}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for c in v: f.write(json.dumps(c, ensure_ascii=False) + "\n")
    manifest["files"][k] = {"n": len(v), "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}
json.dump(manifest, open(f"{OUT}/manifest.json", "w"), indent=2)
print(json.dumps(manifest, indent=2))

def target(c):   # respuesta de entrenamiento exacta
    return json.dumps({"accion": c["label"]})
```

```python
# ===== CELDA 2: verificar enmascaramiento (ejecutar con el trainer ya creado, ANTES de trainer.train()) =====
import math

def inspect_masking(trainer, tokenizer, max_sup_tokens=30):
    batch = next(iter(trainer.get_train_dataloader()))
    ids, labels = batch["input_ids"], batch["labels"]
    ok, n_sup_list = True, []
    for i in range(min(3, ids.shape[0])):
        sup = [int(t) for t, l in zip(ids[i], labels[i]) if int(l) != -100]
        txt = tokenizer.decode(sup)
        n_sup_list.append(len(sup))
        print(f"--- ej {i}: {len(sup)} tokens supervisados de {ids.shape[1]} (con padding)")
        print("SUPERVISADO:", repr(txt))
        if not (0 < len(sup) <= max_sup_tokens) or "PROP" in txt:
            ok = False
    if n_sup_list and n_sup_list[0] > 0:
        print(f"Referencia: si la decisión fuera azar y el resto determinista, loss medio ≈ ln2/N = {math.log(2)/n_sup_list[0]:.4f}")
    print("ENMASCARAMIENTO OK" if ok else "ENMASCARAMIENTO FALLIDO: la pérdida incluye el prompt")
    return ok

masking_ok = inspect_masking(trainer, tokenizer)   # 'trainer' y 'tokenizer' de tu notebook
assert masking_ok, "No entrenar: corregir train_on_responses_only (instruction_part/response_part)"
```

```python
# ===== CELDA 3: puntaje forzado (base vs SFT), T̂ por T, estratos y veredicto preregistrado =====
# Usa T_TRAIN, T_INTERP, BINS de la Celda 1. Antes: FastLanguageModel.for_inference(model).
import json, re, contextlib
import numpy as np, torch
from scipy.stats import rankdata

# ---- CRITERIOS PREREGISTRADOS (el Director confirma ANTES de correr) ----
ACC_FAR_MIN, ACC_FAR_LB, EPS_THAT = 0.95, 0.90, 1.0
TRAIN_ACC_MIN, AUC_MIN, GEN_AGREE_MIN, BASE_FAR_MAX = 0.99, 0.60, 0.98, 0.95

def load(p): return [json.loads(l) for l in open(p, encoding="utf-8")]

def wilson(k, n, z=1.96):
    p = k / n; den = 1 + z*z/n
    c = (p + z*z/(2*n)) / den; h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return c - h, c + h

def auc(x, y):
    x = np.asarray(x, float); y = np.asarray(y, bool)
    n1, n0 = y.sum(), (~y).sum()
    return (rankdata(x)[y].sum() - n1*(n1+1)/2) / (n1*n0)

def chat_ids(tok, prompt):
    text = tok.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True)
    return tok(text, add_special_tokens=False, return_tensors="pt").input_ids

@torch.no_grad()
def seq_lp(model, tok, prompt, completion):
    p = chat_ids(tok, prompt)
    c = tok(completion, add_special_tokens=False, return_tensors="pt").input_ids
    ids = torch.cat([p, c], dim=1).to(model.device)
    lp = torch.log_softmax(model(ids).logits[0, p.shape[1]-1:-1].float(), dim=-1)
    return float(lp.gather(1, ids[0, p.shape[1]:].unsqueeze(1)).sum())

def score_all(model, tok, ctxs, base=False):
    cm = model.disable_adapter() if base else contextlib.nullcontext()
    with cm:
        return np.array([seq_lp(model, tok, c["prompt"], '{"accion": "terminar"}')
                         - seq_lp(model, tok, c["prompt"], '{"accion": "ir_a"}') for c in ctxs])

@torch.no_grad()
def gen_choice(model, tok, prompt):
    ids = chat_ids(tok, prompt).to(model.device)
    out = model.generate(ids, max_new_tokens=24, do_sample=False)
    m = re.search(r'"accion"\s*:\s*"(ir_a|terminar)"', tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True))
    return m.group(1) if m else None

def t_hat(ctxs, diff, T, B=200):
    r = np.random.default_rng(0)
    idx = [i for i, c in enumerate(ctxs) if c["T"] == T and abs(c["d"] - T) <= 4]
    d, z = np.array([ctxs[i]["d"] for i in idx]), diff[idx]
    def fit(dd, zz):
        b, a = np.polyfit(dd, zz, 1)
        return (-a / b) if b < -1e-6 else np.nan
    bs = np.array([fit(d[j], z[j]) for j in (r.integers(0, len(d), len(d)) for _ in range(B))])
    ci = np.nanpercentile(bs, [2.5, 97.5]) if np.isfinite(bs).any() else (np.nan, np.nan)
    return fit(d, z), ci

def strata(ctxs, diff, name):
    y = np.array([c["label"] == "terminar" for c in ctxs]); pred = diff > 0
    print(f"[{name}] acc={np.mean(pred == y):.3f} AUC={auc(diff, y):.3f} frac_pred_terminar={pred.mean():.3f}")
    for lo, hi in BINS:
        for s in ("terminar", "ir_a"):
            ix = [i for i, c in enumerate(ctxs) if tuple(c["bin"]) == (lo, hi) and c["lado"] == s]
            k = int((pred[ix] == y[ix]).sum()); l, h = wilson(k, len(ix))
            print(f"    |d-T| en [{lo},{hi}) lado={s:8s} n={len(ix):3d} acc={k/len(ix):.3f} IC95=[{l:.3f},{h:.3f}]")

def run_eval(model, tok, masking_ok, bank="bancoA2", n_gen=40):
    D = {k: load(f"{bank}/{k}.jsonl") for k in ("train", "val", "test_interp", "test_extrap")}
    out = {n: {k: score_all(model, tok, D[k], base) for k in ("val", "test_interp", "test_extrap")}
           for n, base in (("base", True), ("sft", False))}
    sub = D["train"][:200]; dtr = score_all(model, tok, sub)
    ytr = np.array([c["label"] == "terminar" for c in sub]); yv = np.array([c["label"] == "terminar" for c in D["val"]])
    ag = [gen_choice(model, tok, c["prompt"]) == ("terminar" if s > 0 else "ir_a")
          for c, s in zip(D["val"][:n_gen], out["sft"]["val"][:n_gen])]
    gates = {"masking_verificado": bool(masking_ok),
             "ajuste_train": np.mean((dtr > 0) == ytr) >= TRAIN_ACC_MIN,
             "senal_val": auc(out["sft"]["val"], yv) >= AUC_MIN,
             "generacion_coincide": np.mean(ag) >= GEN_AGREE_MIN}
    print("COMPUERTAS:", gates)
    for n in ("base", "sft"):
        for k in ("val", "test_interp", "test_extrap"): strata(D[k], out[n][k], f"{n}/{k}")
    ci = D["test_interp"]; y = np.array([c["label"] == "terminar" for c in ci])
    far = np.array([c["bin"][0] >= 2.0 for c in ci])
    def far_acc(df): k = int(((df > 0) == y)[far].sum()); return k / far.sum(), wilson(k, int(far.sum()))[0]
    fb, _ = far_acc(out["base"]["test_interp"]); fs, lbs = far_acc(out["sft"]["test_interp"])
    hats = {T: t_hat(ci, out["sft"]["test_interp"], T)[0] for T in T_INTERP}
    print("T_hat (SFT) por T no visto:", hats)
    if not all(gates.values()):
        return "INVÁLIDO / SIN SEÑAL (falló: %s) -> no concluyente sobre el modelo" % [k for k, v in gates.items() if not v]
    if fb >= BASE_FAR_MAX: return "SFT NO APORTA: la base ya resuelve (falsación memo 89)"
    mem = sum(bool(np.isfinite(h) and min(abs(h - s) for s in T_TRAIN) <= 0.5 and abs(h - T) >= 0.7) for T, h in hats.items())
    if mem >= 2: return "NO APRENDIÓ: T_hat cae en umbrales vistos (memoriza)"
    ok_t = all(np.isfinite(h) and abs(h - T) <= EPS_THAT for T, h in hats.items())
    if fs >= ACC_FAR_MIN and lbs >= ACC_FAR_LB and ok_t: return "APRENDIÓ (1a, interpolación)"
    return "INCONCLUSO"

print("VEREDICTO:", run_eval(model, tok, masking_ok))   # 'model' y 'tok' de tu notebook (PeftModel)
```

Las dos preguntas del final del borrador (ajustar el informe y dónde guardarlo) estaban dirigidas a vos, no a mí. Con el criterio de trazabilidad del expediente, guardar esta respuesta como anexo E parece coherente.
