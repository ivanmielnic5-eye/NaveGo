# VERIFICACION_ESTATICA.md — Capas de texto (glyphs)

**Mision:** A (preparacion) — NO aplicado.
**Fecha:** 2026-09-22
**Sandbox:** `~/navego_recuperado/sandbox_refactor_glyphs/`

Todas las verificaciones de abajo fueron **ejecutadas**. Cada una indica
el comando y el resultado real. Lo que NO se pudo verificar esta marcado
explicitamente como PENDIENTE o INCERTIDUMBRE.

---

## V-1 — El binario permite devolver bytes? (BLOQUEANTE)

La tarea pedia: "verificar la API real de react-native-nitro-http-server
para devolver bytes binarios. Si no se puede, DETENER y reportar."

**RESULTADO: SI SE PUEDE.** Evidencia:

`node_modules/react-native-nitro-http-server/lib/index.d.ts`:

```ts
export interface HttpResponse extends Omit<NitroHttpResponse, 'body' | 'binaryBody'> {
    body?: string | ArrayBuffer;
}
```

El tipo `HttpResponse.body` acepta `ArrayBuffer`.

Ademas, `lib/index.js` tiene un `wrapHandler` que intercepta el body
binario y lo manda por la API nativa segura:

```js
const wrapHandler = (handler) => {
    return async (request) => {
        const response = await handler(request);
        if (response.body && typeof response.body === 'object' &&
            (response.body instanceof ArrayBuffer || ArrayBuffer.isView(response.body))) {
            // ...
            await HttpServerModule.sendBinaryResponse(request.requestId, response.statusCode, headersJson, buffer);
```

Y el nativo expone:

```ts
sendBinaryResponse(requestId: string, statusCode: number, headersJson: string, body: ArrayBuffer): Promise<boolean>;
```

**Conclusion: el patron `body: bytes.buffer` (ArrayBuffer) es el correcto
y esta soportado por la libreria.** No hay bloqueo por este lado.

Version instalada: `react-native-nitro-http-server@1.9.2`.

---

## V-2 — Los assets de glyphs existen

```
assets/fonts/open-sans-regular/0-255.pbf    74696 bytes
assets/fonts/open-sans-regular/256-511.pbf  66481 bytes
assets/fonts/open-sans-bold/0-255.pbf       80025 bytes
assets/fonts/open-sans-bold/256-511.pbf     70900 bytes
```

Los 4 existen. Tamano coherente con glyph PBF reales.

---

## V-3 — `atob` NO existe en RN/Expo (DESVIACION, ver REVIEW D-1)

```
$ grep -rn "atob" node_modules/react-native/Libraries/
(sin resultados)

$ grep -rln "atob" node_modules/expo/
(sin resultados)

$ grep -rn "atob" node_modules/@expo/
(sin resultados)
```

RN 0.81.5, Expo 54. `atob` no es global. El snippet original
(`atob(b64)`) habria fallado en runtime con `ReferenceError`.

**Solucion:** `react-native-nitro-buffer` exporta `atob`
(`lib/utils.d.ts`):

```ts
export declare function atob(data: string): string;
```

Implementacion (`lib/utils.js`):

```js
export function atob(data) {
    if (typeof global.atob === 'function') {
        return global.atob(data);
    }
    return Buffer.from(data, 'base64').toString('binary');
}
```

Es dependencia directa de `react-native-nitro-http-server`
(`"react-native-nitro-buffer": ">=0.0.14"`), o sea que **ya esta en el
tree y ya se usa**. No se instalo nada.

---

## V-4 — Decodificacion base64 byte-exacta (simulada en Node)

Se simulo el camino completo: leer archivo como base64 → `atob` → bytes.

```
$ node -e "..."
orig bytes: 74696 decoded bytes: 74696
roundtrip identical: true
first 4 bytes (must be 0ac4c704): 0ac4c704
body is ArrayBuffer: true
byteOffset (must be 0 for clean ArrayBuffer send): 0 byteLength: 74696
```

Las 4 fuentes, roundtrip identico:

```
assets/fonts/open-sans-regular/0-255.pbf    74696  roundtrip: true
assets/fonts/open-sans-regular/256-511.pbf  66481  roundtrip: true
assets/fonts/open-sans-bold/0-255.pbf       80025  roundtrip: true
assets/fonts/open-sans-bold/256-511.pbf     70900  roundtrip: true
```

`byteOffset: 0` importa: el `wrapHandler` usa el ArrayBuffer directo
cuando `byteOffset === 0`; si no, hace un `slice`. Con `Uint8Array.from`
el offset es 0, asi que se toma el camino rapido.

---

## V-5 — Los glyphs son protobuf CRUDO, no gzip

```
assets/fonts/open-sans-regular/0-255.pbf first bytes: 0ac4 c704
assets/fonts/open-sans-regular/256-511.pbf first bytes: 0aad 8704
```

`0x0a` = field 1 varint = protobuf. NO es gzip (gzip seria `1f8b`).

En contraste, los tiles del MBTiles SI son gzip:

```
$ python3 (leer primer tile de santa_fe.mbtiles)
first 4 bytes: 1f8b0800
```

**Consecuencia verificada:** la ruta de fuentes NO lleva
`Content-Encoding: gzip`; la de tiles SI (y ya lo llevaba).

```
$ grep -n "Content-Encoding" sandbox_refactor_glyphs/components/*.tsx
MapaOffline.tsx:135:  // ... NO se envia 'Content-Encoding: gzip' ...
MapaOffline.tsx:155:  ... tiles ... 'Content-Encoding': 'gzip' ...
MapaLocal.tsx:105:    // ... NO se envia 'Content-Encoding: gzip' ...
MapaLocal.tsx:127:    ... tiles ... 'Content-Encoding': 'gzip' ...
```

El header gzip aparece **solo** en la ruta de tiles.

---

## V-6 — Orden final de capas

```
$ grep -oP "id: '\K[a-zA-Z]+(?=')" MapaOffline.tsx

MapaOffline:                MapaLocal:
background                  background
agua                        agua
edificios                   edificios
lineas                      lineas
municipios                  municipios
barrios                     barrios
rutas                       rutas
servicios                   servicios
trackRefLine                (no tiene tracks)
trackActivoLine
```

Coincide exactamente con el orden mandado. MapaLocal no tiene capas de
track (nunca las tuvo).

---

## V-7 — Fontstacks SIN espacios

```
$ grep -oP "'text-font': \[\K[^\]]*" *.tsx | sort -u
'OpenSansBold'
'OpenSansRegular'

$ grep -n "Open Sans" *.tsx
(sin resultados)
```

Correcto: sin espacios, en ambos archivos.

---

## V-8 — Requisitos de posicion en el codigo

```
MapaOffline.tsx
  18-21  las 4 requires
  113    '[ML] 6. fuentes OK'
  115    new HttpServer()
  116    server.start(...)
  121    fontMatch (ruta glyphs)   <-- ANTES del regex de tiles
  143    const m = path.match(...tiles...)

MapaLocal.tsx
  19-22  las 4 requires
  84     'fuentes OK'
  86     new HttpServer()
  87     server.start(...)
  91     fontMatch (ruta glyphs)   <-- ANTES del regex de tiles
  113    const m = path.match(...tiles...)
```

La ruta de fuentes esta antes del regex de tiles en ambos. La copia de
fuentes ocurre antes de abrir el server. Las requires estan al inicio
del modulo.

---

## V-9 — Regex de la ruta de glyphs

```
$ node -e "..."
OK  "/fonts/OpenSansRegular/0-255.pbf"        stack=OpenSansRegular range=0-255
OK  "/fonts/OpenSansBold/256-511.pbf"         stack=OpenSansBold range=256-511
OK  "/fonts/Open Sans Bold/0-255.pbf"         stack=Open Sans Bold range=0-255
OK  "/fonts/OpenSansRegular/0-255.pbf/extra"  no-match
OK  "/santa_fe/12/123/456.pbf"                no-match
OK  "/fonts/OpenSansRegular/0-255.pbf?x=1"    no-match
```

Los 6 casos se comportan como se espera. Nota: un fontstack con espacios
matchea el regex pero cae a `folder = null` → 404. Es correcto, porque el
style usa los nombres sin espacios.

**INCERTIDUMBRE (I-1 del REVIEW):** el caso `?x=1` NO matchea. No pude
verificar si el cliente MapLibre agrega query string a la URL de glyphs,
ni si `request.path` del server la incluiria. Si lo hiciera, daria 404.
No verificable sin ejecutar la app.

---

## V-10 — Chequeo de tipos (tsc) sin errores nuevos

Se compilo cada archivo nuevo y su original con la misma configuracion,
y se comparo la lista de errores.

Config: `tsc --noEmit --jsx react-jsx --esModuleInterop --skipLibCheck
--moduleResolution bundler --module esnext --target es2020`

```
=== MapaOffline (nuevo) ===
MapaOffline.tsx(281,44): error TS2322: ... UserLocationProps ... 'visible' ...

=== MapaOffline (original) ===
MapaOffline.tsx(166,44): error TS2322: ... UserLocationProps ... 'visible' ...

=== MapaLocal (nuevo) ===
MapaLocal.tsx(247,23): error TS2322: ... UserLocationProps ... 'visible' ...

=== MapaLocal (original) ===
MapaLocal.tsx(136,23): error TS2322: ... UserLocationProps ... 'visible' ...
```

**El unico error presente en los nuevos es el MISMO error que ya tenia
el original** (el prop `visible` de `UserLocation`, tema de la version de
MapLibre). Los cambios introducen **cero errores de tipo nuevos**.

Se filtraron los errores de resolucion de modulos del copiado temporal
(`Cannot find module 'react'`, etc.) que aparecen por compilar fuera del
arbol real y son artefactos del metodo, no del codigo.

---

## V-11 — Los archivos reales NO fueron modificados

```
$ stat -c '%y %n' components/MapaOffline.tsx components/MapaLocal.tsx
2026-09-22 19:40:54  components/MapaOffline.tsx
2026-09-22 19:41:25  components/MapaLocal.tsx

$ stat -c '%y %n' sandbox_refactor_glyphs/components/*.tsx
2026-09-22 20:55:54  .../MapaOffline.tsx
2026-09-22 20:56:04  .../MapaLocal.tsx
```

Los reales tienen mtime 19:40/19:41 (ANTERIOR a mi sesion, que empezo
~20:55). No fueron tocados.

```
$ grep -c "FONT_OS_REGULAR\|glyphs\|OpenSans" components/MapaOffline.tsx components/MapaLocal.tsx
components/MapaOffline.tsx:0
components/MapaLocal.tsx:0

$ grep -c "FONT_OS_REGULAR\|glyphs\|OpenSans" sandbox_refactor_glyphs/components/*.tsx
sandbox_refactor_glyphs/components/MapaOffline.tsx:14
sandbox_refactor_glyphs/components/MapaLocal.tsx:14
```

Cero rastros de glyphs en los reales. Todo el cambio esta en el sandbox.

**Aclaracion sobre `git status`:** aparecen `M components/MapaOffline.tsx`,
`M components/MapaLocal.tsx`, `M metro.config.js` y `?? config/`,
`?? assets/fonts/`. Eso es **trabajo previo de Fase 1**, ya presente en el
working tree antes de que yo empezara. No es mio. Verificado por mtime y
por el grep de arriba.

---

## V-12 — No se instalo nada, no se commiteo

- No se ejecuto `npm install` / `yarn add`.
- No se ejecuto `git commit`.
- No se ejecuto la app.
- Solo se escribio dentro de `sandbox_refactor_glyphs/`.
- El directorio temporal `.tmp_glyphcheck/` usado para el chequeo de
  tipos fue borrado (`rm -rf`).

---

## Resumen de verificaciones

| # | Verificacion | Resultado |
|---|---|---|
| V-1 | API binaria de nitro-http-server | OK — soporta ArrayBuffer |
| V-2 | Los 4 assets existen | OK |
| V-3 | `atob` global en RN/Expo | **NO EXISTE** → import de nitro-buffer |
| V-4 | Roundtrip base64 | OK — byte-exacto, offset 0 |
| V-5 | Glyphs crudos vs tiles gzip | OK — header gzip solo en tiles |
| V-6 | Orden de capas | OK — coincide exacto |
| V-7 | Fontstacks sin espacios | OK |
| V-8 | Posicion de los bloques | OK |
| V-9 | Regex de ruta de glyphs | OK (6/6 casos) |
| V-10 | Errores de tipo nuevos | 0 |
| V-11 | Archivos reales intactos | OK |
| V-12 | Sin install / sin commit | OK |

## PENDIENTE (no verificable en Mision A)

1. **Verificacion visual en el TCL T610P** — unica prueba real.
2. Si MapLibre agrega query string a la URL de glyphs (I-1).
3. Performance de 4 capas symbol en gama baja (I-4).
4. Cobertura de caracteres fuera del rango 0-511 (I-3).

---

Fin de la verificacion.
