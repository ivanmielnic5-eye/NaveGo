# BORRADOR — BIBLIOGRAFÍA DE EVALUACIÓN DE SIMULADOR

**Fecha:** 2026-10-15
**Estado:** BORRADOR. Fuera del expediente.
**Origen:** recomendaciones de Notebook + auditoría de Luna 2026-10-15.
**Nota:** este documento NO debe mezclarse con `bibliografia_verificacion_llm_2026-10-15.md`. Son dos líneas paralelas (evaluación de navegación vs seguridad del controlador LLM).

---

## Línea B — Evaluación de navegación

Pregunta guía: ¿la navegación mejora realmente en tiempo, estabilidad y eficiencia, mantiene la seguridad y cumple las reglas en escenarios comparables?

### B1. Agarwal et al. (2021) — Estadística robusta

**Título:** Deep Reinforcement Learning at the Edge of the Statistical Precipice.
**Publicación:** NeurIPS 2021.
**URL:** https://papers.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html
**Herramienta:** https://agarwl.github.io/rliable/

**Métricas propuestas:**
- **IQM (media intercuartil):** descarta 25% de extremos inferiores y 25% de extremos superiores; calcula la media del 50% central.
- **Intervalos de confianza por bootstrap estratificado:** cuantifica incertidumbre sin necesidad de cientos de corridas.
- **Perfiles de desempeño:** curvas acumulativas de resultados frente a distintos umbrales.

**Advertencia de Luna:** `rliable` NO convierte datos incomparables en evidencia fiable. Requiere primero tener un resultado por ejecución (éxito, tiempo, distancia, sobrepaso, estabilidad, fallos).

**Aplicación a NAVEGO:** cuando existan ejecuciones comparables, usar IQM + bootstrap para comparar Python puro vs LLM vs híbrido. NO instalar la librería todavía.

**Estado:** verificado (referencia + método conocidos).

### B2. Zhou et al. (2024) — Indicadores náuticos

**Título:** Indicator designing for performance evaluation of collision avoidance algorithms programs on autonomous ships.
**Publicación:** Ocean Engineering 2024.
**DOI:** https://doi.org/10.1016/j.oceaneng.2024.116810

**Datos verificables (según Luna):** 13 indicadores, 648 casos experimentales, 4 tipos de entorno cartográfico, 5 modelos de barco.

**Afirmaciones NO verificadas** (aparecen en resumen de Notebook pero requieren texto completo):
- Que el paper use específicamente el índice "CRI" (Collision Risk Index).
- Que los indicadores se basen en TCPA/DCPA de una forma concreta.
- Que incluya "suavidad del timón" y "consumo energético" como indicadores definidos.

**Aplicación a NAVEGO:** base para el compilador de seguridad en la Fase 3 (colisiones). No citar los términos CRI/TCPA/DCPA como "del paper" hasta verificar el texto completo.

**Estado:** referencia confirmada. Contenido específico pendiente de verificación.

### B3. Woerner et al. (2018/2019) — Verificación COLREGS

**Título:** Quantifying Protocol Evaluation for Autonomous Collision Avoidance.
**Publicación:** Autonomous Robots, vol. 43 (2019); online 2018.
**URL:** https://dspace.mit.edu/entities/publication/2d20e709-4446-430a-90c9-6c64690f176c

**Contribución:** criterios de entrada y salida para situaciones COLREGS (frente a frente, cruce, adelantamiento). Herramientas para evaluar durante y después de la misión.

**Aplicación a NAVEGO:** convertir "maniobra segura" en criterio verificable. Base para cuando haya obstáculos e interacciones con otras embarcaciones.

**Advertencia:** NO demuestra que el simulador actual tenga obstáculos ni que cumpla COLREGS. Eso requiere instrumentación propia.

**Estado:** verificado (referencia + contribución principal).

---

## Puerta de entrada (Nguyen et al. 2025)

**Título:** Simulation Framework for Addressing Challenges in Path Planning Evaluation for an Autonomous Surface Vehicle.
**Publicación:** Journal of Marine Science and Application, 2025.
**URL:** https://html.rhhz.net/jmsa/html/20250411.htm

**Contribución esperada:** evaluar planificación de rutas para vehículos de superficie; advierte que la longitud de ruta por sí sola omite dinámica, perturbaciones y localización.

**Estado:** NO VERIFICADO. Notebook falló dos veces en leer este link: la primera lo trató como índice de enlaces, la segunda no lo mencionó. Requiere lectura directa antes de citarlo formalmente.

---

## Referencia pendiente de verificar

**PERFORM:** A Metric for Evaluating Autonomous System Performance in Marine Testbed Environments Using Interval Type-2 Fuzzy Logic.
**Estado:** NO VERIFICADA. Sin URL confiable. Si se sostiene que existe, buscar referencia canónica antes de citarla.

---

## Recursos técnicos (no son papers)

- **Open Robotics** — Discusión sobre métricas de navegación (distinguir rendimiento computacional de funcional).
  https://discourse.openrobotics.org/t/nav2-discussion-metrics-framework-for-quantitative-evaluation-of-navigation-performance/28082
- **Gazebo / Stack Exchange** — Ground truth en simuladores (registro desde dentro vs fuera).
  https://robotics.stackexchange.com/questions/29244/what-is-the-best-way-to-record-ground-truth-data-during-a-simulation
- **MCAP** — Formato de registro indexable (tecnología, no paper).
  https://mcap.dev/guides/getting-started/ros-2

---

## Reglas para usar esta bibliografía

1. **No mezclar Línea A y Línea B.** Preguntas distintas, métricas distintas.
2. **No citar como "del paper X" nada que no esté verificado contra el texto completo.**
3. **No instalar librerías** (rliable u otras) antes de tener el contrato de datos y ejecuciones comparables.
4. **Aplicar IQM/bootstrap** solo cuando existan ejecuciones comparables en las mismas condiciones.
5. **Los indicadores náuticos (COLREGS, DCPA, TCPA, CRI)** aplican a Fase 3, no antes.
