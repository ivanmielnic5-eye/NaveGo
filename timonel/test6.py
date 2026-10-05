#!/usr/bin/env python3
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from simulador_polaris import Barco
from agente_llm import decidir_con_qwen
from memoria import conectar

banco = json.load(open("COMMON_CONTEXT_001.json"))
S_state = banco[1]["state"]
S_hist = banco[1]["history"]

def barco(state):
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

S_barco = barco(S_state)
ctxs = [banco[5], banco[6], banco[7]]
conn = conectar()

def ejecutar_con_retry(cond, ctx):
    import time
    st = ctx["state"]
    hi = ctx["history"]
    b = barco(st)
    for intento in range(3):
        if cond == "A":
            d = decidir_con_qwen(st["meta_x"], st["meta_z"], b, conn=None, history=None)
        elif cond == "Ap":
            d = decidir_con_qwen(st["meta_x"], st["meta_z"], b, conn=None, history=hi)
        else:
            d = decidir_con_qwen(st["meta_x"], st["meta_z"], b, conn=conn, history=hi)
        if "_error" not in d:
            return d
        print("    retry " + str(intento+1) + " por: " + str(d.get("_error")))
        time.sleep(1)
    return d

perms = [("A","Ap","B"),("A","B","Ap"),("Ap","A","B"),("Ap","B","A"),("B","A","Ap"),("B","Ap","A")]
resultados = []
print("=== TEST 6: 6 permutaciones ===")
print()
for perm in perms:
    etiqueta = "->".join(perm)
    print("--- " + etiqueta + " ---")
    for i, cond in enumerate(perm):
        d = ejecutar_con_retry(cond, ctxs[i])
        print("    " + cond + ": " + str(d.get("accion")))
    import time
    for _intento in range(3):
        dS = decidir_con_qwen(S_state["meta_x"], S_state["meta_z"], S_barco, conn=None, history=S_hist)
        if "_error" not in dS:
            break
        time.sleep(1)
    s = str(dS.get("accion")) + "|" + str(dS.get("parametro"))
    print("    S*: " + s)
    resultados.append(s)
    print()
conn.close()

distintos = set(resultados)
print("=== RESUMEN ===")
for perm, r in zip(perms, resultados):
    print("  " + "->".join(perm) + ": " + r)
print()
print("Distintos: " + str(len(distintos)))
if len(distintos) == 1:
    print("VEREDICTO: PASS")
else:
    print("VEREDICTO: FAIL")
