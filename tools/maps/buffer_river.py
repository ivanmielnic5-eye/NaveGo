import json, time, gc
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely import union_all
from shapely.ops import transform

SRC="agua.geojson"; OUT="corredor_buffer.geojson"
BUFFER_M=25000; SIMPLIFY_M=100; QUAD_SEGS=2
SRC_CRS="EPSG:4326"; UTM_CRS="EPSG:32720"

t0=time.time()
to_utm=Transformer.from_crs(SRC_CRS,UTM_CRS,always_xy=True).transform
to_wgs=Transformer.from_crs(UTM_CRS,SRC_CRS,always_xy=True).transform

data=json.load(open(SRC))
polys=[]
for feat in data["features"]:
    try:
        g=shape(feat["geometry"])
        if g.is_empty: continue
        g=transform(to_utm,g).simplify(SIMPLIFY_M,preserve_topology=False)
        if g.is_empty: continue
        polys.append(g.buffer(BUFFER_M,quad_segs=QUAD_SEGS,cap_style=2,join_style=2))
    except Exception: pass

print(f"Poligonos: {len(polys)} | t={time.time()-t0:.1f}s")
gc.collect()
merged=union_all(polys)
print(f"Unificado: {merged.geom_type} | t={time.time()-t0:.1f}s")
del polys; gc.collect()

wgs=transform(to_wgs,merged)
b=wgs.bounds
print(f"Bounds: lon[{b[0]:.4f},{b[2]:.4f}] lat[{b[1]:.4f},{b[3]:.4f}]")
out={"type":"FeatureCollection","features":[{"type":"Feature","properties":{"buffer_m":BUFFER_M,"source":"osm_waterway_buffer","crs_used":UTM_CRS},"geometry":mapping(wgs)}]}
json.dump(out,open(OUT,"w"))
print(f"Guardado: {OUT} | total={time.time()-t0:.1f}s")
