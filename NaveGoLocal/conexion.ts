/**
 * Módulo de Parámetros de Conexión y Estado de Señal (GPS / Red)
 * Proyecto: NaveGo / GAIA Tracker
 */

export interface ConnectionParameters {
  timeoutMs: number;
  maxAccuracyMeters: number;
  intervalMs: number;
  distanceIntervalMeters: number;
  retryAttempts: number;
}

export const DEFAULT_CONNECTION_PARAMS: ConnectionParameters = {
  timeoutMs: 15000,          // Tiempo límite de espera de señal GPS
  maxAccuracyMeters: 20,     // Precisión máxima aceptable en metros
  intervalMs: 1000,          // Intervalo de muestreo en milisegundos (1s)
  distanceIntervalMeters: 1, // Distancia mínima de desplazamiento para actualización (1m)
  retryAttempts: 3,          // Intentos de reconexión ante pérdida de señal
};

export type ConnectionState = 'CONECTADO' | 'BUSCANDO_SEÑAL' | 'SIN_CONEXION' | 'PAUSADO';

export interface SignalStatusInfo {
  state: ConnectionState;
  label: string;
  color: string;
}

export function getSignalStatusInfo(state: ConnectionState): SignalStatusInfo {
  switch (state) {
    case 'CONECTADO':
      return { state, label: '● GPS CONECTADO (FIJADO)', color: '#059669' };
    case 'BUSCANDO_SEÑAL':
      return { state, label: '◐ BUSCANDO SATÉLITES...', color: '#d97706' };
    case 'SIN_CONEXION':
      return { state, label: '✕ SIN SEÑAL DE GPS', color: '#be123c' };
    case 'PAUSADO':
      return { state, label: 'II RASTREO PAUSADO', color: '#64748b' };
    default:
      return { state, label: '○ ESTADO DESCONOCIDO', color: '#94a3b8' };
  }
}