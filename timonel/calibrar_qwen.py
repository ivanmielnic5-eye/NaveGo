#!/usr/bin/env python3
"""calibrar_qwen.py - Mide accuracy de Qwen sobre el banco CC002.

Uso:
    python3 calibrar_qwen.py --n 30
    python3 calibrar_qwen.py --n 30 --modelo qwen2.5-coder:3b
"""
import argparse
import json
import math
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, ".")

import agente_llm
from simulador_polaris import Barco


def cargar_banco(split="desarrollo"):
    ctxs = [json.loads(l) for l in open("banco_cc002/banco_contextos.jsonl")]
    lbls = [json.loads(l) for l in open("banco_cc002/banco_etiquetas.jsonl")]
    lbls_by_id = {l["context_id"]: l for l in lbls}
    filtrados = []
    for c in ctxs:
        lbl = lbls_by_id.get(c["context_id"])
        if lbl and lbl.get("split") == split:
            filtrados.append((c, lbl))
    return filtrados


def muestrear_balanceado(items, n, seed=42):
    """Muestrea n items balanceados por accion_optima."""
    rng = random.Random(seed)
    por_accion = defaultdict(list)
    for c, lbl in items:
        por_accion[lbl["accion_optima"]].append((c, lbl))
    por_accion_n = n // 4
    muestra = []
    for accion, lista in por_accion.items():
        rng.shuffle(lista)
        muestra.extend(lista[:por_accion_n])
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


def comparar_acciones(pred_accion, pred_param, true_accion, true_param):
    """Devuelve dict con aciertos."""
    accion_ok = (pred_accion == true_accion)
    param_ok = None
    if accion_ok and true_accion == "corregir_rumbo" and pred_param is not None and true_param is not None:
        try:
            d = abs((float(pred_param) - float(true_param) + 540) % 360 - 180)
            param_ok = (d <= 8.0)
        except Exception:
            param_ok = False
    return {"accion_ok": accion_ok, "param_ok": param_ok}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--modelo", default=None)
    ap.add_argument("--split", default="desarrollo")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="calibracion_qwen_resultado.json")
    args = ap.parse_args()

    if args.modelo:
        agente_llm.MODELO_DECISION = args.modelo
        print("[calib] modelo: " + args.modelo)
    else:
        print("[calib] modelo default: " + agente_llm.MODELO_DECISION)

    items = cargar_banco(args.split)
    print("[calib] contextos en " + args.split + ": " + str(len(items)))

    muestra = muestrear_balanceado(items, args.n, seed=args.seed)
    print("[calib] muestra: " + str(len(muestra)) + " (" + str(args.n // 4) + " por accion)")
    print()

    resultados = []
    aciertos_accion = 0
    aciertos_param = 0
    evaluados_param = 0
    conf_mat = defaultdict(Counter)
    por_accion_total = Counter()
    por_accion_ok = Counter()
    por_familia_total = Counter()
    por_familia_ok = Counter()

    t0 = datetime.now()
    for i, (ctx, lbl) in enumerate(muestra):
        state = ctx["state"]
        true_accion = lbl["accion_optima"]
        true_param = lbl["parametro_oraculo"]
        familia = lbl["familia"]

        b = barco_desde_state(state)
        try:
            r = agente_llm.decidir_con_qwen(state["meta_x"], state["meta_z"], b, conn=None, history=None)
        except Exception as e:
            print("  [" + str(i+1) + "] ERROR: " + str(e))
            continue

        pred_accion = r.get("accion", "_error_")
        pred_param = r.get("parametro")
        comp = comparar_acciones(pred_accion, pred_param, true_accion, true_param)

        if comp["accion_ok"]:
            aciertos_accion += 1
            por_accion_ok[true_accion] += 1
            por_familia_ok[familia] += 1
        if comp["param_ok"] is not None:
            evaluados_param += 1
            if comp["param_ok"]:
                aciertos_param += 1

        por_accion_total[true_accion] += 1
        por_familia_total[familia] += 1
        conf_mat[true_accion][pred_accion] += 1

        marca = "OK " if comp["accion_ok"] else "X  "
        print("  [" + str(i+1) + "/" + str(len(muestra)) + "] " + marca + "true=" + true_accion + " pred=" + pred_accion + " fam=" + familia)

        resultados.append({
            "context_id": ctx["context_id"],
            "true_accion": true_accion,
            "pred_accion": pred_accion,
            "pred_param": pred_param,
            "true_param": true_param,
            "accion_ok": comp["accion_ok"],
            "param_ok": comp["param_ok"],
            "familia": familia,
        })

    elapsed = (datetime.now() - t0).total_seconds()
    n_total = len(resultados)
    print()
    print("=== RESUMEN ===")
    print("[calib] duracion: " + str(round(elapsed, 1)) + "s")
    print("[calib] evaluados: " + str(n_total))
    if n_total > 0:
        print("[calib] accuracy accion: " + str(aciertos_accion) + "/" + str(n_total) + " = " + str(round(100 * aciertos_accion / n_total, 1)) + "%")
    if evaluados_param > 0:
        print("[calib] accuracy parametro (corregir_rumbo): " + str(aciertos_param) + "/" + str(evaluados_param) + " = " + str(round(100 * aciertos_param / evaluados_param, 1)) + "%")
    print()
    print("Por accion:")
    for accion in ["corregir_rumbo", "ir_a_punto", "frenar", "terminar"]:
        tot = por_accion_total.get(accion, 0)
        ok = por_accion_ok.get(accion, 0)
        if tot > 0:
            print("  " + accion + ": " + str(ok) + "/" + str(tot) + " = " + str(round(100 * ok / tot, 1)) + "%")
    print()
    print("Por familia:")
    for fam in ["terminal", "cerca", "medio", "lejos"]:
        tot = por_familia_total.get(fam, 0)
        ok = por_familia_ok.get(fam, 0)
        if tot > 0:
            print("  " + fam + ": " + str(ok) + "/" + str(tot) + " = " + str(round(100 * ok / tot, 1)) + "%")
    print()
    print("Matriz de confusion (true -> pred):")
    for true in ["corregir_rumbo", "ir_a_punto", "frenar", "terminar"]:
        if true in conf_mat:
            preds = dict(conf_mat[true])
            print("  " + true + ": " + str(preds))

    out = {
        "fecha": datetime.now().isoformat(),
        "modelo": agente_llm.MODELO_DECISION,
        "split": args.split,
        "n_muestra": len(muestra),
        "accuracy_accion": round(aciertos_accion / n_total, 4) if n_total > 0 else 0,
        "accuracy_parametro": round(aciertos_param / evaluados_param, 4) if evaluados_param > 0 else None,
        "por_accion": {a: {"ok": por_accion_ok.get(a, 0), "total": por_accion_total.get(a, 0)} for a in ["corregir_rumbo", "ir_a_punto", "frenar", "terminar"]},
        "por_familia": {f: {"ok": por_familia_ok.get(f, 0), "total": por_familia_total.get(f, 0)} for f in ["terminal", "cerca", "medio", "lejos"]},
        "confusion": {t: dict(c) for t, c in conf_mat.items()},
        "resultados": resultados,
        "duracion_s": round(elapsed, 1),
    }
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print("[calib] resultados en " + args.out)


if __name__ == "__main__":
    main()
