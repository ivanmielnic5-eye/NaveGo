import React, { useEffect, useRef, useState } from 'react';
import { View, StyleSheet, Text } from 'react-native';
import { Map, Camera, type CameraRef } from '@maplibre/maplibre-react-native';
import { Asset } from 'expo-asset';
import * as FileSystem from 'expo-file-system/legacy';
import * as SQLite from 'expo-sqlite';
import { HttpServer } from 'react-native-nitro-http-server';

const DIR = FileSystem.documentDirectory + 'maptest/';
const DB_NAME = 'render_big.mbtiles';
const DB_PATH = DIR + DB_NAME;
const PUERTO = 8080;
const SOURCE_LAYER = 'tucuman';
const CENTER: [number, number] = [-65.2, -26.8];
const ZOOM = 10;

export default function MapaLocal() {
  const [uri, setUri] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cameraRef = useRef<CameraRef>(null);

  useEffect(() => {
    let server: any = null;
    let db: SQLite.SQLiteDatabase | null = null;

    (async () => {
      try {
        console.error('[ML] 1. Iniciando');
        await FileSystem.makeDirectoryAsync(DIR, { intermediates: true }).catch(() => {});

        const asset = Asset.fromModule(require('../assets/maptest/render_big.mbtiles'));
        await asset.downloadAsync();
        if (!asset.localUri) throw new Error('asset.localUri null');

        const info = await FileSystem.getInfoAsync(DB_PATH);
        if (!info.exists) {
          await FileSystem.copyAsync({ from: asset.localUri, to: DB_PATH });
        }
        console.error('[ML] 2. Archivo OK');

        db = await SQLite.openDatabaseAsync(DB_NAME, undefined, DIR);
        console.error('[ML] 3. SQLite OK');

        server = new HttpServer();
        await server.start(PUERTO, async (request: any) => {
          const path = (request && request.path) ? request.path : '';
          const m = path.match(/^\/(\d+)\/(\d+)\/(\d+)\.pbf$/);
          if (!m) {
            console.error('[REQ] no-match', path);
            return { statusCode: 404, headers: { 'Content-Type': 'text/plain' }, body: 'not found' };
          }
          const z = Number(m[1]);
          const x = Number(m[2]);
          const y = Number(m[3]);
          const yTms = (1 << z) - 1 - y;
          const row = await db!.getFirstAsync<{ tile_data: Uint8Array }>(
            'SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?',
            [z, x, yTms]
          );
          if (!row || !row.tile_data) {
            console.error('[REQ MISS]', z, x, y);
            return { statusCode: 404, headers: { 'Content-Type': 'text/plain' }, body: 'no tile' };
          }
          console.error('[REQ OK]', z, x, y, 'size', row.tile_data.byteLength);
          const ab = row.tile_data.buffer.slice(
            row.tile_data.byteOffset,
            row.tile_data.byteOffset + row.tile_data.byteLength
          );
          return {
            statusCode: 200,
            headers: { 'Content-Type': 'application/x-protobuf' },
            body: ab,
          };
        });
        console.error('[ML] 4. Server en', PUERTO);

        setUri(`http://127.0.0.1:${PUERTO}/{z}/{x}/{y}.pbf`);
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

  // Después de montar el mapa, forzar la cámara con el ref del <Camera>
  useEffect(() => {
    if (!uri) return;
    const timers = [1500, 3000, 5000].map((ms) =>
      setTimeout(() => {
        try {
          if (cameraRef.current?.jumpTo) {
            cameraRef.current.jumpTo({ center: CENTER, zoom: ZOOM });
            console.error('[CAM] jumpTo OK', ms);
          }
        } catch (e: any) {
          console.error('[CAM ERROR]', e?.message);
        }
      }, ms)
    );
    return () => timers.forEach(clearTimeout);
  }, [uri]);

  if (error) return <View style={s.c}><Text style={s.t}>ERROR: {error}</Text></View>;
  if (!uri) return <View style={s.c}><Text style={s.t}>Cargando...</Text></View>;

  const style = {
    version: 8,
    sources: {
      local: {
        type: 'vector',
        tiles: [uri],
        minzoom: 8,
        maxzoom: 14,
      },
    },
    layers: [
      { id: 'background', type: 'background', paint: { 'background-color': '#e8e0d8' } },
      {
        id: 'agua',
        type: 'fill',
        source: 'local',
        'source-layer': SOURCE_LAYER,
        filter: ['==', ['geometry-type'], 'Polygon'],
        paint: { 'fill-color': '#a5c8e0' },
      },
      {
        id: 'edificios',
        type: 'fill',
        source: 'local',
        'source-layer': SOURCE_LAYER,
        filter: ['==', ['geometry-type'], 'Polygon'],
        paint: { 'fill-color': '#c8b8a0', 'fill-opacity': 0.5 },
      },
      {
        id: 'lineas',
        type: 'line',
        source: 'local',
        'source-layer': SOURCE_LAYER,
        filter: ['==', ['geometry-type'], 'LineString'],
        paint: { 'line-color': '#556677', 'line-width': 1 },
      },
    ],
  };

  return (
    <View style={s.c}>
      <Map style={s.m} mapStyle={JSON.stringify(style)}>
        <Camera
          ref={cameraRef}
          initialViewState={{ center: CENTER, zoom: ZOOM }}
          minZoom={8}
          maxZoom={14}
        />
      </Map>
    </View>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: '#000' },
  m: { flex: 1 },
  t: { color: '#fff', fontSize: 16, textAlign: 'center', marginTop: 100 },
});
