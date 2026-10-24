# 102 — ARQUITECTURA DEL COPILOTO LINGÜÍSTICO Y POLARIS (FASE DE DISEÑO)

**Fecha:** 2026-10-23
**Estado:** CONGELADO COMO RUTA DE TRABAJO PRIORITARIA v0.1.
**Contexto:** Tras el incidente de inestabilidad de la GPU (amdgpu) durante inferencias intensivas, se establece que la Fase 1 del Copiloto se centrará en diseño offline y validación determinista. El congelamiento del marco NO implica la aprobación de las implementaciones técnicas pendientes.

## 1. Principios Arquitectónicos Fijados
1. **Soberanía operativa:** Núcleo funcional offline-first.
2. **Separación intención/actuación:** El LLM interpreta y propone un `Intent`; NO gobierna timón ni actuadores.
3. **Contratos tipados:** `Intent`, `MisionConfig` y `EffectiveMissionConfig` son distintos y trazables.
4. **Validación determinista:** Los límites no se relajan por el LLM. Valores ausentes/ambiguos se rechazan (Fail-Closed).
5. **Separación de políticas:** Validación de misión náutica, envolvente de seguridad, controlador y adaptador no se mezclan.
6. **Control basado en estado:** Un destino no es un pulso de timón. El controlador decide las maniobras.
7. **Telemetría de retorno:** El simulador informa lo ocurrido para evaluar la propuesta del copiloto.
8. **Comandos acotados:** Expiración, épocas y TTL de órdenes deben definirse.
9. **Modelos intercambiables:** PaLM/SayCan son antecedentes. Los modelos se eligen por resultados medidos.
10. **Evidencia antes de integración:** Corpus, pruebas y decisiones expresas antes de ejecutar.

## 2. Ruta Prioritaria de Trabajo
- **P0 — Preservar:** Registrar esta arquitectura (hecho).
- **P1 — Auditoría estática:** Inspeccionar contratos existentes (`mision_config.py`, `action_schema.json`, `polaris_bridge.py`, `timonel_bridge.gd`) en modo lectura. Confirmar hashes y responsabilidades.
- **P2 — Diseñar interfaces:** Documentar fronteras entre `Intent`, config autorizada, telemetría, controlador y comando.
- **P3 — Evaluación offline:** Diseñar corpus de casos (completos, ambiguos, contradictorios, fuera de límites). Pruebas de esquema y rechazo seguro.
- **P4 — Comparar modelos:** (Solo con autorización y máquina estable) Evaluar docentes/locales por resultados, no por prestigio.
- **P5 — Validar simulación:** Integración controlada con Godot solo tras acordar interfaces y criterios.

## 3. Restricciones Operativas Vigentes
- NO ejecutar Ollama/GPU hasta resolver incidente de estabilidad.
- NO ejecutar Godot ni escribir en `comandos.jsonl` real en esta etapa.
- NO implementar adaptadores con correspondencias inventadas.
- NO ampliar el contrato A4 con `requested_constraints` sin revisión.
- NO confundir el puente Godot con el Bridge MCP original.
- NO alterar evidencias históricas.

## 4. Decisiones Pendientes de Autorización
- Modelo docente/local definitivo.
- Ampliaciones del esquema `Intent`.
- Formato final de órdenes (TTL, épocas).
- Reglas dinámicas de seguridad.
- Algoritmo del controlador de navegación.
- Interfaces del adaptador.
- Corpus, umbrales y criterios de homologación.
- Autorización de ejecución en Godot.

*El silencio del Director no constituye aprobación de ninguna de estas decisiones.*

---

## 7. Visión a Futuro: Passthrough y Gemelos Digitales (Digital Twins)

**Registrado el:** 2026-10-24
**Contexto:** A partir del análisis de arquitecturas de videojuegos y robótica moderna (como el concepto de "Passthrough" y proyectos como SayCan), se consolida la visión a largo plazo del ecosistema.

### El concepto de "Passthrough" (Frontera de Proceso)
El sistema no debe ser un monolito. Godot (Polaris) y Python (Policy Engine + Timonel) deben vivir en procesos separados. 
- **La Frontera:** El Sandbox (Bubblewrap) garantiza que no compartan memoria ni puedan romperse mutuamente.
- **El Puente:** Se comunican a través de eventos estructurados (`comandos.jsonl` y `telemetria.jsonl`). Una "explosión" (evento/orden) en un lado afecta al otro de forma controlada y determinista.

### Gemelo Digital (Digital Twin) Bidireccional
El simulador (Polaris) es un laboratorio de *Ground Truth* perfecto. Habilita dos flujos:
1. **Sim2Real:** Usar la telemetría perfecta de Godot para entrenar al copiloto LLM antes de ir al barco real.
2. **Real2Sim:** Inyectar datos de viajes reales en el simulador para que el agente aprenda de imperfecciones en un entorno seguro.

### Conclusión
El objetivo final es un **Gemelo Digital** que permita a la IA cometer errores en la jaula de cristal antes de operar en el barco real.
