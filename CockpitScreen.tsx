import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts, glass, spacing, radii } from './theme';
import { createNaveGoAdapterState } from './cockpit/adapters/navego/NaveGoProjectAdapter';

type ModuleKey = 'estado' | 'trabajo' | 'evidencia' | 'archivos' | 'accion';

const modules: { key: ModuleKey; label: string; icon: string }[] = [
  { key: 'estado', label: 'Estado', icon: 'pulse' },
  { key: 'trabajo', label: 'Trabajo', icon: 'flask' },
  { key: 'evidencia', label: 'Evidencia', icon: 'eye' },
  { key: 'archivos', label: 'Archivos', icon: 'folder' },
  { key: 'accion', label: 'Accion', icon: 'mic' },
];

export function CockpitScreen({ tracker }: { tracker?: any }) {
  const [active, setActive] = useState<ModuleKey>('estado');

  const adapterState = tracker ? createNaveGoAdapterState(tracker) : null;

  const getGnssColor = () => {
    switch (tracker?.navigationStatus) {
      case 'CONFIABLE': return colors.success;
      case 'RECUPERANDO':
      case 'DEGRADADO': return colors.warning;
      case 'GNSS_PERDIDO':
      case 'NO_CONFIABLE': return colors.danger;
      default: return colors.textSecondary;
    }
  };

  const getSyncColor = () => {
    if (tracker?.syncOk === true) return colors.success;
    if (tracker?.syncOk === false) return colors.danger;
    return colors.warning;
  };

  const renderContent = () => {
    switch (active) {
      case 'estado':
        return (
          <View style={styles.section}>
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Ionicons name="pulse" size={20} color={colors.navigateCyan} />
                <Text style={styles.cardTitle}>Estado del Proyecto</Text>
              </View>
              {adapterState ? (
                <>
                  <Text style={styles.cardText}>Proyecto: {adapterState.project}</Text>
                  <Text style={styles.cardText}>Misión: {adapterState.mission}</Text>
                  <Text style={styles.cardText}>Estado: {adapterState.status}</Text>
                  <Text style={styles.cardText}>Sesión: {adapterState.session}</Text>
                  <Text style={styles.cardText}>Última actualización: {adapterState.lastUpdate ?? 'Sin señal'}</Text>
                  <Text style={styles.cardText}>Salud:</Text>
                  {adapterState.health.map((h) => (
                    <Text key={h.name} style={styles.cardText}>  {h.name}: {h.status}</Text>
                  ))}
                </>
              ) : (
                <Text style={styles.cardText}>Sin datos del tracker.</Text>
              )}
            </View>
          </View>
        );
      case 'trabajo':
        return (
          <View style={styles.section}>
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Ionicons name="flask" size={20} color={colors.navigateCyan} />
                <Text style={styles.cardTitle}>Trabajo Actual</Text>
              </View>
              <Text style={styles.cardText}>Course-Up / Sincronización mapa ↔ COG</Text>
              <Text style={styles.cardText}>Estado: EXPERIMENTAL</Text>
              <Text style={styles.cardText}>Próximo paso: validar en movimiento real.</Text>
              <TouchableOpacity style={styles.primaryButton}>
                <Text style={styles.primaryButtonText}>CONTINUAR</Text>
              </TouchableOpacity>
            </View>
          </View>
        );
      case 'evidencia':
        return (
          <View style={styles.section}>
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Ionicons name="eye" size={20} color={colors.navigateCyan} />
                <Text style={styles.cardTitle}>Evidencia</Text>
              </View>
              <Text style={styles.cardText}>IMPLEMENTADO: Course-Up</Text>
              <Text style={styles.cardText}>PROBADO: en interior</Text>
              <Text style={styles.cardText}>OBSERVADO: rota según COG</Text>
              <Text style={styles.cardText}>VALIDADO: no todavía</Text>
            </View>
          </View>
        );
      case 'archivos':
        return (
          <View style={styles.section}>
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Ionicons name="folder" size={20} color={colors.navigateCyan} />
                <Text style={styles.cardTitle}>Documentos Vivos</Text>
              </View>
              <Text style={styles.cardText}>PROJECT_STATE.md</Text>
              <Text style={styles.cardText}>DECISIONS.md</Text>
              <Text style={styles.cardText}>TEST_LOG.md</Text>
              <Text style={styles.cardText}>CHANGE_LOG.md</Text>
              <Text style={styles.cardText}>ARCHITECTURE.md</Text>
            </View>
          </View>
        );
      case 'accion':
        return (
          <View style={styles.section}>
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Ionicons name="mic" size={20} color={colors.navigateCyan} />
                <Text style={styles.cardTitle}>Acción</Text>
              </View>
              <Text style={styles.cardText}>¿Qué querés hacer?</Text>
              <Text style={styles.cardText}>"Quiero mejorar la orientación..."</Text>
              <View style={styles.mockInput}>
                <Text style={styles.mockInputText}>Escribir o dictar intención</Text>
                <Ionicons name="mic" size={20} color={colors.textSecondary} />
              </View>
            </View>
          </View>
        );
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.statusBar}>
        <View style={styles.lightItem}><View style={[styles.lightDot, { backgroundColor: getGnssColor() }]} /><Text style={styles.lightLabel}>GNSS</Text></View>
        <View style={styles.lightItem}><View style={[styles.lightDot, { backgroundColor: getSyncColor() }]} /><Text style={styles.lightLabel}>PC</Text></View>
        <View style={styles.lightItem}><View style={[styles.lightDot, { backgroundColor: getSyncColor() }]} /><Text style={styles.lightLabel}>Sinc</Text></View>
        <View style={styles.lightItem}><View style={[styles.lightDot, { backgroundColor: colors.success }]} /><Text style={styles.lightLabel}>Metro</Text></View>
      </View>

      <Text style={styles.title}>NAVEGO <Text style={styles.titleAccent}>// COCKPIT</Text></Text>

      <ScrollView style={styles.contentArea} contentContainerStyle={styles.contentInner}>
        {renderContent()}
      </ScrollView>

      <View style={styles.dock}>
        {modules.map((mod) => {
          const isActive = active === mod.key;
          return (
            <TouchableOpacity key={mod.key} style={styles.dockButton} onPress={() => setActive(mod.key)}>
              <Ionicons name={mod.icon} size={24} color={isActive ? colors.navigateCyan : colors.textSecondary} />
              <Text style={[styles.dockLabel, isActive && styles.dockLabelActive]}>{mod.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, paddingHorizontal: spacing.lg, paddingTop: spacing.lg, paddingBottom: Platform.OS === 'android' ? 16 : spacing.lg },
  statusBar: { flexDirection: 'row', justifyContent: 'flex-end', gap: 12, marginBottom: spacing.sm },
  lightItem: { alignItems: 'center' },
  lightDot: { width: 10, height: 10, borderRadius: 5, marginBottom: 2 },
  lightLabel: { fontSize: 8, color: colors.textSecondary, fontWeight: '600' },
  title: { fontSize: 20, fontWeight: 'bold', color: colors.textPrimary, letterSpacing: 1.5, textAlign: 'center', marginBottom: spacing.md },
  titleAccent: { color: colors.navigateCyan },
  contentArea: { flex: 1, marginBottom: spacing.md },
  contentInner: { justifyContent: 'flex-start' },
  section: { marginBottom: spacing.md },
  card: { backgroundColor: 'rgba(5, 25, 42, 0.58)', borderRadius: radii.md, borderWidth: 1, borderColor: colors.glassBorder, padding: spacing.md, marginBottom: spacing.md },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  cardTitle: { fontSize: 14, fontWeight: 'bold', color: colors.textPrimary, flexShrink: 1 },
  cardText: { fontSize: 12, color: colors.textSecondary, marginBottom: 4, lineHeight: 18 },
  primaryButton: { marginTop: 12, backgroundColor: 'rgba(0, 217, 255, 0.15)', borderRadius: radii.pill, paddingVertical: 10, paddingHorizontal: 16, alignItems: 'center' },
  primaryButtonText: { color: colors.navigateCyan, fontWeight: 'bold', fontSize: 12, letterSpacing: 1 },
  mockInput: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: radii.md, borderWidth: 1, borderColor: colors.glassBorder, paddingHorizontal: 12, paddingVertical: 10, marginTop: 10 },
  mockInputText: { color: colors.textSecondary, fontSize: 12, flex: 1 },
  dock: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'rgba(5, 25, 42, 0.58)', borderWidth: 1, borderColor: 'rgba(0, 217, 255, 0.30)', borderRadius: 22, paddingVertical: 10, paddingHorizontal: 8 },
  dockButton: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingVertical: 4 },
  dockLabel: { fontSize: 9, color: colors.textSecondary, fontWeight: '600', marginTop: 4 },
  dockLabelActive: { color: colors.navigateCyan },
});
