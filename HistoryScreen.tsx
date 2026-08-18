import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { getAllSessions, createReferenceRouteFromSession, getAllReferenceRoutes } from './db/journal';
import { colors, fonts, spacing, radii, glass } from './theme';

interface SessionItem {
  id: string;
  start_time: number;
  end_time?: number | null;
  total_distance?: number;
  title?: string;
}

export function HistoryScreen({
  db,
  onBack,
  onSelect,
}: {
  db: any;
  onBack: () => void;
  onSelect: (id: string, type: 'session' | 'reference') => void;
}) {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [referenceRoutes, setReferenceRoutes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await getAllSessions(db);
        const refs = await getAllReferenceRoutes(db);
        setSessions(data);
        setReferenceRoutes(refs);
      } catch (err) {
        console.warn('[HISTORY] Error al cargar sesiones:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, [db]);

  const handleCreateReference = async (session: SessionItem) => {
    try {
      await createReferenceRouteFromSession(db, session.id, session.title ?? 'Derrota referencia');
      Alert.alert('Derrota creada', 'La sesión fue guardada como derrota de referencia.');
      const refs = await getAllReferenceRoutes(db);
      setReferenceRoutes(refs);
    } catch (err) {
      console.warn('[HISTORY] Error al crear referencia:', err);
      Alert.alert('Error', 'No se pudo crear la derrota de referencia.');
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.navigateCyan} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backText}>‹ Volver</Text>
        </TouchableOpacity>
        <Text style={styles.title}>DERROTAS</Text>
      </View>

      {/* REFERENCIAS */}
      <Text style={styles.sectionTitle}>Referencias guardadas</Text>
      {referenceRoutes.length === 0 && (
        <Text style={styles.emptyText}>No hay derrotas de referencia.</Text>
      )}
      {referenceRoutes.map((ref) => (
        <TouchableOpacity
          key={ref.id}
          style={styles.referenceCard}
          onPress={() => onSelect(ref.id, 'reference')}
        >
          <Text style={styles.referenceName}>{ref.name}</Text>
          <Text style={styles.referenceMeta}>
            {(ref.distance_m ?? 0).toFixed(1)} m · {(ref.duration_s / 60).toFixed(1)} min
          </Text>
        </TouchableOpacity>
      ))}

      {/* SESIONES */}
      <Text style={styles.sectionTitle}>Sesiones</Text>
      {sessions.map((s) => (
        <View key={s.id} style={styles.sessionRow}>
          <TouchableOpacity style={styles.sessionInfo} onPress={() => onSelect(s.id, 'session')}>
            <Text style={styles.sessionTitle}>{s.title ?? 'Sesión NaveGo'}</Text>
            <Text style={styles.sessionDate}>
              {new Date(s.start_time).toLocaleDateString()} · {new Date(s.start_time).toLocaleTimeString()}
            </Text>
            <Text style={styles.sessionDistance}>{(s.total_distance ?? 0).toFixed(1)} m</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.referenceButton} onPress={() => handleCreateReference(s)}>
            <Text style={styles.referenceButtonText}>Usar como referencia</Text>
          </TouchableOpacity>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.lg },
  loadingContainer: { flex: 1, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center' },
  header: { flexDirection: 'row', alignItems: 'center', gap: 16, marginBottom: spacing.xl },
  backButton: { paddingVertical: 8, paddingHorizontal: 12 },
  backText: { color: colors.navigateCyan, fontSize: 16, fontWeight: 'bold' },
  title: { fontSize: 22, fontWeight: 'bold', color: colors.textPrimary, letterSpacing: 1.5 },
  sectionTitle: { fontSize: 14, fontWeight: 'bold', color: colors.navigateCyan, marginTop: 20, marginBottom: 10, letterSpacing: 1 },
  emptyText: { color: colors.textSecondary, textAlign: 'center', marginTop: 10 },
  referenceCard: { ...glass.telemetryTile, marginBottom: 10 },
  referenceName: { fontSize: 15, fontWeight: 'bold', color: colors.textPrimary },
  referenceMeta: { fontSize: 11, color: colors.textSecondary, marginTop: 4 },
  sessionRow: { ...glass.telemetryTile, marginBottom: 10 },
  sessionInfo: { flex: 1 },
  sessionTitle: { fontSize: 15, fontWeight: 'bold', color: colors.textPrimary },
  sessionDate: { fontSize: 11, color: colors.textSecondary, marginTop: 4 },
  sessionDistance: { fontSize: 12, color: colors.navigateCyan, marginTop: 4 },
  referenceButton: {
    marginTop: 10,
    backgroundColor: 'rgba(0, 217, 255, 0.15)',
    borderRadius: radii.sm,
    paddingVertical: 8,
    alignItems: 'center',
  },
  referenceButtonText: { color: colors.navigateCyan, fontSize: 12, fontWeight: 'bold' },
});