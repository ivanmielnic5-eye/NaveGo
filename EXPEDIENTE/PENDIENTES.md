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
- Estado: CERRADO (commit 0409e8e).
- Seccion "Proteccion de Decisiones Arquitectonicas" ahora incluye
  "Formato obligatorio" completo (8 puntos, validados con Luna).
- Referencia: D-2026-0013 (regla de no-olvido).

### P8 — Limpieza de escapes markdown en PROTOCOLO.md
- Estado: CERRADO (commit 822a4d8).
- Escapes markdown eliminados (124 en total). CRLF -> LF.
  232 lineas tocadas, sin cambio semantico.
- Verificacion: 0 escapes restantes; archivo UTF-8 sin CRLF.

### P9 — R3 "Leer fuentes completas antes de planificar"
- Estado: CERRADO (commit 30c77c6).
- Seccion nueva "Reglas metodologicas obligatorias" en PROTOCOLO.md.
- R3 unica regla de la seccion. R2 y R4 ya tratadas via D-2026-0014
  y D-2026-0013 (sin duplicacion).

---


### P10 — Marcacion visual de outputs por seccion
- Estado: PENDIENTE. Idea del Director, no urgente.
- Idea: que un hilo pueda marcar visualmente las partes de un
  output para copiar solo lo necesario, no todo. Puede ser color,
  separadores, etiquetas, lo que sea que ayude a golpe de vista.
- Nota: si complica cualquier otra cosa, no se implementa.
- Candidatos de aplicacion: logos-foco, logos-gate, cualquier
  comando que devuelva bloques largos.
- A definir: mecanismo, compatibilidad con copia/pegado, si va
  solo en interactivo.
- Sin autoridad asignada todavia. Se retoma cuando logos-foco v1
  este funcionando y haya un caso real que lo justifique.


### P11 — LOGOS v1.1 sin formalizar como D-XXXX
- Estado: PENDIENTE. Reportado por el brief de arranque 2026-10-14.
- Situacion: LOGOS v1.1 (logos-reconcile + drift detection +
  logos-brief) esta implementado en el repo pero no fue
  registrado como D-XXXX en el registro instituido.
- Es el patron exacto que D-2026-0013 resuelve: trabajo hecho
  sin cierre institucional.
- Accion: redactar propuesta D-XXXX para LOGOS v1.1, referenciar
  commits de implementacion, someter a aprobacion del Director.
- Referencia: brief de arranque 2026-10-14, seccion 5.

### P12 — Pendientes del brief de arranque (2026-10-14)
- Estado: PENDIENTE. Items reportados por el brief en su seccion
  7 ("Pendientes priorizados"). Son del proyecto NAVEGO, no del
  hilo cerrado el 2026-10-14.
- Items:
  1. Track honesto — perdida por migracion Doc 46.
  2. Field log no se escribe tras reinicio del celular.
  3. Diseno pendiente: jerarquia de confianza de fuentes para
     cartas nauticas.
  4. Auto-commit WIP en logos-arranque.
  5. Blender MCP — velas dinamicas + timon + mastil no rigido.
- Accion: cada item se atiende por separado, con su propia
  hipotesis o propuesta segun corresponda. Este bloque los
  registra para que no se pierdan al regenerar el brief.
- Referencia: brief de arranque 2026-10-14.
## REGLAS DE ESTE REGISTRO

1. Un pendiente no se cierra por silencio ni por paso de tiempo.
2. Solo el Director marca APROBADO, RECHAZADO o DIFERIDO.
3. DIFERIDO requiere motivo y condicion de revision explicitos.
4. La IA puede agregar pendientes; no puede cerrarlos.
5. Referencia cruzada obligatoria con la D o el memo de origen.
