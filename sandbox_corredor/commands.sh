#!/usr/bin/env bash
# =============================================================================
# commands.sh — Comandos PROPUESTOS para la Etapa 3 (posterior)
# =============================================================================
#
#  *** NO EJECUTAR TODAVIA ***
#
#  Este archivo NO fue ejecutado. Es una PROPUESTA para revision humana.
#  Contiene osmium extract / tags-filter / tippecanoe: todo prohibido en la
#  tarea de analisis que produjo este archivo.
#
#  Generado por: IA (agente)
#  Proyecto: NAVEGO
#  Proposito: recorte de corredor Santa Fe -> CABA (viaje por AUTO)
#
#  ---------------------------------------------------------------------------
#  ANTES DE EJECUTAR — LEER ESTO
#  ---------------------------------------------------------------------------
#  El PBF indicado en la consigna (~/cockpit/argentina-latest.osm.pbf) esta
#  TRUNCADO: no contiene ways ni relations. NO SIRVE para generar cartografia.
#  Este script apunta al BACKUP INTEGRO. Verificar antes de usarlo.
#
#  Decisiones humanas pendientes (NO resueltas por la IA):
#    D1. Confirmar que se usa el backup y no re-descargar el objetivo.
#    D2. Elegir semiancho: 20 / 50 / 90 km.
#    D3. Elegir eje principal: RN 9 o RN 11.
#    D4. Elegir zooms y presupuesto de tamano.
#  ---------------------------------------------------------------------------
#
#  USO PREVISTO:
#     chmod +x commands.sh      # no ejecutar aun
#     # ... luego de la aprobacion, editar las variables de configuracion ...
#
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# CONFIGURACION
# -----------------------------------------------------------------------------

# PBF de ENTRADA.
# OJO: el archivo de la consigna esta truncado. Se usa el backup integro.
# El Director debe confirmar esta sustitucion (decision D1).
PBF_IN="/home/ivan/cockpit/backup_mapa/argentina-260901.osm.pbf"

# (Referencia del archivo NO utilizable, dejado para trazabilidad)
# PBF_TRUNCADO="/home/ivan/cockpit/argentina-latest.osm.pbf"
#   sha256 = 0a979a3da11d64ab871b177ca322e200fe9785c8741bbff8c09a985e689686e4
#   257.252.921 bytes | sin ways ni relations

# Directorio de trabajo de la etapa posterior
WORKDIR="/home/ivan/navego_recuperado/sandbox_corredor/etapa3"
mkdir -p "$WORKDIR"

# Bounding box del candidato elegido.
# Por defecto se deja el C2 (semiancho 50 km) porque es la hipotesis de trabajo.
# Formato osmium: minlon,minlat,maxlon,maxlat
BBOX_C1="-60.915343,-34.784032,-58.163557,-31.430368"   # 20 km
BBOX_C2="-61.242408,-35.054531,-57.836492,-31.159869"   # 50 km  <-- hipotesis
BBOX_C3="-61.678494,-35.415195,-57.400406,-30.799205"   # 90 km
BBOX="$BBOX_C2"                                          # <-- EDITAR si el Director elige otro

# Eje de referencia para el corte por linea (estrategia alternativa, ver PASO 2B)
AXIS_SF_CABA="60.6973,-31.6107,58.3816,-34.6037"        # lon,lat,lon,lat (SF -> CABA)
AXIS_HALF_WIDTH_KM=50

echo "=== NAVEGO / Etapa 3 - recorte de corredor ==="
echo "PBF_IN : $PBF_IN"
echo "WORKDIR: $WORKDIR"
echo "BBOX   : $BBOX"
echo

# =============================================================================
# PASO 0 — PREFLIGHT: verificar que la entrada es valida
# =============================================================================
# POR QUE: antes de gastar tiempo en un extract, confirmar que el PBF lee
# completo. El archivo de la consigna fallaba aqui con "unexpected EOF".

echo "[0] Verificando integridad del PBF de entrada..."
osmium fileinfo -e "$PBF_IN"
# Esperado: sin "PBF error", con conteos de nodes/ways/relations.
# Si aparece "unexpected EOF" -> STOP. No continuar.

echo "[0b] Hash de la entrada (para trazabilidad)..."
sha256sum "$PBF_IN"

# =============================================================================
# PASO 1 — RECORTE DEL CORREDOR  (osmium extract)
# =============================================================================
# POR QUE: reducir 428 MB a una franja manejable alrededor del eje del viaje.
# osmium extract con --bbox conserva los objetos que tocan la caja; con
# --strategy complete_ways asegura que las ways que cruzan el borde queden
# enteras (importante: una way cortada rompe el ruteo).

echo "[1] Extrayendo corredor por bbox..."
osmium extract \
  --bbox "$BBOX" \
  --strategy complete_ways \
  --with-history=false \
  --overwrite \
  --output "$WORKDIR/corridor_raw.osm.pbf" \
  "$PBF_IN"

# NOTA: ~50 km de semiancho captura tanto RN9 como RN11 en el tramo sur,
# de modo que la alternativa quede dentro del recorte.

# =============================================================================
# PASO 2 — (ALTERNATIVA a PASO 1) RECORTE POR POLIGONO/LINEA DEL EJE
# =============================================================================
# POR QUE: si se prefiere una franja "siguiendo la ruta" en vez de una caja
# rectangular, se puede recortar con un poligono. Requiere un GeoJSON del eje,
# que NO existe todavia (el corredor.geojson hallado esta vacio).
#
# osmium extract --polygon "$WORKDIR/axis_buffer.geojson" \
#   --strategy complete_ways \
#   --output "$WORKDIR/corridor_axis.osm.pbf" \
#   "$PBF_IN"
#
# El buffer de 50 km sobre el eje SF->CABA deberia generarse con una herramienta
# GIS (ogrinfo/qgis) o construirse a mano. NO se genero en esta tarea.

# =============================================================================
# PASO 3 — FILTRO DE TAGS RELEVANTES PARA NAVEGACION POR AUTO
# =============================================================================
# POR QUE: el recorte por bbox todavia trae edificios, landuse, hidrografia y
# ruido. El filtro conserva SOLO lo que sirve para conducir.
#
# Estrategia en dos filtros:
#   3A. Red vial + atributos de conduccion.
#   3B. POIs de seguridad y logistica.
# Luego se combinan (merge) en una sola capa.

echo "[3A] Filtrando red vial..."
osmium tags-filter \
  --overwrite \
  --output "$WORKDIR/roads.osm.pbf" \
  "$WORKDIR/corridor_raw.osm.pbf" \
  w/highway=motorway,motorway_link,trunk,trunk_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,unclassified,residential,service \
  w/oneway \
  w/maxspeed \
  w/bridge \
  w/tunnel \
  w/surface \
  w/ref \
  w/name

# Explicacion de cada grupo:
#   highway=*   -> la red por la que se circula (nucleo del mapa vial)
#   oneway      -> sentido de circulacion
#   maxspeed    -> limites de velocidad (ETA)
#   bridge      -> puentes (pasos criticos)
#   tunnel      -> tuneles (pasos criticos)
#   surface     -> pavimento vs tierra (transitabilidad)
#   ref/name    -> etiquetas visibles ("RN 9", "Autopista Rosario-Bs.As.")

echo "[3B] Filtrando POIs de seguridad y logistica..."
osmium tags-filter \
  --overwrite \
  --output "$WORKDIR/pois.osm.pbf" \
  "$WORKDIR/corridor_raw.osm.pbf" \
  n/place=city,town,village \
  n/amenity=fuel \
  n/amenity=hospital \
  n/amenity=police \
  n/amenity=restaurant,fast_food \
  n/amenity=pharmacy \
  n/highway=rest_area,services \
  n/shop=supermarket \
  n/tourism=hotel,motel

# Explicacion:
#   place=*        -> localidades (referencia humana y de ruteo)
#   amenity=fuel   -> estaciones de servicio (critico en ruta)
#   amenity=hospital -> seguridad del viaje
#   amenity=police -> seguridad
#   restaurant/fast_food, supermarket, hotel/motel -> logistica de viaje
#   highway=rest_area/services -> areas de descanso en autopista
#   pharmacy       -> apoyo basico

echo "[3C] Combinando red vial + POIs..."
osmium merge \
  --overwrite \
  --output "$WORKDIR/corridor_nav.osm.pbf" \
  "$WORKDIR/roads.osm.pbf" \
  "$WORKDIR/pois.osm.pbf"

# =============================================================================
# PASO 4 — PREPARACION ANTES DE TIPPECANOE
# =============================================================================
# POR QUE: tippecanoe lee mejor un GeoJSON/FlatGeobuf ordenado que un PBF crudo.
# Convertir el PBF filtrado a GeoJSON con geometrias resueltas.

echo "[4] Exportando a GeoJSON para tippecanoe..."
osmium export \
  --overwrite \
  --output "$WORKDIR/corridor_nav.geojsonseq" \
  --output-format geojsonseq \
  --add-unique-id=type_id \
  "$WORKDIR/corridor_nav.osm.pbf"

# Notas:
#   --add-unique-id=type_id -> da un id estable a cada feature (tippecanoe lo usa
#                              para deduplicar entre zooms).
#   geojsonseq (newline-delimited) -> mejor para streaming que un FeatureCollection.
#
# Opcional: conservar atributos utiles y descartar los que no se usan.
# osmium export --attributes=type,id,name,ref,highway,maxspeed,oneway,surface ...

# =============================================================================
# PASO 5 — GENERACION DE MBTILES (tippecanoe)
# =============================================================================
# POR QUE: NaveGo necesita un MBTiles offline para la prueba real.
# Parametros clave: zoom, simplificacion y limite de tamano.
#
# ADVERTENCIA: los valores de zoom y simplificacion son PROPUESTA, no medicion.
# Ajustar despues de medir el tamano real.

echo "[5] Generando MBTiles con tippecanoe..."

# --- Capa 1: red vial (lineas) ---
tippecanoe \
  --output-to-directory="$WORKDIR/tiles_roads" \
  --force \
  --layer=roads \
  --minimum-zoom=6 \
  --maximum-zoom=14 \
  --simplification=4 \
  --simplify-only-low-zooms \
  --no-simplification-of-shared-nodes \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --attribution="© OpenStreetMap contributors" \
  "$WORKDIR/corridor_nav.geojsonseq"

# Explicacion de parametros:
#   --layer=roads              -> nombre de capa visible desde la app
#   --minimum-zoom=6           -> vista provincial/pais
#   --maximum-zoom=14          -> detalle de calle en ciudad
#   --simplification=4         -> tolerancia en unidades de tile (balance detalle/tamano)
#   --simplify-only-low-zooms  -> no degradar el detalle en zoom alto
#   --no-simplification-of-shared-nodes -> evita romper la topologia de la red
#                                 (importante para ruteo, no solo dibujo)
#   --drop-densest-as-needed   -> control de tamano automatico en zonas densas
#   --extend-zooms-if-still-dropping -> garantiza que el zoom maximo tenga datos
#   --attribution              -> atribucion OSM (obligatoria)
#
# Nota: se genera a DIRECTORIO primero (inspeccionable). El MBTiles final se
# arma despues con tile-join, para poder medir por capa antes de empaquetar.

# --- Capa 2: POIs (puntos) ---
# tippecanoe \
#   --output-to-directory="$WORKDIR/tiles_pois" \
#   --force \
#   --layer=pois \
#   --minimum-zoom=10 \
#   --maximum-zoom=14 \
#   --drop-densest-as-needed \
#   --attribution="© OpenStreetMap contributors" \
#   "$WORKDIR/corridor_nav.geojsonseq"

# =============================================================================
# PASO 6 — EMPAQUETADO FINAL Y MEDICION
# =============================================================================
# POR QUE: unir capas en un solo MBTiles y MEDIR el tamano real.
# Este numero reemplaza la estimacion de size_estimates.csv.

echo "[6] Empaquetando y midiendo..."
# tile-join \
#   --output="$WORKDIR/navego_corridor.mbtiles" \
#   --force \
#   "$WORKDIR/tiles_roads" \
#   "$WORKDIR/tiles_pois"

# ls -la "$WORKDIR/navego_corridor.mbtiles"
# du -h --max-depth=1 "$WORKDIR" | sort -h

# =============================================================================
# PASO 7 — VERIFICACION POST-GENERACION (obligatoria)
# =============================================================================
# POR QUE: no afirmar exito sin evidencia.

echo "[7] Verificando el resultado..."
# osmium fileinfo -e "$WORKDIR/corridor_raw.osm.pbf"
# sqlite3 "$WORKDIR/navego_corridor.mbtiles" "SELECT zoom_level, count(*) FROM tiles GROUP BY zoom_level;"
# sqlite3 "$WORKDIR/navego_corridor.mbtiles" "SELECT * FROM metadata;"

# =============================================================================
# FIN — RECORDATORIO
# =============================================================================
# Este script NO fue ejecutado por la IA.
# La IA propone; el Director decide y ejecuta.
# Antes de correrlo: resolver D1-D4 y validar el PASO 0.
