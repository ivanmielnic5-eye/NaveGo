# REVIEW.md — Capa de borde provincial (`provincias`)

**Mision:** A (preparacion) — NO aplicado al repo.
**Fecha:** 2026-09-22
**Tarea:** Agregar capa de borde provincial al mapa.
**Sandbox:** `~/navego_recuperado/sandbox_refactor_provincias/`
**Base normativa:** EXPEDIENTE/28_DISENO_CAPAS_TEXTO.md

**ESTADO: PREPARADO — PENDIENTE DE APLICACION POR EL HUMANO.**

> REGLA FUNDAMENTAL: la IA prepara, la IA no aplica.
> Ningun archivo real del repo fue modificado.

---

## Que hace este cambio

Agrega **UNA** capa nueva de tipo `line` al array `layers` del estilo
MapLibre, que dibuja los **bordes de provincia** (`admin_level=4`).

Es un cambio UNICO y aditivo: no se modifica ninguna capa existente,
no se toca ningun otro archivo.

---

## Archivos producidos

| Archivo | Estado |
|---|---|
| `components/MapaOffline.tsx` | Version nueva (no aplicada) |
| `components/MapaLocal.tsx` | Version nueva (no aplicada) |
| `REVIEW.md` | Este archivo |

**NO se toco:** `config/mapas.ts`, `metro.config.js`, los MBTiles,
ningun otro componente, ningun archivo real del repo.
**NO** se instalo nada. **NO** se hizo commit. **NO** se toco `main`.

---

## El cambio, textual

Insertado **despues de `lineas`** y **antes de `municipios`**, en los
DOS archivos, identico:

```ts
    {
      id: 'provincias', type: 'line', source: 'local', 'source-layer': SOURCE_LAYER,
      filter: ['all', ['==', ['get', 'admin_level'], '4'], ['==', ['get', 'boundary'], 'administrative'], ['has', 'name']],
      paint: { 'line-color': '#5a6a7a', 'line-width': 2, 'line-opacity': 0.85 },
    },
```

Mas el comentario de orden, actualizado (no es codigo ejecutable):

```ts
  // background, agua, edificios, lineas, provincias, municipios, barrios,
  // rutas, servicios, trackRefLine, trackActivoLine.
```

---

## Como aplicar (lo hace el humano)

```bash
cd ~/navego_recuperado

# 0. Ver que es exactamente lo que va a cambiar (leer ANTES de aplicar)
diff -u components/MapaOffline.tsx sandbox_refactor_provincias/components/MapaOffline.tsx
diff -u components/MapaLocal.tsx   sandbox_refactor_provincias/components/MapaLocal.tsx

# 1. Backup de los originales
cp components/MapaOffline.tsx components/MapaOffline.tsx.bak_pre_provincias
cp components/MapaLocal.tsx   components/MapaLocal.tsx.bak_pre_provincias

# 2. Aplicar
cp sandbox_refactor_provincias/components/MapaOffline.tsx components/MapaOffline.tsx
cp sandbox_refactor_provincias/components/MapaLocal.tsx   components/MapaLocal.tsx

# 3. Verificar que solo cambiaron esos 2 archivos
git status --porcelain

# 4. Recompilar y ver en el celu
```

---

## Verificacion esperada — resultado real

### V-1 — La capa `provincias` aparece exactamente 1 vez en cada archivo

```
$ grep -c "id: 'provincias'" MapaOffline.tsx MapaLocal.tsx
1
1
```

**PASA.** (1 en cada uno, no 0, no 2.)

### V-2 — El filtro usa `admin_level=4` (no 5,6,7,8)

```
$ grep -c "\['get', 'admin_level'\], '4'" MapaOffline.tsx MapaLocal.tsx
1
1
```

**PASA.** Y las capas `municipios` conservan su `'5','6','7','8'` intacto
(verificado: 1 ocurrencia de `'5', '6', '7', '8'` en cada archivo, sin
cambios). No hay colision de niveles: provincia=4, municipios=5..8.

### V-3 — Orden del array `layers`

Orden real extraido de los archivos (no copiado de la tarea):

**MapaOffline.tsx** — 11 capas:

```
 1. background
 2. agua
 3. edificios
 4. lineas
 5. provincias        <- NUEVO
 6. municipios
 7. barrios
 8. rutas
 9. servicios
10. trackRefLine
11. trackActivoLine
```

**PASA** — coincide exactamente con el orden pedido.

**MapaLocal.tsx** — 9 capas:

```
 1. background
 2. agua
 3. edificios
 4. lineas
 5. provincias        <- NUEVO
 6. municipios
 7. barrios
 8. rutas
 9. servicios
```

**PASA respecto de lo aplicable** — ver D-1 mas abajo.

---

## DIFERENCIAS RESPECTO DE LO PEDIDO (leer antes de aplicar)

### D-1 — MapaLocal.tsx NO tiene `trackRefLine` ni `trackActivoLine`

La tarea pedia un orden final de **11** capas, incluyendo `trackRefLine`
y `trackActivoLine` en las posiciones 10 y 11. **Eso vale para
MapaOffline.tsx, pero NO para MapaLocal.tsx.**

**Evidencia (archivos reales, sin modificar):**

- En `MapaOffline.tsx` esas dos capas se agregan con `layers.push()`
  condicional, fuera del array literal (lineas 258-263 del original),
  porque dependen de `refGeoJSON` / `activeGeoJSON`.
- En `MapaLocal.tsx` **no existe** ningun `layers.push` ni ninguna
  referencia a `trackRef`/`trackActivo`: ese componente no recibe
  `trackPoints` y su estilo termina en `servicios`.

```
$ grep -c "trackRefLine\|trackActivoLine" components/MapaLocal.tsx
0
```

**Decision tomada:** NO invente las capas de track en MapaLocal. Agregar
esas dos capas habria requerido crear sources `trackRef`/`trackActivo`
que no existen en ese componente — un cambio de alcance mayor, fuera del
"cambio UNICO" autorizado. Se aplico la capa `provincias` en la posicion
correcta respecto de las capas que SI existen (despues de `lineas`, antes
de `municipios`).

**Es consistente con el original:** MapaLocal tampoco tenia los tracks
antes de este cambio. No se perdio nada.

**Si el Director quiere los tracks en MapaLocal**, es otra tarea (requiere
pasarle los GeoJSON y crear los sources). Marcar como INCERTIDUMBRE
resuelta por alcance, no por codigo.

### D-2 — La tarea dice "Source: local", el codigo real usa la constante `SOURCE_LAYER`

La tarea especificaba literalmente `source-layer: SOURCE_LAYER`. En los
archivos reales el valor es la constante de modulo:

```ts
const SOURCE_LAYER = mapa.sourceLayer;
```

Es decir, `SOURCE_LAYER` **no es un placeholder a completar**: es el
identificador real ya usado por las 9 (u 8) capas existentes. La capa
nueva usa exactamente el mismo patron que `agua`, `edificios`, `lineas`,
`municipios`, `barrios`, `rutas` y `servicios`.

**No se invento ningun valor.** El `source-layer` efectivo depende del
mapa activo (`santa_fe` → `'santa_fe'`, `corredor_sf_caba` → `'corredor'`,
segun `config/mapas.ts`). Eso es correcto y deseable: la capa funciona en
todos los mapas del catalogo sin hardcodear una capa.

---

## Incertidumbres declaradas (NO inventadas)

### I-1 — El dato `admin_level=4` NO esta verificado por mi en este hilo

La tarea afirma "Verificado: los datos estan en los MBTiles con
admin_level=4". **No pude re-verificar esa afirmacion en esta sesion**
(no ejecute decodificacion de tiles).

Lo que SI encontre en las fuentes declaradas:

- `EXPEDIENTE/28_DISENO_CAPAS_TEXTO.md:281` lista
  `admin_level=4 -> provincia (Rio Parana)` entre los valores
  **observados en tiles reales** durante la verificacion previa
  (seccion "AJUSTE — Hallazgos de la verificacion previa").
- `EXPEDIENTE/28_DISENO_CAPAS_TEXTO.md:34` (diagnostico original, previo
  al ajuste) solo listaba `"5", "9", "10"`. El `4` aparece recien en el
  ajuste posterior. **No hay ambiguedad**, pero tampoco hay evidencia
  cruda adjunta en `EXPEDIENTE/05_EVIDENCIA/` (esa carpeta solo contiene
  `daemon_2026-09-22` y `SESION_2026-09-21`).

**Consecuencia practica:** el filtro tambien exige
`['==', ['get','boundary'], 'administrative']`. Si la geometria de
provincia viniera **sin** el campo `boundary`, la capa quedaria **vacia**
(no rompe nada, pero no dibuja). Ese campo **no** aparece listado en el
diagnostico de campos del doc 28 (que menciona `name`, `admin_level`,
`place`, `amenity`, `highway`, `ref`, etc., pero no `boundary`).

**No lo puedo confirmar ni refutar sin decodificar un tile.** Riesgo: la
capa puede no dibujar nada si `boundary` falta. Es **bajo impacto**
(capa aditiva, no rompe el mapa) y **facil de diagnosticar** (comparar
con/sin ese termino del filtro).

**Recomiendo como prueba minima antes de dar por buena la capa:** extraer
un tile con borde provincial y confirmar que la feature trae
`admin_level=4` **y** `boundary=administrative`. Si falta `boundary`,
quitar ese termino del filtro es un cambio de 1 linea.

### I-2 — No se ejecuto la app

Por restriccion de la tarea. La verificacion visual en el TCL T610P queda
pendiente y es la unica prueba real.

### I-3 — Grosor/color del borde a zoom bajo

`line-width: 2` fijo, sin interpolacion por zoom. A zoom 8-10 (vista
provincial) puede verse fino; a zoom 14 puede verse grueso. Es
exactamente lo pedido, pero **no medido visualmente**.

---

## Verificacion estatica ejecutada

### E-1 — El diff es minimo y solo contiene lo pedido

`diff -u` de cada archivo contra el original: **2 hunks por archivo**.
1. El comentario de orden.
2. El bloque de la capa nueva.

Ninguna otra linea cambio. Verificado tambien por md5 del original antes
de editar.

### E-2 — TypeScript parsea los dos archivos

```
$ tsc --noEmit --jsx react-jsx --esModuleInterop --skipLibCheck \
      --target esnext --module esnext --moduleResolution bundler \
      sandbox_refactor_provincias/components/*.tsx
```

Resultado: **4 errores, y los 4 son pre-existentes.**

| Error | Por que NO es culpa de este cambio |
|---|---|
| `Cannot find module '../config/mapas'` (x2) | El sandbox esta un nivel mas profundo, asi que `../config` no resuelve. Es un artefacto de la ruta del sandbox, no del codigo. |
| `UserLocationProps.visible` (x2) | **Tambien aparece en los archivos originales** (verificado ejecutando tsc sobre `components/*.tsx`). Es un error pre-existente. Solo se corrieron los numeros de linea (+5) por el bloque nuevo. |

Prueba de que es pre-existente — mismo comando sobre los originales:

```
components/MapaLocal.tsx(247,23): error TS2322: ... 'visible' does not exist ...
components/MapaOffline.tsx(281,44): error TS2322: ... 'visible' does not exist ...
```

Mismos 2 errores. **La capa nueva introdujo 0 errores nuevos.**

### E-3 — Balance sintactico

Llaves y corchetes balanceados (0/0) en ambos archivos.

---

## Checklist de revision para el humano

1. [ ] Leer los 2 `diff -u` de la seccion "Como aplicar". Confirmar que
       solo esta la capa nueva + el comentario.
2. [ ] Decidir sobre **D-1**: aceptar que MapaLocal no lleve tracks
       (recomendado) o pedir los tracks como tarea aparte.
3. [ ] Decidir sobre **I-1**: confirmar `boundary=administrative` en los
       tiles antes o despues de aplicar. Si la capa no dibuja, este es el
       primer sospechoso.
4. [ ] Aplicar, recompilar.
5. [ ] Verificar visualmente en el TCL T610P:
       - aparece una linea gris-azulada marcando el limite provincial;
       - el borde queda **debajo** de los nombres de municipios/barrios;
       - el track rojo/azul (en MapaOffline) sigue **arriba** de todo;
       - se ve tanto en `santa_fe` como en `corredor_sf_caba`.
6. [ ] Si NO aparece nada: probar quitar `['==', ['get','boundary'],'administrative']`
       del filtro (ver I-1).
7. [ ] Si todo OK: commit (lo hace el humano).

---

## Trazabilidad de reglas

- **Una intervencion por vez / un cambio a la vez:** una sola capa, dos
  archivos, cambio aditivo.
- **Source of truth:** el array y la constante `SOURCE_LAYER` se leyeron
  de los archivos reales, no se asumieron.
- **No inventar datos que no tengo:** `admin_level=4` se declara como
  *no re-verificado en este hilo* (I-1) en vez de darlo por cierto.
- **Verificar antes de asumir:** se ejecuto `tsc` y se comparo contra la
  linea base de los originales.
- **Semaforo de riesgo:** este cambio es **amarillo** (layout/estilo de
  mapa). No toca GNSS, COG/SOG, distancia, persistencia ni sync (rojo).
- **La IA prepara, la IA no aplica:** ningun archivo real fue modificado.

---

Fin del REVIEW.
