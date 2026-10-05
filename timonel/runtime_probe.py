#!/usr/bin/env python3
"""
Sonda de runtime — aislamiento causal del cambio de regimen.
Modo A: 6 llamadas seguidas en el mismo proceso, mismos inputs.
Modo B: 1 llamada por invocacion (para proceso fresco, ver runtime_probe_B.sh).
Uso: python3 runtime_probe.py A | B
"""
import json, math, sys, time, hashlib
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent))
from simulador_polaris import Barco
from agente_llm import decidir_con_qwen, MODELO_DECISION, _stop_modelo

MODO = sys.argv[1] if len(sys.argv) > 1 else "A"

banco = json.load(open("COMMON_CONTEXT_001.json"))
S_state = banco[1]["state"]
S_hist  = banco[1]["history"]

def barco(state):
    b = Barco()
    b.pos_x = state["pos_x"]; b.pos_z = state["pos_z"]
    b.yaw   = math.radians(state["hdg"])
    sog_ms  = state["sog"] / 1.94384449
    b.vel_x = math.sin(b.yaw) * sog_ms
    b.vel_z = -math.cos(b.yaw) * sog_ms
    b.viento_intensidad_kn  = state.get("viento_kn", 0.0)
    b.viento_direccion_deg  = state.get("viento_dir", 0.0)
    return b

S_barco = barco(S_state)

sig = json.dumps({
    "meta_x": S_state["meta_x"], "meta_z": S_state["meta_z"],
    "pos_x": S_state["pos_x"], "pos_z": S_state["pos_z"],
    "hdg": S_state["hdg"], "sog": S_state["sog"],
    "hist_len": len(S_hist) if S_hist else 0,
    "modelo": MODELO_DECISION,
}, sort_keys=True).encode()
prompt_hash = hashlib.sha256(sig).hexdigest()[:12]

def llamar(n):
    if MODO == "B":
        _stop_modelo()
        time.sleep(0.3)
    t0 = time.time()
    d = decidir_con_qwen(S_state["meta_x"], S_state["meta_z"], S_barco,
                         conn=None, history=S_hist)
    dt = time.time() - t0
    accion = d.get("accion", d.get("_error", "?"))
    param  = d.get("parametro", d.get("_raw", ""))
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] modo={MODO} n={n} accion={accion}|{param} t={dt:.2f}s hash={prompt_hash}")

if MODO == "A":
    print(f"modelo={MODELO_DECISION} hash={prompt_hash}")
    for n in range(1, 7):
        llamar(n)
else:
    llamar(1)
