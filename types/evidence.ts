// types/evidence.ts

export type GPSState =
  | 'INITIALIZING'
  | 'OK'
  | 'DEGRADED'
  | 'LOST'
  | 'RECOVERING';

export type GPSCondition =
  | 'NOMINAL'
  | 'LOW_ACCURACY'
  | 'JUMPING'
  | 'DRIFTING'
  | 'STATIONARY_ZUPT';

export interface StateVector {
  timestamp: number;
  epoch: 'GPS_TIME' | 'SYSTEM_TIME' | 'UTC';
  datum: 'WGS84' | 'POSGAR94' | 'NAD83';
  position: { lat: number; lon: number; alt?: number };
  velocity: number;
  heading: number;
  covariance: { dimension: 3 | 6; matrix: number[][] };
  quality: number;
  gpsState: GPSState;
  gpsCondition: GPSCondition;
  source: 'GPS' | 'FILTERED' | 'INFERRED' | 'MANUAL';
  evidence_ref: { source: 'gps_fix' | 'event' | 'report'; id: string };
  integrity_hash?: string;
}