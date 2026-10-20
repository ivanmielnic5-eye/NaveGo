#!/usr/bin/env python3
"""Pruebas unitarias de las salvaguardas de logos-pendiente."""

import importlib.util
from importlib.machinery import SourceFileLoader
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".logos/bin/logos-pendiente"

loader = SourceFileLoader("logos_pendiente_tested", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
if spec is None:
    raise RuntimeError(f"No se pudo cargar {SCRIPT}")
APP = importlib.util.module_from_spec(spec)
loader.exec_module(APP)


class PendingCoordinatorTests(unittest.TestCase):
    def fixture_text(self):
        lines = [
            "### P47 — Anterior",
            "- Estado: PENDIENTE.",
            "- Nota: conservar.",
            "",
            "### P48 — Coordinador",
            "- Estado: PENDIENTE.",
            "- Objetivo: probar.",
            "",
            "### P49 — Siguiente",
            "- Estado: PENDIENTE.",
            "- Nota: no tocar.",
        ]
        return chr(10).join(lines) + chr(10)

    def test_section_only_returns_requested_pending(self):
        text = self.fixture_text()
        block = APP.section(text, "P48")
        self.assertIn("### P48", block)
        self.assertNotIn("P47", block)
        self.assertNotIn("P49", block)

    def test_duplicate_or_missing_pending_is_rejected(self):
        text = self.fixture_text()
        with self.assertRaises(ValueError):
            APP.section(text, "P99")
        with self.assertRaises(ValueError):
            APP.section(text + "\n### P48 — Duplicado\n", "P48")

    def test_decisions_are_appended_inside_correct_section(self):
        with tempfile.TemporaryDirectory(prefix="logos-pending-test-") as tmp:
            path = Path(tmp) / "PENDIENTES.md"
            original = self.fixture_text()
            path.write_text(original, encoding="utf-8")
            args = SimpleNamespace(
                pending_id="P48",
                nota="prueba controlada",
                fase="implementacion",
                decision="ACEPTO",
            )
            with mock.patch.object(APP, "PENDING", path):
                self.assertEqual(APP.cmd_decision(args), 0)
                args.nota = "segunda decisión para conservar historial"
                self.assertEqual(APP.cmd_decision(args), 0)

            changed = path.read_text(encoding="utf-8")
            block = APP.section(changed, "P48")
            self.assertIn("prueba controlada", block)
            self.assertIn("segunda decisión para conservar historial", block)
            self.assertEqual(APP.section(changed, "P47"),
                             APP.section(original, "P47"))
            self.assertEqual(APP.section(changed, "P49"),
                             APP.section(original, "P49"))

    def test_close_rejects_wrong_confirmation_without_writing(self):
        with tempfile.TemporaryDirectory(prefix="logos-pending-test-") as tmp:
            path = Path(tmp) / "PENDIENTES.md"
            original = self.fixture_text()
            path.write_text(original, encoding="utf-8")
            args = SimpleNamespace(
                pending_id="P48",
                confirm="CIERRE P48",
                test=[],
            )
            with mock.patch.object(APP, "PENDING", path):
                self.assertEqual(APP.cmd_cerrar(args), 2)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_close_requires_director_acceptance(self):
        with tempfile.TemporaryDirectory(prefix="logos-pending-test-") as tmp:
            path = Path(tmp) / "PENDIENTES.md"
            original = self.fixture_text()
            path.write_text(original, encoding="utf-8")
            args = SimpleNamespace(
                pending_id="P48",
                confirm="CERRAR P48",
                test=[],
            )
            with mock.patch.object(APP, "PENDING", path):
                self.assertEqual(APP.cmd_cerrar(args), 2)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_prepare_rejects_parent_directory_path(self):
        args = SimpleNamespace(path=["../fuera"], test=[])
        self.assertEqual(APP.cmd_preparar(args), 2)


    def test_reconcile_rejects_undocumented_nonzero(self):
        result = SimpleNamespace(
            returncode=1,
            stdout="UPDATED: MANIFEST modificado correctamente",
            stderr="root of trust ausente",
        )
        with mock.patch.object(APP.subprocess, "run", return_value=result):
            self.assertFalse(APP.reconcile_pending())

    def test_reconcile_accepts_documented_missing_trust_warning(self):
        result = SimpleNamespace(
            returncode=1,
            stdout=(
                "[logos-reconcile] trust: ABSENT\\n"
                "[logos-reconcile] UPDATED: MANIFEST modificado correctamente\\n"
                "[logos-reconcile] NOTA: exit code = 1 indica WARNING "
                "(trust no existe). El mark-reviewed se aplicó correctamente.\\n"
            ),
            stderr="",
        )
        with mock.patch.object(APP.subprocess, "run", return_value=result):
            self.assertTrue(APP.reconcile_pending())

    def test_restore_refuses_concurrent_change(self):
        with tempfile.TemporaryDirectory(prefix="logos-pending-rollback-") as tmp:
            path = Path(tmp) / "PENDIENTES.md"
            path.write_text("cambio concurrente\n", encoding="utf-8")
            with mock.patch.object(APP, "PENDING", path):
                restored = APP.restore_pending_if_unchanged(
                    "contenido escrito por el coordinador\n",
                    "contenido original\n",
                )
            self.assertFalse(restored)
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "cambio concurrente\n",
            )

    def test_restore_original_when_content_matches_expected(self):
        with tempfile.TemporaryDirectory(prefix="logos-pending-rollback-") as tmp:
            path = Path(tmp) / "PENDIENTES.md"
            path.write_text("contenido escrito por el coordinador\n", encoding="utf-8")
            with mock.patch.object(APP, "PENDING", path):
                restored = APP.restore_pending_if_unchanged(
                    "contenido escrito por el coordinador\n",
                    "contenido original\n",
                )
            self.assertTrue(restored)
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "contenido original\n",
            )



if __name__ == "__main__":
    unittest.main(verbosity=2)
