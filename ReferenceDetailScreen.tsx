import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import MapView, { Polyline } from 'react-native-maps';
import { useSQLiteContext } from 'expo-sqlite';
import { getReferenceRoutePoints } from './db/journal';
import { colors, fonts, spacing, radii, glass } from './theme';

export function ReferenceDetailScreen({ routeId, onBack }: { routeId: string; onBack: () => void }) {
  const db = useSQLiteContext();
  const [points, setPoints] = useState<{ latitude: number; longitude: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const pts = await getReferenceRoutePoints(db, routeId);
        setPoints(pts.map((p) => ({ latitude: p.lat, longitude: p.lon })));
      } catch (err) {
        console.warn('[REFERENCE] Error al cargar referencia:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, [db, routeId]);

  if (loading) {
    return <View style={styles.loadingContainer}><ActivityIndicator size="large" color={colors.navigateCyan} /></View>;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backText}>‹ Volver</Text>
        </TouchableOpacity>
        <Text style={styles.title}>DERROTA DE REFERENCIA</Text>
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

      <View style={styles.infoCard}>
        <Text style={styles.infoText}>Puntos: {points.length}</Text>
        <Text style={styles.infoText}>Derrota de referencia cargada localmente.</Text>
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
  map: { height: 250, borderRadius: radii.md, marginBottom: spacing.lg },
  infoCard: { ...glass.dataPanel },
  infoText: { color: colors.textSecondary, fontSize: 12, marginTop: 4 },
});




