#!/usr/bin/env python3
"""auditar_calibracion.py - Audita las respuestas crudas del LLM."""
import json
import math
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, ".")

import agente_llm
from simulador_polaris import Barco


def cargar_banco(split="desarrollo"):
    ctxs = [json.loads(l) for l in open("banco_cc002/banco_contextos.jsonl")]
    lbls = [json.loads(l) for l in open("banco_cc002/banco_etiquetas.jsonl")]
    by_id = {l["context_id"]: l for l in lbls}
    return [(c, by_id[c["context_id"]]) for c in ctxs if by_id.get(c["context_id"], {}).get("split") == split]


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


def consultar_guardando_crudo(prompt, modelo):
    """Llama a Ollama y devuelve (respuesta_cruda, parsed, error)."""
    import urllib.request
    data = json.dumps({
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 2048, "temperature": 0, "seed": 555, "num_predict": 80, "num_batch": 512},
    }).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            response = json.load(r).get("response", "")
    except Exception as e:
        return ("", None, str(e))
    parsed = agente_llm._parsear_respuesta_json(response)
    return (response, parsed, None)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--modelo", default="qwen2.5-coder:1.5b")
    ap.add_argument("--out", default="auditoria_qwen.json")
    args = ap.parse_args()

    items = cargar_banco("desarrollo")
    print("[audit] modelo: " + args.modelo)
    print("[audit] contextos desarrollo: " + str(len(items)))

    # Tomar n contextos variados (2 por accion)
    por_accion = defaultdict(list)
    for c, lbl in items:
        por_accion[lbl["accion_optima"]].append((c, lbl))
    muestra = []
    n_por_accion = max(1, args.n // 4)
    for accion, lista in por_accion.items():
        muestra.extend(lista[:n_por_accion])
    print("[audit] muestra: " + str(len(muestra)) + " (" + str(n_por_accion) + " por accion)")
    print()

    auditorias = []
    for i, (ctx, lbl) in enumerate(muestra):
        state = ctx["state"]
        b = barco_desde_state(state)
        dx = state["meta_x"] - b.pos_x
        dz = state["meta_z"] - b.pos_z
        dist = math.sqrt(dx*dx + dz*dz)
        rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
        hdg = b.heading_deg()
        sog = b.sog_kn()

        prompt = agente_llm.armar_prompt(
            meta_x=state["meta_x"], meta_z=state["meta_z"],
            pos_x=b.pos_x, pos_z=b.pos_z,
            hdg=hdg, sog=sog, dist=dist, rumbo_hacia_meta=rumbo,
            viento_kn=b.viento_intensidad_kn, viento_dir=b.viento_direccion_deg,
        )

        crudo, parsed, err = consultar_guardando_crudo(prompt, args.modelo)

        true_accion = lbl["accion_optima"]
        true_param = lbl["parametro_oraculo"]
        pred_accion = parsed.get("accion", "_error_") if parsed else "_no_parse_"
        pred_param = parsed.get("parametro") if parsed else None
        acierto = (pred_accion == true_accion)

        print("[" + str(i+1) + "/" + str(len(muestra)) + "] true=" + true_accion + " pred=" + pred_accion + " acierto=" + str(acierto))
        print("    crudo: " + repr(crudo[:150]))
        print("    parsed: " + str(parsed))
        print()

        auditorias.append({
            "context_id": ctx["context_id"],
            "familia": lbl["familia"],
            "true_accion": true_accion,
            "true_param": true_param,
            "pred_accion": pred_accion,
            "pred_param": pred_param,
            "acierto": acierto,
            "prompt": prompt,
            "respuesta_cruda": crudo,
            "respuesta_parseada": parsed,
            "error": err,
        })

    with open(args.out, "w") as f:
        json.dump({"fecha": datetime.now().isoformat(), "modelo": args.modelo, "auditorias": auditorias}, f, indent=2, default=str)
    print("[audit] resultados en " + args.out)


if __name__ == "__main__":
    main()
