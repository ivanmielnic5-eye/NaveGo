#!/usr/bin/env python3
"""Pruebas offline de integración para Polaris Bridge.
No conecta con Ollama y no ejecuta Bubblewrap.
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import polaris_bridge as bridge


class TestPolarisBridgeOffline(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name).resolve()
        (self.workspace / "informe.txt").write_text(
            "contenido de prueba", encoding="utf-8"
        )
        (self.workspace / "docs").mkdir()

        # Si el puente intenta abrir una conexión HTTP, la prueba falla.
        self.network_guard = patch(
            "polaris_bridge.urllib.request.urlopen",
            side_effect=AssertionError(
                "RED_PROHIBIDA_EN_TEST_OFFLINE"
            ),
        )
        self.urlopen_mock = self.network_guard.start()

    def tearDown(self):
        self.network_guard.stop()
        self.tmp.cleanup()

    def contract(self, target="informe.txt", action="read_file"):
        return {
            "schema_version": "1.0",
            "action": action,
            "target": target,
            "purpose": "prueba_offline",
            "requested_effect": "read_only",
        }

    def run_proposal(self, proposal):
        raw = (
            proposal if isinstance(proposal, str)
            else json.dumps(proposal)
        )
        calls = []

        def fake_provider(prompt, schema):
            calls.append((prompt, schema))
            return raw

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            audit = bridge.simulate_polaris_pipeline(
                "Solicitud controlada de prueba",
                self.workspace,
                provider_fn=fake_provider,
            )

        self.assertEqual(len(calls), 1, "Debe usarse el proveedor simulado")
        self.assertIsInstance(calls[0][1], dict)
        self.assertEqual(
            self.urlopen_mock.call_count, 0,
            "El modo offline intentó abrir una conexión HTTP",
        )
        return audit

    def test_01_accion_valida_genera_argumentos_sin_ejecutarlos(self):
        audit = self.run_proposal(self.contract())

        self.assertTrue(audit["validacion_politica"]["aprobado"])
        args = audit["bwrap_args_generados"]
        self.assertIsInstance(args, list)
        self.assertEqual(args[0], "/usr/bin/bwrap")
        self.assertIn("--unshare-pid", args)
        proc_index = args.index("--proc")
        self.assertEqual(args[proc_index + 1], "/proc")
        self.assertEqual(
            audit["accion_ejecutiva"], "SIMULADA_INSPECCION"
        )

    def test_02_path_traversal_es_denegado(self):
        audit = self.run_proposal(
            self.contract("../../etc/passwd")
        )

        self.assertFalse(audit["validacion_politica"]["aprobado"])
        self.assertNotIn("bwrap_args_generados", audit)

    def test_03_campo_adicional_es_denegado(self):
        proposal = self.contract()
        proposal["command"] = "rm -rf /"

        audit = self.run_proposal(proposal)

        self.assertFalse(audit["validacion_politica"]["aprobado"])
        self.assertNotIn("bwrap_args_generados", audit)

    def test_04_json_malformado_es_denegado(self):
        audit = self.run_proposal('{"action":}')

        self.assertFalse(audit["validacion_politica"]["aprobado"])
        self.assertNotIn("bwrap_args_generados", audit)

    def test_05_directorio_valido_list_dir(self):
        audit = self.run_proposal(
            self.contract("docs", "list_dir")
        )

        self.assertTrue(audit["validacion_politica"]["aprobado"])
        self.assertIn("bwrap_args_generados", audit)

    def test_06_error_del_proveedor_no_autoriza(self):
        def failing_provider(prompt, schema):
            raise TimeoutError("timeout simulado")

        with contextlib.redirect_stdout(io.StringIO()):
            audit = bridge.simulate_polaris_pipeline(
                "Solicitud de prueba",
                self.workspace,
                provider_fn=failing_provider,
            )

        self.assertFalse(audit["validacion_politica"]["aprobado"])
        self.assertNotIn("bwrap_args_generados", audit)
        self.assertEqual(self.urlopen_mock.call_count, 0)

    def test_07_modo_offline_sin_proveedor_no_autoriza(self):
        with contextlib.redirect_stdout(io.StringIO()):
            audit = bridge.simulate_polaris_pipeline(
                "Solicitud de prueba",
                self.workspace,
                provider_fn=None,
            )

        self.assertFalse(audit["validacion_politica"]["aprobado"])
        self.assertNotIn("bwrap_args_generados", audit)
        self.assertIn("OFFLINE_MODE_ACTIVE", audit["propuesta_modelo"])
        self.assertEqual(self.urlopen_mock.call_count, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
