# Fase A3 — A+KALMAN vs B vs HIBRIDO POR ESTADO

Fecha: 2026-09-25 · `docs/gnss/exp_dist3/` · Scripts: `gen_trayectorias_a3.py`, `run_faseA3.py`
Evidencia: `salida_faseA3.txt`, `resultados_faseA3.json` (25 corridas + barrido de umbral).

## METODOLOGIA

- **Trayectorias (240 s, 1 Hz)**: T1_recta5 (5 kn), T2_virada (la actual), T3_quieto_nav
  (quieto 60 s + 5 kn 120 s + quieto 60 s), T4_garreo (oscilacion real ±0.5 m),
  T5_variable (0→6→0.5→4 kn, cruza 1 kn).
- **Ruido**: sigma_pos=1.5 m, sigma_speed=0.1 m/s. Sin cortes ni spikes.
  Semillas 5000-5004. **5 trayect. x 5 semillas = 25 corridas.**
  `tools/gnss_simulator.py` sin modificar (ya soportaba `speed_sigma_ms`).
- **A+Kalman**: Kalman 2 estados (posicion, velocidad) por eje, velocidad constante,
  R = sigma_pos² = 2.25 m², Q = 0.01² m²/s⁴; se mide la polilinea de la posicion
  filtrada con la MISMA logica gap>15 m / descarte <0.8 m que A.
- **B**: `speed_medido x dt` rectangular. **H**: A+K si v<1 kn, B si v>=1 kn.
- **GT**: polilinea de posiciones reales en instantes reportados (geometrica,
  independiente del speed). Para T4 se reportan **dos** GT para no elegir el favorable.

## RESULTADOS (error relativo %, media de 5 semillas; ref_m = GT camino)

| trayectoria | ref_m | A% | A+K% | B% | H% |
|---|---|---|---|---|---|
| T1_recta5 | 538.88 | +48.80 | +1.16 | +0.21 | +0.79 |
| T2_virada | 538.88 | +48.97 | +3.04 | +0.21 | +0.79 |
| T3_quieto_nav | 295.81 | +141.99 | +6.02 | +1.76 | +3.75 |
| T4_garreo | 96.97 | +534.12 | −93.22 | −89.84 | −93.22 |
| T5_variable | 413.74 | +82.10 | −3.53 | +0.23 | −1.07 |

Error absoluto medio (m): T1 A 263.0 / A+K 6.2 / B 1.2 / H 4.3 · T2 263.9 / 16.4 / 1.2 / 4.3 ·
T3 420.0 / 17.8 / 5.2 / 11.1 · T4 517.9 / −90.4 / −87.1 / −90.4 · T5 339.7 / −14.6 / 1.0 / −4.4.

A+K baja el error de A de ~50-140% a ~1-6% en navegacion. B sigue siendo el mejor con
movimiento. **T4 es caso aparte**: camino oscilado real 96.97 m vs desplazamiento neto real
0.63 m; A+K mide 6.58 m y B 9.85 m (miden deriva/ruido, no el camino); A crudo 614.90 m.

## H1: CONFIRMADA
Diffs |err_A+K − err_B| = 1.404 / 1.172 / 1.096 / 0.838 / 0.212 % → **5/5 < 5%** (criterio ≥4/5).

## H2: REFUTADA
A+K<10 m en **0/5** (89.4/90.5/88.7/89.7/93.8 m); B>50 m en **0/5** (87.2/87.0/88.0/86.7/86.7 m).
A+K **descarta los pasos <0.8 m** y mide solo la deriva neta (~7 m), no las 96.97 m de
oscilacion → error ~90 m. B **no acumula >50 m**: mide ~10 m de ruido de speed. La premisa
"B acumula deriva grande quieto" **no se reproduce** a sigma_speed=0.1 m/s; el problema real
es el opuesto: A+K **subestima** el garreo al filtrar/descartar la oscilacion.

## H3: REFUTADA
max|H| < max|A+K| y < max|B| en **0/2** (T3: 4.04 vs 6.52 y 2.28; T5: 1.37 vs 4.34 y 0.84).
Pareado por corrida (T3+T5, n=10): menor que ambos en **0/10**. La rama A+K <1 kn arrastra el
error de A+K y la rama B el de B: el switch mezcla errores. Barrido de umbral (T5): 0.5 kn
=0.611%, 1.0=1.071%, 1.5=3.203%, 2.0=4.447% → bajar el umbral ayuda pero **no alcanza a B puro (+0.23%)**.

## DECISION PROPUESTA PARA NAVEGO

**Recomendado: B (speed x dt) con fallback a A+Kalman.** B gana en las 5 trayectorias con
movimiento (≤0.23% salvo T3 +1.76%) y es estable a 5 kn, virada y velocidad variable.
**No se recomienda el hibrido por estado**: H3 refutada, mezcla errores y nunca mejora a ambos.

- **Umbral**: no aplica. Si el Director insiste en el switch, el mejor medido es **0.5 kn**,
  pero sigue sin superar a B puro.
- **Fallback sin speed valido**: **A+Kalman** (1.16-6.02% en navegacion), **no A crudo**
  (+49% a +142%). Bajo 1 kn / garreo **ninguno es confiable**: A+K subestima y B mide ruido;
  lo honesto es **no acumular y declarar el tramo** sin dato.
- A+Kalman es un upgrade real de A si se prefiere seguir midiendo por geometria de posicion.

## INCERTIDUMBRES

- **T4 sin GT unico defendible**: camino oscilado (96.97 m) vs neto (0.63 m) dan veredictos
  opuestos; se reportan ambos. Que significa "distancia recorrida" para NaveGo queda al Director.
- **Q del Kalman = 0.01 m/s² fijo**, no optimizado ni barrido (fuera del diseno fijado).
- **Ruido de speed blanco**; el Doppler real tiene sesgo y correlacion temporal. No modelado.
- **Sin cortes de GNSS**; el hibrido por estado no cubre gaps.
- **No verificado en hardware**: H-2026-0001 (TCL T610P) sigue abierta. A+K agrega costo de CPU no medido.
- **B "gana" en parte por identidad del banco**: GT y B comparten la regla rectangular; sus
  errores chicos pueden estar subestimados.
