"""
analyze_highways.py — Analisis de highways del backup. SOLO LECTURA.

Cuenta ways y clasifica highway=* por tipo, y busca RN9 / RN11 / RN8.
Escribe resultados SOLO en el sandbox.
"""
import sys
import json
import collections
import time

sys.path.insert(0, "/home/ivan/navego_recuperado/sandbox_corredor")
from lib_pbf import (iter_blobs, decode_primitive_block, iter_ways,
                     get_way_refs, iter_fields, read_varint)

PBF = "/home/ivan/cockpit/backup_mapa/argentina-260901.osm.pbf"

# Bbox amplio del corredor (para acotar el conteo por ubicacion aproximada)
CORRIDOR = (-63.5, -36.5, -57.0, -30.5)  # min_lon,min_lat,max_lon,max_lat


def way_centroid(refs, node_locs):
    """Centroide aproximado a partir de nodos ya vistos."""
    pts = [node_locs[r] for r in refs if r in node_locs]
    if not pts:
        return None
    return (sum(p[0] for p in pts) / len(pts),
            sum(p[1] for p in pts) / len(pts))


def main():
    t0 = time.time()
    hw_counts = collections.Counter()
    ref_counts = collections.Counter()   # ref=* en highways
    n_ways = 0
    n_rels = 0
    # Candidatos RN9 / RN11 / RN8
    rn9, rn11, rn8 = [], [], []
    # Nodos del corredor (para centroide) — limitado en memoria
    node_locs = {}

    node_blobs = 0
    way_blobs = 0
    rel_blobs = 0

    for btype, data in iter_blobs(PBF):
        if btype == "OSMHeader":
            continue
        if btype == "OSMData":
            blk = decode_primitive_block(data)
            st = blk["stringtable"]
            gran = blk["granularity"]
            lat_off = blk["lat_offset"]
            lon_off = blk["lon_offset"]

            # Recolectar nodos de este bloque (dense o no)
            for g in blk["groups"]:
                for f, w, v, _ in iter_fields(g):
                    if f == 2:  # DenseNodes (schema: 1=Node, 2=DenseNodes, 3=Way, 4=Rel)
                        ids, lats, lons = [], [], []
                        for f2, w2, v2, _ in iter_fields(v):
                            if f2 == 1:
                                pos = 0
                                while pos < len(v2):
                                    x, pos = read_varint(v2, pos)
                                    ids.append(x)
                            elif f2 == 8:
                                pos = 0
                                while pos < len(v2):
                                    raw, pos = read_varint(v2, pos)
                                    lats.append((raw >> 1) ^ -(raw & 1))
                            elif f2 == 9:
                                pos = 0
                                while pos < len(v2):
                                    raw, pos = read_varint(v2, pos)
                                    lons.append((raw >> 1) ^ -(raw & 1))
                        lat = lon = 0
                        for i in range(min(len(ids), len(lats), len(lons))):
                            lat += lats[i]
                            lon += lons[i]
                            la = (lat_off + gran * lat) / 1e9
                            lo = (lon_off + gran * lon) / 1e9
                            # solo guardar los del corredor
                            if (CORRIDOR[1] <= la <= CORRIDOR[3] and
                                    CORRIDOR[0] <= lo <= CORRIDOR[2]):
                                node_locs[ids[i]] = (lo, la)
                    elif f == 1:  # Node normal (no dense)
                        nid = lat = lon = None
                        for f2, w2, v2, _ in iter_fields(v):
                            if w2 != 0:
                                continue
                            if f2 == 1:
                                nid = v2
                            elif f2 == 8:
                                lat = (v2 >> 1) ^ -(v2 & 1)
                            elif f2 == 9:
                                lon = (v2 >> 1) ^ -(v2 & 1)
                        if nid is not None and lat is not None and lon is not None:
                            la = (lat_off + gran * lat) / 1e9
                            lo = (lon_off + gran * lon) / 1e9
                            if (CORRIDOR[1] <= la <= CORRIDOR[3] and
                                    CORRIDOR[0] <= lo <= CORRIDOR[2]):
                                node_locs[nid] = (lo, la)
                    elif f == 3:  # Way
                        n_ways += 1
                        wid, keys, vals = None, [], []
                        for f2, w2, v2, _ in iter_fields(v):
                            if f2 == 1:
                                wid = v2
                            elif f2 == 2:
                                pos = 0
                                while pos < len(v2):
                                    x, pos = read_varint(v2, pos)
                                    keys.append(x)
                            elif f2 == 3:
                                pos = 0
                                while pos < len(v2):
                                    x, pos = read_varint(v2, pos)
                                    vals.append(x)
                        tags = {}
                        for i, k in enumerate(keys):
                            if i < len(vals) and k < len(st) and vals[i] < len(st):
                                tags[st[k].decode("utf-8", "replace")] = \
                                    st[vals[i]].decode("utf-8", "replace")
                        hw = tags.get("highway")
                        if hw:
                            hw_counts[hw] += 1
                            ref = tags.get("ref")
                            if ref:
                                ref_counts[ref] += 1
                            if ref in ("RN9", "9", "RN 9"):
                                rn9.append({"id": wid, "tags": tags})
                            elif ref in ("RN11", "11", "RN 11"):
                                rn11.append({"id": wid, "tags": tags})
                            elif ref in ("RN8", "8", "RN 8"):
                                rn8.append({"id": wid, "tags": tags})
                    elif f == 4:  # Relation
                        n_rels += 1
            node_blobs += 1
        elif btype == "OSMHeader":
            pass

    elapsed = time.time() - t0
    result = {
        "n_ways": n_ways,
        "n_relations": n_rels,
        "highway_counts": dict(hw_counts.most_common()),
        "n_highway_total": sum(hw_counts.values()),
        "n_nodes_corridor": len(node_locs),
        "rn9_count": len(rn9),
        "rn11_count": len(rn11),
        "rn8_count": len(rn8),
        "rn9_sample": rn9[:5],
        "rn11_sample": rn11[:5],
        "rn8_sample": rn8[:5],
        "top_refs": dict(ref_counts.most_common(40)),
        "elapsed_s": round(elapsed, 2),
    }
    with open("/home/ivan/navego_recuperado/sandbox_corredor/highway_analysis.json",
              "w") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    print(json.dumps({k: v for k, v in result.items()
                      if not k.endswith("_sample")}, indent=2, ensure_ascii=False))
    print(f"\nTiempo: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
