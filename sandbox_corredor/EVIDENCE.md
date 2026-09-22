# EVIDENCE.md — Registro de evidencia del análisis

**Proyecto:** NAVEGO
**Tarea:** Caracterizar el PBF de Argentina y proponer candidatos de corredor
**Fecha:** 2026-09-22
**Modo:** solo lectura / análisis. Sin extracción, sin tippecanoe, sin MBTiles.
**Autor:** IA (agente). La IA produce evidencia; el Director decide.

---

## 1. Entorno verificado

| Herramienta | Versión | Fuente |
|---|---|---|
| osmium | 1.19.0 (libosmium 2.23.1) | `osmium --version` |
| tippecanoe | v2.79.0 | `tippecanoe --version` |
| python3 | 3.14.7 | `python3 --version` |
| sha256sum | coreutils | `which sha256sum` |

Compresión PBF soportada por osmium: none, zlib, lz4.

---

## 2. Archivos inspeccionados

| Ruta | Tamaño (bytes) | Estado | Evidencia |
|---|---|---|---|
| `~/cockpit/argentina-latest.osm.pbf` | 257.252.921 | **TRUNCADO** | `osmium fileinfo -e` -> EOF |
| `~/cockpit/backup_mapa/argentina-260901.osm.pbf` | 428.645.479 | **ÍNTEGRO** | `osmium fileinfo -e` -> OK |
| `~/cockpit/backup_mapa/argentina-260902-internal.osm.pbf` | 470.698.521 | no analizado | solo `ls`/hash |
| `~/cockpit/backup_mapa/argentina-internal.osh.pbf` | 908.544.266 | no analizado | solo `ls`/hash |
| `~/cockpit/backup_mapa/uruguay-260901.osm.pbf` | 56.094.813 | fuera de scope | solo `ls`/hash |
| `~/cockpit/santa-fe.osm.pbf` | 9.609 | **INVÁLIDO** | `invalid BlobHeader size` |
| `~/cockpit/backup_mapa/corredor.geojson` | 45 | **VACÍO** | `features: []` |

**Discrepancia de ruta:** la consigna indicaba el PBF en
`~/cockpit/argentina-latest.osm.pbf`. **Confirmado**: existe ahí.
**No** existe copia en `~/navego_recuperado/` (verificado con `stat`).

**Discrepancia de tamaño:** la consigna decía "246 MB aprox". El archivo mide
257.252.921 bytes = **245,3 MiB** = 257,3 MB decimales. Es diferencia de
unidades, no de contenido. **No es una contradicción real.**

---

## 3. Comandos de lectura utilizados

Todos de **solo lectura**. Ninguno modifica el PBF.

### 3.1 Inspección básica

```bash
stat -c '%n %s bytes' ~/cockpit/argentina-latest.osm.pbf
ls -la ~/cockpit/ ~/cockpit/backup_mapa/
df -h ~/cockpit ~/navego_recuperado
sha256sum ~/cockpit/argentina-latest.osm.pbf
osmium fileinfo ~/cockpit/argentina-latest.osm.pbf        # solo header -> exit 0
osmium fileinfo -e ~/cockpit/argentina-latest.osm.pbf     # escaneo total -> exit 1
osmium fileinfo -e ~/cockpit/backup_mapa/argentina-260901.osm.pbf  # -> exit 0
osmium cat -f opl ~/cockpit/argentina-latest.osm.pbf      # -> exit 1 (EOF)
```

### 3.2 Scripts de análisis propios (escritos en el sandbox)

| Script | Propósito | Salida clave |
|---|---|---|
| `probe_truncation.py` | Recorre el framing de blobs sin descomprimir | Corte en byte 257.238.148, faltan 9.409 |
| `probe_content.py` | Descomprime blobs y lee PrimitiveGroup | 49.912.000 nodos, **0 ways, 0 relations** |
| `probe_corridor_nodes.py` | Cuenta nodos dentro del bbox del corredor | **8.830.270 nodos** en el corredor |
| `find_boundary.py` | Localiza el inicio de las ways en el backup | Offset 297.679.654 |
| `geo_analysis.py` | Haversine y conversión grados->km | Distancias y factores |
| `bbox_calc.py` | Geometría de los candidatos | bbox C1/C2/C3 |
| `diag.py` | Diagnóstico de decodificación de nodos | Detectó el bug de field numbers |

Todos escriben **solo a stdout**. No modifican archivos de entrada.

---

## 4. Información obtenida

### 4.1 Hash del PBF objetivo (evidencia observada)

```
sha256 = 0a979a3da11d64ab871b177ca322e200fe9785c8741bbff8c09a985e689686e4
size   = 257.252.921 bytes
```

### 4.2 Header del PBF objetivo (legible y válido)

```
Format: PBF
Compression: none
Bounding boxes: (-73.614525,-55.682956,-53.63534,-21.725753)
generator=osmium/1.16.0
osmosis_replication_base_url=https://download.geofabrik.de/south-america/argentina-updates
osmosis_replication_sequence_number=4900
osmosis_replication_timestamp=2026-09-01T20:20:50Z
sorting=Type_then_ID
```

### 4.3 Truncamiento (evidencia observada)

```
complete_blobs_read:    6,240
last_complete_blob_end: 257,238,148
file_size:              257,252,921
missing_bytes:          9,409
blob_types: {'OSMHeader': 1, 'OSMData': 6,239}

TRUNCATED_BLOB offset=257238148 type=OSMData datasize=24165
  need_end=257262330  file_size=257252921  missing=9409
```

### 4.4 Contenido del tramo legible (evidencia observada — CRÍTICO)

```
node:              49,912,000
dense_node_group:       6,239
way:                        0
relation:                   0

primer blob con node:     índice 1
primer blob con way:      None
primer blob con relation: None
```

Verificación sobre el último blob legible (índice 6239):
`primitive group field numbers present: [2]` (solo DenseNodes).
Los field `3` (ways) y `4` (relations) **no aparecen** en ningún blob legible.

### 4.5 Backup íntegro (evidencia observada)

```
File: ~/cockpit/backup_mapa/argentina-260901.osm.pbf
Size: 428,645,479
Bounding box: (-79.3652783,-61.1276558,-41.4427772,7.2535178)
Number of nodes:     59,348,185
Number of ways:       5,900,717
Number of relations:     88,563
Number of buffers:       84,942
CRC32: not calculated
```

**Header idéntico al objetivo** en bbox, timestamp de replicación (2026-09-01T20:20:50Z),
secuencia (4900) y generator (osmium/1.16.0).

### 4.6 Frontera nodos/ways en el backup íntegro (evidencia observada)

```
PRIMER blob con ways/relations: índice 7420, offset 297.679.654 (69,45% del archivo)
group field types: [3]   -> ways
```

**Implicación:** en un archivo íntegro, los nodos ocupan hasta el byte ~297,7 MB.
El objetivo se corta en 257,2 MB. Por lo tanto le faltan:
- ~40 MB de la **cola de nodos** (49,9M de 59,3M = 84,1%), y
- **131 MB completos de ways + relations**.

### 4.7 Nodos en el corredor (evidencia observada)

```
corridor_bbox_queried: (-62.5,-35.5,-57.5,-30.0)
NODES inside corridor: 8,830,270
corridor_nodes_actual_bbox: (-62.4999976,-35.4999968,-57.5000006,-30.0000004)
```

**Interpretación:** hay nodos, pero **sin ways no forman una red**. No permiten
rutear ni distinguir jerarquía vial.

### 4.8 Geografía del corredor (evidencia + cálculo)

Distancias haversine desde Santa Fe Capital (coordenadas documentadas):

| Destino | km |
|---|---|
| Rosario | 148,3 |
| San Nicolás | 196,9 |
| San Pedro | 249,4 |
| Pergamino | 253,7 |
| Zárate | 317,5 |
| Buenos Aires (CABA) | **396,6** |

Conversión a latitud media (-33,107):

```
1 grado latitud  ≈ 110,906 km
1 grado longitud ≈  93,339 km
```

### 4.9 Hashes de los backups (evidencia observada, prefijo 16 hex)

```
d43f9af1a293f822  argentina-260901.osm.pbf        428.645.479
fcbbf9f5108dd0e4  argentina-260902-internal.osm.pbf 470.698.521
966d490a66619867  argentina-internal.osh.pbf      908.544.266
bc141589f744a6ca  uruguay-260901.osm.pbf           56.094.813
3d45e3d9d7ee988c  santa-fe.osm.pbf                      9.609
```

---

## 5. Distinción evidencia / inferencia / propuesta

| Afirmación | Tipo |
|---|---|
| El PBF objetivo mide 257.252.921 bytes | **OBSERVADO** |
| Su sha256 es `0a979a3d...` | **OBSERVADO** |
| Falta el último blob (9.409 bytes) | **OBSERVADO** |
| El tramo legible tiene 0 ways y 0 relations | **OBSERVADO** |
| Contiene 49.912.000 nodos | **OBSERVADO** |
| El backup tiene 5.900.717 ways y 88.563 relations | **OBSERVADO** |
| Hay 8.830.270 nodos en el bbox del corredor | **OBSERVADO** |
| Objetivo y backup derivan del mismo snapshot | **INFERENCIA** (header idéntico) |
| El objetivo es una descarga incompleta | **INFERENCIA** |
| Las ways empiezan en el byte 297,7 MB del backup | **OBSERVADO** (medido) |
| RN 9 es el eje natural SF -> CABA | **INFERENCIA** (criterio geográfico) |
| La separación RN 9 / RN 11 es 40-60 km | **INFERENCIA** (por ciudades, NO medida) |
| El semiancho de 50 km es el mínimo útil | **PROPUESTA** |
| Los bbox C1/C2/C3 | **PROPUESTA** (derivados de coordenadas) |
| Los comandos de `commands.sh` | **PROPUESTA** (no ejecutados) |
| Los tamaños de MBTiles | **NO ESTIMABLE** con la evidencia actual |

---

## 6. Limitaciones metodológicas

1. **El PBF objetivo no permite caracterizar la red vial.** Es la limitación
   dominante: sin ways, todo lo vial es inferencia geográfica externa.
2. **No se analizó el contenido vial del backup íntegro.** Solo se validó que
   lee completo y se localizó la frontera nodos/ways. No se midió qué rutas
   cubre ni la densidad de POIs.
3. **La separación RN 9 / RN 11 no se midió.** Es un supuesto de criterio,
   no un dato.
4. **No se midió tamaño de MBTiles.** No se ejecutó tippecanoe.
5. **No se evaluó calidad de datos OSM** (completitud, errores de tagging).
6. **La aproximación por eje recto** entre ciudades no refleja la traza real de
   la ruta; los bbox son rectángulos, no franjas siguiendo el camino.
7. **No se analizaron** los otros dos backups (`internal`, `osh`) ni el de Uruguay.
8. **Los cálculos de distancia usan haversine** sobre coordenadas de centro de
   ciudad; no son distancias de ruta por carretera.

---

## 7. Errores propios detectados y corregidos

Registrados por transparencia y reproducibilidad.

### Error 1 — `BlobHeader` field number

Usé `datasize = field 2`. El campo correcto es **field 3**.
Corregido tras inspeccionar los bytes del header (`0a 09 "OSMHeader" 18 b9 01`).

### Error 2 — `DenseNodes` field numbers

Usé `lat = field 9, lon = field 10`. Los correctos son **`id=1, lat=8, lon=9`**
(con `keys_vals=10`).

**Consecuencia:** produjo un **falso resultado de "0 nodos en el corredor"**.
Tras corregir, el conteo real es **8.830.270 nodos**.

> Este falso negativo es un ejemplo del riesgo señalado por la regla
> "ante contradicción, detener el análisis afectado y reportar". Se detuvo,
> se diagnosticó la causa (parser propio, no el dataset) y se re-ejecutó.
> **El primer resultado era artefacto del parser, no un hecho del PBF.**

### Falsos positivos evitados

- `osmium fileinfo` (sin `-e`) devuelve **exit 0** aunque el archivo esté
  truncado. **No alcanza** para validar integridad. Hay que usar `-e`.
- El header es válido y contiene un bbox plausible: **no indica** que el
  archivo esté completo.

---

## 8. Contradicciones detectadas

### 8.1 CONTRADICCIÓN PRINCIPAL (bloqueante)

> La consigna indica que el PBF "está disponible" para producir cartografía.
> La medición muestra que **no contiene ways ni relations**, por lo que **no
> puede producir cartografía vial**.

**Resolución:** no se resuelve por análisis. Es un **punto de decisión humana**.
Se documenta y se detiene el análisis afectado (caracterización de red vial).

### 8.2 Contradicciones menores (resueltas como diferencias de notación)

| Consigna | Medición | Resolución |
|---|---|---|
| "246 MB aprox" | 257.252.921 B = 245,3 MiB | Diferencia de unidades. No es contradicción. |
| "PBF en ~/cockpit/..." | Confirmado en esa ruta | Sin contradicción. |
| "recorrido por auto" | Respetado en todo el análisis | Sin contradicción. |

### 8.3 Hallazgos colaterales que contradicen supuestos de entorno

- `~/cockpit/santa-fe.osm.pbf` **existe pero es inválido** (9.609 B).
  Si alguien asumía que había un extract de Santa Fe utilizable: **no lo hay**.
- `~/cockpit/backup_mapa/corredor.geojson` **existe pero está vacío**.
  Si alguien asumía que había un corredor definido: **no lo hay**.

---

## 9. Qué NO se ejecutó (declaración explícita)

- `osmium extract` — **NO ejecutado**
- `osmium tags-filter` — **NO ejecutado**
- `tippecanoe` — **NO ejecutado**
- Generación de MBTiles — **NO ejecutada**
- Modificación del PBF original — **NO realizada** (solo lectura)
- Instalación de paquetes — **NO realizada**
- Cambios de configuración / servicios / firewall — **NO realizados**
- `git commit` — **NO realizado**
- Operaciones de red — **NO realizadas**
- Acceso o revelación de secretos/credenciales — **NO realizado**

`commands.sh` fue validado **solo sintácticamente** (`bash -n`), que no ejecuta
ningún comando del script.

---

## 10. Archivos producidos

Todos en `~/navego_recuperado/sandbox_corredor/`:

| Archivo | Contenido |
|---|---|
| `CORRIDOR_PROPOSAL.md` | Inspección, hipótesis de trabajo, candidatos |
| `corridor_candidates.json` | 3 candidatos con bbox, rutas, supuestos, incertidumbre |
| `work_hypothesis.md` | Razonamiento del corredor (el "cómo", no solo el "dónde") |
| `commands.sh` | Comandos propuestos para Etapa 3 (**NO ejecutados**) |
| `size_estimates.csv` | Estimaciones — marcadas `UNABLE_TO_ESTIMATE_RELIABLY` |
| `EVIDENCE.md` | Este documento |
| `probe_truncation.py` | Analizador de framing de blobs |
| `probe_content.py` | Analizador de contenido por tipo de elemento |
| `probe_corridor_nodes.py` | Conteo de nodos en el corredor |
| `find_boundary.py` | Localización de la frontera nodos/ways |
| `geo_analysis.py` | Distancias y conversiones |
| `bbox_calc.py` | Cálculo de bbox candidatos |
| `diag.py` | Diagnóstico de decodificación |

**Verificación:** no se escribió **nada** fuera de `sandbox_corredor/`.

---

## 11. Reproducibilidad

Para reproducir el hallazgo principal:

```bash
# 1. Confirmar truncamiento
osmium fileinfo ~/cockpit/argentina-latest.osm.pbf     # exit 0 (solo header)
osmium fileinfo -e ~/cockpit/argentina-latest.osm.pbf  # exit 1: unexpected EOF

# 2. Confirmar hash
sha256sum ~/cockpit/argentina-latest.osm.pbf
# -> 0a979a3da11d64ab871b177ca322e200fe9785c8741bbff8c09a985e689686e4

# 3. Análisis estructural (solo lectura)
cd ~/navego_recuperado/sandbox_corredor
python3 probe_truncation.py      # -> faltan 9.409 bytes
python3 probe_content.py         # -> 0 ways, 0 relations
python3 probe_corridor_nodes.py  # -> 8.830.270 nodos en el corredor

# 4. Contraste con el backup íntegro
osmium fileinfo -e ~/cockpit/backup_mapa/argentina-260901.osm.pbf
python3 find_boundary.py         # -> ways empiezan en 297.679.654
```

---

## 12. Conclusión de la evidencia

**El PBF indicado en la consigna no es apto para generar cartografía de rutas.**
Contiene únicamente nodos; las ways y relations —que son las rutas— no están
presentes por truncamiento del archivo.

**Existe una alternativa íntegra** (`~/cockpit/backup_mapa/argentina-260901.osm.pbf`)
del mismo snapshot, cuya validez para el corredor **no fue verificada** en detalle.

**La IA no decide.** Se proponen candidatos, hipótesis y comandos; la selección
y la decisión sobre el archivo a usar corresponden al Director Ivan.

---
---

# MISIÓN A — CORREDOR SANTA FE → CABA (2026-09-22)

> Esta sección se **anexa** al registro anterior. La sección previa documenta
> la misión que descubrió que `argentina-latest.osm.pbf` estaba truncado.
> Aquí se documenta la misión que preparó el corredor usando el backup.

**Fuente autorizada:** `~/cockpit/backup_mapa/argentina-260901.osm.pbf`
**Modo:** solo lectura. Sin extract, sin tags-filter con salida, sin tippecanoe.
**Escritura:** exclusivamente en `~/navego_recuperado/sandbox_corredor/`.

---

## M1. Comandos de lectura ejecutados

### M1.1 Verificación de identidad e integridad

```bash
# Tamaño, inodo, timestamps (sin modificar)
stat ~/cockpit/backup_mapa/argentina-260901.osm.pbf

# Hash SHA256 completo (428 MB)
sha256sum ~/cockpit/backup_mapa/argentina-260901.osm.pbf
# -> d43f9af1a293f822fb23da570d7cb44d022b1943e73c79fcd6b87b190b5c504f

# Header: bbox declarado, generator, timestamps
osmium fileinfo ~/cockpit/backup_mapa/argentina-260901.osm.pbf

# Escaneo completo: nodos, ways, relations, bbox de datos
osmium fileinfo -e ~/cockpit/backup_mapa/argentina-260901.osm.pbf
```

### M1.2 Inspección de contenido

```bash
# Ways con ref RN9 (lectura a stdout, sin archivo)
osmium cat --object-type=way -f opl ~/cockpit/backup_mapa/argentina-260901.osm.pbf

# Nodos concretos (para validar el lector propio)
osmium cat --object-type=node -f opl ~/cockpit/backup_mapa/argentina-260901.osm.pbf

# Nodos con place=city (anclas Santa Fe y CABA)
osmium cat --object-type=node -f opl ~/cockpit/backup_mapa/argentina-260901.osm.pbf
```

### M1.3 Validación de expresiones de filtro (SIN escribir salida)

```bash
# tags-count es solo lectura: valida la sintaxis de las expresiones
osmium tags-count --expressions=corridor_tags.txt \
  --min-count=1 ~/cockpit/backup_mapa/argentina-260901.osm.pbf
# -> exit 0, stderr vacío. 5282 líneas de conteo. Sintaxis OK.
```

### M1.4 Análisis propio (Python, solo lectura)

```bash
python3 analyze_highways.py       # conteo de highway=* por tipo, RN9/RN11/RN8
python3 analyze_rn9_geometry.py   # geometría de RN9/RN11/RN8
python3 corridor_axis.py          # eje real AP01+RN9 Santa Fe->CABA
python3 bbox_final.py             # cálculo del bbox definitivo
```

### M1.5 Referencias locales medidas

```bash
stat ~/navego_recuperado/assets/maptest/santa_fe.mbtiles
# -> 121,0 MB

python3 -c "sqlite3 ..."   # metadatos, tiles y bytes por zoom del mbtiles

stat ~/navego_recuperado/test_maplibre/grandes/tmp_osm/santa_fe.geojson
# -> 330.297.963 bytes = 315,0 MB
```

---

## M2. Hallazgos

### M2.1 El backup es válido y utilizable

| Objeto | Cantidad |
|---|---|
| Nodos | 59.348.185 |
| **Ways** | **5.900.717** |
| **Relations** | **88.563** |

Contraste con el truncado: 49.912.000 nodos, **0 ways, 0 relations**.
El backup tiene estructura completa → sirve para cartografía vial.

### M2.2 Cobertura confirmada

Ambos bounding boxes (header y datos) cubren el rango requerido
`lon ∈ [−61,5, −58,0]`, `lat ∈ [−34,9, −31,3]`.

### M2.3 Rutas presentes

| Ruta | Ways | Bbox medido |
|---|---:|---|
| RN9 | 1.952 | `[-61.4894, -34.5446, -58.4953, -32.8295]` |
| RN11 | 1.059 | `[-60.9817, -32.8734, -60.3117, -30.0137]` |
| RN8 | 744 | `[-64.0000, -34.4712, -58.6798, -33.1780]` |

Las tres están presentes con `highway=motorway`/`trunk`.

### M2.4 El tramo Santa Fe → Rosario NO es `ref=RN9`

Es **`ref=AP01`** (Autopista Brigadier General Estanislao López).
Un filtro por `ref=RN9` perdería ese tramo. **Hallazgo que cambia el diseño
del filtrado**: el corredor debe definirse por bbox, no por ref.

### M2.5 `ref=RN1V09` es ambiguo

Aparece en dos regiones distintas del país (Córdoba ≈ −64,18/−31,42 y
Santa Fe/Rosario ≈ −61,59/−32,78). No es un identificador unívoco.

### M2.6 Medición de densidad en el corredor

| Métrica | Valor |
|---|---|
| Nodos en el bbox | **7.718.144** (13,00 % del total nacional) |
| Highways en el bbox | **385.728** |

### M2.7 Referencia real de conversión GeoJSON → MBTiles

```
santa_fe.geojson  315,0 MB  ->  santa_fe.mbtiles  121,0 MB
ratio = 0,384
```

Comando exacto recuperado de los metadatos del MBTiles:

```
tippecanoe -o santa_fe.mbtiles -Z8 -z14 --drop-densest-as-needed \
           --extend-zooms-if-still-dropping --force santa_fe.geojson
```

### M2.8 Verificación cruzada del bbox

El `bounds` de la referencia es `[-65.5186, -34.7893, -58.2532, -22.1491]`.
Su `min_lat = −34,7893` coincide con nuestro `min_lat` calculado
`−34,7892`. Dos cálculos independientes convergen → método validado.

---

## M3. ERROR PROPIO DETECTADO Y CORREGIDO (auditoría)

**Qué pasó:** se escribió un lector PBF propio (`lib_pbf.py`) porque no hay
`pyosmium` ni `protobuf` instalados y no se permite instalar paquetes.

**Síntoma:** el lector reportaba el conteo total de nodos correcto
(59.348.185) pero **IDs y coordenadas incorrectos**. P.ej. devolvía el
primer nodo como `n6` cuando `osmium` devuelve `n3`.

**Causa raíz:** en `DenseNodes`, los campos `id` (1), `lat` (8) y `lon` (9)
son `sint64` **delta-encoded con zigzag**, NO varints planos.
El conteo no se veía afectado (por eso pasaba desapercibido), pero **toda
la geometría estaba mal**.

**Detección:** comparación directa contra `osmium cat --object-type=node`.
El desajuste `n6` vs `n3` fue la señal.

**Corrección:** aplicar zigzag `(x >> 1) ^ -(x & 1)` antes de acumular.

**Validación post-corrección:**

```
lector : ids [3, 204806, 29375382, 29375391]
osmium : n3, n204806, n29375382
coords : n3 x-58.4899904 y-34.8140938  (idénticas a osmium)
```

**Impacto:** todos los números del informe provienen del lector ya
corregido. Se documenta por la regla del proyecto
**"evidencia antes que certeza"**.

---

## M4. Contradicciones reportadas (no resueltas por la IA)

| # | Contradicción | Estado |
|---|---|---|
| C-1 | Envelope del enunciado (`min_lat<=-34.9`, `max_lat>=-31.3`) vs márgenes de 20 km decididos | **Escalado al Director** — `CORRIDOR_FINAL.md` §8 |
| C-2 | `ref=RN1V09` en dos lugares distintos | Reportado; se descarta como filtro |
| C-3 | Tramo SF→Rosario es `AP01`, no `RN9` | Reportado; cambia el diseño del filtro |
| C-4 | Bbox de datos (+7,25 lat) ≠ bbox de header (−21,73 lat) | Reportado; no afecta el recorte |

---

## M5. Restricciones respetadas

- No se ejecutó `osmium extract`
- No se ejecutó `osmium tags-filter` con salida a archivo
- No se ejecutó `tippecanoe`
- No se generó ningún MBTiles
- No se modificó el PBF original (hash idéntico antes y después)
- No se instalaron paquetes
- No se descargó de internet
- No se tocó configuración, servicios, firewall ni systemd
- No se hizo `git commit`
- No se escribió fuera de `sandbox_corredor/`
- No se accedió a secretos, API keys ni credenciales

---

## M6. Conclusión de la evidencia (misión A)

El backup `argentina-260901.osm.pbf` está **íntegro y verificado**. Cubre el
corredor Santa Fe → CABA. Se midió la geometría real del eje, se calculó el
bbox, se validaron los comandos y se midió una referencia real de conversión
a MBTiles.

**Queda una sola decisión humana** (envelope de latitud, §8 del informe).

**La IA no ejecuta.** El paquete queda listo para autorización.

---

## Actualizacion — Mision B ejecutada (2026-09-22 18:23)

Estado: EXITOSA.

Ejecutado por bash sandbox_corredor/run_mision_b.sh.
Todos los pasos completados. MBTiles final: 100 MB, 43394 tiles.
Ver MISIÓN_B_RESULTADO.md para detalle completo.

Error encontrado y corregido durante ejecucion: flag -L vs -l en
tippecanoe 2.79. Documentado como leccion.
