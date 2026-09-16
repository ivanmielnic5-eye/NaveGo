# 🏆 HITOS NAVEGO — Registro oficial

> "Vamos rengo, pero vamos." — Capitán Iván

---

## 🗓️ 2026-09-16 — Sesión épica (8:00 → 16:00)

Sesión de 8 horas. Muchos trabones. Muchos avances. Al final del día:
**mapa vectorial offline funcionando en un TCL T610P de gama media.**

---

## ✅ HITO U-08 — Test SQLite puro (mañana)

### Objetivo
Medir rendimiento de lectura SQLite en el TCL antes de comprometer arquitectura.

### Archivos de prueba
| Archivo | Tamaño | Tiles | Features |
|---|---|---|---|
| test_hibrido.mbtiles | 40 KB | 9 | 2 |
| render.mbtiles | 36 KB | 9 | — |
| navigation.sqlite | 8 KB | — | 2 |
| render_big.mbtiles | 29 MB | 10.711 | — |

### Resultados (promedio de 3 corridas)
| Métrica | Archivos chicos | render_big (29 MB) |
|---|---|---|
| Apertura SQLite (caché) | ~9-10 ms | ~10-13 ms |
| tiles LIMIT 1 | ~13-17 ms | ~15-17 ms |
| tiles COUNT(*) | ~13-20 ms | ~46-52 ms |

### Conclusión
✅ **SQL puro con expo-sqlite ESCALA BIEN.**
- Leer un tile puntual no depende del tamaño del archivo.
- Cold start de I/O: ~227 ms la primera vez, ~10 ms después.
- Arquitectura elegida: **archivos separados** (render + navigation).
- Híbrido descartado: no aporta ventajas.

---

## ✅ HITO U-09 — Mapa vectorial offline (tarde)

### Objetivo
Renderizar un mapa real (Tucumán) desde MBTiles local con MapLibre.

### Arquitectura validada

Después, para inmortalizarlo en git:

```bash
cd ~/navego_recuperado
git add HITOS.md
git commit -m "🏆 Hito U-08 y U-09: SQLite + MapLibre con vector tiles offline funcionando en TCL T610P"
git log --oneline -3
cd ~/navego_recuperado
rm -f HITOS.md
ls -la HITOS.md 2>/dev/null || echo "OK, borrado"
cd ~/navego_recuperado
cat > HITOS.md << 'EOF'
# HITOS NAVEGO — Registro oficial

> "Vamos rengo, pero vamos." — Capitan Ivan

## 2026-09-16 — Sesion epica (8:00 a 16:00)

8 horas de trabajo. Muchos trabones. Un logro:
mapa vectorial offline funcionando en un TCL T610P de gama media.

## HITO U-08 — Test SQLite puro (manana)

Archivos de prueba:
- test_hibrido.mbtiles | 40 KB | 9 tiles | 2 features
- render.mbtiles      | 36 KB | 9 tiles | 0 features
- navigation.sqlite   |  8 KB | 0 tiles | 2 features
- render_big.mbtiles  | 29 MB | 10.711 tiles | 0 features

Resultados promedio de 3 corridas:
- Apertura SQLite (cache): ~10 ms en todos los tamanos
- tiles LIMIT 1: ~15 ms en todos los tamanos
- tiles COUNT(*): 13-20 ms (chicos) vs 46-52 ms (grande)
- Cold start de I/O: ~227 ms la primera vez, ~10 ms despues

Conclusion:
- SQL puro con expo-sqlite ESCALA BIEN.
- Arquitectura elegida: archivos separados (render + navigation).
- Hibrido descartado: no aporta ventajas.

## HITO U-09 — Mapa vectorial offline (tarde)

Arquitectura validada:
  assets/maptest/render_big.mbtiles (29 MB)
    -> copia con expo-asset a Paths.document/maptest/
    -> expo-sqlite lee los tiles
    -> servidor HTTP local en puerto 8080 (nitro-http-server)
    -> MapLibre consume con estilo vectorial inline

Stack:
- React Native + Expo SDK 54
- @maplibre/maplibre-react-native (con New Architecture)
- expo-sqlite, expo-asset, expo-file-system
- react-native-nitro-http-server

Resultados:
- 58.5 FPS sostenidos en TCL T610P
- Zoom 8 a 14 funcionando en todos los niveles
- Sin internet, todo offline

## Pipeline de generacion

1. curl -L -o region.osm.pbf https://download.openstreetmap.fr/...
2. osmium export region.osm.pbf -o region.geojson --overwrite
3. tippecanoe -o region.mbtiles -Z8 -z14 --drop-densest-as-needed --force region.geojson
4. mv region.mbtiles assets/maptest/

## Lecciones tecnicas

1. tippecanoe de repos no trae soporte PBF -> usar osmium export
2. MBTiles usa TMS (Y invertida): yTms = (2^z - 1) - y
3. MapLibre v11+ requiere New Architecture (newArchEnabled: true)
4. MapLibre pide .pbf, no .png, para vector tiles
5. Estilo raster no sirve: usar type vector con source-layer
6. Camera no existe en v11: usar center/zoom en el estilo JSON
7. Android bloquea HTTP cleartext: usar localhost o permiso

## Lecciones humanas

1. Cuando algo no funciona, no es fracaso: es diagnostico.
2. Cada trabon es aprendizaje que no se repite.
3. El viento en contra se vuelve a favor.
4. Las sesiones largas necesitan pausas reales.
5. Documentar los hitos inmortaliza el esfuerzo.

## Proximos pasos

- [ ] Mapa de Santa Fe (rios, laguna Setubal, Parana)
- [ ] Silenciar logs de tiles en produccion
- [ ] Integrar navigation.sqlite (features propias)
- [ ] Resolver field type exception (limpieza OSM)
- [ ] Sistema de autoconocimiento como variable

## Dedicatoria

A la paciencia de 8 horas.
A los que creen que "no cualquiera mete un mapa en una app".
A Santa Fe, sus rios, su laguna y su Parana.

Capitan Ivan — 2026-09-16
