#!/usr/bin/env python3
"""preparar_sft_A3.py - Convierte bancoA3 a formato SFT (messages).

Salida:
- bancoA3/train_sft.jsonl
- bancoA3/val_sft.jsonl

Formato por ejemplo:
  {"messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "<prompt>"},
    {"role": "assistant", "content": "{\"accion\": \"<label>\"}"}
  ]}
"""
import json
from pathlib import Path

SYSTEM = ("Sos el timonel de un velero autonomo. Respondes "
          "UNICAMENTE con el JSON pedido, sin texto adicional.")

BASE = Path("bancoA3")


def convertir(path_in, path_out):
    with open(path_in, encoding="utf-8") as f:
        ctxs = [json.loads(l) for l in f]
    with open(path_out, "w", encoding="utf-8") as f:
        for c in ctxs:
            respuesta = json.dumps({"accion": c["label"]}, ensure_ascii=False)
            ejemplo = {
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": c["prompt"]},
                    {"role": "assistant", "content": respuesta},
                ]
            }
            f.write(json.dumps(ejemplo, ensure_ascii=False) + "\n")
    return len(ctxs)


def main():
    n_train = convertir(BASE / "train.jsonl", BASE / "train_sft.jsonl")
    n_val = convertir(BASE / "val.jsonl", BASE / "val_sft.jsonl")
    print(f"train_sft: {n_train}")
    print(f"val_sft:   {n_val}")


if __name__ == "__main__":
    main()
