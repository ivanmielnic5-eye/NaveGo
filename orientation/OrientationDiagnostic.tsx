import React, { useEffect, useState } from 'react';
import {
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {
  createNaveGoOrientationCore,
  OrientationState,
} from './NaveGoOrientationCore';

const orientationCore =
  createNaveGoOrientationCore({
    updateIntervalMs: 50,
    magnetometerCorrection: 0.05,
  });

function formatDegrees(value: number | null): string {
  if (value === null) {
    return '---';
  }

  return `${Math.round(value)}°`;
}

function formatNumber(value: number | null): string {
  if (value === null) {
    return '---';
  }

  return value.toFixed(1);
}

function confidenceLabel(
  confidence: OrientationState['confidence']
): string {
  switch (confidence) {
    case 'HIGH':
      return 'ALTA';

    case 'MEDIUM':
      return 'MEDIA';

    case 'LOW':
      return 'BAJA';

    default:
      return 'NO DISPONIBLE';
  }
}

export default function OrientationDiagnostic() {
  const [state, setState] =
    useState<OrientationState>(
      orientationCore.getState()
    );

  useEffect(() => {
    const unsubscribe =
      orientationCore.subscribe(setState);

    orientationCore.start().catch((error) => {
      console.warn(
        '[OrientationDiagnostic] Error:',
        error
      );
    });

    return () => {
      unsubscribe();
      orientationCore.stop();
    };
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>
        NAVEGO // ORIENTATION ENGINE
      </Text>

      <Text style={styles.subtitle}>
        DIAGNÓSTICO DE ORIENTACIÓN
      </Text>

      <View style={styles.compass}>
        <Text style={styles.north}>N</Text>

        <View style={styles.compassRing}>
          <Text style={styles.degree}>
            {formatDegrees(
              state.smoothedHeading
            )}
          </Text>
        </View>
      </View>

      <View style={styles.panel}>
        <Row
          label="HDG MAGNÉTICO"
          value={formatDegrees(
            state.magneticHeading
          )}
        />

        <Row
          label="HDG SUAVIZADO"
          value={formatDegrees(
            state.smoothedHeading
          )}
        />

        <Row
          label="CAMPO MAGNÉTICO"
          value={`${formatNumber(
            state.magneticFieldStrength
          )} μT`}
        />

        <Row
          label="CALIBRADO"
          value={
            state.calibrated
              ? 'SÍ'
              : 'NO'
          }
        />

        <Row
          label="CONFIANZA"
          value={confidenceLabel(
            state.confidence
          )}
        />

        <Row
          label="SENSOR"
          value={
            state.sensorAvailable
              ? 'DISPONIBLE'
              : 'NO DISPONIBLE'
          }
        />
      </View>

      <View style={styles.instruction}>
        <Text style={styles.instructionTitle}>
          PRUEBA FÍSICA
        </Text>

        <Text style={styles.instructionText}>
          Mantené el teléfono aproximadamente
          horizontal y giralo lentamente sobre
          su eje.
        </Text>

        <Text style={styles.instructionText}>
          Observá si el rumbo aumenta y disminuye
          de manera continua, especialmente al
          atravesar 0° / 360°.
        </Text>
      </View>
    </SafeAreaView>
  );
}

function Row({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <View style={styles.row}>
      <Text style={styles.label}>
        {label}
      </Text>

      <Text style={styles.value}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#030817',
    padding: 20,
  },

  title: {
    color: '#00d9ff',
    fontSize: 18,
    fontWeight: 'bold',
    letterSpacing: 1.2,
  },

  subtitle: {
    color: '#8ea0b8',
    fontSize: 11,
    marginTop: 4,
    letterSpacing: 1,
  },

  compass: {
    height: 260,
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 20,
  },

  compassRing: {
    width: 190,
    height: 190,
    borderRadius: 95,
    borderWidth: 2,
    borderColor: 'rgba(0,217,255,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  north: {
    position: 'absolute',
    top: 20,
    zIndex: 2,
    color: '#ff4055',
    fontSize: 22,
    fontWeight: 'bold',
  },

  degree: {
    color: '#00d9ff',
    fontSize: 38,
    fontWeight: 'bold',
  },

  panel: {
    borderWidth: 1,
    borderColor: 'rgba(0,217,255,0.25)',
    borderRadius: 14,
    padding: 14,
    backgroundColor: 'rgba(5,25,42,0.55)',
  },

  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 7,
  },

  label: {
    color: '#71849b',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.7,
  },

  value: {
    color: '#e8f1f7',
    fontSize: 14,
    fontWeight: 'bold',
  },

  instruction: {
    marginTop: 16,
    padding: 14,
    borderRadius: 12,
    backgroundColor: 'rgba(255,181,46,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255,181,46,0.25)',
  },

  instructionTitle: {
    color: '#ffb52e',
    fontSize: 11,
    fontWeight: 'bold',
    letterSpacing: 0.8,
    marginBottom: 6,
  },

  instructionText: {
    color: '#9aabba',
    fontSize: 12,
    lineHeight: 18,
    marginTop: 3,
  },
});

