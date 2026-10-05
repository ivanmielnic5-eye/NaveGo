#!/usr/bin/env python3
import json
import math
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from simulador_polaris import Barco
from agente_llm import decidir_con_qwen

BANCO = Path(__file__).parent / "COMMON_CONTEXT_001.json"
CICLOS = 20


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

def main():
    banco = json.load(open(BANCO))
    ctx = banco[1]
    state = ctx["state"]
    history = ctx["history"]
    b = barco_desde_estado(state)

    print("=== COLD/WARM INVESTIGATION 001 ===")
    print("Contexto 1, " + str(CICLOS) + " ciclos de cold-start")
    print()
    resultados = []
    for i in range(CICLOS):
        print("--- ciclo " + str(i + 1) + "/" + str(CICLOS) + " ---")
        # Stop ollama
        subprocess.run(["ollama", "stop", "qwen2.5-coder:1.5b"], capture_output=True)
        time.sleep(2)
        # Primera llamada (cold)
        t0 = time.time()
        d_cold = decidir_con_qwen(state["meta_x"], state["meta_z"], b, conn=None, history=history)
        t_cold = time.time() - t0
        # Segunda llamada (warm)
        t0 = time.time()
        d_warm = decidir_con_qwen(state["meta_x"], state["meta_z"], b, conn=None, history=history)
        t_warm = time.time() - t0
        cold_str = str(d_cold.get("accion", "?")) + "|" + str(d_cold.get("parametro", "?"))
        warm_str = str(d_warm.get("accion", "?")) + "|" + str(d_warm.get("parametro", "?"))
        marca = "CAMBIA" if cold_str != warm_str else "igual"
        print("  cold (" + str(round(t_cold, 1)) + "s): " + cold_str)
        print("  warm (" + str(round(t_warm, 1)) + "s): " + warm_str)
        print("  " + marca)
        resultados.append({"ciclo": i + 1, "cold": cold_str, "warm": warm_str, "cambia": cold_str != warm_str})

    # Resumen
    cambia_count = sum(1 for r in resultados if r["cambia"])
    print()
    print("=== RESUMEN ===")
    print("Ciclos: " + str(CICLOS))
    print("Veces que cold != warm: " + str(cambia_count) + "/" + str(CICLOS))
    from collections import Counter
    cold_dist = Counter(r["cold"] for r in resultados)
    warm_dist = Counter(r["warm"] for r in resultados)
    print("Distribucion de cold:")
    for k, v in cold_dist.items():
        print("  " + str(v) + "/" + str(CICLOS) + " -> " + k)
    print("Distribucion de warm:")
    for k, v in warm_dist.items():
        print("  " + str(v) + "/" + str(CICLOS) + " -> " + k)


if __name__ == "__main__":
    main()

