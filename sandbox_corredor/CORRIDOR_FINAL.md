# CORRIDOR FINAL — Santa Fe Capital → CABA (eje RN9)

**TASK_ID:** CORREDOR-SF-CABA-MISION-A
**Fecha:** 2026-09-22
**Misión:** A — PREPARACIÓN (no ejecución)
**Autoridad final:** Iván (Director Funcional)
**Estado:** LISTO PARA AUTORIZACIÓN — pendiente 1 decisión humana (ver §8)

> **La IA prepara. La IA no ejecuta. El humano autoriza.**
> Ningún comando de `commands_final.sh` se ejecutó en esta misión.

---

## 0. Resumen ejecutivo

Se validó el backup como fuente de datos y se midió **directamente sobre el
PBF** la geometría real del corredor. El resultado es un paquete que puede
autorizarse tal cual y ejecutarse en una misión B sin recalcular nada.

| Dato | Valor |
|---|---|
| Hash del backup | `d43f9af1…b5c504f` — **VERIFICADO, coincide** |
| Ways / Relations | **5.900.717 / 88.563** (el truncado tenía 0/0) |
| Bbox definitivo | `-61.5439126, -34.7892201, -57.8418874, -31.4390329` |
| Nodos en el corredor | **7.718.144** (13,00 % del total nacional) |
| Highways en el corredor | **385.728** |
| MBTiles estimado (z8–14) | **40–110 MB** (punto medio ~60 MB) |
| Decisión humana pendiente | **1** — envelope de latitud (§8) |

---

## 1. Validación del backup

### 1.1 Hash SHA256

```
esperado: d43f9af1a293f822fb23da570d7cb44d022b1943e73c79fcd6b87b190b5c504f
observado:d43f9af1a293f822fb23da570d7cb44d022b1943e73c79fcd6b87b190b5c504f
                                    → COINCIDE
```

### 1.2 Integridad estructural (`osmium fileinfo -e`)

| Campo | Valor |
|---|---|
| Tamaño | 428.645.479 bytes (428,6 MB decimales / 408,8 MiB) |
| Formato | PBF, compresión none |
| Generator | `osmium/1.16.0` |
| Timestamp | `2026-09-01T20:20:50Z` |
| Replication sequence | `4900` (Geofabrik argentina-updates) |
| **Nodos** | **59.348.185** |
| **Ways** | **5.900.717** ✅ |
| **Relations** | **88.563** ✅ |
| Ordenado por type+ID | sí |
| Múltiples versiones | no |

**Contraste con el PBF truncado** (`argentina-latest.osm.pbf`, SHA
`0a979a3d…`): 49.912.000 nodos pero **0 ways y 0 relations**. El backup
tiene ways y relations en cantidad coherente → **es utilizable para
cartografía vial**. El truncado queda descartado.

### 1.3 Cobertura del rango requerido

Se verificaron **dos** bounding boxes, porque el header y los datos difieren
(artefacto conocido de Geofabrik):

| Campo | Requerido | Header | Datos | ¿Cubre? |
|---|---|---|---|---|
| min_lon | ≤ −61.5 | −73.614525 | −79.3652783 | ✅ |
| min_lat | ≤ −34.9 | −55.682956 | −61.1276558 | ✅ |
| max_lon | ≥ −58.0 | −53.635340 | −41.4427772 | ✅ |
| max_lat | ≥ −31.3 | −21.725753 | +7.2535178 | ✅ |

Ambos bounding boxes cubren el rango requerido con holgura. El bbox de datos
es anómalamente amplio (llega a lat +7,25, Ecuador/Colombia) — **se reporta
como observación**, pero no afecta el recorte porque `osmium extract` usa el
bbox que uno le pasa, no el del header.

> **Nota de trazabilidad:** el header declara `Compression: none` pero los
> blobs están comprimidos individualmente en zlib; es la convención estándar
> de PBF (el campo se refiere al default del archivo, no a los blobs).

---

## 2. Inspección de ways y relations

### 2.1 Conteo de `highway=*` (todo el país)

Total: **1.587.996** ways con `highway=*`.

| Tipo | Cantidad | | Tipo | Cantidad |
|---|---:|---|---|---:|
| motorway | 5.210 | | motorway_link | 4.938 |
| trunk | 21.598 | | trunk_link | 5.609 |
| primary | 31.913 | | primary_link | 3.473 |
| secondary | 64.075 | | secondary_link | 2.900 |
| tertiary | 72.889 | | tertiary_link | 1.373 |
| unclassified | 174.245 | | living_street | 45.354 |
| residential | 576.148 | | footway | 124.900 |
| service | 265.244 | | path | 36.142 |
| track | 122.199 | | cycleway / steps | 3.107 / 5.780 |

### 2.2 Rutas de interés

| Ruta | ¿Presente? | Ways (país) | Rol | Bbox medido en el corredor |
|---|---|---|---|---|
| **RN9** | ✅ sí | 1.952 | Eje principal | `[-61.4894, -34.5446, -58.4953, -32.8295]` |
| **RN11** | ✅ sí | 1.059 | Desvío alternativo | `[-60.9817, -32.8734, -60.3117, -30.0137]` |
| **RN8** | ✅ sí | 744 | Acceso alternativo AMBA | `[-64.0000, -34.4712, -58.6798, -33.1780]` |

Muestras verificadas de tags:

- **RN9** → `w10585611` `highway=motorway, ref=RN9, name=Autopista Juan José Valle, maxspeed=120`
- **RN11** → `w23110405` `highway=trunk, ref=RN11, name=Ruta Nacional 11 Juan de Garay`
- **RN8** → `w23032020` `highway=motorway, ref=RN8, name=Acceso Norte Ramal Pilar`

### 2.3 HALLAZGO CRÍTICO — el eje no es una sola `ref`

Al medir la geometría real se descubrió algo que **invalida el filtro
ingenuo por `ref=RN9`**:

1. **El tramo Santa Fe → Rosario está taggeado `ref=AP01`**
   (Autopista Brigadier General Estanislao López), **no** `ref=RN9`.
   Un filtro `ref=RN9` **pierde ese tramo completo**.

2. **`ref=RN1V09` es ambiguo**: aparece en **dos lugares distintos** de
   Argentina — uno cerca de Córdoba (−64,18 / −31,42) y otro cerca de
   Santa Fe/Rosario (−61,59 / −32,78). No sirve como filtro único.

3. **`RN9` tiene dos ramas**: la litoral (Rosario → CABA, la que nos
   interesa) y la que sube hacia Córdoba (−64,18 / −29,03 … ). El
   semiancho de 50 km cerca de Rosario captura parte de la rama Córdoba,
   lo cual es inevitable y aceptable.

**Consecuencia para el diseño:** el corredor se define por **BBOX**, no por
`ref`. Los `ref` sirven para etiquetar y para verificar, no para recortar.

### 2.4 Eje real medido (no asumido)

| Tramo | Ruta/ref | Latitud | Longitud | Puntos |
|---|---|---|---|---|
| Santa Fe → Rosario | `AP01` | −32,8850 … −31,6223 | −60,9970 … −60,7105 | 1.518 |
| Rosario → CABA | `RN9` | −34,5446 … −33,0 | −60,5871 … −58,4953 | 3.642 |

Todos los tramos del tramo SF→CABA son `highway=motorway`.
Longitud aproximada del eje: **~320 km**.

**Anclas observadas en el PBF** (no asumidas):

| Ciudad | Nodo OSM | Coordenada | Fuente |
|---|---|---|---|
| Santa Fe | 198423933 | −60,7019561, −31,6186951 | `place=city`, población 404.910 |
| CABA | 81590481 | −58,3887904, −34,6095579 | `place=city`, `official_name=CABA` |

---

## 3. Bbox definitivo

### 3.1 Método

- **Anclas:** Santa Fe (−31,6186951) y CABA (−34,6095579) → eje latitudinal.
- **Eje longitudinal:** rango medido del eje real, −60,9970 (AP01 al oeste
  de Rosario) … −58,3888 (CABA).
- **Semiancho:** 50 km a cada lado (decisión del Director).
- **Margen norte:** 20 km más allá de Santa Fe (decisión del Director).
- **Margen sur:** 20 km más allá de CABA (decisión del Director).
- **Conversión:** 1° lat = 111,32 km; 1° lon = 111,32 · cos(lat) km.
  Para el semiancho se toma el cos de la latitud **más desfavorable**
  (la más cercana al ecuador), que es el caso conservador.

### 3.2 Resultado

```
min_lon = -61.5439126
min_lat = -34.7892201
max_lon = -57.8418874
max_lat = -31.4390329
```

Parámetros derivados:

| Cantidad | Valor |
|---|---|
| Semiancho en grados de longitud | 0,5469126° |
| Margen norte/sur en grados | 0,1796622° (20 km c/u) |
| Extensión latitudinal | 3,350187° |
| Extensión longitudinal | 3,702025° |
| Área aproximada | **128.731 km²** |

### 3.3 Verificación de contención

| Punto | Coordenada | ¿Dentro? |
|---|---|---|
| Santa Fe capital | −60,702, −31,619 | ✅ |
| Rosario | −60,650, −32,950 | ✅ |
| San Nicolás | −60,226, −33,334 | ✅ |
| Zárate | −59,028, −34,098 | ✅ |
| CABA | −58,389, −34,610 | ✅ |
| Córdoba (debe quedar fuera) | −64,188, −31,420 | ❌ fuera (correcto) |

### 3.4 Línea de comando resultante

```
--bbox=-61.5439126,-34.7892201,-57.8418874,-31.4390329
```

---

## 4. Comandos para la misión B

Ver **`commands_final.sh`**. Contiene 5 pasos, todos comentados y explicados:

| Paso | Operación | Entrada | Salida |
|---|---|---|---|
| 0 | Verificar hash | backup | — (aborta si no coincide) |
| 1 | `osmium extract --bbox` | backup | `corredor_sf_caba.osm.pbf` |
| 2 | `osmium tags-filter` | extract | `..._filtrado.osm.pbf` |
| 3 | `osmium export` | filtrado | `corredor_sf_caba.geojson` |
| 4 | `tippecanoe -Z8 -z14` | geojson | `corredor_sf_caba.mbtiles` |
| 5 | Verificación | mbtiles | comparar vs `size_estimates.csv` |

**Parámetros de tippecanoe**: idénticos a los de la referencia real
`santa_fe.mbtiles` que ya funcionó en este proyecto, para no introducir
variables nuevas:

```
-Z8 -z14 --drop-densest-as-needed --extend-zooms-if-still-dropping --force
```

**Sintaxis validada**: el archivo de expresiones `corridor_tags.txt` (30+
reglas) fue verificado con `osmium tags-count` → **exit 0, stderr vacío**.
No hay errores de sintaxis que puedan romper la misión B.

---

## 5. Estimación de tamaños

Ver **`size_estimates.csv`** para el detalle completo. Resumen:

| Paso | Artefacto | Estimado | Rango | Base |
|---|---|---:|---|---|
| 1 | extract PBF | 70 MB | 53–90 | **Extrapolado**: 13,00 % de nodos medido |
| 2 | filtrado PBF | 25 MB | 15–40 | **Inferido** desde el set de tags |
| 3 | GeoJSON | 180 MB | 120–300 | **Inferido** + referencia santa_fe |
| 4 | **MBTiles** | **60 MB** | **40–110** | **Extrapolado** desde santa_fe real |

### 5.1 Cadena de referencia real (medida en este equipo)

```
santa_fe.geojson   315,0 MB  (1.149.012 features)
        ↓ tippecanoe -Z8 -z14 --drop-densest-as-needed
santa_fe.mbtiles   121,0 MB
        ratio observado = 0,384
```

Distribución de tiles por zoom en la referencia (evidencia de por qué z14
domina el tamaño):

| Zoom | Tiles | Bytes | MB |
|---|---:|---:|---:|
| 8 | 44 | 2.147.692 | 2,0 |
| 9 | 109 | 3.040.363 | 2,9 |
| 10 | 298 | 4.487.599 | 4,3 |
| 11 | 894 | 6.786.501 | 6,5 |
| 12 | 2.896 | 13.140.848 | 12,5 |
| 13 | 10.028 | 26.121.827 | 24,9 |
| 14 | 36.527 | 52.107.992 | 49,7 |
| **Total** | **50.796** | **107.832.822** | **102,8** |

### 5.2 Por qué el MBTiles final sigue siendo lo más incierto

Su tamaño depende de decisiones **que el Director todavía no tomó**:
set final de tags, zoom máximo (z14 vs z15/z16), simplificación, y
una capa vs varias. El rango 40–110 MB refleja esa incertidumbre;
**no es un dato**. Se convierte en dato duro midiendo en misión B.

### 5.3 Coincidencia notable (verificación cruzada)

El `bounds` de la referencia `santa_fe.mbtiles` es
`[-65.5186, **-34.7893**, -58.2532, -22.1491]`.

Su `min_lat` = **−34,7893** es casi idéntico a nuestro `min_lat` calculado
= **−34,7892**. Dos cálculos independientes (el del autor de la referencia
y el nuestro) convergen al mismo borde sur. **Refuerza la validez del
método de cálculo del bbox.**

---

## 6. Supuestos, mediciones e inferencias

### 6.1 MEDIDO (evidencia observada en esta misión)

- Hash SHA256 del backup → coincide con el esperado.
- Nodos / ways / relations totales (59.348.185 / 5.900.717 / 88.563).
- Nodos dentro del bbox: **7.718.144** (13,00 % del total).
- Highways dentro del bbox: **385.728**.
- Geometría real de AP01, RN9, RN11, RN8 (lat/lon por banda).
- Coordenadas de Santa Fe y CABA (nodos OSM identificados).
- Tamaños de `santa_fe.geojson` (315,0 MB) y `santa_fe.mbtiles` (121,0 MB).
- Comando exacto que generó la referencia (está en sus metadatos).
- Validez sintáctica de las 30+ expresiones de filtro.

### 6.2 INFERIDO

- Que el factor PBF→GeoJSON está en el orden de 6–10×.
- Que el filtro de tags reduce el extract a ~1/3.
- Que el corredor, siendo la zona más densa del país, tiene densidad de
  datos **mayor** que el promedio nacional (por eso la estimación por área
  pura — que daría ~16 MB de MBTiles — **subestima** y fue descartada).

### 6.3 ASUMIDO

- Que las anclas Santa Fe y CABA representan los extremos del viaje
  (no se midió un origen/destino exacto a nivel de calle).
- Que el semiancho de 50 km es perpendicular al eje en todo su recorrido
  (se implementó como expansión de bbox, que es una **envolvente**, no una
  banda geodésica estricta — ver §7).
- Que las 4 coordenadas de ciudad usadas como verificación (Rosario,
  San Nicolás, Zárate) son correctas a nivel de referencia general.

---

## 7. Incertidumbres explícitas

| # | Incertidumbre | Impacto | Cómo se resuelve |
|---|---|---|---|
| I-1 | **El envelope del enunciado no coincide con los márgenes de 20 km** | Decide el bbox final | **Decisión humana** — §8 |
| I-2 | El bbox es una **envolvente**, no una banda de 50 km perpendicular al eje | En las esquinas se incluye más de 50 km; en el centro, exactamente 50 km | Aceptable para el objetivo declarado ("testear tolerancia de volumen"). Si se quisiera banda estricta, habría que generar un polígono y usar `osmium extract -p` |
| I-3 | Estimación de MBTiles | 40–110 MB | Medir en misión B |
| I-4 | No se midió el GeoJSON real del corredor | 120–300 MB | Requiere ejecutar el extract (prohibido en misión A) |
| I-5 | El bbox de datos del backup es anómalamente amplio (+7,25 lat) | Ninguno (no se usa para recortar) | Reportado por transparencia |
| I-6 | No se pudo determinar si hay datos fuera de Argentina que contaminen el extract | Bajo | El extract usa nuestro bbox, acotado a Argentina |

---

## 8. PUNTO QUE REQUIERE DECISIÓN HUMANA

### El envelope del enunciado contradice los márgenes de 20 km

El enunciado, en la sección de verificación, establece como requisito duro:

```
min_lat <= -34.9     y     max_lat >= -31.3
```

Pero las **decisiones humanas ya tomadas** fijan:

```
margen norte = 20 km   →  max_lat = -31.4390
margen sur   = 20 km   →  min_lat = -34.7892
```

**Ambas cosas no pueden ser verdad al mismo tiempo.** La diferencia:

| Extremo | Con margen 20 km | Requisito del enunciado | Diferencia |
|---|---|---|---|
| Norte | −31,4390 | −31,3000 | **0,1390° ≈ 15,5 km** |
| Sur | −34,7892 | −34,9000 | **0,1110° ≈ 12,4 km** |

Para satisfacer el envelope literal habría que usar márgenes de
**~35,5 km al norte** y **~32,3 km al sur**, no 20 km.

**Opciones (el Director decide):**

- **Opción A — Margen 20 km (fiel a la decisión).**
  Bbox `-61.5439126, -34.7892201, -57.8418874, -31.4390329`.
  No cumple el envelope literal del enunciado.

- **Opción B — Envelope literal (fiel al requisito de verificación).**
  Bbox `-61.5439126, -34.9, -57.8418874, -31.3`.
  Área ~139.000 km² (+8 %). Cumple ambas verificaciones del enunciado.

- **Opción C — Margen 35 km simétrico.**
  Intermedio; cubre el envelope con margen parejo.

> **Recomendación de la IA (no vinculante):** Opción B. El propio enunciado
> pide verificar explícitamente `min_lat <= -34.9` y `max_lat >= -31.3`, y
> el costo (~+8 % de área) es bajo frente al riesgo de que el recorte quede
> corto. Pero es una decisión del Director, no de la IA.

**Los entregables están construidos con la Opción A** (fiel a la decisión
declarada). Si el Director elige B, solo hay que reemplazar la variable
`BBOX` en `commands_final.sh` por
`-61.5439126,-34.9,-57.8418874,-31.3` — **nada más cambia**.

---

## 9. Contradicciones encontradas y cómo se trataron

| # | Contradicción | Tratamiento |
|---|---|---|
| C-1 | Envelope del enunciado vs márgenes de 20 km | **Detenido y reportado** (§8). No se eligió por cuenta propia. |
| C-2 | `ref=RN1V09` aparece en dos lugares distintos del país | Reportado (§2.3). Se descartó como filtro; el corredor se define por bbox. |
| C-3 | El tramo SF→Rosario no es `ref=RN9` sino `ref=AP01` | Reportado (§2.3). Corrige un supuesto que habría roto el filtrado. |
| C-4 | Bbox de datos (+7,25 lat) vs bbox de header (−21,73 lat) | Reportado (§1.3). No afecta el recorte. |

### 9.1 Nota de auditoría — un error propio detectado y corregido

Durante la misión, el lector PBF propio que se escribió para analizar el
archivo produjo primero **resultados incorrectos**: reportaba el conteo
total de nodos correcto (59.348.185) pero **IDs y coordenadas equivocados**.

La causa: en OSM PBF, los campos `id`, `lat` y `lon` de `DenseNodes` son
`sint64` **delta-encoded con zigzag**, no varints planos. El error fue
detectado al comparar contra `osmium cat` (que devolvía node `n3`, mientras
el lector devolvía `n6`).

Corregido y **validado de nuevo contra osmium**: IDs, coordenadas y conteos
coinciden exactamente. *Todos los números de este informe provienen del
lector ya corregido.* Se documenta porque la regla del proyecto es
"evidencia antes que certeza" y porque el error afectaba silenciosamente
a los conteos por área.

---

## 10. Entregables producidos

| Archivo | Contenido |
|---|---|
| `CORRIDOR_FINAL.md` | Este documento |
| `corridor_final.json` | Bbox, metadatos, rutas, márgenes, justificación |
| `commands_final.sh` | Comandos exactos para misión B (NO ejecutados) |
| `size_estimates.csv` | Estimaciones con base explícita por paso |
| `EVIDENCE.md` | Comandos de lectura ejecutados y hallazgos |
| `corridor_tags.txt` | Expresiones de filtro (sintaxis validada) |

### Evidencia de soporte (generada en esta misión)

| Archivo | Contenido |
|---|---|
| `lib_pbf.py` | Lector PBF propio (validado contra osmium) |
| `analyze_highways.py` | Conteo de highways por tipo |
| `analyze_rn9_geometry.py` | Geometría de RN9/RN11/RN8 |
| `corridor_axis.py` | Eje real medido AP01+RN9 |
| `bbox_final.py` | Cálculo del bbox |
| `highway_analysis.json` | Resultado crudo de conteos |
| `rn_geometry.json` | Resultado crudo de geometría |
| `corridor_axis.json` | Perfil latitudinal del eje |
| `bbox_final.json` | Resultado crudo del bbox |
| `counts_bbox.json` | Nodos en el bbox |
| `fileinfo_e.txt` | Salida de `osmium fileinfo -e` |
| `tag_counts.txt` | Validación de expresiones de filtro |
| `.backup_sha256.txt` | Hash verificado |

---

## 11. Qué NO se hizo (restricciones respetadas)

- ❌ No se ejecutó `osmium extract`
- ❌ No se ejecutó `osmium tags-filter` con salida a archivo
- ❌ No se ejecutó `tippecanoe`
- ❌ No se generó ningún MBTiles
- ❌ No se modificó el PBF original
- ❌ No se instalaron paquetes
- ❌ No se descargó de internet
- ❌ No se tocó configuración, servicios, firewall ni systemd
- ❌ No se hizo `git commit`
- ❌ No se escribió nada fuera de `sandbox_corredor/`
- ❌ No se accedió a secretos, API keys ni credenciales

---

## 12. Criterio de éxito

El Director puede leer este documento + `commands_final.sh` y decidir
**"autorizo la misión B"** resolviendo **una sola cosa**: el envelope de
latitud (§8). Todo lo demás está calculado y verificado.

**Instrucción operativa:** si elige la Opción A (ya construida), no hay que
cambiar nada. Si elige la Opción B, reemplazar una línea (`BBOX`) en
`commands_final.sh`.
