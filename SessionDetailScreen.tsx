import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import MapView, { Polyline } from 'react-native-maps';
import { useSQLiteContext } from 'expo-sqlite';
import { getSessionDetail, getSessionFixes } from './db/journal';
import { colors, fonts, spacing, radii, glass } from './theme';

export function SessionDetailScreen({ sessionId, onBack }: { sessionId: string; onBack: () => void }) {
  const db = useSQLiteContext();
  const [detail, setDetail] = useState<any>(null);
  const [points, setPoints] = useState<{ latitude: number; longitude: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const det = await getSessionDetail(db, sessionId);
        const fixes = await getSessionFixes(db, sessionId);
        const coords = fixes
          .filter((f) => Number.isFinite(f.lat_raw) && Number.isFinite(f.lon_raw))
          .map((f) => ({ latitude: f.lat_raw, longitude: f.lon_raw }));
        setDetail(det);
        setPoints(coords);
      } catch (err) {
        console.warn('[DETAIL] Error al cargar sesión:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, [db, sessionId]);

  if (loading) {
    return <View style={styles.loadingContainer}><ActivityIndicator size="large" color={colors.navigateCyan} /></View>;
  }

  if (!detail) {
    return <View style={styles.loadingContainer}><Text style={styles.emptyText}>Sesión no encontrada.</Text></View>;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backText}>‹ Volver</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{detail.title ?? 'Sesión'}</Text>
      </View>

      <MapView
        style={styles.map}
        initialRegion={{
          latitude: points[0]?.latitude ?? -31.6333,
          longitude: points[0]?.longitude ?? -60.7000,
          latitudeDelta: 0.01,
          longitudeDelta: 0.01,
        }}
      >
        {points.length > 1 && <Polyline coordinates={points} strokeWidth={3} strokeColor={colors.navigateCyan} />}
      </MapView>

      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>DISTANCIA</Text>
          <Text style={styles.statValue}>{(detail.total_distance ?? 0).toFixed(1)} m</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>DURACIÓN</Text>
          <Text style={styles.statValue}>
            {detail.end_time ? Math.floor((detail.end_time - detail.start_time) / 60000) : 0} min
          </Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>FIXES</Text>
          <Text style={styles.statValue}>{detail.total_fixes ?? 0}</Text>
        </View>
      </View>

      <View style={styles.qualityCard}>
        <Text style={styles.qualityTitle}>CALIDAD DE EVIDENCIA</Text>
        <Text style={styles.qualityText}>GOOD: {detail.good_fixes ?? 0}</Text>
        <Text style={styles.qualityText}>SUSPECT: {detail.suspect_fixes ?? 0}</Text>
        <Text style={styles.qualityText}>REJECTED: {detail.rejected_fixes ?? 0}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.lg },
  loadingContainer: { flex: 1, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center' },
  emptyText: { color: colors.textSecondary },
  header: { flexDirection: 'row', alignItems: 'center', gap: 16, marginBottom: spacing.lg },
  backButton: { paddingVertical: 8, paddingHorizontal: 12 },
  backText: { color: colors.navigateCyan, fontSize: 16, fontWeight: 'bold' },
  title: { fontSize: 20, fontWeight: 'bold', color: colors.textPrimary },
  map: { height: 250, borderRadius: radii.md, marginBottom: spacing.lg },
  statsGrid: { flexDirection: 'row', gap: 10, marginBottom: spacing.lg },
  statCard: { ...glass.telemetryTile, flex: 1, alignItems: 'center' },
  statLabel: { ...fonts.label },
  statValue: { fontSize: 18, fontWeight: 'bold', color: colors.navigateCyan, marginTop: 6 },
  qualityCard: { ...glass.dataPanel, marginBottom: spacing.lg },
  qualityTitle: { ...fonts.label, marginBottom: 8 },
  qualityText: { color: colors.textSecondary, fontSize: 12, marginTop: 4 },
});




