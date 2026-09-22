#!/usr/bin/env python3
"""Compute candidate corridor bboxes with explicit width justification.
Axis: Santa Fe Capital (north) -> Buenos Aires/CABA (south).
Latitudes are NEGATIVE and DECREASE going south, so bounds are normalized.
"""
import math
def km_per_deg_lat(lat): return 111.13295 - 0.55982*math.cos(2*math.radians(lat)) + 0.00117*math.cos(4*math.radians(lat))
def km_per_deg_lon(lat): return 111.41284*math.cos(math.radians(lat)) - 0.0935*math.cos(3*math.radians(lat)) + 0.00118*math.cos(5*math.radians(lat))

SF   = (-31.6107, -60.6973)
CABA = (-34.6037, -58.3816)

def norm(minlat,minlon,maxlat,maxlon):
    return (min(minlon,maxlon), min(minlat,maxlat), max(minlon,maxlon), max(minlat,maxlat))

def expand(a, b, half_km):
    minlat, maxlat = min(a[0],b[0]), max(a[0],b[0])
    minlon, maxlon = min(a[1],b[1]), max(a[1],b[1])
    midlat = (minlat+maxlat)/2
    dlat = half_km / km_per_deg_lat(midlat)
    worst = min(km_per_deg_lon(minlat), km_per_deg_lon(maxlat))
    dlon = half_km / worst
    return norm(minlat-dlat, minlon-dlon, maxlat+dlat, maxlon+dlon)

print("Axis: SF(-31.6107,-60.6973) -> CABA(-34.6037,-58.3816)")
print("Straight-line axis bbox (no width): ", norm(SF[0],SF[1],CABA[0],CABA[1]))
print()
for name, half in (("C1_ajustado_20km",20),("C2_medio_50km",50),("C3_amplio_90km",90)):
    mnlo,mnla,mxlo,mxla = expand(SF,CABA,half)
    midlat=(mnla+mxla)/2
    area = (mxlo-mnlo)*km_per_deg_lon(midlat) * (mxla-mnla)*km_per_deg_lat(midlat)
    print(f"{name}  half-width={half} km")
    print(f"   min_lon={mnlo:.6f}  min_lat={mnla:.6f}  max_lon={mxlo:.6f}  max_lat={mxla:.6f}")
    print(f"   span: lon={mxlo-mnlo:.4f} deg  lat={mxla-mnla:.4f} deg    area~{area:,.0f} km2")
    print(f"   km/deg at midlat {midlat:.3f}: lat={km_per_deg_lat(midlat):.3f} lon={km_per_deg_lon(midlat):.3f}")
    print()
