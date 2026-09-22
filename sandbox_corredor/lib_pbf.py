"""
lib_pbf.py — Lector PBF minimo, SOLO LECTURA, sin dependencias externas.

Implementa un decodificador de wire-format protobuf (varint, length-delimited)
y un lector de OSM PBF (bloques BlobHeader/Blob, PrimitiveBlock con
stringtable, granularidad y offsets).

NO escribe nada. NO modifica el PBF. Solo lee.

Soporta compresion zlib (la del backup: "Compression: none" en el header
se refiere al default; los blobs zlib se detectan por el campo 3 del Blob).
"""
import struct
import zlib


# --------------------------------------------------------------------------
# Wire format protobuf
# --------------------------------------------------------------------------
def read_varint(buf, pos):
    """Lee un varint. Devuelve (valor, nueva_pos)."""
    result = 0
    shift = 0
    while True:
        if pos >= len(buf):
            raise EOFError("varint truncado")
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift > 63:
            raise ValueError("varint demasiado largo")


def iter_fields(buf):
    """Itera (field_number, wire_type, valor, pos) de un mensaje protobuf.

    wire_type 0 -> valor = int (varint)
    wire_type 1 -> valor = bytes (8, fixed64)
    wire_type 2 -> valor = bytes (length-delimited)
    wire_type 5 -> valor = bytes (4, fixed32)
    """
    pos = 0
    n = len(buf)
    while pos < n:
        key, pos = read_varint(buf, pos)
        field = key >> 3
        wtype = key & 0x07
        if wtype == 0:
            val, pos = read_varint(buf, pos)
        elif wtype == 2:
            ln, pos = read_varint(buf, pos)
            val = buf[pos:pos + ln]
            pos += ln
        elif wtype == 1:
            val = buf[pos:pos + 8]
            pos += 8
        elif wtype == 5:
            val = buf[pos:pos + 4]
            pos += 4
        else:
            raise ValueError(f"wire_type no soportado: {wtype}")
        yield field, wtype, val, pos


def get_field(buf, target, default=None):
    """Primer valor del campo `target`."""
    for field, wtype, val, _ in iter_fields(buf):
        if field == target:
            return val
    return default


# --------------------------------------------------------------------------
# BlobHeader / Blob
# --------------------------------------------------------------------------
def iter_blobs(path, max_blobs=None):
    """Itera (blob_type, raw_bytes_descomprimidos) de un PBF.

    Formato fichero PBF:
      uint32 BE  len(BlobHeader)
      BlobHeader { 1: type (string), 3: datasize (int) }
      Blob       { 1: raw, 2: raw_size, 3: zlib_data }
    """
    with open(path, "rb") as fh:
        count = 0
        while True:
            head = fh.read(4)
            if len(head) < 4:
                return
            (hlen,) = struct.unpack(">I", head)
            hbuf = fh.read(hlen)
            if len(hbuf) < hlen:
                raise EOFError(f"BlobHeader truncado (leidos {len(hbuf)} de {hlen})")
            btype = get_field(hbuf, 1)
            datasize = get_field(hbuf, 3, 0)
            bbuf = fh.read(datasize)
            if len(bbuf) < datasize:
                raise EOFError(f"Blob truncado (leidos {len(bbuf)} de {datasize})")
            # Blob
            raw = get_field(bbuf, 1)
            zdata = get_field(bbuf, 3)
            if raw is not None:
                data = raw
            elif zdata is not None:
                data = zlib.decompress(zdata)
            else:
                raise ValueError("Blob sin raw ni zlib_data")
            yield btype.decode() if isinstance(btype, bytes) else btype, data
            count += 1
            if max_blobs and count >= max_blobs:
                return


def decode_stringtable(buf):
    """campo 1 (repetido) -> lista de bytes."""
    out = []
    for field, wtype, val, _ in iter_fields(buf):
        if field == 1:
            out.append(val)
    return out


def decode_primitive_block(buf):
    """Devuelve dict con stringtable, granularity, lat_offset, lon_offset y
    los grupos (campo 2 = primitivegroup)."""
    st = None
    gran = 100
    lat_off = 0
    lon_off = 0
    groups = []
    for field, wtype, val, _ in iter_fields(buf):
        if field == 1:
            st = decode_stringtable(val)
        elif field == 2:
            groups.append(val)
        elif field == 17:
            gran = val
        elif field == 19:
            lat_off = val if val < (1 << 63) else val - (1 << 64)
        elif field == 20:
            lon_off = val if val < (1 << 63) else val - (1 << 64)
    return {
        "stringtable": st or [],
        "granularity": gran,
        "lat_offset": lat_off,
        "lon_offset": lon_off,
        "groups": groups,
    }


def iter_dense_nodes(buf):
    """Decodifica un mensaje DenseNodes.

    IMPORTANTE (bug corregido 2026-09-22):
    Los campos `id` (1), `lat` (8) y `lon` (9) son variables `sint64`
    DELTA-ENCODED y ZIGZAG. NO son varints planos.
    Ver: osmformat.proto -> message DenseNodes { repeated sint64 id = 1
    [packed=true]; repeated sint64 lat = 8; repeated sint64 lon = 9; }

    Devuelve listas de valores YA acumulados (ids absolutos) y
    lat/lon absolutos en unidades de la granularidad.
    """
    raw_id, raw_lat, raw_lon = [], [], []
    for f2, w2, v2, _ in iter_fields(buf):
        if w2 != 2:
            continue
        pos = 0
        if f2 == 1:
            while pos < len(v2):
                x, pos = read_varint(v2, pos)
                raw_id.append((x >> 1) ^ -(x & 1))
        elif f2 == 8:
            while pos < len(v2):
                x, pos = read_varint(v2, pos)
                raw_lat.append((x >> 1) ^ -(x & 1))
        elif f2 == 9:
            while pos < len(v2):
                x, pos = read_varint(v2, pos)
                raw_lon.append((x >> 1) ^ -(x & 1))

    ids = _accumulate(raw_id)
    lats = _accumulate(raw_lat)
    lons = _accumulate(raw_lon)
    return ids, lats, lons


def _accumulate(deltas):
    """Convierte deltas en valores absolutos acumulados."""
    out = []
    cur = 0
    for d in deltas:
        cur += d
        out.append(cur)
    return out


def iter_ways(block):
    """Itera dicts de ways con tags resueltos.

    PrimitiveGroup campo 3 = repeated Way (no soporta DenseNodes).
    Way: 1=id, 2=keys, 3=vals, 8=refs (sint64 delta), 4=info
    """
    st = block["stringtable"]
    for g in block["groups"]:
        for field, wtype, val, _ in iter_fields(g):
            if field != 3:
                continue
            wid = None
            keys = []
            vals = []
            for f2, w2, v2, _ in iter_fields(val):
                if f2 == 1:
                    wid = v2
                elif f2 == 2:
                    if w2 == 2:
                        pos = 0
                        while pos < len(v2):
                            k, pos = read_varint(v2, pos)
                            keys.append(k)
                    else:
                        keys.append(v2)
                elif f2 == 3:
                    if w2 == 2:
                        pos = 0
                        while pos < len(v2):
                            v, pos = read_varint(v2, pos)
                            vals.append(v)
                    else:
                        vals.append(v2)
            tags = {}
            for i, k in enumerate(keys):
                if i < len(vals) and k < len(st) and vals[i] < len(st):
                    tags[st[k].decode("utf-8", "replace")] = \
                        st[vals[i]].decode("utf-8", "replace")
            yield {"id": wid, "tags": tags}


def get_way_refs(waybuf):
    """Extrae refs (sint64 zigzag delta) de un Way."""
    refs = []
    for f, w, v, _ in iter_fields(waybuf):
        if f == 8:
            pos = 0
            ref = 0
            while pos < len(v):
                raw, pos = read_varint(v, pos)
                delta = (raw >> 1) ^ -(raw & 1)
                ref += delta
                refs.append(ref)
    return refs
