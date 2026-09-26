# EXP — GAPS CON AVANCE (embarcacion avanzando durante la perdida de senal)

Fecha: 2026-09-25 · `docs/gnss/exp_gaps_avance/` · Scripts: `gen_trayectorias_gap.py`, `run_gaps_avance.py`
Evidencia: `resultados_gaps_avance.json` (21 corridas), `tray_GAP*.jsonl`, `fixes_*.jsonl`, `gt_gap_manifest.json`.
Codigo auditado: `useNaveGoTracker.ts` (loop de grabacion), `db/journal.ts` (openGap/closeGap/abandonGap), `components/MapaOffline.tsx` (`aGeoJSON`, capa `trackActivoLine`).

## METODOLOGIA
- 3 escenarios fijados (10 s/30 m, 30 s/100 m, 60 s/200 m) en recta a velocidad constante, gap centrado en t=110 s, 240 s a 1 Hz.
- 5 semillas (7000-7004) por escenario con `sigma=1.0 m` (aisla el gap del ruido) = 15 corridas. Barrido de ruido extra `sigma=0.0` y `sigma=3.0`, 1 semilla por escenario = 6 corridas. **Total 21.**
- Fixes con `tools/gnss_simulator.py` **sin modificar** (`cut_windows`, latencia 300 ms, sin spikes).
- `run_gaps_avance.py` replica el loop de `useNaveGoTracker.ts`: persistir fix → closeGap si habia gap abierto → filtro accuracy>20 → haversine → `MAX_JUMP_DISTANCE_M=15` (`isGapRestart`, incremento=0) → descarte <0.8 m → alta del punto al track. Watchdog cada 1 s abre gap si el ultimo fix tiene >2 s.
- "Distancia app" se compara contra el desplazamiento GT (recta ⇒ camino = desplazamiento). "Salto de track" = mayor distancia entre puntos consecutivos de `routePoints` (lo que dibuja `aGeoJSON`).

## RESULTADOS (sigma=1.0 m: media de 5 semillas; sigma 0.0/3.0: 1 semilla)

| escenario | sig | dist_real_m | dist_app_m | error % | gaps | dur_gap_ms | esp_ms | salto_max_m | salto_track_m |
|---|---|---|---|---|---|---|---|---|---|
| corto 10 s / 30 m | 1.0 | 717.0 | 767.2 | **+7.00** | 1 | 11000 | 10000 | 32.2 | 32.2 |
| medio 30 s / 100 m | 1.0 | 796.7 | 760.4 | **−4.55** | 1 | 31000 | 30000 | 102.4 | 102.4 |
| largo 60 s / 200 m | 1.0 | 796.7 | 650.3 | **−18.38** | 1 | 61000 | 60000 | 202.3 | 202.3 |
| corto 10 s / 30 m | 0.0 | 717.0 | 683.2 | −4.71 | 1 | 11000 | 10000 | 33.0 | 33.0 |
| medio 30 s / 100 m | 0.0 | 796.7 | 692.6 | −13.07 | 1 | 31000 | 30000 | 103.2 | 103.2 |
| largo 60 s / 200 m | 0.0 | 796.7 | 592.7 | −25.61 | 1 | 61000 | 60000 | 203.1 | 203.1 |
| corto 10 s / 30 m | 3.0 | 717.0 | 1384.4 | +93.09 | 1 | 11000 | 10000 | 30.7 | 30.7 |
| medio 30 s / 100 m | 3.0 | 796.7 | 1281.6 | +60.88 | 1 | 31000 | 30000 | 100.9 | 100.9 |
| largo 60 s / 200 m | 3.0 | 796.7 | 1101.9 | +38.31 | 1 | 61000 | 60000 | 200.8 | 200.8 |

Rechazos por `MAX_JUMP_DISTANCE_M`: 1 por corrida (salto del gap) a sigma 0.0/1.0; **2** a sigma 3.0. `openGapIdRef` final = `null` en las 21 corridas; gap siempre `CLOSED`; 1 gap en `gap_events` por corrida.

## H1: CONFIRMADA
Evidencia: `salto_track == salto_max` en las 21 corridas (p.ej. 202.3 m a 60 s). El codigo lo explica: `aGeoJSON` (MapaOffline.tsx:55-64) arma **un unico `LineString`** con todos los puntos y `trackActivoLine` (446) es una `line` solida sin `line-dasharray` ni corte. El par pre-gap/post-gap son puntos consecutivos: la linea los une en recta. **No existe marcador ni separador de discontinuidad** en `routePoints` ni en la capa.

## H2: CONFIRMADA
Evidencia (sigma 0.0, aislado de ruido): deficit real−app = 33.8 / 104.1 / 204.0 m para avance de gap 27.0 / 96.7 / 196.7 m. El deficit es esencialmente el tramo no observado (residuo +6.8/+7.4/+7.3 m = alineacion borde-ventana). El salto se anula (`distanceIncrement=0`, linea 404) y **no se suma**. Correcto segun D-2026-0003. A sigma 3.0 el signo se invierte (+93 %) por ruido, no por el gap.

## H3: CONFIRMADA
Evidencia: `duration_ms` = 11000/31000/61000 ms y coincide **exactamente** con `receivedAt` del primer fix post-gap menos el ultimo pre-gap (idem `measuredAt`). `closeGap` usa `start_at_ms` del fix pre-gap (journal.ts:224-228). Nunca NULL/0/negativo. El +1000 ms sobre el nominal es de borde (corte empieza en t=110 s, primer fix vuelve en 121 s), no error de registro.

## PROBLEMA PRINCIPAL DETECTADO
1. **Primer orden — el track visual inventa el tramo del gap (H1).** NaveGo no suma la distancia (correcto) pero **si dibuja** el puente recto de 30-200 m como recorrido observado. Contradice D-2026-0003 en la capa visual.
2. **Segundo orden — el ruido se disfraza de gap.** Con `sigma=3.0 m` hay un salto de 15.0 m con `dt=1 s` (fix 147, corrida corta) tratado como `isGapRestart`: **corta la distancia** y **no registra gap**. A sigma 3.0 el error pasa de −25 % a **+93 %**: el ruido domina y `MAX_JUMP_DISTANCE_M` no distingue ruido de gap real.
3. **Menor — log enganoso.** `useNaveGoTracker.ts:373` calcula `durMs = currentTimestamp - lastFixTimestampRef.current`, pero `lastFixTimestampRef` ya fue actualizado con el fix actual (linea 339) ⇒ el log `[GAP] cerrado ... duracion=` da casi 0. La DB guarda bien (H3); solo el log miente.

## DECISION PROPUESTA PARA NAVEGO
- **Visual (amarillo, no toca GNSS ni distancia):** agregar `gap_flag`/`segment_id` a `routePoints` al detectar `isGapRestart` y partir `aGeoJSON` en MultiLineString (o dos sources) para **no unir** pre-gap con post-gap. Alternativa minima: `line-dasharray` o color distinto para el primer segmento post-gap. Requiere decision del Director sobre como se muestra el hueco (D-2026-0003).
- **Ruido vs gap (amarillo/rojo, requiere hipotesis previa):** no usar solo `MAX_JUMP_DISTANCE_M`; contrastar el salto con `dt` y `speed` (p.ej. salto >15 m con `dt<=2 s` = spike de ruido, no gap) antes de cortar distancia. **No ejecutar sin hipotesis y sin medir en TCL T610P.**
- **Log:** corregir el `durMs` de la linea 373 (capturar el timestamp previo antes de la linea 339). Sin impacto funcional.

## INCERTIDUMBRES
- Fase 2/A3 mostraron que A (haversine) es inutilizable con ruido; reconfirmado. **No se evaluo el metodo B** (`speed x dt`) frente a gaps: no se sabe si B integraria el speed viejo durante el corte.
- El **efecto visual no se verifico en pantalla**: H1 se sostiene por lectura de codigo y geometria de `routePoints`, no por captura en dispositivo (pendiente en TCL).
- **`sigma=3.0 m` es agresivo**; el GNSS real del TCL T610P no esta caracterizado. El +93 % puede ser pesimista.
- No modelado: perdida por **background/app suspendida** (`AppState` releyendo de SQLite, lineas 594-614 puede alterar `routePoints` sin marcar gaps); ni multi-gap solapado. No se probo gap que **no cierra** al terminar la sesion (`abandonGap`, cubierto por H-2026-0004): el gap siempre cerro dentro de los 240 s.
