// evidence/evidenceGate.ts (versión autónoma, sin gpsStateMachine)
import type { SQLiteDatabase } from 'expo-sqlite';
import type { GPSFix } from '../types/journal';
import type { GPSState, GPSCondition, StateVector } from '../types/evidence';
import { insertGpsFix } from '../db/journal';
import { calculateDistance } from '../kinematics/kinematics';

export interface EvidenceProcessingState {
  lastObservedFix: GPSFix | null;
  lastAcceptedFix: GPSFix | null;
  nextSequenceNo: number;
}

export const INITIAL_EVIDENCE_STATE: EvidenceProcessingState = {
  lastObservedFix: null,
  lastAcceptedFix: null,
  nextSequenceNo: 0,
};

export interface ProcessedFixResult {
  evidenceState: EvidenceProcessingState;
  stateVector: StateVector | null;
  gpsState: GPSState;
  gpsCondition: GPSCondition;
  fixWasRejected: boolean;
  distanceDelta: number;
}

export async function processGpsFix(
  db: SQLiteDatabase,
  rawFix: Omit<GPSFix, 'sequence_no'>,
  sessionId: string,
  currentState: EvidenceProcessingState
): Promise<ProcessedFixResult> {
  const sequenceNo = currentState.nextSequenceNo;
  const fix: GPSFix = {
    ...rawFix,
    id: rawFix.id || `${Date.now()}-${Math.random()}`,
    session_id: sessionId,
    sequence_no: sequenceNo,
  };

  await insertGpsFix(db, fix);

  const lastObservedFix = fix;

  // Regla de rechazo simple
  const isRejected =
    fix.quality === 'REJECTED' ||
    (fix.accuracy !== null && fix.accuracy !== undefined && fix.accuracy > 30);

  let distanceDelta = 0;
  let stateVector: StateVector | null = null;

  if (!isRejected && currentState.lastAcceptedFix) {
    distanceDelta = calculateDistance(
      currentState.lastAcceptedFix.lat_raw,
      currentState.lastAcceptedFix.lon_raw,
      fix.lat_raw,
      fix.lon_raw
    );
  }

  if (!isRejected) {
    stateVector = {
      timestamp: fix.timestamp,
      epoch: 'SYSTEM_TIME',
      datum: 'WGS84',
      position: { lat: fix.lat_raw, lon: fix.lon_raw, alt: fix.alt ?? undefined },
      velocity: fix.speed ?? 0,
      heading: fix.heading ?? 0,
      covariance: { dimension: 3, matrix: [[1,0,0],[0,1,0],[0,0,1]] },
      quality: 0.8,
      gpsState: 'OK' as GPSState,
      gpsCondition: 'NOMINAL' as GPSCondition,
      source: 'GPS',
      evidence_ref: { source: 'gps_fix', id: fix.id },
    };
  }

  const newEvidenceState: EvidenceProcessingState = {
    lastObservedFix,
    lastAcceptedFix: isRejected ? currentState.lastAcceptedFix : fix,
    nextSequenceNo: sequenceNo + 1,
  };

  return {
    evidenceState: newEvidenceState,
    stateVector,
    gpsState: isRejected ? 'DEGRADED' : 'OK',
    gpsCondition: isRejected ? 'LOW_ACCURACY' : 'NOMINAL',
    fixWasRejected: isRejected,
    distanceDelta,
  };
}

