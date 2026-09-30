export const REPLAY_ENABLED =
  process.env.EXPO_PUBLIC_GNSS_REPLAY === '1';

// Fase 2 del Doc 46: activa la Task de background en modo
// observador (escribe a JSONL, no toca SQLite).
// Solo para pruebas de duplicados (Fase 2.5). Desactivar en uso normal.
export const BACKGROUND_TEST_ENABLED =
  process.env.EXPO_PUBLIC_GNSS_BACKGROUND_TEST === '1';

// Fase 4 del Doc 46: en modo produccion, la Task es el UNICO
// productor. El hook deja de capturar y consume processed_points.
export const TASK_PRODUCER_ENABLED =
  process.env.EXPO_PUBLIC_GNSS_TASK_PRODUCER === '1';
