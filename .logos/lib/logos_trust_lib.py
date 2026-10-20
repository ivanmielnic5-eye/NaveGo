#!/usr/bin/env python3
"""LOGOS v1 external root-of-trust verification.

The v1 reference lives outside the repository at ~/.logos/trust/PROJECT.json.
It pins the SHA-256 of .logos/MANIFEST.json and the Git commit at which that
manifest was explicitly approved. This is not a cryptographic signature; v1
also relies on filesystem separation/permissions and explicit human approval.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Optional, Tuple

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def trust_path(project: str, home: Optional[Path] = None) -> Path:
    base = Path(home).expanduser() if home is not None else Path.home()
    return base / ".logos" / "trust" / f"{project}.json"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def verify_manifest_trust(
    project: str,
    manifest: Path,
    repo: Path,
    home: Optional[Path] = None,
) -> Tuple[str, str]:
    """Return (VERIFIED|BLOCKED, detail); never treats absence as a warning."""
    try:
        manifest = Path(manifest).resolve(strict=True)
        repo = Path(repo).resolve(strict=True)
        trust = trust_path(project, home=home)

        trust_dir = trust.parent
        if trust_dir.is_symlink():
            return "BLOCKED", "directorio de confianza es un enlace simbólico"
        if not trust.is_file():
            return "BLOCKED", f"raíz de confianza AUSENTE: {trust}"
        if trust.is_symlink():
            return "BLOCKED", "archivo de confianza es un enlace simbólico"

        st = trust.stat()
        if hasattr(os, "getuid") and st.st_uid != os.getuid():
            return "BLOCKED", "la raíz de confianza no pertenece al usuario actual"
        if stat.S_IMODE(st.st_mode) & 0o022:
            return "BLOCKED", "la raíz de confianza permite escritura a grupo u otros"
        if trust_dir.exists():
            dst = trust_dir.stat()
            if hasattr(os, "getuid") and dst.st_uid != os.getuid():
                return "BLOCKED", "el directorio de confianza no pertenece al usuario actual"
            if stat.S_IMODE(dst.st_mode) & 0o022:
                return "BLOCKED", "el directorio de confianza permite escritura a grupo u otros"

        try:
            data = json.loads(trust.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return "BLOCKED", f"raíz de confianza ilegible o JSON inválido: {exc}"
        if not isinstance(data, dict):
            return "BLOCKED", "la raíz de confianza no es un objeto JSON"
        if data.get("project", project) != project:
            return "BLOCKED", "el proyecto de la raíz de confianza no coincide"

        approved_hash = data.get("approved_manifest_sha256")
        approved_commit = data.get("approved_manifest_commit")
        if not isinstance(approved_hash, str) or not _SHA256.fullmatch(approved_hash):
            return "BLOCKED", "approved_manifest_sha256 ausente o inválido"
        if not isinstance(approved_commit, str) or not _GIT_OID.fullmatch(approved_commit):
            return "BLOCKED", "approved_manifest_commit ausente o inválido; se exige OID completo"

        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        if digest != approved_hash:
            return "BLOCKED", (
                "el MANIFEST actual no coincide con approved_manifest_sha256; "
                f"aprobado={approved_hash}, actual={digest}"
            )

        head = _git(repo, "rev-parse", "HEAD")
        if head.returncode != 0 or not head.stdout.strip():
            return "BLOCKED", "no se pudo determinar HEAD del repositorio"
        obj = _git(repo, "cat-file", "-e", f"{approved_commit}^{{commit}}")
        if obj.returncode != 0:
            return "BLOCKED", "approved_manifest_commit no existe como commit en este repositorio"
        ancestry = _git(repo, "merge-base", "--is-ancestor", approved_commit, head.stdout.strip())
        if ancestry.returncode != 0:
            return "BLOCKED", "approved_manifest_commit no es ancestro de HEAD"

        # The approved commit must contain the exact MANIFEST whose digest is pinned.
        # This binds both reference fields to one approved version, not just to an
        # arbitrary ancestor commit plus the current working-tree hash.
        approved_blob = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "blob", f"{approved_commit}:.logos/MANIFEST.json"],
            capture_output=True,
            check=False,
        )
        if approved_blob.returncode != 0:
            return "BLOCKED", "approved_manifest_commit no contiene .logos/MANIFEST.json"
        committed_digest = hashlib.sha256(approved_blob.stdout).hexdigest()
        if committed_digest != approved_hash:
            return "BLOCKED", (
                "approved_manifest_commit no contiene el MANIFEST cuyo SHA-256 fue aprobado; "
                f"commit={committed_digest}, raíz={approved_hash}"
            )

        return "VERIFIED", f"raíz de confianza: OK (approved_manifest_commit={approved_commit})"
    except Exception as exc:
        return "BLOCKED", f"error verificando raíz de confianza: {type(exc).__name__}: {exc}"
