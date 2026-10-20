#!/usr/bin/env python3
"""Regression tests for LOGOS v1 root-of-trust verification."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
LIB = REPO / ".logos" / "lib" / "logos_trust_lib.py"
spec = importlib.util.spec_from_file_location("logos_trust_lib_tested", LIB)
trust_lib = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(trust_lib)
verify_manifest_trust = trust_lib.verify_manifest_trust


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if p.returncode:
        raise AssertionError(p.stderr or p.stdout)
    return p.stdout.strip()


class TrustRootTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.repo = self.base / "repo"
        (self.repo / ".logos").mkdir(parents=True)
        self.manifest = self.repo / ".logos" / "MANIFEST.json"
        self.manifest.write_text('{"project": "NAVEGO"}\n', encoding="utf-8")
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "logos-test@example.invalid")
        git(self.repo, "config", "user.name", "LOGOS test")
        git(self.repo, "add", ".logos/MANIFEST.json")
        git(self.repo, "commit", "-qm", "test manifest")
        self.head = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        self.temp.cleanup()

    def root_file(self) -> Path:
        return self.home / ".logos" / "trust" / "NAVEGO.json"

    def write_root(self, **overrides):
        p = self.root_file()
        p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(p.parent, 0o700)
        data = {
            "schema_version": "1.0",
            "project": "NAVEGO",
            "approved_manifest_commit": self.head,
            "approved_manifest_sha256": hashlib.sha256(self.manifest.read_bytes()).hexdigest(),
        }
        data.update(overrides)
        p.write_text(json.dumps(data), encoding="utf-8")
        os.chmod(p, 0o600)
        return p

    def check(self):
        return verify_manifest_trust("NAVEGO", self.manifest, self.repo, home=self.home)

    def test_missing_root_is_blocked(self):
        state, detail = self.check()
        self.assertEqual(state, "BLOCKED")
        self.assertIn("AUSENTE", detail)

    def test_valid_root_is_verified(self):
        self.write_root()
        state, detail = self.check()
        self.assertEqual(state, "VERIFIED", detail)
        self.assertIn(self.head, detail)

    def test_changed_manifest_hash_is_blocked(self):
        self.write_root()
        self.manifest.write_text('{"project": "NAVEGO", "changed": true}\n', encoding="utf-8")
        state, detail = self.check()
        self.assertEqual(state, "BLOCKED")
        self.assertIn("no coincide", detail)

    def test_invalid_json_is_blocked(self):
        p = self.root_file()
        p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        p.write_text("{bad", encoding="utf-8")
        os.chmod(p, 0o600)
        state, detail = self.check()
        self.assertEqual(state, "BLOCKED")
        self.assertIn("JSON inválido", detail)

    def test_missing_hash_is_blocked(self):
        self.write_root(approved_manifest_sha256="")
        state, detail = self.check()
        self.assertEqual(state, "BLOCKED")
        self.assertIn("approved_manifest_sha256", detail)

    def test_nonexistent_commit_is_blocked(self):
        self.write_root(approved_manifest_commit="f" * 40)
        state, detail = self.check()
        self.assertEqual(state, "BLOCKED")
        self.assertIn("no existe como commit", detail)

    def test_unrelated_project_commit_is_blocked(self):
        other = self.base / "other"
        other.mkdir()
        git(other, "init", "-q")
        git(other, "config", "user.email", "logos-test@example.invalid")
        git(other, "config", "user.name", "LOGOS test")
        (other / "x.txt").write_text("x\n", encoding="utf-8")
        git(other, "add", "x.txt")
        git(other, "commit", "-qm", "unrelated")
        other_commit = git(other, "rev-parse", "HEAD")
        self.write_root(approved_manifest_commit=other_commit)
        state, detail = self.check()
        self.assertEqual(state, "BLOCKED")
        self.assertIn("no existe como commit", detail)

    def test_approved_commit_must_contain_approved_manifest_hash(self):
        original_manifest = self.manifest.read_bytes()
        self.manifest.write_text('{"project": "NAVEGO", "different_in_commit": true}\n', encoding="utf-8")
        git(self.repo, "add", ".logos/MANIFEST.json")
        git(self.repo, "commit", "-qm", "manifest different from approved hash")
        self.head = git(self.repo, "rev-parse", "HEAD")
        # Restore the previously approved bytes in the working tree. The current
        # hash is correct, but the named commit contains a different MANIFEST.
        self.manifest.write_bytes(original_manifest)
        self.write_root(approved_manifest_commit=self.head)
        state, detail = self.check()
        self.assertEqual(state, "BLOCKED")
        self.assertIn("no contiene el MANIFEST", detail)

    def test_project_mismatch_is_blocked(self):
        self.write_root(project="OTRO")
        state, detail = self.check()
        self.assertEqual(state, "BLOCKED")
        self.assertIn("proyecto", detail)

    def test_symlink_root_is_blocked(self):
        p = self.root_file()
        p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        other = self.base / "elsewhere.json"
        other.write_text("{}", encoding="utf-8")
        p.symlink_to(other)
        state, detail = self.check()
        self.assertEqual(state, "BLOCKED")
        self.assertIn("enlace simbólico", detail)

    def test_gate_wires_trust_check_before_final_status(self):
        gate = (REPO / ".logos" / "bin" / "logos-gate").read_text(encoding="utf-8")
        marker = "# 4. Status final"
        self.assertIn("verify_manifest_trust", gate)
        self.assertIn('checks[\'trust\'] = \'BLOCKED\'', gate)
        self.assertLess(gate.index("verify_manifest_trust(PROYECTO"), gate.index(marker))

    def test_reconcile_fails_closed_when_trust_is_missing(self):
        reconcile = (REPO / ".logos" / "bin" / "logos-reconcile").read_text(encoding="utf-8")
        self.assertIn("state, detail = verify_manifest_trust", reconcile)
        self.assertIn('if state != "VERIFIED":', reconcile)
        self.assertNotIn('return "ABSENT", EXIT_WARNING', reconcile)


if __name__ == "__main__":
    unittest.main(verbosity=2)
