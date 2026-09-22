# HITO — Sistema LOGOS v1 operativo

**Fecha:** 2026-09-22
**Estado:** OPERATIVO Y VERIFICADO

---

## Que es

Sistema de gobernanza de contexto para agentes IA. Resuelve el
problema del incidente del 21 sep 2026: un chat nuevo arrancaba
sin contexto y tomaba decisiones incorrectas.

Regla del sistema:
"La conversacion no es la memoria. La memoria vive en archivos
versionados, auditables, reutilizables."

---

## Componentes construidos

### 1. MANIFEST.json
Declara autoridad por tipo de dato. 21 fuentes declaradas.
Ubicacion: .logos/MANIFEST.json

### 2. validate-manifest
Valida estructura del MANIFEST: campos, paths, autoridad unica.
Exit codes: 0 READY / 1 WARNING / 2 BLOCKED.

### 3. logos-mem
Genera la Capsula de Memoria. Archivo derivado de 2.7 KB con
identidad, estado, hipotesis activa, decisiones pendientes,
restricciones y procedencia. Incluye context_revision
deterministico (hash corto + fecha) y git_commit.

### 4. logos-gate
Preflight obligatorio. Fail-closed. Checks:
manifest, required, authority, project_identity, freshness.
Exit codes: 0 READY / 1 WARNING / 2 BLOCKED.

### 5. test-context-01
Test de regresion del incidente del 21 sep. 5 casos adversos.
Resultado: 5/5 pasando.

### 6. logos-dsh
Wrapper de arranque. Orquesta: Gate -> Capsula -> DSH.
Prompt construido con capsula + tarea + regla.
Exit codes: 0 OK / 1 DSH fallo / 2 BLOCKED / 3 WARNING sin force /
4 mem fallo / 5 error interno.

---

## Context por proyecto

Se creo ~/.logos/projects/NAVEGO/context.json (estado propio de
NAVEGO). El context global de ~/.logos/context/context.json sigue
perteneciendo al meta-sistema LOGOS.

Resuelve la contradiccion que el Gate detectaba (state decia LOGOS,
profile decia NAVEGO).

---

## Puertas de entrada

- START_HERE.md  -> puerta para humanos e IA.
- AGENTS.md      -> instrucciones persistentes para agentes IA.

---

## Verificacion

- TEST-CONTEXT-01: 5/5 pasa.
- Smoke test end-to-end: DSH con contexto de la capsula respondio
  correctamente sobre el estado real del proyecto (decision de
  mapas: Etapa 3 PENDIENTE).

---

## Lo que NO esta en v1 (evoluciones futuras)

- Worktrees para multiples escritores.
- Firma criptografica del MANIFEST (root of trust v2).
- Hash match entre capsula y fuentes.
- Rescate de ESTADO.md y SYNC_BRIEF.md (pendiente).
- Integracion MCP como interfaz de acceso.

---

## Frase del sistema

"La Capsula de Memoria no recuerda por nosotros; transporta el
estado verificable del sistema hasta el proximo contexto."
