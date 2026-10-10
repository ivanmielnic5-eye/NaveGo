#!/usr/bin/env python3
"""comparar_variantes.py - Compara las 4 variantes de prompt sobre CC002.

Uso:
    python3 comparar_variantes.py --n 20
    python3 comparar_variantes.py --n 20 --modelo llama3.1:8b
"""
import argparse
import json
import math
import random
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, ".")

from variantes_prompt import prompt_VA, prompt_VB, prompt_VC, prompt_VD
from simulador_polaris import Barco

OLLAMA_CHAT = "http://127.0.0.1:11434/api/chat"
VARIANTES = {"VA": prompt_VA, "VB": prompt_VB, "VC": prompt_VC, "VD": prompt_VD}
ACCIONES = ["corregir_rumbo", "ir_a_punto", "frenar", "terminar"]
SYSTEM = "Sos un agente de navegacion. Respondes EXCLUSIVAMENTE con el esquema: {\"accion\": \"corregir_rumbo|ir_a_punto|frenar|terminar\", \"parametro\": <numero o [x,z] o null>}. No agregues otras claves."


def consultar(prompt, modelo, timeout_s=120):
    data = json.dumps({
        "model": modelo,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 2048, "temperature": 0, "seed": 555, "num_predict": 80, "num_batch": 512},
    }).encode()
    req = urllib.request.Request(OLLAMA_CHAT, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            resp = json.load(r)
        return resp.get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"ERROR: {e}"


def extraer_json(texto):
    i = texto.find("{")
    j = texto.rfind("}")
    if i == -1 or j == -1 or j <= i:
        return None
    try:
        return json.loads(texto[i:j+1])
    except Exception:
        return None


def cargar_banco(split="desarrollo"):
    ctxs = [json.loads(l) for l in open("banco_cc002/banco_contextos.jsonl")]
    lbls = [json.loads(l) for l in open("banco_cc002/banco_etiquetas.jsonl")]
    by_id = {l["context_id"]: l for l in lbls}
    return [(c, by_id[c["context_id"]]) for c in ctxs if by_id.get(c["context_id"], {}).get("split") == split]


def muestrear_balanceado(items, n, seed=777):
    rng = random.Random(seed)
    por_accion = defaultdict(list)
    for c, l in items:
        por_accion[l["accion_optima"]].append((c, l))
    por_accion_n = n // 4
    muestra = []
    for acc, lst in por_accion.items():
        rng.shuffle(lst)
        muestra.extend(lst[:por_accion_n])
    rng.shuffle(muestra)
    return muestra


def barco_desde_state(state):
    b = Barco()
    b.pos_x = state["pos_x"]
    b.pos_z = state["pos_z"]
    b.yaw = math.radians(state["hdg"])
    sog_ms = state["sog"] / 1.94384449
    b.vel_x = math.sin(b.yaw) * sog_ms
    b.vel_z = -math.cos(b.yaw) * sog_ms
    b.viento_intensidad_kn = state["viento_kn"]
    b.viento_direccion_deg = state["viento_dir"]
    return b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--modelo", default="llama3.1:8b")
    ap.add_argument("--out", default="comparacion_variantes.json")
    ap.add_argument("--seed", type=int, default=777)
    args = ap.parse_args()

    items = cargar_banco("desarrollo")
    muestra = muestrear_balanceado(items, args.n, args.seed)
    print(f"[cmp] modelo: {args.modelo}")
    print(f"[cmp] muestra: {len(muestra)} ({args.n//4} por accion)")
    print()

    resultados = {}
    for nombre, fn in VARIANTES.items():
        print(f"=== {nombre} ===")
        aciertos = 0
        uso = Counter()
        por_acc_ok = Counter()
        por_acc_tot = Counter()
        t0 = datetime.now()
        for i, (ctx, lbl) in enumerate(muestra):
            state = ctx["state"]
            b = barco_desde_state(state)
            dx = state["meta_x"] - b.pos_x
            dz = state["meta_z"] - b.pos_z
            dist = math.sqrt(dx*dx + dz*dz)
            rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0

            prompt = fn(
                meta_x=state["meta_x"], meta_z=state["meta_z"],
                pos_x=b.pos_x, pos_z=b.pos_z,
                hdg=b.heading_deg(), sog=b.sog_kn(),
                dist=dist, rumbo_meta=rumbo,
                viento_kn=b.viento_intensidad_kn, viento_dir=b.viento_direccion_deg,
            )
            crudo = consultar(prompt, args.modelo)
            parsed = extraer_json(crudo) if not crudo.startswith("ERROR") else None
            pred = parsed.get("accion", "_error_") if parsed else "_error_"
            true = lbl["accion_optima"]
            ok = (pred == true)
            if ok:
                aciertos += 1
                por_acc_ok[true] += 1
            por_acc_tot[true] += 1
            uso[pred] += 1

        elapsed = (datetime.now() - t0).total_seconds()
        acc = aciertos / len(muestra) if muestra else 0
        print(f"  accuracy: {aciertos}/{len(muestra)} = {acc*100:.1f}%")
        print(f"  por accion: " + ", ".join([f"{a}:{por_acc_ok.get(a,0)}/{por_acc_tot.get(a,0)}" for a in ACCIONES]))
        print(f"  uso de acciones: {dict(uso)}")
        print(f"  duracion: {elapsed:.1f}s")
        print()
        resultados[nombre] = {
            "accuracy": round(acc, 4),
            "aciertos": aciertos,
            "total": len(muestra),
            "por_accion_ok": dict(por_acc_ok),
            "por_accion_total": dict(por_acc_tot),
            "uso_acciones": dict(uso),
            "duracion_s": round(elapsed, 1),
        }

    with open(args.out, "w") as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "modelo": args.modelo,
            "seed": args.seed,
            "n": args.n,
            "resultados": resultados,
        }, f, indent=2, default=str)
    print(f"[cmp] resultados en {args.out}")

    print()
    print("=== RESUMEN ===")
    for nombre, r in resultados.items():
        print(f"  {nombre}: {r['accuracy']*100:.1f}% ({r['aciertos']}/{r['total']}) - uso: {r['uso_acciones']}")


if __name__ == "__main__":
    main()
