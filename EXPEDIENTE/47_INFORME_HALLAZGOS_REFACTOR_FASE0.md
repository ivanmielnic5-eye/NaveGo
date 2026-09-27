# INFORME 47 — HALLAZGOS DEL REFACTOR FASE 0

**Fecha:** 2026-09-26
**Estado:** pendiente de evaluación por GPT-4
**Sobre:** refactor de `useNaveGoTracker.ts` que separa `processFix` de los efectos (Doc 46, Fase 0)
**Metodología:** análisis propio del chat actual + análisis independiente de DSH (modo headless) + cruce.

---

## 1. Contexto

### 1.1 Qué es Fase 0

Del Doc 46 (EXPEDIENTE/46_PLAN_BACKGROUND_LOCATION.md, líneas 35-49):

> Extraer la lógica del callback actual a una función que recibe un fix crudo y devuelve un resultado determinista, sin tocar SQLite ni React.
>
> Verificación: mismo replay, mismos fixes, gaps, distancia y estado. Comparar contra una corrida grabada antes.

### 1.2 Qué se refactorizó

Un callback de ~140 líneas en `useNaveGoTracker.ts` que hacía 16 tareas mezcladas, partido en tres piezas:

1. `processFix(input, state)` — función pura, sin efectos, en `tracker/processFix.ts`.
2. `publishUiResult(result, location)` — solo efectos de UI.
3. `persistFixResult(result, location)` — solo efectos de SQLite.

El callback nuevo quedó en ~35 líneas: arma `input`, captura `state`, llama `processFix`, despacha los dos efectos.

### 1.3 Estado actual

- Fase 0 aplicada en working tree (commit f70a68b + cambios sin commitear).
- TypeScript: 0 errores nuevos.
- Backups `3A` y `3B` presentes.
- Baseline de replay del 24-09 resultó inválido (log viejo es de un `.jsonl` de 62 fixes; actual es de 270; y no grabó sesión). No hay test de regresión formal ejecutado.
- Fase 1 (infraestructura de background) NO arrancada.

---

## 2. Análisis cruzado

### 2.1 Metodología

- **Chat actual (DeepSeek):** análisis del diff línea por línea y del código completo, sin ejecutar nada.
- **DSH (modo headless):** análisis del mismo diff, sin acceso al hook completo (solo tenía el diff).
- **Cruce:** se cotejaron hallazgos. Los que aparecen en ambos → alta confianza. Los que aparecen en uno solo → verificados manualmente contra el código.

### 2.2 Tabla resumen

| ID  | Hallazgo | Visto por | Veredicto |
|-----|----------|-----------|-----------|
| L1  | Orden de logs [FILTER] vs [DIST] cambia | Chat | real, cosmético |
| L2  | fieldTestLog y logs [FILTER] ahora requieren dbRef | Chat | real, bajo impacto |
| L3  | openGapIdRef = null más tarde en POST | Chat | real, bajo impacto |
| L4  | Si closeGap falla, ref no se limpia | Chat | real, solo error path |
| 3-A | Telemetría viva cuando pausa/no-graba | DSH | FALSO POSITIVO (DSH no tenía el hook completo) |
| 3-D | Timing del cierre de gap + posible race | Ambos | real, cosmético |
| 3-E | lastCog divergente | DSH (duda) | sin problema (verificado) |
| 3-F | Log [DIST] | Ambos | cosmético (equivale a L1) |
| 3-G | Logs [FILTER] condicionados a persist | DSH | regresión real (equivale a L2, elevado) |
| 3-H | Doble Date.now() en measuredAt | DSH | regresión sutil real |
| 4   | 7 riesgos para migrar a background | DSH | correcto, es trabajo de Fase 1+ |

### 2.3 Hallazgos con impacto real

**G1 — Logs [FILTER] condicionados a persist.**
En PRE: [FILTER] acc se emitía siempre que accuracy > MAX_ACCURACY_M, incluso sin sesión ni DB.
En POST: está dentro de persistFixResult, con early-return por !result.persist, !sessionIdRef.current, !dbRef.current.
Impacto: cualquier test que cuente logs [FILTER] va a dar distinto. También cualquier debugging que dependa de esos logs durante replay sin sesión activa.

**G2 — Doble Date.now() en measuredAt.**
El callback calcula input.measuredAt = location.timestamp || Date.now().
persistFixResult vuelve a calcular measuredAt: location.timestamp || Date.now() para el fieldTestLog.
Si location.timestamp es null/0, los dos Date.now() pueden diferir.
Impacto: bajo. El fieldTestLog es auditoría SAF, no lógica.

**G3 — Unhandled rejection en void persistFixResult.**
El callback hace void persistFixResult(result, location) sin .catch.
El código viejo tenía .catch(() => {}).
Si persistFixResult rechaza (por ej. closeGap falla), el rechazo escala sin manejar.
Impacto: medio. En RN puede generar warnings o crasheos en producción.

### 2.4 Falsos positivos

**3-A (telemetría viva cuando pausa).** DSH no tenía el hook completo. El hook actual llama publishUiResult(result, location) incondicionalmente, siempre. processFix devuelve persist:false en pausa, pero publishUiResult corre igual. No hay pérdida de telemetría.

### 2.5 Verificaciones que aclararon dudas

**3-E (lastCog divergente).** Verificado contra tracker/processFix.ts:
- Línea 242: lastCog: calculatedCog (en nextState).
- Línea 249: liveCog: calculatedCog (en el resultado).
- publishUiResult hace lastCogRef.current = result.nextState.lastCog y setCurrentCog(result.liveCog). Mismo valor. Sin divergencia.

---

## 3. Preguntas abiertas para GPT-4

1. **¿G1, G2 y G3 ameritan fix antes de Fase 1, o se aceptan como diferencias documentadas?** La restricción original era "semántica observable al 100%". G1 rompe esa restricción en el plano de logs.

2. **¿Fase 0 se considera cerrada sin test de regresión formal?** El baseline del 24-09 resultó inválido. Alternativas posibles: (a) aceptar auditoría analítica + auditoría DSH como cierre, (b) generar un nuevo baseline corriendo PRE y POST desde worktrees, (c) otro.

3. **¿Los 7 riesgos para background (sección 4 de DSH) son Fase 1, Fase 2, o bloquean algo?** Especialmente 4.1 (refs de React en Task sin UI montada) y 4.2 (setters de React desde la ruta de persistencia).

4. **¿Cómo documentar el uso de DSH como analista?** Este informe es el primer caso de DSH integrado a un flujo real. ¿Se formaliza un protocolo? ¿Se archiva como precedente?

5. **`.logos/dsh-output/` tiene 17 archivos del 25-09 más este nuevo.** ¿Se mantienen todos? ¿Se archivan los viejos?

---

## 4. Anexo A — Análisis completo de DSH

[pendiente: pegar texto íntegro en un segundo paso]

---

## 5. Anexo B — Análisis propio del chat actual

[pendiente: pegar texto íntegro en un segundo paso]

---

*Generado: 2026-09-26*
*Por: DeepSeek (chat) bajo dirección del Director*
