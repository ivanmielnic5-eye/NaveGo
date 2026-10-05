#!/usr/bin/env python3
"""
agente_llm.py - Funciones para consultar a Qwen (Ollama) desde el agente Timonel.

NO ejecuta comandos. Solo pide DECISIONES de alto nivel:
- que receta usar.
- con que parametro.
"""

import json
import urllib.request


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODELO_DECISION = "qwen2.5-coder:1.5b"

# Acciones validas que Qwen puede elegir
ACCIONES_VALIDAS = {"corregir_rumbo", "ir_a_punto", "frenar", "terminar"}


def armar_prompt(meta_x: float, meta_z: float,
                 pos_x: float, pos_z: float,
                 hdg: float, sog: float, dist: float,
                 rumbo_hacia_meta: float) -> str:
    """Arma el prompt para Qwen con el estado actual."""
    prompt = f"""Sos el timonel de un velero. Tu mision: llegar a la meta y detenerte.

ESTADO ACTUAL:
- Posicion: ({pos_x:.1f}, {pos_z:.1f})
- Meta: ({meta_x:.1f}, {meta_z:.1f})
- Distancia a meta: {dist:.1f} metros
- Heading (a donde apunta la proa): {hdg:.1f} grados
- Rumbo hacia la meta: {rumbo_hacia_meta:.1f} grados
- Velocidad: {sog:.2f} nudos

ACCIONES DISPONIBLES (elegi UNA):
1. corregir_rumbo: girar la proa hacia un angulo especifico (0-360 grados)
2. ir_a_punto: navegar hacia un punto especifico (coordenadas x, z)
3. frenar: detener el barco
4. terminar: la mision esta cumplida

REGLAS:
- Si estas a menos de 15m de la meta: usa terminar.
- Si tu heading esta desviado mas de 20 grados del rumbo hacia la meta: usa corregir_rumbo.
- Si tu heading esta casi alineado (< 20 grados de desvio): usa ir_a_punto.
- No uses frenar hasta estar cerca de la meta.

Responde UNICAMENTE con un JSON valido, sin texto, sin explicacion:
Formato exacto:
- Para corregir_rumbo: {{"accion": "corregir_rumbo", "parametro": 90}}
- Para ir_a_punto: {{"accion": "ir_a_punto", "parametro": [200, 0]}}
- Para frenar: {{"accion": "frenar", "parametro": null}}
- Para terminar: {{"accion": "terminar", "parametro": null}}
"""
    return prompt


def consultar_qwen(prompt: str, timeout_s: int = 30) -> dict:
    """Llama a Ollama y devuelve el JSON parseado. Retorna dict vacio si falla."""
    data = json.dumps({
        "model": MODELO_DECISION,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 2048, "temperature": 0.2, "num_predict": 80},
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


def decidir_con_qwen(meta_x: float, meta_z: float, barco) -> dict:
    """
    Toma el estado del barco, arma el prompt, consulta a Qwen y devuelve la decision.
    Si falla, retorna dict con "_error".
    """
    import math
    dx = meta_x - barco.pos_x
    dz = meta_z - barco.pos_z
    dist = math.sqrt(dx * dx + dz * dz)
    rumbo_hacia_meta = math.degrees(math.atan2(dx, -dz)) % 360.0

    prompt = armar_prompt(
        meta_x=meta_x, meta_z=meta_z,
        pos_x=barco.pos_x, pos_z=barco.pos_z,
        hdg=barco.heading_deg(), sog=barco.sog_kn(),
        dist=dist, rumbo_hacia_meta=rumbo_hacia_meta,
    )

    return consultar_qwen(prompt)
