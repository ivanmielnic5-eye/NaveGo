#!/usr/bin/env python3
"""Pruebas de las salvaguardas adicionales de P48."""

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative_path):
    path = ROOT / relative_path
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError(f"No se pudo cargar {path}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


INGESTA = load_script("logos_ingesta_p48_test", ".logos/bin/logos-ingesta")
ARRANQUE = load_script("logos_arranque_p48_test", ".logos/bin/logos-arranque")


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )


class P48SafeguardTests(unittest.TestCase):
    def test_ingesta_commits_only_requested_file(self):
        with tempfile.TemporaryDirectory(prefix="logos-p48-ingesta-") as tmp:
            repo = Path(tmp)
            target = repo / "objetivo.txt"
            unrelated = repo / "ajeno.txt"

            git(repo, "init", "-q")
            git(repo, "config", "user.name", "LOGOS P48 test")
            git(repo, "config", "user.email", "logos-p48@localhost")
            git(repo, "config", "commit.gpgsign", "false")

            target.write_text("base\n", encoding="utf-8")
            unrelated.write_text("base\n", encoding="utf-8")
            git(repo, "add", "objetivo.txt", "ajeno.txt")
            git(repo, "commit", "-qm", "base")

            target.write_text("objetivo modificado\n", encoding="utf-8")
            unrelated.write_text("cambio ajeno\n", encoding="utf-8")
            git(repo, "add", "ajeno.txt")

            with mock.patch.object(
                INGESTA, "_repo_root", return_value=str(repo)
            ):
                result = INGESTA.cmd_commit(str(target), "solo objetivo")

            self.assertEqual(result, 0)

            committed = git(
                repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"
            ).stdout.splitlines()
            self.assertEqual(committed, ["objetivo.txt"])

            staged = git(repo, "diff", "--cached", "--name-only").stdout.splitlines()
            self.assertEqual(staged, ["ajeno.txt"])

    def test_arranque_stops_when_brief_fails(self):
        with tempfile.TemporaryDirectory(prefix="logos-p48-arranque-") as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            output = base / "contexto.txt"
            gate = base / "gate-falso"
            brief = base / "brief-falso"
            brief_md = repo / "BRIEF_NAVEGO.md"
            calls = []

            def fake_run(command, **kwargs):
                calls.append(command)
                if command[0] == str(gate):
                    return SimpleNamespace(
                        returncode=0,
                        stdout=json.dumps({
                            "status": "READY",
                            "checks": {},
                            "reasons": [],
                            "warnings": [],
                        }),
                        stderr="",
                    )
                if command[0] == str(brief):
                    return SimpleNamespace(
                        returncode=17,
                        stdout="",
                        stderr="fallo simulado de logos-brief",
                    )
                raise AssertionError(f"Comando inesperado: {command!r}")

            with (
                mock.patch.object(ARRANQUE, "REPO", repo),
                mock.patch.object(ARRANQUE, "GATE", gate),
                mock.patch.object(ARRANQUE, "BRIEF", brief),
                mock.patch.object(ARRANQUE, "BRIEF_MD", brief_md),
                mock.patch.object(
                    ARRANQUE.sys, "argv",
                    ["logos-arranque", "--out", str(output)],
                ),
                mock.patch.object(ARRANQUE.os, "chdir"),
                mock.patch.object(
                    ARRANQUE.subprocess, "run", side_effect=fake_run
                ),
            ):
                result = ARRANQUE.main()

            self.assertEqual(result, 2)
            self.assertFalse(output.exists())
            self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
