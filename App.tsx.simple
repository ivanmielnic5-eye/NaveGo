import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Platform } from 'react-native';
import CockpitScreen from './CockpitScreen';
import { watchTelemetryStream } from './conexion';

export default function App() {
  const [activeScreen, setActiveScreen] = useState<'logo' | 'cockpit'>('logo');
  const [connectionStatus, setConnectionStatus] = useState<string>('Iniciando enlace...');

  useEffect(() => {
    const unsubscribe = watchTelemetryStream(() => {
      setConnectionStatus('🟢 Enlace Activo (Bridge 8084)');
    });
    return () => unsubscribe();
  }, []);

  if (activeScreen === 'logo') {
    return (
      <View style={styles.rootContainer}>
        <View style={styles.logoBox}>
          <Text style={styles.brandTitle}>NAVEGO // R2-D2</Text>
          <Text style={styles.brandSubtitle}>SISTEMA DE TELEMETRÍA NÁUTICA</Text>
          <View style={styles.statusBadge}>
            <Text style={styles.statusText}>{connectionStatus}</Text>
          </View>
          <TouchableOpacity 
            style={styles.startButton} 
            onPress={() => setActiveScreen('cockpit')}
          >
            <Text style={styles.startButtonText}>INICIALIZAR COCKPIT HUD</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.rootContainer}>
      <View style={styles.navBar}>
        <TouchableOpacity onPress={() => setActiveScreen('logo')} style={styles.backButton}>
          <Text style={styles.backButtonText}>← VOLVER AL LOGO</Text>
        </TouchableOpacity>
        <Text style={styles.navTitle}>HUD NÁUTICO ACTIVO</Text>
      </View>
      <CockpitScreen />
    </View>
  );
}

const styles = StyleSheet.create({
  rootContainer: {
    flex: 1,
    backgroundColor: '#030712',
    ...(Platform.OS === 'web' ? { height: '100vh', width: '100vw', overflow: 'hidden' } : {}),
  },
  logoBox: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    maxWidth: 480,
    alignSelf: 'center',
    width: '100%',
  },
  brandTitle: {
    color: '#f8fafc',
    fontSize: 28,
    fontWeight: '900',
    letterSpacing: 2,
    marginBottom: 8,
    fontFamily: 'monospace',
    textAlign: 'center',
  },
  brandSubtitle: {
    color: '#38bdf8',
    fontSize: 12,
    letterSpacing: 1.5,
    marginBottom: 24,
    fontFamily: 'monospace',
    textAlign: 'center',
  },
  statusBadge: {
    backgroundColor: '#111827',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 32,
    borderWidth: 1,
    borderColor: '#1f2937',
  },
  statusText: {
    color: '#4ade80',
    fontSize: 12,
    fontFamily: 'monospace',
  },
  startButton: {
    backgroundColor: '#0284c7',
    width: '100%',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  startButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  navBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111827',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1f2937',
  },
  backButton: {
    paddingRight: 16,
  },
  backButtonText: {
    color: '#38bdf8',
    fontSize: 12,
    fontFamily: 'monospace',
    fontWeight: 'bold',
  },
  navTitle: {
    color: '#9ca3af',
    fontSize: 12,
    fontFamily: 'monospace',
    letterSpacing: 1,
  },
});
