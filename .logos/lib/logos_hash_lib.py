#!/usr/bin/env python3
"""logos_hash_lib - Biblioteca compartida de hashing para LOGOS.

Extraido de logos-hash (D-2026-0010). Consumido por:
  - logos-hash
  - logos-baseline
  - logos-reconcile

Convencion (D-2026-0010):
  ARCHIVO:    SHA256(contenido)
  DIRECTORIO: SHA256 concatenado de [path_rel + NUL + len + NUL + contenido]
              ordenado por path_rel, comparacion ordinal
  REPO GIT:   (si existe .git/ en el path) git ls-files + contenido working tree
  .git/       siempre excluido
  SYMLINKS:   no se siguen, se hashea el destino como metadata

Fix P31 (2026-10-14): los errores de lectura PROPAGAN en vez de
saltearse silenciosamente. Un hash silenciosamente incompleto es
peor que un fallo visible.
"""
import hashlib
import os
import stat
import subprocess


class HashError(Exception):
    """Error de hashing que debe ser tratado por el consumidor."""
    pass


def hash_file(path):
    """SHA256 de un archivo. Propaga errores de lectura (fix P31)."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h


def hash_directory_standard(dirpath):
    """Recorrido normal de un directorio (no git)."""
    dirpath = os.path.abspath(dirpath)
    entries = []

    def raise_walk_error(error):
        raise error

    for root, dirs, files in os.walk(
        dirpath, onerror=raise_walk_error
    ):
        # P30: registrar enlaces simbolicos a directorios
        # sin recorrer sus destinos.
        kept_dirs = []
        for dirname in dirs:
            full_dir = os.path.join(root, dirname)
            if dirname == '.git':
                continue
            if os.path.islink(full_dir):
                rel = os.path.relpath(full_dir, dirpath)
                entries.append((rel, full_dir))
                continue
            kept_dirs.append(dirname)
        dirs[:] = kept_dirs

        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, dirpath)
            entries.append((rel, full))
    entries.sort(key=lambda e: e[0].encode('utf-8'))
    h = hashlib.sha256()
    for rel, full in entries:
        if os.path.islink(full):
            target = os.readlink(full)
            h.update(rel.encode('utf-8'))
            h.update(b'\x00')
            h.update(b'LINK:' + target.encode('utf-8'))
            h.update(b'\x00')
            continue
        # Fix P31: sin try/except, propaga.
        with open(full, 'rb') as f:
            content = f.read()
        h.update(rel.encode('utf-8'))
        h.update(b'\x00')
        h.update(str(len(content)).encode('utf-8'))
        h.update(b'\x00')
        h.update(content)
    return h, len(entries)


def hash_directory_git(repo_path):
    """Repo git: git ls-files + contenido working tree."""
    repo_path = os.path.abspath(repo_path)
    try:
        r = subprocess.run(
            ['git', '-C', repo_path, 'ls-files', '-z'],
            capture_output=True
        )
    except OSError as e:
        raise HashError(
            f"no se pudo ejecutar git ls-files en {repo_path}: {e}"
        ) from e

    if r.returncode != 0:
        detail = (r.stderr or b"").decode(
            "utf-8", errors="replace"
        ).strip()
        raise HashError(
            f"git ls-files fallo en {repo_path}: "
            f"{detail or 'codigo ' + str(r.returncode)}"
        )
    files = [f for f in r.stdout.split(b'\x00') if f]
    files.sort()
    h = hashlib.sha256()
    contados = 0
    for fbytes in files:
        rel = fbytes.decode('utf-8', errors='replace')
        full = os.path.join(repo_path, rel)

        # Distinguir una ausencia real de un error de acceso.
        # exists() puede devolver False si un directorio padre
        # no permite acceder a la ruta.
        try:
            info = os.lstat(full)
        except FileNotFoundError:
            # Archivo rastreado realmente ausente.
            h.update(rel.encode('utf-8'))
            h.update(b'\x00')
            h.update(b'DELETED\x00')
            contados += 1
            continue
        except OSError as e:
            raise HashError(
                f"no se pudo inspeccionar archivo rastreado "
                f"{rel!r} en {repo_path}: {e}"
            ) from e

        # No seguir symlinks: conservar el hash de su destino
        # como metadata, según la semántica existente.
        if stat.S_ISLNK(info.st_mode):
            try:
                target = os.readlink(full)
            except OSError as e:
                raise HashError(
                    f"no se pudo leer symlink rastreado "
                    f"{rel!r} en {repo_path}: {e}"
                ) from e
            h.update(rel.encode('utf-8'))
            h.update(b'\x00')
            h.update(b'LINK:' + target.encode('utf-8'))
            h.update(b'\x00')
            contados += 1
            continue

        # Un error de lectura debe fallar explícitamente;
        # nunca producir un hash parcial.
        try:
            with open(full, 'rb') as fh:
                content = fh.read()
        except OSError as e:
            raise HashError(
                f"no se pudo leer archivo rastreado "
                f"{rel!r} en {repo_path}: {e}"
            ) from e
        h.update(rel.encode('utf-8'))
        h.update(b'\x00')
        h.update(str(len(content)).encode('utf-8'))
        h.update(b'\x00')
        h.update(content)
        contados += 1
    return h, contados


def hash_source(path):
    """Devuelve (hash_hex, cantidad_archivos, tipo).

    Una ruta realmente inexistente devuelve (None, 0, 'NO_EXISTE').
    Si no se puede inspeccionar o hashear una fuente existente,
    propaga HashError para evitar aceptar hashes incompletos.
    """
    path = os.path.expanduser(path)

    # No usar os.path.exists() como única comprobación: puede ocultar
    # errores de permisos y confundirlos con una ausencia real.
    try:
        path_info = os.stat(path)
    except FileNotFoundError:
        return None, 0, 'NO_EXISTE'
    except OSError as e:
        raise HashError(
            f"no se pudo inspeccionar fuente {path}: {e}"
        ) from e

    # os.stat sigue symlinks, como las comprobaciones anteriores
    # os.path.isfile/isdir. No se cambia aquí el alcance de P30.
    if stat.S_ISREG(path_info.st_mode):
        try:
            h = hash_file(path)
        except OSError as e:
            raise HashError(f"no se puede leer {path}: {e}") from e
        return h.hexdigest(), 1, 'ARCHIVO'

    if stat.S_ISDIR(path_info.st_mode):
        git_path = os.path.join(path, '.git')

        # Mantener la detección histórica de repositorios con .git
        # como directorio; propagar errores de inspección reales.
        try:
            git_info = os.stat(git_path)
        except FileNotFoundError:
            is_git_repo = False
        except OSError as e:
            raise HashError(
                f"no se pudo inspeccionar metadata Git en {path}: {e}"
            ) from e
        else:
            is_git_repo = stat.S_ISDIR(git_info.st_mode)

        if is_git_repo:
            try:
                h, n = hash_directory_git(path)
            except HashError:
                raise
            except OSError as e:
                raise HashError(
                    f"error hasheando repo Git {path}: {e}"
                ) from e
            return h.hexdigest(), n, 'REPO_GIT'

        try:
            h, n = hash_directory_standard(path)
        except OSError as e:
            raise HashError(
                f"error hasheando directorio {path}: {e}"
            ) from e
        return h.hexdigest(), n, 'DIRECTORIO'

    return None, 0, 'TIPO_DESCONOCIDO'
