# work_hypothesis.md — Hipótesis de trabajo del corredor

**Proyecto:** NaveGo
**Viaje:** Santa Fe Capital -> Buenos Aires (CABA)
**Modo:** **AUTO — ruta terrestre** (no navegación acuática)
**Rol:** este documento explica **CÓMO se pensó el corredor**, no solo dónde.
**Estado:** hipótesis. **No es una decisión.** Decide el Director Ivan.

---

## 0. Advertencia que condiciona todo

El PBF objetivo (`~/cockpit/argentina-latest.osm.pbf`) **no contiene ways ni
relations** (ver `EVIDENCE.md` y `CORRIDOR_PROPOSAL.md`, sección A). Por lo tanto:

- **Todo lo que sigue sobre rutas es INFERENCIA GEOGRÁFICA**, construida a partir
  de coordenadas de ciudades y conocimiento de la red vial argentina.
- **Nada de lo que sigue está medido sobre trazas del PBF.**
- Antes de ejecutar cualquier recorte, hay que **verificar la hipótesis contra
  datos reales** (idealmente sobre el backup íntegro).

Marco cada afirmación como **[OBSERVADO]**, **[INFERENCIA]** o **[PROPUESTA]**.

---

## 1. El problema, en una frase

> Necesitamos un recorte de OSM que permita navegar **en auto** desde Santa Fe
> hasta Buenos Aires, que **quepa** en el dispositivo, y que **siga sirviendo
> si la ruta principal se corta**.

Esa última cláusula ("si se corta") es la que manda: es la diferencia entre un
recorte **de una línea** y un recorte **de un corredor**.

---

## 2. Cómo se pensó el corredor — razonamiento paso a paso

### Paso 1 — ¿Qué forma tiene el problema?

Un viaje por auto entre dos ciudades no es una **línea**, es una **franja**.
Si recortás solo la traza de la ruta elegida:

- el mapa funciona mientras esa ruta esté abierta;
- el día que hay un corte (obra, inundación, accidente, piquete), **no hay mapa
  para el desvío**.

Conclusión de diseño: **el recorte debe ser una franja (corredor), no una línea.**
Esto es una **[PROPUESTA]** de diseño, y es la decisión estructurante de todo el resto.

### Paso 2 — ¿Qué define el ancho de la franja?

Si el ancho es arbitrario, el recorte es arbitrario. El ancho tiene que salir de
una **pregunta operativa**:

> ¿Cuál es la ruta alternativa más cercana que quiero tener disponible?

En este viaje, la respuesta geográfica es **RN 11**. Entonces:

```
semiancho_minimo  >  separación entre RN 9 (eje) y RN 11 (alternativa)
```

Si el semiancho es menor que esa separación, **la alternativa queda fuera del
mapa** y el recorte no cumple su propósito. Si es mucho mayor, se paga tamaño
por datos que no se usan.

**Estimación [INFERENCIA]:** la separación RN 9 / RN 11 en el tramo
Rosario -> Zárate es del orden de **40-60 km**, juzgando por las posiciones de
Rosario, San Pedro y Zárate.

De ahí sale el **semiancho de 50 km** como hipótesis principal: es el **mínimo
que hace que RN 11 exista dentro del recorte**.

> **INCERTIDUMBRE CLAVE:** esa separación **no fue medida**. Es el supuesto más
> importante de toda la propuesta. Si la separación real fuera, por ejemplo,
> 70 km, el candidato C2 quedaría corto y habría que ir a C3. **Esto debe
> verificarse antes de decidir.**

### Paso 3 — ¿Cuál es el eje? ¿Por qué RN 9?

Criterios aplicados, en orden de peso:

| # | Criterio | Por qué favorece a RN 9 |
|---|---|---|
| 1 | **Continuidad** | Es el eje histórico y de mayor jerarquía SF -> Rosario -> CABA |
| 2 | **Tiempo** | Concentra los tramos de autopista (Rosario-Bs.As., Acceso Norte) |
| 3 | **Servicios** | Rosario, San Nicolás, Zárate, CABA: cobertura densa |
| 4 | **Redundancia** | Existe RN 11 como paralela -> hay plan B |
| 5 | **Simplicidad de prueba** | Un eje único y claro es más fácil de validar |

**Contra-criterio honesto [INFERENCIA]:** RN 9 atraviesa zonas de **congestión
alta** (Rosario, Acceso Norte al AMBA). RN 11 suele ser **más descongestionada
pero más lenta**. La elección entre ambas depende de si la prioridad es
**tiempo** o **previsibilidad** — y eso es una decisión humana, no técnica.

**Corrección de encuadre importante [INFERENCIA]:**
La consigna menciona RN 9, RN 11, RN 33, RN 34, RN 8 y RN 19. **No todas son
alternativas del mismo viaje.** Es un error frecuente tratarlas como si lo fueran:

- **RN 34** es un eje **norte-sur del oeste** (Rosario -> Santiago del Estero).
  **No sirve** para ir a Buenos Aires.
- **RN 33** va de Rosario hacia el **sudoeste** (Río Cuarto). **No es** eje SF->CABA.
- **RN 19** conecta **Córdoba con Santa Fe**. **Alimenta** el corredor, no es eje.
- **RN 8** conecta Pergamino con Buenos Aires. **Alternativa parcial** al sur.

Solo **RN 9 (eje)** y **RN 11 (alternativa)** son las dos piezas centrales.
Marcar esto evita proponer un corredor mal formado.

### Paso 4 — ¿Qué features hacen falta para navegar en auto?

El principio: **incluir lo que se usa para conducir y decidir; excluir lo que
solo ocupa lugar.**

**Se incluye (ALTA prioridad):**
- **Ways con `highway`** = motorway, trunk, primary, secondary, tertiary (+ links).
  Son la red por la que se circula.
- **`name` y `ref`** — sin etiquetas, el mapa es una telaraña sin nombres.
  Para navegación humana, "RN 9" tiene que leerse.
- **`oneway`, `maxspeed`, `bridge`, `tunnel`, `surface`** — afectan conducción,
  ETA y decisiones.
- **Nodos referenciados por esas ways** — sin ellos las ways no tienen geometría.

**Se incluye (MEDIA prioridad — seguridad y logística):**
- **Localidades** (`place=city/town/village`) — referencia humana y de ruteo.
- **`amenity=fuel`** — en un viaje de ~400 km, saber dónde cargar es crítico.
- **`amenity=hospital`** — seguridad del viaje.
- **`highway=rest_area`/`services`**, policía, comida, hoteles, supermercados.

**Se excluye (para esta prueba):**
- **Edificios** — volumen enorme, valor nulo para navegar una ruta.
- **`landuse`**, hidrografía menor, árboles, mobiliario — ruido.
- **Transporte público** — el viaje es en auto.

> **Nota de alcance:** como el viaje es **terrestre**, **no** se prioriza
> hidrografía navegable, puertos ni faros. Un corredor acuático tendría otro
> conjunto de tags. Acá el encuadre es vial.

### Paso 5 — ¿Cómo se elige entre los tres candidatos?

No se elige acá. Se ofrecen tres **anchos** porque representan tres **posturas
de riesgo** distintas:

- **C1 (20 km):** "confío en que RN 9 esté abierta". Mapa chico, sin plan B.
- **C2 (50 km):** "quiero un plan B real". Equilibrio.
- **C3 (90 km):** "quiero tolerar un corte grave". Máxima cobertura, máximo costo.

Elegir es decidir **cuánto riesgo de corte se está dispuesto a tolerar** — es una
decisión del Director, no de la IA.

---

## 3. Alternativas si la ruta principal se corta

**[PROPUESTA]** — no es ruteo calculado; es un plan a validar.

| Escenario | Desvío natural | Comentario |
|---|---|---|
| Corte RN 9 entre Rosario y San Nicolás | **RN 11** por el este (vía San Pedro), reingreso en Zárate | Desvío primario, el más barato |
| Corte RN 9 al norte de Rosario | RN 33/RN 34 al oeste, reingreso por RN 19/RN 8 | Desvío largo, alto costo de tiempo |
| Corte en Acceso Norte / AMBA | RN 8 (Pergamino -> Buenos Aires) o RN 11 / Panamericana | Entrada alternativa al AMBA |
| Bloqueo total del corredor este | RN 33 -> RN 8 | Último recurso |

**El desvío natural primario es RN 11.** Es la alternativa más corta y de menor costo.

> **INCERTIDUMBRE:** no se pudo confirmar que exista conexión física entre RN 9 y
> RN 11 en cada punto de corte, ni la transitabilidad. Sin ways, no hay verificación.

---

## 4. Riesgos y huecos de datos

### Bloqueantes (confirmados por medición)

1. **El PBF objetivo no tiene ways ni relations** — sin rutas no hay corredor.
2. **Solo tiene 84,1 % de los nodos** — la geometría estaría incompleta aun si
   hubiera ways.

### Altos (no verificados)

3. **No se verificó que el backup íntegro cubra bien el corredor.** Comparte
   header y snapshot con el objetivo, lo cual es buena señal, pero **no se
   inspeccionó su contenido vial**.

### Huecos que limitan la propuesta

4. No se midió la traza real de ninguna ruta.
5. No se midió la **separación RN 9 / RN 11** (supuesto clave de C2).
6. No se verificó presencia ni calidad de combustibles/hospitales en el corredor.
7. No se estimó el tamaño de MBTiles con base empírica.

---

## 5. Incertidumbres explícitas

| # | Incertidumbre | Impacto | Cómo se resolvería |
|---|---|---|---|
| I1 | Separación real RN 9 / RN 11 | Define si C2 alcanza | Medir sobre PBF íntegro |
| I2 | Traza real de RN 9 vs eje recto | Valida la forma de los bbox | Medir sobre PBF íntegro |
| I3 | Cobertura vial del backup | Define si sirve | `osmium fileinfo -e` + conteo por bbox |
| I4 | Conectividad RN 9 <-> RN 11 | Valida el plan B | Análisis de red sobre ways |
| I5 | Tamaño real del MBTiles | Define si entra en el equipo | Generar y medir (etapa posterior) |
| I6 | Causa del truncamiento | ¿re-descargar o usar backup? | Decisión del Director |
| I7 | Densidad de POIs útiles | Ajusta el filtro | Medir sobre PBF íntegro |

---

## 6. Qué haría falta para pasar de hipótesis a propuesta verificada

1. Validar el backup íntegro: `osmium fileinfo -e`.
2. Extraer el corredor **solo para medir** (no para producir MBTiles).
3. Medir la separación real RN 9 / RN 11 en el tramo Rosario -> Zárate.
4. Ajustar el semiancho con ese número, en vez del supuesto de 50 km.
5. Verificar que existan `amenity=fuel` y `amenity=hospital` en cantidad
   razonable sobre el eje.
6. Recién entonces estimar tamaño de MBTiles con base empírica.

**Nada de esto se ejecutó** — está fuera del alcance autorizado de esta tarea.

---

## 7. Resumen de la hipótesis

> **Recortar** una franja Santa Fe -> CABA sobre el eje **RN 9**, con
> **semiancho ~50 km**, incluyendo la red `highway` (motorway/trunk/primary/
> secondary/tertiary) con `name`/`ref`, más localidades, combustibles,
> hospitales y áreas de servicio; tomando **RN 11** como desvío natural y
> **RN 8** como acceso alternativo al AMBA.
>
> **Fundamento del ancho:** es el mínimo que mantiene RN 11 dentro del mapa.
> **Punto débil:** esa separación está estimada, no medida.
> **La IA no elige entre C1, C2 y C3.**
