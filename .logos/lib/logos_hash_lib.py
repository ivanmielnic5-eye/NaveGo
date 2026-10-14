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
    for root, dirs, files in os.walk(dirpath):
        dirs[:] = [d for d in dirs if d != '.git']
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
    r = subprocess.run(
        ['git', '-C', repo_path, 'ls-files', '-z'],
        capture_output=True
    )
    if r.returncode != 0:
        return None, 0
    files = [f for f in r.stdout.split(b'\x00') if f]
    files.sort()
    h = hashlib.sha256()
    contados = 0
    for fbytes in files:
        rel = fbytes.decode('utf-8', errors='replace')
        full = os.path.join(repo_path, rel)
        if os.path.islink(full):
            target = os.readlink(full)
            h.update(rel.encode('utf-8'))
            h.update(b'\x00')
            h.update(b'LINK:' + target.encode('utf-8'))
            h.update(b'\x00')
            contados += 1
            continue
        if not os.path.exists(full):
            h.update(rel.encode('utf-8'))
            h.update(b'\x00')
            h.update(b'DELETED\x00')
            contados += 1
            continue
        # Fix P31: propaga error de lectura.
        with open(full, 'rb') as fh:
            content = fh.read()
        h.update(rel.encode('utf-8'))
        h.update(b'\x00')
        h.update(str(len(content)).encode('utf-8'))
        h.update(b'\x00')
        h.update(content)
        contados += 1
    return h, contados


def hash_source(path):
    """Devuelve (hash_hex, cantidad_archivos, tipo).

    Propaga HashError si el path existe pero no se puede hashear
    (fix P31). Devuelve (None, 0, tipo) si no existe o si es de
    tipo desconocido.
    """
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return None, 0, 'NO_EXISTE'
    if os.path.isfile(path):
        try:
            h = hash_file(path)
        except (OSError, PermissionError) as e:
            raise HashError(f"no se puede leer {path}: {e}") from e
        return h.hexdigest(), 1, 'ARCHIVO'
    if os.path.isdir(path):
        if os.path.isdir(os.path.join(path, '.git')):
            h, n = hash_directory_git(path)
            if h is None:
                return None, 0, 'GIT_ERROR'
            return h.hexdigest(), n, 'REPO_GIT'
        try:
            h, n = hash_directory_standard(path)
        except (OSError, PermissionError) as e:
            raise HashError(f"error hasheando directorio {path}: {e}") from e
        return h.hexdigest(), n, 'DIRECTORIO'
    return None, 0, 'TIPO_DESCONOCIDO'
