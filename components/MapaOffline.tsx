import React, { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { Map, Camera, Marker, type CameraRef } from '@maplibre/maplibre-react-native';
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
const SOURCE_LAYER_ADMIN_PAIS_LABEL = (mapa as any).sourceLayerAdminPaisLabels || SOURCE_LAYER_ADMIN_PAIS;
const SOURCE_LAYER_ADMIN_LABEL = (mapa as any).sourceLayerAdminLabel || SOURCE_LAYER_ADMIN;
const SOURCE_LAYER_ADMIN_LABEL_SUB = (mapa as any).sourceLayerAdminLabelSub || SOURCE_LAYER_ADMIN;
const SOURCE_LAYER_NAUTICAL = (mapa as any).sourceLayerNautical || SOURCE_LAYER;
const SOURCE_LAYER_SEAMARK = (mapa as any).sourceLayerSeamark || SOURCE_LAYER;
const SOURCE_LAYER_WATER = (mapa as any).sourceLayerWater || SOURCE_LAYER;
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
  gapActive?: boolean;
  gapMarkers?: Array<{startLat:number;startLon:number;endLat:number;endLon:number;durationMs:number}>;
  autoFollow?: boolean;
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
  { trackPoints, referencePoints, userPos, absolute, initialCenter, initialZoom, showUserLocation = true, gapActive = false, gapMarkers = [], autoFollow = false },
  ref
) {
  const [uri, setUri] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cameraRef = useRef<CameraRef>(null);
  const yaCentroRef = useRef(false);
  const [blinkOn, setBlinkOn] = useState(true);

  useEffect(() => {
    if (!gapActive) {
      setBlinkOn(true);
      return;
    }
    const interval = setInterval(() => {
      setBlinkOn((v) => !v);
    }, 500);
    return () => {
      clearInterval(interval);
      setBlinkOn(true);
    };
  }, [gapActive]);

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
    if (autoFollow) {
      if (!yaCentroRef.current) {
        // Primera centrada: zoom 16
        try { cameraRef.current.jumpTo({ center: [userPos.longitude, userPos.latitude], zoom: 16 }); } catch (e) {}
        yaCentroRef.current = true;
      } else {
        // Seguimiento continuo: solo cambia el centro, respeta el zoom del usuario
        try { cameraRef.current.jumpTo({ center: [userPos.longitude, userPos.latitude] }); } catch (e) {}
      }
    } else if (!yaCentroRef.current) {
      // Vista de referencia: centra una sola vez y queda estatica
      try { cameraRef.current.jumpTo({ center: [userPos.longitude, userPos.latitude], zoom: 16 }); } catch (e) {}
      yaCentroRef.current = true;
    }
  }, [userPos, autoFollow]);


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
  if (gapMarkers.length > 0) {
    sources.gapArc = {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: gapMarkers.map((g, idx) => ({
          type: 'Feature' as const,
          properties: { idx, durationS: Math.round(g.durationMs / 1000) },
          geometry: {
            type: 'LineString' as const,
            coordinates: [[g.startLon, g.startLat], [g.endLon, g.endLat]],
          },
        })),
      },
    };
  }
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
      id: 'pais_provincias_labels', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN_PAIS_LABEL,
      filter: ['all', ['==', ['get', 'kind'], 'nivel_4'], ['has', 'name']],
      minzoom: 5,
      layout: {
        'text-field': ['coalesce', ['get', 'name:es'], ['get', 'name']],
        'text-size': ['interpolate', ['linear'], ['zoom'], 5, 11, 6, 14, 8, 18],
        'text-font': ['OpenSansBold'],
        'text-letter-spacing': 0.15,
        'text-max-width': 6,
        'text-allow-overlap': false,
        'text-padding': 20,
        'text-variable-anchor': ['center', 'top', 'bottom'],
      },
      paint: { 'text-color': '#3a2a1a', 'text-halo-color': '#ffffff', 'text-halo-width': 2 },
    },
    {
      id: 'water_fill', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER_WATER,
      filter: ['==', ['geometry-type'], 'Polygon'],
      minzoom: 5,
      paint: {
        'fill-color': ['match', ['coalesce', ['get', 'kind'], ''], 'natural_wetland', '#b8c8c0', '#a8c8e0'],
        'fill-opacity': ['interpolate', ['linear'], ['zoom'], 5, 0.6, 10, 0.75, 14, 0.85]
      },
    },
    {
      id: 'waterway_line', type: 'line', source: 'local', 'source-layer': SOURCE_LAYER_WATER,
      filter: ['==', ['geometry-type'], 'LineString'],
      minzoom: 5,
      paint: {
        'line-color': '#5a8aaa',
        'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.6, 10, 1.5, 14, 2.2]
      },
    },
    { id: 'edificios', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'fill-color': '#d8c8b0', 'fill-opacity': 0.6 } },
    { id: 'lineas', type: 'line', source: 'local', 'source-layer': SOURCE_LAYER, paint: { 'line-color': '#7a8a9a', 'line-width': 1 } },
    {
      id: 'provincias', type: 'line', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN,
      filter: ['all', ['==', ['get', 'admin_level'], '4'], ['==', ['get', 'boundary'], 'administrative'], ['has', 'name']],
      paint: { 'line-color': '#5a6a7a', 'line-width': 2, 'line-opacity': 0.85 },
    },
    {
      id: 'municipios', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN_LABEL,
      filter: ['all', ['has', 'label_kind'], ['in', ['get', 'label_kind'], ['literal', ['nivel_7', 'nivel_8']]], ['has', 'name']],
      minzoom: 8,
      layout: {
        'text-field': ['coalesce', ['get', 'label_text'], ['get', 'name']],
        'text-size': ['case', ['==', ['get', 'label_kind'], 'nivel_7'], 13, 11],
        'text-anchor': 'center',
        'text-font': ['OpenSansBold'],
        'symbol-sort-key': ['get', 'label_priority'],
        'text-allow-overlap': false,
      },
      paint: { 'text-color': '#1a1a1a', 'text-halo-color': '#ffffff', 'text-halo-width': 2 },
    },
    {
      id: 'sub_labels', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN_LABEL_SUB,
      filter: ['all', ['has', 'label_kind'], ['in', ['get', 'label_kind'], ['literal', ['nivel_5', 'nivel_6']]], ['has', 'name']],
      minzoom: 6,
      maxzoom: 9,
      layout: {
        'text-field': ['coalesce', ['get', 'label_text'], ['get', 'name']],
        'text-size': ['case', ['==', ['get', 'label_kind'], 'nivel_5'], 12, 11],
        'text-anchor': 'center',
        'text-font': ['OpenSansRegular'],
        'symbol-sort-key': ['get', 'label_priority'],
        'text-allow-overlap': false,
      },
      paint: { 'text-color': '#5a5a5a', 'text-halo-color': '#ffffff', 'text-halo-width': 1.5 },
    },
    {
      id: 'barrios', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER_ADMIN_LABEL, minzoom: 12,
      filter: ['all', ['has', 'label_kind'], ['in', ['get', 'label_kind'], ['literal', ['nivel_9', 'nivel_10', 'nivel_11']]], ['has', 'name']],
      layout: {
        'text-field': ['coalesce', ['get', 'label_text'], ['get', 'name']],
        'text-size': 10,
        'text-anchor': 'center',
        'text-font': ['OpenSansRegular'],
        'symbol-sort-key': ['get', 'label_priority'],
        'text-allow-overlap': false,
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
      filter: ['all', ['has', 'amenity'], ['has', 'name'], ['in', ['get', 'amenity'], ['literal', ['fuel', 'hospital', 'clinic', 'police']]]],
      layout: {
        'text-field': ['get', 'name'],
        'text-size': 10,
        'text-anchor': 'top',
        'text-font': ['OpenSansRegular'],
      },
      paint: { 'text-color': '#b80000', 'text-halo-color': '#ffffff', 'text-halo-width': 1.5 },
    },
    {
      id: 'nautical_points', type: 'circle', source: 'local', 'source-layer': SOURCE_LAYER_NAUTICAL,
      minzoom: 8,
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 8, 3, 10, 3.5, 14, 5],
        'circle-color': ['match', ['coalesce', ['get', 'kind'], ''],
          'man_made_lighthouse', '#ffcc33',
          'marina', '#00c8ff', 'harbour', '#00c8ff', 'ferry_terminal', '#00c8ff',
          'man_made_pier', '#7ec8e0', 'man_made_quay', '#7ec8e0', 'man_made_breakwater', '#7ec8e0',
          'waterway_dock', '#7ec8e0',
          'slipway', '#a8d8e8', 'mooring', '#a8d8e8',
          '#a8c8e0'],
        'circle-stroke-color': '#1a2a3a', 'circle-stroke-width': 1, 'circle-opacity': 0.95
      },
    },
    {
      id: 'nautical_labels', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER_NAUTICAL,
      minzoom: 10, filter: ['has', 'name'],
      layout: {
        'text-field': ['coalesce', ['get', 'name:es'], ['get', 'name']],
        'text-size': ['interpolate', ['linear'], ['zoom'], 10, 9, 12, 10, 14, 11],
        'text-variable-anchor': ['top', 'right', 'bottom', 'left'],
        'text-offset': [0, 0.8],
        'text-font': ['OpenSansRegular'],
        'text-allow-overlap': false,
        'symbol-sort-key': ['match', ['get', 'kind'], 'harbour', 10, 'ferry_terminal', 15, 'marina', 20, 'man_made_lighthouse', 25, 'man_made_quay', 30, 'man_made_pier', 30, 'waterway_dock', 35, 'slipway', 40, 'mooring', 50, 100],
      },
      paint: { 'text-color': '#0a4a6a', 'text-halo-color': '#ffffff', 'text-halo-width': 1.5 },
    },
    {
      id: 'seamark_areas', type: 'fill', source: 'local', 'source-layer': SOURCE_LAYER_SEAMARK,
      minzoom: 9,
      filter: ['all', ['==', ['geometry-type'], 'Polygon'], ['match', ['get', 'seamark:type'], ['restricted_area', 'anchorage', 'anchor_berth'], true, false]],
      paint: { 'fill-color': '#ffb52e', 'fill-opacity': 0.08 },
    },
    {
      id: 'seamark_points', type: 'circle', source: 'local', 'source-layer': SOURCE_LAYER_SEAMARK,
      minzoom: 9,
      filter: ['==', ['geometry-type'], 'Point'],
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 2.5, 11, 3.2, 14, 4],
        'circle-color': ['case',
          ['match', ['get', 'seamark:type'], ['buoy_isolated_danger', 'beacon_isolated_danger', 'wreck', 'obstruction', 'rock'], true, false], '#ff4055',
          ['all', ['match', ['get', 'seamark:type'], ['buoy_lateral', 'beacon_lateral'], true, false], ['==', ['get', 'seamark:buoy_lateral:colour'], 'red']], '#ff4055',
          ['all', ['match', ['get', 'seamark:type'], ['buoy_lateral', 'beacon_lateral'], true, false], ['==', ['get', 'seamark:buoy_lateral:colour'], 'green']], '#35d39a',
          ['match', ['get', 'seamark:type'], ['buoy_special_purpose', 'beacon_special_purpose'], true, false], '#ffcc33',
          ['match', ['get', 'seamark:type'], ['buoy_cardinal', 'beacon_cardinal', 'buoy_safe_water', 'beacon_safe_water'], true, false], '#d8e4e8',
          ['match', ['get', 'seamark:type'], ['light_major', 'light_minor'], true, false], '#ffdd55',
          ['match', ['get', 'seamark:type'], ['berth', 'harbour_basin'], true, false], '#00c8ff',
          ['match', ['get', 'seamark:type'], ['small_craft_facility'], true, false], '#7ec8e0',
          ['match', ['get', 'seamark:type'], ['distance_mark'], true, false], '#ffb52e',
          ['match', ['get', 'seamark:type'], ['recommended_track', 'fairway'], true, false], '#e8c88a',
          '#ffb52e'],
        'circle-stroke-color': '#1a0c0c', 'circle-stroke-width': 1, 'circle-opacity': 0.95
      },
    },
    {
      id: 'seamark_labels', type: 'symbol', source: 'local', 'source-layer': SOURCE_LAYER_SEAMARK,
      minzoom: 11,
      filter: ['all',
        ['has', 'name'],
        ['match', ['get', 'seamark:type'],
          ['harbour', 'harbour_basin', 'berth', 'fairway', 'small_craft_facility',
           'wreck', 'buoy_isolated_danger', 'beacon_isolated_danger',
           'mooring', 'landmark', 'bridge', 'coastguard_station',
           'pipeline_submarine', 'sea_area', 'light_major'],
          true, false]
      ],
      layout: {
        'text-field': ['case',
          ['all',
            ['match', ['get', 'seamark:type'], ['buoy_isolated_danger', 'beacon_isolated_danger', 'wreck'], true, false],
            ['in', '(', ['coalesce', ['get', 'name'], '']]
          ],
          'Peligro',
          ['coalesce', ['get', 'name:es'], ['get', 'name']]
        ],
        'text-size': ['interpolate', ['linear'], ['zoom'], 11, 9, 13, 10, 14, 11],
        'text-variable-anchor': ['top', 'right', 'bottom', 'left'],
        'text-offset': [0, 0.7],
        'text-font': ['OpenSansRegular'],
        'text-allow-overlap': false,
        'text-ignore-placement': false,
        'symbol-sort-key': ['match', ['get', 'seamark:type'],
          'wreck', 10,
          'buoy_isolated_danger', 12,
          'beacon_isolated_danger', 12,
          'harbour', 20,
          'fairway', 25,
          'harbour_basin', 30,
          'berth', 35,
          'small_craft_facility', 40,
          'mooring', 50,
          'light_major', 55,
          'coastguard_station', 60,
          'landmark', 70,
          'bridge', 75,
          'pipeline_submarine', 80,
          'sea_area', 85,
          100],
      },
      paint: { 'text-color': '#6a3a0a', 'text-halo-color': '#ffffff', 'text-halo-width': 1.2 },
    },
  ];
  if (refGeoJSON) {
    layers.push({ id: 'trackRefLine', type: 'line', source: 'trackRef', paint: { 'line-color': '#00D9FF', 'line-width': 2, 'line-dasharray': [2, 2] } });
  }
  if (activeGeoJSON && !gapActive) {
    layers.push({ id: 'trackActivoLine', type: 'line', source: 'trackActivo', paint: { 'line-color': '#FF4055', 'line-width': 3 } });
  }
  if (gapMarkers.length > 0) {
    // Capa inferior: borde negro continuo
    layers.push({
      id: 'gapArcBorder',
      type: 'line',
      source: 'gapArc',
      paint: {
        'line-color': '#000000',
        'line-width': 4,
      },
    });
    // Capa superior: línea amarilla punteada
    layers.push({
      id: 'gapArcLine',
      type: 'line',
      source: 'gapArc',
      paint: {
        'line-color': '#FFCC00',
        'line-width': 2,
        'line-dasharray': [3, 3],
      },
    });
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
        {showUserLocation && userPos && (
          <Marker lngLat={[userPos.longitude, userPos.latitude]}>
            <Animated.View
              style={{
                width: 22,
                height: 22,
                borderRadius: 11,
                backgroundColor: gapActive ? '#FFCC00' : '#0A84FF',
                borderWidth: 3,
                borderColor: '#000000',
                alignItems: 'center',
                justifyContent: 'center',
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 2 },
                shadowOpacity: 0.4,
                shadowRadius: 3,
                elevation: 6,
                opacity: blinkOn ? 1 : 0.2,
              }}
            >
              <View
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: 7,
                  backgroundColor: gapActive ? '#FFCC00' : '#0A84FF',
                  borderWidth: 2,
                  borderColor: '#FFFFFF',
                }}
              />
            </Animated.View>
          </Marker>
        )}
      </Map>
    </View>
  );
});

const styles = StyleSheet.create({
  container: { flex: 1, overflow: 'hidden', backgroundColor: '#f5efe6' },
});
