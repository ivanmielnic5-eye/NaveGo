#!/usr/bin/env python3

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from simulador_polaris import Barco
from agente_llm import decidir_con_qwen
from memoria import conectar

BANCO = Path(__file__).parent / "COMMON_CONTEXT_001.json"
REPS = 10


def barco_desde_estado(state):
    b = Barco()
    b.pos_x = state["pos_x"]
    b.pos_z = state["pos_z"]
    b.yaw = math.radians(state["hdg"])
    sog_ms = state["sog"] / 1.94384449
    b.vel_x = math.sin(b.yaw) * sog_ms
    b.vel_z = -math.cos(b.yaw) * sog_ms
    b.viento_intensidad_kn = state.get("viento_kn", 0.0)
    b.viento_direccion_deg = state.get("viento_dir", 0.0)
    return b


def consultar(state, history, conn, usar_memoria):
    b = barco_desde_estado(state)
    history_arg = history if history else None
    conn_arg = conn if usar_memoria else None
    return decidir_con_qwen(state["meta_x"], state["meta_z"], b, conn=conn_arg, history=history_arg)


def main():
    banco = json.load(open(BANCO))
    contextos = banco[:5]
    conn = conectar()
    print("=== DETERMINISM GATE 001 ===")
    print("5 contextos x 3 condiciones x " + str(REPS) + " reps = " + str(5 * 3 * REPS) + " llamadas")
    print()
    resultados = []
    for i, ctx in enumerate(contextos):
        state = ctx["state"]
        history = ctx["history"]
        print("--- contexto " + str(i) + " (fuente=" + ctx.get("fuente", "?") + ") ---")
        for cond in ["A", "A_prima", "B"]:
            decisiones = []
            for r in range(REPS):
                if cond == "A":
                    d = consultar(state, [], None, usar_memoria=False)
                elif cond == "A_prima":
                    d = consultar(state, history, None, usar_memoria=False)
                else:
                    d = consultar(state, history, conn, usar_memoria=True)
                decisiones.append(str(d.get("accion", "?")) + "|" + str(d.get("parametro", "?")))
            unicas = set(decisiones)
            if len(unicas) == 1:
                estado = "PASS"
            else:
                estado = "FAIL (" + str(len(unicas)) + " decisiones distintas)"
            print("  " + cond.ljust(8) + ": " + estado)
            for u in unicas:
                cuenta = decisiones.count(u)
                print("      " + str(cuenta) + "/" + str(REPS) + " -> " + u)
            resultados.append({"contexto": i, "cond": cond, "distintas": len(unicas)})
        print()
    conn.close()
    fallos = sum(1 for r in resultados if r["distintas"] > 1)
    total = len(resultados)
    print("=== RESUMEN ===")
    print("Combinaciones evaluadas: " + str(total))
    print("Fallos: " + str(fallos))
    if fallos == 0:
        print("VEREDICTO: PASS")
    else:
        print("VEREDICTO: FAIL")


if __name__ == "__main__":
    main()
