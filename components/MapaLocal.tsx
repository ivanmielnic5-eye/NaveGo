import React, { useEffect, useRef, useState } from 'react';
import { View, StyleSheet, Text } from 'react-native';
import { Map, Camera, UserLocation, type CameraRef } from '@maplibre/maplibre-react-native';
import { Asset } from 'expo-asset';
import * as FileSystem from 'expo-file-system/legacy';
import * as SQLite from 'expo-sqlite';
import * as Location from 'expo-location';
import { HttpServer } from 'react-native-nitro-http-server';

const DIR = FileSystem.documentDirectory + 'maptest/';
const DB_NAME = 'santa_fe.mbtiles';
const DB_PATH = DIR + DB_NAME;
const PUERTO = 8080;
const SOURCE_LAYER = 'santa_fe';
const CENTER_DEFAULT: [number, number] = [-60.7, -31.63];
const ZOOM = 14;

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
        console.error('[ML] Iniciando');
        await FileSystem.makeDirectoryAsync(DIR, { intermediates: true }).catch(() => {});

        const asset = Asset.fromModule(require('../assets/maptest/santa_fe.mbtiles'));
        await asset.downloadAsync();
        if (!asset.localUri) throw new Error('asset.localUri null');

        const info = await FileSystem.getInfoAsync(DB_PATH);
        if (!info.exists) {
          await FileSystem.copyAsync({ from: asset.localUri, to: DB_PATH });
        }
        console.error('[ML] Archivo OK');

        db = await SQLite.openDatabaseAsync(DB_NAME, undefined, DIR);
        console.error('[ML] SQLite OK');

        server = new HttpServer();
        await server.start(PUERTO, async (request: any) => {
          const path = (request && request.path) ? request.path : '';
          const m = path.match(/^\/(\d+)\/(\d+)\/(\d+)\.pbf$/);
          if (!m) return { statusCode: 404, headers: { 'Content-Type': 'text/plain' }, body: 'nf' };
          const z = Number(m[1]);
          const x = Number(m[2]);
          const y = Number(m[3]);
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
        console.error('[ML] Server en', PUERTO);

        setUri(`http://127.0.0.1:${PUERTO}/{z}/{x}/{y}.pbf`);

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

  const style = {
    version: 8,
    sources: { local: { type: 'vector', tiles: [uri], minzoom: 8, maxzoom: 14 } },
    layers: [
      { id: 'background', type: 'background', paint: { 'background-color': '#f5efe6' } },
      { id: 'agua', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'fill-color': '#a8c8e0' } },
      { id: 'edificios', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'fill-color': '#d8c8b0', 'fill-opacity': 0.6 } },
      { id: 'lineas', type: 'line', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'line-color': '#7a8a9a', 'line-width': 1 } },
    ],
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
