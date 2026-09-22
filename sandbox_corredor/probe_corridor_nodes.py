#!/usr/bin/env python3
"""
READ-ONLY: verify whether NODES inside the Santa Fe -> CABA corridor
bbox exist in the readable (non-truncated) portion of the target PBF.
Nodes alone do not give roads, but this establishes coverage of the
node layer. Writes only to stdout.
"""
import struct, os, zlib

PBF = os.path.expanduser("~/cockpit/argentina-latest.osm.pbf")
size = os.path.getsize(PBF)

# Corridor bounding box: Santa Fe Capital -> Buenos Aires (CABA), generous
MINLON, MINLAT, MAXLON, MAXLAT = -62.5, -35.5, -57.5, -30.0

def rv(buf, p):
    v = 0; sh = 0
    while True:
        b = buf[p]; p += 1
        v |= (b & 0x7F) << sh
        if not (b & 0x80): return v, p
        sh += 7

def skip(buf, p, wt):
    if wt == 0: _, p = rv(buf, p)
    elif wt == 1: p += 8
    elif wt == 2:
        ln, p = rv(buf, p); p += ln
    elif wt == 5: p += 4
    return p

def zz(n): return (n >> 1) ^ -(n & 1)

off = 0; n = 0; last_ok = 0
in_corridor = 0
corridor_bbox = [None]*4
with open(PBF, "rb") as f:
    while off < size:
        f.seek(off); raw = f.read(4)
        if len(raw) < 4: break
        (blen,) = struct.unpack(">I", raw)
        if blen == 0 or blen > 64*1024: break
        hdr = f.read(blen)
        if len(hdr) < blen: break
        p = 0; datasize = None
        while p < len(hdr):
            key, p = rv(hdr, p); fn, wt = key >> 3, key & 7
            if wt == 2:
                ln, p = rv(hdr, p); p += ln
            elif wt == 0:
                v, p = rv(hdr, p)
                if fn == 3: datasize = v
            else: break
        if datasize is None: break
        end = off + 4 + blen + datasize
        if end > size: break
        f.seek(off + 4 + blen)
        blob = f.read(datasize)
        p = 0; body = None
        while p < len(blob):
            key, p = rv(blob, p); fn, wt = key >> 3, key & 7
            if wt == 0: _, p = rv(blob, p)
            elif wt == 2:
                ln, p = rv(blob, p); data = blob[p:p+ln]; p += ln
                if fn == 3: body = zlib.decompress(data)
            else: break
        # parse PrimitiveBlock
        p = 0; gran = 100; lat_off = 0; lon_off = 0; groups = []
        while p < len(body):
            key, p = rv(body, p); fn, wt = key >> 3, key & 7
            if fn == 2 and wt == 2:
                ln, p = rv(body, p); groups.append(body[p:p+ln]); p += ln
            elif fn == 17 and wt == 0: gran, p = rv(body, p)
            elif fn == 19 and wt == 0:
                lat_off, p = rv(body, p)
                if lat_off >= 2**31: lat_off -= 2**32
            elif fn == 20 and wt == 0:
                lon_off, p = rv(body, p)
                if lon_off >= 2**31: lon_off -= 2**32
            else: p = skip(body, p, wt)
        for g in groups:
            q = 0
            while q < len(g):
                key, q = rv(g, q); fn, wt = key >> 3, key & 7
                if wt != 2:
                    q = skip(g, q, wt); continue
                ln, q = rv(g, q); payload = g[q:q+ln]; q += ln
                if fn != 2: continue     # only DenseNodes
                r = 0; lat_v = b""; lon_v = b""
                while r < len(payload):
                    k2, r = rv(payload, r); f2, w2 = k2 >> 3, k2 & 7
                    if f2 == 8 and w2 == 2:
                        l2, r = rv(payload, r); lat_v = payload[r:r+l2]; r += l2
                    elif f2 == 9 and w2 == 2:
                        l2, r = rv(payload, r); lon_v = payload[r:r+l2]; r += l2
                    else:
                        r = skip(payload, r, w2)
                pp = 0; acc = 0; lats = []
                while pp < len(lat_v):
                    v, pp = rv(lat_v, pp); acc += zz(v); lats.append(acc)
                pp = 0; acc = 0; lons = []
                while pp < len(lon_v):
                    v, pp = rv(lon_v, pp); acc += zz(v); lons.append(acc)
                for la_i, lo_i in zip(lats, lons):
                    la = 1e-9*(lat_off + gran*la_i)
                    lo = 1e-9*(lon_off + gran*lo_i)
                    if MINLON <= lo <= MAXLON and MINLAT <= la <= MAXLAT:
                        in_corridor += 1
                        if corridor_bbox[0] is None or lo < corridor_bbox[0]: corridor_bbox[0] = lo
                        if corridor_bbox[1] is None or la < corridor_bbox[1]: corridor_bbox[1] = la
                        if corridor_bbox[2] is None or lo > corridor_bbox[2]: corridor_bbox[2] = lo
                        if corridor_bbox[3] is None or la > corridor_bbox[3]: corridor_bbox[3] = la
        n += 1; last_ok = end; off = end

print(f"blobs_read: {n}")
print(f"readable_bytes: {last_ok:,} / {size:,}")
print(f"corridor_bbox_queried: ({MINLON},{MINLAT},{MAXLON},{MAXLAT})")
print(f"NODES inside corridor (readable portion): {in_corridor:,}")
print(f"corridor_nodes_actual_bbox: {corridor_bbox}")
print()
print("NOTE: ways (roads) and relations are NOT in the readable portion.")
