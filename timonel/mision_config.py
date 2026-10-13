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


# ============================================================
# VALIDADOR (sin jsonschema, propio de F0)
# ============================================================

from types import MappingProxyType


def _validar(config, schema):
    """Valida config contra schema. Devuelve lista de errores."""
    errores = []

    # 1. Claves top-level obligatorias
    for k in schema["required_top"]:
        if k not in config:
            errores.append("falta clave obligatoria: " + k)

    # 2. Claves desconocidas top-level
    validas = set(schema["required_top"]) | {"mission_instance_hash"}
    for k in config:
        if k not in validas:
            errores.append("clave desconocida: " + k)

    # 3. Campos con valor: tipo y unidad
    for path, spec in schema["campos_valor"].items():
        partes = path.split(".")
        actual = config
        for p in partes:
            if not isinstance(actual, dict) or p not in actual:
                actual = None
                break
            actual = actual[p]
        if actual is None:
            continue
        # actual es un dict con valor/unidad/etc, o un valor suelto
        if isinstance(actual, dict):
            v = actual.get("valor")
        else:
            v = actual
        if v is not None and not isinstance(v, (int, float)):
            errores.append(path + ": valor no numerico: " + str(v))
        if isinstance(actual, dict):
            prov = actual.get("procedencia")
            est = actual.get("estado")
            if prov is not None and prov not in schema["procedencias_validas"]:
                errores.append(path + ": procedencia invalida: " + str(prov))
            if est is not None and est not in schema["estados_validos"]:
                errores.append(path + ": estado invalido: " + str(est))

    return errores


def _congelar(obj):
    """Devuelve un objeto inmutable equivalente."""
    if isinstance(obj, dict):
        return MappingProxyType({k: _congelar(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return tuple(_congelar(v) for v in obj)
    return obj


def cargar_mision(path):
    """Carga, valida y congela una instancia de mision.

    - Falla si el JSON es invalido.
    - Falla si hay errores de validacion.
    - Inicializa garantia_dinamica si falta.
    - Adjunta mission_instance_hash.
    - Devuelve objeto inmutable.
    """
    import os
    if not os.path.exists(path):
        raise FileNotFoundError("No existe: " + path)

    with open(path, encoding="utf-8") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError("JSON invalido: " + str(e))

    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "mision_schema.json")
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    errores = _validar(config, schema)
    if errores:
        raise ValueError("Errores de validacion:\n  " + "\n  ".join(errores))

    if "outcomes" in config:
        if "garantia_dinamica" not in config["outcomes"]:
            config["outcomes"]["garantia_dinamica"] = schema["garantia_dinamica_default"]

    config["mission_instance_hash"] = hash_canonico(config)
    return _congelar(config)
