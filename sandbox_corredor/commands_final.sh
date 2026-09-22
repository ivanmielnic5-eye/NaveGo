#!/usr/bin/env bash
# =============================================================================
# commands_final.sh — Comandos EXACTOS para la MISION B
# Corredor Santa Fe Capital -> CABA (eje RN9)
# =============================================================================
#
#   *** ESTE SCRIPT NO SE EJECUTA EN LA MISION A ***
#
# La mision A es SOLO preparacion. Estos comandos quedan listos para que el
# Director los autorice y se ejecuten en una mision B posterior.
#
# PARA EJECUTAR EN MISION B:
#   1. Revisar que el hash del backup siga siendo el esperado (PASO 0).
#   2. Descomentar el bloque de ejecucion o correr comando por comando.
#   3. Verificar el tamano de cada salida contra size_estimates.csv.
#
# Herramientas verificadas: osmium 1.19.0, tippecanoe 2.79.0
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# CONFIGURACION (rutas)
# ---------------------------------------------------------------------------
SRC_PBF="$HOME/cockpit/backup_mapa/argentina-260901.osm.pbf"
SRC_SHA256="d43f9af1a293f822fb23da570d7cb44d022b1943e73c79fcd6b87b190b5c504f"

OUTDIR="$HOME/navego_recuperado/sandbox_corredor/out_mision_b"
EXTRACT_PBF="$OUTDIR/corredor_sf_caba.osm.pbf"
FILTERED_PBF="$OUTDIR/corredor_sf_caba_filtrado.osm.pbf"
CORREDOR_GEOJSON="$OUTDIR/corredor_sf_caba.geojson"
MBTILES="$OUTDIR/corredor_sf_caba.mbtiles"

# BBOX DEFINITIVO (calculado en mision A, ver corridor_final.json)
# Orden osmium: LEFT(min_lon),BOTTOM(min_lat),RIGHT(max_lon),TOP(max_lat)
BBOX="-61.5439126,-34.7892201,-57.8418874,-31.4390329"

# ---------------------------------------------------------------------------
# PASO 0 — VERIFICACION DE INTEGRIDAD DEL BACKUP (obligatorio antes de todo)
# ---------------------------------------------------------------------------
# Por que: el PBF hermano (argentina-latest.osm.pbf) esta TRUNCADO y sin ways.
# Si el hash no coincide, ABORTAR: no hay que generar cartografia desde una
# fuente dudosa.
#
#   echo "$SRC_SHA256  $SRC_PBF" | sha256sum -c -
#
# Salida esperada: "argentina-260901.osm.pbf: OK"

# ---------------------------------------------------------------------------
# PASO 1 — EXTRACCION DEL BBOX
# ---------------------------------------------------------------------------
# osmium extract recorta el PBF al rectangulo del corredor.
#
#   -b / --bbox           LEFT,BOTTOM,RIGHT,TOP  (lon_min,lat_min,lon_max,lat_max)
#   -s complete_ways      (DEFAULT) Incluye TODOS los nodos de cada way que
#                         toca el bbox, aunque algunos nodos queden fuera.
#                         Es lo correcto para ruteo: sin esto, las rutas que
#                         cruzan el borde quedan cortadas.
#   -S detect_changes=... NO se usa (el backup no es historia).
#   --set-bounds          Reescribe el bbox del header al del extract.
#                         Util para que herramientas posteriores sepan el
#                         alcance real del archivo.
#   -O                    Sobrescribe la salida si existe.
#   -f pbf                Formato de salida PBF (comprimido).
#
# OJO: el default de osmium es PBF con compresion. El paso 1 conserva
#      absolutamente todo lo que cae en el bbox (todos los tags, POIs,
#      buildings, landuse). El filtrado es el PASO 2.
#
#   osmium extract \
#     --bbox="$BBOX" \
#     --strategy=complete_ways \
#     --set-bounds \
#     --overwrite \
#     --output="$EXTRACT_PBF" \
#     --output-format=pbf \
#     "$SRC_PBF"

# ---------------------------------------------------------------------------
# PASO 1b — (OPCIONAL) EXTRACCION CON ESTRATEGIA SIMPLE
# ---------------------------------------------------------------------------
# Alternativa mas liviana: 'simple' NO arrastra nodos fuera del bbox.
# Ventaja: archivo mas chico. Desventaja: las ways que cruzan el borde
# quedan truncadas en el limite. Para navegacion dentro del corredor es
# aceptable; para ruteo que salga del corredor, NO.
#
#   osmium extract \
#     --bbox="$BBOX" \
#     --strategy=simple \
#     --set-bounds --overwrite \
#     --output="${EXTRACT_PBF%.osm.pbf}_simple.osm.pbf" \
#     "$SRC_PBF"

# ---------------------------------------------------------------------------
# PASO 2 — FILTRADO DE TAGS
# ---------------------------------------------------------------------------
# Por que filtrar: el extract completo trae buildings, landuse, natural,
# boundaries, etc. Para un mapa de navegacion vial no hacen falta y
# multiplican el tamano del GeoJSON y del MBTiles.
#
# El archivo de expresiones (corridor_tags.txt) se lista mas abajo y se
# escribe con el heredoc del PASO 2a.
#
# osmium tags-filter:
#   -e/--expressions=FILE  archivo con las expresiones (una por linea)
#   -R/--omit-referenced   NO incluir nodos referenciados por ways que no
#                          matchean. Reduce tamano. CUIDADO: puede romper
#                          geometrias si se combina mal. Para este caso,
#                          probar SIN -R primero (mas seguro).
#   -O                     sobrescribir
#
# ---------------------------------------------------------------------------
# PASO 2a — ESCRIBIR EL ARCHIVO DE EXPRESIONES
# ---------------------------------------------------------------------------
# Sintaxis osmium:  PREFIX/KEY=VALUE  o  PREFIX/KEY  (cualquier valor)
#   n = nodos, w = ways, r = relations, a = areas, nwr = los tres
#
#   cat > "$OUTDIR/corridor_tags.txt" <<'EOF'
#   # --- RED VIAL (todos los tipos, necesarios para render y ruteo) ---
#   w/highway
#   w/highway=motorway
#   w/highway=trunk
#   w/highway=primary
#   w/highway=secondary
#   w/highway=tertiary
#   w/highway=unclassified
#   w/highway=residential
#   w/highway=service
#   w/highway=motorway_link
#   w/highway=trunk_link
#   w/highway=primary_link
#   w/highway=secondary_link
#   w/highway=tertiary_link
#   w/highway=living_street
#   w/highway=track
#   # --- JERARQUIA DE RUTAS (para etiquetas tipo "RN9") ---
#   w/ref
#   w/route
#   r/route=road
#   r/type=route
#   r/network
#   # --- LUGARES Y POBLADOS (etiquetas y busqueda) ---
#   n/place
#   w/place
#   r/place
#   n/place=city
#   n/place=town
#   n/place=village
#   n/place=hamlet
#   # --- SERVICIOS PARA VIAJE (combustible, salud, descanso) ---
#   n/amenity=fuel
#   n/amenity=hospital
#   n/amenity=clinic
#   n/amenity=pharmacy
#   n/amenity=police
#   n/amenity=restaurant
#   n/amenity=cafe
#   n/amenity=fast_food
#   n/amenity=toilets
#   n/amenity=parking
#   n/amenity=rest_area
#   w/amenity=fuel
#   # --- ALOJAMIENTO ---
#   n/tourism=hotel
#   n/tourism=motel
#   n/tourism=camp_site
#   # --- TRANSPORTE ---
#   n/highway=bus_stop
#   n/railway=station
#   n/public_transport
#   # --- LIMITES ADMINISTRATIVOS (contexto) ---
#   r/boundary=administrative
#   # --- AGUA (referencia visual y navegacion) ---
#   w/waterway=river
#   w/waterway=stream
#   w/waterway=canal
#   w/natural=water
#   r/natural=water
#   # --- PEAJES Y BARRERAS (critico en ruta) ---
#   n/barrier=toll_booth
#   w/barrier=toll_booth
#   n/highway=motorway_junction
#   n/highway=traffic_signals
#   EOF
#
# ---------------------------------------------------------------------------
# PASO 2b — APLICAR EL FILTRO
# ---------------------------------------------------------------------------
#   osmium tags-filter \
#     --expressions="$OUTDIR/corridor_tags.txt" \
#     --overwrite \
#     --output="$FILTERED_PBF" \
#     --output-format=pbf \
#     "$EXTRACT_PBF"
#
# NOTA: se ejecuta SIN --omit-referenced a proposito, para no romper
#       geometrias de ways que comparten nodos. Si el tamano resulta
#       excesivo, reintentar agregando -R (medir diferencia antes).

# ---------------------------------------------------------------------------
# PASO 3 — CONVERSION A GEOJSON
# ---------------------------------------------------------------------------
# tippecanoe NO lee PBF directamente: necesita GeoJSON (o GeoJSONSeq).
# Ese es el motivo de este paso.
#
# osmium export:
#   -f geojson            FeatureCollection (un solo objeto JSON)
#   -f geojsonseq         una Feature por linea (RECOMENDADO para archivos
#                         grandes: permite streaming y evita cargar todo en
#                         memoria). tippecanoe lee ambos.
#   --add-unique-id=counter  Asigna un id numerico unico a cada feature.
#                         Necesario porque muchos objetos OSM no tienen id
#                         propio y tippecanoe lo requiere para el deduplicado.
#   -x print_record_separator=false  (solo geojsonseq) evita el separador
#                         RS (0x1e) que algunos consumidores no toleran.
#   --geometry-types      Limita tipos de geometria. Para navegacion:
#                         linestring para vias, point para POIs.
#                         NO limitar si se quieren poligonos de agua.
#
# OJO MEMORIA: con ~7.7M nodos en el bbox, el geojson puede superar los
# 500 MB. Usar geojsonseq y monitorear RAM/espacio en disco.
#
#   osmium export \
#     --output="$CORREDOR_GEOJSON" \
#     --output-format=geojsonseq \
#     --add-unique-id=counter \
#     --format-option=print_record_separator=false \
#     --overwrite \
#     "$FILTERED_PBF"
#
# Si se prefiere FeatureCollection clasico (un solo JSON):
#   osmium export \
#     --output="$CORREDOR_GEOJSON" \
#     --output-format=geojson \
#     --add-unique-id=counter \
#     --overwrite \
#     "$FILTERED_PBF"

# ---------------------------------------------------------------------------
# PASO 4 — GENERACION DE MBTILES
# ---------------------------------------------------------------------------
# Parametros COPIADOS de la referencia real que funciono en este proyecto
# (santa_fe.mbtiles, 121 MB, generado por tippecanoe v2.79.0). Se mantienen
# identicos para no introducir variables nuevas.
#
#   -o                    archivo de salida
#   -Z8                   zoom minimo 8
#   -z14                  zoom maximo 14
#   --drop-densest-as-needed
#                         Si un tile supera el limite de tamano, descarta
#                         features de menor importancia (densest) en vez de
#                         fallar. Clave para zonas urbanas (Rosario, AMBA).
#   --extend-zooms-if-still-dropping
#                         Si aun asi no entra, agrega zooms adicionales.
#   --force               Sobrescribe la salida existente.
#
#   -L corredor           Nombre de la capa vectorial ("corredor").
#                         Si se omite, tippecanoe deduce el nombre del
#                         archivo. Conviene fijarlo para que la app lo
#                         referencie de forma estable.
#   -n "Corredor SF-CABA" Nombre legible en metadatos.
#
# RECOMENDACION: para un corredor largo conviene separar capas por tipo, o
# al menos fijar -L. Version minima (identica a la referencia):
#
#   tippecanoe \
#     -o "$MBTILES" \
#     -Z8 -z14 \
#     --drop-densest-as-needed \
#     --extend-zooms-if-still-dropping \
#     --force \
#     "$CORREDOR_GEOJSON"
#
# Version con nombre de capa explicito:
#
#   tippecanoe \
#     -o "$MBTILES" \
#     -Z8 -z14 \
#     -L corredor \
#     -n "Corredor Santa Fe - CABA (RN9)" \
#     --drop-densest-as-needed \
#     --extend-zooms-if-still-dropping \
#     --force \
#     "$CORREDOR_GEOJSON"

# ---------------------------------------------------------------------------
# PASO 5 — VERIFICACION DE LA SALIDA (post-ejecucion, mision B)
# ---------------------------------------------------------------------------
# Comparar el MBTiles real contra size_estimates.csv. Si difiere mas del
# 50% de la estimacion, DETENER y reportar: significa que un supuesto
# de la mision A era incorrecto.
#
#   ls -la "$EXTRACT_PBF" "$FILTERED_PBF" "$CORREDOR_GEOJSON" "$MBTILES"
#   du -h "$MBTILES"
#   tippecanoe-decode --stats "$MBTILES"
#   sqlite3 "$MBTILES" "select zoom_level,count(*) from tiles group by zoom_level;"

# =============================================================================
# FIN — Ningun comando de este archivo se ejecuto en la mision A.
# =============================================================================
echo "commands_final.sh: SOLO LECTURA. Este script NO se ejecuta en mision A."
echo "Todos los comandos estan comentados a proposito."
exit 0
