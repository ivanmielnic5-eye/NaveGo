# EXP — RUIDO VS GAP: el ruido se disfraza de gap?

Fecha: 2026-09-25 · `docs/gnss/exp_ruido_vs_gap/` · Scripts: `gen_gt_ruido.py`, `run_ruido_vs_gap.py`, `eval_regla.py`
Evidencia: `resultados_ruido_vs_gap.json`, `fixes_ruido_sigma*.jsonl`, `fixes_gapreal10s_S*.jsonl`, `gt_ruido_5min_5kn.jsonl`.
Simulador: `tools/gnss_simulator.py` **sin modificar**. Replica del tracker: idéntica a `run_gaps_avance.py` (ya validada contra la app).

## METODOLOGIA
- GT: 300 s a 5 nudos (2.5722 m/s), recta rumbo 90, 1 Hz, **sin `cut_windows`**. Camino real = 769.09 m.
- Ruido: `sigma_pos` ∈ {0.5, 1.5, 3.0, 5.0} m × 5 semillas (7100-7104) = 20 corridas, 6000 fixes, 0 gaps programados.
- Gap real de control: corte de 10 s en t=150 s, sigma=1.0 m, 3 semillas.
- Se copian las constantes del código: `MAX_JUMP_DISTANCE_M=15`, `MAX_ACCURACY_M=20`, `MIN_DISTANCE_DELTA_M=0.8`, watchdog 2000 ms.
- El watchdog NO aporta falsos gaps (con dt=1 s nunca alcanza 2 s): los falsos gaps medidos son **exclusivamente `isGapRestart`** (línea 401). `accuracy = sigma*1.5 ≤ 7.5` en todos los casos ⇒ el filtro de accuracy no interviene.

## H1: PARCIALMENTE CONFIRMADA — el mecanismo sí, la predicción no
El ruido **sí** genera saltos >15 m tratados como `isGapRestart`, pero solo desde σ=3.0 m:

| sigma | saltos >15 m (5×5min) | por corrida | error distancia medio |
|---|---|---|---|
| 0.5 | 0 | 0 | ≈0 % |
| 1.5 | **0** | 0 | ≈0 % |
| 3.0 | 9 | 1.8 | +80 % a +93 % |
| 5.0 | 193 | 38.6 | >+200 % |

Evidencia: `resultados_ruido_vs_gap.json["ruido"]`. **Refutación de la predicción de H1**: se exigía ≥3 falsos gaps en 5 min con σ=1.5 m; el resultado es **0** en las 5 semillas. Con σ=3.0 m el conteo (1.8/corrida) es ~1, no ≥3.
Verificación independiente (Monte Carlo, 2M muestras, ruido gaussiano diferencial N(0, 2σ²)): p(salto>15 m) = 0.0000 % (σ≤1.5), **0.4625 %** (σ=3.0 → 1.39 esperados/300 fixes), **12.12 %** (σ=5.0 → 36.4). Coincide con lo observado (1.8 y 38.6). El salto de 15.0 m del informe `exp_gaps_avance` a σ=3.0 es reproducible y estadísticamente esperable.

## H2: CONFIRMADA — la regla separa perfectamente
Regla `dt > 2 s O speed ≤ 0.3 m/s`:

| conjunto | saltos >15 m | clasificados gap | resultado |
|---|---|---|---|
| ruido (σ 0.5-5.0, 20 corridas) | 202 | **0** | 0.0 % falsos positivos |
| gap real 10 s (3 corridas) | 3 | **3** | 100 % recall |

Evidencia: `eval_regla.py`. En los 202 saltos de ruido `dt=1.0 s` exacto y `speed=2.57 m/s` (= velocidad real del barco, no coincide con el salto). En el gap real `dt=11.0 s`. Predicción de H2 (>90 % recall, <10 % FP) **superada**.

## H3: REFUTADA como criterio
La predicción era que en ruido el fix N+1 volviera a <5 m de N-1 y en gap real a >20 m.

| conjunto | n | mediana \|N+1 − N-1\| | <5 m | >20 m |
|---|---|---|---|---|
| ruido σ=3.0 | 9 | 8.2 m | **0/9 (0 %)** | 0 |
| ruido σ=5.0 | 193 | 12.4 m | 13/193 (7 %) | 17 |
| gap real 10 s | 3 | 33.2 m | 0 | **3/3 (100 %)** |

Evidencia: `eval_regla.py`. El gap real se separa bien (>20 m en 3/3), pero el ruido **NO vuelve cerca** del punto pre-salto: el fix N+1 es otro punto ruidoso independiente, cuya distancia esperada a N-1 es 2·σ·√2 (~8.5 m a σ=3). La "vuelta" no es una firma fiable por sí sola; hay solapamiento entre 5 y 20 m. REFUTADA como regla única.

## REGLA PROPUESTA
**`esGapReal = (dt > 2 s) O (speed ≤ 0.3 m/s)`.** Es la única que separa limpio: 0 FP / 100 % recall en este dataset. Justificación física: un salto >15 m en dt≤2 s exige >7.5 m/s (14.6 nudos), imposible para el barco; el `speed` del fix delata el movimiento real. Es la regla de menor costo (ya hay `dt` y `speed` disponibles: `lastPointRef.timestamp` y `coords.speed`) y no requiere estado nuevo. H3 puede usarse como confirmación secundaria (solo descarta cuando \|N+1−N-1\|>20 m), nunca como criterio primario.

## IMPACTO EN EL SISTEMA
- **Falsos gaps por hora real**: a σ=1.5 m ⇒ ~0/h. A σ=3.0 m ⇒ ~21.6/h (1.8 por 5 min). A σ=5.0 m ⇒ ~463/h.
- **Si no se arregla**: cada falso gap corta la distancia (pierde el tramo) y **no** abre `gap_events`, así que el HUD del track honesto mostraría "perdiste señal" sin haber perdido nada — el peor caso señalado en la tarea. El error de distancia pasa de −25 % a +93 % (reproducido).
- **Si se arregla**: los falsos gaps se reclasifican como salto de ruido (no cortan distancia, no dibujan gap). Con σ=3.0/5.0 el error de distancia vuelve al orden de σ=1.0. Cero falsos "perdiste señal" en los 202 casos medidos.
- **Incertidumbre clave**: no se conoce el σ real del TCL T610P. Si es ≤1.5 m, el bug es hoy inofensivo; si es ≥3 m, es crítico. **No inventar el dato: hay que caracterizar el receptor antes de priorizar.**

## PLAN PROPUESTO
Cambio amarillo/rojo (toca distancia ⇒ **requiere hipótesis previa y medición en dispositivo**; no ejecutar sin autorización):
1. En `useNaveGoTracker.ts:401`, reemplazar la condición por `distanceIncrement > MAX_JUMP_DISTANCE_M && (dtSecs > GAP_DT_UMBRAL_S || liveSog <= GAP_SPEED_ZERO_MS)`; declarar `GAP_DT_UMBRAL_S=2.0`, `GAP_SPEED_ZERO_MS=0.3`.
2. Si el salto supera 15 m pero `dt`/`speed` dicen ruido: **no** cortar la distancia como gap; tratarlo como outlier (saltar el punto, sin sumar, sin marcar gap) y loguear `[NOISE]`.
3. Corregir de paso el log mentiroso de línea 373 (`durMs`), ya detectado en `exp_gaps_avance`.
4. Re-correr este experimento con el σ medido del TCL y recién entonces commit.
Riesgo: si un gap real ocurre con `dt` pequeño (reloj/SQLite congelado), la regla lo clasificaría como ruido. Mitigación: el watchdog sigue abriendo gap por antigüedad >2 s, que es independiente de esta regla (defensa en profundidad).

## INCERTIDUMBRES
- **σ real del TCL T610P: NO MEDIDO.** Todo el impacto depende de este valor; es el dato que falta.
- El simulador usa ruido gaussiano i.i.d.; el ruido GNSS real tiene correlación temporal y sesgo (multipath), que puede cambiar el conteo.
- No se modeló `speed` ruidoso (`speed_sigma_ms` existe en el simulador pero no se barrió): con speed ruidoso alto, la rama `speed ≤ 0.3` de la regla podría dar falsos positivos.
- H3 no se pudo llevar a cabo con un gap real a 5 nudos y σ alto a la vez: el único gap real se midió a σ=1.0.
- No verificado en pantalla; todo es lectura de código + réplica, no captura en dispositivo.
