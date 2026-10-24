#!/usr/bin/env python3
"""
Suite de Pruebas Unitarias para el Orquestador Simulado (Fase 1B)
Valida el comportamiento de la política determinista y el rechazo de contratos anómalos.
"""

import unittest
import json
from orquestador_simulado import validar_politica_determinista, simular_ejecucion

class TestOrquestadorSimulado(unittest.TestCase):

    def test_contrato_valido_permitido(self):
        contrato = json.dumps({
            "contrato_version": "1.0",
            "accion_solicitada": {
                "operacion": "LEER_ARCHIVO",
                "parametros": {"ruta_relativa": "EXPEDIENTE/evidencias_agente/auditoria_entorno_20261023.json"}
            },
            "evaluacion_modelo": {
                "riesgo_propuesto": "BAJO",
                "requiere_autorizacion_propuesta": False
            }
        })
        res = simular_ejecucion(contrato)
        self.assertEqual(res["estado"], "APROBADO_Y_SIMULADO")
        self.assertFalse(res["ejecutado_real"])

    def test_operacion_no_autorizada(self):
        contrato = json.dumps({
            "contrato_version": "1.0",
            "accion_solicitada": {
                "operacion": "EJECUTAR_SHELL_MALICIOSO",
                "parametros": {"ruta_relativa": "cualquier_cosa.txt"}
            }
        })
        res = simular_ejecucion(contrato)
        self.assertEqual(res["estado"], "RECHAZADO")
        self.assertIn("Operación no autorizada", res["motivo"])

    def test_path_traversal_rechazado(self):
        contrato = json.dumps({
            "contrato_version": "1.0",
            "accion_solicitada": {
                "operacion": "LEER_ARCHIVO",
                "parametros": {"ruta_relativa": "../../etc/passwd"}
            }
        })
        res = simular_ejecucion(contrato)
        self.assertEqual(res["estado"], "RECHAZADO")
        self.assertIn("Path Traversal", res["motivo"])

    def test_inyeccion_shell_rechazada(self):
        contrato = json.dumps({
            "contrato_version": "1.0",
            "accion_solicitada": {
                "operacion": "LEER_ARCHIVO",
                "parametros": {"ruta_relativa": "archivo.txt; rm -rf /"}
            }
        })
        res = simular_ejecucion(contrato)
        self.assertEqual(res["estado"], "RECHAZADO")
        self.assertIn("prohibido", res["motivo"])

    def test_alta_riesgo_requiere_autorizacion(self):
        contrato = json.dumps({
            "contrato_version": "1.0",
            "accion_solicitada": {
                "operacion": "ESCRIBIR_ARCHIVO",
                "parametros": {"ruta_relativa": "EXPEDIENTE/test.log"}
            },
            "evaluacion_modelo": {
                "riesgo_propuesto": "ALTO",
                "requiere_autorizacion_propuesta": True
            }
        })
        res = simular_ejecucion(contrato)
        self.assertEqual(res["estado"], "PENDIENTE_AUTORIZACION")

if __name__ == "__main__":
    unittest.main()
