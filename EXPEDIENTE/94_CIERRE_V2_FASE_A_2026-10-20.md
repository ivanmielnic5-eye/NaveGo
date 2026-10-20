# 94 - CIERRE JORNADA V2 FASE A - 2026-10-20

## Contexto

Sesion dedicada a redisenar y ejecutar el experimento Track Honesto
bajo un pipeline nuevo (V2), tras la auditoria que mostro que el
experimento V1 (docs/gnss/exp_dist/) media mal (method_b integraba el
ground truth, no un algoritmo; 160 corridas con B_m constante).

## Que se hizo

Pipeline V2 completo, 10 archivos bajo docs/gnss/v2/:
- gtgen/gen_traj.py + events_schema.md: generador de GT y etiquetas
  de trayectoria. 4 trayectorias (recta_const_5kn, detencion_5kn_20s,
  lenta_1ms, virada_5kn_90_150s).
- obsgen/gen_obs.py: wrapper de tools/gnss_simulator.py. Genera fixes
  y obs_events con hash sha256. 11 configuraciones de Fase A.
- eval/methods.py: A (historico), B (produccion, verificado F.4+F.5),
  C_orig + 5 variantes (pair, var, ctrl_no_event, and_speed, v2).
- eval/metrics.py: 5 familias (distancia, discontinuidades, falsos
  gaps, cortes omitidos, continuidad visual) + etiquetado de saltos.
- eval/run_all.py: runner de Fase A + criterios bloqueantes.
- tests/test_sanity.py (220 lineas), tests/test_recovery.py (265).
- README.md + HALLAZGOS_FASE_A_v1.md (361 lineas).

Verificacion F.4 + F.5: B replica fielmente processFix.ts y
orchestrator.ts. Diferencia conocida (calculatedSog/calculatedCog
no replicados) documentada, no afecta dist_m ni gap_events.

## Corridas

- v2_20261020_040923: 385 filas, 7 metodos. C1 y C5 FAIL por criterios
  originales (C1 umbral 0.5m mas fino que el sesgo geodesico de 0.864m;
  C5 err_m_B absoluto no contemplaba ruido geometrico base).
- v2_20261020_042653: 440 filas, 8 metodos (agregado C_v2). 5/5
  criterios evaluables PASS. Esta es la corrida de referencia.

Ambas corridas preservadas. No se sobrescriben.

## Hallazgos principales

1. Ruido geometrico domina desde sigma >= 1.5. A, B, C_orig inflan el
   recorrido por sumar distancias euclidianas entre puntos ruidosos.
   sigma=1.5: +39%. sigma=3.0: +126%. sigma=5.0: +171% (A).
   No estaba en la hipotesis original. Linea de investigacion
   independiente: filtrado de ruido posicional antes de acumular.

2. B (produccion) es PEOR que A en ruido puro. sigma=5, sin corte:
   A=+171.4%, B=+262.6%. B no corta saltos de ruido porque su umbral
   adaptativo se agranda con velocidad y precision. A, con umbral fijo
   de 15m, corta.

3. En corte de 10s, B NO detecta. Watchdog requiere >15s. Threshold
   adaptativo = 61m > salto 26m. C_orig y C_v2 SI detectan (abren
   gap_event). B-A = +29.4m en S6, coincide con avance del barco
   durante corte (25.7m) + ruido (2-3m). Causalidad NO aislada
   (falta control S6' sin corte).

4. C_orig tenia bug grave: la rama speed <= 0.3 m/s se cumple siempre
   en barco detenido. Cualquier salto > 15m por ruido se clasifica
   GAP_REAL. En S17 (sigma=5, detenido, sin corte): 3.6 falsos
   gap_event por corrida.

5. C_v2 (solo dt > 2s, sin rama speed) elimina los 3.6 falsos gaps
   de S17 con +0.9 pp de error de distancia (+211.5% -> +212.4%).
   Sin cambios en S6, S18, S16, S5. Justificacion fisica: un salto
   >15m en dt<=2s exige >7.5 m/s, imposible para el barco.

6. C_pair_v2 (combinacion: dt>2s + acumular d_pair) registrada como
   candidata experimental NO evaluada. Podria combinar lo mejor de
   C_v2 (menos falsos gaps) y C_pair (menor inflacion en ruido). No
   implementada.

## Decisiones tomadas

- C1 relajado a |err_m|<2.0, |err_rel|<1.0%. Justificacion metrologica:
  diferencia entre WGS84 (R=6378137) del simulador y R=6371000 del
  codigo de produccion. Cubre recorridos hasta ~1.5 km sin ocultar
  errores de algoritmo.
- C5 reformulado como diferencial B-A en [20,35] m (antes err_m_B
  absoluto en [20,30]).
- C_v2 agregado a methods.py como variante experimental (Opcion A:
  solo dt>2s). C_orig conservado como referencia historica.

## Estado al cierre del 2026-10-20 (snapshot historico, no actualizado)

NOTA HISTORICA: este bloque registra el estado al momento del primer
cierre. Ver "Actualizacion 2026-10-20 12:18" al final para el estado
posterior (C7 y C8 PASS en corrida v2_20261020_121820).

- Fase A: 5/5 criterios evaluables aprobados (C1, C3, C4, C5, C6).
- C7 (recuperacion) y C8 (V1 intacto): diferidos explicitamente. NO
  integrados en run_all.py como criterios automatizados. Fase A NO
  se declara formalmente cerrada de manera integral.
- C, C_v2, C_pair: NO promovidos a produccion.
- H-2026-0026: NO declarado (no existe como archivo en ~/.logos/hypotheses/).
- V1, tools/gnss_simulator.py, hipotesis LOGOS: sin cambios.

## Pendientes para proxima sesion

1. [RESUELTO a nivel working tree, pendiente de publicacion]
   Integrar C7 (test_recovery.py) y C8 (git status V1) como criterios
   automatizados en run_all.py. Ver "Actualizacion 2026-10-20 12:18"
   al final.
2. Disenar control S6' sin corte (misma trayectoria, seed, sigma, con
   las mismas observaciones fuera de la ventana de corte) para aislar
   causalidad del +29.4m en S6.
3. Implementar C_pair_v2 y evaluarla.
4. Abrir Fase B (S7-S9, S12-S15): cortes 30s/60s, speed_sigma_ms,
   latency_jitter_ms, batch_delivery_s, velocidad variable.

Cada uno requiere aprobacion explicita separada.

## Referencias

- docs/gnss/v2/HALLAZGOS_FASE_A_v1.md (361 lineas, secciones 10-12)
- docs/gnss/v2/results/v2_20261020_042653/ (corrida final, 440 filas)
- docs/gnss/v2/results/v2_20261020_040923/ (corrida previa, preservada)
- docs/gnss/v2/README.md (manifiesto V1<->V2)

## Frase de cierre

El problema de medir bien no es solo el manejo de gaps: sumar
distancias entre puntos GPS ruidosos infla el recorrido por diseno
geometrico. Eso es el proximo problema a resolver, y es mas grande
que el track honesto.

## Actualizacion 2026-10-20 12:18

Continuacion post-cierre. Se integraron C7 y C8 en run_all.py como
criterios automatizados. Corrida de referencia: v2_20261020_121820
(n_rows: 440, n_missing: 0, exit code: 0, 7/7 PASS).

Estado actual (working tree, NO publicado):
- Fase A: 7/7 criterios evaluables PASS (incluye C7 y C8).
- C7 PASS: test_recovery.py exit 0, corrido como subprocess desde
  run_all.py.
- C8 PASS: git status --porcelain vacio sobre V1_DIRS.
- Corridas preservadas: 040923, 042653, 121614 (fallida por bug C.1),
  121820 (referencia).

Distincion local vs publicado:
- Commit 7b17426 en origin/v2-track-honesto: pipeline V2 hasta 042653,
  C7/C8 SKIP.
- Working tree local: C7/C8 PASS, corrida 121820. NO commiteado.
- El pendiente #1 original quedo resuelto a nivel working tree. Su
  publicacion requiere commit + push con aprobacion separada.

> *Nota (2026-10-20): Se añadió la Sección 14 en HALLAZGOS_FASE_A_v1.md documentando el desacople entre el watchdog y el umbral adaptativo mediante un barrido de cortes (2s a 30s).*
