#!/usr/bin/env python3
"""Pruebas de regresión P32 para la biblioteca de hashing y sus consumidores."""

import builtins
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from types import SimpleNamespace
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[2]
LIB_PATH = ROOT / ".logos/lib/logos_hash_lib.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el módulo: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LIB = load_module("p32_hash_lib_under_test", LIB_PATH)


def run_git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Falló git {args} en {repo}: {result.stderr}"
        )
    return result


def create_git_source(repo):
    """Crea un repo temporal con un archivo rastreado en un subdirectorio."""
    blocked = repo / "directorio_bloqueado"
    blocked.mkdir(parents=True)
    (blocked / "archivo.txt").write_text(
        "contenido de prueba\n", encoding="utf-8"
    )
    run_git(repo, "init", "-q")
    run_git(repo, "add", "directorio_bloqueado/archivo.txt")
    return blocked


class HashLibraryTests(unittest.TestCase):
    def test_file_hash_matches_sha256(self):
        with tempfile.TemporaryDirectory(prefix="p32-file-") as tmp:
            path = pathlib.Path(tmp) / "archivo.txt"
            content = b"contenido de prueba\n"
            path.write_bytes(content)

            digest, count, kind = LIB.hash_source(str(path))

            self.assertEqual(digest, hashlib.sha256(content).hexdigest())
            self.assertEqual(count, 1)
            self.assertEqual(kind, "ARCHIVO")

    def test_standard_directory_preserves_hash_semantics(self):
        with tempfile.TemporaryDirectory(prefix="p32-dir-") as tmp:
            directory = pathlib.Path(tmp)
            (directory / "subdir").mkdir()
            (directory / "a.txt").write_text("alfa\n", encoding="utf-8")
            (directory / "subdir/b.txt").write_text(
                "beta\n", encoding="utf-8"
            )
            os.symlink("a.txt", directory / "enlace.txt")

            entries = [
                ("a.txt", directory / "a.txt"),
                ("subdir/b.txt", directory / "subdir/b.txt"),
                ("enlace.txt", directory / "enlace.txt"),
            ]
            entries.sort(key=lambda entry: entry[0].encode("utf-8"))

            expected = hashlib.sha256()
            for relative, full in entries:
                expected.update(relative.encode("utf-8"))
                expected.update(b"\x00")
                if os.path.islink(full):
                    expected.update(b"LINK:" + os.readlink(full).encode("utf-8"))
                    expected.update(b"\x00")
                else:
                    content = full.read_bytes()
                    expected.update(str(len(content)).encode("utf-8"))
                    expected.update(b"\x00")
                    expected.update(content)

            digest, count, kind = LIB.hash_source(str(directory))

            self.assertEqual(digest, expected.hexdigest())
            self.assertEqual(count, 3)
            self.assertEqual(kind, "DIRECTORIO")

    def test_missing_path_remains_no_existe(self):
        with tempfile.TemporaryDirectory(prefix="p32-missing-") as tmp:
            missing = pathlib.Path(tmp) / "no_existe"
            self.assertEqual(
                LIB.hash_source(str(missing)),
                (None, 0, "NO_EXISTE"),
            )

    def test_source_stat_permission_becomes_hash_error(self):
        with tempfile.TemporaryDirectory(prefix="p32-stat-error-") as tmp:
            source = pathlib.Path(tmp) / "fuente"
            source.mkdir()
            real_stat = LIB.os.stat
            target = str(source)

            def simulated_stat(path, *args, **kwargs):
                if os.fspath(path) == target:
                    raise PermissionError("fallo de stat simulado")
                return real_stat(path, *args, **kwargs)

            with mock.patch.object(
                LIB.os, "stat", side_effect=simulated_stat
            ):
                with self.assertRaises(LIB.HashError):
                    LIB.hash_source(target)

    def test_standard_directory_read_error_becomes_hash_error(self):
        with tempfile.TemporaryDirectory(prefix="p32-read-error-") as tmp:
            directory = pathlib.Path(tmp)
            target = directory / "archivo.txt"
            target.write_text("contenido\n", encoding="utf-8")
            real_open = builtins.open

            def simulated_open(path, *args, **kwargs):
                if os.fspath(path) == str(target):
                    raise PermissionError("fallo de lectura simulado")
                return real_open(path, *args, **kwargs)

            with mock.patch("builtins.open", side_effect=simulated_open):
                with self.assertRaises(LIB.HashError):
                    LIB.hash_source(str(directory))

    def test_directory_walk_error_becomes_hash_error(self):
        with tempfile.TemporaryDirectory(prefix="p32-walk-error-") as tmp:
            directory = pathlib.Path(tmp)
            (directory / "archivo.txt").write_text("prueba\n")

            def simulated_walk(top, *args, **kwargs):
                callback = kwargs.get("onerror")
                error = PermissionError("fallo de recorrido simulado")
                if callback is not None:
                    callback(error)
                raise error

            with mock.patch.object(
                LIB.os, "walk", side_effect=simulated_walk
            ):
                with self.assertRaises(LIB.HashError):
                    LIB.hash_source(str(directory))

    def test_git_ls_files_nonzero_becomes_hash_error(self):
        with tempfile.TemporaryDirectory(prefix="p32-git-error-") as tmp:
            result = SimpleNamespace(
                returncode=2,
                stdout=b"",
                stderr=b"fallo Git simulado",
            )
            with mock.patch.object(
                LIB.subprocess, "run", return_value=result
            ):
                with self.assertRaises(LIB.HashError):
                    LIB.hash_directory_git(tmp)

    def test_git_ls_files_execution_error_becomes_hash_error(self):
        with tempfile.TemporaryDirectory(prefix="p32-git-exec-") as tmp:
            with mock.patch.object(
                LIB.subprocess, "run",
                side_effect=OSError("ejecución Git simulada"),
            ):
                with self.assertRaises(LIB.HashError):
                    LIB.hash_directory_git(tmp)

    def test_git_permission_error_is_not_treated_as_deleted(self):
        with tempfile.TemporaryDirectory(prefix="p32-git-access-") as tmp:
            repo = pathlib.Path(tmp) / "repo"
            blocked = create_git_source(repo)
            target = str(blocked / "archivo.txt")
            real_lstat = LIB.os.lstat

            def simulated_lstat(path, *args, **kwargs):
                if os.fspath(path) == target:
                    raise PermissionError("acceso denegado simulado")
                return real_lstat(path, *args, **kwargs)

            with mock.patch.object(
                LIB.os, "lstat", side_effect=simulated_lstat
            ):
                with self.assertRaises(LIB.HashError):
                    LIB.hash_source(str(repo))

    def test_git_hashes_match_known_legacy_reference(self):
        """Preserva hashes exactos comprobados contra la implementación anterior."""
        with tempfile.TemporaryDirectory(prefix="p32-git-golden-") as tmp:
            repo = pathlib.Path(tmp) / "repo"
            repo.mkdir()
            (repo / "a.txt").write_text(
                "archivo alfa\n", encoding="utf-8"
            )
            (repo / "eliminable.txt").write_text(
                "original\n", encoding="utf-8"
            )
            os.symlink("a.txt", repo / "enlace.txt")

            run_git(repo, "init", "-q")
            run_git(repo, "add", "a.txt", "eliminable.txt", "enlace.txt")

            digest, count, kind = LIB.hash_source(str(repo))
            self.assertEqual(
                digest,
                "42ba2dfc3112e6a332909a886766288b3abc876117e680581e9b451ace6cf0a8",
            )
            self.assertEqual(count, 3)
            self.assertEqual(kind, "REPO_GIT")

            (repo / "eliminable.txt").unlink()
            digest, count, kind = LIB.hash_source(str(repo))
            self.assertEqual(
                digest,
                "99f1fef8ada6957e00d103c4384e7fc1d88e1ecb35d5ecafd9603845a7dcb264",
            )
            self.assertEqual(count, 3)
            self.assertEqual(kind, "REPO_GIT")

    def test_genuinely_deleted_git_file_keeps_deleted_semantics(self):
        with tempfile.TemporaryDirectory(prefix="p32-deleted-") as tmp:
            repo = pathlib.Path(tmp) / "repo"
            blocked = create_git_source(repo)
            (blocked / "archivo.txt").unlink()

            digest, count, kind = LIB.hash_source(str(repo))

            self.assertEqual(len(digest), 64)
            self.assertEqual(count, 1)
            self.assertEqual(kind, "REPO_GIT")


@unittest.skipIf(
    os.geteuid() == 0,
    "Las pruebas de permisos necesitan un usuario normal, no root.",
)
class ConsumerFailureTests(unittest.TestCase):
    def make_gate_case(self, required_failure):
        failed_type = "pending" if required_failure else "simulator_source"
        expected_status = "BLOCKED" if required_failure else "WARNING"
        expected_code = 2 if required_failure else 1

        with tempfile.TemporaryDirectory(prefix="p32-gate-test-") as tmp:
            root = pathlib.Path(tmp)
            (root / ".logos/bin").mkdir(parents=True)
            (root / ".logos/lib").mkdir(parents=True)

            for relative in (
                ".logos/bin/logos-gate",
                ".logos/bin/validate-manifest",
                ".logos/lib/logos_hash_lib.py",
            ):
                shutil.copy2(ROOT / relative, root / relative)

            (root / ".logos/bin/logos-gate").chmod(0o755)
            (root / ".logos/bin/validate-manifest").chmod(0o755)

            sources_dir = root / "sources"
            sources_dir.mkdir()
            (sources_dir / "state.json").write_text(
                '{"project":{"id":"NAVEGO"}}', encoding="utf-8"
            )
            (sources_dir / "profile.json").write_text(
                '{"id":"NAVEGO"}', encoding="utf-8"
            )
            (sources_dir / "protocol.txt").write_text("protocolo\n")
            (sources_dir / "decisions.txt").write_text("decisiones\n")
            (sources_dir / "pending.txt").write_text("pendientes\n")
            (sources_dir / "simulator.txt").write_text("simulador\n")

            repo_pending = sources_dir / "repo_pending"
            repo_simulator = sources_dir / "repo_simulator"
            blocked_pending = create_git_source(repo_pending)
            blocked_simulator = create_git_source(repo_simulator)

            paths = {
                "state": "sources/state.json",
                "profile": "sources/profile.json",
                "protocol": "sources/protocol.txt",
                "decisions": "sources/decisions.txt",
                "pending": (
                    "sources/repo_pending" if required_failure
                    else "sources/pending.txt"
                ),
                "simulator_source": (
                    "sources/simulator.txt" if required_failure
                    else "sources/repo_simulator"
                ),
            }

            sources = []
            for source_type, relative_path in paths.items():
                entry = {
                    "type": source_type,
                    "path": relative_path,
                    "authority": True,
                    "role": "singleton",
                    "validation_policy": "hash",
                }
                if source_type == failed_type:
                    entry["reviewed_against_hash"] = "f" * 64
                else:
                    digest, _, _ = LIB.hash_source(str(root / relative_path))
                    entry["reviewed_against_hash"] = digest
                sources.append(entry)

            manifest = {
                "schema_version": "1",
                "manifest_version": "1",
                "project": "NAVEGO",
                "fail_closed": True,
                "required": [
                    "state", "profile", "protocol", "decisions", "pending"
                ],
                "optional": ["simulator_source"],
                "sources": sources,
            }
            (root / ".logos/MANIFEST.json").write_text(
                json.dumps(manifest, indent=2), encoding="utf-8"
            )

            blocked = blocked_pending if required_failure else blocked_simulator
            os.chmod(blocked, 0)
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        str(root / ".logos/bin/logos-gate"),
                        "NAVEGO",
                        "--json",
                    ],
                    cwd=root,
                    capture_output=True,
                    text=True,
                )
            finally:
                os.chmod(blocked, 0o700)

            self.assertEqual(
                process.returncode, expected_code,
                msg=process.stdout + "\n" + process.stderr,
            )
            result = json.loads(process.stdout)
            self.assertEqual(result["status"], expected_status)

            drift = result.get("checks", {}).get("drift", "")
            self.assertIn(f"{failed_type}(INVALID:hash_error:", drift)
            self.assertNotIn(f"{failed_type}(CURRENT:", drift)

            if required_failure:
                self.assertTrue(any(
                    item.startswith("drift_required:pending(INVALID:")
                    for item in result["reasons"]
                ))
            else:
                self.assertTrue(any(
                    item.startswith("drift_optional:simulator_source(INVALID:")
                    for item in result["warnings"]
                ))

    def test_gate_blocks_invalid_required_source(self):
        self.make_gate_case(required_failure=True)

    def test_gate_warns_on_invalid_optional_source(self):
        self.make_gate_case(required_failure=False)

    def test_baseline_does_not_write_manifest_on_hash_error(self):
        with tempfile.TemporaryDirectory(prefix="p32-baseline-test-") as tmp:
            root = pathlib.Path(tmp)
            (root / ".logos/bin").mkdir(parents=True)
            (root / ".logos/lib").mkdir(parents=True)
            shutil.copy2(ROOT / ".logos/bin/logos-baseline",
                         root / ".logos/bin/logos-baseline")
            shutil.copy2(LIB_PATH, root / ".logos/lib/logos_hash_lib.py")

            source_repo = root / "sources/repo_pending"
            blocked = create_git_source(source_repo)

            manifest = {
                "schema_version": "1",
                "manifest_version": "1",
                "project": "NAVEGO",
                "fail_closed": True,
                "required": ["pending"],
                "optional": [],
                "sources": [{
                    "type": "pending",
                    "path": "sources/repo_pending",
                    "authority": True,
                    "role": "singleton",
                    "validation_policy": "hash",
                    "reviewed_against_hash": "f" * 64,
                }],
            }
            manifest_path = root / ".logos/MANIFEST.json"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

            run_git(root, "init", "-q")
            run_git(root, "config", "user.name", "P32 Test")
            run_git(root, "config", "user.email", "p32@example.invalid")
            run_git(
                root, "add", ".logos/MANIFEST.json",
                ".logos/bin/logos-baseline",
                ".logos/lib/logos_hash_lib.py",
            )
            run_git(root, "commit", "-q", "-m", "Fixture baseline P32")

            before = manifest_path.read_bytes()
            os.chmod(blocked, 0)
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        str(root / ".logos/bin/logos-baseline"),
                        "NAVEGO",
                        "--reason=prueba de regresión P32",
                    ],
                    cwd=root,
                    capture_output=True,
                    text=True,
                )
            finally:
                os.chmod(blocked, 0o700)

            self.assertEqual(process.returncode, 2, process.stdout + process.stderr)
            self.assertIn("BLOCKED", process.stdout)
            self.assertEqual(manifest_path.read_bytes(), before)
            status = run_git(
                root, "status", "--short", "--", ".logos/MANIFEST.json"
            ).stdout.strip()
            self.assertEqual(status, "")

    def test_reconcile_does_not_write_manifest_on_hash_error(self):
        with tempfile.TemporaryDirectory(prefix="p32-reconcile-test-") as tmp:
            root = pathlib.Path(tmp)
            (root / ".logos/bin").mkdir(parents=True)
            (root / ".logos/lib").mkdir(parents=True)
            shutil.copy2(ROOT / ".logos/bin/logos-reconcile",
                         root / ".logos/bin/logos-reconcile")
            shutil.copy2(LIB_PATH, root / ".logos/lib/logos_hash_lib.py")

            blocked = root / "directorio_bloqueado"
            blocked.mkdir()
            (blocked / "archivo.txt").write_text("prueba\n")

            manifest = {
                "schema_version": "1",
                "manifest_version": "1",
                "project": "P32TEST",
                "fail_closed": True,
                "required": ["pending"],
                "optional": [],
                "sources": [{
                    "type": "pending",
                    "path": ".",
                    "authority": True,
                    "role": "singleton",
                    "validation_policy": "hash",
                    "reviewed_against_commit": "",
                    "reviewed_against_hash": "f" * 64,
                }],
            }
            manifest_path = root / ".logos/MANIFEST.json"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

            run_git(root, "init", "-q")
            run_git(root, "config", "user.name", "P32 Test")
            run_git(root, "config", "user.email", "p32@example.invalid")
            run_git(root, "add", "-A")
            run_git(root, "commit", "-q", "-m", "Fixture reconcile P32")

            home = root / "home-aislado"
            home.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(home)

            before = manifest_path.read_bytes()
            os.chmod(blocked, 0)
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        str(root / ".logos/bin/logos-reconcile"),
                        "mark-reviewed", "pending",
                    ],
                    cwd=root,
                    env=env,
                    capture_output=True,
                    text=True,
                )
            finally:
                os.chmod(blocked, 0o700)

            self.assertEqual(process.returncode, 2, process.stdout + process.stderr)
            self.assertIn("BLOCKED", process.stdout)
            self.assertEqual(manifest_path.read_bytes(), before)
            status = run_git(
                root, "status", "--short", "--", ".logos/MANIFEST.json"
            ).stdout.strip()
            self.assertEqual(status, "")


class AtomicWriteTests(unittest.TestCase):
    def test_reconcile_atomic_write_preserves_old_file_on_replace_error(self):
        with tempfile.TemporaryDirectory(prefix="p32-atomic-test-") as tmp:
            root = pathlib.Path(tmp)
            (root / ".logos/bin").mkdir(parents=True)
            (root / ".logos/lib").mkdir(parents=True)
            script = root / ".logos/bin/logos-reconcile"
            shutil.copy2(ROOT / ".logos/bin/logos-reconcile", script)
            shutil.copy2(LIB_PATH, root / ".logos/lib/logos_hash_lib.py")

            name = "p32_reconcile_atomic_under_test"
            old_path = list(sys.path)
            try:
                loader = SourceFileLoader(name, str(script))
                spec = importlib.util.spec_from_loader(name, loader)
                self.assertIsNotNone(spec)
                module = importlib.util.module_from_spec(spec)
                loader.exec_module(module)
            finally:
                sys.path[:] = old_path

            manifest = root / "MANIFEST.json"
            original = b'{\n  "estado": "anterior"\n}\n'
            manifest.write_bytes(original)

            with mock.patch.object(
                module.os, "replace",
                side_effect=OSError("fallo de reemplazo simulado"),
            ):
                with self.assertRaisesRegex(OSError, "fallo de reemplazo"):
                    module.write_manifest_atomic(
                        manifest, {"estado": "nuevo"}
                    )

            self.assertEqual(manifest.read_bytes(), original)
            self.assertEqual(list(root.glob(".MANIFEST.*.tmp")), [])

            module.write_manifest_atomic(manifest, {"estado": "nuevo"})
            self.assertEqual(
                json.loads(manifest.read_text(encoding="utf-8")),
                {"estado": "nuevo"},
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
