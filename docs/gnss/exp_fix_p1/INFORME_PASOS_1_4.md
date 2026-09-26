# INFORME PASOS 1-4 — FIX P1 (rutas de referencia suman gaps)

Fecha: 2026-09-25 · `docs/gnss/exp_fix_p1/`
Evidencia: `fixture.json`, `gen_fixture.py`, `test_ref_route_no_gap.py`,
`backups/journal.ts.PRE_FIX_P1`.
Codigo del bug: `db/journal.ts` -> `createReferenceRouteFromSession`
(calculo de distancia, lineas 115-123 pre-fix).
Nota: los pasos 5-7 NO se ejecutaron (fuera de alcance).

## PASO 1 — FIXTURE
- `fixture.json`: 1 sesion (`SESSION_FIXTURE_P1`), 230 fixes, 1 gap
  CLOSED (`duration_ms=11000`). Reconstruido replicando el loop de
  `useNaveGoTracker.ts` sobre evidencia ya congelada de
  `exp_gaps_avance` (escenario `gap_corto_10s_30m`, semilla 7000,
  sigma=1.0). NO se modifico el simulador.
- Distancia de la sesion (tracker, con corte de gap): **773.880 m**
- Distancia de la ruta de referencia (naive journal.ts): **808.141 m**
- Divergencia: **+34.260 m**
- Avance real del gap (GT): **30.000 m**. Residuo +4.26 m = alineacion
  borde-ventana ya documentada (INFORME_GAPS_AVANCE H2), no bug nuevo.
- **H1 CONFIRMADA** (referencia > sesion; diferencia del orden del avance
  del gap). Se reporta el residuo, no se oculta.

## PASO 2 — BACKUP
- Comando: `cp db/journal.ts backups/journal.ts.PRE_FIX_P1`
- sha256 identico (db vs backup): `f857b164...d30a16b`.
- Verificacion H2: `cp backups/journal.ts.PRE_FIX_P1 /tmp/... && diff
  db/journal.ts /tmp/...` -> **diff vacio**.
- **H2 CONFIRMADA.**

## PASO 3 — TEST (rojo)
- Como corre: `python3 docs/gnss/exp_fix_p1/test_ref_route_no_gap.py`.
  Compila `db/journal.ts` REAL con `tsc` (commonjs), arma una SQLite
  real (`node:sqlite`) con el fixture y llama
  `createReferenceRouteFromSession`. No es una copia del bug.
- Antes del Fix A: **RED** (exit 1). reference=808.141, session=773.880,
  divergencia +34.260 m > tolerancia 8 m.
- **H3 (parcial) CONFIRMADA.**

## PASO 4 — FIX A
- Cambio en `db/journal.ts` (unico archivo tocado, diff vs backup = +17/-1):
  - Se consultan los gaps CLOSED de la sesion en `gap_events`
    (`start_fix_id`, `end_fix_id`).
  - En el loop de distancia: `if (gapSegments.has(prevId->curId)) continue;`
    Se excluye SOLO el segmento puente pre-gap/post-gap.
  - NO se tocaron filtros de accuracy/quality/delta.
- Despues del Fix A: **GREEN** (exit 0). reference=775.953, session=773.880,
  divergencia **+2.072 m**.
- Verificacion independiente: `full(808.141) - bridge(32.188) = 775.953`
  = resultado del Fix A (excluye exactamente el tramo del gap).
- Golden path (fixture sin `gap_events`): distancia = 808.141 m, igual
  al calculo viejo -> el fix es no-op si no hay gaps (no sobre-corrige).
- `tsc --noEmit db/journal.ts`: exit 0.
- **H3 (completa) CONFIRMADA. H4 CONFIRMADA** (|divergencia| 34.26 -> 2.07 m).

## RESULTADO
- **Fix A solo alcanza? SI, para el criterio fijado** (divergencia del
  orden del gap eliminada; residual 2.07 m < 8 m). La divergencia
  restante NO es del gap: es el distinto tratamiento de pasos
  sub-umbral (<0.8 m) entre tracker y ruta de referencia.
- Si se exigiera divergencia ~0: faltaria alinear el criterio de
  descarte (posible paso 6, filtros). No fue el alcance de este fix.
- Proximo paso recomendado: pasos 5-7 segun plan aprobado. Antes de
  cerrar, decidir si el residual 2.07 m es aceptable o si el paso 6
  debe unificar el descarte del tracker con el de la ruta.

## INCERTIDUMBRES
- No se ejecuto en TCL T610P ni en la app real: solo `db/journal.ts`
  contra SQLite en Node. H-2026-0001 sigue abierta.
- El fixture asume que `gap_events` de la DB real tiene `end_fix_id`
  poblado en gaps cerrados (verificado en harness y schema, no en DB
  de dispositivo).
- Gaps `abandonGap` (sin `end_fix_id`) no se excluyen; si quedan
  `CLOSED` sin end_fix_id, ese tramo no esta cubierto por Fix A.
- Verifique que `getSessionFixes` (SELECT *) devuelve `id`: probe
  aislado OK, el match de segmentos no falla por eso.
