#!/usr/bin/env python3
"""_gen_nb_A3.py - Genera el notebook de entrenamiento A3.

Estructura basada en _gen_nb_A2.py, adaptada para banco A3:
- Carga train_sft.jsonl y val_sft.jsonl de bancoA3.
- Mismo LoRA r=16, alpha=32.
- max_steps=300 (~2 epochs sobre 1188 ejemplos).
- Enmascaramiento verificado antes de entrenar.
- Guarda en timonel_lora_banco_A3.
"""
import json


def md(t):
    return {"cell_type": "markdown", "metadata": {},
            "source": t.splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": t.splitlines(keepends=True)}


celdas = [
    md("# Timonel SFT - Banco A3 (Fase 1a etapa 1)\n\n"
       "Objetivo: entrenar Llama 3.1 8B con el banco A3 para que\n"
       "aprenda a aplicar contratos con clausula de velocidad.\n\n"
       "Diferencias con A2:\n"
       "- Clausula Y la velocidad es <= v_max (no solo distancia).\n"
       "- v_max variable en train.\n"
       "- Contra-prior en Q1 (v en la parte alta del rango permitido).\n"
       "- Formulaciones F_train y F_dev mezcladas.\n\n"
       "Evaluacion esperada:\n"
       "- bancoA3 (visible): comparar contra P-text (100%) y P-struct.\n"
       "- F-held (retenido): donde P-text falla (50%)."),
    md("## 1. Instalar dependencias"),
    code("""!pip install -q unsloth
!pip install -q --no-deps trl peft accelerate bitsandbytes
!pip install -q datasets"""),

    md("## 2. Cargar modelo base"),
    code("""from unsloth import FastLanguageModel
import torch

max_seq_length = 1024
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
    max_seq_length = max_seq_length,
    load_in_4bit = True,
)"""),

    md("## 3. LoRA"),
    code("""model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 32,
    lora_dropout = 0.0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
)"""),
]


celdas += [
    md("## 4. Cargar banco A3"),
    code("""import glob, os
from datasets import load_dataset

_candidatos = glob.glob("/kaggle/input/**/train_sft.jsonl", recursive=True)
assert _candidatos, "No encontre train_sft.jsonl en /kaggle/input"
TRAIN_PATH = _candidatos[0]
VAL_PATH = os.path.join(os.path.dirname(TRAIN_PATH), "val_sft.jsonl")
assert os.path.exists(VAL_PATH), f"No encontre val_sft.jsonl en {VAL_PATH}"
print(f"TRAIN_PATH = {TRAIN_PATH}")
print(f"VAL_PATH   = {VAL_PATH}")

dataset_train = load_dataset("json", data_files=TRAIN_PATH, split="train")
dataset_val = load_dataset("json", data_files=VAL_PATH, split="train")
print(f"Train: {len(dataset_train)} | Val: {len(dataset_val)}")

e = dataset_train[0]["messages"]
print()
print("System:", e[0]["content"][:80])
print("User (primeros 200):", e[1]["content"][:200])
print("Assistant:", e[2]["content"])"""),

    md("## 5. Chat template"),
    code("""from unsloth import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="llama-3.1")

def formatear(ejemplo):
    return {"text": tokenizer.apply_chat_template(
        ejemplo["messages"], tokenize=False, add_generation_prompt=False)}

dataset_train = dataset_train.map(formatear)
dataset_val = dataset_val.map(formatear)
print("--- Primeros 600 chars del primer ejemplo ---")
print(dataset_train[0]["text"][:600])"""),

    md("## 6. SFTTrainer"),
    code("""from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

trainer = SFTTrainer(
    model = model, tokenizer = tokenizer,
    train_dataset = dataset_train, eval_dataset = dataset_val,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2, packing = False,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 10, max_steps = 300,
        learning_rate = 2e-4,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 10,
        eval_strategy = "steps", eval_steps = 50,
        save_strategy = "steps", save_steps = 50,
        optim = "adamw_8bit", weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407, output_dir = "outputs_A3", report_to = "none",
    ),
)"""),

    md("## 7. Enmascaramiento del prompt"),
    code("""from unsloth.chat_templates import train_on_responses_only

trainer = train_on_responses_only(
    trainer,
    instruction_part="<|start_header_id|>user<|end_header_id|>\\n\\n",
    response_part="<|start_header_id|>assistant<|end_header_id|>\\n\\n",
)
print("[OK] train_on_responses_only aplicado")"""),

    md("## 8. Verificacion de enmascaramiento"),
    code("""import math

def inspect_masking(trainer, tokenizer, max_sup_tokens=30):
    batch = next(iter(trainer.get_train_dataloader()))
    ids, labels = batch["input_ids"], batch["labels"]
    ok = True
    n_sup_list = []
    for i in range(min(3, ids.shape[0])):
        sup = [int(t) for t, l in zip(ids[i], labels[i]) if int(l) != -100]
        txt = tokenizer.decode(sup)
        n_sup_list.append(len(sup))
        print(f"--- ej {i}: {len(sup)} tokens supervisados de {ids.shape[1]}")
        print("SUPERVISADO:", repr(txt))
        if not (0 < len(sup) <= max_sup_tokens) or "PROPOSITO" in txt:
            ok = False
    if n_sup_list and n_sup_list[0] > 0:
        print(f"Referencia: si la decision fuera azar, loss medio ~ ln2/N = {math.log(2)/n_sup_list[0]:.4f}")
    print("ENMASCARAMIENTO OK" if ok else "ENMASCARAMIENTO FALLIDO")
    return ok

masking_ok = inspect_masking(trainer, tokenizer)
assert masking_ok, "No entrenar: corregir train_on_responses_only"
print()
print("[COMPUERTA] Enmascaramiento: PASO")"""),

    md("## 9. Entrenamiento"),
    code("""stats = trainer.train()
print(stats)"""),

    md("## 10. Guardar"),
    code("""model.save_pretrained("timonel_lora_banco_A3")
tokenizer.save_pretrained("timonel_lora_banco_A3")
!ls -la timonel_lora_banco_A3/"""),
]

nb = {"cells": celdas,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python", "version": "3.10"},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 5}

with open("timonel_sft_A3_kaggle.ipynb", "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("[OK] Notebook A3 generado")
