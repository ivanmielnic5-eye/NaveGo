#!/usr/bin/env python3
"""runtime_carryover.py - RUNTIME-CARRYOVER-001 (memo 65)."""

import hashlib
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from simulador_polaris import Barco
from agente_llm import decidir_con_qwen, armar_prompt, formatear_historial

BANCO = Path(__file__).parent / "COMMON_CONTEXT_001.json"


def cargar_contexto(indice):
    banco = json.load(open(BANCO))
    return banco[indice]


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


def hash_prompt(state, history, con_memoria=False):
    """Reconstruye el prompt como lo haria agente_llm y devuelve su hash."""
    b = barco_desde_estado(state)
    dx = state["meta_x"] - b.pos_x
    dz = state["meta_z"] - b.pos_z
    dist = math.sqrt(dx*dx + dz*dz)
    rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
    hdg = b.heading_deg()
    sog = b.sog_kn()
    bloque_hist = formatear_historial(history) if history else ""
    bloque_exp = ""
    prompt = armar_prompt(
        meta_x=state["meta_x"], meta_z=state["meta_z"],
        pos_x=b.pos_x, pos_z=b.pos_z, hdg=hdg, sog=sog,
        dist=dist, rumbo_hacia_meta=rumbo,
        bloque_experiencias=bloque_exp,
        bloque_historial=bloque_hist,
    )
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]


def consultar(state, history, conn, usar_memoria):
    b = barco_desde_estado(state)
    h_arg = history if history else None
    c_arg = conn if usar_memoria else None
    t0 = time.time()
    d = decidir_con_qwen(state["meta_x"], state["meta_z"], b, conn=c_arg, history=h_arg)
    t1 = time.time()
    return d, t1 - t0

def test_1_repeticion_pura():
    """S* S* S* S* S* - sin prompts intermedios."""
    print("=== TEST 1: repeticion pura ===")
    ctx = cargar_contexto(1)
    state = ctx["state"]
    history = ctx["history"]
    resultados = []
    for i in range(5):
        d, dur = consultar(state, history, None, usar_memoria=False)
        s = str(d.get("accion")) + "|" + str(d.get("parametro"))
        print(f"  {i+1}: {s} ({dur:.2f}s)")
        resultados.append(s)
    distintos = set(resultados)
    print(f"  Distintos: {len(distintos)}")
    print()
    return {"test": 1, "resultados": resultados, "distintos": len(distintos)}


def test_2_prompt_neutral():
    """S* N S* N S* - con prompts neutrales entre medio."""
    print("=== TEST 2: prompt neutral entre medio ===")
    ctx = cargar_contexto(1)
    state = ctx["state"]
    history = ctx["history"]
    resultados = []
    for i in range(4):
        d, dur = consultar(state, history, None, usar_memoria=False)
        s = str(d.get("accion")) + "|" + str(d.get("parametro"))
        print(f"  S* {i+1}: {s} ({dur:.2f}s)")
        resultados.append(s)
        if i < 3:
            import urllib.request
            data = json.dumps({"model": "qwen2.5-coder:1.5b", "prompt": "responde solo: hola", "stream": False, "options": {"num_predict": 5, "temperature": 0, "seed": 555}}).encode()
            req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=data, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    json.load(r)
                print(f"    (neutral {i+1} ejecutado)")
            except Exception as e:
                print(f"    (neutral {i+1} error: {e})")
    distintos = set(resultados)
    print(f"  Distintos: {len(distintos)}")
    print()
    return {"test": 2, "resultados": resultados, "distintos": len(distintos)}
def test_precedencia(nombre_test, condicion_previa):
    """Ejecuta [previa, S*, previa, S*, previa, S*]."""
    print(f"=== {nombre_test}: precedencia {condicion_previa} ===")
    ctx = cargar_contexto(1)
    state = ctx["state"]
    history = ctx["history"]
    # Elegir un contexto previo distinto al de S* (uso el contexto 5)
    ctx_previa = cargar_contexto(5)
    state_previa = ctx_previa["state"]
    history_previa = ctx_previa["history"]
    resultados = []
    for i in range(3):
        # Ejecutar condicion previa
        if condicion_previa == "A":
            consultar(state_previa, [], None, usar_memoria=False)
        elif condicion_previa == "A_prima":
            consultar(state_previa, history_previa, None, usar_memoria=False)
        elif condicion_previa == "B":
            from memoria import conectar
            conn = conectar()
            consultar(state_previa, history_previa, conn, usar_memoria=True)
            conn.close()
        # Ejecutar S*
        d, dur = consultar(state, history, None, usar_memoria=False)
        s = str(d.get("accion")) + "|" + str(d.get("parametro"))
        print(f"  ciclo {i+1}: previa={condicion_previa} S*={s} ({dur:.2f}s)")
        resultados.append(s)
    distintos = set(resultados)
    print(f"  Distintos: {len(distintos)}")
    print()
    return {"test": nombre_test, "previa": condicion_previa, "resultados": resultados, "distintos": len(distintos)}


if __name__ == "__main__":
    print("=== RUNTIME-CARRYOVER-001 ===")
    print("Contexto S*: contexto 1 del banco")

    print("Contexto previo: contexto 5 del banco")

    print()
    todos = []
    todos.append(test_1_repeticion_pura())
    todos.append(test_2_prompt_neutral())
    todos.append(test_precedencia("TEST 3", "A"))
    todos.append(test_precedencia("TEST 4", "A_prima"))
    todos.append(test_precedencia("TEST 5", "B"))
    print("=== RESUMEN ===")
    for t in todos:
        print("  Test " + str(t["test"]) + ": distintos=" + str(t["distintos"]) + " resultados=" + str(t["resultados"]))

    # Verificacion global
    bloqueantes = [t for t in todos if t["distintos"] > 1]
    print()
    if bloqueantes:
        print(f"VEREDICTO: CARRY-OVER DETECTADO en {len(bloqueantes)} tests")
    else:
        print("VEREDICTO: sin carry-over detectable")
