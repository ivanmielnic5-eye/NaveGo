// theme.ts
export const colors = {
  background: '#030817',
  backgroundSecondary: '#061322',
  navigateCyan: '#00D9FF',
  cyanDark: '#008FA8',
  textPrimary: '#F2F7FA',
  textSecondary: '#91A6B5',
  success: '#35D39A',
  warning: '#FFB52E',
  danger: '#FF4055',

  // Niveles de vidrio
  glassSubstrate: 'rgba(8, 27, 45, 0.72)',
  glassControl: 'rgba(5, 25, 42, 0.38)',
  glassSurface: 'rgba(5, 25, 42, 0.58)',
  glassElevated: 'rgba(5, 25, 42, 0.76)',

  // Tintes semánticos
  glassCyan: 'rgba(0, 217, 255, 0.12)',
  glassSuccess: 'rgba(53, 211, 154, 0.14)',
  glassWarning: 'rgba(255, 181, 46, 0.12)',
  glassDanger: 'rgba(255, 64, 85, 0.16)',

  // Bordes
  borderSubtle: 'rgba(255, 255, 255, 0.18)',
  glassBorder: 'rgba(0, 217, 255, 0.35)',
  glassBorderStrong: 'rgba(0, 217, 255, 0.60)',

  // Halo de instrumentación (muy tenue)
  halo: 'rgba(0, 217, 255, 0.08)',
};

export const fonts = {
  label: {
    fontSize: 10,
    fontWeight: '600' as const,
    letterSpacing: 2.0,
    textTransform: 'uppercase' as const,
    color: colors.textSecondary,
  },
  value: {
    fontSize: 34,
    fontWeight: 'bold' as const,
    letterSpacing: -1.0,
    color: colors.textPrimary,
  },
  valueCyan: {
    fontSize: 48,
    fontWeight: 'bold' as const,
    letterSpacing: -1.5,
    color: colors.navigateCyan,
  },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 28,
};

export const radii = {
  sm: 16,
  md: 22,
  lg: 28,
  pill: 999,
};

export const glass = {
  substrate: {
    backgroundColor: colors.glassSubstrate,
    borderRadius: radii.lg,
    borderWidth: 0.5,
    borderColor: colors.borderSubtle,
    padding: spacing.md,
    // Halo de instrumentación: sombra interior sutil en la zona superior
    shadowColor: colors.halo,
    shadowOpacity: 0.8,
    shadowOffset: { width: 0, height: 6 },
    shadowRadius: 12,
    elevation: 2,
  },
  mapControl: {
    backgroundColor: colors.glassCyan,
    borderWidth: 1,
    borderColor: colors.glassBorder,
    borderRadius: radii.pill,
    paddingVertical: 8,
    paddingHorizontal: 14,
  },
  telemetryTile: {
    backgroundColor: colors.glassSurface,
    borderWidth: 1,
    borderColor: colors.glassBorder,
    borderRadius: radii.md,
    padding: spacing.md,
  },
  dataPanel: {
    backgroundColor: colors.glassElevated,
    borderWidth: 1,
    borderColor: colors.glassBorderStrong,
    borderRadius: radii.md,
    padding: spacing.lg,
  },
  actionControl: {
    backgroundColor: colors.glassElevated,
    borderWidth: 1,
    borderColor: colors.borderSubtle,
    borderRadius: radii.sm,
    paddingVertical: 12,
    paddingHorizontal: 18,
  },
  navTile: {
    backgroundColor: colors.glassControl,
    borderWidth: 0.5,
    borderColor: colors.borderSubtle,
    borderRadius: radii.sm,
    paddingVertical: 10,
    paddingHorizontal: 6,
  },
  statusChip: {
    backgroundColor: colors.glassControl,
    borderWidth: 1,
    borderColor: colors.borderSubtle,
    borderRadius: radii.pill,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
};