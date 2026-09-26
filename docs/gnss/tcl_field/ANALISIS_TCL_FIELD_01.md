# ANALISIS DEL PRIMER DATASET REAL DEL TCL T610P

Archivo: `docs/gnss/tcl_field/tcl_field_1790382982173.jsonl`
Script: `docs/gnss/tcl_field/analisis_tcl_field.py` (solo lectura, no toca codigo de app)

Codigo actual verificado en `useNaveGoTracker.ts`:
- L18 `MAX_JUMP_DISTANCE_M = 15`
- L20 `MIN_DISTANCE_DELTA_M = 0.8`
- L21 `MIN_SPEED_FOR_COG_UPDATE = 0.3`
- L407 `isGapRestart = true` si `haversine > 15 m`. **No consulta dt ni speed.**

## ESTADISTICAS BASICAS
- Fixes: **321 lineas con contenido** (la tarea declara 320; hay 1 de diferencia — no invento la causa).
- Rango temporal: `measuredAt` 1790382647552 → 1790382981684.
- Duracion total: **334.1 s** (5.57 min).
- Schema completo, sin nulls, `measuredAt`/`receivedAt` monotonos. Latencia `receivedAt-measuredAt` ~50-160 ms.

## ANALISIS DE dt
- dt mediano **1.000 s**; min 0.999 s; max **6.114 s**.
- dt > 2 s: **3**. dt > 5 s: **3**.
- Histograma: `<=1.2s: 315` | `1.2-2s: 2` | `2-5s: 0` | `5-10s: 3` | `>10s: 0`.
- Los 3 dt>5s son los fixes i=1,2,3 (arranque del log, dt 5.03/6.11/5.04 s). El resto es 1 Hz estricto.

## ANALISIS DE speed
- Mediana **0.000**; max **0.992 m/s**.
- `speed == 0`: **311**. `speed > 0`: **10**. `> 0.3`: **6**. `> 1`: **0**.
- Los 10 fixes con speed>0 estan agrupados en 4 rafagas cortas (i=33-35, 43-45, 72, 248-249, 274), todas con speed < 1 m/s.

## ANALISIS DE accuracy
- Mediana **1.766 m**; min 1.600 m; max **12.570 m**.
- Simulador = 4.5 m fijo → el TCL es **0.39x** el simulador (mejor, no peor).
- `acc < 5 m`: 258. `acc > 8 m`: 19. Los peores accuracy (>10 m) son solo el arranque i=0-4.

## SALTOS ESPACIALES
- Distancia acumulada cruda: **242.76 m** (215.93 m excluyendo el unico salto grande).
- Saltos > 15 m: **1**. Detalle del unico salto:
  - `i=23` dt=**1.000 s** dist=**26.84 m** speed=**0.000** acc=7.08
- Saltos por umbral: >5 m: 6 | >8 m: 3 | >10 m: 1 | >12 m: 1 | >15 m: 1 | >20 m: 1.
- Contexto i=19-28: la traza salta 26.84 m y luego vuelve, con `speed=0` sostenido y accuracy 7.08. Morfologia de **outlier de posicion**, no de desplazamiento real.
- Regla propuesta `(dt > 2 s O speed <= 0.3)` → gap_real: **1**, outlier: **0**.

## FALSOS GAPS
| Metrica | Codigo actual | Regla propuesta |
|---|---|---|
| gap real | 1 | 1 |
| outlier | 0 | 0 |
| falsos positivos evitados | — | **0** |

El dataset **no discrimina** entre ambas reglas: el unico salto > 15 m tiene `dt=1 s` y `speed=0`, y cae del mismo lado en las dos. El codigo actual NO produce falsos gaps masivos en esta sesion.

## H1: REFUTADA
Evidencia: dt mediano = 1.000 s en los 4 tramos. Bajo techo (tramos 1, 3, 4) el dt mediano es 1.00 s, no >2 s. Los unicos dt>2 s (3 casos, 5.03/6.11/5.04 s) son el arranque del log, no pasillo/interior. El TCL sostiene 1 Hz incluso sin cielo.

## H2: INCONCLUSA (tendencia a REFUTADA por la prediccion literal)
Evidencia: hay fixes con speed>0 en ventanas de movimiento (max 0.992 m/s, 10 fixes), pero **ninguno supera 1 m/s** y la mediana global es 0.000. La prediccion `speed > 1 m/s` da **0 fixes** → refutacion literal. Sin embargo hay señal >0 en tramos de patineta. No puedo afirmar cual tramo es cual: el dataset no trae etiqueta de tramo y los cambios de speed no coinciden limpiamente con la estructura declarada de 4 tramos.

## H3: REFUTADA
Evidencia: la prediccion pide **≥3** saltos >15 m con dt<2 s. Hay **1** (i=23). El umbral de refutacion era "0 o 1" → se cumple la refutacion.

## H4: REFUTADA
Evidencia: mediana de accuracy = **1.766 m**, muy por debajo de 5 m. La prediccion era >8 m. El TCL es mas preciso que el simulador (4.5 m), no menos.

## CONCLUSIONES
1. **El TCL es mas limpio que el simulador, no mas sucio.** 1 Hz casi perfecto, accuracy mediana 1.77 m (0.39x del simulador), traza quieta con dispersion de solo 1.7-1.9 m.
2. **El riesgo temido de falsos gaps no se materializo.** 1 solo salto >15 m en 321 fixes (0.3%). El `MAX_JUMP_DISTANCE_M=15` actual es suficiente para este dataset.
3. **La regla propuesta no puede validarse ni refutarse con este dataset.** No hay ni un caso de solapamiento entre "salto grande" y "dt corto + speed alto". El unico salto es ambiguo por morfologia pero ambas reglas lo clasifican igual. Se necesita un dataset con un gap real genuino (pej. tunel/estacionamiento) para discriminar.
4. **Observacion lateral sobre `MIN_DISTANCE_DELTA_M=0.8`:** la fase quieta larga (i=46-247, 201 s) muestra dispersion de 1.7-1.9 m con speed=0. Eso sugiere que el filtro de 0.8 m no descarta todo el jitter en reposo, pero esto NO fue parte de las 4 hipotesis y no lo cuantifique mas alla de la dispersion.

## INCERTIDUMBRES
- **320 vs 321**: la tarea declara 320 fixes, el archivo tiene 321 lineas con contenido. No se cual es correcto; use las 321 reales.
- **Segmentacion por tramos**: el dataset NO incluye marca de tramo. Mi segmentacion por rafagas de `speed>0.3` no reconstruye los 4 tramos declarados (pasillo/patio/pasillo/interior). No pude asignar dt ni accuracy a cada tramo declarado; los valores "por tramo" de H1 son por lo tanto **no verificables** y solo reporto el dt global.
- **Naturaleza del salto i=23**: no puedo probar si fue outlier de posicion o movimiento real no reportado por speed (speed=0 lo sugiere outlier, pero no es concluyente).
- **H2**: la prediccion literal (>1 m/s) se refuta, pero no tengo ground truth de movimiento para saber si hubo desplazamiento real en patineta.
- No conozco la version/commit del codigo del tracker al momento de la captura; asumi el estado actual del repo (`useNaveGoTracker.ts`).
