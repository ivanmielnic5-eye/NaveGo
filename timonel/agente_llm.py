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
                 viento_kn: float = 0.0, viento_dir: float = 0.0,
                 bloque_experiencias: str = "",
                 bloque_historial: str = "") -> str:
    """Arma el prompt para Qwen.

    Contrato de tarea explicito (que significa cada accion).
    Sin reglas condicionales (que accion elegir ante que estado).
    """
    desvio = abs((rumbo_hacia_meta - hdg + 540) % 360 - 180)

    prefijo_exp = ""
    if bloque_experiencias:
        prefijo_exp = bloque_experiencias + "\n\n"

    bloque_viento = ""
    if viento_kn > 0.0:
        bloque_viento = f"- Viento: {viento_kn:.1f} nudos desde {viento_dir:.0f} grados\n"

    fase = "en la meta" if dist < 15.0 else "navegando"

    prompt = f"""Sos el timonel de un velero. Mision: llevar el barco a la meta.

ESTADO ACTUAL:
- Posicion: ({pos_x:.1f}, {pos_z:.1f})
- Meta: ({meta_x:.1f}, {meta_z:.1f})
- Distancia a meta: {dist:.1f} metros
- Fase de mision: {fase}
- Heading (proa): {hdg:.1f} grados (0=norte, 90=este)
- Rumbo hacia la meta: {rumbo_hacia_meta:.1f} grados
- Desvio actual: {desvio:.1f} grados
- Velocidad: {sog:.2f} nudos
{bloque_viento}
{bloque_historial}

ACCIONES DISPONIBLES:

1) corregir_rumbo
   Que hace: gira la proa del barco hasta un angulo absoluto.
   Parametro: grados (0-360). 0=norte, 90=este, 180=sur, 270=oeste.
   Cuando es apropiada: cuando el rumbo actual esta muy desviado del rumbo a la meta.
   Efecto: el barco no avanza, solo gira.

2) ir_a_punto
   Que hace: navega hacia coordenadas especificas.
   Parametro: [x, z].
   Cuando es apropiada: cuando el barco ya esta razonablemente alineado con la meta
   y puede avanzar directamente.
   Efecto: el barco avanza hacia el punto, corrigiendo rumbo automaticamente.

3) frenar
   Que hace: reduce la velocidad del barco a aproximadamente 0.3 nudos.
   Parametro: ninguno.
   Cuando es apropiada: cuando necesitas reducir la velocidad para maniobrar con
   precision o detenerte suavemente cerca de la meta.
   NO detiene completamente el barco. Solo lo desacelera.
   Efecto: el barco pierde velocidad progresivamente.

4) terminar
   Que hace: declara la mision como cumplida.
   Parametro: ninguno.
   Cuando es apropiada: SOLO cuando el barco ya esta dentro del radio de llegada
   (distancia a meta menor a 15 metros). Fuera de ese radio, es invalida.
   Efecto: la mision se cierra.

TAREA:
Analiza el estado actual y elegi la accion que mejor contribuya al objetivo.

{prefijo_exp}

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


def _parsear_respuesta_json(texto: str) -> dict:
    """Parsea la respuesta del modelo buscando el primer objeto JSON valido."""
    texto = texto.strip()
    if texto.startswith("```"):
        lineas = texto.split(chr(10))
        lineas = [l for l in lineas if not l.strip().startswith("```")]
        texto = chr(10).join(lineas).strip()
    i = texto.find("{")
    j = texto.rfind("}")
    if i == -1 or j == -1 or j <= i:
        return {"_error": "sin_json", "_raw": texto[:200]}
    try:
        return json.loads(texto[i:j+1])
    except json.JSONDecodeError as e:
        return {"_error": "json_invalido: " + str(e), "_raw": texto[:200]}


def _validar_decision(decision: dict, raw: str) -> dict:
    """Valida accion y parametro segun memo 74 seccion 2.
    Devuelve la decision si es valida, o un dict con _error."""
    if "accion" not in decision:
        return {"_error": "sin campo accion", "_raw": raw[:200]}
    accion = decision["accion"]
    if accion not in ACCIONES_VALIDAS:
        return {"_error": "accion desconocida: " + str(accion), "_raw": raw[:200]}
    parametro = decision.get("parametro")
    if accion == "corregir_rumbo":
        if not isinstance(parametro, (int, float)) or isinstance(parametro, bool):
            return {"_error": "corregir_rumbo sin parametro numerico", "_raw": raw[:200]}
        if not (0.0 <= float(parametro) <= 360.0):
            return {"_error": "corregir_rumbo parametro fuera de rango: " + str(parametro), "_raw": raw[:200]}
    elif accion == "ir_a_punto":
        if not isinstance(parametro, (list, tuple)) or len(parametro) != 2:
            return {"_error": "ir_a_punto sin parametro [x, z]", "_raw": raw[:200]}
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in parametro):
            return {"_error": "ir_a_punto parametro no numerico", "_raw": raw[:200]}
    # frenar y terminar: sin parametro requerido
    return decision


def _consultar_via_chat(prompt: str, modelo: str, timeout_s: int = 120) -> str:
    """Llama a /api/chat. Usado para modelos de chat como Llama."""
    data = json.dumps({
        "model": modelo,
        "messages": [
            {"role": "system", "content": "Sos un agente de navegacion. Respondes EXCLUSIVAMENTE con este esquema JSON exacto, sin ninguna otra clave ni texto: {\"accion\": \"<corregir_rumbo|ir_a_punto|frenar|terminar>\", \"parametro\": <numero o [x, z] o null>}. No agregues claves como 'answer', 'response' ni 'reasoning'. Solo 'accion' y 'parametro'."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 2048, "temperature": 0, "seed": 555, "num_predict": 80, "num_batch": 512},
    }).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as r:
        resp = json.load(r)
    return resp.get("message", {}).get("content", "").strip()


def _stop_modelo():
    import subprocess
    try:
        subprocess.run(["ollama", "stop", MODELO_DECISION], capture_output=True, timeout=10)
    except Exception:
        pass


def consultar_qwen(prompt: str, timeout_s: int = 10) -> dict:
    """Llama a Ollama y devuelve el JSON parseado. Retorna dict vacio si falla.

    Dispatch por modelo:
    - Modelos de chat (llama): usa /api/chat con format:json.
    - Modelos de codigo (qwen): usa /api/generate con reintento por respuesta corrupta.
    """
    if "llama" in MODELO_DECISION.lower():
        try:
            resp = _consultar_via_chat(prompt, MODELO_DECISION, timeout_s=max(timeout_s, 120))
        except Exception as e:
            return {"_error": f"error de conexion chat: {e}"}
        if not resp:
            return {"_error": "respuesta_vacia_chat", "_raw": ""}
        decision = _parsear_respuesta_json(resp)
        if "_error" in decision:
            return decision
        return _validar_decision(decision, resp)

    data = json.dumps({
        "model": MODELO_DECISION,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 2048, "temperature": 0, "seed": 555, "num_predict": 80, "top_k": 40, "top_p": 0.9, "repeat_penalty": 1.0, "num_batch": 512},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL, data=data,
        headers={"Content-Type": "application/json"},
    )

    resp = ""
    for intento in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as r:
                resp = json.load(r).get("response", "").strip()
        except Exception as e:
            return {"_error": f"error de conexion: {e}"}

        if resp and "?????" not in resp:
            break

        if intento == 0:
            _stop_modelo()

    if not resp or "?????" in resp:
        return {"_error": "respuesta_vacia_o_corrupta", "_raw": resp[:200]}

    decision = _parsear_respuesta_json(resp)

    if "_error" in decision:
        return decision

    return _validar_decision(decision, resp)


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

    viento_kn = getattr(barco, "viento_intensidad_kn", 0.0)
    viento_dir = getattr(barco, "viento_direccion_deg", 0.0)

    prompt = armar_prompt(
        meta_x=meta_x, meta_z=meta_z,
        pos_x=barco.pos_x, pos_z=barco.pos_z,
        hdg=hdg, sog=sog,
        dist=dist, rumbo_hacia_meta=rumbo_hacia_meta,
        viento_kn=viento_kn, viento_dir=viento_dir,
        bloque_experiencias=bloque_experiencias,
        bloque_historial=bloque_historial,
    )

    return consultar_qwen(prompt)
