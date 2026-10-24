# P51 — EVALUACIÓN DE HARNESS² PARA TIMONEL

**Fecha:** 2026-10-24
**Estado:** PENDIENTE (Investigación)
**Contexto:** A partir del análisis del paper *Harness²: Recursive Agent Harnessing for an Open World* (google-research), se propone evaluar si su enfoque puede reducir el trabajo manual en Timonel.

## Objetivo
Evaluar si el enfoque Harness² permite reducir el trabajo manual repetitivo de Timonel mediante propuestas, pruebas comparativas y reutilización de lecciones verificadas, sin reentrenar el modelo base ni debilitar los controles de LOGOS.

## Alcance Inicial (Solo Investigación)
- Revisar la fuente primaria y contrastar sus mecanismos con la arquitectura real de Timonel.
- Diseñar un experimento offline sobre registros históricos o simulador, con una referencia fija y candidatos aislados (Propose-Probe-Compose).
- Evaluar scripts y skills mediante pruebas reproducibles, límites de recursos y evidencia trazable.
- Definir una biblioteca de experiencias versionada (`experience.md`), con procedencia, resultados, confianza y criterios de aceptación.
- Documentar las barreras entre propuestas generadas por IA, selección automática dentro de límites autorizados y aprobación humana.

## Exclusiones Explícitas
- No modificar automáticamente el Policy Engine ni los guardrails críticos.
- No adaptar filtros en navegación real sin validación.
- No ejecutar código candidato con acceso irrestricto.
- No modificar la biblioteca aprobada sin control de cambios.
- No desplegar mejoras en producción ni alterar el modelo base.

## Criterio de Salida
Un diseño evaluado con evidencia, sus limitaciones y un plan de pruebas. La implementación y cualquier cambio de autoridad o seguridad requieren una decisión explícita posterior del Director.
