# 04 — Archivos clave y símbolos

## tracker/types.ts
- ProcessInput, ProcessState, ProcessResult, GPSFix (importado de types/journal).

## tracker/processFix.ts
- processFix(input, state): ProcessResult
- Usa: calculateDistance, MAX_ACCURACY_M, MAX_JUMP_DISTANCE_M, MIN_DISTANCE_DELTA_M
- Ramas: not-recording/paused, accuracy-reject, min-delta-reject, gap-restart, normal.

## useNaveGoTracker.ts
- Hook principal. Contiene el callback que estamos refactorizando.
- Refs relevantes:
    lastPointRef, lastCogRef, lastFixTimestampRef, lastFixAccuracyRef,
    routePointsRef, totalDistanceRef, lastDistanceLogRef, lastFixIdRef,
    lastSogRef, fieldTestLogRef, sessionIdRef, dbRef,
    openGapIdRef, gapStartAtMsRef, gapStartPosRef, isRecordingRef, isPausedRef
- Setters de UI: setLivePosition, setCurrentSog, setCurrentCog,
    setLastFixTimestamp, setLastFixAccuracy, setActiveHazards,
    setRoutePoints, setTotalDistance, setGapCount, setGapTotalDurationMs,
    setGapActive, setGapMarkers
- Helpers importados: updateNavigationStatus, evaluateHazards, persistRawFix, closeGap

## Archivos que NO se tocan en este refactor
- App.tsx (tiene smoothedCog, error viejo conocido, no es nuestro)
- types/journal.ts (solo se importa GPSFix)

## Backups generados
- useNaveGoTracker.ts.pre-refactor
- tracker/types.ts.pre-rawdistance
- tracker/processFix.ts.pre-rawdistance
