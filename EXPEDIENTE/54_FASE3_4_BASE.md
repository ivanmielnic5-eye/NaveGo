# DOC 46 FASES 3+4 — BASE IMPLEMENTADA
## Task escribe a SQLite, React consumidor (base)

**Fecha:** 2026-09-30
**Estado:** BASE FUNCIONAL. Verificacion con datos pendiente.
**Rama:** experimento-v4-admin
**Commit actual:** 2050e81

---

## Objetivo cumplido

La Task de background recibe ubicaciones del OS y las procesa
en SQLite via el orquestador. React sigue funcionando con
watchPosition en paralelo, escribiendo a una sesion real
separada de la sesion test de la Task.

Arquitectura:

  OS -> Task -> Orquestador -> SQLite
                                  |
                          (mismo tiempo)
                                  |
                    watchPosition -> SQLite (sesion real)

Sin mezcla: dos session_id distintos. La sesion de la Task se
llama `TASK_TEST` y se crea desde el hook cuando el flag
BACKGROUND_TEST_ENABLED esta activo.

---

## Componentes implementados

### 1. Orquestador (tracker/orchestrator.ts)
- processBatchInDb(db, sessionId, fixes): procesa un batch
  completo cargando el estado UNA VEZ al inicio.
- detectAndOpenGapIfNeeded: detecta gap por timestamp sin
  timers. Umbral GAP_THRESHOLD_MS=3500.
- processOneFix: por cada fix, detecta gap, ejecuta
  processFix, persiste raw, cierra gap si aplica, avanza
  cursor.

### 2. Helpers de estado (db/journal.ts)
- loadProcessStateFromDb: reconstruye ProcessState de SQLite.
- loadOrchestratorStateFromDb: ProcessState + metadatos de
  persistencia (lastFixId, lastSog, lastCog, lastAccuracy,
  openGapId, cursorSeq).
- findOrCreateTestSession: busca/crea sesion 'TASK_TEST'.
- saveIsPaused / saveLastProcessedSeq / advanceLastProcessedSeq.

### 3. Schema SQLite v3
Migracion v2 -> v3 agrega a sessions:
- is_paused INTEGER DEFAULT 0
- last_processed_seq INTEGER DEFAULT -1

### 4. Task de background (tasks/backgroundLocationTask.ts)
- Escribe JSONL (Fase 2, sin cambios).
- Abre SQLite con useNewConnection:true.
- Busca sesion TASK_TEST activa.
- Convierte locations a OrchestratorInput[].
- Llama processBatchInDb.

### 5. Hook (useNaveGoTracker.ts)
- Crea sesion test al iniciar grabacion si el flag esta activo.
- Ref testSessionIdRef.


---

## Hallazgo critico: expo-sqlite en Headless JS

**Sintoma:** la Task fallaba con:
"Call to function 'NativeDatabase.prepareAsync' has been rejected.
 Caused by: java.lang.NullPointerException"

**Diagnostico (3 pruebas):**
- PRUEBA A: Task abre 'test_prueba_a.db' (DB que el foreground
  no toca) -> OK.
- PRUEBA B (implícita): Task abre 'navego.db' -> falla.
- PRUEBA C: Task abre 'navego.db' con useNewConnection:true -> OK.

**Conclusion:** expo-sqlite SI funciona en Headless JS. El
problema era la coexistencia de conexiones. El foreground ya
tiene 'navego.db' abierta via SQLiteProvider; la Task reusaba
esa conexion cacheada y fallaba con NPE. `useNewConnection:
true` fuerza conexion nueva, compatible con WAL.

**Fix aplicado:** `SQLite.openDatabaseAsync('navego.db',
{ useNewConnection: true })` en la Task.

---

## Hallazgo critico: umbral de gap

**Sintoma:** 33 gaps abiertos en 98 fixes. Todos con
`elapsed=2001ms`. Todos se abrian y cerraban en el mismo fix.

**Causa:** el intervalo nominal del OS no es 1000ms sino
2000ms. Con GAP_THRESHOLD_MS=2000, cualquier jitter de 1ms
disparaba gap falso.

**Distribucion de elapsed medida:**
- 33 gaps: 2001ms (falsos)
- 3 gaps: 2084-2306ms (borde)
- 1 gap: 3066ms (borde)
- 16 gaps: 5033-7402ms (probablemente reales)
- 3 gaps: 239562ms, 514030ms, 1021522ms (reales, pausas
  largas de la app)

**Fix aplicado:** GAP_THRESHOLD_MS = 3500.

**Verificacion posterior:** corrida de 101s, 50+ fixes,
0 gaps falsos. Los 3 gaps reales de minutos se siguen
detectando.

---

## Verificacion funcional (por logcat)

Corrida 12:29:18 - 12:30:59 (101s):
- [TASK-BG] +1 fixes escritos          (JSONL, cada ~2s)
- [TASK-BG] DB: procesados=1 skipped=0 (SQLite, cada ~2s)
- [ORCH] gap abierto/cerrado           (0 en esta corrida)
- 0 errores de DB en el proceso actual


---

## Lo que NO se hizo todavia

1. **Verificacion de datos reales en la DB.**
   La APK es release, no se puede leer la DB via adb directo
   (`run-as` falla) ni via `adb backup` (Android 12+ lo
   bloquea para apps sin debuggable). Los datos existen pero
   solo los veriamos con export desde la app.

2. **Consumidor React.**
   Hoy el hook sigue siendo el productor (watchPosition). La
   Fase 4 real (React lee de SQLite) todavia no esta
   implementada. Lo que hay es la infraestructura para que la
   Task escriba en SQLite.

3. **Gate de exclusividad (Fase 2.5 -> Fase 3 real).**
   Hoy la Task y watchPosition conviven (una en sesion test,
   otra en sesion real). En Fase 3 de produccion, uno de los
   dos debe apagarse y el otro tomar el control.

4. **Pausa y fin de sesion desde la Task.**
   El boton PAUSAR/FINALIZAR del hook solo afecta la sesion
   real, no la test. En produccion, la Task tiene que saber
   cuando la sesion se pausa/finaliza.

5. **Fase 5 (Finalizar correctamente) y Fase 6 (Recuperacion
   de sesion ACTIVE) del Doc 46.**

---

## Proximos pasos sugeridos

1. Agregar export de DB via SAF (boton temporal en la app)
   para verificar los datos reales que escribio la Task.
2. Documentar el resultado de esa verificacion.
3. Avanzar con la Fase 4 real: mover el procesamiento del
   hook a la Task + hook consumidor.
4. Implementar el gate de exclusividad antes de apagar
   watchPosition en produccion.

---

## Backups relevantes

- tasks/backgroundLocationTask.ts.pre-prueba-a
- tasks/backgroundLocationTask.ts.pre-prueba-c
- tasks/backgroundLocationTask.ts.pre-cleanup
- tracker/orchestrator.ts.pre-threshold-3500
- db/journal.ts.pre-helpers
- db/journal.ts.pre-orch-state
- db/journal.ts.pre-test-session
- db/schema.ts.pre-v3
- useNaveGoTracker.ts.pre-test-session
- types/journal.ts.pre-task-source

---

*Generado: 2026-09-30*
*Por: agente (chat) bajo direccion del Director Ivan Mielniczuk*

---

## Analisis de datos crudos (DB exportada 2026-09-30)

DB exportada: navego_export_1790783523809.db (11 MB, SQLite v3).
Analisis via sqlite3 + Python.

### Contenido de la DB

- 17 sesiones (16 'Sesion NaveGo' + 2 'TASK_TEST' + 1 COMPLETED
  del viaje + 1 ACTIVE).
- Fuentes presentes en gps_fixes: GNSS, REPLAY, TASK.
- 2 sesiones TASK_TEST activas durante la prueba:
  - session_test_1790782158541_lje86nfa: 581 fixes TASK.
  - session_test_1790783428718_hxy3a7ma: 40 fixes TASK.
- Gap events: 44 totales. Todos CLOSED excepto uno (OPEN en
  sesion vieja de REPLAY, heredado).

### Verificacion de la Task

**Duplicados:** 1 en 141 fixes TASK (0.7%). Causa probable:
un fix aparecio en el ultimo batch del OS y en el siguiente.

**Frecuencia:**
- watchPosition: mediana 1000ms entre fixes.
- Task: mediana 2000ms entre fixes.

**Relacion entre productores:**
- 40 timestamps de TASK, todos dentro de los 76 de GNSS.
- 0 timestamps unicos en TASK.
- 36 timestamps de GNSS ausentes en TASK.

**Conclusion:** la Task recibe el mismo stream pero con menor
granularidad. `startLocationUpdatesAsync` corre en TaskService
y el OS agrupa/regatea los fixes. No es bug. En produccion (con
Task como unico productor) la distancia se acumula a 2s/fix,
suficiente para un velero tipico.

### Precision y calidad

- Accuracy mediana en los fixes de la Task: ~5-12 m.
- Quality GOOD en la mayoria. Algunos SUSPECT.
- Los accuracy altos (>10m) al arranque de la Task confirman
  que el GPS tarda ~5-10s en estabilizar cuando recien arranca
  la captura.

### Gaps reales registrados

Los gaps de minutos (239s, 514s, 1021s) estan todos en la
sesion real del viaje (28-29 sep), no en la sesion test. Eso
confirma que la Task y watchPosition mantienen sesiones
independientes sin mezcla.

