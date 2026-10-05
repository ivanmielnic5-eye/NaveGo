# ESTADO DE SESION — 2026-10-05

**Proyecto:** Timonel (agente LLM local sobre Polaris)
**Autor:** Directora de Investigacion
**Tipo de documento:** estado de sesion. NO es memo de diseno.
**Uso:** arranque de proximo hilo. Resumen del dia y mapa de archivos.

---

## 0. Proposito

Los memos 62, 63, 64 y 65 son documentos de diseno, densos tecnicamente. Este memo 66 es el estado de la sesion: que se hizo, que se aprendio, que quedo abierto, donde esta cada cosa. Sirve para que un hilo nuevo entienda el panorama sin leer los cuatro anteriores completos.

---

## 1. Que se hizo hoy

### Etapa previa (durante la manana y primera tarde)

- Validacion del oraculo multi-horizonte (Oracle Validation 001): PASS 3/3 criterios.
- Oracle-Pure Pilot: 100/100 misiones completas llegando a meta.
- Construccion del banco COMMON_CONTEXT-001 con 350 contextos congelados.
- Purgado por leakage: se detectaron 8 casos con contaminacion de memoria, se removieron. El banco quedo con 350 snapshots utiles.
- Deteccion de defecto de retrieval (misaligned experience replay): las experiencias con exito=False contaminaban las decisiones de B. Fix aplicado (solo_exitos=True).
- Deteccion de no-determinismo de Ollama (temperatura=0, seed=555). Investigacion con DSH. Hallazgo: gfx1103 sin kernels Tensile para ROCm 7.2 en Radeon 760M.
- Se probaron variaciones: num_batch explicito, Flash Attention off, CPU-only. Ninguna elimino el cambio de regimen.
- Determinism Gate 001: PASS (15/15 combinaciones reproducibles dentro de un bloque de 20 ciclos).

### Benchmark causal (la parte mas importante del dia)

- Se corrieron dos benchmarks de N=100 contextos cada uno.
- Primer benchmark (contextos 0-99): A = corregir_rumbo en 100/100. B intervino en 13/100. Cuando intervino: 11 mejoras de regret, 1 empeoramiento, 1 sin cambio. IC 95% bootstrap: [1.76, 7.03].
- Segundo benchmark held-out (contextos 100-199): A cambio de regimen a mitad de corrida. B interfirio negativamente en contextos donde A ya estaba bien.
- El cambio de signo entre benchmarks invalida la estimacion causal global.

### Experimentos de carry-over (ultima parte del dia)
- RUNTIME-CARRYOVER-001: Tests 1 a 5 corrieron completos. Resultado: sin carry-over detectable (S* invariante frente a cualquier prompt previo).
- Test 6 (6 permutaciones): fallo por bug de infraestructura, no por carry-over.

---

## 2. Que quedo abierto

### Problema 1 — Bug de Ollama con format:json (BLOQUEANTE)

Durante el Test 6, Ollama devolvio 5 de 6 respuestas vacias con el error:

got exception: Unexpected empty grammar stack after accepting piece: ? (30)

Causa: el grammar (GBNF) que Ollama usa para forzar JSON valido tiene un bug con ciertas secuencias de tokens. La llamada devuelve HTTP 200 pero con contenido vacio.

Impacto: cualquier benchmark que dependa de format=json puede fallar silenciosamente.

Fix pendiente: probar sin format=json y parsear manualmente con regex. O buscar workaround en la configuracion.

### Problema 2 — Cambio de regimen de inferencia (NO RESUELTO)

Ollama puede pasar de un regimen estable (A = corregir_rumbo) a otro (A = ir_a_punto) entre bloques de ejecucion. No sabemos que lo dispara. No es carry-over. No es num_batch. No es Flash Attention. No es backend (CPU y GPU dan lo mismo).

Hipotesis viva: seleccion de kernel dependiente de estado en hipBLASLt/ROCm, cacheada por proceso. Pero NO confirmada.

### Problema 3 — Signo ambiguo de la memoria

El primer benchmark mostro que B mejora. El held-out mostro que B perjudica cuando A ya esta bien. El signo del efecto depende del regimen de A, que no controlamos.

Conclusion provisoria: no hay evidencia de un efecto global de memoria. Hay evidencia de una INTERACCION entre memoria y regimen del agente base.

---

## 3. Archivos clave del dia

### Memos
- EXPEDIENTE/60_DISENO_EXPERIMENTAL_MEMORIA.md — diseno original (superseded en parte).
- EXPEDIENTE/61_REVISION_DISENO_EXPERIMENTAL.md — revision 1 (regret vs accuracy).
- EXPEDIENTE/62_REVISION_2_DISENO_EXPERIMENTAL.md — revision 2 (COMMON-CONTEXT).
- EXPEDIENTE/63_DEFECTO_RETRIEVAL_MEMORIA.md — defecto de retrieval + seccion 8 regimen estable.
- EXPEDIENTE/64_CAMBIO_REGIMEN_DURANTE_BENCHMARK.md — hallazgo + 2 enmiendas.
- EXPEDIENTE/65_RUNTIME_CARRYOVER_PROTOCOLO.md — protocolo del carry-over.
- EXPEDIENTE/66_ESTADO_SESION_2026-10-05.md — este documento.

### Informes de DSH
- EXPEDIENTE/INVESTIGACION_NO_DETERMINISMO_OLLAMA_ROCM_760M.md
- EXPEDIENTE/INVESTIGACION_LLAMACPP_ROCM_NONDETERMINISMO.md
- EXPEDIENTE/ROCm_NONDETERMINISM_REPORT.md

### Codigo
- timonel/simulador_polaris.py — fisica del barco (viento, prop walk, prop wash).
- timonel/recetas_navegacion.py — recetas de maniobras.
- timonel/oraculo.py — oraculo multi-horizonte.
- timonel/oracle_pure_pilot.py — controlador puro con oraculo.
- timonel/memoria.py — SQLite con retrieval y filtro de consenso.
- timonel/agente_llm.py — Qwen via Ollama (num_batch=512, temp=0, seed=555).
- timonel/timonel_python.py — agente multi-meta.
- timonel/benchmark_decisions.py — benchmark local (--offset para held-out).
- timonel/runtime_carryover.py — Tests 1-5 carry-over.
- timonel/test6.py — Test 6 (fallo por bug de Ollama).

### Datos
- timonel/COMMON_CONTEXT_001.json — 350 contextos congelados.
- timonel/MEMORY_DEFECT_001.json — evidencia del defecto de retrieval.
- /tmp/bench_100.json — resultado benchmark regimen B.
- /tmp/bench_100_heldout.json — resultado benchmark held-out (regimen mixto).
---

## 4. Proximo paso inmediato

**Antes de cualquier otro benchmark:**

1. Arreglar el bug de format=json en agente_llm.py. Probablemente sacar format=json y parsear manualmente. Sin esto, cualquier benchmark puede fallar silenciosamente.

2. Volver a correr el Test 6 con el fix aplicado. Con reintentos y verificacion de que cada respuesta sea parseable.

3. Recien despues, decidir si seguir investigando el cambio de regimen o reformular el benchmark con lo que ya sabemos.

---

## 5. Lo que NO hay que hacer

- No correr mas benchmarks hasta arreglar el bug de format=json.
- No reformular el diseno experimental hasta cerrar Test 6.
- No descartar los resultados del dia. Son validos como evidencia exploratoria. El bench_100.json y bench_100_heldout.json son datos reales que muestran la interaccion memoria x regimen.
- No borrar los .pre-* backups.

---

## 6. Estado del repo al cierre

- Rama: experimento-v4-admin
- Ultimo commit: cff0647 (memos 64 y 65).
- Working tree: limpio despues del commit de este memo.
- Todo pusheado a origin.

---

## 7. Diagnostico honesto de la sesion

**Lo positivo:**
- Se valido el oraculo. Se construyo el banco. Se detectaron tres problemas reales (retrieval, no-determinismo, bug de format=json).
- El primer benchmark mostro un resultado solido en regimen B (IC 95% no incluye cero).
- Se descarto carry-over como explicacion del cambio de regimen con tests 1-5 completos.
- Cada hallazgo quedo documentado en un memo con evidencia.

**Lo negativo:**
- No pudimos estimar el efecto causal global de memoria porque el agente base no es estable.
- El Test 6 no se pudo cerrar por bug de infraestructura.
- Quedaron preguntas abiertas sobre la causa del cambio de regimen.

**Lo que NO cambia:**
- La memoria no es buena ni mala. Interactua con el regimen del agente base. Eso ya es un hallazgo util.
- El oraculo funciona. El banco sirve. Las herramientas estan.
- El proximo hilo tiene todo lo necesario para continuar desde aca.

---

*Documento de estado de sesion.*
*Fecha: 2026-10-05.*
*Registrado en EXPEDIENTE/66.*
