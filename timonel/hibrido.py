#!/usr/bin/env python3
"""hibrido.py - Orquesta las 3 capas del sistema hibrido.

Capa 1: admisibilidad simbolica.
Capa 2: seleccion del LLM entre las admisibles.
Capa 3: validacion + respaldo Python (timon_python).

Referencia: EXPEDIENTE/80 seccion 2.
"""
import json
import math
import sys
import urllib.request

sys.path.insert(0, ".")

from admisibilidad import acciones_admisibles, validar_parametro
from prompt_hibrido import prompt_hibrido

OLLAMA_CHAT = "http://127.0.0.1:11434/api/chat"

SYSTEM_PROMPT = ("Sos un agente de navegacion. Respondes EXCLUSIVAMENTE con el esquema: "
                 "{\"accion\": \"<nombre>\", \"parametro\": <valor o null>}. "
                 "La accion DEBE ser una de las acciones admisibles listadas. "
                 "No agregues otras claves.")


def _llamar_llm(prompt, modelo, timeout_s=120):
    data = json.dumps({
        "model": modelo,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 2048, "temperature": 0, "seed": 555, "num_predict": 80, "num_batch": 512},
    }).encode()
    req = urllib.request.Request(OLLAMA_CHAT, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            resp = json.load(r)
        return resp.get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"ERROR: {e}"


def _extraer_json(texto):
    i = texto.find("{")
    j = texto.rfind("}")
    if i == -1 or j == -1 or j <= i:
        return None
    try:
        return json.loads(texto[i:j+1])
    except Exception:
        return None


def _respaldo_python(dist, rumbo_meta, hdg):
    """Politica Python simple (equivale a timon_python, pero sin estado)."""
    desvio = abs((rumbo_meta - hdg + 540) % 360 - 180)
    if dist < 10.0:
        return ("frenar", None)
    if desvio > 15.0:
        return ("corregir_rumbo", round(rumbo_meta, 2))
    return ("ir_a_punto", None)


def decidir_hibrido(meta_x, meta_z, pos_x, pos_z, hdg, sog, dist, rumbo_meta,
                    viento_kn=0.0, viento_dir=0.0, modelo="llama3.1:8b"):
    """Devuelve dict con la decision y metadata de las 3 capas."""
    # CAPA 1: admisibilidad
    admisibles = acciones_admisibles(dist, sog)

    # Si el simbolico deja UNA SOLA accion admisible, no se consulta al LLM
    if len(admisibles) == 1:
        return {
            "accion": admisibles[0],
            "parametro": None,
            "fuente": "simbolico_unico",
            "admisibles": admisibles,
        }

    # CAPA 2: LLM elige entre admisibles
    prompt = prompt_hibrido(
        meta_x=meta_x, meta_z=meta_z, pos_x=pos_x, pos_z=pos_z,
        hdg=hdg, sog=sog, dist=dist, rumbo_meta=rumbo_meta,
        admisibles=admisibles,
        viento_kn=viento_kn, viento_dir=viento_dir,
    )
    crudo = _llamar_llm(prompt, modelo)
    parsed = _extraer_json(crudo) if not crudo.startswith("ERROR") else None

    # CAPA 3: validacion + respaldo
    if parsed is None:
        accion, parametro = _respaldo_python(dist, rumbo_meta, hdg)
        return {
            "accion": accion,
            "parametro": parametro,
            "fuente": "respaldo_python_json_invalido",
            "admisibles": admisibles,
            "crudo": crudo[:200],
        }

    accion = parsed.get("accion")
    parametro = parsed.get("parametro")

    if accion not in admisibles:
        accion_py, param_py = _respaldo_python(dist, rumbo_meta, hdg)
        return {
            "accion": accion_py,
            "parametro": param_py,
            "fuente": "respaldo_python_accion_no_admisible",
            "admisibles": admisibles,
            "accion_rechazada": accion,
            "crudo": crudo[:200],
        }

    ok, motivo = validar_parametro(accion, parametro)
    if not ok:
        accion_py, param_py = _respaldo_python(dist, rumbo_meta, hdg)
        return {
            "accion": accion_py,
            "parametro": param_py,
            "fuente": "respaldo_python_parametro_invalido",
            "admisibles": admisibles,
            "motivo_rechazo": motivo,
            "crudo": crudo[:200],
        }

    return {
        "accion": accion,
        "parametro": parametro,
        "fuente": "llm",
        "admisibles": admisibles,
    }
