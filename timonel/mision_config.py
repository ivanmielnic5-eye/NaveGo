#!/usr/bin/env python3
"""mision_config.py - Configuracion de mision (F0).

Hash canonico con floats normalizados. Bloqueante 2 de F0.

Reglas:
- Claves ordenadas alfabeticamente.
- Numeros normalizados: 15 y 15.0 dan el mismo string.
- Sin espacios en el JSON serializado.
- SHA-256 sobre el string canonico.

Referencia: borradores/f0_diseno_v2.md, bloqueante 2.
"""
import hashlib
import json


def _normalizar_numero(x):
    """Convierte un numero a una representacion canonica.

    Reglas:
    - bool se deja como bool (True/False, no 1/0).
    - int se convierte a float para consistencia.
    - Si el float es entero, se quita el .0.
    - Si tiene decimales, se usa repr.
    """
    if isinstance(x, bool):
        return x
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        if x != x:  # NaN
            return "nan"
        if x == float("inf"):
            return "inf"
        if x == float("-inf"):
            return "-inf"
        # Entero: quitar .0
        if x.is_integer():
            return str(int(x))
        # Con decimales: repr (es determinista en Python 3)
        return repr(x)
    return x


def _normalizar(obj):
    """Recorre recursivamente y normaliza numeros."""
    if isinstance(obj, dict):
        return {k: _normalizar(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalizar(v) for v in obj]
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return _normalizar_numero(obj)
    return obj


def hash_canonico(obj):
    """SHA-256 canonico de un objeto.

    Dos objetos con mismos datos pero distinto formato de numero
    (15 vs 15.0) dan el mismo hash.
    Dos objetos con mismas claves en distinto orden dan el mismo hash.
    """
    obj_norm = _normalizar(obj)
    texto = json.dumps(obj_norm, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def hash_canonico_corto(obj, chars=16):
    """Version corta del hash, para IDs legibles."""
    return hash_canonico(obj)[:chars]
