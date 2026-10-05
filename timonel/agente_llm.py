#!/usr/bin/env python3
"""
agente_llm.py - Funciones para consultar a Qwen (Ollama) desde el agente Timonel.

NO ejecuta comandos. Solo pide DECISIONES de alto nivel:
- que receta usar.
- con que parametro.
"""

import json
import math
import urllib.request


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODELO_DECISION = "qwen2.5-coder:1.5b"

# Acciones validas que Qwen puede elegir
ACCIONES_VALIDAS = {"corregir_rumbo", "ir_a_punto", "frenar", "terminar"}


def armar_prompt(meta_x: float, meta_z: float,
                 pos_x: float, pos_z: float,
                 hdg: float, sog: float, dist: float,
                 rumbo_hacia_meta: float,
                 bloque_experiencias: str = "",
                 bloque_historial: str = "") -> str:
    """Arma el prompt para Qwen con el estado actual y experiencias previas."""
    desvio = abs((rumbo_hacia_meta - hdg + 540) % 360 - 180)

    # Prefijo con experiencias previas (si las hay)
    prefijo_exp = ""
    if bloque_experiencias:
        prefijo_exp = bloque_experiencias + "\n\n"

    prompt = f"""Sos el timonel de un velero. Mision: llegar a la meta.

ESTADO ACTUAL:
- Posicion: ({pos_x:.1f}, {pos_z:.1f})
- Meta: ({meta_x:.1f}, {meta_z:.1f})
- Distancia a meta: {dist:.1f} metros
- Heading (proa): {hdg:.1f} grados
- Rumbo hacia la meta: {rumbo_hacia_meta:.1f} grados
- Desvio actual: {desvio:.1f} grados
- Velocidad: {sog:.2f} nudos

{bloque_historial}

ACCIONES DISPONIBLES:
- corregir_rumbo: girar la proa a un angulo. Parametro: grados (0-360).
- ir_a_punto: avanzar hacia coordenadas. Parametro: [x, z].
- frenar: detener el barco.
- terminar: SOLO si distancia < 15m.

TAREA:
Analiza la situacion actual. Elegi la mejor accion.

Criterios generales (guias):
- Si estas a menos de 15m de la meta: terminar.
- Si estas mal alineado (>30deg): corregir_rumbo.
- Si estas bien alineado (<=30deg): ir_a_punto.

{prefijo_exp}

REVISA LAS EXPERIENCIAS ANTES DE DECIDIR. Si alguna experiencia similar
sugiere una accion distinta a las guias, priorizala.

Responde UNICAMENTE con JSON, sin texto adicional. Formato:
{{"accion": "<accion>", "parametro": <parametro o null>}}
"""
    return prompt


def formatear_historial(history: list) -> str:
    """Convierte una lista de pasos previos en texto para el prompt."""
    if not history:
        return ""
    lineas = ["HISTORIAL DE LA MISION (ultimos pasos):"]
    for h in history:
        lineas.append(
            "  paso " + str(h.get("paso", "?")) + ": "
            + "pos=(" + str(h.get("pos_x", "?")) + "," + str(h.get("pos_z", "?")) + ") "
            + "hdg=" + str(h.get("hdg", "?")) + " "
            + "sog=" + str(h.get("sog", "?")) + " "
            + "-> " + str(h.get("decision", "?"))
        )
    return "\n".join(lineas)


def consultar_qwen(prompt: str, timeout_s: int = 10) -> dict:
    """Llama a Ollama y devuelve el JSON parseado. Retorna dict vacio si falla."""
    data = json.dumps({
        "model": MODELO_DECISION,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 2048, "temperature": 0, "seed": 555, "num_predict": 80, "top_k": 40, "top_p": 0.9, "repeat_penalty": 1.0, "num_batch": 512},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL, data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            resp = json.load(r).get("response", "").strip()
    except Exception as e:
        return {"_error": f"error de conexion: {e}"}

    try:
        decision = json.loads(resp)
    except json.JSONDecodeError as e:
        return {"_error": f"json invalido: {e}", "_raw": resp[:200]}

    if "accion" not in decision:
        return {"_error": "sin campo accion", "_raw": resp[:200]}

    if decision["accion"] not in ACCIONES_VALIDAS:
        return {"_error": f"accion desconocida: {decision['accion']}", "_raw": resp[:200]}

    return decision


def decidir_con_qwen(meta_x: float, meta_z: float, barco, conn=None, history=None) -> dict:
    """
    Toma el estado del barco, arma el prompt, consulta a Qwen y devuelve la decision.
    Si conn != None, recupera experiencias similares y las inyecta al prompt.
    Si falla, retorna dict con "_error".
    """
    dx = meta_x - barco.pos_x
    dz = meta_z - barco.pos_z
    dist = math.sqrt(dx * dx + dz * dz)
    rumbo_hacia_meta = math.degrees(math.atan2(dx, -dz)) % 360.0
    hdg = barco.heading_deg()
    desvio = abs((rumbo_hacia_meta - hdg + 540) % 360 - 180)
    sog = barco.sog_kn()

    # Recuperar experiencias previas si hay memoria disponible
    bloque_experiencias = ""
    if conn is not None:
        try:
            from memoria import (recuperar_similares, formatear_experiencias_para_prompt,
                                 filtrar_por_consenso)
            exp = recuperar_similares(conn, dist, desvio, sog, n=5, solo_exitos=True)
            exp = filtrar_por_consenso(exp, minimo_ratio=0.6)
            bloque_experiencias = formatear_experiencias_para_prompt(exp)
        except Exception:
            bloque_experiencias = ""

    bloque_historial = formatear_historial(history) if history else ""

    prompt = armar_prompt(
        meta_x=meta_x, meta_z=meta_z,
        pos_x=barco.pos_x, pos_z=barco.pos_z,
        hdg=hdg, sog=sog,
        dist=dist, rumbo_hacia_meta=rumbo_hacia_meta,
        bloque_experiencias=bloque_experiencias,
        bloque_historial=bloque_historial,
    )

    return consultar_qwen(prompt)
