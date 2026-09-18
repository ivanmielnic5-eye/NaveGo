import React, { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';
import { View, StyleSheet } from 'react-native';
import { Map, Camera, UserLocation, type CameraRef } from '@maplibre/maplibre-react-native';
import { Asset } from 'expo-asset';
import * as FileSystem from 'expo-file-system/legacy';
import * as SQLite from 'expo-sqlite';
import { HttpServer } from 'react-native-nitro-http-server';

const DIR = FileSystem.documentDirectory + 'maptest/';
const DB_NAME = 'santa_fe.mbtiles';
const DB_PATH = DIR + DB_NAME;
const PUERTO = 8080;
const SOURCE_LAYER = 'santa_fe';
const CENTER_DEFAULT: [number, number] = [-60.7, -31.63];

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
        const asset = Asset.fromModule(require('../assets/maptest/santa_fe.mbtiles'));
        await asset.downloadAsync();
        if (!asset.localUri) throw new Error('asset.localUri null');
        const info = await FileSystem.getInfoAsync(DB_PATH);
        if (!info.exists) {
          await FileSystem.copyAsync({ from: asset.localUri, to: DB_PATH });
        }
        db = await SQLite.openDatabaseAsync(DB_NAME, undefined, DIR);
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
          return { statusCode: 200, headers: { 'Content-Type': 'application/x-protobuf', 'Content-Encoding': 'gzip' }, body: ab };
        });
        setUri(`http://127.0.0.1:${PUERTO}/{z}/{x}/{y}.pbf`);
      } catch (e: any) {
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
    local: { type: 'vector', tiles: [uri], minzoom: 8, maxzoom: 14 },
  };
  if (activeGeoJSON) sources.trackActivo = { type: 'geojson', data: activeGeoJSON };
  if (refGeoJSON) sources.trackRef = { type: 'geojson', data: refGeoJSON };

  const layers: any[] = [
    { id: 'background', type: 'background', paint: { 'background-color': '#f5efe6' } },
    { id: 'agua', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'fill-color': '#a8c8e0' } },
    { id: 'edificios', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'fill-color': '#d8c8b0', 'fill-opacity': 0.6 } },
    { id: 'lineas', type: 'line', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'line-color': '#7a8a9a', 'line-width': 1 } },
  ];
  if (refGeoJSON) {
    layers.push({ id: 'trackRefLine', type: 'line', source: 'trackRef', paint: { 'line-color': '#00D9FF', 'line-width': 2, 'line-dasharray': [2, 2] } });
  }
  if (activeGeoJSON) {
    layers.push({ id: 'trackActivoLine', type: 'line', source: 'trackActivo', paint: { 'line-color': '#FF4055', 'line-width': 3 } });
  }

  const style = { version: 8, sources, layers };

  return (
    <View style={containerStyle}>
      <Map style={StyleSheet.absoluteFill as any} mapStyle={JSON.stringify(style)} logoEnabled={false} attributionEnabled={false}>
        <Camera
          ref={cameraRef}
          initialViewState={{ center: initialCenter ?? CENTER_DEFAULT, zoom: initialZoom ?? 16 }}
          minZoom={8}
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
