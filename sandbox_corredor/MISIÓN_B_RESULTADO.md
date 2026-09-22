# Resultado — Misión B (ejecución real)

**Fecha:** 2026-09-22 18:21-18:23
**Ejecutado por:** Shell (bash sandbox_corredor/run_mision_b.sh)
**Orquestado por:** Director (Iván)
**Estado:** EXITOSO

## Comparación estimado vs real

| Paso     | Estimado DSH     | Real    | Desvío |
|----------|------------------|---------|--------|
| Extract  | 70 MB (53-90)    | 75 MB   | OK     |
| Filtrado | 25 MB (15-40)    | 32 MB   | OK     |
| GeoJSON  | 180 MB (120-300) | 222 MB  | OK     |
| MBTiles  | 60 MB (40-110)   | 100 MB  | OK     |

Las 4 estimaciones cayeron dentro del rango previsto.

## MBTiles final

- Archivo: corredor_sf_caba.mbtiles
- Tamaño: 100 MB
- Tiles totales: 43.394
- Zoom 8: 37 tiles
- Zoom 9: 95 tiles
- Zoom 10: 259 tiles
- Zoom 11: 757 tiles
- Zoom 12: 2.463 tiles
- Zoom 13: 8.586 tiles
- Zoom 14: 31.197 tiles
- SHA256: 4d069e7b89b8f212fa434329d58a4fdae804eb9a79b5a720f667043d88ec0d1d

## Error encontrado y corregido

DSH propuso `-L corredor` (mayúscula) en el comando tippecanoe.
Tippecanoe 2.79 cambio el significado de `-L`: ahora espera
formato `layername:file`. La opción correcta es `-l` (minúscula).

Detectado en ejecucion. Corregido con sed. Re-ejecutado paso 4.

Leccion: DSH debe verificar version exacta de herramientas antes
de proponer flags. Las opciones cambian entre versiones.

## Archivos producidos

- corredor_sf_caba.osm.pbf        (75 MB)  — extract intermedio
- corredor_sf_caba_filtrado.osm.pbf (32 MB)  — filtrado de tags
- corredor_sf_caba.geojsonseq      (222 MB) — intermedio para tippecanoe
- corredor_sf_caba.mbtiles         (100 MB) — producto final
- mision_b.log                     (1,3 KB) — log de ejecucion

Total en disco: ~428 MB (se puede borrar los intermedios si hace falta).

## Verificaciones

- Hash del backup verificado OK antes de ejecutar.
- Nada se escribio fuera del sandbox.
- Backup original intacto.
- HEAD del repo sin cambios por la ejecucion.
