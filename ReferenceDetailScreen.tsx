import React, { useEffect, useRef, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSQLiteContext } from 'expo-sqlite';
import { getReferenceRoutePoints } from './db/journal';
import { colors, fonts, spacing, radii, glass } from './theme';
import { MapaOffline } from './components/MapaOffline';

export function ReferenceDetailScreen({ routeId, onBack }: { routeId: string; onBack: () => void }) {
  const db = useSQLiteContext();
  const [points, setPoints] = useState<{ lat: number; lon: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const mapRef = useRef<any>(null);

  useEffect(() => {
    (async () => {
      try {
        const pts = await getReferenceRoutePoints(db, routeId);
        setPoints(pts.map((p) => ({ lat: p.lat, lon: p.lon })));
      } catch (err) {
        console.warn('[REFERENCE] Error al cargar referencia:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, [db, routeId]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
      <ActivityIndicator size="large" color={colors.navigateCyan} />
      </View>
    );
  }

  const firstPoint = points[0];
  const lastPoint = points[points.length - 1];

  const centerPoint: [number, number] | undefined = firstPoint
    ? [
        points.reduce((sum, p) => sum + p.lon, 0) / points.length,
        points.reduce((sum, p) => sum + p.lat, 0) / points.length,
      ]
    : undefined;

  return (
    <View style={styles.container}>
    <View style={styles.header}>
    <TouchableOpacity onPress={onBack} style={styles.backButton}>
    <Text style={styles.backText}>‹ Volver</Text>
    </TouchableOpacity>
    <Text style={styles.title}>TRAYECTO DE REFERENCIA</Text>
    </View>

    <View style={styles.mapWrapper}>
    <MapaOffline
      ref={mapRef}
      trackPoints={[]}
      referencePoints={points.map((p) => ({ latitude: p.lat, longitude: p.lon }))}
      userPos={null}
      showUserLocation={false}
      initialCenter={centerPoint}
      initialZoom={15}
    />
    <View style={styles.mapBadge}>
      <Text style={styles.mapBadgeText}>{points.length} puntos</Text>
    </View>
    <TouchableOpacity
      style={styles.centerButton}
      onPress={() => {
        if (mapRef.current?.centerOn && centerPoint) {
          mapRef.current.centerOn({ latitude: centerPoint[1], longitude: centerPoint[0] }, 15);
        }
      }}
    >
      <Text style={styles.centerButtonText}>CENTRAR</Text>
    </TouchableOpacity>
    </View>

    <View style={styles.infoCard}>
    <View style={styles.infoRow}>
    <Ionicons name="location" size={16} color={colors.navigateCyan} />
    <Text style={styles.infoLabel}>Puntos:</Text>
    <Text style={styles.infoValue}>{points.length}</Text>
    </View>

    {firstPoint && (
      <View style={styles.infoRow}>
      <Ionicons name="play" size={16} color={colors.success} />
      <Text style={styles.infoLabel}>Inicio:</Text>
      <Text style={styles.infoValue}>
      {firstPoint.lat.toFixed(5)}, {firstPoint.lon.toFixed(5)}
      </Text>
      </View>
    )}

    {lastPoint && (
      <View style={styles.infoRow}>
      <Ionicons name="flag" size={16} color={colors.danger} />
      <Text style={styles.infoLabel}>Fin:</Text>
      <Text style={styles.infoValue}>
      {lastPoint.lat.toFixed(5)}, {lastPoint.lon.toFixed(5)}
      </Text>
      </View>
    )}

    </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.lg },
  loadingContainer: { flex: 1, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center' },
  header: { flexDirection: 'row', alignItems: 'center', gap: 16, marginBottom: spacing.lg },
  backButton: { paddingVertical: 8, paddingHorizontal: 12 },
  backText: { color: colors.navigateCyan, fontSize: 16, fontWeight: 'bold' },
  title: { fontSize: 18, fontWeight: 'bold', color: colors.textPrimary, letterSpacing: 1.2 },
  mapWrapper: {
    height: 260,
    borderRadius: radii.md,
    overflow: 'hidden',
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.glassBorder,
  },
  mapBadge: {
    position: 'absolute',
    bottom: 12,
    right: 12,
    backgroundColor: 'rgba(5, 25, 42, 0.75)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.glassBorder,
  },
  mapBadgeText: {
    color: colors.navigateCyan,
    fontSize: 10,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  centerButton: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: 'rgba(5, 25, 42, 0.75)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.glassBorder,
  },
  centerButtonText: {
    color: colors.navigateCyan,
    fontSize: 10,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  mapPlaceholder: {
    height: 200,
    borderRadius: radii.md,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.glassBorder,
    backgroundColor: '#0a1128',
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderTitle: {
    color: colors.navigateCyan,
    fontSize: 14,
    fontWeight: 'bold',
    letterSpacing: 1.2,
    marginTop: 12,
  },
  placeholderSub: {
    color: colors.textSecondary,
    fontSize: 11,
    marginTop: 6,
  },
  infoCard: { ...glass.dataPanel, padding: spacing.md },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  infoLabel: {
    color: colors.textSecondary,
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  infoValue: {
    color: colors.textPrimary,
    fontSize: 12,
    fontFamily: 'monospace',
  },
});
