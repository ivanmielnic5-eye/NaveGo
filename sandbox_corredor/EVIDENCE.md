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
