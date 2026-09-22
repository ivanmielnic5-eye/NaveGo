#!/usr/bin/env python3
"""Diagnostic: print actual node coordinate ranges from a few blobs."""
import struct, os, zlib
PBF = os.path.expanduser("~/cockpit/argentina-latest.osm.pbf")
size = os.path.getsize(PBF)
def rv(buf,p):
    v=0;sh=0
    while True:
        b=buf[p];p+=1
        v|=(b&0x7f)<<sh
        if not (b&0x80): return v,p
        sh+=7
def skip(buf,p,wt):
    if wt==0: _,p=rv(buf,p)
    elif wt==1: p+=8
    elif wt==2:
        ln,p=rv(buf,p);p+=ln
    elif wt==5: p+=4
    return p
def zz(n): return (n>>1)^-(n&1)

off=0;n=0
with open(PBF,"rb") as f:
    while off<size and n<5:
        f.seek(off);raw=f.read(4)
        if len(raw)<4: break
        (blen,)=struct.unpack(">I",raw)
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
        end=off+4+blen+ds
        if end>size: break
        f.seek(off+4+blen);blob=f.read(ds)
        p=0;body=None
        while p<len(blob):
            key,p=rv(blob,p);fn,wt=key>>3,key&7
            if wt==0: _,p=rv(blob,p)
            elif wt==2:
                ln,p=rv(blob,p);data=blob[p:p+ln];p+=ln
                if fn==3: body=zlib.decompress(data)
            else: break
        # PrimitiveBlock header
        p=0;gran=100;lat_off=0;lon_off=0;groups=[]
        while p<len(body):
            key,p=rv(body,p);fn,wt=key>>3,key&7
            if fn==2 and wt==2:
                ln,p=rv(body,p);groups.append(body[p:p+ln]);p+=ln
            elif fn==17 and wt==0: gran,p=rv(body,p)
            elif fn==19 and wt==0:
                lat_off,p=rv(body,p)
                if lat_off>=2**31: lat_off-=2**32
            elif fn==20 and wt==0:
                lon_off,p=rv(body,p)
                if lon_off>=2**31: lon_off-=2**32
            else: p=skip(body,p,wt)
        print(f"--- blob {n}: gran={gran} lat_off={lat_off} lon_off={lon_off} groups={len(groups)}")
        for g in groups[:1]:
            q=0
            while q<len(g):
                key,q=rv(g,q);fn,wt=key>>3,key&7
                if wt!=2:
                    q=skip(g,q,wt);continue
                ln,q=rv(g,q);payload=g[q:q+ln];q+=ln
                if fn!=2: continue
                r=0;lat_v=b"";lon_v=b""
                while r<len(payload):
                    k2,r=rv(payload,r);f2,w2=k2>>3,k2&7
                    if f2==9 and w2==2:
                        l2,r=rv(payload,r);lat_v=payload[r:r+l2];r+=l2
                    elif f2==10 and w2==2:
                        l2,r=rv(payload,r);lon_v=payload[r:r+l2];r+=l2
                    else: r=skip(payload,r,w2)
                pp=0;acc=0;lats=[]
                while pp<len(lat_v):
                    v,pp=rv(lat_v,pp);acc+=zz(v);lats.append(acc)
                pp=0;acc=0;lons=[]
                while pp<len(lon_v):
                    v,pp=rv(lon_v,pp);acc+=zz(v);lons.append(acc)
                if lats:
                    print(f"    n_lat={len(lats)} n_lon={len(lons)}")
                    print(f"    raw lat first={lats[0]} last={lats[-1]} min={min(lats)} max={max(lats)}")
                    print(f"    deg  lat min={1e-9*(lat_off+gran*min(lats)):.6f} max={1e-9*(lat_off+gran*max(lats)):.6f}")
                    print(f"    deg  lon min={1e-9*(lon_off+gran*min(lons)):.6f} max={1e-9*(lon_off+gran*max(lons)):.6f}")
        n+=1;off=end
