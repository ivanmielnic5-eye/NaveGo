#!/usr/bin/env python3
"""preparar_dataset_sft.py - Genera el dataset de fine-tuning SFT.

Salida:
- sft_dataset/train.jsonl (240 ejemplos)
- sft_dataset/val.jsonl (60 ejemplos)
- sft_dataset/manifiesto.json

Formato por ejemplo (HuggingFace chat template):
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

Referencia: EXPEDIENTE/82_PREREGISTRO_SFT.md
"""
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, ".")

from prompt_hibrido import prompt_hibrido
from admisibilidad import acciones_admisibles

SYSTEM_PROMPT = ("Sos un agente de navegacion. Respondes EXCLUSIVAMENTE con el esquema: "
                 "{\"accion\": \"<nombre>\", \"parametro\": <valor o null>}.")

SEED_SPLIT = 42


def cargar_desarrollo():
    ctxs = [json.loads(l) for l in open("banco_cc002/banco_contextos.jsonl")]
    lbls = [json.loads(l) for l in open("banco_cc002/banco_etiquetas.jsonl")]
    by_id = {l["context_id"]: l for l in lbls}
    return [(c, by_id[c["context_id"]]) for c in ctxs
            if by_id.get(c["context_id"], {}).get("split") == "desarrollo"]


def generar_ejemplo(ctx, lbl):
    state = ctx["state"]
    dx = state["meta_x"] - state["pos_x"]
    dz = state["meta_z"] - state["pos_z"]
    dist = math.sqrt(dx*dx + dz*dz)
    rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0

    admisibles = acciones_admisibles(dist, state["sog"])

    prompt = prompt_hibrido(
        meta_x=state["meta_x"], meta_z=state["meta_z"],
        pos_x=state["pos_x"], pos_z=state["pos_z"],
        hdg=state["hdg"], sog=state["sog"], dist=dist, rumbo_meta=rumbo,
        admisibles=admisibles,
        viento_kn=state["viento_kn"], viento_dir=state["viento_dir"],
    )

    # Normalizar parametro: frenar y terminar van siempre con null
    accion = lbl["accion_optima"]
    param = lbl["parametro_oraculo"]
    if accion in ("frenar", "terminar"):
        param = None
    # ir_a_punto: forzar lista si vino tupla
    if accion == "ir_a_punto" and isinstance(param, (list, tuple)):
        param = list(param)
    # corregir_rumbo: forzar float redondeado
    if accion == "corregir_rumbo" and isinstance(param, (int, float)):
        param = round(float(param), 2)

    respuesta = json.dumps({
        "accion": accion,
        "parametro": param,
    })

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": respuesta},
        ],
        "meta": {
            "context_id": ctx["context_id"],
            "accion": lbl["accion_optima"],
            "familia": lbl["familia"],
        }
    }


def split_estratificado(items, n_train=240, n_val=60, seed=SEED_SPLIT):
    """Split estratificado por accion, agrupando familias."""
    rng = random.Random(seed)
    por_accion = defaultdict(list)
    for ctx, lbl in items:
        por_accion[lbl["accion_optima"]].append((ctx, lbl))

    train, val = [], []
    for accion, lista in por_accion.items():
        rng.shuffle(lista)
        # 80/20 por accion
        n_acc_train = min(int(len(lista) * 0.8), n_train // 4)
        n_acc_val = min(len(lista) - n_acc_train, n_val // 4)
        train.extend(lista[:n_acc_train])
        val.extend(lista[n_acc_train:n_acc_train + n_acc_val])

    rng.shuffle(train)
    rng.shuffle(val)
    return train, val


def main():
    print("[sft] cargando banco de desarrollo...")
    items = cargar_desarrollo()
    print(f"[sft] contextos disponibles: {len(items)}")

    train, val = split_estratificado(items)
    print(f"[sft] train: {len(train)} | val: {len(val)}")

    out_dir = Path("sft_dataset")
    out_dir.mkdir(exist_ok=True)

    # Train
    with open(out_dir / "train.jsonl", "w") as f:
        for ctx, lbl in train:
            ej = generar_ejemplo(ctx, lbl)
            f.write(json.dumps({"messages": ej["messages"]}, ensure_ascii=False) + "\n")

    # Val
    with open(out_dir / "val.jsonl", "w") as f:
        for ctx, lbl in val:
            ej = generar_ejemplo(ctx, lbl)
            f.write(json.dumps({"messages": ej["messages"]}, ensure_ascii=False) + "\n")

    # Manifiesto
    from collections import Counter
    manifiesto = {
        "fecha": datetime.now().isoformat(),
        "seed_split": SEED_SPLIT,
        "n_train": len(train),
        "n_val": len(val),
        "accion_counts_train": dict(Counter(l["accion_optima"] for _, l in train)),
        "accion_counts_val": dict(Counter(l["accion_optima"] for _, l in val)),
        "familia_counts_train": dict(Counter(l["familia"] for _, l in train)),
        "familia_counts_val": dict(Counter(l["familia"] for _, l in val)),
        "system_prompt": SYSTEM_PROMPT,
        "confirmatorio_intacto": True,
    }
    with open(out_dir / "manifiesto.json", "w") as f:
        json.dump(manifiesto, f, indent=2, ensure_ascii=False)

    print(f"[sft] archivos en {out_dir}/")
    print(f"[sft] train por accion: {manifiesto['accion_counts_train']}")
    print(f"[sft] val por accion:   {manifiesto['accion_counts_val']}")


if __name__ == "__main__":
    main()
