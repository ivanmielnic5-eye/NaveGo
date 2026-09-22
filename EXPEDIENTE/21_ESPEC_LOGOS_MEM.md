# ESPECIFICACION — logos-mem (generador de Capsula de Memoria)

**Fecha:** 2026-09-22
**ID:** D-LOGOS-MEM-002
**Estado:** VIGENTE (contrato para implementacion)
**Propuesto por:** DeepSeek (sesion 2026-09-22).
**Autoridad final:** Ivan (Director Funcional).

---

## Proposito

Generar la Capsula de Memoria del proyecto activo. Transporta el
estado verificable del sistema hacia un nuevo contexto (chat, agente).

La capsula es DERIVADA. No es fuente de verdad.

---

## Contrato de entrada

- Parametro unico: nombre del proyecto (ej: NAVEGO).
- Comando: logos-mem [PROYECTO]  (atajo: mem [PROYECTO])

---

## Contrato de proceso

### Paso 0 — Preflight obligatorio

1. Localizar MANIFEST (default: .logos/MANIFEST.json).
2. Ejecutar .logos/bin/validate-manifest.
3. Si resultado != READY -> ABORTAR sin generar capsula.
   - BLOCKED: no se puede generar capsula sin contexto valido.
   - WARNING: generar capsula con advertencia visible en la metadata.

### Paso 1 — Leer fuentes segun regla

Regla de lectura (por tipo de fuente):

- FUENTES REQUERIDAS (lectura completa):
    state, profile, protocol, decisions

- FUENTES CON EXTRACTO (lectura parcial):
    hypotheses   -> solo las que tengan estado EN_CURSO
    pending      -> solo los primeros 5 items

- FUENTES REFERENCIADAS (solo path, sin copiar contenido):
    architecture, workflow, incidents, multi_ia_protocol,
    framework_decision, decision_maps, decision_manifest,
    decision_gate, session_spec, spec_capsule, glossary, evidence

### Paso 2 — Calcular context_revision

context_revision = sha256(
    manifest_sha + state_sha + profile_sha + protocol_sha + decisions_sha
) primeros 8 caracteres.

Deterministico. Cambia si cambia cualquier fuente requerida o el
MANIFEST. No requiere estado externo. No usa timestamps como autoridad.

### Paso 3 — Calcular procedencia

Incluye en la metadata:

    generated_at         -> ISO 8601 con zona horaria
    project              -> NAVEGO
    context_revision     -> calculado en paso 2
    git_commit           -> HEAD actual (git rev-parse --short HEAD)
    manifest_version     -> extraido del MANIFEST
    generated_by         -> logos-mem v1.0.0

### Paso 4 — Escribir salida

Dos archivos, en la raiz del repo (o donde diga el MANIFEST):

    capsula-de-memoria.md     -> version legible (Markdown)
    capsula-de-memoria.json   -> version estructurada (metadata)

---

## Contrato de salida

### capsula-de-memoria.md

Estructura obligatoria, en este orden:

    # Capsula de Memoria — [PROYECTO]
    
    ## Procedencia
    (generated_at, context_revision, git_commit, manifest_version,
     generated_by)
    
    ## Identidad del proyecto
    (de profile: id, name, type, mission, capabilities)
    
    ## Estado actual
    (de state: status, risk, phase, next_step, last_decision)
    
    ## Trabajo activo
    (de state: work.hypothesis_id, work.hypothesis, work.next_step)
    
    ## Hipotesis activas
    (de hypotheses: solo las EN_CURSO, con id y descripcion)
    
    ## Decisiones pendientes
    (de pending: primeros 5 items)
    
    ## Restricciones operativas
    (de protocol: constraints activas + semaforo de riesgo)
    
    ## Reglas criticas
    (nucleo minimo autocontenido, 5-7 reglas vitales)
    
    ## Fuentes de verdad
    (lista de types + paths del MANIFEST, sin contenido)
    
    ## Advertencias
    (si las hubo: WARNING del validador, capsulas viejas, etc.)

Tamano objetivo: 3-8 KB. Maximo operacional: 12 KB.
Si supera 12 KB -> ABORTAR y reportar (no truncar silenciosamente).

### capsula-de-memoria.json

Estructura:

    {
      "metadata": {
        "generated_at": "...",
        "project": "NAVEGO",
        "context_revision": "a1b2c3d4",
        "git_commit": "abc1234",
        "manifest_version": "1.0.0",
        "generated_by": "logos-mem v1.0.0"
      },
      "sections": {
        "identity": {...},
        "state": {...},
        "active_work": {...},
        "hypotheses": [...],
        "pending": [...],
        "constraints": [...],
        "critical_rules": [...],
        "sources_index": [...]
      },
      "warnings": []
    }

---

## Errores posibles

- MANIFEST ausente -> BLOCKED.
- MANIFEST invalido -> BLOCKED.
- Fuente requerida ausente -> BLOCKED.
- Fuente requerida ilegible -> BLOCKED.
- Capsula supera 12 KB -> ABORTAR con reporte.
- Git commit no disponible (repo sin git) -> metadata git_commit = null,
  generar con WARNING.

---

## Reglas respetadas

- La capsula es DERIVADA. No se edita a mano.
- El MANIFEST es autoridad. La capsula lo respeta.
- El Gate es FAIL-CLOSED. Sin contexto valido, no hay capsula.
- El estado tiene PROCEDENCIA. context_revision es deterministico.
- R-17: no autoescritura. logos-mem solo transporta, no decide.
- R-19: incertidumbre explicita. Si falta algo, se marca.

---

## Frase oficial

"La Capsula de Memoria no recuerda por nosotros; transporta el
estado verificable del sistema hasta el proximo contexto."
