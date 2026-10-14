# PENDIENTES ABIERTOS — registro institucional

**Creado:** 2026-10-14 (D-2026-0013)
**Regla:** ninguna propuesta que requiera aprobacion del Director
queda olvidada por avance del workflow. Sin respuesta explicita,
sigue pendiente. La IA detecta, registra y recuerda; no aprueba.

Estados posibles: PENDIENTE_DE_LECTURA | PENDIENTE_DE_APROBACION |
APROBADO | RECHAZADO | DIFERIDO (con motivo y condicion de revision).

---

## PENDIENTES ACTIVOS

### P1 — D-B "No-olvido de pendientes"
- Estado: APROBADO (D-2026-0013, 2026-10-14).
- Ubicacion: `.logos/decisions/D-2026-0013.json`.
- Cerrado.

### P2 — D-A "Auditar Entrenador antes de entrenar"
- Estado: APROBADO (D-2026-0012, 2026-10-14).
- Ubicacion: `.logos/decisions/D-2026-0012.json`.
- Cerrado.

### P3 — D-C "Comparaciones justas antes de auditar"
- Estado: APROBADO (D-2026-0014, 2026-10-14).
- Ubicacion: `.logos/decisions/D-2026-0014.json`.
- Cerrado.

### P4 — R-21 (kernel multi-IA): version concisa de D-B
- Estado: PENDIENTE. Se agrega despues de aprobar D-B (ya aprobada).
- Accion: redactar R-21 y agregar a `~/.logos/core/protocol/protocols.json`.
- Referencia: D-2026-0013.

### P5 — R-22 (kernel multi-IA): version concisa de D-C
- Estado: PENDIENTE. Se agrega despues de aprobar D-C (ya aprobada).
- Accion: redactar R-22 y agregar a `~/.logos/core/protocol/protocols.json`.
- Referencia: D-2026-0014.

### P6 — Procedimiento vinculado a D-A
- Estado: PENDIENTE. Metodo detallado de auditoria del Entrenador.
- Accion: definir ubicacion autoritativa (verificar MANIFEST) y redactar.
- Referencia: D-2026-0012, nivel B.6.

### P7 — Reparacion del bug en PROTOCOLO.md
- Estado: PENDIENTE. Seccion "Proteccion de Decisiones Arquitectonicas" termina en "Formato obligatorio:" sin formato.
- Accion: commit independiente. Documentar alcance exacto.
- Referencia: hallazgo 2026-10-14.

### P8 — Limpieza de escapes markdown en PROTOCOLO.md
- Estado: PENDIENTE. Verificar primero si las barras invertidas son literales del archivo o efecto de representacion.
- Accion: si son literales, corregir y validar en commit independiente.
- Referencia: hallazgo 2026-10-14.

### P9 — R3 "Leer fuentes completas antes de planificar"
- Estado: PENDIENTE. Agregar a PROTOCOLO.md en seccion nueva "Reglas metodologicas obligatorias".
- Accion: redactar y agregar. Debe dejar explicito como actuar cuando no puedan leerse integramente.
- Referencia: EXPEDIENTE/71 (leccion de metodo), criterios de Luna.

---

## REGLAS DE ESTE REGISTRO

1. Un pendiente no se cierra por silencio ni por paso de tiempo.
2. Solo el Director marca APROBADO, RECHAZADO o DIFERIDO.
3. DIFERIDO requiere motivo y condicion de revision explicitos.
4. La IA puede agregar pendientes; no puede cerrarlos.
5. Referencia cruzada obligatoria con la D o el memo de origen.
