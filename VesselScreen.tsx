import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useSQLiteContext } from 'expo-sqlite';
import { getVessel, saveVessel } from './db/vessel';
import { colors, fonts, glass, spacing, radii } from './theme';

type Props = { onBack: () => void };

export function VesselScreen({ onBack }: Props) {
  const db = useSQLiteContext();
  const [nombre, setNombre] = useState('');
  const [tipo, setTipo] = useState('');
  const [modelo, setModelo] = useState('');
  const [eslora, setEslora] = useState('');
  const [manga, setManga] = useState('');
  const [calado, setCalado] = useState('');
  const [motor, setMotor] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const v = await getVessel(db);
        if (v) {
          setNombre(v.nombre ?? '');
          setTipo(v.tipo ?? '');
          setModelo(v.modelo ?? '');
          setEslora(v.eslora != null ? String(v.eslora) : '');
          setManga(v.manga != null ? String(v.manga) : '');
          setCalado(v.calado != null ? String(v.calado) : '');
          setMotor(v.motor ?? '');
        }
      } catch (err) {
        console.warn('[VESSEL] Error al cargar:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, [db]);

  const parseNum = (s: string): number | null => {
    const limpio = s.trim().replace(',', '.');
    if (limpio === '') return null;
    const n = parseFloat(limpio);
    return isNaN(n) ? null : n;
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveVessel(db, {
        nombre: nombre.trim() || null,
        tipo: tipo.trim() || null,
        modelo: modelo.trim() || null,
        eslora: parseNum(eslora),
        manga: parseNum(manga),
        calado: parseNum(calado),
        motor: motor.trim() || null,
      });
      Alert.alert('Guardado', 'Ficha de embarcación actualizada.');
    } catch (err) {
      console.warn('[VESSEL] Error al guardar:', err);
      Alert.alert('Error', 'No se pudo guardar la ficha.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={colors.navigateCyan} />
        <Text style={styles.loadingText}>Cargando ficha…</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <TouchableOpacity onPress={onBack} style={styles.backButton}>
        <Text style={styles.backText}>← Volver</Text>
      </TouchableOpacity>

      <Text style={styles.title}>Mi embarcación</Text>
      <Text style={styles.subtitle}>Todos los campos son opcionales.</Text>

      <Text style={styles.label}>Nombre</Text>
      <TextInput
        style={styles.input}
        value={nombre}
        onChangeText={setNombre}
        placeholder="Ej: Polaris"
        placeholderTextColor={colors.textSecondary}
      />

      <Text style={styles.label}>Tipo</Text>
      <TextInput
        style={styles.input}
        value={tipo}
        onChangeText={setTipo}
        placeholder="Velero, lancha, motor…"
        placeholderTextColor={colors.textSecondary}
      />

      <Text style={styles.label}>Modelo o diseño</Text>
      <TextInput
        style={styles.input}
        value={modelo}
        onChangeText={setModelo}
        placeholder="Fabricante y modelo"
        placeholderTextColor={colors.textSecondary}
      />

      <Text style={styles.label}>Eslora (m)</Text>
      <TextInput
        style={styles.input}
        value={eslora}
        onChangeText={setEslora}
        keyboardType="decimal-pad"
        placeholder="10.0"
        placeholderTextColor={colors.textSecondary}
      />

      <Text style={styles.label}>Manga (m)</Text>
      <TextInput
        style={styles.input}
        value={manga}
        onChangeText={setManga}
        keyboardType="decimal-pad"
        placeholder="3.0"
        placeholderTextColor={colors.textSecondary}
      />

      <Text style={styles.label}>Calado (m)</Text>
      <TextInput
        style={styles.input}
        value={calado}
        onChangeText={setCalado}
        keyboardType="decimal-pad"
        placeholder="1.63"
        placeholderTextColor={colors.textSecondary}
      />

      <Text style={styles.label}>Motor o propulsión</Text>
      <TextInput
        style={styles.input}
        value={motor}
        onChangeText={setMotor}
        placeholder="Tipo de motor"
        placeholderTextColor={colors.textSecondary}
      />

      <TouchableOpacity
        style={[styles.saveButton, saving && { opacity: 0.6 }]}
        onPress={handleSave}
        disabled={saving}
      >
        <Text style={styles.saveText}>
          {saving ? 'GUARDANDO…' : 'GUARDAR'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing.xl,
  },
  backButton: {
    marginBottom: spacing.md,
  },
  backText: {
    color: colors.navigateCyan,
    fontSize: 14,
    fontWeight: '600',
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  loadingText: {
    color: colors.textPrimary,
    marginTop: spacing.md,
  },
  label: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: spacing.md,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    fontWeight: '600',
  },
  input: {
    backgroundColor: 'rgba(5, 25, 42, 0.6)',
    borderWidth: 1,
    borderColor: colors.borderSubtle,
    borderRadius: radii.md,
    padding: spacing.sm,
    color: colors.textPrimary,
    fontSize: 14,
  },
  saveButton: {
    marginTop: spacing.xl,
    backgroundColor: 'rgba(53, 211, 154, 0.20)',
    borderWidth: 1,
    borderColor: colors.success,
    borderRadius: radii.md,
    padding: spacing.md,
    alignItems: 'center',
  },
  saveText: {
    color: colors.success,
    fontWeight: 'bold',
    fontSize: 14,
    letterSpacing: 0.8,
  },
});
