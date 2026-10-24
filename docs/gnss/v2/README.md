# Pipeline sintético V2 — Track Honesto

Estado: DISEÑO APROBADO, CÓDIGO EN REVISIÓN. **NO EJECUTAR AÚN.**

## Qué es esto

Pipeline experimental para comparar tres métodos de filtrado de distancia
GNSS bajo condiciones controladas y reproducibles:

- A  — filtro histórico (umbral fijo 15 m + delta mínimo 0,8 m)
- B  — producción real (`orchestrator.ts` + `processFix.ts`), VERIFICADO F.4/F.5 (límites en SOG/COG)
- C  — clasificador experimental (ΔreceivedAt > 2 s) OR (speed <= 0.3 m/s)
       con acción operativa (C.5.1: abre gap_event en GAP_REAL)

## Qué NO es esto

- No reemplaza ni modifica V1 (`docs/gnss/exp_dist/`, `exp_ruido_vs_gap/`,
  `exp_gaps_avance/`, `exp_dist2/`, `exp_dist3/`, `exp_fix_p1/`, `tcl_field/`).
- V1 queda congelado como evidencia histórica. Sus scripts no se
  vuelven a ejecutar desde acá.
- Ningún script de v2/ escribe fuera de v2/.
- No declara validada ni refutada ninguna hipótesis LOGOS.

## Reglas duras

1. Preservación V1: post-corrida, git status docs/gnss/exp_* debe
   quedar vacío. Si no, hay bug.
2. Mismas observaciones: A/B/C procesan exactamente el mismo fixes.jsonl.
   El evaluador verifica sha256 del archivo antes de correr los tres.
3. Etiquetas independientes: las produce gtgen/ y obsgen/, NO el
   evaluador. El evaluador solo las lee.
4. Separación temporal:
   - C.orig usa ΔreceivedAt para clasificar.
   - C.var (variante) usa ΔmeasuredAt.
   - Watchdog de B usa receivedAt.
   - processFix.dtSec de B usa measuredAt.
   - Vinculación fix↔GT usa measuredAt (nunca receivedAt).
5. B VERIFICADO (F.4/F.5): las zonas F.4 (processFix.ts 200-280)
   y F.5 (useNaveGoTracker.ts inline) están marcadas con TODO(F.4) /
   TODO(F.5) en eval/methods.py. No se declara que B reproduce
   producción hasta cerrar esas verificaciones.
6. Sin prejuicio sobre C: el escenario adversarial S16-S18 (barco
   detenido + ruido) puede mostrar falsos gaps de C.orig. NO se exige
   cero. Se mide y se documenta.

## Dos estados separados por método (crítico)

Cada método mantiene:
- last_observation_received_at — avanza con CADA fix, incluso rechazado.
- last_accepted_anchor (lat, lon, measuredAt) — avanza solo al aceptar
  o al cerrar un GAP_REAL. Rechazos de ruido NO lo mueven.

Confundir estos dos estados es el bug que produce falsos gaps de watchdog
por "rechazo".

## Dos distancias (crítico)

- d_pair: distancia entre observaciones consecutivas. Es el candidato
  histórico de C. Se usa para CLASIFICAR.
- d_anchor: distancia entre el ancla geométrica vigente y el fix actual.
  Se usa para ACUMULAR y para el umbral adaptativo de B.

C.orig clasifica por d_pair y acumula por d_anchor (decisión C.8).
C.pair (variante) clasifica y acumula por d_pair. C.var cambia receivedAt
por measuredAt. Cada variante tiene nombre propio y resultados separados.

## Decisiones cerradas

- C.1  — C.orig: receivedAt. C.var: measuredAt. Nombres separados.
- C.2  — GAP_REAL: cero distancia, ancla salta al fix post-gap.
- C.3  — RUIDO: rechaza sin mover ancla. Recuperación tras N rechazos (C.3.1).
- C.4  — una única regla de contabilización por intervalo.
- C.5  — C.orig abre gap_event en GAP_REAL. C.ctrl_no_event = control.
- C.5.1 — máximo un gap_event por interrupción. Watchdog y C comparten.
- C.6  — C se aplica después de accuracy, antes de MIN_DELTA, sobre d_pair > 15.
- C.7  — C comparte watchdog de 15 s; no duplica eventos.
- C.8  — C.orig acumula d_anchor (no d_pair). C.pair es variante.

## Fases

- Fase A (mínima): S1-S6, S10-S11, S16-S18. 3 trayectorias + adversarial.
- Fase B (completa): S7-S9, S12-S15. Solo si Fase A pasa los 8 criterios
  bloqueantes (ver tests/test_sanity.py).

## Cómo se corre (cuando se autorice)

Ver eval/run_all.py. Por ahora, no ejecutar.

## Contacto

Este pipeline se apoya en la auditoría de V1. Cualquier divergencia con
los informes de V1 se reporta como hallazgo, no como bug de V2.

> *Nota (2026-10-20): Se añadió la Sección 14 en HALLAZGOS_FASE_A_v1.md documentando el desacople entre el watchdog y el umbral adaptativo mediante un barrido de cortes (2s a 30s).*
