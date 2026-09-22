# ESPECIFICACION — logos-dsh (wrapper de arranque)

**Fecha:** 2026-09-22
**ID:** D-LOGOS-DSH-001
**Estado:** VIGENTE (contrato para implementacion)
**Propuesto por:** DeepSeek (sesion 2026-09-22).
**Autoridad final:** Ivan (Director Funcional).

---

## Proposito

Wrapper de arranque que ejecuta el flujo completo antes de autorizar
a DSH sobre el proyecto: Gate (preflight) + Capsula (contexto) + DSH
(ejecucion).

Resuelve el problema del incidente del 21 sep 2026: sin contexto
valido, DSH no arranca.

---

## Contrato de entrada

- Parametro 1 (obligatorio): nombre del proyecto (ej: NAVEGO).
- Parametro 2 (obligatorio): tarea en lenguaje natural.
- Flags:
    --force-warning : autoriza arranque aunque el Gate de WARNING.
    --dry-run       : ejecuta Gate + Capsula pero NO llama a DSH.

Comando: logos-dsh PROYECTO "tarea" [--force-warning] [--dry-run]

---

## Contrato de proceso

### Paso 0 — Preflight (Gate)

Ejecutar logos-gate PROYECTO.
- BLOCKED -> ABORTAR. DSH no se invoca.
- WARNING -> si NO hay --force-warning, ABORTAR con mensaje claro.
- READY -> continuar.

### Paso 1 — Generar capsula

Ejecutar logos-mem PROYECTO.
- Si falla -> ABORTAR.
- Salida: capsula-de-memoria.md en la raiz del repo.

### Paso 2 — Construir prompt

Prompt = contenido de capsula-de-memoria.md + separador + tarea.

Formato:
  [CONTEXTO - Capsula de Memoria]
  {contenido de capsula-de-memoria.md}

  [TAREA]
  {tarea del usuario}

  [REGLA]
  Trabaja respetando el contexto anterior. Si algo no esta en el
  contexto, declaralo como incertidumbre en lugar de inventarlo.

### Paso 3 — Ejecutar DSH

Llamar: dsh --profile headless "<prompt>"

### Paso 4 — Reportar

Al terminar:
- Mostrar codigo de salida de DSH.
- Mostrar el context_revision usado (de la capsula).
- Si DSH produjo cambios en el repo, avisar que hay diff para revisar.
- NO hacer commit automatico. El humano decide.

---

## Contrato de salida

### Exit codes

- 0: DSH ejecuto y devolvio 0.
- 1: DSH ejecuto pero devolvio != 0 (tarea fallo).
- 2: Gate BLOCKED. DSH no se ejecuto.
- 3: Gate WARNING y falta --force-warning. DSH no se ejecuto.
- 4: logos-mem fallo (no se pudo generar capsula).
- 5: error interno del wrapper (bug).

### Aviso al terminar

Al finalizar exitosamente (o no), el wrapper reporta:
- Status del Gate (READY/WARNING forzado).
- context_revision usado.
- Exit code de DSH.
- Si hay cambios sin commitear: mostrar git status resumido.

---

## Reglas respetadas

- FAIL-CLOSED: sin Gate READY, DSH no arranca.
- El wrapper no decide. Orquesta. R-16.
- No autoescritura sobre git: no hace commit. R-17.
- Incertidumbre explicita en el prompt. R-19.
- El estado tiene procedencia (context_revision visible).

---

## Fuera de alcance (v1)

- NO implementa worktrees.
- NO implementa multiples escritores en paralelo.
- NO hace commit automatico.
- NO valida el contenido del diff producido por DSH.
- NO revierte cambios si DSH falla.

Todo eso son evoluciones v2.

---

## Frase oficial

"El wrapper no confia en el agente; confia en el contexto que el
agente recibe."

