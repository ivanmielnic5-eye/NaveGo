import React, { useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Asset } from 'expo-asset';
import * as SQLite from 'expo-sqlite';
import { Directory, File, Paths } from 'expo-file-system';

type DbResult = {
  nombre: string;
  archivo: string;
  tamanoBytes: number | null;
  tamanoMB: string;
  aperturaMs: number | null;
  navigationSelectMs: number | null;
  navigationRows: number | null;
  tilesCountMs: number | null;
  tilesCount: number | null;
  tilesFirstMs: number | null;
  error?: string;
};

const DOCUMENTS_MAPTEST = new Directory(Paths.document, 'maptest');

const ASSETS = {
  hibrido: require('../assets/maptest/test_hibrido.mbtiles'),
  render: require('../assets/maptest/render.mbtiles'),
  navigation: require('../assets/maptest/navigation.sqlite'),
  renderBig: require('../assets/maptest/render_big.mbtiles'),
};

const TESTS = [
  { key: 'hibrido', nombre: 'Hibrido', archivo: 'test_hibrido.mbtiles', asset: ASSETS.hibrido },
  { key: 'render', nombre: 'Render', archivo: 'render.mbtiles', asset: ASSETS.render },
  { key: 'navigation', nombre: 'Navigation', archivo: 'navigation.sqlite', asset: ASSETS.navigation },
  { key: 'renderBig', nombre: 'Render Big', archivo: 'render_big.mbtiles', asset: ASSETS.renderBig },
] as const;

function nowMs(): number {
  return globalThis.performance?.now ? globalThis.performance.now() : Date.now();
}

function bytesToMB(bytes: number): string {
  return (bytes / (1024 * 1024)).toFixed(3);
}

async function copyAssetToDocuments(assetModule: number, filename: string): Promise<string> {
  DOCUMENTS_MAPTEST.create({ idempotent: true, intermediates: true });
  const asset = Asset.fromModule(assetModule);
  await asset.downloadAsync();
  if (!asset.localUri) throw new Error('Asset sin localUri: ' + filename);
  const source = new File(asset.localUri);
  const destination = new File(DOCUMENTS_MAPTEST, filename);
  if (destination.exists) destination.delete();
  source.copy(destination);
  if (!destination.exists) throw new Error('No se pudo copiar ' + filename);
  return destination.uri;
}

async function openAndMeasure(test: (typeof TESTS)[number]): Promise<DbResult> {
  const result: DbResult = {
    nombre: test.nombre,
    archivo: test.archivo,
    tamanoBytes: null,
    tamanoMB: '-',
    aperturaMs: null,
    navigationSelectMs: null,
    navigationRows: null,
    tilesCountMs: null,
    tilesCount: null,
    tilesFirstMs: null,
  };

  let db: SQLite.SQLiteDatabase | null = null;

  try {
    const fileUri = await copyAssetToDocuments(test.asset, test.archivo);
    const file = new File(fileUri);
    result.tamanoBytes = file.size;
    result.tamanoMB = file.size != null ? bytesToMB(file.size) : '-';

    const openStart = nowMs();
    db = await SQLite.openDatabaseAsync(test.archivo, undefined, DOCUMENTS_MAPTEST.uri);
    result.aperturaMs = Number((nowMs() - openStart).toFixed(3));

    try {
      const navStart = nowMs();
      const rows = await db.getAllAsync<Record<string, unknown>>('SELECT * FROM navigation_features');
      result.navigationSelectMs = Number((nowMs() - navStart).toFixed(3));
      result.navigationRows = rows.length;
    } catch (e) {
      result.navigationSelectMs = null;
      result.navigationRows = null;
    }

    try {
      const countStart = nowMs();
      const row = await db.getFirstAsync<{ count: number }>('SELECT COUNT(*) AS count FROM tiles');
      result.tilesCountMs = Number((nowMs() - countStart).toFixed(3));
      result.tilesCount = row?.count ?? null;
    } catch (e) {
      result.tilesCountMs = null;
      result.tilesCount = null;
    }

    try {
      const firstStart = nowMs();
      await db.getFirstAsync('SELECT * FROM tiles LIMIT 1');
      result.tilesFirstMs = Number((nowMs() - firstStart).toFixed(3));
    } catch (e) {
      result.tilesFirstMs = null;
    }
  } catch (error) {
    result.error = error instanceof Error ? error.message : String(error);
  } finally {
    if (db) {
      try { await db.closeAsync(); } catch {}
    }
  }

  return result;
}

export default function TestMapLibre() {
  const [results, setResults] = useState<DbResult[]>([]);
  const [running, setRunning] = useState(false);

  async function runTest() {
    if (running) return;
    setRunning(true);
    setResults([]);
    try {
      const newResults: DbResult[] = [];
      for (const test of TESTS) {
        const result = await openAndMeasure(test);
        newResults.push(result);
        setResults([...newResults]);
      }
    } finally {
      setRunning(false);
    }
  }

  function formatMs(value: number | null): string {
    return value == null ? '-' : value.toFixed(3) + ' ms';
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>TEST CARTOGRAFICO - SQLITE</Text>
        <Text style={styles.subtitle}>U-08 - NaveGo - Sin render - Sin red</Text>

        <View style={styles.infoBox}>
          <Text style={styles.infoText}>Dispositivo: TCL T610P</Text>
          <Text style={styles.infoText}>Objetivo: medir SQLite puro</Text>
          <Text style={styles.infoText}>Archivos: 3</Text>
        </View>

        <TouchableOpacity
          style={[styles.button, running && styles.buttonDisabled]}
          onPress={runTest}
          disabled={running}
        >
          {running ? (
            <>
              <ActivityIndicator size="small" color="#fff" />
              <Text style={styles.buttonText}>Ejecutando...</Text>
            </>
          ) : (
            <Text style={styles.buttonText}>Correr test</Text>
          )}
        </TouchableOpacity>

        {results.map((item) => (
          <View key={item.archivo} style={styles.card}>
            <Text style={styles.cardTitle}>{item.nombre}</Text>
            <Text style={styles.fileName}>{item.archivo}</Text>
            {item.error ? (
              <Text style={styles.error}>ERROR: {item.error}</Text>
            ) : (
              <>
                <Row label="Tamano" value={item.tamanoMB + ' MB'} />
                <Row label="Apertura SQLite" value={formatMs(item.aperturaMs)} />
                <Row
                  label="navigation_features"
                  value={
                    item.navigationRows == null
                      ? 'No disponible'
                      : item.navigationRows + ' filas - ' + formatMs(item.navigationSelectMs)
                  }
                />
                <Row
                  label="tiles COUNT(*)"
                  value={
                    item.tilesCount == null
                      ? 'No disponible'
                      : item.tilesCount + ' filas - ' + formatMs(item.tilesCountMs)
                  }
                />
                <Row label="tiles LIMIT 1" value={formatMs(item.tilesFirstMs)} />
              </>
            )}
          </View>
        ))}

        {results.length === 3 && (
          <View style={styles.footerBox}>
            <Text style={styles.footerTitle}>TEST COMPLETADO</Text>
            <Text style={styles.footerText}>Los resultados son mediciones del dispositivo real.</Text>
            <Text style={styles.footerText}>No se ha utilizado MapLibre.</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#08111f' },
  content: { padding: 20, paddingTop: 50, paddingBottom: 40 },
  title: { color: '#ffffff', fontSize: 24, fontWeight: '700', marginBottom: 6 },
  subtitle: { color: '#8fa5bb', fontSize: 14, marginBottom: 20 },
  infoBox: { backgroundColor: '#101d2d', borderRadius: 10, padding: 14, marginBottom: 16 },
  infoText: { color: '#dce7f0', fontSize: 14, marginBottom: 4 },
  button: { minHeight: 54, borderRadius: 10, backgroundColor: '#1e6f9f', alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 10, marginBottom: 18 },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#ffffff', fontSize: 17, fontWeight: '700' },
  card: { backgroundColor: '#101d2d', borderRadius: 12, padding: 16, marginBottom: 14 },
  cardTitle: { color: '#ffffff', fontSize: 19, fontWeight: '700', marginBottom: 3 },
  fileName: { color: '#7590a7', fontSize: 12, marginBottom: 14 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', borderTopWidth: 1, borderTopColor: '#203044', paddingVertical: 9, gap: 12 },
  rowLabel: { flex: 1, color: '#aebfd0', fontSize: 13 },
  rowValue: { flex: 1, color: '#ffffff', fontSize: 13, fontWeight: '600', textAlign: 'right' },
  error: { color: '#ff6875', fontSize: 13 },
  footerBox: { backgroundColor: '#142637', borderRadius: 12, padding: 16, marginTop: 4 },
  footerTitle: { color: '#ffffff', fontSize: 16, fontWeight: '700', marginBottom: 6 },
  footerText: { color: '#aec0d0', fontSize: 13, marginBottom: 3 },
});
