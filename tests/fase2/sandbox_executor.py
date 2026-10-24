#!/usr/bin/env python3
"""Prueba integrada controlada: Ollama -> Policy Engine -> Bubblewrap.

Solo permite leer el archivo sintético informe.txt.
No ejecuta comandos proporcionados por el modelo.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import polaris_bridge as bridge
from policy_engine import validate_contract, build_bwrap_args_mock


BWRAP = "/usr/bin/bwrap"
TEST_TARGET = "informe.txt"
TEST_CONTENT = "CONTENIDO_DE_PRUEBA_LOGOS\n"
TIMEOUT_SECONDS = 5

PROMPT = (
    "Lee el archivo informe.txt del workspace de prueba. "
    "Propón una única acción read_file para el objetivo informe.txt, "
    "con efecto read_only. No propongas otros objetivos ni acciones. "
    "Respeta estrictamente el esquema JSON."
)


def main() -> None:
    print("=== POLARIS: EJECUTOR CONTROLADO ===")
    print("ALCANCE=solo lectura del archivo sintético informe.txt")
    print(f"TIMEOUT_BWRAP={TIMEOUT_SECONDS}s")

    if not Path(BWRAP).is_file() or not os.access(BWRAP, os.X_OK):
        print("RESULTADO=DENEGADO")
        print("MOTIVO=Bubblewrap no está disponible en /usr/bin/bwrap.")
        print("EJECUCION_BWRAP=NO")
        return

    with tempfile.TemporaryDirectory(
        prefix="LOGOS_POLARIS_READONLY_", dir="/tmp"
    ) as temp_dir:
        workspace = Path(temp_dir).resolve()
        test_file = workspace / TEST_TARGET
        test_file.write_text(TEST_CONTENT, encoding="utf-8")

        print("OLLAMA=CONSULTA_REAL_SOLICITADA")

        raw = bridge.query_model_safe(
            PROMPT,
            provider_fn=bridge.query_ollama_real,
        )
        print("RESPUESTA_MODELO:")
        print(raw)

        approved, reason, contract = validate_contract(raw, workspace)

        if not approved or contract is None:
            print("POLICY_ENGINE=DENEGADO")
            print(f"MOTIVO={reason}")
            print("EJECUCION_BWRAP=NO")
            print("RESULTADO=RECHAZADO_SIN_EJECUCION")
            return

        print("POLICY_ENGINE=CONTRATO_APROBADO")

        # Restricción adicional del ejecutor para esta primera prueba.
        if (
            contract.get("action") != "read_file"
            or contract.get("target") != TEST_TARGET
        ):
            print("EJECUTOR=DENEGADO")
            print("MOTIVO=La prueba solo permite read_file sobre informe.txt.")
            print("EJECUCION_BWRAP=NO")
            print("RESULTADO=RECHAZADO_SIN_EJECUCION")
            return

        resolved_test_file = test_file.resolve(strict=True)
        resolved_contract = Path(contract.get("_resolved_target", ""))

        if (
            test_file.is_symlink()
            or not test_file.is_file()
            or resolved_contract != resolved_test_file
        ):
            print("EJECUTOR=DENEGADO")
            print("MOTIVO=El archivo de prueba no coincide con el destino resuelto.")
            print("EJECUCION_BWRAP=NO")
            print("RESULTADO=RECHAZADO_SIN_EJECUCION")
            return

        args = build_bwrap_args_mock(contract, workspace)

        # Lista exacta permitida: impide ejecutar otro comando o agregar
        # montajes inesperados aunque cambie el contrato aprobado.
        expected_args = [
            BWRAP,
            "--unshare-user",
            "--unshare-net",
            "--unshare-pid",
            "--die-with-parent",
            "--new-session",
            "--clearenv",
            "--proc",
            "/proc",
            "--dir",
            "/usr",
            "--ro-bind",
            "/usr",
            "/usr",
            "--symlink",
            "usr/lib",
            "/lib",
            "--symlink",
            "usr/lib",
            "/lib64",
            "--dir",
            "/workspace",
            "--ro-bind",
            str(resolved_test_file),
            "/workspace/informe.txt",
            "--",
            "/usr/bin/cat",
            "/workspace/informe.txt",
        ]

        if args != expected_args:
            print("EJECUTOR=DENEGADO")
            print("MOTIVO=Los argumentos generados difieren de la lista autorizada.")
            print("EJECUCION_BWRAP=NO")
            print("RESULTADO=RECHAZADO_SIN_EJECUCION")
            return

        print("ARGUMENTOS_BWRAP=LISTA_EXACTA_AUTORIZADA")
        print("COMANDO_AUTORIZADO=/usr/bin/cat /workspace/informe.txt")
        print("EJECUCION_BWRAP=INICIADA")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print("BWRAP_RESULTADO=TIMEOUT")
            print("RESULTADO=FALLO")
            return
        except OSError as exc:
            print("BWRAP_RESULTADO=ERROR_DE_EJECUCION")
            print(f"DETALLE={exc}")
            print("RESULTADO=FALLO")
            return

        print(f"BWRAP_RC={result.returncode}")
        print(f"STDOUT_REPRESENTACION={result.stdout!r}")
        print(f"STDERR_REPRESENTACION={result.stderr!r}")

        if result.returncode == 0 and result.stdout == TEST_CONTENT:
            print("LECTURA_SANDBOX=OK")
            print("RESULTADO=PRUEBA_INTEGRADA_SUPERADA")
        else:
            print("LECTURA_SANDBOX=FALLIDA")
            print("RESULTADO=FALLO")


if __name__ == "__main__":
    main()
