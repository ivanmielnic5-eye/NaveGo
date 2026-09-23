# REVIEW.md — Guia de revision del refactor de mapas (Fase 1)

**Mision:** A (preparacion). **Estado:** PREPARADO, NO APLICADO.
**Fecha:** 2026-09-22
**Fuente de diseno:** `EXPEDIENTE/27b_DISENO_FASE_1_AJUSTADO.md` (D-MAPAS-002)
**Regla:** La IA prepara. La IA no aplica. El humano revisa y aplica.

---

## ⚠️ LEER PRIMERO — BLOQUEANTE DETECTADO

**El archivo `assets/maptest/corredor_sf_caba.mbtiles` NO EXISTE.**

Evidencia (comando y salida observada, 2026-09-22):

```
$ test -f assets/maptest/corredor_sf_caba.mbtiles && echo SI || echo NO
NO EXISTE

$ ls -1 assets/maptest/
navigation.sqlite
render_big.mbtiles
render.mbtiles
santa_fe.mbtiles
test_hibrido.mbtiles
```

El `.mbtiles` del corredor si existe, pero en otra ruta:

```
$ ls -la sandbox_corredor/out_mision_b/*.mbtiles
sandbox_corredor/out_mision_b/corredor_sf_caba.mbtiles   (generado 2026-09-22 18:23)
```

Ademas, `*.mbtiles` esta en `.gitignore` (linea 89), y
`sandbox_corredor/out_mision_b/` tambien (linea 87). Es decir: el asset
**no esta versionado** y **no esta en la ruta que el diseno asume**.

**Consecuencia si se aplica el refactor tal cual, sin copiar el asset:**
`require('../assets/maptest/corredor_sf_caba.mbtiles')` falla en build de
Metro. El refactor esta disenado para que `santa_fe` siga siendo el default
(D-2), asi que **la app arrancaria igual**, pero el catalogo queda con una
entrada rota: cualquier intento de `setMapaActivo('corredor_sf_caba')`
fallaria.

**Accion requerida antes de aplicar (decision humana):**

```bash
mkdir -p assets/maptest
cp sandbox_corredor/out_mision_b/corredor_sf_caba.mbtiles assets/maptest/
```

Nota: `*.mbtiles` esta gitignoreado, asi que este archivo no se versionara.
Eso puede ser lo deseado (126 MB) o no. **Es una decision del Director.**
Ver seccion "Puntos que requieren decision humana".

---

## 1. Archivos producidos

Todos dentro del sandbox. **Nada fue escrito en el repo real.**

| # | Archivo en sandbox | Corresponde a | Tipo |
|---|---|---|---|
| 1 | `sandbox_refactor_mapas/config/mapas.ts` | `config/mapas.ts` | **NUEVO** |
| 2 | `sandbox_refactor_mapas/components/MapaOffline.tsx` | `components/MapaOffline.tsx` | MODIFICADO |
| 3 | `sandbox_refactor_mapas/components/MapaLocal.tsx` | `components/MapaLocal.tsx` | MODIFICADO |
| 4 | `sandbox_refactor_mapas/REVIEW.md` | — | este documento |
| 5 | `sandbox_refactor_mapas/VERIFICACION_ESTATICA.md` | — | verificaciones |

Rutas absolutas: `/home/ivan/navego_recuperado/sandbox_refactor_mapas/`

Contexto verificado: rama `experimento-dsh-01`, working tree limpio al
momento de preparar (`git status --short` sin salida).

---

## 2. Que cambio en cada archivo

### 2.1 `config/mapas.ts` (NUEVO — 88 lineas)

Contenido, en orden:

- `export const PUERTO = 8080;`
- `export type MapDescriptor = { id, nombre, archivo, sourceLayer, center, minzoom, maxzoom, version, asset }`
- `const CATALOGO: Record<string, MapDescriptor>` con 2 entradas:
  - `santa_fe`: archivo `santa_fe.mbtiles`, sourceLayer `santa_fe`,
    center `[-60.7, -31.63]`, min 8 / max 14, version `2026-09-20`
  - `corredor_sf_caba`: archivo `corredor_sf_caba.mbtiles`, sourceLayer
    `corredor`, center `[-60.65, -32.95]`, min 8 / max 14, version `2026-09-22`
- `let mapaActivoId = 'santa_fe';`
- `getMapaActivo()` → descriptor; lanza `Error` con la lista de validos si el id no existe
- `setMapaActivo(id)` → valida y setea; lanza `Error` con la lista de validos
- `getMapasDisponibles()` → `string[]`

Los `require` son **literales**, uno por entrada (Metro no resuelve
`require` con variable). Viven solo aca.

Decisiones del Director aplicadas: D-1 = (b) Rosario `[-60.65, -32.95]`;
D-2 = (a) default `santa_fe`.

### 2.2 `components/MapaOffline.tsx` (169 → 174 lineas)

Diff real (`diff -u original sandbox`), 4 bloques + 1:

**(a) Linea 8 — import agregado**
```diff
 import { HttpServer } from 'react-native-nitro-http-server';
+import { getMapaActivo, PUERTO } from '../config/mapas';
```

**(b) Lineas 11-19 — constantes reemplazadas**
```diff
 const DIR = FileSystem.documentDirectory + 'maptest/';
-const DB_NAME = 'santa_fe.mbtiles';
+
+// Descriptor del mapa activo (Fase 1). Reemplaza los hardcodes de santa_fe.
+const mapa = getMapaActivo();
+const DB_NAME = mapa.archivo;
 const DB_PATH = DIR + DB_NAME;
-const PUERTO = 8080;
-const SOURCE_LAYER = 'santa_fe';
-const CENTER_DEFAULT: [number, number] = [-60.7, -31.63];
+const SOURCE_LAYER = mapa.sourceLayer;
+const CENTER_DEFAULT: [number, number] = mapa.center;
+const MINZOOM = mapa.minzoom;
+const MAXZOOM = mapa.maxzoom;
```
`DIR` **no cambio**. Se eliminaron las 5 constantes (DB_NAME, PUERTO,
SOURCE_LAYER, CENTER_DEFAULT + require literal). `DB_PATH` se mantiene
derivado.

**(c) Linea 68 — require literal eliminado**
```diff
-        const asset = Asset.fromModule(require('../assets/maptest/santa_fe.mbtiles'));
+        const asset = Asset.fromModule(mapa.asset);
```

**(d) Lineas 82-85 — regex del server + indices de grupo**
```diff
-          const m = path.match(/^\/(\d+)\/(\d+)\/(\d+)\.pbf$/);
+          const m = path.match(/^\/([^\/]+)\/(\d+)\/(\d+)\/(\d+)\.pbf$/);
-          const z = Number(m[1]);
-          const x = Number(m[2]);
-          const y = Number(m[3]);
+          const z = Number(m[2]);
+          const x = Number(m[3]);
+          const y = Number(m[4]);
```

**(e) Linea 97 — URL que consume MapLibre**
```diff
-        setUri(`http://127.0.0.1:${PUERTO}/{z}/{x}/{y}.pbf`);
+        setUri(`http://127.0.0.1:${PUERTO}/${mapa.id}/{z}/{x}/{y}.pbf`);
```

**(f) Linea 137 — minzoom/maxzoom del source vectorial**
```diff
-    local: { type: 'vector', tiles: [uri], minzoom: 8, maxzoom: 14 },
+    local: { type: 'vector', tiles: [uri], minzoom: MINZOOM, maxzoom: MAXZOOM },
```

### 2.3 `components/MapaLocal.tsx` (141 → 146 lineas)

Mismos 6 cambios (a)-(f), con numeros de linea desplazados:
import en linea 9; constantes en 13-20; require en 38; regex/indices en
54/56-58; URL en 74; min/max del source en 118.

**Diferencia importante respecto de MapaOffline:** `MapaLocal` **mantiene**
`const ZOOM = 14;` y el bloque `// ─── UBICACIÓN ───` completo
(`Location.requestForegroundPermissionsAsync`, `getCurrentPositionAsync`,
`setUserPos`). Ese codigo **no se toco**, tal como pidio la mision.

---

## 3. Que NO cambio (explicito)

Verificado con `diff -u` (ver `VERIFICACION_ESTATICA.md`, seccion E):

- **`aGeoJSON()`**: byte-identica en ambos archivos.
- **`useEffect` de ubicacion** (`MapaOffline`, lineas 104-110 originales): intacto.
- **`useEffect` de recentrado por `initialCenter`** (`MapaOffline`, 114-120): intacto.
- **`useEffect` de timers de `MapaLocal`** (93-106): intacto.
- **`useImperativeHandle` / `centerOn`**: intacto.
- **Estilo de MapLibre** (`sources`, `layers`, colores, `source-layer`):
  intacto salvo el `minzoom/maxzoom` del source, que ahora lee del descriptor.
- **`DIR = FileSystem.documentDirectory + 'maptest/'`**: intacto (el diseno
  lo lista como SE MANTIENE).
- **Logica de copia del asset / apertura de SQLite / montaje del server**:
  intacta salvo el origen del asset y el patron de URL.
- **`minZoom`/`maxZoom` del componente `<Camera>`**: intactos como literales
  (8/22 en MapaOffline, 8/16 en MapaLocal). Ver Incertidumbre I-2.
- **Props, interfaz `Props`, `forwardRef`, firmas**: intactas.
- **`App.tsx`, `ReferenceDetailScreen.tsx`**: no tocados. No requieren
  cambios: siguen importando `MapaOffline` igual que antes.

---

## 4. Como aplicar cada archivo al repo

**Pre-requisito:** resolver el BLOQUEANTE de la seccion superior (copiar el
`.mbtiles` del corredor), o aceptar conscientemente que esa entrada queda rota.

**Paso 0 — punto de rollback (sugerido por el diseno, P0):**

```bash
cd ~/navego_recuperado
git status                       # debe estar limpio
git log -1 --format=%H           # guardar hash
git tag pre-fase1-mapas
```

**Paso 1 — crear config/mapas.ts (nada existente se toca):**

```bash
mkdir -p config
cp sandbox_refactor_mapas/config/mapas.ts config/mapas.ts
```

**Paso 2 — MapaOffline.tsx:**

```bash
cp sandbox_refactor_mapas/components/MapaOffline.tsx components/MapaOffline.tsx
```

**Paso 3 — MapaLocal.tsx:**

```bash
cp sandbox_refactor_mapas/components/MapaLocal.tsx components/MapaLocal.tsx
```

**Paso 4 — copiar el asset faltante (si se decide hacerlo):**

```bash
cp sandbox_corredor/out_mision_b/corredor_sf_caba.mbtiles assets/maptest/
```

**Verificar el diff antes de dar por aplicado:**

```bash
git diff --stat
# esperado: config/mapas.ts (nuevo), components/MapaOffline.tsx, components/MapaLocal.tsx
```

**Rollback por paso (no de todo):**

```bash
git checkout components/MapaOffline.tsx   # paso 2
git checkout components/MapaLocal.tsx     # paso 3
rm config/mapas.ts                        # paso 1
```

---

## 5. Checklist de verificacion post-aplicacion

### Estaticas (sin ejecutar la app)

- [ ] `npx tsc --noEmit` — **no debe agregar errores nuevos**. Ojo: hoy ya
      existen **2 errores preexistentes** por `UserLocation visible={...}`
      (ver `VERIFICACION_ESTATICA.md` §A). El criterio correcto es
      "los mismos 2 de antes", no "0 errores".
- [ ] `grep -rn "santa_fe" components/` → **0 coincidencias** de hardcode.
- [ ] `grep -rn "require(" components/MapaOffline.tsx components/MapaLocal.tsx` → **0**.
- [ ] Ambos componentes tienen exactamente el mismo bloque de constantes.
- [ ] `PUERTO = 8080` declarado **una sola vez** (en `config/mapas.ts`).

### Runtime (requiere compilar APK — fuera del alcance de esta mision)

- [ ] Arranca con `santa_fe` (comportamiento actual intacto).
- [ ] Log `[ML] 1. dir ok` … `[ML] 5. server OK`.
- [ ] El tracker sigue dibujando la linea roja.
- [ ] `http://127.0.0.1:8080/santa_fe/10/339/606.pbf` → tile valido.
- [ ] `http://127.0.0.1:8080/corredor_sf_caba/10/339/606.pbf` → tile
      **distinto** (prueba del namespacing, criterio 6 del diseno).
- [ ] `setMapaActivo('corredor_sf_caba')` — documentar si requiere remount
      (criterio 7 del diseno).
- [ ] `mapaActivoId = 'no_existe'` → error legible con lista de validos
      (criterio 5 / test negativo).

---

## 6. Incertidumbres

- **I-1 — Ruta del asset del corredor.** El diseno asume
  `assets/maptest/corredor_sf_caba.mbtiles`; el archivo real esta en
  `sandbox_corredor/out_mision_b/`. Prepare el `require` con la ruta del
  diseno (la objetivo). **No decidi mover ni copiar el archivo.** Es
  decision humana.

- **I-2 — Alcance de `MINZOOM`/`MAXZOOM`.** La tarea dice: *"El
  minzoom/maxzoom del source vectorial tambien deberia leer del descriptor
  (MINZOOM, MAXZOOM) en vez de 8/14 fijos."* Aplique eso **solo al source
  vectorial**, y deje los `minZoom`/`maxZoom` del componente `<Camera>`
  como literales (8/22 y 8/16). Motivo: `<Camera>` ya tiene un `maxZoom`
  distinto por componente (22 vs 16) que no coincide con el `maxzoom` del
  descriptor (14); cambiarlo alteraria el comportamiento de zoom del mapa,
  y la tarea dice "el resto del componente NO cambia". **Si la intencion
  era tambien unificar el `<Camera>`, avisar: es un cambio adicional.**

- **I-3 — Semantica de `request.path`.** El regex nuevo es estricto:
  `/santa_fe/10/339/606.pbf` matchea; con query string
  (`...pbf?x=1`) **no** matchea (verificado). No pude confirmar en la
  documentacion de `react-native-nitro-http-server` si `request.path`
  incluye query string. **Riesgo bajo**: el comportamiento es identico al
  codigo actual (el regex viejo tambien era estricto y anclado), asi que el
  refactor no lo empeora. Queda como observacion, no como regresion.

- **I-4 — Validacion de `mapaId` en el server.** El diseno (linea 161) dice
  *"El server valida que mapaId == mapaActivoId (o sirve de la DB que ya
  tiene cargada)"*, con un "o" que deja dos alternativas. La tarea de la
  mision **no pide** agregar esa validacion: solo pide capturar el grupo y
  cambiar la URL. Implemente la opcion debil (el grupo se captura pero no se
  valida; el server sirve siempre de la DB abierta). **Si el Director quiere
  la validacion estricta, es codigo adicional y no lo invente.**

- **I-5 — Cambio de mapa en caliente.** `mapa` se evalua **a nivel de
  modulo, una vez**. Por lo tanto `setMapaActivo()` en runtime **no**
  reagrupa el mapa ni reinicia el server: requiere remount del componente /
  reinicio de la app. Esto es consistente con "evaluado una vez" que pide la
  tarea, y es lo que el criterio 7 del diseno pide *documentar*. Lo dejo
  documentado, no resuelto.

---

## 7. Contradicciones encontradas

- **C-1 (BLOQUEANTE).** Diseno vs. realidad del repo: el asset del corredor
  no existe en `assets/maptest/`. Detallado arriba. **No lo resolvi.**

- **C-2.** Diseno 27b (lineas 193-196) lista `const DIR = ...` como "SE
  MANTIENE" y no incluye `DB_PATH` en la lista de "ENTRA". La tarea si pide
  explicitamente `const DB_PATH = DIR + DB_NAME;`. **No hay conflicto
  real**: `DB_PATH` ya existia y se conserva derivado (lineas 11-15 del
  original). Solo lo señalo para que no sorprenda en la revision del diff.

- **C-3.** Diseno (linea 135) define `setMapaActivo` con el mensaje
  `'Mapa no encontrado: ' + id` sin enumerar validos; la tarea pide
  *"Si el id no existe: throw Error con lista de validos"* para el modulo en
  general. Unifique ambos mensajes para que **los dos** enumeren los mapas
  validos, cumpliendo el criterio 5 del diseno. Es una mejora de mensaje,
  no un cambio de comportamiento.

- **C-4.** Diseno seccion "Que sale de cada componente" menciona quitar
  `PUERTO` de los componentes. **Confirmado**: ya no se declara ahi, se
  importa de `config/mapas`.

**Sin contradiccion:** los hardcodes listados por la tarea
(`DB_NAME`, `DB_PATH`, `PUERTO`, `SOURCE_LAYER`, `CENTER_DEFAULT`, require
literal) coinciden exactamente con lo que hay en ambos archivos originales.
El patron de uso (`Asset.fromModule` + `SQLite.openDatabaseAsync` +
`HttpServer`) no cambio respecto de lo que el diseno asume.

---

## 8. Puntos que requieren decision humana

1. **Copiar o no** `corredor_sf_caba.mbtiles` a `assets/maptest/`
   (BLOQUEANTE C-1). Si se copia, decidir si se versiona pese al
   `.gitignore` (126 MB).
2. **I-2:** ¿`minZoom`/`maxZoom` del `<Camera>` tambien se unifican al
   descriptor, o quedan como estan (8/22 y 8/16)?
3. **I-4:** ¿se agrega validacion estricta de `mapaId` en el server?
4. **D-2 al desplegar:** el default queda en `santa_fe`. El diseno (paso 4)
   sugiere cambiarlo a `corredor_sf_caba` solo para el viaje del 29.
5. **I-5:** documentar si el cambio de mapa en caliente es requisito o
   alcanza con remount.

---

## Fin de la guia de revision.

Recordatorio: **la IA prepara, la IA no aplica.** Nada de lo listado en la
seccion 4 fue ejecutado.
