#!/usr/bin/env python3
"""
Orquestador Simulado (Fase 1B) - LOGOS Kernel
Propósito: Validar contratos de acción estructurada, aplicar política determinista
y registrar el veredicto sin invocar ningún comando real del sistema operativo.
"""

import json
import os
from pathlib import Path

WORKSPACE_DIR = Path.cwd().resolve()

OPERACIONES_PERMITIDAS = {
    "LISTAR_DIRECTORIO",
    "LEER_ARCHIVO",
    "ESCRIBIR_ARCHIVO",
    "CONSULTAR_GIT"
}

def validar_politica_determinista(contrato: dict) -> tuple[bool, str]:
    """
    Aplica reglas inmutables de seguridad sobre el contrato estructurado propuesto.
    Retorna: (es_valido: bool, motivo: str)
    """
    if not isinstance(contrato, dict):
        return False, "El contrato no es un diccionario JSON válido."
    
    accion = contrato.get("accion_solicitada", {})
    operacion = accion.get("operacion")
    
    if operacion not in OPERACIONES_PERMITIDAS:
        return False, f"Operación no autorizada o fuera de lista blanca: {operacion}"
    
    parametros = accion.get("parametros", {})
    ruta_relativa = parametros.get("ruta_relativa", "")
    
    if ".." in ruta_relativa or ruta_relativa.startswith("/"):
        return False, "Violación de política: Intento de Path Traversal o ruta absoluta prohibida."
    
    param_str = json.dumps(parametros)
    caracteres_prohibidos = [";", "&&", "||", "|", ">", "<", "`", "$(", "eval", "exec"]
    for char in caracteres_prohibidos:
        if char in param_str:
            return False, f"Violación de política: Carácter o keyword de shell prohibido detectado ('{char}')."

    try:
        ruta_absoluta = (WORKSPACE_DIR / ruta_relativa).resolve()
        if not str(ruta_absoluta).startswith(str(WORKSPACE_DIR)):
            return False, "Violación de política: La ruta resuelta escapa del workspace autorizado."
    except Exception as e:
        return False, f"Error al resolver la ruta: {e}"

    return True, "Contrato aprobado por la política determinista."


def simular_ejecucion(contrato_json_str: str) -> dict:
    """
    Ejecuta el pipeline completo de validación sin efectos laterales en el host.
    """
    resultado_registro = {
        "estado": "RECHAZADO",
        "motivo": "",
        "ejecutado_real": False
    }

    try:
        contrato = json.loads(contrato_json_str)
    except json.JSONDecodeError as e:
        resultado_registro["motivo"] = f"JSON malformado: {e}"
        return resultado_registro

    valido, mensaje = validar_politica_determinista(contrato)
    if not valido:
        resultado_registro["motivo"] = mensaje
        return resultado_registro

    evaluacion = contrato.get("evaluacion_modelo", {})
    riesgo = evaluacion.get("riesgo_propuesto", "ALTO")
    requiere_auth = evaluacion.get("requiere_autorizacion_propuesta", True)

    if riesgo in ("ALTO", "CRITICO") or requiere_auth:
        resultado_registro["motivo"] = "Aprobado por política, pero retenido por requerir autorización humana."
        resultado_registro["estado"] = "PENDIENTE_AUTORIZACION"
        return resultado_registro

    accion = contrato.get("accion_solicitada", {})
    resultado_registro["estado"] = "APROBADO_Y_SIMULADO"
    resultado_registro["motivo"] = "Simulación completada con éxito (Cero efectos en el Host)."
    resultado_registro["detalle_mock"] = {
        "operacion": accion.get("operacion"),
        "ruta": accion.get("parametros", {}).get("ruta_relativa"),
        "exit_code": 0
    }
    return resultado_registro

if __name__ == "__main__":
    print("Módulo Orquestador Simulado cargado correctamente en tests/fase1b/orquestador_simulado.py")
