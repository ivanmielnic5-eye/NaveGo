#!/usr/bin/env python3
"""
Suite de Pruebas Unitarias - Motor de Política Determinista (Fase 1D/1E)
Verifica rechazos deterministas, el contrato estricto de tuplas de 3 elementos en todas las ramas,
y contención geométrica de rutas.
"""

import unittest
import json
import tempfile
from pathlib import Path
from policy_engine import validate_contract, build_bwrap_args_mock

class TestPolicyEngineComprehensive(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.test_dir.name).resolve()

        self.valid_file = self.workspace / "doc.txt"
        self.valid_file.write_text("contenido seguro", encoding="utf-8")

        self.nested_dir = self.workspace / "sub"
        self.nested_dir.mkdir(exist_ok=True)
        self.nested_file = self.nested_dir / "nested.txt"
        self.nested_file.write_text("contenido anidado", encoding="utf-8")

        self.evil_sibling = Path(f"{self.workspace}_evil")
        self.evil_sibling.mkdir(exist_ok=True)
        self.evil_file = self.evil_sibling / "secret.txt"
        self.evil_file.write_text("secreto del hermano", encoding="utf-8")

    def tearDown(self):
        self.test_dir.cleanup()
        if self.evil_sibling.exists():
            for f in self.evil_sibling.glob("*"):
                f.unlink()
            self.evil_sibling.rmdir()

    def test_tuple_contract_on_all_branches(self):
        cases = [
            '{"action": "read_file", "target": "doc.txt",}',
            json.dumps({"schema_version": "1.0", "action": "read_file", "purpose": "p", "requested_effect": "read_only"}),
            json.dumps({"schema_version": "1.0", "action": ["read_file"], "target": "doc.txt", "purpose": "p", "requested_effect": "read_only", "extra": 1}),
            json.dumps({"schema_version": "1.0", "action": "read_file", "target": "doc.txt", "purpose": "p", "requested_effect": "read_only"})
        ]
        for raw in cases:
            res = validate_contract(raw, self.workspace)
            self.assertIsInstance(res, tuple)
            self.assertEqual(len(res), 3)
            valid, reason, contract = res
            self.assertIsInstance(valid, bool)
            self.assertIsInstance(reason, str)
            if not valid:
                self.assertIsNone(contract)
            else:
                self.assertIsInstance(contract, dict)

    def test_01_json_malformado(self):
        raw = '{"action": "read_file", "target": "doc.txt",}'
        valid, reason, _ = validate_contract(raw, self.workspace)
        self.assertFalse(valid)
        self.assertTrue(reason.startswith("JSON_SYNTAX_ERROR"))

    def test_02_falta_campos_obligatorios(self):
        raw = json.dumps({
            "schema_version": "1.0",
            "action": "read_file",
            "purpose": "prueba",
            "requested_effect": "read_only"
        })
        valid, reason, _ = validate_contract(raw, self.workspace)
        self.assertFalse(valid)
        self.assertIn("SCHEMA_VIOLATION", reason)

    def test_03_tipos_incorrectos_y_campos_adicionales(self):
        raw = json.dumps({
            "schema_version": "1.0",
            "action": ["read_file"],
            "target": "doc.txt",
            "purpose": "prueba",
            "requested_effect": "read_only",
            "extra_field": "inyeccion"
        })
        valid, reason, _ = validate_contract(raw, self.workspace)
        self.assertFalse(valid)
        self.assertIn("SCHEMA_VIOLATION", reason)

    def test_04_schema_version_o_effect_incorrectos(self):
        raw = json.dumps({
            "schema_version": "2.0",
            "action": "read_file",
            "target": "doc.txt",
            "purpose": "prueba",
            "requested_effect": "read_only"
        })
        valid, reason, _ = validate_contract(raw, self.workspace)
        self.assertFalse(valid)
        self.assertIn("SCHEMA_VIOLATION", reason)

    def test_05_accion_fuera_lista_blanca(self):
        raw = json.dumps({
            "schema_version": "1.0",
            "action": "write_file",
            "target": "doc.txt",
            "purpose": "prueba",
            "requested_effect": "read_only"
        })
        valid, reason, _ = validate_contract(raw, self.workspace)
        self.assertFalse(valid)
        self.assertIn("SCHEMA_VIOLATION", reason)

    def test_06_ruta_absoluta_o_traversal(self):
        raw_abs = json.dumps({
            "schema_version": "1.0",
            "action": "read_file",
            "target": str(self.valid_file),
            "purpose": "prueba",
            "requested_effect": "read_only"
        })
        valid, reason, _ = validate_contract(raw_abs, self.workspace)
        self.assertFalse(valid)
        self.assertIn("SECURITY_VIOLATION", reason)

        raw_dotdot = json.dumps({
            "schema_version": "1.0",
            "action": "read_file",
            "target": "sub/../doc.txt",
            "purpose": "prueba",
            "requested_effect": "read_only"
        })
        valid_d, reason_d, _ = validate_contract(raw_dotdot, self.workspace)
        self.assertFalse(valid_d)
        self.assertIn("SECURITY_VIOLATION", reason_d)

    def test_07_enlace_simbolico_externo(self):
        symlink_path = self.workspace / "link_externo.txt"
        try:
            symlink_path.symlink_to(self.evil_file)
        except OSError:
            self.skipTest("El sistema de archivos no soporta symlinks en este entorno.")

        raw = json.dumps({
            "schema_version": "1.0",
            "action": "read_file",
            "target": "link_externo.txt",
            "purpose": "prueba_symlink",
            "requested_effect": "read_only"
        })
        valid, reason, _ = validate_contract(raw, self.workspace)
        self.assertFalse(valid)
        self.assertIn("SECURITY_VIOLATION", reason)

    def test_08_bypass_directorio_hermano(self):
        relative_bypass = f"../{self.evil_sibling.name}/secret.txt"
        raw = json.dumps({
            "schema_version": "1.0",
            "action": "read_file",
            "target": relative_bypass,
            "purpose": "prueba_bypass",
            "requested_effect": "read_only"
        })
        valid, reason, _ = validate_contract(raw, self.workspace)
        self.assertFalse(valid)
        self.assertIn("SECURITY_VIOLATION", reason)

    def test_09_contrato_valido_y_argumentos_anidados(self):
        raw = json.dumps({
            "schema_version": "1.0",
            "action": "read_file",
            "target": "sub/nested.txt",
            "purpose": "lectura_anidada",
            "requested_effect": "read_only"
        })
        valid, reason, data = validate_contract(raw, self.workspace)
        self.assertTrue(valid)
        self.assertEqual(reason, "CONTRACT_APPROVED")

        args = build_bwrap_args_mock(data, self.workspace)
        self.assertIsInstance(args, list)
        self.assertEqual(args[0], "/usr/bin/bwrap")
        self.assertIn(str(self.nested_file), args)
        self.assertIn("--dir", args)
        self.assertIn("/workspace/sub", args)

if __name__ == "__main__":
    unittest.main()
