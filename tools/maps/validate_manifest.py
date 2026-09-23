#!/usr/bin/env python3
import json, sys, os, hashlib
from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = "manifest.schema.json"
MANIFEST_PATH = sys.argv[1] if len(sys.argv) > 1 else "manifest.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

schema = load_json(SCHEMA_PATH)
manifest = load_json(MANIFEST_PATH)

validator = Draft202012Validator(schema, format_checker=FormatChecker())
errors = sorted(validator.iter_errors(manifest), key=lambda e: e.path)

if errors:
    print("Manifest INVALIDO:")
    for err in errors:
        print(f"  - {err.json_path}: {err.message}")
    sys.exit(1)

warnings = []

t = manifest["tiles"]
if t["minzoom"] > t["maxzoom"]:
    print(f"minzoom ({t['minzoom']}) > maxzoom ({t['maxzoom']})")
    sys.exit(1)

bbox = manifest["coverage"]["bbox_wgs84"]
if not (bbox[0] < bbox[2] and bbox[1] < bbox[3]):
    print(f"bbox_wgs84 invalido: {bbox}")
    sys.exit(1)

mbtiles_path = t["file"]
if not os.path.exists(mbtiles_path):
    warnings.append(f"Archivo de tiles no encontrado: {mbtiles_path} (esperado si aun no se genero)")
else:
    real_size = os.path.getsize(mbtiles_path)
    meta_size = manifest["metadata"]["size_bytes"]
    if meta_size == 0:
        warnings.append(f"size_bytes=0 en manifest, tamano real={real_size}")
    elif meta_size != real_size:
        warnings.append(f"size_bytes ({meta_size}) != tamano real ({real_size})")

    if manifest["metadata"]["checksum_sha256"]:
        h = hashlib.sha256()
        with open(mbtiles_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        if manifest["metadata"]["checksum_sha256"] != h.hexdigest():
            warnings.append("checksum_sha256 no coincide con el archivo real")

if warnings:
    print("Manifest VALIDO (con warnings):")
    for w in warnings:
        print(f"  - {w}")
else:
    print("Manifest VALIDO y consistente.")
