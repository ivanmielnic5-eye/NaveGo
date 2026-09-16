# 15 — Decisión de Arquitectura de Mapas

Fecha: 2026-09-16
Estado: EN PROCESO
Framework aplicado: EXPEDIENTE/14_FRAMEWORK_DECISION.md

## Pregunta

¿Qué arquitectura de datos cartográficos conviene para NaveGo?

## Opciones candidatas

- A: MBTiles híbrido (con D1: dump/reload)
- B: Dos archivos sueltos (render.mbtiles + navigation.sqlite)
- C: Dos archivos + manifiesto (con hashes y region_id)
- D: Directorio por región con archivos separados por capa
- E: Servidor local de tiles
- F: BASELINE — un solo MBTiles estándar sin tabla extra

## Etapa 1: VETOS — COMPLETADA

| Opción | ¿Pasa? | Razón |
|--------|--------|-------|
| A | PARCIAL | Depende de pieza única. Riesgo de pérdida simultánea (render + nav). |
| B | SÍ | Sin vetos. |
| C | SÍ | Sin vetos. |
| D | SÍ | Sin vetos. |
| E | SÍ | Introduce proceso runtime, pero no viola veto. |
| F | NO | No incluye datos de navegación. ELIMINADA. |

Conclusión:
- F eliminada.
- A con bandera amarilla.
- B, C, D, E pasan limpias.

## Etapa 2: PESOS CON JUSTIFICACIÓN

Regla: cada peso debe tener una justificación de una frase
vinculada a una restricción explícita de NaveGo.
Los pesos se fijan ANTES de puntuar.

### Criterios núcleo

| Criterio | Peso | Justificación |
|----------|------|---------------|
| Soberanía | 10 | Principio no negociable. Sin dependencias externas. |
| Tolerancia a fallos | 9 | Offline-first: no hay servidor de respaldo. |
| Mantenibilidad | 9 | 1 dev + IAs. Sin esto el sistema se vuelve inmantenible. |
| Integridad + Proveniencia | 8 | R-04 + R-18. Datos íntegros y rastreables. |
| Recuperabilidad | 8 | Post-incidente Windows, central. |
| Testeabilidad | 8 | R-04. Sin test no hay evidencia. |
| Degradación funcional | 8 | El sistema debe seguir útil al perder dependencias. |
| Simplicidad operativa | 7 | Menos operaciones humanas = menos fallos. |
| Reversibilidad | 7 | Volver atrás sin destruir datos. |
| Observabilidad | 7 | Diagnóstico en operación real, no solo en lab. |
| Interoperabilidad | 7 | Convive con Godot, LOGOS, Android, iOS, GIS. |
| Costo de cambio futuro | 6 | Migrar si la hipótesis falla. |

### Criterios contextuales (cartografía)

| Criterio | Peso | Justificación |
|----------|------|---------------|
| Rendimiento geográfico | 8 | Gama media (TCL T610P), navegación activa. |
| Escalabilidad regional | 7 | NaveGo puede pasar de 1 a 50 regiones. |
| Tamaño de dataset | 6 | Importante pero medible después. |

### Notas sobre pesos

- Los pesos fueron fijados ANTES de puntuar las alternativas.
- Cualquier cambio posterior debe documentarse aquí.
- El análisis de sensibilidad evaluará si el orden es estable
  ante variaciones plausibles.

## Etapa 3: PUNTUACIÓN

PENDIENTE
Cada puntuación debe declarar:
- valor (1-5)
- evidencia (MEDIDA / ESTIMADA / OPINIÓN)
- confianza (ALTA / MEDIA / BAJA)
- fuente (referencia)

## Etapa 4: SENSIBILIDAD

PENDIENTE

## Etapa 5: INFORME DE DISENSO

PENDIENTE

## Etapa 6: DECISIÓN HUMANA

PENDIENTE
