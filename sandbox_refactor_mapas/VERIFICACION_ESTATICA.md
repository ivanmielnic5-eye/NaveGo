# VERIFICACION_ESTATICA.md — Refactor de mapas Fase 1

**Alcance:** verificaciones ejecutables **sin compilar ni correr la app**.
**Fecha de ejecucion:** 2026-09-22
**Entorno:** `/home/ivan/navego_recuperado`, rama `experimento-dsh-01`,
`typescript 5.9.x` (local en `node_modules/.bin/tsc`).
**Regla:** solo se reporta lo observado. Lo inferido va marcado como
inferencia.

Todas las verificaciones se corrieron sobre los archivos del sandbox
(`sandbox_refactor_mapas/`), **nunca** sobre el repo real.

---

## A. `tsc --noEmit`

### A.1 Resultado sobre el refactor

Los archivos del sandbox se copiaron a un directorio temporal aislado
(`/tmp/tscheck_<pid>/new/`), con un `tsconfig.json` que extiende
`expo/tsconfig.base` y `strict: true` (igual al del repo), y symlinks a
`node_modules` para resolver tipos. Se crearon stubs vacios de
`assets/maptest/*.mbtiles` para que los `require` resuelvan.

Salida observada:

```
error TS2322: Type '{ visible: boolean; }' is not assignable to type
'IntrinsicAttributes & UserLocationProps'.
Property 'visible' does not exist on type
'IntrinsicAttributes & UserLocationProps'.
```

### A.2 Baseline sobre los ORIGINALES (control)

Misma prueba, con `components/MapaOffline.tsx` y `components/MapaLocal.tsx`
**originales**, sin refactor:

```
error TS2322: Type '{ visible: boolean; }' is not assignable to type
'IntrinsicAttributes & UserLocationProps'.
Property 'visible' does not exist on type
'IntrinsicAttributes & UserLocationProps'.
```

### A.3 Conclusion (comparacion normalizada)

Comparando los conjuntos de errores normalizados (se descarto el numero de
linea, que cambia por el refactor):

```
$ diff eo.txt en.txt
>>> IDENTICOS
```

**Resultado: el refactor NO introduce errores de tipo nuevos.**

**HALLAZGO — error preexistente:** los 2 errores `TS2322` sobre
`UserLocation visible={...}` **ya existen en el codigo original**. No son
causados por este refactor. Afectan a `MapaOffline.tsx:161` y
`MapaLocal.tsx:131` en el original.

> **Nota para el humano:** el criterio "`tsc --noEmit` sin errores" del
> diseno (paso 1/2/3) **no se cumple hoy ni antes del refactor**. El
> criterio correcto es "los mismos 2 errores preexistentes, 0 nuevos".
> Arreglar esos 2 errores es un cambio aparte, fuera de esta mision
> (tocaria `UserLocation`, que no esta en el scope autorizado).
> **No lo toque.**

### A.4 `config/mapas.ts` aislado

```
$ tsc --noEmit --strict --skipLibCheck --target es2019 \
      --moduleResolution bundler --module esnext config/mapas.ts
[exit: 0]
```

**Resultado: `config/mapas.ts` typechequea limpio, 0 errores.**

---

## B. Grep — hardcodes remanentes

Sobre `sandbox_refactor_mapas/components/`:

| Patron buscado | Coincidencias | Resultado |
|---|---|---|
| `santa_fe.mbtiles` | 0 | OK |
| `'santa_fe'` | 0 | OK |
| `"santa_fe"` | 0 | OK |
| `require(` | 0 | OK |

**No quedan hardcodes de santa_fe ni `require` en los componentes.**

### B.1 `PUERTO` declarado una sola vez

```
config/mapas.ts:19:  export const PUERTO = 8080;      <- unica DECLARACION
```

En los componentes solo aparece como **uso** o **import**:

```
MapaOffline.tsx:8   import { getMapaActivo, PUERTO } from '../config/mapas';
MapaOffline.tsx:80  await server.start(PUERTO, ...)
MapaOffline.tsx:97  `http://127.0.0.1:${PUERTO}/${mapa.id}/...`
MapaLocal.tsx:9     import { getMapaActivo, PUERTO } from '../config/mapas';
MapaLocal.tsx:52    await server.start(PUERTO, ...)
MapaLocal.tsx:72    console.log('[ML] Server en', PUERTO);
MapaLocal.tsx:74    `http://127.0.0.1:${PUERTO}/${mapa.id}/...`
```

**Resultado: PUERTO desduplicado. Cumple CAMBIO 3 del diseno.**

---

## C. Mismo patron en ambos componentes

Ocurrencias del patron del descriptor:

| Uso | MapaOffline | MapaLocal |
|---|---|---|
| `import { getMapaActivo, PUERTO }` | linea 8 | linea 9 |
| `const mapa = getMapaActivo();` | 13 | 14 |
| `const DB_NAME = mapa.archivo;` | 14 | 15 |
| `const SOURCE_LAYER = mapa.sourceLayer;` | 16 | 17 |
| `const CENTER_DEFAULT = mapa.center;` | 17 | 18 |
| `const MINZOOM = mapa.minzoom;` | 18 | 19 |
| `const MAXZOOM = mapa.maxzoom;` | 19 | 20 |
| `Asset.fromModule(mapa.asset)` | 68 | 38 |
| URL `${mapa.id}` | 97 | 74 |

**Resultado: ambos componentes siguen exactamente el mismo patron.**

---

## D. Regex del server — identica y funcional

```
MapaOffline.tsx:82  path.match(/^\/([^\/]+)\/(\d+)\/(\d+)\/(\d+)\.pbf$/)
MapaLocal.tsx:54    path.match(/^\/([^\/]+)\/(\d+)\/(\d+)\/(\d+)\.pbf$/)
```

**Resultado: regex byte-identica en ambos.**

Prueba funcional del regex con Node (comportamiento observado):

| Path de entrada | Regex nuevo | Grupos extraidos | Regex viejo |
|---|---|---|---|
| `/santa_fe/10/339/606.pbf` | MATCH | mapaId=santa_fe z=10 x=339 y=606 | no |
| `/corredor_sf_caba/10/339/606.pbf` | MATCH | mapaId=corredor_sf_caba z=10 x=339 y=606 | no |
| `/10/339/606.pbf` | no (404) | — | MATCH |
| `/santa_fe/10/339/606.png` | no (404) | — | no |
| `/santa_fe/a/339/606.pbf` | no (404) | — | no |
| `//10/339/606.pbf` | no (404) | — | no |
| `/santa_fe/10/339/606.pbf?x=1` | no (404) | — | no |

**Observaciones:**
- El namespacing funciona: ambos mapas producen paths distintos y parseables.
  Esto es la base del CAMBIO 1 (evitar mezcla de cache).
- El formato viejo `/10/339/606.pbf` **deja de matchear** (404). Es
  intencional: la URL que se pasa a MapLibre tambien cambio, asi que el
  cliente pide siempre la ruta nueva. **Inferencia:** no hay consumidor
  externo de la ruta vieja dentro del repo (no se encontro ninguno con
  grep), asi que no deberia romper nada.
- El caso con query string (`?x=1`) da 404. **Es identico al comportamiento
  anterior** (el regex viejo tambien era estricto y anclado con `$`), por lo
  que **no es una regresion introducida por el refactor**. Ver Incertidumbre
  I-3 del `REVIEW.md`.

---

## E. `aGeoJSON` y logica no tocada — diff de bloques

Se extrajo el bloque `function aGeoJSON(...)` de original y sandbox y se
comparo:

```
--- MapaOffline
    aGeoJSON IDENTICO
--- MapaLocal
    aGeoJSON IDENTICO
```

**Resultado: `aGeoJSON` es byte-identica en ambos archivos.**

Ademas, el `diff -u` completo (ver `REVIEW.md` §2) muestra que los unicos
bloques modificados son:
import, bloque de constantes, origen del asset, regex + indices de grupo,
URL `setUri`, y `minzoom/maxzoom` del source. **Ningun `useEffect`, ningun
`useImperativeHandle`, ninguna capa de estilo, ni el codigo de ubicacion de
`MapaLocal` fueron alterados.**

---

## F. Prueba funcional de `config/mapas.ts`

Se transpilo el modulo a CommonJS (reemplazando los `require` de assets
`.mbtiles` por un stub, ya que Node no puede cargarlos) y se ejercito la
API:

```
PUERTO           : 8080
disponibles      : [ 'santa_fe', 'corredor_sf_caba' ]
activo (default) : santa_fe | sourceLayer: santa_fe | center: [-60.7,-31.63]
                   | version: 2026-09-20 | archivo: santa_fe.mbtiles
tras set         : corredor_sf_caba | sourceLayer: corredor
                   | center: [-60.65,-32.95] | version: 2026-09-22
                   | archivo: corredor_sf_caba.mbtiles
set invalido     : OK lanza -> Mapa no encontrado: no_existe.
                   Mapas disponibles: santa_fe, corredor_sf_caba
vuelto a santa_fe: santa_fe
```

**Resultado:**
- D-1 aplicado: center del corredor = `[-60.65, -32.95]` (Rosario).
- D-2 aplicado: default = `santa_fe`.
- Criterio 5 del diseno cumplido: id invalido lanza error claro con lista
  de validos.

---

## G. Consistencia de los descriptores contra los `.mbtiles` reales

Verificado leyendo la tabla `metadata` de cada archivo con `sqlite3` (Python):

| Campo | descriptor santa_fe | mbtiles real | ¿coincide? |
|---|---|---|---|
| `sourceLayer` | `santa_fe` | vector_layers = `['santa_fe']` | **SI** |
| `archivo` | `santa_fe.mbtiles` | `assets/maptest/santa_fe.mbtiles` existe | **SI** |
| minzoom / maxzoom | 8 / 14 | metadata 8 / 14 | **SI** |

| Campo | descriptor corredor | mbtiles real | ¿coincide? |
|---|---|---|---|
| `sourceLayer` | `corredor` | vector_layers = `['corredor']` | **SI** |
| `archivo` | `corredor_sf_caba.mbtiles` | existe en `sandbox_corredor/out_mision_b/`, **NO** en `assets/maptest/` | **NO — ver H** |
| minzoom / maxzoom | 8 / 14 | metadata 8 / 14 | **SI** |

Nota: el `center` del metadata del `.mbtiles` del corredor es
`-58.392334,-34.587997` (CABA), pero el descriptor usa `[-60.65, -32.95]`
por **decision explicita del Director (D-1 = b, Rosario)**. No es un error:
es la decision tomada, y el campo `center` del descriptor es de vista
inicial, no metadata del tileset.

---

## H. VERIFICACION BLOQUEANTE — asset del corredor

```
$ test -f assets/maptest/corredor_sf_caba.mbtiles && echo SI || echo NO
NO EXISTE

$ ls -1 assets/maptest/
navigation.sqlite
render_big.mbtiles
render.mbtiles
santa_fe.mbtiles
test_hibrido.mbtiles

$ ls -la sandbox_corredor/out_mision_b/*.mbtiles
-rw-r--r-- 1 ivan ivan ... corredor_sf_caba.mbtiles

$ git check-ignore -v assets/maptest/corredor_sf_caba.mbtiles
.gitignore:89:*.mbtiles   assets/maptest/corredor_sf_caba.mbtiles
$ git check-ignore -v sandbox_corredor/out_mision_b/corredor_sf_caba.mbtiles
.gitignore:87:sandbox_corredor/out_mision_b/   ...
```

**Resultado: BLOQUEANTE.** El asset que el `require` del descriptor espera
no existe en la ruta declarada. **Antes de aplicar hay que copiarlo** (o
aceptar que la entrada `corredor_sf_caba` queda rota, ya que el default es
`santa_fe`).

Comando sugerido (a ejecutar por el humano, **no ejecutado por la IA**):

```bash
cp sandbox_corredor/out_mision_b/corredor_sf_caba.mbtiles assets/maptest/
```

---

## I. Resumen de criterios

| # | Verificacion estatica | Resultado |
|---|---|---|
| A | `tsc --noEmit` sin errores **nuevos** | ✅ 0 nuevos (2 preexistentes) |
| A.4 | `config/mapas.ts` aislado | ✅ 0 errores |
| B | Sin hardcodes `santa_fe` / `require` en componentes | ✅ 0 coincidencias |
| B.1 | `PUERTO` declarado una sola vez | ✅ 1 sola vez |
| C | Ambos componentes con el mismo patron | ✅ si |
| D | Regex identica + funcional (namespacing) | ✅ si |
| E | `aGeoJSON` / useEffect / estilo intactos | ✅ identicos |
| F | API de `mapas.ts` (default, set, error) | ✅ correcta |
| G | Descriptores consistentes con metadata real | ✅ (salvo ruta asset) |
| H | Asset del corredor en la ruta esperada | ❌ **BLOQUEANTE** |

### Lo que esta verificacion NO cubre

- Que la app arranque y muestre el mapa (requiere APK).
- Que el server sirva tiles reales en el celu (criterio 6 del diseno).
- Que el cambio de mapa en caliente funcione (criterio 7).
- Que no haya mezcla de tiles en la practica (criterio 6).
- Rendimiento en TCL T610P (hipotesis H-2026-0001, fuera de alcance).

**No se afirma exito de nada que no se haya observado.**
