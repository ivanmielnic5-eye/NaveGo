# DOC 46 FASE 2 — Task aislada (background location)
## Cerrada el 2026-09-30

**Estado:** COMPLETA.
**Commit:** pendiente (se hace al cerrar este documento).
**Rama:** experimento-v4-admin

---

## Objetivo de Fase 2

Crear una Task de background que reciba ubicaciones del OS
mientras la app esta en segundo plano o la pantalla apagada.
La Task escribe a un JSONL de prueba. NO toca SQLite.
watchPositionAsync sigue activo en paralelo.

Verificacion: abrir app, apagar pantalla 60s, encender 60s,
cerrar. El JSONL debe tener fixes de los 3 periodos.

---

## Implementacion

### Archivos nuevos

`tasks/backgroundLocationTask.ts` (71 lineas):
- Define `TaskManager.defineTask('NAVEGO_BACKGROUND_LOCATION', ...)`.
- Escribe cada fix recibido a `documentDirectory/background_test.jsonl`.
- Solo campos minimos: source, t, lat, lon, accuracy, speed, heading.
- No importa React, SQLite ni el tracker.

### Archivos modificados

`devConfig.ts`:
- Nuevo flag `BACKGROUND_TEST_ENABLED` (env var
  `EXPO_PUBLIC_GNSS_BACKGROUND_TEST === '1'`).

`useNaveGoTracker.ts`:
- Import side-effect de la Task (para que `defineTask` corra).
- Nuevo `useEffect` que arranca la Task si el flag esta activo
  y REPLAY esta desactivado. Usa `startLocationUpdatesAsync`
  con foregroundService (notification persistente).
- Al finalizar sesion, copia el archivo `background_test.jsonl`
  al SAF con nombre `tcl_bgtask_<timestamp>.jsonl`.


---

## Prueba realizada (2026-09-30, 10:09 - 10:17)

**Escenario:** tres bloques de grabacion consecutivos.

- Bloque 1 (10:09 - 10:12): celular prendido, caminata + patineta.
- Bloque 2 (10:12 - 10:14): celular con pantalla apagada, caminando.
- Bloque 3 (10:14 - 10:17): celular prendido, caminando.

**Metodo:** la Task y watchPosition corrieron en paralelo. Ambos
escribieron a archivos separados. Al finalizar, se copiaron via
SAF a `/sdcard/Download/navego_track/`:
- `tcl_bgtask_1790774241332.jsonl` (Task)
- `tcl_field_1790774240939.jsonl` (watchPosition)

---

## Resultados

**Task (background):**
- 425 fixes
- Duracion: 449 s (10:09:51 a 10:17:20)
- Cadencia: 1.06 s/fix

**watchPosition (field):**
- 323 fixes
- Duracion: 336 s (10:11:40 a 10:17:16)
- Cadencia: 1.04 s/fix

**Captura por minuto (Task):**
- 10:09: 2 (arranque)
- 10:10: 41 (estabilizandose)
- 10:11 a 10:16: 60, 60, 60, 60, 61, 60 (1 Hz exacto)
- 10:17: 21 (cierre)

**Huecos detectados:** 6, todos en los primeros 32 segundos
(10:09:51 a 10:10:23). Despues de eso: captura continua sin
interrupcion durante 6 minutos 27 segundos.


---

## Hallazgo critico para Fase 2.5 (gate de exclusividad)

**Los dos productores reciben los MISMOS fixes del sistema operativo.**

Evidencia:
- Timestamps identicos entre Task y watchPosition: **323**.
- Pares cercanos <200 ms: 324.
- Los 323 fixes de watchPosition estan TODOS dentro de la Task.

**Implicacion:** en Fase 3, si los dos escriben a SQLite sin gate,
cada fix entra dos veces al pipeline. La distancia se duplicaria.

Numeros concretos del experimento:
- Task sola (futuro Fase 3 con gate): 425 fixes.
- watchPosition solo (alternativa): 323 fixes.
- Los dos sin gate: 748 fixes. **Incorrecto.**

El gate de exclusividad (Fase 2.5) NO es opcional. Es obligatorio.

---

## La Task sobrevive a pantalla apagada

**Confirmado con datos.**

El Bloque 2 (10:12 - 10:14) tuvo el celular con la pantalla apagada.
La captura fue continua: 60, 60, 60 fixes por minuto. 1 Hz exacto.

Comparacion con bloques con pantalla encendida: identico.
La Task no distingue entre pantalla encendida y apagada.

---

## Diferencias con watchPosition

- La Task arranca cuando la app abre (10:09:51).
- watchPosition arranca cuando el tracker se inicializa (10:11:40).
- La Task captura 102 fixes extra durante esos 2 minutos de
  diferencia. **En Fase 3 el gate decidira cuando cada uno
  captura, no cuando arranca la app.**

---

## Verificaciones completadas

- [x] Build release con expo-task-manager y permisos.
- [x] Task definida y registrada al arranque.
- [x] Task captura fixes con la app en foreground.
- [x] Task captura fixes con la pantalla apagada.
- [x] Task captura fixes con la app en segundo plano.
- [x] Task NO toca SQLite.
- [x] Task escribe a JSONL y sobrevive a la sesion.
- [x] Copia al SAF al finalizar sesion.
- [x] Demostrado que los dos productores ven el mismo stream.
- [x] Demostrado que sin gate hay duplicacion.

---

## Conclusion

**Fase 2 cumple el objetivo.** La Task de background funciona,
captura en segundo plano y con pantalla apagada, sin tocar el
pipeline actual. El experimento ademas confirma la necesidad
del gate de exclusividad de Fase 2.5.

**Siguiente:** Fase 2.5 (gate) y Fase 3 (Task como productor
real). Ambas dependen del diseno del gate.

---

## Backups relevantes

- `devConfig.ts.pre-bgtask`
- `useNaveGoTracker.ts.pre-bgtask`
- `useNaveGoTracker.ts.pre-saf-copy`

---

*Generado: 2026-09-30*
*Por: agente (chat) bajo direccion del Director Ivan Mielniczuk*
