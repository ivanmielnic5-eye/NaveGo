import React, { useEffect, useRef, useState, memo } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Alert, ActivityIndicator, InteractionManager, useWindowDimensions, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
// import MapView, { Polyline } from 'react-native-maps';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import * as NavigationBar from 'expo-navigation-bar';
import { Accelerometer } from 'expo-sensors';
import { SQLiteProvider, useSQLiteContext } from 'expo-sqlite';
import { useNaveGoTracker } from './useNaveGoTracker';
import { colors, fonts, glass, spacing, radii } from './theme';
import { initDatabase } from './db/schema';
import { HistoryScreen } from './HistoryScreen';
import { SessionDetailScreen } from './SessionDetailScreen';
import { ReferenceDetailScreen } from './ReferenceDetailScreen';
import { getReferenceRoutePoints } from './db/journal';
import { CockpitScreen } from './CockpitScreen';

const darkMapStyle = [
  { elementType: 'geometry', stylers: [{ color: '#1d2c4d' }] },
{ elementType: 'labels.text.fill', stylers: [{ color: '#8ec3cb' }] },
{ elementType: 'labels.text.stroke', stylers: [{ color: '#1a3646' }] },
{ featureType: 'administrative.country', elementType: 'geometry.stroke', stylers: [{ color: '#4b6878' }] },
{ featureType: 'administrative.land_parcel', elementType: 'labels.text.fill', stylers: [{ color: '#64748b' }] },
{ featureType: 'administrative.neighborhood', stylers: [{ visibility: 'off' }] },
{ featureType: 'poi', elementType: 'geometry', stylers: [{ color: '#283d6a' }] },
{ featureType: 'poi', elementType: 'labels.text.fill', stylers: [{ color: '#6f9abc' }] },
{ featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#1d2c4d' }] },
{ featureType: 'poi.park', elementType: 'labels.text.fill', stylers: [{ color: '#3b768f' }] },
{ featureType: 'road', elementType: 'geometry', stylers: [{ color: '#304a6d' }] },
{ featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: '#1a2c4a' }] },
{ featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: '#98a5be' }] },
{ featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#2c4070' }] },
{ featureType: 'road.highway', elementType: 'geometry.stroke', stylers: [{ color: '#1d2c4d' }] },
{ featureType: 'road.highway', elementType: 'labels.text.fill', stylers: [{ color: '#8ea0c0' }] },
{ featureType: 'transit', elementType: 'geometry', stylers: [{ color: '#2a3d5f' }] },
{ featureType: 'transit.station', elementType: 'labels.text.fill', stylers: [{ color: '#6f9abc' }] },
{ featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0a1128' }] },
{ featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#3e5c7a' }] },
];

const TelemetryTile = memo(({ label, value, accent }: { label: string; value: string; accent?: boolean }) => (
  <View style={[glass.telemetryTile, { flex: 1, padding: 0 }]}>
  <View style={{ padding: spacing.sm }}>
  <Text style={styles.label}>{label}</Text>
  <Text style={[styles.value, { color: accent ? colors.navigateCyan : colors.textPrimary }]}>
  {value}
  </Text>
  </View>
  </View>
));

const OrientationIndicator = memo(({
  isCourseUp,
  cog,
}: {
  isCourseUp: boolean;
  cog: number | null;
}) => {
  const cogText =
  cog !== null && Number.isFinite(cog)
  ? `${Math.round((cog + 360) % 360).toString().padStart(3, '0')}°`
  : '---°';

return (
  <View style={styles.orientationIndicator}>
  <View style={styles.orientationArrowContainer}>
  <Ionicons
  name="arrow-up"
  size={16}
  color={isCourseUp ? colors.navigateCyan : colors.textSecondary}
  />
  </View>

  <View style={styles.orientationInfo}>
  <Text
  style={[
    styles.orientationValue,
    {
      color: isCourseUp
      ? colors.navigateCyan
      : colors.textPrimary,
    },
  ]}
  >
  {isCourseUp ? cogText : 'N'}
  </Text>

  <Text style={styles.orientationMode}>
  {isCourseUp ? 'COURSE-UP · COG' : 'NORTH-UP'}
  </Text>
  </View>
  </View>
);
});

function AppContent() {
  const db = useSQLiteContext();
  const { width, height } = useWindowDimensions();
  const isLandscape = width > height;

  const [permissionState, setPermissionState] = useState<'loading' | 'granted' | 'denied'>('loading');
  const tracker = useNaveGoTracker();
  const mapRef = useRef<any>(null);
  const [mapReady, setMapReady] = useState(false);

  const [screen, setScreen] = useState<'hud' | 'history' | 'detail' | 'reference' | 'cockpit'>('hud');
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [referencePoints, setReferencePoints] = useState<{ latitude: number; longitude: number }[]>([]);

  const [accelerometerZ, setAccelerometerZ] = useState<number>(1);

  useEffect(() => {
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        setPermissionState(status === 'granted' ? 'granted' : 'denied');
      } catch (error) {
        console.warn('[APP] Error al solicitar permisos:', error);
        setPermissionState('denied');
      }
    })();
  }, []);

  useEffect(() => {
    const sub = Accelerometer.addListener(({ z }) => {
      if (Number.isFinite(z)) {
        // setAccelerometerZ(Math.abs(z)); // desactivado temporalmente para diagnóstico
      }
    });

    Accelerometer.setUpdateInterval(100);

    return () => sub.remove();
  }, []);

  useEffect(() => {
    const hideNavigationBar = async () => {
      try {
        await NavigationBar.setVisibilityAsync('hidden');
      } catch (error) {
        console.warn('[APP] Error al ocultar NavigationBar:', error);
      }
    };
    hideNavigationBar();
  }, [isLandscape]);

  useEffect(() => {
    if (screen === 'hud' && selectedRouteId) {
      (async () => {
        try {
          const pts = await getReferenceRoutePoints(db, selectedRouteId);
          setReferencePoints(
            pts
            .map((p: any) => ({
              latitude: p.lat ?? p.latitude,
              longitude: p.lon ?? p.longitude,
            }))
            .filter((p: any) => p.latitude !== undefined && p.longitude !== undefined)
          );
        } catch (err) {
          console.warn('[APP] Error al cargar puntos de referencia:', err);
        }
      })();
    }
  }, [screen, selectedRouteId]);

  const routePoints = (tracker.routePoints || [])
  .map((point: any) => ({
    latitude: point.lat ?? point.latitude,
    longitude: point.lon ?? point.longitude,
  }))
  .filter((p: any) => p.latitude !== undefined && p.longitude !== undefined);

  const lastPoint = routePoints.length > 0 ? routePoints[routePoints.length - 1] : null;
  const initialPosition = lastPoint || { latitude: -31.6333, longitude: -60.7000 };

  const distanceKm = (Number(tracker.totalDistance) / 1000).toFixed(3);
  const sogKnots = Number(tracker.currentSog || 0).toFixed(1);
  const cogDeg = Math.round(Number(tracker.currentCog || 0));

  const gpsStateText = tracker.isTracking ? 'GPS OK' : 'AMARRE';
  const gpsColor = tracker.isTracking ? colors.success : colors.navigateCyan;

  const navStatus = tracker.navigationStatus;
  const navConfig = {
    CONFIABLE: { icon: 'compass' as const, color: colors.success, label: 'GNSS OK' },
    DEGRADADO: { icon: 'cloud' as const, color: colors.warning, label: 'GNSS DEGRADADO' },
    NO_CONFIABLE: { icon: 'alert-circle' as const, color: colors.danger, label: 'NAVEGACIÓN NO CONFIABLE' },
    NO_DISPONIBLE: { icon: 'location' as const, color: colors.textSecondary, label: 'GNSS NO DISPONIBLE' },
    GNSS_PERDIDO: { icon: 'location' as const, color: colors.warning, label: 'GNSS PERDIDO' },
    RECUPERANDO: { icon: 'sync' as const, color: colors.navigateCyan, label: 'RECUPERANDO' },
  }[navStatus] || { icon: 'help-circle' as const, color: colors.textSecondary, label: navStatus };

  const ageSeconds = tracker.lastFixTimestamp
  ? Math.floor((Date.now() - tracker.lastFixTimestamp) / 1000)
  : null;
  const ageText =
  ageSeconds === null
  ? 'sin señal'
  : ageSeconds < 60
  ? `hace ${ageSeconds} s`
  : `hace ${Math.floor(ageSeconds / 60)} min`;
  const accuracyM = tracker.lastFixAccuracy !== null ? tracker.lastFixAccuracy.toFixed(0) : null;

  const internetColor = tracker.syncOk === true ? colors.success : tracker.syncOk === false ? colors.warning : colors.textSecondary;
  const internetIcon = tracker.syncOk === true ? 'cloud-done' : tracker.syncOk === false ? 'cloud-offline' : 'cloud';
  const internetLabel = tracker.syncOk === true ? 'INTERNET' : tracker.syncOk === false ? 'SIN INTERNET' : 'INTERNET...';

  const phoneIsHorizontal = accelerometerZ > 0.7;
  const courseUpActive = isLandscape && phoneIsHorizontal && tracker.smoothedCog !== null && Number(tracker.currentSog || 0) > 0.5;

  const handleToggleRecord = () => tracker.togglePause();
  const handleReset = () => tracker.resetTracking();
  const handleStart = () => {
    tracker.startTracking().catch((err) => {
      console.warn('[APP] Error al iniciar tracking:', err);
    });
  };

  const handleCenterMap = () => {
    if (mapRef.current && lastPoint) {
      mapRef.current.animateToRegion(
        {
          latitude: lastPoint.latitude,
          longitude: lastPoint.longitude,
          latitudeDelta: 0.005,
          longitudeDelta: 0.005,
        },
        500
      );
    }
  };

  const handleFinalize = () => {
    tracker.stopTracking();
    Alert.alert(
      'Sistema',
      `Derrota finalizada y guardada exitosamente.\nDistancia: ${Number(tracker.totalDistance).toFixed(1)} m`
    );
    console.log('[GAIA] Derrota finalizada y guardada.');
  };

  const floatingActions = [
    { key: 'config', icon: 'settings' as const, label: 'Config' },
    { key: 'energy', icon: 'flash' as const, label: 'Energía' },
    { key: 'vessel', icon: 'navigate' as const, label: 'Embarcación' },
    { key: 'port', icon: 'home' as const, label: 'Puerto' },
    { key: 'history', icon: 'time' as const, label: 'Historial' },
  ];

  if (permissionState === 'loading') {
    return (
      <SafeAreaView style={styles.loadingContainer}>
      <StatusBar style="light" />
      <ActivityIndicator size="large" color={colors.navigateCyan} />
      <Text style={styles.loadingText}>Solicitando permisos...</Text>
      </SafeAreaView>
    );
  }

  if (permissionState === 'denied') {
    return (
      <SafeAreaView style={styles.loadingContainer}>
      <StatusBar style="light" />
      <Ionicons name="location" size={48} color={colors.warning} />
      <Text style={[styles.loadingText, { color: colors.warning }]}>
      Permiso de ubicación denegado
      </Text>
      <Text style={styles.permissionHint}>
      Habilitá el acceso a la ubicación para usar NaveGo.
      </Text>
      </SafeAreaView>
    );
  }

  if (screen === 'history') {
    return (
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <StatusBar style="light" />
      <HistoryScreen
      db={db}
      onBack={() => setScreen('hud')}
      onSelect={(id, type) => {
        if (type === 'session') {
          setSelectedSessionId(id);
          setScreen('detail');
        } else if (type === 'reference') {
          setSelectedRouteId(id);
          setScreen('reference');
        }
      }}
      />
      </SafeAreaView>
    );
  }

  if (screen === 'detail' && selectedSessionId) {
    return (
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <StatusBar style="light" />
      <SessionDetailScreen
      sessionId={selectedSessionId}
      onBack={() => setScreen('history')}
      />
      </SafeAreaView>
    );
  }

  if (screen === 'reference' && selectedRouteId) {
    return (
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <StatusBar style="light" />
      <ReferenceDetailScreen
      routeId={selectedRouteId}
      onBack={() => setScreen('history')}
      onUse={() => {
        setSelectedRouteId(selectedRouteId);
        setScreen('hud');
      }}
      />
      </SafeAreaView>
    );
  }

  if (screen === 'cockpit') {
    return (
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <StatusBar style="light" />
      <View style={styles.cockpitHeader}>
      <TouchableOpacity onPress={() => setScreen('hud')} style={styles.cockpitBackButton}>
      <Ionicons name="arrow-back" size={24} color={colors.navigateCyan} />
      </TouchableOpacity>
      </View>
      <CockpitScreen tracker={tracker} />
      </SafeAreaView>
    );
  }

  if (isLandscape) {
    return (
      <View style={styles.landscapeContainer}>
      <StatusBar style="light" />

      <View style={[StyleSheet.absoluteFill, { alignItems: 'center', justifyContent: 'center', backgroundColor: '#0a1128' }]}>
      <Ionicons name="map-outline" size={48} color={colors.navigateCyan} />
      <Text style={{ color: colors.navigateCyan, fontSize: 16, fontWeight: 'bold', marginTop: 12 }}>
      MAPA PENDIENTE
      </Text>
      <Text style={{ color: colors.textSecondary, fontSize: 12, marginTop: 8 }}>
      API key de Google Maps no configurada
      </Text>
      </View>

      {lastPoint && (
        <TouchableOpacity style={[glass.mapControl, styles.landscapeCenterButton]} onPress={handleCenterMap}>
        <Text style={styles.centerButtonText}>CENTRAR</Text>
        </TouchableOpacity>
      )}

      <View style={styles.landscapeOrientationBadge}>
      <OrientationIndicator
      isCourseUp={courseUpActive}
      cog={tracker.smoothedCog ?? null}
      />
      </View>

      <View style={[glass.statusChip, styles.landscapeGpsBadge]}>
      <Text style={[styles.headerStatus, { color: gpsColor }]}>{gpsStateText}</Text>
      </View>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
    <StatusBar style="light" />

    <View style={styles.header}>
    <Text style={styles.headerTitle}>NAVEGO <Text style={styles.headerAccent}>// HUD</Text></Text>
    <TouchableOpacity onPress={() => setScreen('cockpit')} style={styles.cockpitButton}>
    <Ionicons name="grid" size={22} color={colors.navigateCyan} />
    </TouchableOpacity>
    </View>

    <View style={[styles.navChip, { borderColor: navConfig.color }]}>
    <Ionicons name={navConfig.icon} size={18} color={navConfig.color} />
    <Text style={[styles.navChipText, { color: navConfig.color }]}>{navConfig.label}</Text>
    <Text style={styles.navChipAge}>{ageText}</Text>
    {accuracyM !== null && <Text style={styles.navChipAge}>· ± {accuracyM} m</Text>}
    </View>

    <View style={[styles.internetChip, { borderColor: internetColor }]}>
    <Ionicons name={internetIcon} size={18} color={internetColor} />
    <Text style={[styles.internetChipText, { color: internetColor }]}>{internetLabel}</Text>
    </View>

    <View style={styles.mapWrapper}>
    <View style={[styles.map, { alignItems: 'center', justifyContent: 'center', backgroundColor: '#0a1128' }]}>
    <Ionicons name="map-outline" size={32} color={colors.navigateCyan} />
    <Text style={{ color: colors.navigateCyan, fontSize: 12, fontWeight: 'bold', marginTop: 8 }}>
    MAPA PENDIENTE
    </Text>
    </View>
    {lastPoint && <TouchableOpacity style={[glass.mapControl, styles.centerButton]} onPress={handleCenterMap}><Text style={styles.centerButtonText}>CENTRAR</Text></TouchableOpacity>}
    </View>

    <View style={glass.substrate}>
    <View style={styles.row}>
    <TelemetryTile
    label="SOG (NUDOS)"
    value={sogKnots}
    />

    <View style={[glass.telemetryTile, { flex: 1, padding: 0 }]}>
    <View style={styles.cogTileContent}>
    <View style={styles.cogHeader}>
    <Text style={styles.label}>COG</Text>

    <Ionicons
    name="arrow-up"
    size={14}
    color={colors.navigateCyan}
    style={{
      transform: [{ rotate: `${cogDeg}deg` }],
    }}
    />
    </View>

    <Text
    style={[
      styles.value,
      { color: colors.navigateCyan },
    ]}
    >
    {`${cogDeg}°`}
    </Text>

    <View style={styles.cogNorthRow}>
    <Ionicons name="arrow-up" size={10} color={colors.textSecondary} />
    <Text style={styles.cogNorthText}>N</Text>
    </View>

    <Text style={styles.cogSubLabel}>
    RUMBO SOBRE FONDO
    </Text>
    </View>
    </View>
    </View>

    <View style={[glass.dataPanel, styles.distanceCardCompact]}>
    <View style={styles.distanceCompactContent}>
    <View style={styles.distanceHeader}>
    <Text style={styles.label}>DISTANCIA</Text>
    <Text style={styles.distanceValue}>{distanceKm} <Text style={styles.distanceUnit}>KM</Text></Text>
    </View>
    <Text style={styles.distanceSub}>({Number(tracker.totalDistance).toFixed(1)} m)</Text>

    <View style={styles.statusRowCompact}>
    <View style={[styles.dot, tracker.isPaused ? styles.dotPaused : styles.dotActive]} />
    <Text style={[styles.recordingText, { color: tracker.isPaused ? colors.warning : colors.navigateCyan }]}>{tracker.isPaused ? 'II PAUSADO' : '● GRABANDO'}</Text>
    </View>

    {tracker.activeHazards && tracker.activeHazards.length > 0 && (
      <View style={styles.alertBannerCompact}>
      <Text style={styles.alertTextCompact}>{tracker.activeHazards[0].confidence === 'CONFIRMADO' ? '⚠️' : '◌'} {tracker.activeHazards[0].name} a {Math.round(tracker.activeHazards[0].distance)} m</Text>
      <Text style={styles.alertSubTextCompact}>{tracker.activeHazards[0].confidence === 'CONFIRMADO' ? 'CONFIRMADO' : 'ÚLTIMA INFORMACIÓN'} · hace {tracker.activeHazards[0].lastReportedAt ? Math.floor((Date.now() - tracker.activeHazards[0].lastReportedAt) / 60000) : 0} min</Text>
      </View>
    )}

    {tracker.syncOk === false && <Text style={styles.syncWarning}>Sin conexión con PC</Text>}
    {tracker.syncOk === true && <Text style={styles.syncOk}>Sincronizado con PC</Text>}
    </View>
    </View>

    <View style={styles.dockBar}>
    {floatingActions.map((item) => (
      <TouchableOpacity key={item.key} style={styles.dockItemTouchable} onPress={() => { if (item.key === 'history') setScreen('history'); }}>
      <Ionicons name={item.icon} size={22} color={item.key === 'history' ? colors.navigateCyan : colors.textSecondary} />
      <Text style={styles.dockLabel}>{item.label}</Text>
      </TouchableOpacity>
    ))}
    </View>

    {!tracker.isTracking ? (
      <TouchableOpacity style={[glass.actionControl, { flex: 1, backgroundColor: 'rgba(53,211,154,0.14)' }]} onPress={handleStart}>
      <Text style={[styles.actionButtonText, { color: colors.success }]}>INICIAR DERROTA</Text>
      </TouchableOpacity>
    ) : (
      <View style={styles.row}>
      <TouchableOpacity style={[glass.actionControl, { flex: 1, backgroundColor: tracker.isPaused ? 'rgba(53,211,154,0.14)' : 'rgba(255,181,46,0.12)' }]} onPress={handleToggleRecord}>
      <Text style={[styles.actionButtonText, { color: tracker.isPaused ? colors.success : colors.warning }]}>{tracker.isPaused ? 'REANUDAR' : 'PAUSAR'}</Text>
      </TouchableOpacity>
      <TouchableOpacity style={[glass.actionControl, { flex: 1 }]} onPress={handleReset}>
      <Text style={[styles.actionButtonText, { color: colors.textSecondary }]}>RESETEAR</Text>
      </TouchableOpacity>
      </View>
    )}

    <View style={styles.finalContainer}>
    <TouchableOpacity style={[glass.actionControl, { paddingHorizontal: 24, backgroundColor: 'rgba(5,25,42,0.55)', borderColor: colors.borderSubtle }]} onPress={handleFinalize}>
    <Text style={[styles.actionButtonText, { color: colors.textPrimary }]}>FINALIZAR</Text>
    </TouchableOpacity>
    </View>
    </View>
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <SQLiteProvider databaseName="navego.db" onInit={initDatabase}>
    <SafeAreaProvider>
    <AppContent />
    </SafeAreaProvider>
    </SQLiteProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    paddingHorizontal: 16,
    paddingTop: 2,
    paddingBottom: Platform.OS === 'android' ? 27 : 15,
    justifyContent: 'space-between',
  },
  loadingContainer: { flex: 1, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center', padding: 20 },
  loadingText: { fontSize: 16, fontWeight: 'bold', color: colors.textPrimary, marginTop: 12, textAlign: 'center' },
  permissionHint: { fontSize: 13, color: colors.textSecondary, marginTop: 8, textAlign: 'center' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 2,
    marginBottom: 6,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.textPrimary,
    letterSpacing: 1.2,
    textAlign: 'center',
    flex: 1,
  },
  headerAccent: { color: colors.navigateCyan },
  headerStatus: { fontSize: 11, fontWeight: 'bold', letterSpacing: 0.8 },
  navChip: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, backgroundColor: colors.glassControl, borderWidth: 1, borderRadius: radii.pill, paddingHorizontal: 12, paddingVertical: 6, marginBottom: 6 },
  navChipText: { fontSize: 12, fontWeight: 'bold', letterSpacing: 0.5 },
  navChipAge: { fontSize: 10, color: colors.textSecondary },
  internetChip: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, backgroundColor: colors.glassControl, borderWidth: 1, borderRadius: radii.pill, paddingHorizontal: 12, paddingVertical: 6, marginBottom: 6 },
  internetChipText: { fontSize: 12, fontWeight: 'bold', letterSpacing: 0.5 },
  mapWrapper: { height: 190, borderRadius: radii.md, overflow: 'hidden', marginBottom: 8, borderWidth: 1, borderColor: colors.glassBorderStrong },
  map: { ...StyleSheet.absoluteFillObject },
  mapLoading: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(3, 7, 23, 0.7)' },
                                 centerButton: { position: 'absolute', top: 50, right: 8 },
                                 centerButtonText: { color: colors.navigateCyan, fontWeight: 'bold', fontSize: 10 },
                                 actionButtonText: { fontSize: 13, fontWeight: 'bold', letterSpacing: 0.8 },
                                 row: { flexDirection: 'row', gap: 10, marginBottom: 8 },
                                 half: { flex: 1, padding: 0 },
                                 distanceCardCompact: { padding: 0, marginBottom: 8 },
                                 distanceCompactContent: { padding: spacing.sm },
                                 distanceHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
                                 label: { ...fonts.label },
                                 value: { fontSize: 22, fontWeight: 'bold', letterSpacing: -0.5 },
                                 unit: { fontSize: 14, color: colors.textSecondary },
                                 distanceValue: { fontSize: 24, fontWeight: 'bold', letterSpacing: -0.8, color: colors.navigateCyan },
                                 distanceUnit: { fontSize: 14, color: colors.textSecondary },
                                 distanceSub: { fontSize: 11, color: colors.textSecondary, marginTop: 2 },
                                 statusRowCompact: { flexDirection: 'row', alignItems: 'center', marginTop: 6, gap: 6 },
                                 dot: { width: 8, height: 8, borderRadius: 4 },
                                 dotActive: { backgroundColor: colors.navigateCyan },
                                 dotPaused: { backgroundColor: colors.warning },
                                 recordingText: { fontSize: 10, fontWeight: 'bold', letterSpacing: 0.8 },
                                 alertBannerCompact: { marginTop: 8, padding: 8, borderRadius: 6, borderWidth: 0.5, borderColor: colors.danger, backgroundColor: 'rgba(255, 64, 85, 0.10)' },
                                 alertTextCompact: { color: colors.danger, fontSize: 12, fontWeight: 'bold', textAlign: 'center' },
                                 alertSubTextCompact: { color: colors.danger, fontSize: 10, textAlign: 'center', marginTop: 2, opacity: 0.8 },
                                 syncWarning: { marginTop: 6, color: colors.warning, fontSize: 10, textAlign: 'center' },
                                 syncOk: { marginTop: 6, color: colors.success, fontSize: 10, textAlign: 'center' },
                                 dockBar: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'rgba(5, 25, 42, 0.58)', borderWidth: 1, borderColor: 'rgba(0, 217, 255, 0.30)', borderRadius: 22, paddingVertical: 14, paddingHorizontal: 10, height: 68, marginBottom: 8 },
                                 dockItemTouchable: { flex: 1, alignItems: 'center', justifyContent: 'center' },
                                 dockLabel: { fontSize: 9, color: colors.textSecondary, fontWeight: '600', letterSpacing: 0.5, marginTop: 4 },
                                 finalContainer: {
                                   alignItems: 'center',
                                   marginBottom: Platform.OS === 'android' ? 18 : 10,
                                 },
                                 landscapeContainer: { flex: 1, backgroundColor: colors.background },
                                 landscapeCenterButton: { position: 'absolute', top: 60, right: 12 },
                                 landscapeGpsBadge: { position: 'absolute', bottom: 60, right: 12 },
                                 orientationIndicator: {
                                   flexDirection: 'row',
                                   alignItems: 'center',
                                   alignSelf: 'flex-start',
                                   paddingHorizontal: 8,
                                   paddingVertical: 4,
                                   borderRadius: radii.pill,
                                   backgroundColor: 'rgba(5, 25, 42, 0.58)',
                                 borderWidth: 1,
                                 borderColor: colors.glassBorder,
                                 },
                                 orientationArrowContainer: {
                                   width: 20,
                                   height: 20,
                                   alignItems: 'center',
                                   justifyContent: 'center',
                                   marginRight: 4,
                                 },
                                 orientationInfo: {
                                   justifyContent: 'center',
                                 },
                                 orientationValue: {
                                   fontSize: 11,
                                   fontWeight: 'bold',
                                   letterSpacing: 0.5,
                                   lineHeight: 13,
                                 },
                                 orientationMode: {
                                   fontSize: 7,
                                   color: colors.textSecondary,
                                   fontWeight: '700',
                                   letterSpacing: 0.3,
                                   marginTop: 1,
                                 },
                                 cogTileContent: {
                                   padding: spacing.sm,
                                 },
                                 cogHeader: {
                                   flexDirection: 'row',
                                   alignItems: 'center',
                                   justifyContent: 'space-between',
                                 },
                                 cogNorthRow: {
                                   flexDirection: 'row',
                                   alignItems: 'center',
                                   gap: 2,
                                   marginTop: 2,
                                 },
                                 cogNorthText: {
                                   fontSize: 9,
                                   color: colors.textSecondary,
                                   fontWeight: '700',
                                 },
                                 cogSubLabel: {
                                   fontSize: 6,
                                   color: colors.textSecondary,
                                   fontWeight: '600',
                                   letterSpacing: 0.3,
                                   marginTop: 2,
                                 },
                                 landscapeOrientationBadge: {
                                   position: 'absolute',
                                   top: 60,
                                   left: 12,
                                   zIndex: 10,
                                 },
                                 cockpitButton: {
                                   padding: 8,
                                 },
                                 cockpitHeader: {
                                   flexDirection: 'row',
                                   alignItems: 'center',
                                   marginBottom: 8,
                                 },
                                 cockpitBackButton: {
                                   padding: 8,
                                 },
});
