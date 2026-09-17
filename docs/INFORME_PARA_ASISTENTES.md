# INFORME TÉCNICO — NaveGo

## Estado + bug abierto + pedido a asistentes

**Fecha:** 16 de septiembre de 2026
**Autor:** Iván + DeepSeek
**Propósito:** Consultar a GPT, Claude y Gemini con el mismo informe y la misma pregunta, para localizar la causa de un bug específico.

---

## 1. QUÉ ES NAVEGO

App de navegación offline para Android, en desarrollo.
- Mapa offline de una región (Santa Fe, Argentina).
- Punto de ubicación offline ("usted está aquí").
- Tracker de posición.
- Base de datos de navegación propia.
- Todo funcionando sin internet, sin PC, sin servidor externo.

---

## 2. STACK TÉCNICO

- Host: CachyOS (Arch Linux)
- Node: v26.8.2
- Expo SDK: 54.0.0
- Dispositivo: TCL T610P (Android gama media, 2-4 GB RAM)
- Librerías:
  - @maplibre/maplibre-react-native v11+
  - expo-sqlite
  - expo-asset
  - expo-file-system (API legacy)
  - react-native-nitro-http-server
- Generación:
  - osmium-tool 1.19.0
  - tippecanoe 2.79.0

---

## 3. ARQUITECTURA ACTUAL

Cadena de generación de datos:

    OSM PBF
      ↓
    osmium export
      ↓
    GeoJSON
      ↓
    tippecanoe
      ↓
    MBTiles (SQLite con tiles PBF vectoriales)

Cadena de uso en el dispositivo:

    MBTiles se copia al celular con expo-asset
      ↓
    expo-sqlite lee los tiles como BLOB
      ↓
    Servidor HTTP embebido (react-native-nitro-http-server) en puerto 8080
    responde a pedidos /{z}/{x}/{y}.pbf
      ↓
    MapLibre Native decodifica el PBF y lo renderiza

**Nota sobre el diseño:**
En esta implementación concreta no estamos usando un source MBTiles
directo de MapLibre. Construimos un puente HTTP porque la API de
MapLibre React Native que usamos no expone un source MBTiles local
de forma directa. Esto describe nuestro diseño actual, no una
propiedad universal del framework.

---

## 4. LO QUE FUNCIONA — VERIFICADO

### 4.1 Tucumán — 100% funcional

- Archivo: render_big.mbtiles (29 MB, 10.711 tiles, zoom 8-14)
- Estado: renderiza perfecto, 58 FPS, zoom in/out OK
- Pipeline: PBF -> GeoJSON -> tippecanoe con banderas por defecto
- Código: MapaLocal.tsx con servidor HTTP local + MapLibre

### 4.2 Santa Fe — funcional en APK RELEASE

- Archivo: santa_fe.mbtiles (126 MB, ~50.000 tiles, zoom 8-14)
- Release: el APK compilado con ProGuard renderiza offline OK
- Dev mode: falla con "unknown pbf field type exception"

### 4.3 Infraestructura

- Backup con ProGuard + reglas MapLibre + Nitro
- Documentación de aprendizaje (U-09)
- Glosario de términos técnicos

---

## 5. BUG ACTUAL

### 5.1 Síntoma

En dev mode (Expo + Metro), con santa_fe.mbtiles, el mapa queda con
fondo rojo sin formas. Los logs muestran:

    MapLibre Native [ERROR] [Mbgl] {RenderThread 69}[Style]:
    Failed to load tile 10/339/606=>10 for source local:
    unknown pbf field type exception

### 5.2 Comportamiento observado

- El servidor HTTP responde perfecto: [REQ OK] con tamaños correctos
- Los tiles llegan bien al celular
- MapLibre falla al DECODIFICAR el tile (no al recibirlo)
- Tucumán con el MISMO código funciona
- En APK RELEASE, Santa Fe SÍ funciona

---

## 6. EVIDENCIA CLAVE

### E-01 — El patrón que no cierra

El mismo pipeline de aplicación:

- FUNCIONA con render_big.mbtiles (Tucumán).
- FALLA con santa_fe.mbtiles (Santa Fe) en DEV.
- FUNCIONA con santa_fe.mbtiles en RELEASE.

Este comportamiento está verificado por observación del sistema.

No se ha determinado todavía su causa.

---

## 7. HIPÓTESIS DESCARTADAS

- NO es la ruta del archivo (md5 en celular vs PC iguales)
- NO es el servidor HTTP (responde OK a todos los pedidos)
- NO es el source-layer (verificado: 'santa_fe')
- NO es el estilo ni los colores
- NO es el código React Native (Tucumán funciona con el mismo código)

---

## 8. HIPÓTESIS VIGENTES

- Datos sucios en OSM: Santa Fe tiene atributos con tipos raros que
  tippecanoe vuelca en el tile y MapLibre no puede parsear.
- Tiles demasiado grandes: se observaron tiles de hasta 488 KB.
- Diferencia dev vs release: ProGuard o el build de release podría
  estar filtrando el error o usando un parser más permisivo.
- Bug específico de tippecanoe 2.79 con este dataset.

---

## 9. PRUEBAS YA REALIZADAS

- Verificar md5 del MBTiles en celular vs PC: idéntico.
- Verificar source-layer en metadata: correcto ('santa_fe').
- Regenerar con --drop-densest-as-needed: sin éxito.
- Regenerar sin esa bandera: sin éxito.
- --no-tile-stats y --maximum-tile-bytes=500000: sin éxito.
- Filtrar capas por geometría (Polygon, LineString): sin éxito.
- Cambiar a console.error para ver más logs: sin éxito.

---

## 10. PREGUNTA CONCRETA

No asumir que "unknown pbf field type exception" demuestra que el
PBF está corrupto. Determinar primero en qué capa de la cadena
ocurre la incompatibilidad:

    OSM
     ↓
    osmium
     ↓
    GeoJSON
     ↓
    tippecanoe
     ↓
    MBTiles
     ↓
    SQLite
     ↓
    HTTP
     ↓
    MapLibre
     ↓
    decoder
     ↓
    render

Preguntas específicas:

1. ¿Bug conocido de tippecanoe 2.79 + MapLibre Native v11?
2. ¿Banderas de tippecanoe específicas para este error?
3. ¿Conviene filtrar el GeoJSON con osmium tags-filter antes?
4. ¿Límite de tamaño de tile que MapLibre no tolera?
5. ¿Por qué release sí y dev no?

---

## 11. RESTRICCIONES

NO modificar todavía, salvo evidencia directa de que son la causa:

- Pipeline OSM
- tippecanoe
- MBTiles
- Servidor HTTP
- Versión de MapLibre
- Arquitectura de Nueva Arquitectura

Evitar respuestas del tipo "instalá otra versión" o "regenerá todo
el mapa" sin justificación técnica basada en la evidencia.

---

## 12. SALIDA ESPERADA DEL ASISTENTE

Pedimos cualquiera de estas:

1. Diagnóstico del bug con causa raíz identificada.
2. Banderas de tippecanoe específicas para evitar este error.
3. Confirmación de si es bug conocido de tippecanoe + MapLibre.
4. Fuentes alternativas de datos OSM de Santa Fe, Argentina.
5. Explicación de por qué dev y release se comportan distinto.

Cualquier aporte, experiencia o enlace es bienvenido.

---

## 13. CONTEXTO HUMANO

Llevamos ~13 horas de trabajo. Tucumán funciona 100% (dev y release).
Santa Fe funciona 100% en release. El bug solo afecta el flujo de
desarrollo (dev mode). No bloquea el producto final, pero sí frena
la iteración rápida.

El objetivo a largo plazo es una app de navegación offline completa,
usable sin internet, en un celular de gama media.

Gracias por cualquier aporte.
