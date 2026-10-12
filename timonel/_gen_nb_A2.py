#!/usr/bin/env python3
"""_gen_nb_A2.py - Genera el notebook de entrenamiento A2.

Diferencia clave con A1:
- Usa train_on_responses_only con verificacion antes de train().
- El banco A2 tiene prompt sin mencion a velocidad.
- max_steps ajustado a 616 ejemplos (2 epochs).
"""
import json


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.split("\n")}


def code(t):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": t.split("\n"),
    }


celdas = [
    md("# Timonel SFT - Banco A2 (Fase 1a, rev. 2)\n\n"
       "Objetivo: verificar si Llama 3.1 8B aplica el criterio de finalizacion\n"
       "`d < T -> terminar` y generaliza a valores de T no vistos.\n\n"
       "Diferencias con A1:\n"
       "- Prompt sin mencion a velocidad.\n"
       "- Respuesta en palabra (ir_a / terminar), no en digito.\n"
       "- Enmascaramiento del prompt verificado antes de entrenar.\n"
       "- 11 valores de T en train (no 4)."),
]

celdas += [
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
    md("## 4. Cargar banco A2"),
    code("""from datasets import load_dataset

TRAIN_PATH = "/kaggle/input/timonel-banco-a2/train.jsonl"
VAL_PATH   = "/kaggle/input/timonel-banco-a2/val.jsonl"

dataset_train = load_dataset("json", data_files=TRAIN_PATH, split="train")
dataset_val = load_dataset("json", data_files=VAL_PATH, split="train")
print(f"Train: {len(dataset_train)} | Val: {len(dataset_val)}")
print()
print("Ejemplo 0 (prompt):")
print(dataset_train[0]["prompt"][:400])
print()
print(f"T={dataset_train[0]['T']} d={dataset_train[0]['d']} label={dataset_train[0]['label']}")"""),

    md("## 5. Chat template + formateo\n\n"
       "La respuesta esperada es un JSON con la accion como palabra:\n"
       '`{"accion": "ir_a"}` o `{"accion": "terminar"}`.'),
    code("""from unsloth import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="llama-3.1")

SYSTEM_PROMPT = ("Sos el timonel de un velero autonomo. Respondes "
                 "UNICAMENTE con el JSON pedido, sin texto adicional.")

def formatear(ejemplo):
    respuesta = '{"accion": "' + ejemplo["label"] + '"}'
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": ejemplo["prompt"]},
        {"role": "assistant", "content": respuesta},
    ]
    return {"text": tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)}

dataset_train = dataset_train.map(formatear)
dataset_val = dataset_val.map(formatear)
print("--- Ejemplo formateado (primeros 800 chars) ---")
print(dataset_train[0]["text"][:800])"""),
]

celdas += [
    md("## 6. SFTTrainer\n\n"
       "Se crea el trainer con la config conservadora (misma que A1).\n"
       "El enmascaramiento se aplica DESPUES de crear el trainer y se\n"
       "verifica ANTES de train()."),
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
        warmup_steps = 10, max_steps = 154,
        learning_rate = 2e-4,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 10,
        eval_strategy = "steps", eval_steps = 50,
        save_strategy = "steps", save_steps = 50,
        optim = "adamw_8bit", weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407, output_dir = "outputs_A2", report_to = "none",
    ),
)"""),

    md("## 7. Enmascaramiento del prompt\n\n"
       "Aplica train_on_responses_only para que el loss se calcule SOLO\n"
       "sobre la respuesta del asistente. Esto es lo que no se hizo en A1."),
    code("""from unsloth.chat_templates import train_on_responses_only

trainer = train_on_responses_only(
    trainer,
    instruction_part="<|start_header_id|>user<|end_header_id|>\\n\\n",
    response_part="<|start_header_id|>assistant<|end_header_id|>\\n\\n",
)
print("[OK] train_on_responses_only aplicado")"""),
]

celdas += [
    md("## 8. Verificacion de enmascaramiento\n\n"
       "Compuerta tecnica: si el enmascaramiento fallo, NO se entrena.\n"
       "Se inspeccionan 3 ejemplos y se verifica que los tokens supervisados\n"
       "sean pocos (la respuesta JSON, ~10 tokens) y NO incluyan el prompt."),
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
    code("""model.save_pretrained("timonel_lora_banco_A2")
tokenizer.save_pretrained("timonel_lora_banco_A2")
!ls -la timonel_lora_banco_A2/"""),
]

nb = {
    "cells": celdas,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10"},
        "accelerator": "GPU",
    },
    "nbformat": 4, "nbformat_minor": 5,
}

with open("timonel_sft_A2_kaggle.ipynb", "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("[OK] Notebook A2 generado")
