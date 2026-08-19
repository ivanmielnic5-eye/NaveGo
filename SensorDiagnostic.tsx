import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

// La palabra "export default" es obligatoria para que App lo pueda leer
export default function SensorDiagnostic() {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>¡SensorDiagnostic está conectado!</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0b0f19',
  },
  text: {
    color: '#00e5ff',
    fontSize: 18,
    fontWeight: 'bold',
  }
});

