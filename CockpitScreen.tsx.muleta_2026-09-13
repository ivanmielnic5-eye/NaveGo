import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView } from 'react-native';
import { watchTelemetryStream, TelemetryData } from './conexion';

export default function CockpitScreen() {
  const [data, setData] = useState<TelemetryData | null>(null);

  useEffect(() => {
    const unsubscribe = watchTelemetryStream((telemetry) => {
      setData(telemetry);
    });
    return () => unsubscribe();
  }, []);

  return (
    <ScrollView contentContainerStyle={styles.scrollContainer}>
      {/* Header / Estado del Sistema */}
      <View style={styles.headerCard}>
        <View style={styles.headerTop}>
          <Text style={styles.systemTitle}>NAVEGO // R2-D2 HUD</Text>
          <View style={[styles.badge, { backgroundColor: data ? '#064e3b' : '#7f1d1d' }]}>
            <Text style={[styles.badgeText, { color: data ? '#4ade80' : '#f87171' }]}>
              {data ? '🟢 ENLACE ACTIVO' : '🔴 ESPERANDO DATOS'}
            </Text>
          </View>
        </View>
        <Text style={styles.subText}>SISTEMA DE TELEMETRÍA GPRMC (1Hz)</Text>
      </View>

      {/* Grid Principal de Instrumentos */}
      <View style={styles.grid}>
        {/* Tarjeta SOG (Velocidad) */}
        <View style={styles.card}>
          <Text style={styles.cardLabel}>SOG (VELOCIDAD)</Text>
          <Text style={styles.cardValue}>{data ? data.sog : '--'}</Text>
          <Text style={styles.cardUnit}>NUDOS</Text>
        </View>

        {/* Tarjeta COG (Rumbo) */}
        <View style={styles.card}>
          <Text style={styles.cardLabel}>COG (RUMBO)</Text>
          <Text style={styles.cardValue}>{data ? data.cog : '--'}</Text>
          <Text style={styles.cardUnit}>GRADOS (°)</Text>
        </View>
      </View>

      {/* Tarjeta de Posición Geodésica */}
      <View style={styles.wideCard}>
        <Text style={styles.cardLabel}>POSICIÓN GPS (LAT / LON)</Text>
        <View style={styles.coordRow}>
          <Text style={styles.coordText}>LAT: {data ? data.lat : '---.----'}</Text>
          <Text style={styles.coordText}>LON: {data ? data.lon : '---.----'}</Text>
        </View>
      </View>

      {/* Tarjeta de Estado y Tiempo UTC */}
      <View style={styles.wideCard}>
        <View style={styles.rowBetween}>
          <View>
            <Text style={styles.cardLabel}>ESTADO DEL FIX</Text>
            <Text style={styles.statusVal}>{data ? data.status : 'Desconocido'}</Text>
          </View>
          <View style={{ alignItems: 'flex-end' }}>
            <Text style={styles.cardLabel}>TIEMPO UTC</Text>
            <Text style={styles.utcVal}>{data ? data.utc : '--:--:--'}</Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollContainer: {
    padding: 16,
    backgroundColor: '#0b0f19',
    flexGrow: 1,
  },
  headerCard: {
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1f2937',
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  systemTitle: {
    color: '#f3f4f6',
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'monospace',
    letterSpacing: 1,
  },
  subText: {
    color: '#9ca3af',
    fontSize: 10,
    fontFamily: 'monospace',
    letterSpacing: 1.5,
  },
  badge: {
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  grid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  card: {
    flex: 1,
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: '#1f2937',
    alignItems: 'center',
  },
  wideCard: {
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1f2937',
  },
  cardLabel: {
    color: '#9ca3af',
    fontSize: 11,
    fontFamily: 'monospace',
    marginBottom: 8,
    letterSpacing: 1,
  },
  cardValue: {
    color: '#38bdf8',
    fontSize: 32,
    fontWeight: '900',
    fontFamily: 'monospace',
  },
  cardUnit: {
    color: '#64748b',
    fontSize: 10,
    fontFamily: 'monospace',
    marginTop: 4,
    letterSpacing: 1,
  },
  coordRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  coordText: {
    color: '#e2e8f0',
    fontSize: 14,
    fontFamily: 'monospace',
    fontWeight: 'bold',
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusVal: {
    color: '#4ade80',
    fontSize: 13,
    fontFamily: 'monospace',
    fontWeight: 'bold',
    marginTop: 2,
  },
  utcVal: {
    color: '#f8fafc',
    fontSize: 13,
    fontFamily: 'monospace',
    fontWeight: 'bold',
    marginTop: 2,
  },
});
