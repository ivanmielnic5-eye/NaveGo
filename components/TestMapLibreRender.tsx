import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Map, Camera } from '@maplibre/maplibre-react-native';

export default function TestMapLibreRender() {
  return (
    <View style={styles.container}>
      <Map
        style={styles.map}
        mapStyle="https://demotiles.maplibre.org/style.json"
      >
        <Camera
          initialViewState={{
            center: [-65.0, -35.0],
            zoom: 4,
          }}
        />
      </Map>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
});
