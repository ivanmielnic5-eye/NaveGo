# ESPECIFICACION — Estados del Context Gate

**Fecha:** 2026-09-22
**ID:** D-LOGOS-GATE-001
**Estado:** VIGENTE (autoritativo)
**Propuesto por:** DeepSeek (sesion 2026-09-22).
**Criticado por:** GPT-4 (verificacion de cierre).
**Autoridad final:** Ivan (Director Funcional).

---

## Proposito

Definir operacionalmente que significa cada estado del Context Gate,
especialmente WARNING, para que la implementacion no introduzca
ambiguedad ni regreso silencioso al problema original.

El Gate es FAIL-CLOSED (fail_closed = true). El default es no-actuar.

---

## BLOCKED — sin autorizacion para actuar

**Cuando se dispara:**
- Falta el MANIFEST.
- Falta una fuente declarada como required.
- Hay dos fuentes con authority:true para el mismo tipo singleton.
- Contradiccion entre fuentes (ej: context.json dice NAVEGO y
  profile.json dice SIMULATOR).
- Proyecto no identificable.

**Accion permitida:** ninguna.
- No arranca agente.
- No se permite leer ni escribir.
- STOP.

---

## READY — autorizacion completa

**Cuando se dispara:**
- Todas las fuentes required existen, son legibles, no vacias.
- Autoridad unica por tipo singleton.
- Sin contradicciones entre fuentes.
- Proyecto identificado.
- Manifest valido.

**Accion permitida:**
- Leer y escribir dentro del scope declarado.
- Generar capsula de memoria.
- Arrancar agente.

---

## WARNING — autorizacion condicional

**Cuando se dispara (ejemplos):**
- Falta una fuente declarada como optional (todas las required OK).
- Una fuente required esta "vieja" (frescura superada) pero legible
  y coherente.
- Git sucio (hay cambios sin commitear) pero MANIFEST valido.
- La capsula tiene context_revision menor que el sistema
  (realidad vieja).

**Accion permitida:**
- LEER: siempre permitido.
- REPORTAR el warning al humano.
- ESCRIBIR: NUNCA sin autorizacion humana explicita para ese caso.
- NO arrancar DSH automaticamente.

**Regla de oro del WARNING:**
"Leer si, escribir no, sin permiso humano."

**Corolario:**
El wrapper logos-dsh no debe arrancar DSH en WARNING automaticamente.
Debe mostrar el warning y esperar accion humana explicita
(ej: logos-dsh navego --force-warning "objetivo").

Con fail_closed=true, un WARNING es INFORMACION AL HUMANO,
no autorizacion implicita.

---

## Resumen operacional

| Estado  | Leer | Escribir | Arrancar agente |
|---------|------|----------|-----------------|
| READY   | Si   | Si       | Si              |
| WARNING | Si   | No*      | No*             |
| BLOCKED | No   | No       | No              |

(*) WARNING: escribir y arrancar agente requieren autorizacion
humana explicita para ese caso concreto.

---

## Reglas respetadas
- R-04: ninguna accion sin evidencia. El Gate produce evidencia
  del estado.
- R-16: contexto no es autoridad. El Gate verifica, no decide.
- R-17: no autoescritura. El WARNING no autoriza por si solo.
- Fail-closed: el default es no-actuar.
