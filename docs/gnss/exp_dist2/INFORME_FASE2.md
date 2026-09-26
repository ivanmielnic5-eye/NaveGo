# Fase 2 — ¿Qué método representa mejor la distancia real?

Fecha: 2026-09-25 · Carpeta: `docs/gnss/exp_dist2/` · Scripts: `gen_trayectorias.py`, `run_fase2.py`
Evidencia cruda: `salida_fase2.txt`, `resultados_fase2.json` (60 corridas), `tray_*.jsonl` (GT).

## METODOLOGIA
3 trayectorias x 4 ruidos x 5 semillas = **60 corridas**. Sin cortes GNSS ni spikes
(se aísla el efecto de trayectoria y ruido, que es lo que piden H1/H2/H3).
- T1_recta (693.22 m, sin viradas) · T2_virada (693.22 m, virada suave 140-170 s igual a la actual)
- T3_acel_decel (569.49 m, rampas 0→6→2→5 kn, sin viradas)
- sigma = 0.0 / 0.5 / 1.5 / 3.0 m · semillas 3000-3004
- A = réplica de `useNaveGoTracker.ts` (haversine + gap>15 m + descarte<0.8 m).
  B = `speed x dt` rectangular. B\* = trapezoidal. C = combinado (ver `run_fase2.py`).
- **Ground truth = polilínea de las posiciones reales**, no la velocidad integrada.
  Es geométrico e independiente de `speed`: no favorece a B.

## RESULTADOS (error relativo %, media de 5 semillas)

| trayectoria | sigma | ref_m | A% | B% | B\*% | C% |
|---|---|---|---|---|---|---|
| T1_recta | 0.0 | 693.22 | -0.09 | 0.00 | -0.19 | -0.19 |
| T1_recta | 0.5 | 693.22 | **+5.62** | 0.00 | -0.19 | +1.92 |
| T1_recta | 1.5 | 693.22 | **+46.17** | 0.00 | -0.19 | +9.46 |
| T1_recta | 3.0 | 693.22 | **+138.48** | 0.00 | -0.19 | +19.42 |
| T2_virada | 0.0 | 693.22 | -0.07 | 0.00 | -0.19 | -0.19 |
| T2_virada | 0.5 | 693.22 | **+5.77** | 0.00 | -0.19 | +1.62 |
| T2_virada | 1.5 | 693.22 | **+46.79** | 0.00 | -0.19 | +8.36 |
| T2_virada | 3.0 | 693.22 | **+139.32** | 0.00 | -0.19 | +17.11 |
| T3_acel_decel | 0.0 | 569.49 | -0.04 | 0.00 | -0.27 | -0.27 |
| T3_acel_decel | 0.5 | 569.49 | **+7.61** | 0.00 | -0.27 | +2.56 |
| T3_acel_decel | 1.5 | 569.49 | **+68.60** | 0.00 | -0.27 | +12.43 |
| T3_acel_decel | 3.0 | 569.49 | **+184.89** | 0.00 | -0.27 | +24.53 |

Bias: A siempre **sobreestima** (+). B es ~0 y sin tendencia. B\* subestima levemente (-0.19/-0.27%).

## H1: CONFIRMADA
Evidencia: en T1_recta (sin viradas) el |error| de B es **0.000% en las 20 corridas**
(máx 0.000%), por debajo del 2%. Ninguna celda de T1 tiene >5% en 3/5 corridas.
**La virada no era la causa**: T2_virada da el mismo 0.00%. El ~10.6% de la Fase 1
era un artefacto de la referencia, no de B (ver INCERTIDUMBRES).

## H2: CONFIRMADA
Evidencia: peor celda con ruido (media de 5) — A **184.89%**, C 24.53%,
B\* **0.27%**, **B 0.00%**. B queda <5% en las 12 celdas realistas; B\* también.
Nota: C no cumple (<5%) porque arrastra la geometría ruidosa de A.

## H3: CONFIRMADA
Evidencia: con sigma=1.5 m, A sobreestima **+53.85%** en promedio (46.2-68.6% por
trayectoria), muy por encima del 20% y del 10% de refutación. A es inutilizable en
navegación realista; el error crece con el ruido (138-185% a sigma=3.0).

## DECISION PROPUESTA PARA NAVEGO
**Para medición de distancia, el método recomendado es B (`speed x dt` trapezoidal),
porque es el único con error <0.3% en las 12 celdas realistas e insensible al ruido
GNSS**, mientras A llega a +185%. A debe dejar de ser la fuente de distancia.
Salvedades obligatorias antes de cambiar código (no ejecutado en esta tarea):
(a) B es exacto en esta simulación porque el simulador entrega `speed` sin error y
`dt` exacto de 1 s — hay que medir en TCL T610P si el Doppler real se comporta así;
(b) B no puede medir distancia si no hay velocidad (quieto/deriva): hace falta el
fallback geométrico de C, hoy insuficiente por heredar el ruido de A.

## INCERTIDUMBRES
- **El 0.00% de B es en parte identidad del banco de pruebas**: el generador de GT
  integra posición con suma rectangular derecha, y el método B usa esa misma regla
  (`sog_kn*K*dt`). Verificado: rect−poly = +0.000000 m exacto. B mide bien porque
  reproduce el integrador del simulador, no porque se haya validado contra la física.
- **El ~10.6% de la Fase 1 provenía de la referencia, no de B**: `gt_reference`
  (Fase 1) integraba sog por trapecio y usaba `receivedAt`, y comparaba contra una
  polilínea; B rectangular daba 693.22 m (0.00%) sobre el GT completo. El sesgo de
  gap achicaba la referencia ~1.7%, no el 10.6%. La causa del 10.6% queda sin
  explicar con la evidencia disponible; **no la doy por resuelta**.
- El simulador no modela corriente/deriva ni error de velocidad propio; con 1% de
  error relativo de speed, B se mantiene <0.1% (probado), pero eso no sustituye
  una medición de campo.
- Sin cortes GNSS en este diseño (a propósito): no se evaluó B durante pérdida de señal.
