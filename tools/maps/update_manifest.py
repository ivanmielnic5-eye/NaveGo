import json, hashlib, os, sys

MANIFEST = "manifest.json"
MBTILES = "corredor_sf_caba.mbtiles"

if not os.path.exists(MBTILES):
    sys.exit(f"No existe {MBTILES}")

size = os.path.getsize(MBTILES)
h = hashlib.sha256()
with open(MBTILES, "rb") as f:
    for chunk in iter(lambda: f.read(1024*1024), b""):
        h.update(chunk)
sha = h.hexdigest()

m = json.load(open(MANIFEST))
m["metadata"]["size_bytes"] = size
m["metadata"]["checksum_sha256"] = sha
json.dump(m, open(MANIFEST, "w"), indent=2, ensure_ascii=False)

print(f"size_bytes: {size} ({size/1024/1024:.1f} MB)")
print(f"checksum:   {sha}")
