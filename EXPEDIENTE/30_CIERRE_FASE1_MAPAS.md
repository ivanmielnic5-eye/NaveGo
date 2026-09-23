# EXPEDIENTE 30 — Cierre Fase 1 Mapas

**Fecha:** 2026-09-23
**Commit:** 89a19f3 (main)
**Rama:** main

## Estado al cierre

Fase 1 de mapas cerrada. El corredor dejó de ser un rectángulo (bbox)
y pasó a ser un polígono derivado del río.

| Artefacto | Estado |
|---|---|
| corredor_buffer.geojson | OK, 279 vértices, ratio 60.55% |
| corredor_sf_caba.mbtiles | OK, 61 MB, z5-z14, 0 tiles >500KB |
| manifest.json | Validado contra schema |
| Pipeline (7 scripts) | Versionado en git |
| agent_fsm.py + audit_log.json | Fuera del commit (otra sesión) |

## Métricas finales

| Métrica | Valor |
|---|---|
| PBF origen (Argentina) | 470 MB |
| PBF recortado al bbox | 74 MB |
| PBF filtrado | 32 MB |
| GeoJSON completo | 725 MB |
| GeoJSON filtrado | 179 MB |
| MBTiles final | 61 MB |
| Features capturadas | 483.530 |
| Radares | 412 |
| Peajes | 138 |
| Rutas con toll=yes | 737 |
| Vértices del buffer | 279 |
| Ratio geom/bbox | 60.55% |
| Tiles >500KB | 0 |
| Tiempo de buffer | 1.2 s |

## Decisiones arquitectónicas

### 1. Buffer sobre río, NO bbox
Se extrae waterway=river + canal de OSM, se proyecta a UTM 20S
(EPSG:32720), buffer de 25 km en metros, reproyección a WGS84.
Resultado: forma de río, no de caja. CABA cae cerca del límite
UTM 20S/21S pero la distorsión es <1% a esta escala.

### 2. Map Region Package (MRP)
manifest.json (contrato) + tiles.mbtiles (datos). El manifest declara
cobertura, bbox real, capas, zoom range, tamaño, checksum, versión
del source OSM y política de deduplicación.

### 3. Duplicación aceptada en v1
Si el usuario tiene Santa Fe + Corredor, los tiles superpuestos viven
dos veces. Manifest preparado con deduplication_strategy:
none_v1_future_tile_hash para migrar sin romper el contrato.

### 4. Pipeline separado de la app
App Android solo lee MBTiles + manifest. Sin cargador universal hasta
que haya un segundo caso real de uso.

### 5. Filtrado agresivo antes de Tippecanoe
Solo features relevantes: highway, waterway, natural=water, water,
place, boundary=administrative, highway=speed_camera,
enforcement=speed_camera, barrier=toll_booth, toll=yes.

## Pipeline reproducible

### Recorte PBF
osmium extract -b -60.8,-34.8,-58.3,-31.5 backup_mapa/argentina-260902-internal.osm.pbf -o corredor_region.osm.pbf --overwrite

### Filtro features relevantes
osmium tags-filter corredor_region.osm.pbf w/highway w/waterway w/natural=water w/water w/toll=yes a/natural=water n/place n/highway=speed_camera n/enforcement=speed_camera n/barrier=toll_booth n/highway=toll_booth r/boundary=administrative -o corredor_relevante.osm.pbf --overwrite

### Agua para buffer
osmium tags-filter corredor_region.osm.pbf w/waterway=river,canal -o agua_filtrada.osm.pbf --overwrite
osmium export agua_filtrada.osm.pbf -o agua.geojson --overwrite

### Buffer
python3 buffer_river.py
python3 validate_buffer.py corredor_buffer.geojson

### MBTiles
tippecanoe -o corredor_sf_caba.mbtiles -Z5 -z14 -S 10 --detect-shared-borders --coalesce-densest-as-needed --drop-densest-as-needed --force --no-progress-indicator corredor_relevante.geojson

### Validación
python3 update_manifest.py
python3 validate_manifest.py manifest.json

## Aprendizajes técnicos

### Shapely 2.x cambia el juego
unary_union sobre 3664 líneas crudas produjo OOM a 4 GB y proceso
muerto. union_all (Shapely 2.x) + simplify(100m) por línea antes de
unir dio 1.2 segundos. No volver a unary_union en geometrías grandes.

### Simplificar antes de bufferear es invisible
100 m de tolerancia sobre un buffer de 25 km es <0.4% del radio.
Reduce vértices >90% sin degradar el resultado visual.

### Filtrar antes de Tippecanoe es obligatorio
Sin filtro: 725 MB GeoJSON, 123 MB MBTiles, drops masivos.
Con filtro: 179 MB, 61 MB, 0 drops.

### Schema con additionalProperties:false es estricto
Obliga a mantener el schema actualizado. Campos ad-hoc no se pueden
agregar sin tocar el schema.

### Flags de Tippecanoe que importan
-S 10: simplificación de vértices (no --coalesce-densest-as-needed,
que es control de tamaño de tile, no de simplificación geométrica).
--detect-shared-borders: evita que fronteras compartidas se abran
al simplificar.
-Z5 -z14: rango de zoom del paquete.

### Bbox del artefacto real, no del teórico
Buffer teórico: lon[-61.68, -57.20]. MBTiles real: lon[-61.10, -57.94].
Usar el del MBTiles. Si no, la app pide tiles que no existen y
aparecen huecos negros.

## Deuda técnica

### Crítica
1. Split de capas: MBTiles tiene 1 capa (corredor_relevante), no las
   6 planeadas. Fase 2 debe separar en: roads, water, waterway,
   places, admin_province, navigation_context.

### Importante
2. Render real en app: verificar z5-z14 sin huecos.
3. Segundo paquete: santa_fe.mbtiles con mismo pipeline para validar
   coexistencia.

### Diferible
4. Deduplicación por tile hash cuando haya 2+ paquetes.
5. Buffer adaptativo (hoy constante 25 km).
6. CRS parametrizable por región.

## Cómo retomar mañana

1. Leer este archivo.
2. cd /home/ivan/workspace && source .venv/bin/activate
3. git log --oneline -3 → confirmar 89a19f3.
4. Verificar corredor_sf_caba.mbtiles en disco (61 MB).
5. Arrancar por split de capas o render en app.

## Archivos del commit 89a19f3

Agregados:
- buffer_river.py
- validate_buffer.py
- validate_manifest.py
- update_manifest.py
- fix_manifest.py
- fix_manifest_bbox.py
- manifest.json
- manifest.schema.json
- .gitignore

Generados (gitignored):
- corredor_region.osm.pbf (74 MB)
- corredor_relevante.osm.pbf (32 MB)
- corredor_relevante.geojson (179 MB)
- corredor_buffer.geojson (15 KB)
- corredor_sf_caba.mbtiles (61 MB)

---

Fase 1 cerrada. Fase 2 arranca con split de capas o render en app.
