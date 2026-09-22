#!/usr/bin/env python3
"""
READ-ONLY probe: locate truncation point of the PBF by walking the
blob framing (4-byte big-endian BlobHeader length + BlobHeader protobuf).
Does NOT modify the PBF. Reads only. Writes only to stdout.
"""
import struct, os

PBF = os.path.expanduser("~/cockpit/argentina-latest.osm.pbf")
size = os.path.getsize(PBF)
print(f"file_size_bytes: {size}")

def read_varint(buf, p):
    v = 0; sh = 0
    while True:
        b = buf[p]; p += 1
        v |= (b & 0x7F) << sh
        if not (b & 0x80):
            return v, p
        sh += 7

off = 0; nblob = 0; last_ok = 0; header_end = None
types = {}
with open(PBF, "rb") as f:
    while off < size:
        f.seek(off)
        raw = f.read(4)
        if len(raw) < 4:
            print(f"TRUNCATED_AT_LENGTH_PREFIX offset={off} remaining={len(raw)}")
            break
        (blen,) = struct.unpack(">I", raw)
        if blen == 0 or blen > 64 * 1024:
            print(f"SUSPICIOUS_BLOBHEADER_LEN offset={off} blen={blen}")
            break
        hdr = f.read(blen)
        if len(hdr) < blen:
            print(f"TRUNCATED_IN_BLOBHEADER offset={off} want={blen} got={len(hdr)}")
            break
        p = 0; btype = None; datasize = None
        while p < len(hdr):
            key, p = read_varint(hdr, p)
            fn, wt = key >> 3, key & 7
            if wt == 2:
                ln, p = read_varint(hdr, p)
                val = hdr[p:p+ln]; p += ln
                if fn == 1:
                    btype = val.decode("utf-8", "replace")
            elif wt == 0:
                v, p = read_varint(hdr, p)
                if fn == 3:
                    datasize = v
            else:
                print(f"UNEXPECTED_WIRE_TYPE offset={off} fn={fn} wt={wt}")
                p = len(hdr)
        if datasize is None:
            print(f"NO_DATASIZE offset={off} type={btype} header_len={blen}")
            break
        blob_end = off + 4 + blen + datasize
        if blob_end > size:
            print(f"TRUNCATED_BLOB offset={off} type={btype} datasize={datasize} "
                  f"need_end={blob_end} file_size={size} missing_bytes={blob_end-size}")
            break
        if nblob == 0:
            header_end = blob_end
        types[btype] = types.get(btype, 0) + 1
        nblob += 1; last_ok = blob_end; off = blob_end

print("--- SUMMARY ---")
print(f"complete_blobs_read: {nblob}")
print(f"header_blob_end: {header_end}")
print(f"last_complete_blob_end: {last_ok}")
print(f"bytes_readable_pct: {100*last_ok/size:.4f}")
print(f"blob_types: {types}")
