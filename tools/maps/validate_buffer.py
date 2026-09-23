import json, sys
from shapely.geometry import shape
from shapely.ops import unary_union

SRC = sys.argv[1] if len(sys.argv) > 1 else "corredor_buffer.geojson"
data = json.load(open(SRC))
geoms = [shape(f["geometry"]) for f in data["features"]]
geom = unary_union(geoms)

minx, miny, maxx, maxy = geom.bounds
bbox_area = (maxx - minx) * (maxy - miny)
ratio = geom.area / bbox_area if bbox_area else 0

print(f"Area geometria: {geom.area:.4f}")
print(f"Area bbox:      {bbox_area:.4f}")
print(f"Ratio geom/bbox: {ratio:.2%}")
print(f"Vertices: {sum(len(p.exterior.coords) for p in (geom.geoms if hasattr(geom,'geoms') else [geom]))}")

if ratio > 0.80:
    print("ALERTA: el buffer parece un rectangulo (ratio > 80%)")
    sys.exit(1)
print("OK: el buffer tiene forma de corredor")
