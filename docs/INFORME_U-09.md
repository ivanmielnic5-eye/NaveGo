# INFORME U-09 — NaveGo
## Mapa offline con MapLibre + MBTiles local

**Fecha:** 16 de septiembre de 2026
**Duración:** ~9 horas
**Dispositivo:** TCL T610P (Android, gama media)
**Host:** CachyOS (Arch Linux)

---

## 1. LOGRO PRINCIPAL

MapLibre renderizando tiles vectoriales desde un MBTiles local,
servido por un servidor HTTP embebido en la app, sin internet,
sin PC, sin Metro. 58 FPS sostenidos.

Capturas: zoom 8 (provincia), zoom 10 (ciudad), zoom 14 (calle).
Fondo, agua, ríos, calles, manzanas, POIs. Todo desde el MBTiles propio.

---

## 2. PIPELINE TÉCNICO

OSM PBF → osmium export → GeoJSON → tippecanoe → MBTiles
                                                    ↓
                                            expo-asset (copia)
                                                    ↓
                                            expo-sqlite (lectura)
                                                    ↓
                                     nitro-http-server (puerto 8080)
                                                    ↓
                                            MapLibre (vector tiles)

### Herramientas
- osmium-tool 1.19.0 (AUR)
- tippecanoe 2.79.0
- expo-sqlite, expo-asset, expo-file-system
- react-native-nitro-http-server
- @maplibre/maplibre-react-native v11+

### Archivos generados
- render_big.mbtiles (Tucumán, 29 MB, 10.711 tiles, zoom 8-14)
- santa_fe.mbtiles (Santa Fe, 122 MB, 49.796 tiles, zoom 8-14)

---

## 3. ERRORES ENCONTRADOS Y SOLUCIONES

| Error | Causa | Solución |
|---|---|---|
| Unable to resolve .mbtiles | Metro no reconoce la extensión | assetExts en metro.config.js |
| NativeLogModule.onLog undefined | MapLibre requiere Nueva Arquitectura | newArchEnabled true + prebuild --clean |
| Cannot read MapView | API v11 renombró MapView a Map | import { Map } |
| pmtiles:// unable to parse | MapLibre no lee pmtiles nativo | Servidor HTTP local con SQLite |
| raster decode failed | Estilo raster sobre tiles vectoriales | Estilo vector con source-layer |
| Cannot find module render_*.pbf | Nombre de capa mal | Verificar metadata.json del MBTiles |
| MapLibre + R8 en release | Reflexión rota por minificación | PENDIENTE: proguard rules |

---

## 4. LO QUE NO FUNCIONÓ

- PMTiles custom: MapLibre Native no tiene handler nativo y el paquete
  pmtiles de npm está hecho para navegador. Descartado tras 2 horas.
- Camera con defaultSettings: API incorrecta en v11.
- Cámara como objeto del estilo (center, zoom en JSON):
  MapLibre Native ignora esas props. Las usa MapLibre GL JS (web).
- Raster tiles: tippecanoe genera vectoriales, no PNG.

---

## 5. APRENDIZAJES DE PROCESO

### Protocolo de trabajo
- El usuario NO edita archivos. Se le pasan bloques completos
  cat > archivo << EOF que sobrescriben.
- Los logs son la fuente de verdad. No adivinar.
- Pausas cada 2-3 horas evitan bucles de frustración.

### Sobre el diagnóstico
- Cuando no hay logs, el problema está antes del log faltante.
- adb logcat es indispensable en release y en dev build.
- console.log en Metro cubre JS. logcat cubre nativo.

### Autoconocimiento del asistente
- Fallé al inventar Camera defaultSettings sin verificar la API real.
- Fallé al asumir que center/zoom en el estilo funcionarían en Native.
- Fallé en no advertir sobre R8/ProGuard antes del primer release.
- Aprendí que el protocolo cat > es el correcto para este usuario.
- Aprendí a pedir pausas cuando el usuario lleva muchas horas.

---

## 6. PENDIENTES (mañana)

1. Resolver MapLibre + R8 (proguard rules para org.maplibre.android).
2. Retomar Santa Fe (MBTiles ya generado, falta render en celular).
3. Backup automático a la nube (rclone + systemd timer o cron).
4. Integrar navigation.sqlite sobre el mapa (features propias).
5. Revisar triángulo blanco en Tucumán zoom 8 (cosmético).

---

## 7. LECCIÓN DE FONDO

Ninguna de las complicaciones invalida el logro. El mapa funcionó.
Lo que vino después fue el precio natural de empaquetar, minificar
y cambiar de mapa. Ese precio se paga una vez y queda resuelto
para todos los mapas futuros.

Un mapa offline en una app no es trivial. Hoy existe.

---

## 8. LECCIÓN CRÍTICA DEL DÍA — EL FIX DE GZIP

**Síntoma:** MapLibre mostraba pantalla blanca aunque el servidor
respondía con `[REQ OK]` y tiles de 400 KB.

**Error en logs:**
`Failed to load tile X/Y/Z: unknown pbf field type exception`

**Diagnóstico (3 comandos):**
1. Verificar el header del tile en SQLite:
   `sqlite3 santa_fe.mbtiles "SELECT hex(substr(tile_data,1,4)) FROM tiles LIMIT 1;"`
2. Si devuelve `1F8B0800` → el tile está comprimido con GZIP.
3. MapLibre espera PBF crudo si no se le avisa que es GZIP.

**Fix (1 línea):**
Agregar `'Content-Encoding': 'gzip'` al header de la respuesta HTTP.

**Por qué es importante:**
- tippecanoe gzipea los tiles por defecto al generar MBTiles.
- MBTiles estándar asume gzip y los clientes lo manejan automáticamente.
- Con servidor HTTP propio, la responsabilidad del header es nuestra.

**Regla nueva:** siempre verificar el header del tile con `hex(substr(...))`
antes de escribir el handler HTTP.

---

## 9. LO QUE APRENDIMOS SOBRE NOSOTROS

### Sobre el asistente (DeepSeek)
- Tiende a inventar APIs sin verificar la versión real.
- Repite errores ya resueltos si no se le recuerda el contexto.
- Propone comandos asumiendo que el usuario puede editar archivos.
- Necesita protocolo de "un cambio, un build, un test".

### Sobre el usuario (Capitán)
- NO edita archivos. Se le pasan bloques `cat > ... << 'EOF'`.
- Detecta rápido cuando el asistente miente o se contradice.
- Aguantó 15 horas sin rendirse.
- Pide orden: "una cosa a la vez".

### Sobre el proceso conjunto
- Funciona cuando: hay un cambio → un build → un test → feedback.
- Falla cuando: se meten muchos cambios juntos.
- El log es la fuente de verdad. Sin logs, es adivinar.
- Las pausas son parte del trabajo, no pérdida de tiempo.

---

## 8. LECCIÓN CRÍTICA DEL DÍA — EL FIX DE GZIP

**Síntoma:** MapLibre mostraba pantalla blanca aunque el servidor
respondía con `[REQ OK]` y tiles de 400 KB.

**Error en logs:**
`Failed to load tile X/Y/Z: unknown pbf field type exception`

**Diagnóstico (3 comandos):**
1. Verificar el header del tile en SQLite:
   `sqlite3 santa_fe.mbtiles "SELECT hex(substr(tile_data,1,4)) FROM tiles LIMIT 1;"`
2. Si devuelve `1F8B0800` → el tile está comprimido con GZIP.
3. MapLibre espera PBF crudo si no se le avisa que es GZIP.

**Fix (1 línea):**
Agregar `'Content-Encoding': 'gzip'` al header de la respuesta HTTP.

**Por qué es importante:**
- tippecanoe gzipea los tiles por defecto al generar MBTiles.
- MBTiles estándar asume gzip y los clientes lo manejan automáticamente.
- Con servidor HTTP propio, la responsabilidad del header es nuestra.

**Regla nueva:** siempre verificar el header del tile con `hex(substr(...))`
antes de escribir el handler HTTP.

---

## 9. LO QUE APRENDIMOS SOBRE NOSOTROS

### Sobre el asistente (DeepSeek)
- Tiende a inventar APIs sin verificar la versión real.
- Repite errores ya resueltos si no se le recuerda el contexto.
- Propone comandos asumiendo que el usuario puede editar archivos.
- Necesita protocolo de "un cambio, un build, un test".

### Sobre el usuario (Capitán)
- NO edita archivos. Se le pasan bloques `cat > ... << 'EOF'`.
- Detecta rápido cuando el asistente miente o se contradice.
- Aguantó 15 horas sin rendirse.
- Pide orden: "una cosa a la vez".

### Sobre el proceso conjunto
- Funciona cuando: hay un cambio → un build → un test → feedback.
- Falla cuando: se meten muchos cambios juntos.
- El log es la fuente de verdad. Sin logs, es adivinar.
- Las pausas son parte del trabajo, no pérdida de tiempo.
