#!/usr/bin/env python3
"""
LOGOS Kernel - Motor de Política Determinista (Fase 1D/1E - Corrección Estricta)
Propósito: Validación formal mediante jsonschema utilizando action_schema.json,
tuplas de retorno garantizadas de 3 elementos, contención estricta de rutas mediante
is_relative_to(), y generación segura de argumentos bwrap consumiendo la ruta validada.
"""

import json
from pathlib import Path
import jsonschema

ALLOWED_ACTIONS = {"read_file", "list_dir"}

def load_schema(schema_path: Path | None = None) -> dict:
    if schema_path is None:
        schema_path = Path(__file__).parent / "action_schema.json"

    if not schema_path.is_file():
        raise RuntimeError(f"CONFIG_ERROR: No se encuentra el archivo de esquema requerido en {schema_path}.")

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"CONFIG_ERROR: El esquema action_schema.json contiene JSON inválido: {exc}")

    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        raise RuntimeError(f"CONFIG_ERROR: El esquema action_schema.json no es un JSON Schema válido: {exc}")

    return schema

def validate_contract(raw_json: str, base_workspace: Path) -> tuple[bool, str, dict | None]:
    if not isinstance(base_workspace, Path):
        return False, "CONFIG_ERROR: base_workspace debe ser un objeto Path explícito.", None

    try:
        schema = load_schema()
    except RuntimeError as exc:
        return False, str(exc), None

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        return False, f"JSON_SYNTAX_ERROR: {e.msg} (line {e.lineno}, col {e.colno})", None

    if not isinstance(data, dict):
        return False, "SCHEMA_ERROR: El JSON raíz debe ser un objeto/diccionario.", None

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        return False, f"SCHEMA_VIOLATION: {e.message} (en path: {'/'.join(str(p) for p in e.path)})", None
    except Exception as exc:
        return False, f"SCHEMA_ERROR: Error inesperado validando esquema: {exc}", None

    target = data.get("target", "")

    if any(ord(c) < 32 or ord(c) == 127 for c in target):
        return False, "SECURITY_VIOLATION: La ruta contiene caracteres de control ASCII prohibidos.", None

    if target.startswith("/") or Path(target).is_absolute():
        return False, "SECURITY_VIOLATION: Se rechazan rutas absolutas.", None

    path_parts = Path(target).parts
    if ".." in path_parts:
        return False, "SECURITY_VIOLATION: Segmentos de navegación '..' prohibidos en la ruta objetivo.", None

    try:
        resolved_base = base_workspace.resolve(strict=True)
        resolved_path = (resolved_base / target).resolve(strict=False)

        if not resolved_path.is_relative_to(resolved_base):
            return False, "SECURITY_VIOLATION: La ruta resuelta escapa del workspace autorizado (Bypass de prefijo o traversal).", None
    except Exception as exc:
        return False, f"SECURITY_VIOLATION: Error al resolver la ruta: {exc}", None

    data["_resolved_target"] = str(resolved_path)
    return True, "CONTRACT_APPROVED", data

def build_bwrap_args_mock(contract: dict, base_workspace: Path) -> list[str]:
    target = contract["target"]
    action = contract["action"]

    resolved_target_str = contract.get("_resolved_target")
    if resolved_target_str:
        resolved_target = Path(resolved_target_str)
    else:
        resolved_target = (base_workspace.resolve() / target).resolve(strict=False)

    cmd = [
        "/usr/bin/bwrap",
        "--unshare-user",
        "--unshare-net",
        "--unshare-pid",
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--proc", "/proc",
        "--dir", "/usr",
        "--ro-bind", "/usr", "/usr",
        "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib", "/lib64",
        "--dir", "/workspace"
    ]

    target_path_obj = Path(target)
    if len(target_path_obj.parts) > 1:
        parent_parts = target_path_obj.parts[:-1]
        current_sub = Path("/workspace")
        for part in parent_parts:
            current_sub = current_sub / part
            cmd.extend(["--dir", str(current_sub)])

    cmd.extend([
        "--ro-bind", str(resolved_target), f"/workspace/{target}"
    ])

    if action == "read_file":
        cmd.extend(["--", "/usr/bin/cat", f"/workspace/{target}"])
    elif action == "list_dir":
        cmd.extend(["--", "/usr/bin/ls", "-la", f"/workspace/{target}"])

    return cmd
