import json

def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.split("\n")}

def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": t.split("\n")}

celdas = [
    md("# Timonel SFT - Banco A\n\nObjetivo: entrenar Llama 3.1 8B para responder 1 (terminar) o 2 (ir_a) segun el umbral T.\n\nBaseline: Llama base sin SFT = 52.3% (siempre dice ir_a)."),
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
    md("## 4. Cargar datos"),
    code("""from datasets import load_dataset

TRAIN_PATH = "/kaggle/input/timonel-banco-a/train_A_sft.jsonl"
VAL_PATH   = "/kaggle/input/timonel-banco-a/val_A_sft.jsonl"

dataset_train = load_dataset("json", data_files=TRAIN_PATH, split="train")
dataset_val = load_dataset("json", data_files=VAL_PATH, split="train")
print(f"Train: {len(dataset_train)} | Val: {len(dataset_val)}")"""),
    md("## 5. Chat template"),
    code("""from unsloth import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="llama-3.1")

def formatear(ejemplo):
    return {"text": tokenizer.apply_chat_template(ejemplo["messages"], tokenize=False, add_generation_prompt=False)}

dataset_train = dataset_train.map(formatear)
dataset_val = dataset_val.map(formatear)
print(dataset_train[0]["text"][:500])"""),
    md("## 6. Entrenamiento"),
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
        warmup_steps = 10, max_steps = 150,
        learning_rate = 2e-4,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 10,
        eval_strategy = "steps", eval_steps = 50,
        save_strategy = "steps", save_steps = 50,
        optim = "adamw_8bit", weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407, output_dir = "outputs_A", report_to = "none",
    ),
)
stats = trainer.train()
print(stats)"""),
    md("## 7. Guardar"),
    code("""model.save_pretrained("timonel_lora_banco_A")
tokenizer.save_pretrained("timonel_lora_banco_A")
!ls -la timonel_lora_banco_A/"""),
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

with open("timonel_sft_banco_A_kaggle.ipynb", "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("[OK] Notebook generado")
