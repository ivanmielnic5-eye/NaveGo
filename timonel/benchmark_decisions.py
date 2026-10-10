#!/usr/bin/env python3
"""
benchmark_decisions.py - Benchmark LOCAL de decisiones (memo 62).

Carga COMMON_CONTEXT_001.json (350 contextos congelados).
Para cada contexto corre 3 condiciones:
    A       = estado solo, sin historial, sin memoria
    A_prima = estado + historial, sin memoria
    B       = estado + historial + memoria

Cada decision se compara contra el oraculo (regret + safety).
Guarda resultados en JSON.

Uso:
    python3 benchmark_decisions.py --n 50
"""

import argparse
import json
import math
import time
from pathlib import Path

from simulador_polaris import Barco
from agente_llm import decidir_con_qwen
from memoria import conectar
from oraculo import Oracle


BANCO_DEFAULT = Path(__file__).parent / "COMMON_CONTEXT_001.json"


def barco_desde_estado(state: dict) -> Barco:
    """Construye un Barco a partir de un estado del banco."""
    b = Barco()
    b.pos_x = state["pos_x"]
    b.pos_z = state["pos_z"]
    b.yaw = math.radians(state["hdg"])
    sog_ms = state["sog"] / 1.94384449
    # Aproximar velocidad hacia la direccion del heading
    b.vel_x = math.sin(b.yaw) * sog_ms
    b.vel_z = -math.cos(b.yaw) * sog_ms
    b.viento_intensidad_kn = state.get("viento_kn", 0.0)
    b.viento_direccion_deg = state.get("viento_dir", 0.0)
    return b


def consultar_decision(state, history, conn, usar_memoria):
    """Pide una decision a Qwen desde un estado + historial dado."""
    b = barco_desde_estado(state)
    meta_x = state["meta_x"]
    meta_z = state["meta_z"]
    history_arg = history if history else None
    conn_arg = conn if usar_memoria else None
    return decidir_con_qwen(meta_x, meta_z, b, conn=conn_arg, history=history_arg)


def evaluar_decision_con_oraculo(state, decision_qwen):
    """Corre el oraculo sobre el estado y compara con la decision de Qwen."""
    b = barco_desde_estado(state)
    orac = Oracle()
    resultados = orac.evaluar_todas(b, state["meta_x"], state["meta_z"])
    # resultados[0] es la mejor receta segun el oraculo
    mejor = resultados[0].receta
    h_max = round(max(orac.horizontes), 1)
    progreso_mejor = resultados[0].progreso_por_horizonte.get(h_max, 0.0)

    # Buscar la decision de Qwen en los resultados
    progreso_qwen = None
    safety_violation_qwen = False
    for r in resultados:
        if r.receta == decision_qwen:
            progreso_qwen = r.progreso_por_horizonte.get(h_max, 0.0)
            safety_violation_qwen = r.safety_violation
            break

    if progreso_qwen is None:
        # La decision de Qwen no coincide con ninguna receta conocida
        return {
            "oraculo_mejor": mejor,
            "regret": None,
            "safety_violation": None,
            "error": "decision_qwen_desconocida",
        }

    regret = round(progreso_mejor - progreso_qwen, 2)
    return {
        "oraculo_mejor": mejor,
        "progreso_oraculo": progreso_mejor,
        "progreso_qwen": progreso_qwen,
        "regret": regret,
        "safety_violation": safety_violation_qwen,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10, help="Cuantos contextos evaluar")
    parser.add_argument("--offset", type=int, default=0, help="Desde que contexto empezar")
    parser.add_argument("--banco", type=str, default=str(BANCO_DEFAULT))
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    # Warm-up: descartar la primera corrida (memo 63, seccion 8)
    print("Warm-up...")
    from timonel_python import AgenteTimonel as _AT
    _warm = _AT(meta_x=100, meta_z=100, timeout_s=10, usar_llm=True, conn=None, max_pasos=1)
    _warm.correr(verbose=False)
    print("Warm-up listo.")
    print()

    banco = json.load(open(args.banco))
    print("Banco cargado: " + str(len(banco)) + " contextos")

    # Tomar los primeros N contextos
    contextos = banco[args.offset:args.offset+args.n]
    conn = conectar()

    resultados = []
    t0 = time.time()

    for i, ctx in enumerate(contextos):
        state = ctx["state"]
        history = ctx["history"]

        # Tres condiciones
        dec_A = consultar_decision(state, [], None, usar_memoria=False)
        dec_Ap = consultar_decision(state, history, None, usar_memoria=False)
        dec_B = consultar_decision(state, history, conn, usar_memoria=True)

        # Evaluar con oraculo
        eval_A = evaluar_decision_con_oraculo(state, dec_A.get("accion", "?"))
        eval_Ap = evaluar_decision_con_oraculo(state, dec_Ap.get("accion", "?"))
        eval_B = evaluar_decision_con_oraculo(state, dec_B.get("accion", "?"))

        resultados.append({
            "contexto_id": i,
            "fuente_contexto": ctx.get("fuente", "?"),
            "estado": state,
            "historial_len": len(history),
            "dec_A": dec_A,
            "dec_Ap": dec_Ap,
            "dec_B": dec_B,
            "eval_A": eval_A,
            "eval_Ap": eval_Ap,
            "eval_B": eval_B,
        })

        print("[" + str(i + 1).rjust(3) + "/" + str(len(contextos)) + "] "
              + "A=" + str(dec_A.get("accion", "?")) + " "
              + "Ap=" + str(dec_Ap.get("accion", "?")) + " "
              + "B=" + str(dec_B.get("accion", "?"))
              + " | regret_A=" + str(eval_A.get("regret")) 
              + " regret_Ap=" + str(eval_Ap.get("regret"))
              + " regret_B=" + str(eval_B.get("regret")))

    duracion = time.time() - t0
    print()
    print("=== RESUMEN ===")
    print("Contextos evaluados: " + str(len(resultados)))
    print("Duracion: " + str(round(duracion, 1)) + "s")

    if args.output:
        out_path = Path(args.output)
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(resultados, fh, indent=2, ensure_ascii=False)
        print("Guardado en: " + str(out_path))

    conn.close()
