# DECISION FINAL — MANIFEST v3 + Capsula de Memoria + Context Gate

**Fecha:** 2026-09-22
**ID:** D-LOGOS-MANIFEST-001
**Estado:** CERRADA — pendiente verificacion final GPT-4 antes de
implementar codigo.
**Decidido por:** DeepSeek (propuesta), GPT-4 (critica en 2 rondas),
Ivan (Director) delego decision final a DeepSeek con fundamento.

---

## Contexto

El incidente del 21 sep 2026 (inicio de hilo sin protocolo) revelo
una vulnerabilidad arquitectonica: el sistema dependia de que la IA
recordara el protocolo de arranque. Se diseno una solucion en cuatro
iteraciones con GPT-4. Esta decision cierra el diseno y lo deja listo
para implementacion.

## Componentes aceptados

### 1. MANIFEST.json
- Vive en el REPO (.logos/MANIFEST.json), no solo en ~/.logos/.
- Declara autoridad por tipo de dato. No declara estado.
- Campos globales: schema_version, manifest_version, project,
  updated_at, fail_closed (siempre true), required[], optional[],
  sources[], consistency_rules[].
- Por fuente: type, path, authority (true/false), role
  (singleton|collection), description, generated_by,
  validation_policy.
- Regla de autoridad: singleton = exactamente una fuente autoritativa
  por tipo. Collection = una fuente raiz autoritativa que contiene
  multiples elementos.

### 2. Capsula de Memoria
- Nombre: Capsula de Memoria (documento + componente conceptual).
- Comando canonico: logos-mem. Atajo: mem.
- Es DERIVADA. No es fuente de verdad. Se regenera.
- Contenido: identidad + estado + trabajo activo + hipotesis activa
  + decisiones pendientes + restricciones operativas + fuentes de
  verdad + reglas criticas + procedencia.
- Tamano objetivo: 3-8 KB. Maximo operacional: 12 KB.
- Incluye PROCEDENCIA (generated_at, project, context_revision,
  git_commit, manifest_version).
- Incluye CONTEXT_REVISION para detectar realidad vieja.

### 3. Context Gate
- Preflight obligatorio. Fail-closed.
- Calcula: exists, readable, nonempty, hash, freshness, coherence,
  authority_uniqueness, project_identity.
- Produce: READY | WARNING | BLOCKED.
- Sin contexto valido: NO se autoriza el agente.

### 4. Dos frentes separados
- Frente local (DSH): automatizacion total via logos-dsh.
- Frente web (ChatGPT, DeepSeek, Gemini): reduccion al minimo via
  capsula pegada manualmente.
- Ambos comparten la MISMA fuente de verdad.

### 5. Nivel de automatizacion (fases)
- Fase A: comando corto (mem) + recordatorio al abrir terminal.
- Fase B: capsula autogenerada al cambiar algo importante.
- Fase C: alias que genera + copia al portapapeles + avisa.

### 6. Root of Trust (v1)
- MANIFEST en git + commit aprobado + revision humana.
- Referencia externa en ~/.logos/trust/PROYECTO.json con
  approved_manifest_commit + approved_manifest_sha256.
- No hay firma criptografica en v1. Se contempla en v2.

### 7. Worktrees
- v1: 1 escritor por proyecto + N lectores/criticos.
- v2: N escritores con worktree independiente + locks.

### 8. Reglas criticas en la capsula
- Nucleo minimo autocontenido (5-7 reglas vitales) + puntero al
  archivo completo de protocolo. Los chats web no pueden leer disco.

### 9. Integraciones
- AGENTS.md: capa de instrucciones persistentes.
- ChatGPT Projects: cache de contexto (NO fuente de verdad).
- MCP: interfaz de acceso (NO cerebro de LOGOS).
- Portapapeles: si (comando mem copia al portapapeles).
- URL con params / servidor HTTP local / plugin navegador: overkill
  para v1, no se implementan.

## Tres propiedades obligatorias

1. La capsula es DERIVADA.
2. El Gate es FAIL-CLOSED.
3. El estado tiene PROCEDENCIA.

## Frase oficial

"La Capsula de Memoria no recuerda por nosotros; transporta el
estado verificable del sistema hasta el proximo contexto."

## Verificacion pendiente

Antes de implementar codigo, una verificacion final de GPT-4 sobre
este documento cerrado. No es nueva ronda de diseno. Es critica de
cierre. Si aprueba sin cambios: implementar. Si hay objeciones
fundadas: volver al Director.

## Reglas respetadas
- R-09: quien propone no cierra su rama. Verificacion final a GPT-4.
- R-10: no regresion. SESIONES.md migrado, no descartado.
- R-17: no autoescritura. Este documento declara, no decide solo.
