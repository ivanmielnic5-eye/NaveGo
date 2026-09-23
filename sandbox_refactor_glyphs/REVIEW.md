# REVIEW.md — Capas de texto (symbol) con glyphs bundleados

**Mision:** A (preparacion) — NO aplicado al repo.
**Fecha:** 2026-09-22
**Base:** EXPEDIENTE/28_DISENO_CAPAS_TEXTO.md
**Sandbox:** `~/navego_recuperado/sandbox_refactor_glyphs/`

---

## Que hace este cambio

Agrega 4 capas de tipo `symbol` (texto) al estilo MapLibre, y sirve los
glyphs `.pbf` desde el servidor HTTP local. Antes no habia NINGUNA capa
`symbol`, por eso el mapa se veia "minimalista": los datos (`name`,
`admin_level`, `ref`, `amenity`) ya estaban en los MBTiles, pero el estilo
no los dibujaba.

---

## Archivos producidos

| Archivo | Estado |
|---|---|
| `components/MapaOffline.tsx` | Version nueva (no aplicada) |
| `components/MapaLocal.tsx` | Version nueva (no aplicada) |
| `REVIEW.md` | Este archivo |
| `VERIFICACION_ESTATICA.md` | Verificaciones ejecutadas |

**NO se toco:** `config/mapas.ts`, `metro.config.js`, MBTiles, ningun otro
componente, ningun archivo real del repo.

---

## Como aplicar (lo hace el humano)

```bash
cd ~/navego_recuperado

# 1. Backup de los originales (si no existe ya)
cp components/MapaOffline.tsx components/MapaOffline.tsx.bak_pre_glyphs
cp components/MapaLocal.tsx   components/MapaLocal.tsx.bak_pre_glyphs

# 2. Aplicar
cp sandbox_refactor_glyphs/components/MapaOffline.tsx components/MapaOffline.tsx
cp sandbox_refactor_glyphs/components/MapaLocal.tsx   components/MapaLocal.tsx

# 3. Verificar que solo cambiaron esos 2 archivos
git status --porcelain

# 4. Recompilar y ver en el celu
```

Antes de aplicar, comparar con:

```bash
diff -u components/MapaOffline.tsx sandbox_refactor_glyphs/components/MapaOffline.tsx
diff -u components/MapaLocal.tsx   sandbox_refactor_glyphs/components/MapaLocal.tsx
```

---

## Los 6 cambios, uno por uno

### 1. Imports de fuentes (inicio del modulo)

```ts
const FONT_OS_REGULAR_0 = require('../assets/fonts/open-sans-regular/0-255.pbf');
const FONT_OS_REGULAR_1 = require('../assets/fonts/open-sans-regular/256-511.pbf');
const FONT_OS_BOLD_0    = require('../assets/fonts/open-sans-bold/0-255.pbf');
const FONT_OS_BOLD_1    = require('../assets/fonts/open-sans-bold/256-511.pbf');
```

`require` es LITERAL a proposito: Metro no resuelve `require(variable)`.
`metro.config.js` ya acepta `.pbf` como asset (verificado).

### 2. Constante FONTS_DIR

```ts
const FONTS_DIR = FileSystem.documentDirectory + 'fonts/';
```

### 3. Copia de las 4 fuentes (dentro del useEffect, tras copiar el MBTiles y antes de abrir el server)

Se crean las dos subcarpetas y se copia cada fuente si falta. La copia es
**idempotente** (chequea `getInfoAsync` antes de copiar), asi que no
re-copia en cada arranque.

Se factorizo en un helper `copiarFuente()` para no repetir 4 veces el
mismo bloque. El helper hace exactamente lo pedido, nada mas.

Log: `console.log('[ML] 6. fuentes OK')`.

### 4. Ruta de glyphs en el servidor HTTP

Va **ANTES** del regex de tiles (linea 121 vs 143 en MapaOffline).
Formato servido: `/fonts/{fontstack}/{range}.pbf`.

Mapeo de fontstack → carpeta:
- `OpenSansRegular` → `open-sans-regular`
- `OpenSansBold` → `open-sans-bold`
- cualquier otro → 404

### 5. `glyphs` en el style

```ts
const style = {
  version: 8,
  glyphs: 'http://127.0.0.1:8080/fonts/{fontstack}/{range}.pbf',
  sources,
  layers,
};
```

### 6. Las 4 capas symbol

Insertadas entre `lineas` y `trackRefLine`, en el orden mandado:
`municipios`, `barrios`, `rutas`, `servicios`.

Los filtros, tamanos, colores y fontstacks son **exactamente** los del
diseno 28. No se agrego ninguna capa extra.

---

## Orden final de capas (verificado)

```
background, agua, edificios, lineas,
municipios, barrios, rutas, servicios,
trackRefLine, trackActivoLine
```

Los tracks quedan arriba de los textos, como pide el diseno.

---

## DIFERENCIAS RESPECTO DE LO PEDIDO (leer)

### D-1 — `atob` NO existe en React Native: se importa de nitro-buffer

**Esto es la desviacion mas importante.** El snippet de la tarea usaba
`atob(b64)`. Verifique que **`atob` NO es un global en React Native 0.81.5
ni en Expo 54**:

- `setUpGlobals.js` de RN no define `atob`.
- Ningun archivo de `node_modules/expo/` ni `node_modules/@expo/` lo define.
- `grep -rn "atob" node_modules/react-native/Libraries/` no devuelve nada.

Usar `atob()` directo habria dado `ReferenceError: atob is not defined`
en runtime.

**Solucion aplicada (sin instalar nada):** `react-native-nitro-buffer`
exporta una funcion `atob`. Y no es una dependencia nueva:
`react-native-nitro-http-server` YA la tiene como dependencia directa
(`"react-native-nitro-buffer": ">=0.0.14"`) y YA la usa internamente.

```ts
import { atob } from 'react-native-nitro-buffer';
```

Su implementacion: si `global.atob` existe lo usa; si no, cae a
`Buffer.from(data, 'base64').toString('binary')`.

**Riesgo:** bajo, pero es un import a una dependencia transitiva. Si
preferis no depender de eso, ver Alternativa A mas abajo.

### D-2 — NO se envia `Content-Encoding: gzip` en la ruta de fuentes

El snippet de la tarea no especificaba este header. Lo deje **afuera**
a proposito, y es un detalle que puede romper todo si se copia mal.

Verificado con bytes reales:
- Los **tiles** del MBTiles son gzip (empiezan `1f8b0800`) → el header
  `Content-Encoding: gzip` existente es correcto.
- Los **glyphs** son protobuf CRUDO (empiezan `0ac4c704`) → **NO** van
  con `Content-Encoding: gzip`.

Si se agrega `Content-Encoding: gzip` a la ruta de fuentes, MapLibre
intentaria descomprimir protobuf crudo y el texto NO se veria.

### D-3 — Helper `copiarFuente()` en vez de 4 bloques repetidos

El punto 3 pedia "para cada una de las 4 fuentes: descargar asset,
chequear si ya existe, copiar si no". Lo implemente como un helper y 4
llamadas. Es la misma logica, menos repetida. Si preferis los 4 bloques
explicitos, es un cambio trivial.

### D-4 — MapaLocal: se extrajo `layers` a un array

En MapaLocal el estilo estaba inline con el array `layers` literal. Como
ahora hay 4 capas symbol largas, extraje `const layers: any[] = [...]`
antes del `style` (igual que ya hacia MapaOffline). El estilo resultante
es identico en contenido.

MapaLocal **no tiene** capas de track (no usa `trackPoints`), asi que su
orden termina en `servicios`. Eso es correcto y consistente con el
original, que tampoco las tenia.

---

## Incertidumbres declaradas (NO inventadas)

### I-1 — `request.path` e include del query string

El handler lee `request.path`. El regex de glyphs **no** acepta query
string (`?x=1` → no match → 404). Si el cliente MapLibre agrega query
params a la URL de glyphs, la ruta fallaria. **No pude verificar** si
`react-native-nitro-http-server` entrega `path` sin query string, porque
eso depende del nativo (Rust) y no lo puedo ejecutar.

Nota: los tiles ya funcionan con el mismo patron, y tampoco aceptan
query string. Eso sugiere que `path` viene limpio, pero es inferencia,
no verificacion.

### I-2 — No se pudo ejecutar la app

Por restriccion de la tarea. Todo lo verificado es estatico + simulacion
de la decodificacion base64 en Node. **La verificacion visual en el
TCL T610P queda pendiente** y es la unica prueba real.

### I-3 — Rango de glyphs 256-511

Las fuentes cubren 0-255 y 256-511. Los nombres en español (acentos,
ñ) estan en 0-255 (Latin-1), asi que deberian alcanzar. **No verifique**
si hay caracteres usados por los datos que caigan fuera de 512; si
aparecen cuadrados vacios en algun nombre exotico, esa es la causa.

### I-4 — Performance en gama baja (TCL T610P)

4 capas symbol a zoom alto pueden costar. El diseno ya puso `minzoom: 12`
en `barrios` y `servicios` para acotarlo. **No medido** — pertenece a la
hipotesis H-2026-0001.

---

## Alternativa A (si no se quiere importar de nitro-buffer)

Reemplazar el import por una decodificacion base64 propia con
`base64-js` (dependencia directa de React Native, `node_modules/base64-js`,
no requiere instalar):

```ts
import { toByteArray } from 'base64-js';
// ...
const bytes = toByteArray(b64);
return { statusCode: 200, headers: { 'Content-Type': 'application/x-protobuf' }, body: bytes.buffer };
```

**NO aplique esta alternativa** porque implicaba una decision que no me
corresponde (cambia de que dependencia se tira el proyecto). Queda como
opcion para el Director.

---

## Lo que NO se hizo (respetando scope)

- No se modifico `config/mapas.ts` ni `metro.config.js`.
- No se modifico ningun MBTiles.
- No se agrego ninguna capa extra (ni iconos, ni aeropuertos, ni puertos).
- No se instalo ningun paquete.
- No se ejecuto la app.
- No se hizo commit.
- No se toco `main`.

---

## Checklist de revision para el humano

1. [ ] `diff -u` de los 2 archivos contra los originales: solo los 6
       cambios esperados.
2. [ ] Confirmar que `require('../assets/fonts/...')` apunta a rutas que
       existen en el repo (si).
3. [ ] Decidir sobre D-1 (`atob` de nitro-buffer) vs Alternativa A.
4. [ ] Confirmar que la ruta de fuentes NO lleva `Content-Encoding: gzip`.
5. [ ] Aplicar, recompilar, y verificar visualmente:
       - zoom bajo → nombres de departamentos/municipios.
       - zoom 12+ → barrios y servicios.
       - sobre rutas → RN9, AP01.
       - el track rojo debe quedar ARRIBA del texto.
6. [ ] Si aparece texto pero con cuadrados vacios → problema de glyphs
       (revisar que los .pbf se copiaron y que la ruta responde 200).
7. [ ] Si NO aparece ningun texto → revisar logs `[ML] 6. fuentes OK` y
       la consola de Metro por errores de glyph fetch.

---

## Evidencia

Ver `VERIFICACION_ESTATICA.md` para los comandos y resultados crudos.

---

Fin del REVIEW.
