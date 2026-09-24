import React, { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';
import { View, StyleSheet } from 'react-native';
import { Map, Camera, UserLocation, type CameraRef } from '@maplibre/maplibre-react-native';
import { Asset } from 'expo-asset';
import * as FileSystem from 'expo-file-system/legacy';
import * as SQLite from 'expo-sqlite';
import { HttpServer } from 'react-native-nitro-http-server';
import { atob } from 'react-native-nitro-buffer';
import { getMapaActivo, PUERTO } from '../config/mapas';

const DIR = FileSystem.documentDirectory + 'maptest/';

// ─── GLYPHS (Mision A: capas de texto) ───────────────────────────────
// Los .pbf de glyphs viajan en el bundle como assets (metro.config.js ya
// acepta la extension 'pbf'). Metro exige require() LITERAL: no se puede
// construir la ruta con una variable.
// FUENTE: EXPEDIENTE/28_DISENO_CAPAS_TEXTO.md
const FONT_OS_REGULAR_0 = require('../assets/fonts/open-sans-regular/0-255.pbf');
const FONT_OS_REGULAR_1 = require('../assets/fonts/open-sans-regular/256-511.pbf');
const FONT_OS_BOLD_0 = require('../assets/fonts/open-sans-bold/0-255.pbf');
const FONT_OS_BOLD_1 = require('../assets/fonts/open-sans-bold/256-511.pbf');

// Carpeta destino en el dispositivo, espejo de la estructura de assets.
const FONTS_DIR = FileSystem.documentDirectory + 'fonts/';

// Descriptor del mapa activo (Fase 1). Reemplaza los hardcodes de santa_fe.
const mapa = getMapaActivo();
const DB_NAME = mapa.archivo;
const DB_PATH = DIR + DB_NAME;
const SOURCE_LAYER = mapa.sourceLayer;
const SOURCE_LAYER_ADMIN = (mapa as any).sourceLayerAdmin || mapa.sourceLayer;
const SOURCE_LAYER_ADMIN_PAIS = (mapa as any).sourceLayerAdminPais || mapa.sourceLayer;
const SOURCE_LAYER_ADMIN_PAIS_LABELS = (mapa as any).sourceLayerAdminPaisLabels || mapa.sourceLayer;
const CENTER_DEFAULT: [number, number] = mapa.center;
const MINZOOM = mapa.minzoom;
const MAXZOOM = mapa.maxzoom;

type Punto = { latitude: number; longitude: number };

interface Props {
  trackPoints: Punto[];
  referencePoints: Punto[];
  userPos: Punto | null;
  absolute?: boolean;
  initialCenter?: [number, number];
  initialZoom?: number;
  showUserLocation?: boolean;
}

function aGeoJSON(puntos: Punto[]) {
  return {
    type: 'Feature' as const,
    properties: {},
    geometry: {
      type: 'LineString' as const,
      coordinates: puntos.map((p) => [p.longitude, p.latitude]),
    },
  };
}

// Copia un asset de glyphs al filesystem del dispositivo si falta.
// Idempotente: si el archivo ya existe, no vuelve a copiar.
async function copiarFuente(modulo: any, subcarpeta: string, archivo: string) {
  const destino = FONTS_DIR + subcarpeta + '/' + archivo;
  const info = await FileSystem.getInfoAsync(destino);
  if (info.exists) return;
  const asset = Asset.fromModule(modulo);
  await asset.downloadAsync();
  if (!asset.localUri) throw new Error('glyph asset.localUri null: ' + archivo);
  await FileSystem.copyAsync({ from: asset.localUri, to: destino });
}

export const MapaOffline = forwardRef<any, Props>(function MapaOffline(
  { trackPoints, referencePoints, userPos, absolute, initialCenter, initialZoom, showUserLocation = true },
  ref
) {
  const [uri, setUri] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cameraRef = useRef<CameraRef>(null);
  const yaCentroRef = useRef(false);

  useImperativeHandle(ref, () => ({
    centerOn: (punto: Punto, zoom: number = 16) => {
      try {
        cameraRef.current?.jumpTo({ center: [punto.longitude, punto.latitude], zoom });
      } catch (e) {}
    },
  }));

  useEffect(() => {
    let server: any = null;
    let db: SQLite.SQLiteDatabase | null = null;
    (async () => {
      try {
        await FileSystem.makeDirectoryAsync(DIR, { intermediates: true }).catch(() => {});
        console.log('[ML] 1. dir ok');
        const asset = Asset.fromModule(mapa.asset);
        await asset.downloadAsync();
        if (!asset.localUri) throw new Error('asset.localUri null');
        console.log('[ML] 2. asset ok:', asset.localUri);
        const info = await FileSystem.getInfoAsync(DB_PATH);
        if (!info.exists) {
          await FileSystem.copyAsync({ from: asset.localUri, to: DB_PATH });
        }
        console.log('[ML] 3. copy ok, abriendo SQLite');
        db = await SQLite.openDatabaseAsync(DB_NAME, undefined, DIR);
        console.log('[ML] 4. SQLite abierto');

        // ─── 5. GLYPHS: copiar las 4 fuentes al filesystem ───
        await FileSystem.makeDirectoryAsync(FONTS_DIR + 'open-sans-regular/', { intermediates: true }).catch(() => {});
        await FileSystem.makeDirectoryAsync(FONTS_DIR + 'open-sans-bold/', { intermediates: true }).catch(() => {});
        await copiarFuente(FONT_OS_REGULAR_0, 'open-sans-regular', '0-255.pbf');
        await copiarFuente(FONT_OS_REGULAR_1, 'open-sans-regular', '256-511.pbf');
        await copiarFuente(FONT_OS_BOLD_0, 'open-sans-bold', '0-255.pbf');
        await copiarFuente(FONT_OS_BOLD_1, 'open-sans-bold', '256-511.pbf');
        console.log('[ML] 6. fuentes OK');

        server = new HttpServer();
        await server.start(PUERTO, async (request: any) => {
          const path = (request && request.path) ? request.path : '';

          // ─── RUTA DE GLYPHS (debe ir ANTES del regex de tiles) ───
          // Formato: /fonts/{fontstack}/{range}.pbf
          const fontMatch = path.match(/^\/fonts\/([^\/]+)\/(\d+-\d+)\.pbf$/);
          if (fontMatch) {
            const fontstack = decodeURIComponent(fontMatch[1]);
            const range = fontMatch[2];
            const folder = fontstack === 'OpenSansRegular' ? 'open-sans-regular'
                         : fontstack === 'OpenSansBold'    ? 'open-sans-bold'
                         : null;
            if (!folder) return { statusCode: 404, headers: { 'Content-Type': 'text/plain' }, body: 'no font' };
            const fontPath = FONTS_DIR + folder + '/' + range + '.pbf';
            const fontInfo = await FileSystem.getInfoAsync(fontPath);
            if (!fontInfo.exists) return { statusCode: 404, headers: { 'Content-Type': 'text/plain' }, body: 'no font' };
            const b64 = await FileSystem.readAsStringAsync(fontPath, { encoding: FileSystem.EncodingType.Base64 });
            const bytes = Uint8Array.from(atob(b64), (c: string) => c.charCodeAt(0));
            // NOTA: los .pbf de glyphs son protobuf CRUDO (0x0a...), NO gzip.
            // Por eso NO se envia 'Content-Encoding: gzip' (a diferencia de los tiles).
            return {
              statusCode: 200,
              headers: { 'Content-Type': 'application/x-protobuf' },
              body: bytes.buffer,
            };
          }

          const m = path.match(/^\/([^\/]+)\/(\d+)\/(\d+)\/(\d+)\.pbf$/);
          if (!m) return { statusCode: 404, headers: { 'Content-Type': 'text/plain' }, body: 'nf' };
          const z = Number(m[2]);
          const x = Number(m[3]);
          const y = Number(m[4]);
          const yTms = (1 << z) - 1 - y;
          const row = await db!.getFirstAsync<{ tile_data: Uint8Array }>(
            'SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?',
            [z, x, yTms]
          );
          if (!row || !row.tile_data) return { statusCode: 404, headers: { 'Content-Type': 'text/plain' }, body: 'no tile' };
          const ab = row.tile_data.buffer.slice(row.tile_data.byteOffset, row.tile_data.byteOffset + row.tile_data.byteLength);
          return { statusCode: 200, headers: { 'Content-Type': 'application/x-protobuf', 'Content-Encoding': 'gzip' }, body: ab };
        });
        console.log('[ML] 7. server OK');
        setUri(`http://127.0.0.1:${PUERTO}/${mapa.id}/{z}/{x}/{y}.pbf`);
      } catch (e: any) {
        console.error('[ML ERROR]', e?.message ?? String(e));
        setError(e?.message ?? String(e));
      }
    })();
    return () => {
      if (server) server.stop().catch(() => {});
      if (db) db.closeAsync().catch(() => {});
    };
  }, []);

  useEffect(() => {
    if (!userPos || !cameraRef.current?.jumpTo) return;
    if (!yaCentroRef.current) {
      try { cameraRef.current.jumpTo({ center: [userPos.longitude, userPos.latitude], zoom: 16 }); } catch (e) {}
      yaCentroRef.current = true;
    }
  }, [userPos]);


  // FIX: recentrar cuando initialCenter llegue después del montaje (reference detail)
  useEffect(() => {
    if (!initialCenter || !cameraRef.current?.jumpTo) return;
    if (!yaCentroRef.current) {
      try { cameraRef.current.jumpTo({ center: initialCenter, zoom: initialZoom ?? 15 }); } catch (e) {}
      yaCentroRef.current = true;
    }
  }, [initialCenter]);

  const containerStyle = absolute
    ? [styles.container, StyleSheet.absoluteFill as any]
    : styles.container;

  if (error || !uri) return <View style={containerStyle} />;

  const activeGeoJSON = trackPoints.length > 1 ? aGeoJSON(trackPoints) : null;
  const refGeoJSON = referencePoints.length > 1 ? aGeoJSON(referencePoints) : null;

  const sources: any = {
    local: { type: 'vector', tiles: [uri], minzoom: MINZOOM, maxzoom: MAXZOOM },
  };
  if (activeGeoJSON) sources.trackActivo = { type: 'geojson', data: activeGeoJSON };
  if (refGeoJSON) sources.trackRef = { type: 'geojson', data: refGeoJSON };

  // Orden de capas (de abajo hacia arriba):
  // background, agua, edificios, lineas, provincias, municipios, barrios,
  // rutas, servicios, trackRefLine, trackActivoLine.
  // Los tracks quedan SIEMPRE arriba de los textos.
  const layers: any[] = [
    { id: 'background', type: 'background', paint: { 'background-color': '#f5efe6' } },
    {
      id: 'pais_fill', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN_PAIS,
      filter: ['==', ['get', 'admin_level'], '2'],
      paint: { 'fill-color': '#e8dfd0', 'fill-opacity': 0.4 },
    },
    {
      id: 'pais_border', type: 'line', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN_PAIS,
      filter: ['==', ['get', 'admin_level'], '2'],
      paint: { 'line-color': '#8a7a6a', 'line-width': 1.5, 'line-opacity': 0.7 },
    },
    {
      id: 'pais_provincias_border', type: 'line', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN_PAIS,
      filter: ['==', ['get', 'admin_level'], '4'],
      paint: { 'line-color': '#b0a090', 'line-width': 0.8, 'line-opacity': 0.6 },
    },
    {
      id: 'pais_provincias_labels', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN_PAIS_LABELS,
      filter: ['all', ['==', ['get', 'admin_level'], '4'], ['has', 'name']],
      minzoom: 4,
      layout: {
        'text-field': ['coalesce', ['get', 'name:es'], ['get', 'name']],
        'text-size': ['interpolate', ['linear'], ['zoom'], 4, 10, 6, 14, 8, 18],
        'text-font': ['OpenSansBold'],
        'text-letter-spacing': 0.1,
        'text-max-width': 6,
        'text-allow-overlap': false,
        'text-padding': 40,
      },
      paint: { 'text-color': '#3a2a1a', 'text-halo-color': '#ffffff', 'text-halo-width': 2 },
    },
    { id: 'agua', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'fill-color': '#a8c8e0' } },
    { id: 'edificios', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'fill-color': '#d8c8b0', 'fill-opacity': 0.6 } },
    { id: 'lineas', type: 'line', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'line-color': '#7a8a9a', 'line-width': 1 } },
    {
      id: 'provincias', type: 'line', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN,
      filter: ['all', ['==', ['get', 'admin_level'], '4'], ['==', ['get', 'boundary'], 'administrative'], ['has', 'name']],
      paint: { 'line-color': '#5a6a7a', 'line-width': 2, 'line-opacity': 0.85 },
    },
    {
      id: 'municipios', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN,
      filter: ['all', ['has', 'admin_level'], ['in', ['get', 'admin_level'], ['literal', ['5', '6', '7', '8']]], ['has', 'name']],
      layout: {
        'text-field': ['coalesce', ['get', 'name:es'], ['get', 'name']],
        'text-size': ['case', ['==', ['get', 'admin_level'], '5'], 15, ['==', ['get', 'admin_level'], '6'], 14, ['==', ['get', 'admin_level'], '7'], 13, 11],
        'text-anchor': 'center',
        'text-font': ['OpenSansBold'],
      },
      paint: { 'text-color': '#1a1a1a', 'text-halo-color': '#ffffff', 'text-halo-width': 2 },
    },
    {
      id: 'barrios', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN, minzoom: 12,
      filter: ['all', ['has', 'admin_level'], ['in', ['get', 'admin_level'], ['literal', ['9', '10', '11']]], ['has', 'name']],
      layout: {
        'text-field': ['coalesce', ['get', 'name:es'], ['get', 'name']],
        'text-size': 10,
        'text-anchor': 'center',
        'text-font': ['OpenSansRegular'],
      },
      paint: { 'text-color': '#404040', 'text-halo-color': '#ffffff', 'text-halo-width': 1.5 },
    },
    {
      id: 'rutas', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER,
      filter: ['all', ['has', 'ref'], ['==', ['geometry-type'], 'LineString'], ['in', ['get', 'highway'], ['literal', ['motorway', 'trunk', 'primary', 'secondary']]]],
      layout: {
        'text-field': ['get', 'ref'],
        'symbol-placement': 'line',
        'text-size': 11,
        'text-rotation-alignment': 'map',
        'text-font': ['OpenSansRegular'],
      },
      paint: { 'text-color': '#7a5c00', 'text-halo-color': '#ffffff', 'text-halo-width': 1.5 },
    },
    {
      id: 'servicios', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER, minzoom: 12,
      filter: ['all', ['has', 'amenity'], ['has', 'name'], ['in', ['get', 'amenity'], ['literal', ['fuel', 'hospital', 'clinic', 'pharmacy']]]],
      layout: {
        'text-field': ['get', 'name'],
        'text-size': 10,
        'text-anchor': 'top',
        'text-font': ['OpenSansRegular'],
      },
      paint: { 'text-color': '#b80000', 'text-halo-color': '#ffffff', 'text-halo-width': 1.5 },
    },
  ];
  if (refGeoJSON) {
    layers.push({ id: 'trackRefLine', type: 'line', source: 'trackRef', paint: { 'line-color': '#00D9FF', 'line-width': 2, 'line-dasharray': [2, 2] } });
  }
  if (activeGeoJSON) {
    layers.push({ id: 'trackActivoLine', type: 'line', source: 'trackActivo', paint: { 'line-color': '#FF4055', 'line-width': 3 } });
  }

  const style = {
    version: 8,
    glyphs: 'http://127.0.0.1:8080/fonts/{fontstack}/{range}.pbf',
    sources,
    layers,
  };

  return (
    <View style={containerStyle}>
      <Map style={StyleSheet.absoluteFill as any} mapStyle={JSON.stringify(style)} logo={false} attribution={false} compassPosition={{ top: 60, right: 12 }}>
        <Camera
          ref={cameraRef}
          initialViewState={{ center: initialCenter ?? CENTER_DEFAULT, zoom: initialZoom ?? 16 }}
          minZoom={4}
          maxZoom={22}
        />
        {showUserLocation && <UserLocation visible={true} />}
      </Map>
    </View>
  );
});

const styles = StyleSheet.create({
  container: { flex: 1, overflow: 'hidden', backgroundColor: '#f5efe6' },
});
