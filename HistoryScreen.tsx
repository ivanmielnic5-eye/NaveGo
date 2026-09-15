import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, Alert, ScrollView } from 'react-native';
import { getAllSessions, createReferenceRouteFromSession, getAllReferenceRoutes, deleteSession, deleteReferenceRoute } from './db/journal';
import { colors, fonts, spacing, radii, glass } from './theme';

interface SessionItem {
  id: string;
  start_time: number;
  end_time?: number | null;
  total_distance?: number;
  title?: string;
  status?: string;
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
  const [creating, setCreating] = useState(false);

  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectedType, setSelectedType] = useState<'session' | 'reference'>('session');

  useEffect(() => {
    (async () => {
      try {
        const data = await getAllSessions(db);
        const refs = await getAllReferenceRoutes(db);
        setSessions(data);
        setReferenceRoutes(refs);
      } catch (err) {
        console.warn('[TRAYECTOS] Error al cargar:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, [db]);

  const reload = async () => {
    const data = await getAllSessions(db);
    const refs = await getAllReferenceRoutes(db);
    setSessions(data);
    setReferenceRoutes(refs);
  };

  const handleCreateReference = async (session: SessionItem) => {
    if (creating) return;
    const exists = referenceRoutes.some((ref) => ref.source_session_id === session.id);
    if (exists) {
      Alert.alert('Referencia ya existe', 'Este trayecto ya fue guardado como referencia.');
      return;
    }
    setCreating(true);
    try {
      await createReferenceRouteFromSession(db, session.id, session.title ?? 'Trayecto de referencia');
      Alert.alert('Referencia creada', 'El trayecto fue guardado como referencia.');
      await reload();
    } catch (err) {
      console.warn('[TRAYECTOS] Error al crear referencia:', err);
      Alert.alert('Error', 'No se pudo crear la referencia.');
    } finally {
      setCreating(false);
    }
  };

  const toggleSelection = (id: string, type: 'session' | 'reference') => {
    if (selectedType !== type) return;
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      if (next.size === 0) setSelectionMode(false);
      return next;
    });
  };

  const startSelection = (id: string, type: 'session' | 'reference') => {
    setSelectionMode(true);
    setSelectedType(type);
    setSelectedIds(new Set([id]));
  };

  const cancelSelection = () => {
    setSelectionMode(false);
    setSelectedIds(new Set());
  };

  const confirmDelete = () => {
    if (selectedIds.size === 0) return;
    const count = selectedIds.size;
    const isSession = selectedType === 'session';
    const plural = isSession
      ? (count === 1 ? 'trayecto' : 'trayectos')
      : (count === 1 ? 'referencia' : 'referencias');
    Alert.alert(
      'Borrar ' + plural,
      'Se van a borrar ' + count + ' ' + plural + '. Esta accion no se puede deshacer.',
      [
        { text: 'CANCELAR', style: 'cancel' },
        {
          text: 'BORRAR',
          style: 'destructive',
          onPress: async () => {
            try {
              for (const id of selectedIds) {
                if (isSession) await deleteSession(db, id);
                else await deleteReferenceRoute(db, id);
              }
              await reload();
              cancelSelection();
              Alert.alert('Listo', 'Se borraron ' + count + ' ' + plural + '.');
            } catch (err) {
              console.warn('[TRAYECTOS] Error al borrar:', err);
              Alert.alert('Error', 'No se pudieron borrar todos los elementos.');
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

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.contentContainer}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onBack} style={styles.backButton}>
            <Text style={styles.backText}>Volver</Text>
          </TouchableOpacity>
          <Text style={styles.title}>TRAYECTOS</Text>
        </View>

        <Text style={styles.sectionTitle}>Referencias guardadas</Text>
        {referenceRoutes.length === 0 && (
          <Text style={styles.emptyText}>No hay referencias guardadas.</Text>
        )}
        {referenceRoutes.map((ref) => {
          const isSelected = selectedIds.has(ref.id) && selectedType === 'reference';
          return (
            <TouchableOpacity
              key={ref.id}
              style={[styles.referenceCard, isSelected && styles.cardSelected]}
              onPress={() => selectionMode ? toggleSelection(ref.id, 'reference') : onSelect(ref.id, 'reference')}
              onLongPress={() => startSelection(ref.id, 'reference')}
            >
              <View style={styles.rowBetween}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.referenceName}>{ref.name}</Text>
                  <Text style={styles.referenceMeta}>
                    {(ref.distance_m ?? 0).toFixed(1)} m · {((ref.duration_s ?? 0) / 60).toFixed(1)} min
                  </Text>
                </View>
                {isSelected && <Text style={styles.checkmark}>OK</Text>}
              </View>
            </TouchableOpacity>
          );
        })}

        <Text style={styles.sectionTitle}>Trayectos</Text>
        {sessions.length === 0 && (
          <Text style={styles.emptyText}>No hay trayectos guardados.</Text>
        )}
        {sessions.map((s) => {
          const isActive = s.status === 'ACTIVE';
          const isSelected = selectedIds.has(s.id) && selectedType === 'session';
          return (
            <View key={s.id} style={[styles.sessionRow, isSelected && styles.cardSelected]}>
              <TouchableOpacity
                style={styles.sessionInfo}
                onPress={() => {
                  if (selectionMode) return toggleSelection(s.id, 'session');
                  if (isActive) return;
                  onSelect(s.id, 'session');
                }}
                onLongPress={() => { if (!isActive) startSelection(s.id, 'session'); }}
              >
                <View style={styles.rowBetween}>
                  <Text style={styles.sessionTitle}>{s.title ?? 'Trayecto NaveGo'}</Text>
                  {isActive && <Text style={styles.activeBadge}>EN CURSO</Text>}
                  {isSelected && <Text style={styles.checkmark}>OK</Text>}
                </View>
                <Text style={styles.sessionDate}>
                  {new Date(s.start_time).toLocaleDateString()} · {new Date(s.start_time).toLocaleTimeString()}
                </Text>
                <Text style={styles.sessionDistance}>{(s.total_distance ?? 0).toFixed(1)} m</Text>
              </TouchableOpacity>

              {!isActive && !selectionMode && (
                <TouchableOpacity style={styles.referenceButton} onPress={() => handleCreateReference(s)}>
                  <Text style={styles.referenceButtonText}>Usar como referencia</Text>
                </TouchableOpacity>
              )}
            </View>
          );
        })}
      </ScrollView>

      {selectionMode && (
        <View style={styles.bottomBar}>
          <TouchableOpacity onPress={cancelSelection} style={styles.cancelButton}>
            <Text style={styles.cancelButtonText}>CANCELAR</Text>
          </TouchableOpacity>
          <Text style={styles.counter}>{selectedIds.size} seleccionado{selectedIds.size !== 1 ? 's' : ''}</Text>
          <TouchableOpacity onPress={confirmDelete} style={styles.deleteButton}>
            <Text style={styles.deleteButtonText}>BORRAR</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  contentContainer: { padding: spacing.lg, paddingBottom: 120 },
  loadingContainer: { flex: 1, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center' },
  header: { flexDirection: 'row', alignItems: 'center', gap: 16, marginBottom: spacing.xl },
  backButton: { paddingVertical: 8, paddingHorizontal: 12 },
  backText: { color: colors.navigateCyan, fontSize: 16, fontWeight: 'bold' },
  title: { fontSize: 22, fontWeight: 'bold', color: colors.textPrimary, letterSpacing: 1.5 },
  sectionTitle: { fontSize: 14, fontWeight: 'bold', color: colors.navigateCyan, marginTop: 20, marginBottom: 10, letterSpacing: 1 },
  emptyText: { color: colors.textSecondary, textAlign: 'center', marginTop: 10, fontSize: 12 },
  referenceCard: { ...glass.telemetryTile, marginBottom: 10 },
  cardSelected: { borderColor: colors.navigateCyan, borderWidth: 2 },
  referenceName: { fontSize: 15, fontWeight: 'bold', color: colors.textPrimary },
  referenceMeta: { fontSize: 11, color: colors.textSecondary, marginTop: 4 },
  sessionRow: { ...glass.telemetryTile, marginBottom: 10 },
  sessionInfo: { flex: 1 },
  sessionTitle: { fontSize: 15, fontWeight: 'bold', color: colors.textPrimary },
  sessionDate: { fontSize: 11, color: colors.textSecondary, marginTop: 4 },
  sessionDistance: { fontSize: 12, color: colors.navigateCyan, marginTop: 4 },
  activeBadge: { fontSize: 9, color: colors.success, fontWeight: 'bold', letterSpacing: 0.5, paddingHorizontal: 6, paddingVertical: 2, borderWidth: 1, borderColor: colors.success, borderRadius: 4 },
  checkmark: { fontSize: 14, color: colors.navigateCyan, fontWeight: 'bold' },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  referenceButton: {
    marginTop: 10,
    backgroundColor: 'rgba(0, 217, 255, 0.15)',
    borderRadius: radii.sm,
    paddingVertical: 8,
    alignItems: 'center',
  },
  referenceButtonText: { color: colors.navigateCyan, fontSize: 12, fontWeight: 'bold' },
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(5, 25, 42, 0.95)',
    borderTopWidth: 1,
    borderTopColor: colors.glassBorder,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  cancelButton: { paddingVertical: 8, paddingHorizontal: 12 },
  cancelButtonText: { color: colors.textSecondary, fontSize: 13, fontWeight: 'bold', letterSpacing: 0.5 },
  counter: { color: colors.textPrimary, fontSize: 13, fontWeight: 'bold' },
  deleteButton: { backgroundColor: 'rgba(255, 64, 85, 0.15)', borderWidth: 1, borderColor: colors.danger, borderRadius: radii.sm, paddingVertical: 8, paddingHorizontal: 16 },
  deleteButtonText: { color: colors.danger, fontSize: 13, fontWeight: 'bold', letterSpacing: 0.5 },
});
