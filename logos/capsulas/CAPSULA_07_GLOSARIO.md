# 07 — Glosario

- NaveGo / navego_recuperado: el proyecto de tracker GPS.
- Cerebro / processFix: función pura que decide todo a partir de input+state.
- Efectos: publishUiResult (UI) y persistFixResult (SQLite).
- Callback: la lambda de useNaveGoTracker.ts que recibe `location` de GPS.
- Fix: una lectura GPS (lat, lon, accuracy, speed, heading, timestamp).
- Gap: interrupción en el flujo de fixes (pérdida de señal).
  - gap abierto: hay un openGapId activo.
  - gap restart: salto > MAX_JUMP_DISTANCE_M, resetea track sin sumar distancia.
  - gap close: fix válido después de un gap abierto.
- SOG / COG: Speed Over Ground / Course Over Ground.
- rawDistanceDelta: distancia cruda, solo diagnóstico (nuevo en este refactor).
- distanceDelta: distancia efectivamente sumada al total.
- Replay: reproducción de un track grabado para comparar comportamiento antes/después.
- DSH: observador/análisis externo. Se le alimenta diff + commit + archivos nuevos.
  Produce análisis de semántica y riesgos. NO se usa mid-refactor (mete ruido).
- LOGOS: sistema donde vive la evidencia del proceso (incluye análisis de DSH).
- Fase 0 (background): etapa siguiente al refactor, mover cómputo fuera del hilo UI.
- Etapas: Paso 3A (rawDistanceDelta), Paso 3B (reemplazo de callback).
