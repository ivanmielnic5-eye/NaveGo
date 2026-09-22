"""
corridor_axis.py — Eje RN9 Santa Fe Capital -> CABA. SOLO LECTURA.

Objetivo: medir la geometria REAL de RN9 en el tramo Santa Fe -> CABA
para calcular un bbox defendible (no una linea recta asumida).

Metodo:
  1. Pasada de nodos en ventana amplia (todo el litoral).
  2. Recolectar todos los ways ref=RN9 con sus puntos.
  3. Quedarse con el tramo que va de Santa Fe a CABA:
       - Santa Fe Capital ~ (-60.70, -31.65)
       - CABA            ~ (-58.45, -34.60)
     Se toma el corredor latitudinal [-34.75, -31.45] y se descartan
     los tramos de RN9 al oeste de -61.5 (Cordoba) que no pertenecen
     al eje litoral.
  4. Reportar: extremos, perfil por banda de latitud, longitud aproximada.
"""
import sys
import json
import math
import time
import collections

sys.path.insert(0, "/home/ivan/navego_recuperado/sandbox_corredor")
from lib_pbf import (iter_blobs, decode_primitive_block, iter_fields,
                     read_varint, get_way_refs, iter_dense_nodes)

PBF = "/home/ivan/cockpit/backup_mapa/argentina-260901.osm.pbf"

# Ventana amplia para capturar RN9 completa en el litoral
WIN = (-64.5, -36.5, -57.0, -29.5)

# Extremos de referencia (declarados por el Director / OSM)
SANTA_FE = (-60.7000, -31.6500)
CABA = (-58.4500, -34.6000)

# Banda latitudinal del tramo SF -> CABA (con holgura)
LAT_MIN, LAT_MAX = -34.90, -31.45
# Limite oeste: descartar RN9 cordobesa (el eje litoral va por ~-60.5)
LON_WEST_CUT = -61.50


def haversine(a, b):
    R = 6371.0
    lon1, lat1 = math.radians(a[0]), math.radians(a[1])
    lon2, lat2 = math.radians(b[0]), math.radians(b[1])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def main():
    t0 = time.time()
    locs = {}
    print("PASADA 1: nodos en ventana litoral")
    for btype, data in iter_blobs(PBF):
        if btype != "OSMData":
            continue
        blk = decode_primitive_block(data)
        gran = blk["granularity"]
        lat_off = blk["lat_offset"]
        lon_off = blk["lon_offset"]
        for g in blk["groups"]:
            for f, w, v, _ in iter_fields(g):
                if f == 2:
                    ids, lats, lons = iter_dense_nodes(v)
                    for i in range(min(len(ids), len(lats), len(lons))):
                        la = (lat_off + gran * lats[i]) / 1e9
                        lo = (lon_off + gran * lons[i]) / 1e9
                        if WIN[0] <= lo <= WIN[2] and WIN[1] <= la <= WIN[3]:
                            locs[ids[i]] = (lo, la)
    print(f"  nodos: {len(locs):,} ({time.time()-t0:.0f}s)")

    print("PASADA 2: ways RN9")
    t1 = time.time()
    rn9_ways = []
    for btype, data in iter_blobs(PBF):
        if btype != "OSMData":
            continue
        blk = decode_primitive_block(data)
        st = blk["stringtable"]
        for g in blk["groups"]:
            for f, w, v, _ in iter_fields(g):
                if f != 3:
                    continue
                wid = None
                keys, vals = [], []
                for f2, w2, v2, _ in iter_fields(v):
                    if f2 == 1 and w2 == 0:
                        wid = v2
                    elif f2 == 2 and w2 == 2:
                        pos = 0
                        while pos < len(v2):
                            x, pos = read_varint(v2, pos)
                            keys.append(x)
                    elif f2 == 3 and w2 == 2:
                        pos = 0
                        while pos < len(v2):
                            x, pos = read_varint(v2, pos)
                            vals.append(x)
                tags = {}
                for i, k in enumerate(keys):
                    if i < len(vals) and k < len(st) and vals[i] < len(st):
                        tags[st[k].decode("utf-8", "replace")] = \
                            st[vals[i]].decode("utf-8", "replace")
                if tags.get("ref") != "RN9":
                    continue
                refs = get_way_refs(v)
                pts = [locs[r] for r in refs if r in locs]
                if not pts:
                    continue
                # Filtrar al tramo SF->CABA
                sel = [p for p in pts
                       if LAT_MIN <= p[1] <= LAT_MAX and p[0] >= LON_WEST_CUT]
                if sel:
                    rn9_ways.append({
                        "id": wid,
                        "highway": tags.get("highway"),
                        "name": tags.get("name"),
                        "oneway": tags.get("oneway"),
                        "pts": sel,
                    })
    print(f"  ways RN9 en el tramo: {len(rn9_ways)} ({time.time()-t1:.0f}s)")

    allpts = [p for w in rn9_ways for p in w["pts"]]
    lons = [p[0] for p in allpts]
    lats = [p[1] for p in allpts]

    # Perfil por banda de 0.25 grados de latitud: min/max lon
    bands = collections.defaultdict(list)
    for lo, la in allpts:
        bands[round(la * 4) / 4].append(lo)

    profile = []
    for la in sorted(bands, reverse=True):
        v = bands[la]
        profile.append({
            "lat": la,
            "n": len(v),
            "lon_min": round(min(v), 6),
            "lon_max": round(max(v), 6),
            "lon_span_km": round((max(v) - min(v)) * 111 * math.cos(math.radians(la)), 2),
        })

    # Longitud acumulada aproximada del eje (no es ruta navegable, es cota)
    # Ordenar por latitud descendente tomando la mediana de lon por banda
    axis = []
    for la in sorted(bands, reverse=True):
        v = bands[la]
        v_sorted = sorted(v)
        med = v_sorted[len(v_sorted) // 2]
        axis.append((med, la))
    length = sum(haversine(axis[i], axis[i + 1]) for i in range(len(axis) - 1))

    out = {
        "reference_points": {
            "santa_fe": SANTA_FE,
            "caba": CABA,
        },
        "filter": {"lat_min": LAT_MIN, "lat_max": LAT_MAX,
                    "lon_west_cut": LON_WEST_CUT},
        "n_ways_rn9_tramo": len(rn9_ways),
        "n_points": len(allpts),
        "bbox_rn9_tramo": [min(lons), min(lats), max(lons), max(lats)],
        "north_point": max(allpts, key=lambda p: p[1]),
        "south_point": min(allpts, key=lambda p: p[1]),
        "west_point": min(allpts, key=lambda p: p[0]),
        "east_point": max(allpts, key=lambda p: p[0]),
        "lat_profile": profile,
        "approx_axis_length_km": round(length, 1),
        "highway_types": dict(collections.Counter(w["highway"] for w in rn9_ways)),
    }
    with open("/home/ivan/navego_recuperado/sandbox_corredor/corridor_axis.json",
              "w") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    print(json.dumps({k: v for k, v in out.items() if k != "lat_profile"},
                     indent=2, ensure_ascii=False))
    print(f"\nPerfil latitudinal (bandas de 0.25 grados):")
    for p in profile:
        print(f"  lat {p['lat']:>7.2f}  n={p['n']:>5}  "
              f"lon [{p['lon_min']:.4f}, {p['lon_max']:.4f}]  "
              f"span {p['lon_span_km']:>6.1f} km")


if __name__ == "__main__":
    main()
