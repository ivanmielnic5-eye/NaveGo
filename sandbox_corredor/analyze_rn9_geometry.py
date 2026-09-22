"""
analyze_rn9_geometry.py — Geometria REAL de RN9/RN11/RN8. SOLO LECTURA.

Problema: en PBF ordenado por tipo, los ways vienen antes de... no: vienen
DESPUES de los nodos (type_then_ID). Pero el lector necesita las coordenadas
de los nodos referenciados por las ways del corredor.

Estrategia de 2 pasadas (sin escribir nada):
  Pasada 1: recolectar coords de nodos dentro de la ventana de interes.
  Pasada 2: para cada way con ref RN9/RN11/RN8, resolver sus refs y quedarse
            con los puntos que caen en la ventana.
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

# Ventana de trabajo (generosa): todo el litoral pampeano
WIN = (-64.0, -37.5, -57.0, -30.0)  # lon_min, lat_min, lon_max, lat_max

TARGET_REFS = {"RN9", "RN11", "RN8"}


def iter_dense_nodes_local(buf):
    """DEPRECADO: usar lib_pbf.iter_dense_nodes (zigzag corregido)."""
    return iter_dense_nodes(buf)


def iter_nodes(buf):
    """Node normal (no dense)."""
    nid = lat = lon = None
    for f2, w2, v2, _ in iter_fields(buf):
        if w2 != 0:
            continue
        if f2 == 1:
            nid = v2
        elif f2 == 8:
            lat = (v2 >> 1) ^ -(v2 & 1)
        elif f2 == 9:
            lon = (v2 >> 1) ^ -(v2 & 1)
    return nid, lat, lon


def pass1_nodes():
    """Coords de todos los nodos dentro de WIN -> dict id -> (lon,lat)."""
    locs = {}
    t0 = time.time()
    for btype, data in iter_blobs(PBF):
        if btype != "OSMData":
            continue
        blk = decode_primitive_block(data)
        gran = blk["granularity"]
        lat_off = blk["lat_offset"]
        lon_off = blk["lon_offset"]
        for g in blk["groups"]:
            for f, w, v, _ in iter_fields(g):
                if f == 2:  # DenseNodes (schema: 1=Node, 2=DenseNodes, 3=Way, 4=Rel)
                    ids, lats, lons = iter_dense_nodes(v)  # ya acumulados
                    for i in range(min(len(ids), len(lats), len(lons))):
                        la = (lat_off + gran * lats[i]) / 1e9
                        lo = (lon_off + gran * lons[i]) / 1e9
                        if WIN[0] <= lo <= WIN[2] and WIN[1] <= la <= WIN[3]:
                            locs[ids[i]] = (lo, la)
                elif f == 1:  # Node normal (no dense)
                    nid, lat, lon = iter_nodes(v)
                    if nid is not None and lat is not None and lon is not None:
                        la = (lat_off + gran * lat) / 1e9
                        lo = (lon_off + gran * lon) / 1e9
                        if WIN[0] <= lo <= WIN[2] and WIN[1] <= la <= WIN[3]:
                            locs[nid] = (lo, la)
    print(f"  nodos en ventana: {len(locs):,}  ({time.time()-t0:.1f}s)")
    return locs


def pass2_ways(locs):
    """Ways con ref objetivo, con sus puntos resueltos."""
    out = collections.defaultdict(list)
    t0 = time.time()
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
                ref = tags.get("ref")
                if ref not in TARGET_REFS:
                    continue
                refs = get_way_refs(v)
                pts = [locs[r] for r in refs if r in locs]
                if pts:
                    out[ref].append({
                        "id": wid,
                        "highway": tags.get("highway"),
                        "name": tags.get("name"),
                        "oneway": tags.get("oneway"),
                        "n_refs": len(refs),
                        "n_pts_local": len(pts),
                        "pts": pts,
                    })
    print(f"  ways resueltas ({time.time()-t0:.1f}s): " +
          ", ".join(f"{k}={len(v)}" for k, v in out.items()))
    return out


def main():
    print("PASADA 1: nodos del corredor")
    locs = pass1_nodes()
    print("PASADA 2: ways RN9/RN11/RN8")
    ways = pass2_ways(locs)

    summary = {"window": WIN, "nodes_in_window": len(locs), "routes": {}}
    for ref, lst in ways.items():
        allpts = [p for w in lst for p in w["pts"]]
        lons = [p[0] for p in allpts]
        lats = [p[1] for p in allpts]
        # Extremos geograficos y sus vecinos
        north = max(allpts, key=lambda p: p[1])
        south = min(allpts, key=lambda p: p[1])
        west = min(allpts, key=lambda p: p[0])
        east = max(allpts, key=lambda p: p[0])
        summary["routes"][ref] = {
            "n_ways": len(lst),
            "n_points": len(allpts),
            "bbox_pts": [min(lons), min(lats), max(lons), max(lats)],
            "north_point": north,
            "south_point": south,
            "west_point": west,
            "east_point": east,
            "highway_types": dict(collections.Counter(
                w["highway"] for w in lst)),
        }
    with open("/home/ivan/navego_recuperado/sandbox_corredor/rn_geometry.json",
              "w") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
