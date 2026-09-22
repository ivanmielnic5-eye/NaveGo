# ESPECIFICACION — logos-gate (Context Gate)

**Fecha:** 2026-09-22
**ID:** D-LOGOS-GATE-002
**Estado:** VIGENTE (contrato para implementacion)
**Propuesto por:** DeepSeek (sesion 2026-09-22).
**Autoridad final:** Ivan (Director Funcional).

---

## Proposito

Preflight obligatorio antes de autorizar a un agente a actuar sobre
el proyecto. Complementa al validador (que solo chequea estructura
del MANIFEST) agregando chequeos de coherencia y frescura.

Diferencia con validate-manifest:
- validate-manifest: "el MANIFEST esta bien formado?"
- logos-gate: "el sistema esta en condiciones de autorizar trabajo?"

El Gate es FAIL-CLOSED. Sin contexto valido -> BLOCKED.

---

## Contrato de entrada

- Parametro opcional: nombre del proyecto (ej: NAVEGO).
  Si se omite, se toma del MANIFEST.
- Comando: logos-gate [PROYECTO]
- Salida estandar: reporte legible + codigo de salida.
- Opcional: --json para salida estructurada (para consumo por script).

Codigos de salida:
- 0 = READY
- 1 = WARNING
- 2 = BLOCKED
- 3 = error interno (bug del Gate)

---

## Contrato de proceso

### Paso 0 — Precondicion

Si no existe .logos/MANIFEST.json -> BLOCKED inmediato.

### Paso 1 — Validacion estructural

Invocar .logos/bin/validate-manifest.
- Si BLOCKED -> el Gate hereda BLOCKED y termina.
- Si WARNING -> el Gate hereda WARNING (puede convertirse en BLOCKED
  si los pasos siguientes detectan algo peor).
- Si READY -> continuar.

### Paso 2 — Chequeos de coherencia

Ejecutar las consistency_rules declaradas en el MANIFEST.

Reglas implementadas en v1:
- CR-01 (project_identity):
    context.json debe tener un campo "project.id" que coincida con
    profile.json.id.
    Si no coincide -> BLOCKED con razon "conflict:project_identity".
- CR-02 (authority_uniqueness):
    Ya lo chequea el validador. El Gate lo hereda.

Reglas NO implementadas en v1 (documentadas para futuro):
- Hash match entre capsula y fuentes.

### Paso 3 — Chequeo de frescura (v1: informativo)

Comparar el mtime de context.json con la fecha de hoy.
- Si context.json tiene mas de N dias sin actualizar (default 7),
  agregar WARNING "stale:state" (no bloquea).
- N configurable en el MANIFEST por fuente (opcional).
- v1 usa 7 dias como default.

### Paso 4 — Construir reporte

Salida legible (por defecto):

    === LOGOS GATE — NAVEGO ===
    Manifest:         OK
    Required:         OK
    Authority:        OK
    Project identity: OK
    Freshness:        OK

    STATUS: READY

Salida JSON (con --json):

    {
      "status": "READY",
      "project": "NAVEGO",
      "checks": {
        "manifest": "OK",
        "required": "OK",
        "authority": "OK",
        "project_identity": "OK",
        "freshness": "OK"
      },
      "reasons": [],
      "warnings": [],
      "context_revision": "6e7b3e5a @ 2026-09-22",
      "evaluated_at": "2026-09-22T12:30:00-03:00"
    }

---

## Contrato de salida

### READY (exit 0)

Todas las validaciones pasaron. No hay warnings.
Significado: se autoriza arranque de agente.
Acciones permitidas: leer y escribir dentro del scope declarado.

### WARNING (exit 1)

Alguna validacion paso con advertencia pero no bloqueante.
Ejemplos: fuente opcional ausente, fuente required "vieja" pero
coherente, git sucio.
Significado: NO se autoriza arranque automatico de agente.
Acciones permitidas: leer. Escribir y arrancar agente requieren
autorizacion humana explicita (--force-warning).

### BLOCKED (exit 2)

Alguna validacion requerida fallo.
Ejemplos: MANIFEST ausente, fuente required ausente, contradiccion
de identidad, autoridad duplicada.
Significado: no se autoriza ninguna accion. STOP.

---

## Diferencia con logos-mem

- logos-mem genera una capsula (artefacto).
- logos-gate decide si autorizar o no (gatekeeper).
- logos-mem invoca al validador.
- logos-gate invoca al validador + chequeos propios.

Un wrapper (logos-dsh) va a:
1. Ejecutar logos-gate.
2. Si READY -> ejecutar logos-mem -> arrancar DSH.
3. Si WARNING -> mostrar warning, esperar decision humana.
4. Si BLOCKED -> detener.

---

## Reglas respetadas

- FAIL-CLOSED: default es no actuar.
- Gate verifica, no decide. R-16.
- No autoescritura. R-17.
- Incertidumbre explicita. R-19.
- El estado tiene procedencia (context_revision).

---

## Frase oficial

"El Context Gate no decide si el trabajo vale la pena; decide si el
sistema esta en condiciones de autorizarlo."
