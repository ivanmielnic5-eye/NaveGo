# BORRADOR — BIBLIOGRAFÍA DE VERIFICACIÓN DE AGENTES LLM

**Fecha:** 2026-10-15
**Estado:** BORRADOR. Fuera del expediente.
**Origen:** sugerencias de Notebook, auditadas por Luna (2026-10-15).
**Nota:** esta bibliografía NO es la que aplica al benchmark de controladores marinos. Es una línea paralela sobre verificación de seguridad de agentes LLM.

---

## 1. AgentVerify — verificación con lógica temporal

**Tipo:** Preprint no revisado por pares.
**URL:** https://www.preprints.org/manuscript/202604.1029
**Resultado informado:** 86.67% precisión de verificación post-hoc sobre 15 escenarios sintéticos. Verificador neuronal monolítico: 13.33%. Detección del 100% de fallos catastróficos en su benchmark con analizador posterior.
**Limitación declarada:** el mismo trabajo reporta resultados débiles para su variante de monitorización híbrida en tiempo de ejecución.
**Corrección de Luna:** NO significa que cualquier sistema basado en LTL garantice seguridad. Son resultados de una configuración específica.
**Aplicación potencial a NAVEGO:** definir invariantes sobre la secuencia de eventos de Timonel y comprobarlos durante y después de la misión.

## 2. MAGS — especificaciones formales con Dafny

**Tipo:** Preprint (arXiv, septiembre 2026).
**URL:** https://arxiv.org/abs/2609.19391
**Resultado informado:** certificados verificados para 220 ejemplos: 100 CUDA, 100 terminal, 20 robótica. Evaluación de seguridad independiente: 82/100 en terminal, 100/100 en CUDA, 20/20 en robótica.
**Corrección de Luna:** el 18% de discrepancia se refiere al subconjunto de terminal, no al conjunto. La distinción clave: satisfacer una especificación formal NO demuestra que la especificación cubra todos los riesgos del mundo real.
**Aplicación potencial a NAVEGO:** definir restricciones de seguridad independientes del LLM, congelarlas antes de evaluar, comprobarlas contra la ejecución real.

## 3. Constraint Drift — conservación de las restricciones

**Tipo:** Propuesta de investigación con estudio de caso (arXiv).
**URL:** https://arxiv.org/abs/2605.10481
**Idea:** Constraint State Governance (CSG): mantener restricciones de seguridad como estado explícito y auditable, en vez de depender de que sigan presentes en el prompt o contexto.
**Corrección de Luna:** no constituye demostración de que CSG resuelva la deriva en navegación marítima. Es pertinente para controladores que atraviesan múltiples decisiones.
**Aplicación potencial a NAVEGO:** registrar el estado vigente de las restricciones, validar cada acción contra ese estado, dejar evidencia de todo veto o modificación.

## 4. Toward Safe LLM Agents — revisión de especificación, verificación y aplicación

**Tipo:** Survey (preprint, arXiv). Coautores de la Universidad de Manchester.
**URL:** https://arxiv.org/abs/2608.14590
**Contenido:** resume problemas de traducción del lenguaje natural a especificaciones formales. Introduce el "Verifier Tax": bloquear acciones inseguras no asegura que el agente pueda terminar la tarea con seguridad.
**Corrección de Luna:** los porcentajes citados (24-35% para ciertos resultados de traducción semántica y <5% de éxito seguro) NO son tasas universales. El propio survey declara heterogeneidad entre estudios, ausencia de metaanálisis y certeza baja o muy baja.
**Aplicación potencial a NAVEGO:** medir dos resultados por separado — cuántas acciones inseguras se bloquean y cuántas misiones terminan con seguridad.

---

## Matriz de transferencia metodológica

| Propuesta | Dictamen de Luna |
|---|---|
| Restricciones de seguridad independientes del LLM | Adoptar como principio de diseño. Verificar implementaciones actuales antes de actuar. |
| Lógica temporal y verificación de secuencias | Evaluar cuando exista contrato de eventos y propiedades a cumplir. |
| Estado explícito y auditable de restricciones | Investigar como mecanismo para el Entrenador y roles de ejecución. NO implementar CSG automáticamente. |
| Métricas estadísticas robustas (IQM, intervalos de confianza) | Incorporar al benchmark cuando existan ejecuciones comparables. No reemplazan la calidad de los datos. |
| `navego_gym_env.py` y `test_suite_timonel.py` | NO asumir que existen. Verificar rutas reales. |
| "Inercia al ejecutar TERMINAR" | Verificar primero qué significa en cada entorno. No trasladar semántica del benchmark Python a Godot. |

---

## Las tres capas que deben mantenerse separadas

1. **Especificación** de seguridad (declarado).
2. **Aplicación** efectiva de las restricciones.
3. **Evaluación** independiente del resultado.

Tener una no garantiza las otras.

---

## Advertencia

Esta bibliografía NO debe mezclarse con la de evaluación de simulador marino (`bibliografia_evaluacion_simulador.md`). Son líneas paralelas:
- **Marina**: cómo evaluar el controlador y comparar variantes.
- **Verificación LLM**: cómo garantizar que el LLM no se salga de las restricciones.
