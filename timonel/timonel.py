#!/usr/bin/env python3
"""
timonel.py - Intermediario entre Godot (Polaris) y DSH (Qwen).

Fase 1: no consulta a DSH. Escribe timon=0 fijo.
Fase 2: consulta a DSH via Ollama.

Un escritor por archivo:
  - Godot escribe telemetria.jsonl
  - timonel.py escribe comandos.jsonl
"""

import json
import math
import os
import time
from pathlib import Path

# --- Configuracion ---
GODOT_DIR = Path.home() / ".local/share/godot/app_userdata/interfaz/timonel"
TELEMETRIA = GODOT_DIR / "telemetria.jsonl"
COMANDOS = GODOT_DIR / "comandos.jsonl"

INTERVALO_S = 3.0
MODO_FASE1 = False   # True: no consulta DSH. False: consulta.
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODELO = "qwen2.5-coder:3b"

def leer_ultima_telemetria(n=5):
    """Devuelve las ultimas n lineas de telemetria como listas de dicts."""
    if not TELEMETRIA.exists():
        return []
    try:
        with TELEMETRIA.open("r") as f:
            lineas = f.readlines()
    except Exception:
        return []
    muestras = []
    for l in lineas[-n:]:
        l = l.strip()
        if not l:
            continue
        try:
            muestras.append(json.loads(l))
        except json.JSONDecodeError:
            continue
    return muestras


def escribir_comando(timon, timon_ms, avance, avance_ms, fuente, nota):
    """Escribe una linea en comandos.jsonl."""
    GODOT_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "t": int(time.time() * 1000),
        "timon": int(timon),
        "timon_ms": int(timon_ms),
        "avance": int(avance),
        "avance_ms": int(avance_ms),
        "fuente": fuente,
        "nota": nota,
    }
    with COMANDOS.open("a") as f:
        f.write(json.dumps(entry) + "\n")
        f.flush()
    print(f"[timonel] comando escrito: {entry}")

def timon_python(px, pz, hdg, meta_x=36.0, meta_z=-6.0):
    """Devuelve (timon, avance). Ley de control con freno al llegar."""
    dx = meta_x - px
    dz = meta_z - pz
    dist = math.hypot(dx, dz)
    bearing = math.degrees(math.atan2(dx, -dz)) % 360
    delta = (bearing - hdg + 180) % 360 - 180

    # Zona de llegada: frenar todo
    if dist < 10.0:
        return 0, 0

    # Timon segun delta
    if delta > 15:
        timon = 1
    elif delta < -15:
        timon = -1
    else:
        timon = 0

    # Avance: solo si esta razonablemente alineado
    if abs(delta) > 45:
        avance = 0
    else:
        avance = 1

    return timon, avance


def consultar_dsh(muestras):
    """Consulta a DSH. Devuelve (timon, timon_ms, avance, avance_ms, nota)."""
    import urllib.request
    if not muestras:
        return 0, 0, 0, 0, "sin telemetria"
    u = muestras[-1]
    hdg = u.get("hdg_deg", 0)
    cog = u.get("cog_deg", 0)
    sog = u.get("sog_kn", 0)
    px = u.get("pos_x", 0)
    pz = u.get("pos_z", 0)
    aws = u.get("aws_kn", 0)
    awa = u.get("awa_deg", 0)
    dist = u.get("dist_a_meta", 0)
    prog = u.get("progreso", 0)

    prompt = (
        "Sos el timonel del velero Polaris. Meta: (36, -6).\n"
        "Pos actual: (%.1f, %.1f). HDG: %.1f. Dist a meta: %.1f m.\n"
        "Regla de timon segun HDG:\n"
        "  HDG 000-075 -> timon=+1\n"
        "  HDG 075-105 -> timon=0\n"
        "  HDG 105-360 -> timon=-1\n"
        "Pon siempre avance=1 y avance_ms=1500.\n"
        "Responde SOLO JSON: "
        '{"timon": N, "timon_ms": N, "avance": N, "avance_ms": N}'
    ) % (px, pz, hdg, dist)
    data = json.dumps({
        "model": MODELO,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 512, "temperature": 0.0, "num_predict": 100}
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            respuesta = json.load(r).get("response", "").strip()
    except Exception as e:
        return 0, 0, 0, 0, f"error HTTP: {e}"
    import re
    texto = respuesta.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```[a-z]*\n?", "", texto)
        texto = re.sub(r"\n?```$", "", texto)
    i = texto.find("{")
    if i == -1:
        return 0, 0, 0, 0, f"sin JSON: {texto[:80]}"
    j = texto.rfind("}")
    if j == -1 or j <= i:
        # Respuesta truncada: intentar reparar agregando el cierre
        texto = texto[i:] + "}"
    else:
        texto = texto[i:j+1]
    try:
        obj = json.loads(texto)
    except Exception as e:
        return 0, 0, 0, 0, f"JSON no parseable ({e}): {texto[:120]}"
    timon = int(obj.get("timon", 0))
    timon_ms = int(obj.get("timon_ms", 0))
    avance = int(obj.get("avance", 0))
    avance_ms = int(obj.get("avance_ms", 0))
    # Sanidad
    timon = max(-1, min(1, timon))
    avance = max(-1, min(1, avance))
    timon_ms = max(0, min(30000, timon_ms))
    avance_ms = max(0, min(30000, avance_ms))
    return timon, timon_ms, avance, avance_ms, respuesta

def main():
    print("[timonel] arrancando.")
    print(f"[timonel] telemetria: {TELEMETRIA}")
    print(f"[timonel] comandos:   {COMANDOS}")
    print(f"[timonel] modo fase 1: {MODO_FASE1}")
    print(f"[timonel] intervalo:   {INTERVALO_S}s")
    print("[timonel] MISION: Puerto Esperanza en (36, -6).")
    print("[timonel] Ctrl+C para salir.")
    while True:
        try:
            time.sleep(INTERVALO_S)
            muestras = leer_ultima_telemetria(5)
            if MODO_FASE1:
                escribir_comando(0, 0, 0, 0, "fase1", "quieto")
            elif muestras:
                u = muestras[-1]
                timon, avance = timon_python(u.get("pos_x", 0), u.get("pos_z", 0),
                                             u.get("hdg_deg", 0))
                timon_ms = 1500
                avance_ms = 1500
                escribir_comando(timon, timon_ms, avance, avance_ms,
                                 "python", f"hdg={u.get('hdg_deg',0):.0f}")
            else:
                escribir_comando(0, 0, 0, 0, "sin_tel", "sin telemetria")
        except KeyboardInterrupt:
            print("[timonel] saliendo.")
            break
        except Exception as e:
            print(f"[timonel] error: {e}")
            continue


if __name__ == "__main__":
    main()
