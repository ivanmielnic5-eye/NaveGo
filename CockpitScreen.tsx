import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts, glass, spacing, radii } from './theme';

export function CockpitScreen() {
  const [sog] = useState('5.2');
  const [cog] = useState('073°');
  const [distance] = useState('12.84');
  const [showLearning, setShowLearning] = useState(false);

  const systemLights = [
    { id: 'gnss', label: 'GNSS', color: colors.success },
    { id: 'server', label: 'Servidor', color: colors.success },
    { id: 'tunnel', label: 'Túnel', color: colors.warning },
    { id: 'metro', label: 'Metro', color: colors.success },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Barra de salud del sistema */}
      <View style={styles.statusBar}>
        {systemLights.map((light) => (
          <View key={light.id} style={styles.lightItem}>
            <View style={[styles.lightDot, { backgroundColor: light.color }]} />
            <Text style={styles.lightLabel}>{light.label}</Text>
          </View>
        ))}
      </View>

      {/* Título */}
      <Text style={styles.title}>
        NAVEGO <Text style={styles.titleAccent}>// COCKPIT</Text>
      </Text>

      {/* Métricas principales */}
      <View style={styles.metricsRow}>
        <View style={styles.metricBox}>
          <Text style={styles.metricLabel}>SOG</Text>
          <Text style={styles.metricValue}>{sog} kn</Text>
        </View>
        <View style={styles.metricBox}>
          <Text style={styles.metricLabel}>COG</Text>
          <Text style={styles.metricValue}>{cog}</Text>
        </View>
      </View>
      <Text style={styles.distanceText}>Distancia total: {distance} km</Text>

      {/* Plan de Pruebas — Acciones siempre visibles */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Ionicons name="information-circle" size={20} color={colors.navigateCyan} />
          <Text style={styles.cardTitle}>Plan de Pruebas — Course-Up</Text>
        </View>
        <Text style={styles.cardText}>1. Salir al exterior con GNSS fijo.</Text>
        <Text style={styles.cardText}>2. Rotar a landscape y mantener velocidad constante.</Text>
        <Text style={styles.cardText}>3. Realizar 3–4 giros amplios.</Text>
        <Text style={styles.cardText}>4. Observar si el mapa rota en tiempo real o con retraso.</Text>
        <Text style={styles.cardText}>5. Registrar COG, SOG, hora y sensación visual.</Text>
      </View>

      {/* Botón de Aprendizaje */}
      <TouchableOpacity style={styles.learningToggle} onPress={() => setShowLearning(!showLearning)}>
        <Ionicons name="school" size={20} color={colors.navigateCyan} />
        <Text style={styles.learningToggleText}>Aprendizaje</Text>
        <Ionicons name={showLearning ? 'chevron-up' : 'chevron-down'} size={16} color={colors.textSecondary} />
      </TouchableOpacity>

      {/* Tarjetas de Aprendizaje — solo visibles si showLearning es true */}
      {showLearning && (
        <>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="terminal" size={20} color={colors.success} />
              <Text style={styles.cardTitle}>Terminales — Arranque</Text>
            </View>
            <Text style={styles.cardText}>Servidor → Túnel → Metro</Text>
            <Text style={styles.cardText}>1. node simulate.js</Text>
            <Text style={styles.cardText}>2. npx localtunnel --port 3000</Text>
            <Text style={styles.cardText}>3. npx expo start --clear</Text>
          </View>

          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="terminal" size={20} color={colors.warning} />
              <Text style={styles.cardTitle}>Terminales — Cierre</Text>
            </View>
            <Text style={styles.cardText}>Metro → Túnel → Servidor</Text>
            <Text style={styles.cardText}>1. Cerrar Metro con Ctrl + C</Text>
            <Text style={styles.cardText}>2. Cerrar túnel con Ctrl + C</Text>
            <Text style={styles.cardText}>3. Cerrar servidor con Ctrl + C</Text>
          </View>

          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="git-branch" size={20} color={colors.navigateCyan} />
              <Text style={styles.cardTitle}>Dependencia entre terminales</Text>
            </View>
            <Text style={styles.cardText}>El túnel depende del servidor.</Text>
            <Text style={styles.cardText}>Metro puede correr solo, pero para sincronizar con PC necesitás servidor y túnel activos.</Text>
            <Text style={styles.cardText}>Por eso: arrancar de abajo hacia arriba, cerrar de arriba hacia abajo.</Text>
          </View>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    paddingBottom: spacing.lg,
  },
  content: {
    justifyContent: 'flex-start',
  },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    marginBottom: spacing.sm,
  },
  lightItem: {
    alignItems: 'center',
  },
  lightDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginBottom: 2,
  },
  lightLabel: {
    fontSize: 8,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.textPrimary,
    letterSpacing: 1.5,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  titleAccent: {
    color: colors.navigateCyan,
  },
  metricsRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.sm,
  },
  metricBox: {
    flex: 1,
    backgroundColor: colors.glassControl,
    borderRadius: radii.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.glassBorder,
  },
  metricLabel: {
    fontSize: 10,
    color: colors.textSecondary,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.textPrimary,
  },
  distanceText: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  card: {
    backgroundColor: 'rgba(5, 25, 42, 0.58)',
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.glassBorder,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.textPrimary,
    flexShrink: 1,
  },
  cardText: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 4,
    lineHeight: 18,
  },
  learningToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: 'rgba(0, 217, 255, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(0, 217, 255, 0.25)',
    borderRadius: radii.pill,
    paddingVertical: 10,
    paddingHorizontal: 16,
    marginBottom: spacing.md,
  },
  learningToggleText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.navigateCyan,
  },
});