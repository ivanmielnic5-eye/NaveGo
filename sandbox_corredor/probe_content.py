#!/usr/bin/env python3
"""
READ-ONLY structural probe of argentina-latest.osm.pbf.

Decompresses every COMPLETE OSMData blob and reads PrimitiveBlock /
PrimitiveGroup headers to report:
  - element counts by type (node/way/relation)
  - the ORDER in which types appear through the file
  - geographic extent covered by the readable portion

Does NOT modify the PBF. Writes only to stdout.

OSM PBF PrimitiveGroup fields:
  1 = nodes (repeated Node)
  2 = dense (DenseNodes)
  3 = ways (repeated Way)
  4 = relations (repeated Relation)
"""
import struct, os, zlib

PBF = os.path.expanduser("~/cockpit/argentina-latest.osm.pbf")
size = os.path.getsize(PBF)

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
    else: raise ValueError(f"wiretype {wt}")
    return p

def zigzag(n):
    return (n >> 1) ^ -(n & 1)

def scan_block(body):
    """Return dict of counts + bbox covered by this block (approx via offsets)."""
    p = 0; gran = 100; lat_off = 0; lon_off = 0
    groups = []
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
        else:
            p = skip(body, p, wt)

    c = {}
    bb = [None, None, None, None]  # minlon,minlat,maxlon,maxlat

    def upd(lon_i, lat_i):
        lon = 1e-9 * (lon_off + gran * lon_i)
        lat = 1e-9 * (lat_off + gran * lat_i)
        if bb[0] is None or lon < bb[0]: bb[0] = lon
        if bb[2] is None or lon > bb[2]: bb[2] = lon
        if bb[1] is None or lat < bb[1]: bb[1] = lat
        if bb[3] is None or lat > bb[3]: bb[3] = lat

    for g in groups:
        q = 0
        while q < len(g):
            key, q = rv(g, q); fn, wt = key >> 3, key & 7
            if wt != 2:
                q = skip(g, q, wt); continue
            ln, q = rv(g, q); payload = g[q:q+ln]; q += ln
            if fn == 1:      # Node
                c["node"] = c.get("node", 0) + 1
                r = 0
                while r < len(payload):
                    k2, r = rv(payload, r); f2, w2 = k2 >> 3, k2 & 7
                    if f2 == 8 and w2 == 0:
                        v, r = rv(payload, r)
                        upd(zigzag(v), 0) if False else None
                    else:
                        r = skip(payload, r, w2)
            elif fn == 2:    # DenseNodes
                c["dense_node_group"] = c.get("dense_node_group", 0) + 1
                r = 0; lat_v = []; lon_v = []
                while r < len(payload):
                    k2, r = rv(payload, r); f2, w2 = k2 >> 3, k2 & 7
                    if f2 == 8 and w2 == 2:      # id (packed sint64)
                        l2, r = rv(payload, r); ids = payload[r:r+l2]; r += l2
                    elif f2 == 9 and w2 == 2:    # lat (packed sint64)
                        l2, r = rv(payload, r); lat_v = payload[r:r+l2]; r += l2
                    elif f2 == 10 and w2 == 2:   # lon (packed sint64)
                        l2, r = rv(payload, r); lon_v = payload[r:r+l2]; r += l2
                    elif f2 == 8 and w2 == 0:
                        _, r = rv(payload, r)
                    else:
                        r = skip(payload, r, w2)
                # decode deltas -> count + bbox
                pp = 0; acc = 0; lats = []
                while pp < len(lat_v):
                    v, pp = rv(lat_v, pp); acc += zigzag(v); lats.append(acc)
                pp = 0; acc = 0; lons = []
                while pp < len(lon_v):
                    v, pp = rv(lon_v, pp); acc += zigzag(v); lons.append(acc)
                c["node"] = c.get("node", 0) + len(lats)
                for la, lo in zip(lats, lons): upd(lo, la)
            elif fn == 3:
                c["way"] = c.get("way", 0) + 1
            elif fn == 4:
                c["relation"] = c.get("relation", 0) + 1
    return c, bb

off = 0; n = 0; last_ok = 0
timeline = []; tot = {}
gminlon = gminlat = gmaxlon = gmaxlat = None
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
        if end > size:
            print(f"STOP: truncated final blob at offset {off} "
                  f"(missing {end-size} bytes)", flush=True)
            break
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
        c, bb = scan_block(body)
        for k, v in c.items(): tot[k] = tot.get(k, 0) + v
        if bb[0] is not None:
            gminlon = bb[0] if gminlon is None else min(gminlon, bb[0])
            gminlat = bb[1] if gminlat is None else min(gminlat, bb[1])
            gmaxlon = bb[2] if gmaxlon is None else max(gmaxlon, bb[2])
            gmaxlat = bb[3] if gmaxlat is None else max(gmaxlat, bb[3])
        timeline.append((n, 100*off/size, dict(c)))
        n += 1; last_ok = end; off = end

print("=== TOTAL COUNTS (readable portion) ===")
for k in ("node", "dense_node_group", "way", "relation"):
    if k in tot: print(f"  {k}: {tot[k]:,}")
print(f"\nblobs_scanned: {n}")
print(f"readable_bytes: {last_ok:,} / {size:,} ({100*last_ok/size:.4f}%)")
print(f"bbox_of_readable_portion: ({gminlon:.6f},{gminlat:.6f},{gmaxlon:.6f},{gmaxlat:.6f})")

print("\n=== TYPE ORDER THROUGH FILE (every ~5%) ===")
def s(c): return ",".join(f"{k}={v}" for k, v in sorted(c.items())) or "(empty)"
step = max(1, n//22)
for i, pct, c in timeline[::step]:
    print(f"  blob {i:5d} @{pct:7.3f}%  {s(c)}")
print(f"  FIRST: {s(timeline[0][2])}")
print(f"  LAST : {s(timeline[-1][2])}")

# boundaries
def first_blob_with(key):
    for i, pct, c in timeline:
        if c.get(key): return i, pct
    return None
for k in ("node", "way", "relation"):
    r = first_blob_with(k)
    print(f"first blob containing {k}: {r}")
