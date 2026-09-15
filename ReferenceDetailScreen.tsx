import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSQLiteContext } from 'expo-sqlite';
import { getReferenceRoutePoints, deleteReferenceRoute } from './db/journal';
import { colors, fonts, spacing, radii, glass } from './theme';

export function ReferenceDetailScreen({ routeId, onBack }: { routeId: string; onBack: () => void }) {
  const db = useSQLiteContext();
  const [points, setPoints] = useState<{ lat: number; lon: number }[]>([]);
  const [loading, setLoading] = useState(true);

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

  const handleDelete = () => {
    Alert.alert(
      'Borrar referencia',
      'Esta acción no se puede deshacer. ¿Confirmás el borrado?',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Borrar',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteReferenceRoute(db, routeId);
              onBack();
            } catch (err) {
              console.warn('[REFERENCE] Error al borrar:', err);
              Alert.alert('Error', 'No se pudo borrar la referencia.');
            }
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
      <ActivityIndicator size="large" color={colors.navigateCyan} />
      </View>
    );
  }

  const firstPoint = points[0];
  const lastPoint = points[points.length - 1];

  return (
    <View style={styles.container}>
    <View style={styles.header}>
    <TouchableOpacity onPress={onBack} style={styles.backButton}>
    <Text style={styles.backText}>‹ Volver</Text>
    </TouchableOpacity>
    <Text style={styles.title}>TRAYECTO DE REFERENCIA</Text>
    </View>

    <View style={styles.mapPlaceholder}>
    <Ionicons name="map-outline" size={48} color={colors.navigateCyan} />
    <Text style={styles.placeholderTitle}>MAPA PENDIENTE</Text>
    <Text style={styles.placeholderSub}>
    {points.length} puntos cargados
    </Text>
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

    <TouchableOpacity
    style={styles.deleteButton}
    onPress={handleDelete}
    >
    <Ionicons name="trash" size={16} color={colors.danger} />
    <Text style={styles.deleteButtonText}>BORRAR REFERENCIA</Text>
    </TouchableOpacity>
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
  deleteButton: {
    marginTop: 16,
    backgroundColor: 'rgba(255, 64, 85, 0.15)',
                                 borderRadius: radii.sm,
                                 paddingVertical: 12,
                                 alignItems: 'center',
                                 justifyContent: 'center',
                                 flexDirection: 'row',
                                 gap: 8,
                                 borderWidth: 1,
                                 borderColor: colors.danger,
  },
  deleteButtonText: {
    color: colors.danger,
    fontSize: 12,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
});
