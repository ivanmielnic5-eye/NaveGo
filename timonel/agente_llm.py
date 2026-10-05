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
                 bloque_experiencias: str = "") -> str:
    """Arma el prompt para Qwen con el estado actual y experiencias previas."""
    desvio = abs((rumbo_hacia_meta - hdg + 540) % 360 - 180)

    # Prefijo con experiencias previas (si las hay)
    prefijo_exp = ""
    if bloque_experiencias:
        prefijo_exp = bloque_experiencias + "\n\n"

    prompt = f"""{prefijo_exp}Sos el timonel de un velero. Mision: llegar a la meta.

ESTADO:
- Posicion: ({pos_x:.1f}, {pos_z:.1f})
- Meta: ({meta_x:.1f}, {meta_z:.1f})
- Distancia a meta: {dist:.1f} metros
- Heading (proa): {hdg:.1f} grados
- Rumbo hacia la meta: {rumbo_hacia_meta:.1f} grados
- Desvio actual: {desvio:.1f} grados
- Velocidad: {sog:.2f} nudos

ACCIONES:
- corregir_rumbo: girar la proa a un angulo. Parametro: grados (0-360).
- ir_a_punto: avanzar hacia coordenadas. Parametro: [x, z].
- frenar: detener el barco.
- terminar: llegaste a la meta.

REGLAS DE DECISION (aplicar en orden):
1. Si distancia < 15m: usa terminar.
2. Si desvio > 30 grados: usa corregir_rumbo con parametro = rumbo_hacia_meta.
3. Si desvio <= 30 grados: usa ir_a_punto con parametro = [{meta_x:.0f}, {meta_z:.0f}].

REGLA CRITICA: no corrijas el rumbo si el desvio ya es menor a 30 grados.
Avanzar con desvio pequenio es correcto y eficiente. Corregir de mas hace
perder tiempo. Confia en ir_a_punto.

Responde UNICAMENTE con JSON, sin texto adicional. Ejemplos:
{{"accion": "terminar", "parametro": null}}
{{"accion": "corregir_rumbo", "parametro": 90}}
{{"accion": "ir_a_punto", "parametro": [200, 0]}}
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


def decidir_con_qwen(meta_x: float, meta_z: float, barco, conn=None) -> dict:
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
            from memoria import recuperar_similares, formatear_experiencias_para_prompt
            exp = recuperar_similares(conn, dist, desvio, sog, n=3)
            bloque_experiencias = formatear_experiencias_para_prompt(exp)
        except Exception:
            bloque_experiencias = ""

    prompt = armar_prompt(
        meta_x=meta_x, meta_z=meta_z,
        pos_x=barco.pos_x, pos_z=barco.pos_z,
        hdg=hdg, sog=sog,
        dist=dist, rumbo_hacia_meta=rumbo_hacia_meta,
        bloque_experiencias=bloque_experiencias,
    )

    return consultar_qwen(prompt)
