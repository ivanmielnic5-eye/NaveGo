#!/usr/bin/env python3
import argparse, json, math, re, sys, time, urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
sys.path.insert(0, ".")
from prompt_banco_A import armar_prompt_A_orden_directo, armar_prompt_A_orden_invertido

OLLAMA_CHAT = "http://127.0.0.1:11434/api/chat"
SYSTEM_PROMPT = "Sos un timonel. Respondes UNICAMENTE con el numero 1 o 2. Sin texto, sin JSON, sin explicacion. Solo el numero."

def consultar_llm(prompt, modelo, timeout_s=120):
    data = json.dumps({
        "model": modelo,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"num_ctx": 2048, "temperature": 0, "seed": 555,
                    "num_predict": 8, "num_batch": 512},
    }).encode()
    req = urllib.request.Request(OLLAMA_CHAT, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            resp = json.load(r)
        return resp.get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"ERROR: {e}"

def extraer_opcion(texto):
    if not texto or texto.startswith("ERROR"):
        return None
    m = re.search(r"[12]", texto)
    return int(m.group(0)) if m else None


def mapear_opcion_a_accion(opcion, orden):
    if opcion == 1:
        return orden[0]
    elif opcion == 2:
        return orden[1]
    return None


def evaluar_contexto(estado, modelo):
    d = estado["d"]
    T = estado["T"]

    prompt_a = armar_prompt_A_orden_directo(d, T)
    crudo_a = consultar_llm(prompt_a, modelo)
    opcion_a = extraer_opcion(crudo_a)
    accion_a = mapear_opcion_a_accion(opcion_a, ["terminar", "ir_a"])

    prompt_b = armar_prompt_A_orden_invertido(d, T)
    crudo_b = consultar_llm(prompt_b, modelo)
    opcion_b = extraer_opcion(crudo_b)
    accion_b = mapear_opcion_a_accion(opcion_b, ["ir_a", "terminar"])

    consistente = (accion_a == accion_b and accion_a is not None)
    decision = accion_a if consistente else None

    p_term_a = 1.0 if accion_a == "terminar" else 0.0
    p_term_b = 1.0 if accion_b == "terminar" else 0.0
    p_term_unbiased = (p_term_a + p_term_b) / 2.0

    p_opt1_directo = 1.0 if opcion_a == 1 else 0.0
    p_opt1_invertido = 1.0 if opcion_b == 1 else 0.0
    pbi_contexto = (p_opt1_directo + p_opt1_invertido) / 2.0 - 0.5

    return {
        "d": d, "T": T, "banda": estado["banda"],
        "accion_optima": estado["accion_optima"],
        "opcion_directo": opcion_a, "opcion_invertido": opcion_b,
        "accion_directo": accion_a, "accion_invertido": accion_b,
        "consistente": consistente, "decision": decision,
        "acierto": (decision == estado["accion_optima"]) if consistente else False,
        "p_term_unbiased": p_term_unbiased,
        "pbi_contexto": pbi_contexto,
        "crudo_directo": crudo_a[:100], "crudo_invertido": crudo_b[:100],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--banco", default="banco_A/confirmatorio.jsonl")
    ap.add_argument("--modelo", default="llama3.1:8b")
    ap.add_argument("--limite", type=int, default=None)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--out", default="runner_banco_A_resultados.jsonl")
    args = ap.parse_args()

    contextos = [json.loads(l) for l in open(args.banco)]
    if args.limite:
        contextos = contextos[args.offset:]
    if args.limite:
        contextos = contextos[:args.limite]

    print(f"[runner] banco: {args.banco}")
    print(f"[runner] modelo: {args.modelo}")
    print(f"[runner] contextos: {len(contextos)}")
    print()

    resultados = []
    t0 = time.time()
    for i, e in enumerate(contextos):
        r = evaluar_contexto(e, args.modelo)
        resultados.append(r)
        if (i + 1) % 10 == 0:
            elapsed = time.time() - t0
            eta = elapsed / (i + 1) * (len(contextos) - i - 1)
            print(f"  [{i+1}/{len(contextos)}] t={elapsed:.0f}s ETA={eta:.0f}s")
        if (i + 1) % 50 == 0:
            with open(args.out, "w") as f:
                for x in resultados:
                    f.write(json.dumps(x) + "\n")

    with open(args.out, "w") as f:
        for x in resultados:
            f.write(json.dumps(x) + "\n")

    print()
    print(f"[runner] terminado en {time.time()-t0:.0f}s")
    print(f"[runner] resultados en {args.out}")
    print()

    total = len(resultados)
    consistentes = sum(1 for r in resultados if r["consistente"])
    aciertos = sum(1 for r in resultados if r["acierto"])
    pbi_promedio = sum(r["pbi_contexto"] for r in resultados) / max(total, 1)

    print("=== RESUMEN ===")
    print(f"  Contextos: {total}")
    print(f"  Consistentes: {consistentes}/{total} ({100*consistentes/max(total,1):.1f}%)")
    print(f"  Accuracy (sobre consistentes): {aciertos}/{consistentes} = {100*aciertos/max(consistentes,1):.1f}%")
    print(f"  PBI promedio: {pbi_promedio:+.4f} (ideal 0)")

    print()
    print("=== POR BANDA ===")
    por_banda = {}
    for r in resultados:
        por_banda.setdefault(r["banda"], []).append(r)
    for banda in ["muy_cerca", "cerca", "critica", "lejos", "muy_lejos"]:
        if banda not in por_banda:
            continue
        rs = por_banda[banda]
        n = len(rs)
        aciertos_b = sum(1 for r in rs if r["acierto"])
        cons = sum(1 for r in rs if r["consistente"])
        p_term_avg = sum(r["p_term_unbiased"] for r in rs) / n
        print(f"  {banda:10s}: n={n:3d} aciertos={aciertos_b:3d} consistentes={cons:3d} p_term={p_term_avg:.3f}")

    print()
    print("=== POR T ===")
    por_T = {}
    for r in resultados:
        por_T.setdefault(r["T"], []).append(r)
    for T in sorted(por_T.keys()):
        rs = por_T[T]
        n = len(rs)
        aciertos_t = sum(1 for r in rs if r["acierto"])
        print(f"  T={T}: n={n} aciertos={aciertos_t} ({100*aciertos_t/n:.1f}%)")


if __name__ == "__main__":
    main()
