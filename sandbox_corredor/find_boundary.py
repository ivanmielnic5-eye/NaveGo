#!/usr/bin/env python3
"""READ-ONLY: find the byte offset where ways begin in the INTACT backup.
This quantifies exactly what the truncated target is missing."""
import struct, os, zlib
PBF = os.path.expanduser("~/cockpit/backup_mapa/argentina-260901.osm.pbf")
size = os.path.getsize(PBF)
def rv(b,p):
    v=0;sh=0
    while True:
        x=b[p];p+=1
        v|=(x&0x7f)<<sh
        if not(x&0x80): return v,p
        sh+=7
def skip(b,p,wt):
    if wt==0: _,p=rv(b,p)
    elif wt==1: p+=8
    elif wt==2:
        ln,p=rv(b,p);p+=ln
    elif wt==5: p+=4
    return p

off=0;n=0
first_way_off=None; last_node_off=None
f=open(PBF,"rb")
while off<size:
    f.seek(off);raw=f.read(4)
    if len(raw)<4: break
    (blen,)=struct.unpack(">I",raw)
    if blen==0 or blen>64*1024: break
    hdr=f.read(blen)
    p=0;ds=None
    while p<len(hdr):
        key,p=rv(hdr,p);fn,wt=key>>3,key&7
        if wt==2:
            ln,p=rv(hdr,p);p+=ln
        elif wt==0:
            v,p=rv(hdr,p)
            if fn==3: ds=v
        else: break
    if ds is None: break
    end=off+4+blen+ds
    if end>size: break
    f.seek(off+4+blen); blob=f.read(ds)
    p=0;body=None
    while p<len(blob):
        key,p=rv(blob,p);fn,wt=key>>3,key&7
        if wt==0: _,p=rv(blob,p)
        elif wt==2:
            ln,p=rv(blob,p);data=blob[p:p+ln];p+=ln
            if fn==3: body=zlib.decompress(data)
        else: break
    # inspect groups for presence of ways(3)/relations(4)
    p=0;types=set()
    while p<len(body):
        key,p=rv(body,p);fn,wt=key>>3,key&7
        if fn==2 and wt==2:
            ln,p=rv(body,p);g=body[p:p+ln];p+=ln
            q=0
            while q<len(g):
                k2,q=rv(g,q);f2,w2=k2>>3,k2&7
                if w2!=2:
                    q=skip(g,q,w2);continue
                l2,q=rv(g,q);q+=l2
                types.add(f2)
        else:
            p=skip(body,p,wt)
    if (3 in types or 4 in types) and first_way_off is None:
        first_way_off=off
        print(f"FIRST blob with ways/relations: index={n} offset={off:,} ({100*off/size:.4f}% of file)")
        print(f"  group field types: {sorted(types)}")
        print(f"  this is the NODE->WAY boundary")
        break
    if 2 in types:
        last_node_off=end
    n+=1;off=end
f.close()
print()
print(f"=== WHAT THE TRUNCATED TARGET IS MISSING ===")
print(f"  intact node section ends ~ offset {first_way_off:,}")
print(f"  target readable ends at   offset 257,238,148")
print(f"  missing from target: {(size-first_way_off):,} bytes of ways+relations")
