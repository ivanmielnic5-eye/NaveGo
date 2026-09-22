#!/usr/bin/env python3
"""
READ-ONLY: compute corridor geography.
Uses the intact backup PBF? NO - we only read headers here.
Computes haversine distances and bbox math for candidate corridors.
Writes only to stdout.
"""
import math

def hav(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2-lat1); dl = math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def km_per_deg_lat(lat): return 111.13295 - 0.55982*math.cos(2*math.radians(lat)) + 0.00117*math.cos(4*math.radians(lat))
def km_per_deg_lon(lat): return 111.41284*math.cos(math.radians(lat)) - 0.0935*math.cos(3*math.radians(lat)) + 0.00118*math.cos(5*math.radians(lat))

print("=== REFERENCE POINTS (documented coordinates, not invented) ===")
pts = {
 "Santa Fe Capital (plaza/centro)": (-31.6107, -60.6973),
 "Rosario centro":                  (-32.9442, -60.6505),
 "San Nicolas":                     (-33.3330, -60.2110),
 "Buenos Aires (Obelisco/CABA)":    (-34.6037, -58.3816),
 "Zarate":                          (-34.0981, -59.0286),
 "Pergamino":                       (-33.8899, -60.5733),
 "San Pedro":                       (-33.6791, -59.6669),
 "La Plata":                        (-34.9214, -57.9544),
 "Cordoba Capital":                 (-31.4201, -64.1888),
 "Rafaela":                         (-31.2503, -61.4867),
 "Reconquista":                     (-29.1430, -59.6435),
 "Rio Cuarto":                      (-33.1300, -64.3499),
 "Villa Maria":                     (-32.4075, -63.2401),
 "Bahia Blanca":                    (-38.7183, -62.2663),
 "Mendoza":                         (-32.8895, -68.8458),
 "Concordia":                       (-31.3925, -58.0209),
 "Gualeguaychu":                    (-33.0100, -58.5170),
 "Parana":                          (-31.7327, -60.5290),
}
for k,(la,lo) in pts.items():
    print(f"  {k:35s} lat={la:9.4f} lon={lo:10.4f}")

print("\n=== DISTANCES FROM SANTA FE CAPITAL ===")
sf = pts["Santa Fe Capital (plaza/centro)"]
for k,(la,lo) in pts.items():
    if k.startswith("Santa Fe"): continue
    print(f"  SF -> {k:35s} {hav(*sf, la, lo):8.1f} km")

print("\n=== DEGREE->KM AT KEY LATITUDES ===")
for la in (-31.6, -32.9, -33.9, -34.6):
    print(f"  lat {la:6.2f}: 1 deg lat = {km_per_deg_lat(la):7.3f} km | 1 deg lon = {km_per_deg_lon(la):7.3f} km")
