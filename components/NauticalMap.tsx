// NauticalMap.tsx
import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Dimensions } from 'react-native';
import MapView, { Marker, Polyline } from 'react-native-maps';
import { useSQLiteContext } from 'expo-sqlite';
import { getAllSessions } from '../db/journal';
import { loadSimulationFromSession, SimulationPoint } from '../simulate';

export default function NauticalMap() {
  const db = useSQLiteContext();
  const [sessions, setSessions] = useState<{ id: string; start_time: number; boat_name: string | null }[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [routePoints, setRoutePoints] = useState<SimulationPoint[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  // Cargar sesiones al iniciar
  useEffect(() => {
    async function fetchSessions() {
      const data = await getAllSessions(db);
      setSessions(data);
      if (data.length > 0) {
        setSelectedSessionId(data[0].id);
      }
    }
    fetchSessions();
  }, [db]);

  // Cargar puntos de la sesión seleccionada
  const handleSelectSession = async (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setIsSimulating(false);
    setCurrentIndex(0);
    const points = await loadSimulationFromSession(db, sessionId);
    setRoutePoints(points);
  };

  // Iniciar la reproducción simulada
  const startSimulation = async () => {
    if (!selectedSessionId || routePoints.length === 0) return;
    setIsSimulating(true);
    setCurrentIndex(0);

    for (let i = 0; i < routePoints.length; i++) {
      setCurrentIndex(i);
      await new Promise(resolve => setTimeout(resolve, 1000)); // 1 punto por segundo
    }
    setIsSimulating(false);
  };

  const currentPoint = routePoints[currentIndex] || routePoints[0] || { lat: -31.6333, lon: -60.7, timestamp: Date.now() };

  return (
    <View style={styles.container}>
      <MapView
        style={styles.map}
        region={{
          latitude: currentPoint.lat,
          longitude: currentPoint.lon,
          latitudeDelta: 0.01,
          longitudeDelta: 0.01,
        }}
      >
        {/* Línea completa de la trayectoria */}
        <Polyline
          coordinates={routePoints.map(p => ({ latitude: p.lat, longitude: p.lon }))}
          strokeColor="#00E5FF"
          strokeWidth={4}
        />

        {/* Marcador de la posición actual en la simulación */}
        <Marker
          coordinate={{ latitude: currentPoint.lat, longitude: currentPoint.lon }}
          title="Embarcación"
          description={`Punto ${currentIndex + 1} de ${routePoints.length}`}
        />
      </MapView>

      <View style={styles.panel}>
        <Text style={styles.title}>Simulador de Navegación</Text>
        <Text style={styles.subtitle}>Sesiones grabadas: {sessions.length}</Text>

        <TouchableOpacity 
          style={[styles.button, isSimulating && styles.buttonDisabled]} 
          onPress={startSimulation}
          disabled={isSimulating || routePoints.length === 0}
        >
          <Text style={styles.buttonText}>{isSimulating ? `Reproduciendo (${currentIndex + 1}/${routePoints.length})` : 'Reproducir Recorrido'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    width: Dimensions.get('window').width,
    height: Dimensions.get('window').height * 0.7,
  },
  panel: {
    flex: 0.3,
    backgroundColor: '#121212',
    padding: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  subtitle: {
    color: '#AAA',
    fontSize: 14,
    marginBottom: 12,
  },
  button: {
    backgroundColor: '#00E5FF',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  buttonDisabled: {
    backgroundColor: '#555',
  },
  buttonText: {
    color: '#000',
    fontWeight: 'bold',
    fontSize: 16,
  },
});