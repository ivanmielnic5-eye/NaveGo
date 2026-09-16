# INFORME U-09 — Mapa Vectorial Offline
**Fecha:** 16 de septiembre de 2026
**Duración:** ~9h 20min (08:00 - 17:20, con pausas). Planificación previa: días.
**Dispositivo:** TCL T610P (gama media, Android)
**Host:** CachyOS (Arch)

## 1. RESUMEN
Se logró renderizar un mapa vectorial offline en NaveGo usando MBTiles local, servidor HTTP local (nitro-http-server) leyendo SQLite, y MapLibre Native. 58.5 FPS sostenidos. Funciona sin internet.

## 2. STACK FINAL
- Expo SDK 54, React Native 0.81 (Nueva Arquitectura)
- @maplibre/maplibre-react-native 11.x
- expo-sqlite, expo-asset, expo-file-system (API nueva)
- react-native-nitro-http-server
- tippecanoe v2.79.0 (sin soporte PBF), osmium-tool 1.19.0
- CachyOS (Arch)

## 3. PIPELINE
OSM (.osm.pbf) → osmium export → GeoJSON → tippecanoe -Z8 -z14 → MBTiles → assets/ → expo-asset → expo-file-system → SQLite → servidor HTTP :8080 → MapLibre

Nota: MBTiles usa TMS (Y invertida). Conversión: yTms = (2^z - 1) - y

## 4. ERRORES Y SOLUCIONES
1. Unable to resolve .mbtiles → agregar extensiones en metro.config.js
2. NativeLogModule.default.onLog → habilitar Nueva Arquitectura
3. MapView undefined → usar { Map } en lugar de MapView
4. Bitmap decoding failed → estilo raster a vector con source-layer
5. Element type invalid (Camera) → mover cámara al estilo JSON
6. HTTP Unable to parse (pmtiles) → descartar pmtiles, usar MBTiles + HTTP
7. field type exception → cosmético, no bloquea render
8. Pantalla beige sin tiles → tiles: [uri] con {z}/{x}/{y}.pbf + zoom 8-14

## 5. LO QUE NO FUNCIONÓ
- PMTiles custom (complejo, no aporta)
- react-native-http-bridge-refurbished (solo JSON, no binarios)
- tippecanoe con PBF en CachyOS (compilado sin esa feature)
- Camera component (API distinta entre versiones)
- Dev build sin internet (requiere Metro, usar release)

## 4. ERRORES Y SOLUCIONES
1. Unable to resolve .mbtiles → agregar extensiones en metro.config.js
2. NativeLogModule.default.onLog → habilitar Nueva Arquitectura
3. MapView undefined → usar { Map } en lugar de MapView
4. Bitmap decoding failed → estilo raster a vector con source-layer
5. Element type invalid (Camera) → mover cámara al estilo JSON
6. HTTP Unable to parse (pmtiles) → descartar pmtiles, usar MBTiles + HTTP
7. field type exception → cosmético, no bloquea render
8. Pantalla beige sin tiles → tiles: [uri] con {z}/{x}/{y}.pbf + zoom 8-14

## 5. LO QUE NO FUNCIONÓ
- PMTiles custom (complejo, no aporta)
- react-native-http-bridge-refurbished (solo JSON, no binarios)
- tippecanoe con PBF en CachyOS (compilado sin esa feature)
- Camera component (API distinta entre versiones)
- Dev build sin internet (requiere Metro, usar release)

## 4. ERRORES Y SOLUCIONES
1. Unable to resolve .mbtiles → agregar extensiones en metro.config.js
2. NativeLogModule.default.onLog → habilitar Nueva Arquitectura
3. MapView undefined → usar { Map } en lugar de MapView
4. Bitmap decoding failed → estilo raster a vector con source-layer
5. Element type invalid (Camera) → mover cámara al estilo JSON
6. HTTP Unable to parse (pmtiles) → descartar pmtiles, usar MBTiles + HTTP
7. field type exception → cosmético, no bloquea render
8. Pantalla beige sin tiles → tiles: [uri] con {z}/{x}/{y}.pbf + zoom 8-14

## 5. LO QUE NO FUNCIONÓ
- PMTiles custom (complejo, no aporta)
- react-native-http-bridge-refurbished (solo JSON, no binarios)
- tippecanoe con PBF en CachyOS (compilado sin esa feature)
- Camera component (API distinta entre versiones)
- Dev build sin internet (requiere Metro, usar release)

## 6. APRENDIZAJES DE PROCESO
- NO editar archivos manualmente. Usar cat > archivo << EOF para sobrescribir.
- Los console.log son la ventana al runtime. Sin ellos, se adivina.
- En release los logs están silenciados. En dev build, visibles en Metro.
- [REQ OK] / [REQ MISS] son oro para saber si el servidor recibe pedidos.
- 6 horas seguidas es mucho. Pausas cortas recargan.
- Verificar versión de librería antes de usar una API.
- Confirmar nombres exactos de capas, rutas y formatos.

## 7. AUTOCONOCIMIENTO DEL ASISTENTE
Donde la pifié:
- Asumí Camera sin verificar la versión de MapLibre.
- Asumí que react-native-http-bridge-refurbished soporta binarios.
- No revisé que tippecanoe de CachyOS no tiene PBF.
- Olvidé el protocolo de no editar archivos.
- Fui verboso cuando el usuario pedía comandos concretos.

Cómo evitarlo:
- Verificar la API real antes de proponer código.
- Confirmar soporte binario/PBF antes de asumir.
- Un comando concreto, no un ensayo.

## 8. MÉTRICAS FINALES
- MBTiles: 28.68 MB
- Tiles: 10.711
- Zoom: 8-14
- FPS: 58.5
- Errores resueltos: 8
- Commit: 529248f

## 9. PRÓXIMOS PASOS
1. Mapa de Santa Fe
2. Integrar navigation.sqlite
3. Resolver field type exception
4. Documentar autoconocimiento por sesión

## 10. FRASE DE CIERRE
"No cualquiera mete un mapa en una aplicación." — Iván, 16/09/2026

## NOTA METODOLÓGICA
La ventana de 9h 20min corresponde a la ejecución en sí (08:00 a 17:20).
La planificación, decisiones de arquitectura y preparación de archivos
comenzaron días antes. Esta distinción importa para medir con honestidad
el costo real de meter un mapa offline en una app.
