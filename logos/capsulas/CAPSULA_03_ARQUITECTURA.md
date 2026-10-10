# 03 — Arquitectura y decisiones

## Principio rector
"El cerebro es puro. Los efectos son dos funciones que cada una hace una sola cosa."

## Contrato de processFix
Entrada:  ProcessInput  { lat, lon, accuracy, speed, heading, measuredAt }
          ProcessState  { lastPoint, lastCog, isRecording, isPaused, hasOpenGap }
Salida:   ProcessResult {
            persist: boolean
            quality: <clasificación>
            rejectForNavigation: null | 'ACCURACY' | 'MIN_DELTA'
            isGapRestart: boolean
            gapAction: 'NONE' | 'OPEN' | 'CLOSE'
            distanceDelta: number       // lo que se suma al total
            rawDistanceDelta: number    // crudo, solo diagnóstico
            nextState: ProcessState
            livePosition, liveSog, liveCog
            newPoint | null
          }

## Invariantes que NO se pueden romper
- distanceDelta = 0 cuando isGapRestart = true (semántica vieja).
- rawDistanceDelta SIEMPRE refleja la distancia cruda (para logs).
- persist se decide dentro de processFix, no en el callback.
- El callback solo arma input, captura state, llama processFix, despacha efectos.

## Umbrales actuales
- MAX_ACCURACY_M = 20
- MAX_JUMP_DISTANCE_M = 15
- MIN_DISTANCE_DELTA_M = (ver constante, usado para descartar micro-movimientos)

## Los 3 efectos (en useNaveGoTracker.ts)
1. publishUiResult(result, location)
   - Actualiza refs de telemetría (lastFixTimestamp, lastFixAccuracy, lastCog).
   - Actualiza HUD (setLivePosition, setCurrentSog, setCurrentCog, hazards, status).
   - Si result.newPoint: actualiza routePoints, totalDistance, lastPointRef.
   - Log de distancia cada 10s.
2. persistFixResult(result, location)
   - Solo si result.persist y hay sessionId + db.
   - Genera fixId, empuja a fieldTestLog, persistRawFix.
   - Maneja cierre de gap si gapAction === 'CLOSE' (closeGap, setGapCount, markers).
   - Logs de filtrado (ACCURACY, gap restart).
3. (El callback) — orquesta: input → state → processFix → publish + persist.
