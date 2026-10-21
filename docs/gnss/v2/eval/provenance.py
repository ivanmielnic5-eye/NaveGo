#!/usr/bin/env python3
"""Create and validate retrospective provenance manifests for NaveGo GNSS V2.

This tool is intentionally standalone: it does not run or modify the evaluator,
generators, input files, or existing result files. A manifest is written to a
separate path. It uses only the Python standard library.

Historical-run note: for existing runs, the original producing commit may not
have been recorded. The manifest therefore labels code hashes and Git state as
measured_at_audit_time instead of claiming that they were the run-time code.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

MANIFEST_TYPE = "navego-v2-provenance"
SCHEMA_VERSION = 1
RESULT_FILES = ("detail.jsonl", "by_scenario.csv", "summary.json")
CODE_DIRS = (
    "docs/gnss/v2/eval",
    "docs/gnss/v2/gtgen",
    "docs/gnss/v2/obsgen",
)

# Files whose identity matters for a V2 evaluation run. Generator files are
# fingerprinted as available context, not falsely claimed as proof of which
# source process originally produced pre-existing inputs.
RUNTIME_CODE_PATHS = (
    ("docs/gnss/v2/eval/run_all.py", "evaluator_source_at_run_start"),
    ("docs/gnss/v2/eval/methods.py", "method_implementation_source_at_run_start"),
    ("docs/gnss/v2/eval/metrics.py", "metrics_source_at_run_start"),
    ("docs/gnss/v2/eval/provenance.py", "provenance_tool_source_at_run_start"),
    ("docs/gnss/v2/gtgen/gen_traj.py", "upstream_generator_source_available_at_run_start"),
    ("docs/gnss/v2/obsgen/gen_obs.py", "upstream_generator_source_available_at_run_start"),
    ("tools/gnss_simulator.py", "upstream_simulator_source_available_at_run_start"),
    ("docs/gnss/v2/tests/test_recovery.py", "recovery_test_source_at_run_start"),
)


class ProvenanceError(Exception):
    """Invalid or unverifiable provenance data."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"No se pudo leer JSON {path}: {exc}") from exc


def repo_root_default() -> Path:
    # File location: <repo>/docs/gnss/v2/eval/provenance.py
    return Path(__file__).resolve().parents[4]


def safe_repo_file(raw_path: str | Path, repo_root: Path) -> Path:
    """Resolve a recorded path and require that it is a file inside the repo."""
    p = Path(raw_path)
    if not p.is_absolute():
        p = repo_root / p
    try:
        resolved = p.resolve(strict=True)
        resolved.relative_to(repo_root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ProvenanceError(f"Ruta inexistente o fuera del repositorio: {raw_path}") from exc
    if not resolved.is_file():
        raise ProvenanceError(f"No es un archivo regular: {raw_path}")
    return resolved


def relpath(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def file_record(path: Path, repo_root: Path, role: str) -> dict[str, Any]:
    return {
        "path": relpath(path, repo_root),
        "role": role,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "hash_observed_at": "manifest_generation_time",
    }


def git_state(repo_root: Path) -> dict[str, Any]:
    state: dict[str, Any] = {
        "commit_at_audit_time": None,
        "available": False,
        "dirty_tree_at_audit_time": None,
        "modified_count_at_audit_time": None,
        "untracked_count_at_audit_time": None,
        "tracked_diff_sha256_at_audit_time": None,
    }
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=repo_root,
            capture_output=True, text=True, check=True,
        ).stdout
        diff = subprocess.run(
            ["git", "diff", "--binary", "HEAD"], cwd=repo_root,
            capture_output=True, check=True,
        ).stdout
        lines = [line for line in status.splitlines() if line.strip()]
        modified = sum(not line[3:].startswith("?? ") and line[:2] != "??" for line in lines)
        untracked = sum(line[:2] == "??" for line in lines)
        state.update({
            "commit_at_audit_time": commit,
            "available": True,
            "dirty_tree_at_audit_time": bool(lines),
            "modified_count_at_audit_time": modified,
            "untracked_count_at_audit_time": untracked,
            "tracked_diff_sha256_at_audit_time": hashlib.sha256(diff).hexdigest(),
        })
    except (OSError, subprocess.CalledProcessError):
        # A manifest can still be useful without Git, but its limitation is explicit.
        pass
    return state


def load_detail(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ProvenanceError(f"detail.jsonl línea {line_no}: JSON inválido: {exc}") from exc
                if not isinstance(row, dict):
                    raise ProvenanceError(f"detail.jsonl línea {line_no}: cada registro debe ser objeto JSON")
                required = ("fixes_path", "gt_path", "obs_events_path", "fix_hash", "scenario", "traj", "seed", "method")
                missing = [key for key in required if key not in row]
                if missing:
                    raise ProvenanceError(f"detail.jsonl línea {line_no}: faltan claves {missing}")
                rows.append(row)
    except OSError as exc:
        raise ProvenanceError(f"No se pudo leer {path}: {exc}") from exc
    if not rows:
        raise ProvenanceError("detail.jsonl no contiene evaluaciones")
    return rows


def code_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for directory in CODE_DIRS:
        base = repo_root / directory
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.py")):
            if path.name == "provenance.py":
                # The audit utility did not produce the historical experiment.
                continue
            key = relpath(path, repo_root)
            if key not in seen:
                records.append(file_record(path, repo_root, "experimental_source_code_at_audit_time"))
                seen.add(key)
    simulator = repo_root / "tools/gnss_simulator.py"
    if simulator.is_file():
        key = relpath(simulator, repo_root)
        if key not in seen:
            records.append(file_record(simulator, repo_root,
                                       "upstream_simulator_source_at_audit_time"))
            seen.add(key)
    if not records:
        raise ProvenanceError("No se encontraron scripts fuente para registrar")
    return records


def runtime_code_records(repo_root: Path, observed_at: str) -> list[dict[str, Any]]:
    """Hash the source files relevant to a run, with honest role labels."""
    records: list[dict[str, Any]] = []
    for rel, role in RUNTIME_CODE_PATHS:
        path = safe_repo_file(rel, repo_root)
        records.append({
            "path": rel,
            "role": role,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "hash_observed_at_utc": observed_at,
        })
    return records


def capture_runtime_snapshot(
    repo_root: Path,
    run_id: str,
    phase: str,
    command: list[str],
) -> dict[str, Any]:
    """Capture code/Git/environment fingerprints before evaluating rows.

    This is not a cryptographic attestation of loaded machine code. It records
    the source files visible on disk at run start, then the finalizer checks
    that those files still match after output creation.
    """
    repo_root = Path(repo_root).resolve(strict=True)
    captured_at = utc_now()
    records = runtime_code_records(repo_root, captured_at)
    return {
        "captured_at_utc": captured_at,
        "run_id": run_id,
        "phase": phase,
        "command": [str(part) for part in command],
        "python_version": sys.version,
        "platform": platform.platform(),
        "git_state_at_run_start": git_state(repo_root),
        "code_artifacts_at_run_start": records,
        "capture_semantics": (
            "Huella de archivos fuente al inicio. Es evidencia de los bytes visibles "
            "en disco, no una atestación criptográfica del código cargado por el proceso."
        ),
    }


def create_manifest(
    run_dir: Path, output_path: Path, repo_root: Path,
    runtime_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    run_dir = safe_repo_file(run_dir / "detail.jsonl", repo_root).parent
    run_rel = relpath(run_dir, repo_root)
    if "/results/" not in f"/{run_rel}/":
        raise ProvenanceError(f"La corrida no está bajo un directorio results: {run_rel}")

    if output_path.exists():
        raise ProvenanceError(f"El destino ya existe; por seguridad no se sobrescribe: {output_path}")
    # Output must also reside inside the repository; this keeps paths relocatable.
    output_parent = output_path.parent.resolve() if output_path.parent.exists() else output_path.parent
    try:
        output_parent.resolve().relative_to(repo_root)
    except ValueError as exc:
        raise ProvenanceError("El manifiesto de salida debe guardarse dentro del repositorio") from exc

    summary_path = safe_repo_file(run_dir / "summary.json", repo_root)
    detail_path = safe_repo_file(run_dir / "detail.jsonl", repo_root)
    csv_path = safe_repo_file(run_dir / "by_scenario.csv", repo_root)
    summary = read_json(summary_path)
    rows = load_detail(detail_path)
    if summary.get("n_rows") is not None and int(summary["n_rows"]) != len(rows):
        raise ProvenanceError(
            f"Inconsistencia interna: summary.json declara n_rows={summary['n_rows']} pero detail.jsonl contiene {len(rows)} registros"
        )
    output_by_name = {"detail.jsonl": detail_path, "by_scenario.csv": csv_path, "summary.json": summary_path}

    inputs: dict[str, dict[str, Any]] = {}
    evaluations: list[dict[str, Any]] = []
    group_hashes: dict[tuple[str, int], set[str]] = {}
    row_key_seen: set[tuple[str, int, str]] = set()

    for index, row in enumerate(rows, 1):
        fixes = safe_repo_file(row["fixes_path"], repo_root)
        gt = safe_repo_file(row["gt_path"], repo_root)
        events = safe_repo_file(row["obs_events_path"], repo_root)
        fixes_hash = sha256_file(fixes)
        expected_row_hash = str(row["fix_hash"]).lower()
        if expected_row_hash != fixes_hash:
            raise ProvenanceError(
                f"Fila {index}: fix_hash guardado no coincide con el archivo: {row['scenario']}/seed={row['seed']}/method={row['method']}"
            )
        event_data = read_json(events)
        expected_events_hash = event_data.get("fixes_sha256")
        if not expected_events_hash:
            raise ProvenanceError(f"Falta fixes_sha256 en archivo de eventos: {relpath(events, repo_root)}")
        if str(expected_events_hash).lower() != fixes_hash:
            raise ProvenanceError(f"fixes_sha256 de eventos no coincide: {relpath(events, repo_root)}")

        group = (str(row["scenario"]), int(row["seed"]))
        group_hashes.setdefault(group, set()).add(fixes_hash)
        row_key = (group[0], group[1], str(row["method"]))
        if row_key in row_key_seen:
            raise ProvenanceError(f"Evaluación duplicada para scenario/seed/method: {row_key}")
        row_key_seen.add(row_key)

        gt_event = repo_root / "docs/gnss/v2/gtgen/events" / f"traj_events_{row['traj']}_{row['seed']}.json"
        if not gt_event.is_file():
            raise ProvenanceError(
                f"Faltan los metadatos de eventos del ground truth: {relpath(gt_event, repo_root)}"
            )
        roles = ((fixes, "synthetic_gnss_fixes"), (gt, "ground_truth_trajectory"),
                 (events, "observation_events_and_gnss_configuration"))
        for path, role in roles:
            rel = relpath(path, repo_root)
            inputs.setdefault(rel, file_record(path, repo_root, role))
        gt_event = safe_repo_file(gt_event, repo_root)
        gt_event_rel = relpath(gt_event, repo_root)
        inputs.setdefault(gt_event_rel, file_record(gt_event, repo_root, "ground_truth_event_metadata"))

        evaluations.append({
            "scenario": str(row["scenario"]),
            "trajectory_id": str(row["traj"]),
            "seed": int(row["seed"]),
            "method": str(row["method"]),
            "variant": row.get("variant"),
            "fixes_path": relpath(fixes, repo_root),
            "fixes_sha256": fixes_hash,
            "ground_truth_path": relpath(gt, repo_root),
            "observation_events_path": relpath(events, repo_root),
            "ground_truth_event_metadata_path": gt_event_rel,
            "gnss_configuration_from_event_file": event_data.get("gnss_cfg"),
        })

    parity_failures = {f"{s}/seed={seed}": sorted(hashes) for (s, seed), hashes in group_hashes.items() if len(hashes) > 1}
    if parity_failures:
        raise ProvenanceError(f"Paridad de fijaciones fallida entre métodos: {parity_failures}")

    outputs = [file_record(output_by_name[name], repo_root, "experiment_result_output") for name in RESULT_FILES]
    # Store relative paths for all outputs (file_record already does so).
    manifest = {
        "manifest_type": MANIFEST_TYPE,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "audit_mode": "runtime_capture" if runtime_snapshot is not None else "retrospective_existing_run",
        "historical_code_attribution": {
            "status": "captured_at_run_start" if runtime_snapshot is not None else "not_recorded_at_original_run_time",
            "explanation": (
                "Se registraron hashes de las fuentes al comienzo de la evaluación y se compararon al terminar. "
                "Esto mejora la procedencia de ejecución, pero no es una atestación criptográfica del código cargado."
                if runtime_snapshot is not None else
                "Los hashes de código y el estado de Git de este manifiesto se midieron al generar esta auditoría; no prueban qué commit produjo originalmente esta corrida."
            )
        },
        "run": {
            "run_id": run_dir.name,
            "run_path": run_rel,
            "phase": summary.get("phase"),
            "timestamp_recorded_in_summary": summary.get("timestamp"),
            "n_rows_detail": len(rows),
            "n_rows_summary": summary.get("n_rows"),
            "n_missing_summary": summary.get("n_missing"),
            "criteria_statuses": {k: v.get("status") for k, v in summary.get("criteria", {}).items() if isinstance(v, dict)},
        },
        "code_state_at_audit_time": git_state(repo_root),
        "code_artifacts_at_audit_time": code_records(repo_root),
        "input_artifacts": sorted(inputs.values(), key=lambda x: x["path"]),
        "evaluations": evaluations,
        "output_artifacts": outputs,
        "integrity_model": {
            "algorithm": "SHA-256",
            "manifest_self_hash": "not_included_to_avoid_self_reference",
            "authenticity_note": "Un manifiesto y sus hashes pueden alterarse conjuntamente; SHA-256 detecta diferencias frente a una copia confiable, pero no autentica por sí solo al autor."
        },
    }
    if runtime_snapshot is not None:
        # Capture the same source files at end and compare byte fingerprints.
        end_time = utc_now()
        end_code = runtime_code_records(repo_root, end_time)
        start_by_path = {item["path"]: item for item in runtime_snapshot["code_artifacts_at_run_start"]}
        end_by_path = {item["path"]: item for item in end_code}
        comparisons = []
        for rel, start_item in start_by_path.items():
            end_item = end_by_path.get(rel)
            unchanged = bool(end_item and start_item.get("sha256") == end_item.get("sha256"))
            comparisons.append({
                "path": rel,
                "sha256_at_run_start": start_item.get("sha256"),
                "sha256_at_run_end": end_item.get("sha256") if end_item else None,
                "unchanged_during_run": unchanged,
            })
        start_commit = runtime_snapshot.get("git_state_at_run_start", {}).get("commit_at_audit_time")
        end_git_state = git_state(repo_root)
        end_commit = end_git_state.get("commit_at_audit_time")
        manifest["run_execution"] = {
            "capture_started_at_utc": runtime_snapshot["captured_at_utc"],
            "capture_finished_at_utc": end_time,
            "run_id": runtime_snapshot["run_id"],
            "phase": runtime_snapshot["phase"],
            "command": runtime_snapshot["command"],
            "python_version": runtime_snapshot["python_version"],
            "platform": runtime_snapshot["platform"],
            "git_state_at_run_start": runtime_snapshot["git_state_at_run_start"],
            "git_state_at_run_end": end_git_state,
            "code_artifacts_at_run_start": runtime_snapshot["code_artifacts_at_run_start"],
            "code_artifacts_at_run_end": end_code,
            "code_file_comparison": comparisons,
            "source_files_unchanged_during_run": bool(comparisons) and all(
                item["unchanged_during_run"] for item in comparisons
            ),
            "git_commit_unchanged_during_run": (
                start_commit == end_commit if start_commit and end_commit else None
            ),
            "capture_semantics": runtime_snapshot["capture_semantics"],
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create; do not overwrite a pre-existing audit artifact.
    with output_path.open("x", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return manifest


def validate_manifest(manifest_path: Path, repo_root: Path) -> list[str]:
    repo_root = repo_root.resolve(strict=True)
    manifest_path = safe_repo_file(manifest_path, repo_root)
    manifest = read_json(manifest_path)
    errors: list[str] = []
    if manifest.get("manifest_type") != MANIFEST_TYPE:
        errors.append("manifest_type desconocido")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version no soportada: {manifest.get('schema_version')}")

    seen_asset_paths: set[str] = set()
    sections = ["input_artifacts", "code_artifacts_at_audit_time", "output_artifacts"]
    if manifest.get("audit_mode") == "runtime_capture":
        sections.extend([
            "run_execution.code_artifacts_at_run_start",
            "run_execution.code_artifacts_at_run_end",
        ])
    for section in sections:
        if section.startswith("run_execution."):
            assets = manifest.get("run_execution", {}).get(section.split(".", 1)[1])
        else:
            assets = manifest.get(section)
        if not isinstance(assets, list):
            errors.append(f"{section} debe ser una lista")
            continue
        for asset in assets:
            if not isinstance(asset, dict) or not all(k in asset for k in ("path", "sha256", "size_bytes")):
                errors.append(f"Registro de artefacto inválido en {section}")
                continue
            rel = asset["path"]
            if rel in seen_asset_paths and section != "input_artifacts":
                # A code file may be listed only in its own section; output/input overlaps are noteworthy.
                pass
            seen_asset_paths.add(rel)
            try:
                path = safe_repo_file(rel, repo_root)
            except ProvenanceError as exc:
                errors.append(str(exc))
                continue
            actual = sha256_file(path)
            if actual != asset["sha256"]:
                errors.append(f"SHA-256 no coincide: {rel}")
            if path.stat().st_size != asset["size_bytes"]:
                errors.append(f"Tamaño no coincide: {rel}")

    parity: dict[tuple[str, int], set[str]] = {}
    for evaluation in manifest.get("evaluations", []):
        try:
            key = (str(evaluation["scenario"]), int(evaluation["seed"]))
            parity.setdefault(key, set()).add(str(evaluation["fixes_sha256"]))
            fix_path = safe_repo_file(evaluation["fixes_path"], repo_root)
            if sha256_file(fix_path) != evaluation["fixes_sha256"]:
                errors.append(f"El hash de fijaciones de la evaluación no coincide: {evaluation['fixes_path']}")
        except (KeyError, TypeError, ValueError, ProvenanceError) as exc:
            errors.append(f"Evaluación inválida: {exc}")
    for (scenario, seed), hashes in parity.items():
        if len(hashes) > 1:
            errors.append(f"Paridad rota entre métodos: {scenario}/seed={seed}")

    input_by_path = {
        item.get("path"): item for item in manifest.get("input_artifacts", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    for evaluation in manifest.get("evaluations", []):
        if not isinstance(evaluation, dict):
            continue
        for field in ("fixes_path", "ground_truth_path", "observation_events_path"):
            path_key = evaluation.get(field)
            if path_key not in input_by_path:
                errors.append(f"La evaluación referencia un insumo que no está en input_artifacts: {path_key}")
        events_rel = evaluation.get("observation_events_path")
        try:
            if events_rel:
                event_obj = read_json(safe_repo_file(events_rel, repo_root))
                if str(event_obj.get("fixes_sha256", "")).lower() != str(evaluation.get("fixes_sha256", "")).lower():
                    errors.append(f"El fixes_sha256 embebido en eventos no coincide: {events_rel}")
        except ProvenanceError as exc:
            errors.append(str(exc))

    attribution_status = manifest.get("historical_code_attribution", {}).get("status")
    if manifest.get("audit_mode") == "runtime_capture":
        if attribution_status != "captured_at_run_start":
            errors.append("Una corrida con captura de ejecución debe declararse captured_at_run_start")
        runtime = manifest.get("run_execution")
        if not isinstance(runtime, dict):
            errors.append("Falta run_execution en manifiesto runtime_capture")
        else:
            if runtime.get("source_files_unchanged_during_run") is not True:
                errors.append("Una o más fuentes cambiaron entre el inicio y el final de la corrida")
            if runtime.get("git_commit_unchanged_during_run") is False:
                errors.append("El commit de Git cambió durante la corrida")
            if not runtime.get("capture_started_at_utc") or not runtime.get("capture_finished_at_utc"):
                errors.append("Faltan marcas de tiempo de inicio/fin de la captura")
    elif attribution_status != "not_recorded_at_original_run_time":
        errors.append("La atribución histórica retrospectiva del código debe declararse explícitamente")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None, help="Raíz del repositorio; por defecto se deduce desde este script")
    sub = parser.add_subparsers(dest="command", required=True)
    p_create = sub.add_parser("create", help="Crear manifiesto retrospectivo sin alterar la corrida")
    p_create.add_argument("--run", required=True, type=Path, help="Directorio de la corrida existente")
    p_create.add_argument("--output", required=True, type=Path, help="Ruta nueva para guardar el manifiesto")
    p_validate = sub.add_parser("validate", help="Verificar los artefactos registrados en el manifiesto")
    p_validate.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)
    repo_root = (args.repo_root or repo_root_default()).resolve()
    try:
        if args.command == "create":
            run_dir = args.run if args.run.is_absolute() else repo_root / args.run
            output_path = args.output if args.output.is_absolute() else repo_root / args.output
            manifest = create_manifest(run_dir, output_path, repo_root)
            print(f"[MANIFEST PASS] Creado: {output_path}")
            print(f"Corrida: {manifest['run']['run_id']} | evaluaciones={manifest['run']['n_rows_detail']}")
            print(f"Entradas únicas={len(manifest['input_artifacts'])} | fuentes={len(manifest['code_artifacts_at_audit_time'])} | salidas={len(manifest['output_artifacts'])}")
            print("Aviso: la atribución del código de esta corrida es retrospectiva, no histórica.")
            return 0
        errors = validate_manifest(args.manifest if args.manifest.is_absolute() else repo_root / args.manifest, repo_root)
        if errors:
            print("[MANIFEST FAIL]")
            for error in errors:
                print(f" - {error}")
            return 1
        print("[MANIFEST PASS] Todos los artefactos registrados coinciden con sus hashes y tamaños.")
        print("Esto verifica integridad respecto del manifiesto, no autoría criptográfica.")
        return 0
    except (ProvenanceError, OSError, json.JSONDecodeError) as exc:
        print(f"[MANIFEST ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
