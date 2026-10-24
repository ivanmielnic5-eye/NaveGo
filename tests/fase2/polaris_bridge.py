#!/usr/bin/env python3
"""
LOGOS Kernel - Polaris Bridge (Fase 1E - Simulación Estricta y Conexión Controlada)
Propósito: Conectar propuestas de intención estructuradas con el motor de política
determinista, soportando modo offline/simulado para pruebas y conexión opcional
desactivada por defecto con Ollama (Qwen2.5-Coder), garantizando manejo robusto de tuplas.
"""

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Callable, Any
from policy_engine import validate_contract, load_schema, build_bwrap_args_mock

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:3b"

def query_ollama_real(prompt: str, schema: dict) -> str:
    system_prompt = (
        "Eres un agente de sistema seguro bajo el kernel LOGOS. "
        "Debes responder ÚNICAMENTE con un objeto JSON válido que cumpla estrictamente "
        "el esquema JSON proporcionado. No agregues texto explicativo ni markdown."
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": f"{system_prompt}\n\nSolicitud: {prompt}",
        "format": schema,
        "stream": False
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_ENDPOINT,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
        return result.get("response", "{}")

def query_model_safe(prompt: str, provider_fn: Callable[[str, dict], str] | None = None) -> str:
    if provider_fn is None:
        return json.dumps({
            "error": "OFFLINE_MODE_ACTIVE: La conexión real con Ollama está desactivada por defecto en modo simulación."
        })

    try:
        schema = load_schema()
        raw_response = provider_fn(prompt, schema)
        return raw_response
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return json.dumps({
            "error": f"OLLAMA_CONNECTION_ERROR: No se pudo conectar al endpoint: {e}"
        })
    except Exception as exc:
        return json.dumps({
            "error": f"MODEL_QUERY_ERROR: Error inesperado al consultar el modelo: {exc}"
        })

def simulate_polaris_pipeline(user_prompt: str, workspace_dir: Path, provider_fn: Callable[[str, dict], str] | None = None) -> dict:
    print(f"[*] Prompt de usuario: '{user_prompt}'")

    raw_response = query_model_safe(user_prompt, provider_fn)
    print(f"[*] Propuesta recibida:\n{raw_response}\n")

    is_valid, reason, contract = validate_contract(raw_response, workspace_dir)

    audit_record = {
        "prompt_usuario": user_prompt,
        "propuesta_modelo": raw_response,
        "validacion_politica": {
            "aprobado": is_valid,
            "motivo": reason
        },
        "accion_ejecutiva": "SIMULADA_INSPECCION"
    }

    if is_valid and contract:
        bwrap_args = build_bwrap_args_mock(contract, workspace_dir)
        audit_record["bwrap_args_generados"] = bwrap_args
        print(f"[+] DHS HARNESS [VERDICTO]: CONTRATO APROBADO.")
        print(f"[+] Argumentos bwrap generados para inspección:")
        print("    " + " ".join(bwrap_args))
    else:
        print(f"[-] DHS HARNESS [VERDICTO]: CONTRATO DENEGADO.")
        print(f"[-] Motivo: {reason}")

    return audit_record

if __name__ == "__main__":
    import tempfile

    def mock_provider(prompt: str, schema: dict) -> str:
        return json.dumps({
            "schema_version": "1.0",
            "action": "read_file",
            "target": "informe.txt",
            "purpose": "demostracion_offline",
            "requested_effect": "read_only"
        })

    with tempfile.TemporaryDirectory() as tmp_dir:
        ws = Path(tmp_dir).resolve()
        test_file = ws / "informe.txt"
        test_file.write_text("Contenido confidencial de prueba LOGOS", encoding="utf-8")

        print("=== INICIANDO SIMULACIÓN POLARIS BRIDGE (MODO OFFLINE) ===")
        simulate_polaris_pipeline("Lee el archivo informe.txt", ws, provider_fn=mock_provider)
