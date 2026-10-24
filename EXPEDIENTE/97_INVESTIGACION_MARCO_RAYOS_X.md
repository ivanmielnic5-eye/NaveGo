# 97 — INVESTIGACIÓN: INGENIERÍA INVERSA Y DESARROLLO PROPIO MEDIANTE EL MARCO DE RAYOS X

**Estado:** EXPLORATORIO — NO NORMATIVO
**Fecha de materialización:** 2026-10-22
**Clasificación:** Investigación independiente. No es decisión D, no es regla R,
no es fuente autoritativa del MANIFEST, no autoriza implementación.

---

## Parte I — Marco metodológico de rayos X

### Propósito

Estudiar artefactos externos (software, formatos, protocolos, binarios,
configuraciones) para extraer patrones y desarrollar soluciones propias,
sin copiar, sin adoptar por analogía y sin comprometer la independencia
metodológica del proyecto.

### Sobre la metáfora

"Rayos X" designa el acto de observar el interior de un artefacto sin
modificarlo. La metáfora es ilustrativa, no normativa: la observación
revela estructura, no autoriza adopción. El producto de la observación
es evidencia; la adopción requiere un proceso separado.

### Pasos del marco

1. **Observar** un artefacto externo sin modificarlo.
2. **Registrar** lo efectivamente observado y las fuentes que respaldan
   la observación.
3. **Extraer** un patrón posible, diferenciándolo explícitamente de la
   implementación original.
4. **Formular una hipótesis falsable** que permita contrastar si ese
   patrón aporta algo al problema propio.
5. **Desarrollar una solución propia** y validarla en un entorno de
   prueba adecuado.
6. **Evaluar** compatibilidad, licencia, acoplamientos y cumplimiento de
   los requisitos propios.
7. **Recomendar** adoptar, adaptar o descartar el patrón. La decisión
   final queda al Director.

### Criterio de análisis: estructura vs lógica de dominio

La distinción entre capa estructural/interoperabilidad y capa de lógica
de dominio es un **criterio de análisis**, no una presunción de seguridad.

- Ambas capas requieren los mismos filtros (licencia, hipótesis falsable,
  verificación de acoplamiento).
- Lo que cambia es **qué se espera encontrar** en cada una, no el nivel
  de exigencia.
- Ningún patrón es adoptable "porque es estructural". Ningún patrón es
  inaceptable "porque es de dominio".

### Límites del marco

- **Observar no es copiar.** Toda implementación posterior es desarrollo
  propio con decisiones propias.
- **Documentar no es formalizar.** Este expediente no crea norma.
- **La observación no autoriza por sí misma la adopción.** La adopción
  requiere hipótesis, validación y decisión del Director.
- **Observación autorizada.** La inspección se limita a artefactos, datos
  y métodos cuyo acceso y análisis estén autorizados y sean compatibles
  con la legislación y las condiciones aplicables. No se eluden controles
  de acceso ni se accede a información privada sin autorización.

---

## Parte II — Nota metodológica para futuras fichas

Este expediente no contiene actualmente fichas de investigación cerradas.
Define únicamente el formato que adoptarán cuando exista un artefacto
externo concreto.

### Formato de una ficha

Cada ficha deberá contener, como mínimo:

1. **Artefacto examinado:** nombre, versión, procedencia, licencia conocida
   o a verificar.
2. **Pregunta de investigación:** falsable, acotada a un aspecto observable.
3. **Evidencia requerida:** qué tipo de información se espera obtener
   (protocolo, formato, algoritmo, esquema, endpoint).
4. **Patrón o mecanismo hipotético:** qué se cree que podría revelar el
   artefacto.
5. **Criterios de refutación:** qué observación haría descartar la hipótesis.
6. **Método de validación propia:** qué prueba demostraría que el patrón
   funciona en entorno propio sin arrastrar acoplamiento.

La ficha debe distinguir explícitamente:

- **Hechos observados** (evidencia directa).
- **Inferencias** (lectura razonada de la evidencia).
- **Hipótesis** (conjetura a contrastar).

### Candidatos identificados (no fichas)

- **NMEA (protocolo de comunicaciones náuticas).** Candidato prioritario
  para la primera ficha. La especificación exacta (versión, extensión
  propietaria si la hubiere, documentación pública disponible) debe
  determinarse antes de abrir la ficha. Mientras no se identifique la
  especificación, permanece como candidato, no como investigación
  delimitada.

- **Auditoría de soberanía / trazabilidad de comunicaciones externas.**
  Línea de interés abierta. Sin artefacto externo concreto seleccionado.
  Se abrirá ficha cuando se identifique un artefacto, su versión, su
  procedencia y una pregunta falsable.

### Lo que una ficha no es

- No es decisión D.
- No es regla R.
- No es fuente autoritativa del MANIFEST.
- No autoriza implementación.

---

## Fuentes y trazabilidad

Este expediente no cuenta todavía con fuentes primarias verificadas para
casos concretos. Las fuentes se registrarán por investigación, a medida
que cada caso se delimite, indicando:

- Artefacto examinado y su procedencia.
- Documentación pública disponible.
- Observaciones directas realizadas.
- Evidencia recolectada.

Hasta que exista una primera ficha con fuentes verificadas, esta sección
permanece como declaración de estado, no como listado de fuentes.

---

## Límites de este expediente

- **Carácter exploratorio y no autoritativo.** No crea categoría documental
  nueva, no modifica el protocolo, no resuelve la discrepancia entre
  `03_WORKFLOW.md` y `protocols.json`, y no altera P41.
- **Sin adscripción a proyecto o línea concreta.** Este expediente no se
  adscribe a ningún proyecto o línea de desarrollo concreta. Cualquier
  vinculación futura requerirá una decisión expresa del Director.
- **Sin presunción de simetría.** La ausencia de una segunda ficha no se
  suple con un caso inventado.
- **Autoría.** Redacción asistida por IA; revisión y aprobación a cargo
  del Director.

---

## Estado de aprobación

- **Redacción:** asistida por IA.
- **Revisión:** conformidad organizacional de Luna sobre el diseño del expediente (2026-10-22); verificación de coincidencia entre borrador y archivo materializado a cargo del Director.
- **Aprobación del contenido:** aprobada por el Director el 2026-10-22.
- **Autorización de materialización:** otorgada por el Director el 2026-10-22.
- **Fecha de materialización:** 2026-10-22.
