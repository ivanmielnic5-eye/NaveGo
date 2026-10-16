# BRIEF DE CIERRE — Hilo FOCO contrato_intent + Gobernanza
# Fecha: 2026-10-14
# Rama: experimento-v4-admin
# HEAD al cierre: da4514b (pusheado a origin)

## QUE SE HIZO

7 commits pusheados:

  b7d9a27  Contrato Intent A4 con estados por campo atomico (D-2026-0011)
  ea66e3d  Gobernanza: 3 decisiones de cierre institucional (D-0012/13/14)
  822a4d8  P8: limpieza de formato en PROTOCOLO.md (escapes + CRLF)
  0409e8e  P7: reparar seccion 'Formato obligatorio' en PROTOCOLO.md
  bac8583  P10: registrar pendiente de marcacion visual de outputs
  30c77c6  P9: seccion 'Reglas metodologicas obligatorias' con R3
  da4514b  P7/P8/P9 cerrados en registro de pendientes

Decisiones congeladas nuevas (4):
  D-2026-0011  Contrato Intent A4: 4 estados por campo atomico.
  D-2026-0012  Auditar Entrenador antes de entrenar.
  D-2026-0013  No-olvido de pendientes del Director.
  D-2026-0014  Comparaciones justas antes de auditar.

Artefactos nuevos:
  EXPEDIENTE/PENDIENTES.md  Registro institucional de pendientes.
  PROTOCOLO.md seccion "Reglas metodologicas obligatorias" con R3.
  PROTOCOLO.md seccion "Formato obligatorio" completa (8 puntos).

## NOMENCLATURA / LECCIONES

- "Oraculo" -> "Entrenador" (obsoleto desde memo 86).
- Commit != aprobacion. D-XXXX es la constancia autoritativa.
- Busquedas son evidencia, no veredicto. Declarar cobertura.
- Scratch != memo != D-XXXX. Tres niveles, no jerarquia.
- R-17 kernel multi-IA: una IA no convierte propuesta en decision.
- "Ningun pendiente que requiera aprobacion del Director queda
  olvidado" — D-2026-0013, regla permanente.

## PENDIENTES ACTIVOS

Todos en EXPEDIENTE/PENDIENTES.md. Los principales:

  P4   R-21 kernel multi-IA (version concisa de D-0013).
  P5   R-22 kernel multi-IA (version concisa de D-0014).
  P6   Procedimiento vinculado a D-0012 (metodo de auditoria).
  P10  Marcacion visual de outputs (idea, no urgente).
  --   logos-foco v1: diseñado, no implementado. Hilo nuevo.
  --   Validacion manual de logos-foco sobre mision_config.
  --   Secciones 23/24/26 del memo 89 (A2/A3/A4).

## ESTADO DE BRIEF_NAVEGO

EXPEDIENTE/BRIEF_NAVEGO.md y BRIEF_NAVEGO_pegable.txt quedan
modificados sin commitear (autogenerados, se regeneran cuando
haga falta). No entran al repo.

## COMO ARRANCAR EL PROXIMO HILO

1. Correr logos-arranque (arranque general).
2. Leer EXPEDIENTE/PENDIENTES.md (estado de pendientes).
3. Leer este brief (contexto del hilo anterior).
4. Segun lo que se vaya a hacer:
   - logos-foco v1: leer _log_comando_foco.md (scratch untracked).
   - A4 / Intent: leer contrato_intent.md + D-2026-0011.
   - Gobernanza: leer D-2026-0012/13/14 + PENDIENTES.md.

## SCRATCH DEL HILO (untracked)

  _log_foco_intent.md         270 lineas (cerrado, puede tener ruido).
  _log_comando_foco.md         69 lineas (logos-foco, abierto).
  _log_cierre_institucional.md 138 lineas (cerrado).

  D-A.borrador.json / D-B.borrador.json / D-C.borrador.json
  (los tres aprobados; se materializaron como D-0012/13/14).
  Pueden eliminarse o conservarse como historial. Decide el Director.

## CIERRE

Hilo cerrado el 2026-10-14. HEAD = da4514b, sincronizado con
origin/experimento-v4-admin.
