"""
bbox_final.py — Calculo del bbox definitivo del corredor Santa Fe -> CABA.

Parametros fijados por el Director (NO se cuestionan aqui, solo se aplican):
  - Eje: RN9 (Santa Fe -> Rosario -> San Nicolas -> Zarate -> CABA)
  - Semiancho: 50 km a cada lado del eje
  - Margen adicional al norte de Santa Fe: 20 km
  - Margen adicional al sur de CABA: 20 km

Anclas (OBSERVADAS en el PBF, no asumidas):
  - Santa Fe: nodo 198423933  (-60.7019561, -31.6186951)
  - CABA:     nodo 81590481   (-58.3887904, -34.6095579)

Conversion geodesica (WGS84):
  - 1 grado de latitud  ~ 111.32 km (constante, meridiano)
  - 1 grado de longitud ~ 111.32 * cos(lat) km (varia con la latitud)
  El corredor va de lat -31.62 a -34.61. Se usa cos(lat) en el punto
  medio y tambien el cos del extremo mas desfavorable, para dar rango.
"""
import json
import math

# --- Anclas observadas en el PBF ---
SANTA_FE = (-60.7019561, -31.6186951)
CABA = (-58.3887904, -34.6095579)

# --- Parametros del Director ---
SEMIWIDTH_KM = 50.0
MARGIN_NORTH_KM = 20.0
MARGIN_SOUTH_KM = 20.0

KM_PER_DEG_LAT = 111.32


def deg_lon_per_km(lat_deg):
    """Cuantos grados de longitud hay en 1 km a esa latitud."""
    c = math.cos(math.radians(lat_deg))
    if c <= 0:
        raise ValueError("latitud invalida")
    return 1.0 / (KM_PER_DEG_LAT * c)


def build_bbox(axis_lon_west, axis_lon_east, lat_min, lat_max,
               semiwidth_km, margin_north_km, margin_south_km):
    """Construye el bbox envolvente.

    axis_lon_west/east: rango de longitud que ocupa el eje en el tramo.
    lat_min/lat_max: latitud de CABA y Santa Fe (extremos del eje).
    """
    # Margenes en latitud (norte = mas cerca de 0 = mayor lat)
    lat_top = lat_max + margin_north_km / KM_PER_DEG_LAT
    lat_bot = lat_min - margin_south_km / KM_PER_DEG_LAT

    # Semiancho en longitud: se evalua en la latitud mas desfavorable
    # (donde 1 grado de longitud es mas ancho => se necesitan menos grados;
    #  el peor caso para CUBRIR es la latitud mas alta, donde cos es mayor
    #  y por lo tanto cada km exige menos grados... el caso que MANDA es
    #  el cos mas grande, es decir la latitud mas cercana al ecuador).
    lat_cover = max(abs(lat_top), abs(lat_bot))

    # Expandir el eje hacia ambos lados por el semiancho.
    # Se calcula el semiancho en grados a la latitud de cobertura y a la
    # latitud de cada extremo; se toma el MAYOR (mas conservador).
    dl_cover = semiwidth_km * deg_lon_per_km(lat_cover)
    dl_north = semiwidth_km * deg_lon_per_km(lat_top)
    dl_south = semiwidth_km * deg_lon_per_km(lat_bot)
    dl = max(dl_cover, dl_north, dl_south)

    lon_min = axis_lon_west - dl
    lon_max = axis_lon_east + dl

    return {
        "min_lon": lon_min,
        "min_lat": lat_bot,
        "max_lon": lon_max,
        "max_lat": lat_top,
        "semiwidth_deg_lon": dl,
        "margin_north_deg_lat": margin_north_km / KM_PER_DEG_LAT,
        "margin_south_deg_lat": margin_south_km / KM_PER_DEG_LAT,
    }


def main():
    # --- Eje RN9 (litoral) en el tramo SF->CABA ---
    # Extremos del EJE (no del bbox):
    #  Norte: Santa Fe        (-60.7019561, -31.6186951)
    #  Sur:   CABA            (-58.3887904, -34.6095579)
    # El eje NO es una recta: tiene un quiebre en Rosario.
    # Rango de longitud que ocupa el eje completo (medido en el PBF):
    #   AP01 (SF->Rosario): lon -61.00 .. -60.71
    #   RN9  (Rosario->CABA): lon -61.18 .. -58.50  (incluye el tramo
    #        hacia Cordoba al oeste de Rosario, que NO es el eje, pero
    #        el eje litoral usa -60.58 .. -58.50)
    axis_lon_west = -60.9970   # AP01, tramo mas al oeste cerca de Rosario
    axis_lon_east = -58.3888   # CABA
    axis_lat_max = SANTA_FE[1]   # -31.6186951
    axis_lat_min = CABA[1]       # -34.6095579

    bb = build_bbox(axis_lon_west, axis_lon_east, axis_lat_min, axis_lat_max,
                    SEMIWIDTH_KM, MARGIN_NORTH_KM, MARGIN_SOUTH_KM)

    # --- Metricas ---
    lat_span = bb["max_lat"] - bb["min_lat"]
    lon_span = bb["max_lon"] - bb["min_lon"]
    lat_mid = (bb["min_lat"] + bb["max_lat"]) / 2

    area_km2_approx = (lat_span * KM_PER_DEG_LAT) * \
                      (lon_span * KM_PER_DEG_LAT * math.cos(math.radians(lat_mid)))

    # Verificacion: ¿cae Santa Fe y CABA dentro?
    def inside(lon, lat):
        return (bb["min_lon"] <= lon <= bb["max_lon"] and
                bb["min_lat"] <= lat <= bb["max_lat"])

    result = {
        "bbox": {
            "min_lon": round(bb["min_lon"], 7),
            "min_lat": round(bb["min_lat"], 7),
            "max_lon": round(bb["max_lon"], 7),
            "max_lat": round(bb["max_lat"], 7),
        },
        "params": {
            "semiwidth_km": SEMIWIDTH_KM,
            "margin_north_km": MARGIN_NORTH_KM,
            "margin_south_km": MARGIN_SOUTH_KM,
            "km_per_deg_lat": KM_PER_DEG_LAT,
        },
        "anchors": {
            "santa_fe": {"lon": SANTA_FE[0], "lat": SANTA_FE[1],
                          "osm_node": 198423933,
                          "source": "place=city, population=404910"},
            "caba": {"lon": CABA[0], "lat": CABA[1],
                      "osm_node": 81590481,
                      "source": "place=city, official_name=CABA"},
        },
        "axis": {
            "lon_west": axis_lon_west,
            "lon_east": axis_lon_east,
            "lat_max": axis_lat_max,
            "lat_min": axis_lat_min,
        },
        "derived": {
            "semiwidth_deg_lon": round(bb["semiwidth_deg_lon"], 7),
            "margin_north_deg_lat": round(bb["margin_north_deg_lat"], 7),
            "margin_south_deg_lat": round(bb["margin_south_deg_lat"], 7),
            "lat_span_deg": round(lat_span, 6),
            "lon_span_deg": round(lon_span, 6),
            "lat_mid": round(lat_mid, 6),
            "approx_area_km2": round(area_km2_approx, 1),
        },
        "verification": {
            "santa_fe_inside": inside(*SANTA_FE),
            "caba_inside": inside(*CABA),
        },
    }

    with open("/home/ivan/navego_recuperado/sandbox_corredor/bbox_final.json",
              "w") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    b = result["bbox"]
    print("\n=== COMANDO osmium extract ===")
    print(f"--bbox={b['min_lon']},{b['min_lat']},{b['max_lon']},{b['max_lat']}")


if __name__ == "__main__":
    main()
