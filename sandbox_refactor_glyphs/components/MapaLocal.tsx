import React, { useEffect, useRef, useState } from 'react';
import { View, StyleSheet, Text } from 'react-native';
import { Map, Camera, UserLocation, type CameraRef } from '@maplibre/maplibre-react-native';
import { Asset } from 'expo-asset';
import * as FileSystem from 'expo-file-system/legacy';
import * as SQLite from 'expo-sqlite';
import * as Location from 'expo-location';
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
const CENTER_DEFAULT: [number, number] = mapa.center;
const MINZOOM = mapa.minzoom;
const MAXZOOM = mapa.maxzoom;
const ZOOM = 14;

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

export default function MapaLocal() {
  const [uri, setUri] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [userPos, setUserPos] = useState<[number, number] | null>(null);
  const cameraRef = useRef<CameraRef>(null);

  useEffect(() => {
    let server: any = null;
    let db: SQLite.SQLiteDatabase | null = null;

    (async () => {
      try {
        console.log('[ML] Iniciando');
        await FileSystem.makeDirectoryAsync(DIR, { intermediates: true }).catch(() => {});

        const asset = Asset.fromModule(mapa.asset);
        await asset.downloadAsync();
        if (!asset.localUri) throw new Error('asset.localUri null');

        const info = await FileSystem.getInfoAsync(DB_PATH);
        if (!info.exists) {
          await FileSystem.copyAsync({ from: asset.localUri, to: DB_PATH });
        }
        console.log('[ML] Archivo OK');

        db = await SQLite.openDatabaseAsync(DB_NAME, undefined, DIR);
        console.log('[ML] SQLite OK');

        // ─── GLYPHS: copiar las 4 fuentes al filesystem ───
        await FileSystem.makeDirectoryAsync(FONTS_DIR + 'open-sans-regular/', { intermediates: true }).catch(() => {});
        await FileSystem.makeDirectoryAsync(FONTS_DIR + 'open-sans-bold/', { intermediates: true }).catch(() => {});
        await copiarFuente(FONT_OS_REGULAR_0, 'open-sans-regular', '0-255.pbf');
        await copiarFuente(FONT_OS_REGULAR_1, 'open-sans-regular', '256-511.pbf');
        await copiarFuente(FONT_OS_BOLD_0, 'open-sans-bold', '0-255.pbf');
        await copiarFuente(FONT_OS_BOLD_1, 'open-sans-bold', '256-511.pbf');
        console.log('[ML] fuentes OK');

        server = new HttpServer();
        await server.start(PUERTO, async (request: any) => {
          const path = (request && request.path) ? request.path : '';

          // ─── RUTA DE GLYPHS (debe ir ANTES del regex de tiles) ───
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
          return {
            statusCode: 200,
            headers: { 'Content-Type': 'application/x-protobuf', 'Content-Encoding': 'gzip' },
            body: ab,
          };
        });
        console.log('[ML] Server en', PUERTO);

        setUri(`http://127.0.0.1:${PUERTO}/${mapa.id}/{z}/{x}/{y}.pbf`);

        // ─── UBICACIÓN ───
        console.error('[LOC] Pidiendo permiso');
        const { status } = await Location.requestForegroundPermissionsAsync();
        console.error('[LOC] Permiso:', status);
        if (status === 'granted') {
          const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
          const coords: [number, number] = [loc.coords.longitude, loc.coords.latitude];
          console.error('[LOC] Posición:', coords);
          setUserPos(coords);
        }
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
    if (!uri) return;
    const timers = [1500, 3000, 5000].map((ms) =>
      setTimeout(() => {
        try {
          if (cameraRef.current?.jumpTo) {
            const target = userPos ?? CENTER_DEFAULT;
            cameraRef.current.jumpTo({ center: target, zoom: ZOOM });
          }
        } catch (e) {}
      }, ms)
    );
    return () => timers.forEach(clearTimeout);
  }, [uri, userPos]);

  if (error) return <View style={s.c}><Text style={s.t}>ERROR: {error}</Text></View>;
  if (!uri) return <View style={s.c}><Text style={s.t}>Cargando...</Text></View>;

  // Orden de capas (de abajo hacia arriba):
  // background, agua, edificios, lineas, municipios, barrios, rutas,
  // servicios, trackRefLine, trackActivoLine.
  // Los tracks quedan SIEMPRE arriba de los textos.
  const layers: any[] = [
    { id: 'background', type: 'background', paint: { 'background-color': '#f5efe6' } },
    { id: 'agua', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'fill-color': '#a8c8e0' } },
    { id: 'edificios', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'fill-color': '#d8c8b0', 'fill-opacity': 0.6 } },
    { id: 'lineas', type: 'line', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'line-color': '#7a8a9a', 'line-width': 1 } },
    {
      id: 'municipios', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER,
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
      id: 'barrios', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER, minzoom: 12,
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

  const style = {
    version: 8,
    glyphs: 'http://127.0.0.1:8080/fonts/{fontstack}/{range}.pbf',
    sources: { local: { type: 'vector', tiles: [uri], minzoom: MINZOOM, maxzoom: MAXZOOM } },
    layers,
  };

  return (
    <View style={s.c}>
      <Map style={s.m} mapStyle={JSON.stringify(style)}>
        <Camera
          ref={cameraRef}
          initialViewState={{ center: userPos ?? CENTER_DEFAULT, zoom: ZOOM }}
          minZoom={8}
          maxZoom={16}
        />
        <UserLocation visible={true} />
      </Map>
    </View>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, width: '100%', height: '100%', backgroundColor: '#000' },
  m: { flex: 1, width: '100%', height: '100%' },
  t: { color: '#fff', fontSize: 16, textAlign: 'center', marginTop: 100 },
});
