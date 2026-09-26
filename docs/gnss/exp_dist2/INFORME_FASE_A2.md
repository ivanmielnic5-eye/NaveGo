# Fase A2 — B con Doppler imperfecto
Fecha: 2026-09-25 · `docs/gnss/exp_dist2/` · Scripts: `run_faseA2.py`, `gen_trayectorias_a2.py`
Evidencia: `salida_faseA2.txt`, `resultados_faseA2.json` (60 corridas).

## METODOLOGIA
3 trayectorias x 4 sigma_speed x 5 semillas = **60 corridas**. sigma_pos fijo 1.5 m, sin
cortes ni spikes. Cambio en `tools/gnss_simulator.py` (backup previo; retrocompatible):
`speed_medido = max(0, speed_real + N(0, sigma_speed))`; se agrega `speed_real` al fix.
GT = polilínea de posiciones reales (independiente de speed). A = réplica de
`useNaveGoTracker.ts`; B = `speed x dt` rectangular; B\* = trapezoidal; C = combinado
(B\* si v≥1 kn, A si v<1 kn). T1_recta (5 kn, 693.22 m) · T4_lenta (1 kn, 151.50 m) ·
T5_variable (0→6→0.5→4 kn, 487.05 m). ss = 0.05/0.1/0.2/0.5 m/s · semillas 4000-4004.
Bias: A sobreestima siempre y **no depende de ss** (solo de sigma_pos); B casi insesgado
hasta 0.2, y a 0.5 el clamp a ≥0 sesga al alza (T4: +8.93%).

## RESULTADOS (error relativo %, media de 5 semillas; columnas = ss m/s)

| trayectoria (ref_m) | método | 0.05 | 0.10 | 0.20 | 0.50 |
|---|---|---|---|---|---|
| T1_recta (693.22) | A | +49.65 | +49.65 | +49.65 | +49.65 |
| T1_recta | B | +0.05 | +0.10 | **+0.21** | **+0.55** |
| T1_recta | B\* | −0.14 | −0.09 | +0.02 | +0.35 |
| T1_recta | C | +8.51 | +8.49 | +8.42 | +7.24 |
| T4_lenta (151.50) | A | +425.67 | +425.67 | +425.67 | +425.67 |
| T4_lenta | B | −0.02 | −0.02 | **+0.04** | **+8.93** |
| T4_lenta | B\* | −0.20 | −0.21 | −0.16 | +8.67 |
| T4_lenta | C | +218.37 | +221.14 | +225.75 | +230.65 |
| T5_variable (487.05) | A | +93.98 | +93.98 | +93.98 | +93.98 |
| T5_variable | B | +0.06 | +0.12 | **+0.35** | **+1.80** |
| T5_variable | B\* | −0.15 | −0.09 | +0.13 | +1.56 |
| T5_variable | C | +34.78 | +35.14 | +35.14 | +33.31 |
## H1: CONFIRMADA
T1_recta, ss=0.2 → |err B| = **0.05/0.12/0.16/0.25/0.47%**, **5/5 < 10%** (criterio ≥4/5).
## H2: REFUTADA
T4_lenta (1 kn), ss=0.2 → B peor que A en **0/5 corridas** (criterio ≥3/5). |B| = 0.18-1.10%
vs |A| = 412-458%: con 1.5 m de ruido el paso real es 0.507 m/s pero el medido 2.56 m
(mediana), 5x inflado; el descarte <0.8 m solo elimina 23/299 intervalos. **A baja
velocidad A es peor, no mejor.**
## H3: REFUTADA
T5_variable, max|C| < max|A| y < max|B| en **0/4 celdas** (criterio ≥4). Ej. ss=0.2:
max|A|=102.91%, max|B|=0.73%, **max|C|=37.63%**. Causa medida: la rama A (v<1 kn) aporta
184.89 m cuando la distancia real de ese tramo es ~14 m (~170 m de ruido geométrico).
El fallback a A rompe C, no la integración de velocidad.
## DECISION PROPUESTA PARA NAVEGO
**Recomendado: B trapezoidal (B\*); B rectangular equivalente en la práctica.** Con Doppler
realista (ss≤0.2 m/s) B queda <0.5% en las 3 trayectorias, incluso 1 nudo y velocidad
variable; A va de +50% a +426%. Única celda de B >1%: ss=0.5 en T4 (+8.93%), sesgo del
clamp a ≥0, no del método.
**Fallback si no hay speed: NO usar A como está** (infla >400% a baja velocidad). Opciones
a medir antes de decidir (no evaluadas aquí): (a) última velocidad válida con timeout,
(b) descarte adaptativo al accuracy en vez del 0.8 m fijo, (c) marcar el tramo sin dato.
Sin speed, hoy lo honesto es **no acumular** y declarar el gap.
## INCERTIDUMBRES
- Ruido de speed blanco y por-fix; el Doppler real tiene sesgo, correlación temporal y
  dependencia de la dinámica (multipath, aceleración). No modelado.
- **Clamp a ≥0 = sesgo real**: ss=0.5 en T4, 46/300 fixes a 0, media 0.569 vs 0.505 real.
- **B mide "bien" en parte por identidad del banco**: el integrador del GT y B comparten la
  regla rectangular; los errores chicos pueden estar subestimados.
- **No verificado contra hardware.** H-2026-0001 (TCL T610P) sigue abierta.
- **C no fue optimizado**: se usó el umbral 1 kn especificado; otras reglas no se probaron.
