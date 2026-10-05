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
import os
import time
from pathlib import Path

# --- Configuracion ---
GODOT_DIR = Path.home() / ".local/share/godot/app_userdata/interfaz/timonel"
TELEMETRIA = GODOT_DIR / "telemetria.jsonl"
COMANDOS = GODOT_DIR / "comandos.jsonl"

INTERVALO_S = 15.0
MODO_FASE1 = False   # True: no consulta DSH. False: consulta.
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODELO = "qwen2.5-coder:7b"

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

    contexto = (
        "Sos el timonel del velero Polaris. MISION: hay gente esperando "
        "en Puerto Sano, que esta en pos_x = 200, pos_z = 0. "
        "Ahora estas en pos_x = %.1f, pos_z = %.1f. "
        "El viento sopla del norte (000) a %.1f nudos y te empuja al sur. "
        "Tenes que llegar a Puerto Sano con el barco a flote.\n\n"
        "COMANDOS DISPONIBLES (responde con los 4):\n"
        "- timon: -1 (babor/izquierda), 0 (recto), +1 (estribor/derecha)\n"
        "- timon_ms: cuantos milisegundos aplicar el timon (0 a 30000)\n"
        "- avance: -1 (reversa), 0 (no acelerar), +1 (adelante)\n"
        "- avance_ms: cuantos milisegundos aplicar avance (0 a 30000)\n\n"
        "ESCALA HDG (direccion de la proa): 000=norte, 090=este, 180=sur, 270=oeste.\n"
        "ESCALA COG (direccion del movimiento): igual escala.\n"
        "Para ir de tu posicion actual a Puerto Sano (200, 0), "
        "necesitas HDG cercano a 090 (este).\n\n"
        "REGLA DE DECISION (usa HDG). Cinco casos:\n"
        "- HDG 075 a 105: en rumbo. timon=0.\n"
        "- HDG 105 a 180: timon=-1.\n"
        "- HDG 180 a 270: timon=-1.\n"
        "- HDG 270 a 360: timon=+1.\n"
        "- HDG 000 a 075: timon=+1.\n"
        "Siempre que muevas el timon, pon avance=1 para tener "
        "autoridad sobre la proa.\n\n"
        "CALIBRACION DEL TIMON (medida real): 1s = 6.7 grados. "
        "3s = 20 grados. 5s = 34 grados. 10s = 67 grados. "
        "Para corregir 30 grados, aplica 4000ms. Para corregir 10 "
        "grados, aplica 1500ms. NO apliques timon mas de 10s "
        "seguidos, porque gira demasiado."
    ) % (px, pz, aws)

    estado = (
        "ESTADO ACTUAL:\n"
        "- HDG: %.1f (proa)\n"
        "- COG: %.1f (movimiento)\n"
        "- SOG: %.2f nudos\n"
        "- AWS: %.1f (viento)\n"
        "- AWA: %.1f (angulo viento)\n"
        "- pos: (%.1f, %.1f)\n"
        "- dist_a_meta: %.1f metros\n"
        "- progreso (ultimo ciclo): %+.1f metros (positivo=se acerco)"
    ) % (hdg, cog, sog, aws, awa, px, pz, dist, prog)

    prompt = (
        contexto
        + "\n\n"
        + estado
        + "\n\nResponde UNICAMENTE con un JSON valido, sin texto, "
        "sin explicacion, sin markdown. Formato exacto: "
        '{"timon": N, "timon_ms": N, "avance": N, "avance_ms": N}'
    )
    data = json.dumps({
        "model": MODELO,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 2048, "temperature": 0.3}
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
    try:
        obj = json.loads(respuesta)
    except Exception:
        return 0, 0, 0, 0, f"JSON no parseable: {respuesta[:60]}"
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
    print("[timonel] MISION: Puerto Sano en (200, 0).")
    print("[timonel] Ctrl+C para salir.")
    while True:
        try:
            time.sleep(INTERVALO_S)
            muestras = leer_ultima_telemetria(5)
            if MODO_FASE1:
                escribir_comando(0, 0, 0, 0, "fase1", "quieto")
            else:
                timon, timon_ms, avance, avance_ms, nota = consultar_dsh(muestras)
                escribir_comando(timon, timon_ms, avance, avance_ms, "dsh", nota)
        except KeyboardInterrupt:
            print("[timonel] saliendo.")
            break
        except Exception as e:
            print(f"[timonel] error: {e}")
            continue


if __name__ == "__main__":
    main()
