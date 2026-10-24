import contextlib
import io
import json
import unittest
from unittest.mock import patch

import sandbox_executor as executor


class TestSandboxExecutorGuardrails(unittest.TestCase):
    def proposal(self, action="read_file", target="informe.txt", extra=None):
        data = {
            "schema_version": "1.0",
            "action": action,
            "target": target,
            "purpose": "Prueba controlada de solo lectura",
            "requested_effect": "read_only",
        }
        if extra:
            data.update(extra)
        return json.dumps(data)

    def run_mocked(self, raw, tamper_args=False):
        output = io.StringIO()

        with (
            patch.object(
                executor.bridge, "query_model_safe", return_value=raw
            ),
            patch.object(executor.subprocess, "run") as process,
            contextlib.redirect_stdout(output),
        ):
            if tamper_args:
                with patch.object(
                    executor,
                    "build_bwrap_args_mock",
                    return_value=[
                        "/usr/bin/bwrap", "--",
                        "/usr/bin/id",
                    ],
                ):
                    executor.main()
            else:
                executor.main()

        return output.getvalue(), process

    def assert_rejected_without_execution(self, raw, tamper_args=False):
        output, process = self.run_mocked(raw, tamper_args)
        self.assertIn("EJECUCION_BWRAP=NO", output)
        self.assertIn("RESULTADO=RECHAZADO_SIN_EJECUCION", output)
        process.assert_not_called()

    def test_path_traversal_no_ejecuta(self):
        self.assert_rejected_without_execution(
            self.proposal(target="../../etc/passwd")
        )

    def test_campo_adicional_no_ejecuta(self):
        self.assert_rejected_without_execution(
            self.proposal(extra={"command": "rm -rf /"})
        )

    def test_accion_no_permitida_por_el_ejecutor_no_ejecuta(self):
        self.assert_rejected_without_execution(
            self.proposal(action="list_dir")
        )

    def test_objetivo_distinto_no_ejecuta(self):
        self.assert_rejected_without_execution(
            self.proposal(target="otro.txt")
        )

    def test_argumentos_alterados_no_ejecutan(self):
        self.assert_rejected_without_execution(
            self.proposal(),
            tamper_args=True,
        )


if __name__ == "__main__":
    unittest.main()
