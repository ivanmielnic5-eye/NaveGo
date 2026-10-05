#!/usr/bin/env python3
"""
Sonda STOP — una permutacion por proceso, ollama stop + verificacion + S*.
Uso: python3 runtime_probe_stop.py A:Ap:B
Registra: 3 respuestas de perm, estado de ollama ps post-stop, respuesta S*.
"""
import json, math, sys, subprocess, time, hashlib
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent))
from simulador_polaris import Barco
from agente_llm import decidir_con_qwen, MODELO_DECISION
from memoria import conectar

if len(sys.argv) < 2:
    print("uso: runtime_probe_stop.py A:Ap:B"); sys.exit(1)
perm = sys.argv[1].split(":")
assert len(perm) == 3 and set(perm) == {"A", "Ap", "B"}, "perm invalida"

banco = json.load(open("COMMON_CONTEXT_001.json"))
S_state = banco[1]["state"]
S_hist  = banco[1]["history"]
ctxs    = [banco[5], banco[6], banco[7]]

def barco(state):
    b = Barco()
    b.pos_x = state["pos_x"]; b.pos_z = state["pos_z"]
    b.yaw   = math.radians(state["hdg"])
    sog_ms  = state["sog"] / 1.94384449
    b.vel_x = math.sin(b.yaw) * sog_ms
    b.vel_z = -math.cos(b.yaw) * sog_ms
    b.viento_intensidad_kn = state.get("viento_kn", 0.0)
    b.viento_direccion_deg = state.get("viento_dir", 0.0)
    return b

def hash_S():
    sig = json.dumps({
        "meta_x": S_state["meta_x"], "meta_z": S_state["meta_z"],
        "pos_x": S_state["pos_x"], "pos_z": S_state["pos_z"],
        "hdg": S_state["hdg"], "sog": S_state["sog"],
        "hist_len": len(S_hist) if S_hist else 0,
        "modelo": MODELO_DECISION,
    }, sort_keys=True).encode()
    return hashlib.sha256(sig).hexdigest()[:12]

def stop_y_verificar(timeout=15):
    subprocess.run(["ollama", "stop", MODELO_DECISION],
                   capture_output=True, timeout=15)
    t0 = time.time()
    cargado = True
    while time.time() - t0 < timeout:
        out = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=5).stdout
        if MODELO_DECISION not in out:
            cargado = False
            break
        time.sleep(0.5)
    return not cargado  # True si quedo descargado

conn = conectar()
res_perm = []
for i, cond in enumerate(perm):
    ctx = ctxs[i]
    st, hi = ctx["state"], ctx["history"]
    b = barco(st)
    if cond == "A":
        d = decidir_con_qwen(st["meta_x"], st["meta_z"], b, conn=None, history=None)
    elif cond == "Ap":
        d = decidir_con_qwen(st["meta_x"], st["meta_z"], b, conn=None, history=hi)
    else:
        d = decidir_con_qwen(st["meta_x"], st["meta_z"], b, conn=conn, history=hi)
    accion = d.get("accion", d.get("_error", "?"))
    param  = d.get("parametro", d.get("_raw", ""))
    res_perm.append(f"{cond}={accion}|{param}")

# -- STOP + verificacion --
descargado = stop_y_verificar()
estado_stop = "unloaded" if descargado else "STILL_LOADED"

# -- S* --
S_barco = barco(S_state)
dS = decidir_con_qwen(S_state["meta_x"], S_state["meta_z"], S_barco,
                      conn=None, history=S_hist)
S_accion = dS.get("accion", dS.get("_error", "?"))
S_param  = dS.get("parametro", dS.get("_raw", ""))

conn.close()

ts = datetime.now().strftime("%H:%M:%S")
print(f"[{ts}] {perm[0]}->{perm[1]}->{perm[2]} || " + " || ".join(res_perm) +
      f" || stop={estado_stop} || S*={S_accion}|{S_param} hash={hash_S()}")
