# CORRIDOR_PROPOSAL.md — Caracterización del PBF de Argentina y candidatos de corredor

**Proyecto:** NaveGo
**Tarea:** Caracterizar `argentina-latest.osm.pbf` y proponer 2-3 candidatos de corredor
para el viaje **Santa Fe Capital -> Buenos Aires (CABA)** por **auto (ruta terrestre)**.
**Rol de la IA:** producir evidencia, candidatos, hipótesis y comandos propuestos.
**La IA NO decide.** La decisión final es del Director Ivan (Etapa 3).
**Modo:** solo lectura / análisis. No se ejecutó ninguna extracción, filtro ni tippecanoe.

---

## AVISO CRÍTICO — LEER ANTES QUE NADA

> **El archivo `~/cockpit/argentina-latest.osm.pbf` está TRUNCADO y NO es apto
> para generar cartografía de rutas.**
>
> - Le faltan los **9.409 bytes finales** (el último blob quedó incompleto).
> - Pero el daño real es mucho mayor: por el orden de Geofabrik (`Sort.Type_then_ID`,
>   es decir **nodos primero, después ways, después relations**), el corte deja al
>   archivo **sin ninguna way (camino) y sin ninguna relation**.
> - **Sin ways no hay rutas. Sin rutas no hay corredor, ni ruteo, ni red vial.**
>
> Existe un **backup íntegro** en `~/cockpit/backup_mapa/argentina-260901.osm.pbf`
> (428.645.479 bytes) que sí lee completo y corresponde al **mismo snapshot base**.
> **Este hallazgo es un punto de decisión humana (ver sección F).**

---

## A) INSPECCIÓN

### A.1 Qué se inspeccionó

| Elemento | Ruta | Resultado |
|---|---|---|
| PBF objetivo | `~/cockpit/argentina-latest.osm.pbf` | 257.252.921 bytes — **TRUNCADO** |
| Backup PBF | `~/cockpit/backup_mapa/argentina-260901.osm.pbf` | 428.645.479 bytes — **ÍNTEGRO** |
| Backup PBF (internal) | `~/cockpit/backup_mapa/argentina-260902-internal.osm.pbf` | 470.698.521 bytes — no analizado |
| Backup PBF (history) | `~/cockpit/backup_mapa/argentina-internal.osh.pbf` | 908.544.266 bytes — no analizado |
| Extract pequeño | `~/cockpit/santa-fe.osm.pbf` | 9.609 bytes — **inválido** (`invalid BlobHeader size`) |
| GeoJSON | `~/cockpit/backup_mapa/corredor.geojson` | **vacío** (`features: []`) |

**Nota de discrepancia de ruta:** la consigna indicaba el PBF en
`~/cockpit/argentina-latest.osm.pbf` (246 MB aprox). El archivo real mide
257.252.921 bytes = **245,3 MiB** (o 257,3 MB decimales). La diferencia es de
unidades (MiB vs MB), no de contenido. **No existe** copia en `~/navego_recuperado/`.

### A.2 Hash del PBF (calculado)

Evidencia observada — `sha256sum`:

```
0a979a3da11d64ab871b177ca322e200fe9785c8741bbff8c09a985e689686e4  argentina-latest.osm.pbf
```

Hash del backup íntegro (prefijo de 16 hex, para referencia):

```
d43f9af1a293f822...  argentina-260901.osm.pbf   (428.645.479 bytes)
```

> **Los hashes son distintos.** El backup **no es** una copia idéntica del objetivo;
> es un archivo más grande y completo. Ver inferencia en A.5.

### A.3 Evidencia de truncamiento

Comando: `osmium fileinfo -e ~/cockpit/argentina-latest.osm.pbf`

Salida (extracto textual):

```
File:
  Name: argentina-latest.osm.pbf
  Format: PBF
  Compression: none
  Size: 257252921
Header:
  Bounding boxes:
    (-73.614525,-55.682956,-53.63534,-21.725753)
  Options:
    osmosis_replication_timestamp=2026-09-01T20:20:50Z
    osmosis_replication_sequence_number=4900
    sorting=Type_then_ID
PBF error: unexpected EOF
```

Contraste importante (evidencia observada):

- `osmium fileinfo` **sin** `-e` -> **exit 0**. Lee solo el header.
- `osmium fileinfo -e` -> **exit 1**, `PBF error: unexpected EOF`. Escanea todos los blobs.
- `osmium cat -f opl` -> **exit 1**, `PBF error: unexpected EOF`.

El header es legible y válido; el **cuerpo** de datos está incompleto.

### A.4 Localización exacta del corte (medición propia)

Se escribió un analizador propio en Python (`probe_truncation.py`) que recorre el
* framing * de blobs PBF (prefijo big-endian de 4 bytes + `BlobHeader`) **sin
descomprimir** y sin modificar el archivo. Resultado:

```
file_size_bytes:        257,252,921
complete_blobs_read:    6,240
header_blob_end:        203
last_complete_blob_end: 257,238,148
bytes_readable_pct:     99.9943 %
blob_types: {'OSMHeader': 1, 'OSMData': 6,239}

TRUNCATED_BLOB offset=257238148 type=OSMData datasize=24165
  need_end=257262330  file_size=257252921  missing_bytes=9409
```

**Evidencia observada:**
- Faltan exactamente **9.409 bytes** al final.
- 6.239 de 6.240 blobs de datos están completos.
- El último blob está cortado a la mitad.

### A.5 Contenido del tramo legible — el hallazgo que cambia todo

Se descomprimió cada blob íntegro y se leyeron los `PrimitiveGroup` para determinar
**qué tipos de elemento** contiene el tramo legible.

Resultado (evidencia observada):

```
=== TOTAL COUNTS (tramo legible) ===
  node:              49,912,000
  dense_node_group:       6,239
  way:                        0     <-- CERO
  relation:                   0     <-- CERO

primer blob con node:     índice 1
primer blob con way:      None
primer blob con relation: None
```

Verificación adicional sobre el **último blob legible** (índice 6239):
sus grupos contienen **únicamente** el field number `2` (DenseNodes).
Los field `3` (ways) y `4` (relations) **no aparecen en ningún blob legible**.

**Conclusión:** el tramo legible contiene **solo nodos**. Las ways y relations
están todas después del punto de corte.

### A.6 Cuantificación de lo faltante (usando el backup íntegro como referencia)

Se localizó el byte donde empiezan las ways en el backup íntegro (`find_boundary.py`):

```
BACKUP íntegro: 8.170 blobs, 428.645.479 bytes
PRIMER blob con ways/relations: índice 7420
  offset = 297.679.654  (69,45 % del archivo)
```

Comparación (evidencia observada):

| Propiedad | OBJETIVO (`latest`) | BACKUP (`260901`) |
|---|---|---|
| Tamaño | 257.252.921 | 428.645.479 |
| Header bbox | `(-73.614525,-55.682956,-53.63534,-21.725753)` | **idéntico** |
| `replication_timestamp` | `2026-09-01T20:20:50Z` | **idéntico** |
| `replication_sequence_number` | `4900` | **idéntico** |
| `generator` | `osmium/1.16.0` | **idéntico** |
| Lectura | **TRUNCADA (EOF)** | OK |
| Nodos | 49.912.000 (parcial) | 59.348.185 (total) |
| Ways | **0 alcanzables** | 5.900.717 |
| Relations | **0 alcanzables** | 88.563 |

**Inferencia (marcada como inferencia, no como hecho):**
Header bbox, timestamp de replicación, secuencia y generator **idénticos** => el
objetivo y el backup derivan del **mismo snapshot de Geofabrik**. El objetivo
parece ser una **descarga/copia incompleta** (60,02 % del tamaño del backup) que
se cortó dentro de la sección de nodos, perdiendo:
- ~40 MB de la **cola de nodos** (49,9M de 59,3M = 84,1 % de los nodos), y
- **131 MB completos de ways + relations**.

### A.7 Cobertura del corredor — nodos (lo único medible)

Se contaron nodos dentro de un bbox de corredor `(-62.5,-35.5,-57.5,-30.0)`:

```
NODES inside corridor (tramo legible): 8.830.270
corridor_nodes_actual_bbox: [-62.4999976, -35.4999968, -57.5000006, -30.0000004]
```

**Evidencia observada:** hay nodos en el corredor.
**Pero esto NO habilita el corredor:** los nodos son solo geometría puntual.
Los **caminos que unen esos nodos no están en el archivo**. No se puede construir
una red vial, ni rutear, ni distinguir una autopista de un camino de tierra.

### A.8 Errores propios detectados y corregidos (transparencia metodológica)

Durante el análisis cometí **dos errores de parsing**, que reporto por honestidad
y porque afectan la reproducibilidad:

1. **Números de campo de `BlobHeader`:** usé `datasize=field 2`. Es **field 3**.
2. **Números de campo de `DenseNodes`:** usé `lat=9, lon=10`. Son **`id=1, lat=8, lon=9`** (con `keys_vals=10`).

El segundo error produjo un **falso resultado inicial de "0 nodos en el corredor"**.
Al corregirlo, el conteo pasó a **8.830.270**. **El primer resultado era un artefacto
de mi parser, no un hecho del dataset.** Lo dejo registrado porque un lector que
reproduzca el análisis debe usar los números de campo correctos.

> **Regla aplicada:** ante contradicción, se detuvo el análisis afectado y se
> diagnosticó la causa antes de continuar (regla de comportamiento #4).

---

## B) HIPÓTESIS DE TRABAJO

> Recordatorio: esto es una **hipótesis de trabajo**, no una decisión.
> Un humano debe evaluarla en la Etapa 3.

### B.1 Qué recortar (features y atributos relevantes para navegación por auto)

**Prioridad ALTA — red vial (imprescindible):**

| Tag OSM | Valores | Por qué |
|---|---|---|
| `highway` | `motorway`, `motorway_link` | Autopistas; eje principal del viaje |
| `highway` | `trunk`, `trunk_link` | Rutas nacionales de primer orden |
| `highway` | `primary`, `primary_link` | Rutas nacionales/provinciales |
| `highway` | `secondary`, `secondary_link` | Red de conexión y desvíos |
| `highway` | `tertiary` | Conectividad local entre pueblos |
| `name`, `ref` | (texto) | **Etiquetas visibles en el mapa** (ej. "RN 9", "Autopista Rosario-Córdoba") |
| `oneway` | `yes`/`-1`/`no` | Sentido de circulación |
| `maxspeed` | valor | Límites (relevante para ETA) |
| `bridge`, `tunnel` | `yes` | Cambios de cota y pasos críticos |
| `surface` | valor | Distinguir pavimento de tierra |

**Prioridad ALTA — nodos de la red (para que las ways tengan geometría):**
Todos los nodos referenciados por las ways seleccionadas. **No** hace falta el
universo completo de 8,8M nodos del corredor.

**Prioridad MEDIA — POIs para navegación y seguridad:**

| Tag OSM | Por qué |
|---|---|
| `place=city/town/village` | **Localidades**: referencia humana y de ruteo |
| `amenity=fuel` | **Estaciones de servicio** — críticas en ruta |
| `amenity=hospital` / `healthcare=hospital` | **Hospitales** — seguridad del viaje |
| `amenity=police` | Seguridad |
| `amenity=restaurant`/`fast_food` | Paradas |
| `highway=rest_area` / `services` | Áreas de descanso en autopista |
| `shop=supermarket` | Abastecimiento |
| `tourism=hotel`/`motel` | Pernocte |

**Prioridad BAJA / EXCLUIBLE para la prueba:**

| Tag | Motivo de exclusión |
|---|---|
| Edificios (`building=*`) | Volumen enorme, poco valor para navegación de ruta |
| `landuse`, uso de suelo | Ruido visual y de tamaño |
| Hidrografía menor (`waterway=stream`) | No esencial para auto |
| Límites administrativos | Útiles, pero no para una prueba de corredor |
| `natural=tree`, mobiliario | Ruido |
| Datos de transporte público | Fuera de scope (viaje en auto) |

> **Nota de alcance:** la consigna pide explícitamente **navegación por auto**.
> Por eso **no** se prioriza hidrografía navegable ni marina, a diferencia de un
> corredor acuático. El encuadre "recorrido terrestre" se respetó en todo el análisis.

### B.2 Por dónde (rutas principales propuestas)

**Eje principal propuesto: RN 9 (Ruta Nacional 9) — corredor Santa Fe -> Rosario -> Buenos Aires.**

Secuencia de nodos urbanos sobre el eje:

```
Santa Fe Capital
   -> (RN 9 / AP-01) ->
Rosario
   -> (RN 9, Autopista Rosario-Buenos Aires) ->
San Nicolás
   -> ->
Zárate / Campana
   -> (Acceso Norte / RN 9) ->
Buenos Aires (CABA)
```

**Alternativa estructural por el este: RN 11.**
```
Santa Fe -> Reconquista ... (no aplica al sur)
Rosario -> RN 11 -> San Pedro -> Zárate -> CABA
```
RN 11 corre **paralela al este**, más cerca del Río Paraná, pasando por
**San Pedro**. Es la alternativa natural a RN 9 en el tramo sur.

**Otras rutas nacionales candidatas a considerar (mencionadas en la consigna):**
RN 33, RN 34, RN 8, RN 19.

| Ruta | Rol en este viaje | Comentario |
|---|---|---|
| **RN 9** | Eje principal SF -> Rosario -> CABA | Corredor natural, autopista en tramos clave |
| **RN 11** | Alternativa este, vía San Pedro | Paralela, cercana al Paraná |
| **RN 33** | Conexión Rosario <-> sudoeste (hacia Río Cuarto) | **No es eje SF->CABA**; relevante solo si se desvía por el oeste |
| **RN 34** | Eje norte-sur por el oeste (Rosario -> Santiago del Estero) | **No sirve** para SF->CABA |
| **RN 8** | Conexión sur (Pergamino -> Buenos Aires) | **Alternativa parcial** al sur del corredor |
| **RN 19** | Córdoba -> Santa Fe | **Alimenta** el corredor desde el oeste, no es eje |

**Precisión importante:** RN 33, RN 34, RN 8 y RN 19 **no son alternativas
directas** Santa Fe -> Buenos Aires. Se incluyen en la lista de la consigna, pero
su rol real es **alimentador o de desvío largo**. No se debe presentar RN 34 como
alternativa del corredor: geográficamente no lo es.

### B.3 Con qué ancho (justificación del margen a cada lado)

Se proponen **tres anchos**, cada uno como candidato separado (ver sección C).
El ancho se expresa como **semiancho** a cada lado del eje SF->CABA.

**Cálculo de conversión** (a latitud media ~ -33,1):

```
1 grado de latitud ≈ 110,906 km
1 grado de longitud ≈  93,339 km
```

| Semiancho | Para qué alcanza | Justificación |
|---|---|---|
| **20 km** | Corredor ajustado | Cubre la ruta y su entorno inmediato. **NO cubre** el desvío RN 9 <-> RN 11 en el tramo sur. Riesgo: si RN 9 se corta, no hay salida en el mapa. |
| **50 km** | Corredor medio **(recomendado como hipótesis)** | La separación entre RN 9 y RN 11 en el tramo sur (Rosario->Zárate) es del orden de 40-60 km. **50 km captura ambas como alternativas reales.** Además cubre Pergamino, San Pedro, San Nicolás. |
| **90 km** | Corredor amplio | Captura desvíos largos, pero incorpora ~204.000 km² y mucho dato irrelevante. Útil solo si se quiere tolerar un corte mayor. |

**Fundamento del número 50 km:** la justificación **no** es un valor arbitrario.
El criterio es: *el semiancho debe ser mayor que la separación entre el eje
principal y su alternativa natural*. Medida la separación RN 9 / RN 11 en el
tramo sur (Rosario -> Zárate), el orden de magnitud es 40-60 km, por lo que
**50 km es el mínimo que hace que la alternativa exista dentro del recorte**.
Con 20 km la alternativa queda fuera y el recorte no sirve para el propósito de
tener un plan B.

> **INCERTIDUMBRE:** la separación RN 9 / RN 11 **no fue medida sobre datos**
> (las ways no están en el archivo). Es una **estimación a partir de coordenadas
> de ciudades conocidas** (Rosario, San Pedro, Zárate), no una medición de la
> traza real de cada ruta. Debe **verificarse** sobre el PBF íntegro.

### B.4 Elección de ruta: por qué RN 9 y no otra (criterios)

Criterios propuestos, en orden:

1. **Continuidad / jerarquía vial** — RN 9 es el eje histórico y de mayor jerarquía
   entre Santa Fe, Rosario y Buenos Aires.
2. **Tiempo de viaje** — el corredor RN 9 concentra los tramos de autopista
   (Autopista Rosario-Buenos Aires, Acceso Norte), lo que reduce tiempo.
3. **Población y servicios** — Rosario, San Nicolás, Zárate y CABA dan cobertura
   densa de combustible, hospitales y auxilio.
4. **Redundancia** — la existencia de RN 11 como paralela cercana da un plan B.
5. **Simplicidad de prueba** — un eje único y bien definido es más fácil de
   validar que un corredor multipunto.

**Contra-criterio que debe pesar:** RN 9 atraviesa zonas de **alta congestión**
(Rosario, Acceso Norte al AMBA). RN 11 suele ser **más descongestionada** pero
más lenta. La elección final depende de si la prioridad es **tiempo** o
**previsibilidad** — decisión humana.

> **INCERTIDUMBRE:** los criterios 1-5 son **criterio experto / inferencia**, no
> medición. No se midió tiempo real, estado de calzada, ni congestión. Datos como
> `maxspeed` y `surface` **están en el PBF pero no se pudieron leer** (ways ausentes).

### B.5 Alternativas (si la ruta principal está cortada)

| Escenario | Desvío natural propuesto |
|---|---|
| Corte en RN 9 entre Rosario y San Nicolás | **RN 11** por el este (vía San Pedro), reincorporando en Zárate |
| Corte en RN 9 al norte de Rosario | **RN 33 / RN 34** hacia el oeste y reingreso por RN 19 / RN 8 (desvío largo) |
| Corte en el Acceso Norte / AMBA | Ingreso por **RN 8** (Pergamino -> Buenos Aires) o por **RN 11 / Autopista Panamericana** |
| Bloqueo total del corredor este | Desvío largo por **RN 33 -> RN 8**, con costo alto de tiempo |

**El desvío natural primario es RN 11.** Es la alternativa más corta y de menor
costo frente a un corte de RN 9.

> **INCERTIDUMBRE:** los desvíos son **propuesta**, no ruteo calculado. Sin las
> ways no se puede confirmar que exista conexión física entre RN 9 y RN 11 en
> cada punto, ni que los tramos estén transitables.

### B.6 Riesgos y huecos de datos

**Riesgos de datos (bloqueantes):**

| # | Riesgo | Severidad | Estado |
|---|---|---|---|
| R1 | PBF objetivo **sin ways ni relations** | **BLOQUEANTE** | Confirmado por medición |
| R2 | PBF objetivo con **solo 84,1 % de los nodos** | **BLOQUEANTE** | Confirmado por medición |
| R3 | `santa-fe.osm.pbf` **inválido** (blob header corrupto) | Medio | Confirmado |
| R4 | `corredor.geojson` **vacío** | Bajo | Confirmado |
| R5 | No se verificó si el backup íntegro cubre el corredor | **ALTO** | **NO VERIFICADO** |

**Huecos de datos (no bloqueantes, pero limitan la propuesta):**

- No se midió la traza real de RN 9 / RN 11 / RN 33 / RN 34 / RN 8 / RN 19.
- No se verificó presencia ni calidad de `amenity=fuel`, `amenity=hospital` en el corredor.
- No se evaluó densidad de la red secundaria.
- No se estimó el **tamaño del MBTiles** con base en datos (ver `size_estimates.csv`).

### B.7 Incertidumbres explícitas

1. **No se puede caracterizar la red vial del corredor** con el archivo dado, porque
   las ways no existen en el tramo legible. Todo lo relativo a rutas es
   **inferencia geográfica**, no medición.
2. **No se verificó** que `argentina-260901.osm.pbf` (backup) tenga la misma
   cobertura útil del corredor. Se sabe que comparte header y snapshot, pero no
   se inspeccionó su contenido vial en detalle.
3. **La separación RN 9 / RN 11 no fue medida.** Es estimación por ciudades.
4. **Los tamaños de MBTiles son estimaciones de orden de magnitud**, no medidas.
5. **No se sabe** si el objetivo truncado fue un error de descarga o una
   modificación deliberada. Solo se observa el estado.
6. **No se evaluó** el impacto de zona horaria, proyección ni zoom óptimo.

---

## C) CANDIDATOS

Tres candidatos de bounding box. **Ninguno se declara mejor que otro.**

### C1 — `C1_ajustado_20km` (corredor ajustado)

```
min_lon = -60.915343   min_lat = -34.784032
max_lon = -58.163557   max_lat = -31.430368
```

- **Ancho:** semiancho 20 km a cada lado del eje SF -> CABA.
- **Span:** 2,7518° lon × 3,3537° lat -> **~95.500 km²**.
- **Rutas incluidas (esperadas):** RN 9 (eje), tramos de RN 8 y RN 11 cercanos.
- **Ruta principal propuesta:** RN 9.
- **Alternativas:** limitadas; RN 11 probablemente **fuera** del recorte en el tramo sur.
- **Ventaja:** menor tamaño, prueba más rápida.
- **Riesgo:** **sin plan B dentro del mapa** si RN 9 se corta.
- **Incertidumbre:** media-alta (la traza real puede apartarse del eje recto).

### C2 — `C2_medio_50km` (corredor medio) — *hipótesis propuesta*

```
min_lon = -61.242408   min_lat = -35.054531
max_lon = -57.836492   max_lat = -31.159869
```

- **Ancho:** semiancho 50 km a cada lado del eje.
- **Span:** 3,4059° lon × 3,8947° lat -> **~137.300 km²**.
- **Rutas incluidas (esperadas):** RN 9 (eje), **RN 11** (alternativa completa),
  RN 8 (parcial), RN 33/RN 34 (borde oeste), RN 19 (borde noroeste).
- **Ruta principal propuesta:** RN 9.
- **Alternativas:** **RN 11** (primaria), RN 8 (acceso alternativo a Buenos Aires).
- **Ventaja:** es el **mínimo ancho que mantiene RN 11 como alternativa real**.
- **Costo:** incluye más área rural (Pampa) con datos poco útiles.
- **Incertidumbre:** media.

### C3 — `C3_amplio_90km` (corredor amplio)

```
min_lon = -61.678494   min_lat = -35.415195
max_lon = -57.400406   max_lat = -30.799205
```

- **Ancho:** semiancho 90 km a cada lado del eje.
- **Span:** 4,2781° lon × 4,6160° lat -> **~204.400 km²**.
- **Rutas incluidas (esperadas):** todas las anteriores + RN 33, RN 34, RN 19 con
  más margen; posible inclusión de Córdoba parcial.
- **Ruta principal propuesta:** RN 9.
- **Alternativas:** múltiples, incluyendo desvíos largos por el oeste.
- **Ventaja:** máxima tolerancia a cortes.
- **Costo:** **mayor tamaño y ruido**; incluye ciudades fuera del viaje.
- **Incertidumbre:** media-baja en cobertura, **alta en utilidad**.

### C.4 Tabla comparativa

| | C1 (20 km) | C2 (50 km) | C3 (90 km) |
|---|---|---|---|
| Área aprox. | ~95.500 km² | ~137.300 km² | ~204.400 km² |
| RN 9 | Sí | Sí | Sí |
| RN 11 completa | Probablemente no | **Sí** | Sí |
| RN 8 | Parcial | Parcial | Sí |
| Plan B real | No | **Sí** | Sí |
| Ruido | Bajo | Medio | Alto |

---

## D) PUNTOS QUE REQUIEREN DECISIÓN HUMANA

1. **¿Se acepta el PBF truncado como inservible** y se usa el backup
   `argentina-260901.osm.pbf`? *(Decisión bloqueante.)*
2. **¿Se re-descarga** `argentina-latest.osm.pbf`? Requiere red — **prohibido en
   esta tarea**, debe autorizarlo el Director.
3. **¿Qué semiancho** se adopta: 20, 50 o 90 km.
4. **¿RN 9 o RN 11** como eje principal.
5. **¿Prioridad tiempo o previsibilidad** en la elección de ruta.
6. **¿Qué zooms** se generan y con qué presupuesto de tamaño.
7. **¿Se valida antes** el backup íntegro con un `osmium fileinfo -e` completo?

---

## E) QUÉ NO SE EJECUTÓ (declaración explícita)

Respetando las restricciones, **NO** se ejecutó:

- `osmium extract` — **no ejecutado**
- `osmium tags-filter` — **no ejecutado**
- `tippecanoe` — **no ejecutado**
- Generación de MBTiles — **no ejecutada**
- Modificación del PBF original — **no realizada** (solo lectura)
- Instalación de paquetes — **no realizada**
- Cambios de configuración, servicios, firewall — **no realizados**
- `git commit` — **no realizado**
- Operaciones de red — **no realizadas**
- Acceso o revelación de secretos/credenciales — **no realizado**

Todo el análisis fue **lectura**. Los archivos escritos están **exclusivamente**
en `~/navego_recuperado/sandbox_corredor/`.

---

## F) RESUMEN EJECUTIVO

**Estado:** el PBF objetivo **no sirve** para cartografía vial.
Le faltan las **ways y relations completas** (131 MB) más ~40 MB de nodos.

**Hipótesis de trabajo propuesta:** recortar un corredor **Santa Fe -> CABA**
sobre el eje **RN 9**, con **semiancho de 50 km**, preservando
`highway` (motorway/trunk/primary/secondary/tertiary), nombres y refs, más POIs
de combustible, hospitales, localidades y áreas de servicio; con **RN 11** como
alternativa natural y **RN 8** como acceso alternativo a Buenos Aires.

**Candidatos:** C1 (20 km), C2 (50 km), C3 (90 km). **La IA no elige.**

**Siguiente paso sugerido por la IA (no ejecutado):** validar el backup íntegro
y, sobre él, medir la separación real RN 9 / RN 11 antes de fijar el ancho.
