# RUNTIME-CARRYOVER-001 — Protocolo de investigacion

**Proyecto:** Timonel (agente LLM local sobre Polaris)
**Autor:** Directora de Investigacion
**Estado:** protocolo cerrado. Pendiente de ejecucion.
**Origen:** enmienda al memo 64 (seccion 11).

---

## 0. Por que este experimento

El benchmark causal del memo 62 ejecuta A, A_prima y B en orden fijo dentro de cada contexto. Si el runtime de Ollama tiene estado interno que depende del prompt inmediatamente anterior, B no se evalua bajo las mismas condiciones que A o A_prima. Eso introduce un confusor entre tratamiento (memoria) y posicion (orden en la secuencia).

Antes de rehacer el benchmark hay que determinar si el runtime tiene carry-over entre prompts consecutivos.

**Hipotesis H-CARRY-1:** la salida de un contexto fijo S* depende de los prompts ejecutados inmediatamente antes.
**Hipotesis alternativa H-CARRY-0:** la salida de S* es independiente del prompt previo.

**Criterio de falsacion:** si para todas las precondiciones probadas la salida de S* es identica, H-CARRY-1 se refuta.

---

## 1. Definiciones operativas

**S* (contexto sentinela):** contexto fijo, siempre el mismo input. Definido en seccion 2.

**Precondicion:** secuencia de prompts ejecutados inmediatamente antes de S*.

**Cache tokens:** cantidad de tokens en cache de prompt antes de cada llamada. Se obtiene del log de Ollama o de la respuesta de la API.

**Prompt hash:** SHA256 del prompt enviado a Ollama, para verificar identidad byte a byte.

**Cache prompt flag:** valor de cache_prompt en cada llamada (true o false).

---

## 2. Contexto sentinela S*

S* debe ser:
- Fijo: siempre el mismo estado inicial.
- Simple: no depende de contexto del banco.
- Con decision no ambigua en regimen estable conocido.

**Propuesta:** contexto 1 del banco COMMON_CONTEXT_001.json (indice 1).

Razon: ya tenemos evidencia de que puede dar corregir_rumbo|59.3 en regimen B y valores distintos en regimen A. Es un buen indicador de regimen.

**Fallback:** si el contexto 1 resulta ambiguo, usar un contexto artificial con estado trivial (barco en 0,0 mirando al norte, meta a 100m al este).

---

## 3. Los tests

Seis tests, cada uno responde una pregunta distinta.

### Test 1 — Repeticion pura

Secuencia: S* S* S* S* S* (5 veces).

Pregunta: la salida de S* es estable cuando no hay prompts intermedios?

### Test 2 — Prompt neutral entre medio

Secuencia: S* N S* N S* N S* (donde N es un prompt generico sin relacion con el dominio, como responde solo hola).

Pregunta: un prompt cualquiera intermedio altera la salida de S*?

### Test 3 — Precedencia A

Secuencia: A_like S* A_like S* A_like S* (donde A_like es el prompt de la condicion A sobre un contexto distinto al de S*).

Pregunta: ejecutar A antes de S* altera la salida de S*?

### Test 4 — Precedencia A_prima

Secuencia: A_prima_like S* A_prima_like S* ...

Pregunta: ejecutar A_prima antes de S* altera la salida de S*?

### Test 5 — Precedencia B

Secuencia: B_like S* B_like S* ...

Pregunta: ejecutar B antes de S* altera la salida de S*?

### Test 6 — Las seis permutaciones

Para cada contexto del banco (por ejemplo los primeros 20), ejecutar las seis permutaciones de A, A_prima, B:

Permutacion 1: A -> A_prima -> B
Permutacion 2: A -> B -> A_prima
Permutacion 3: A_prima -> A -> B
Permutacion 4: A_prima -> B -> A
Permutacion 5: B -> A -> A_prima
Permutacion 6: B -> A_prima -> A

Pregunta: la decision de B depende de su posicion en la secuencia?

---

## 4. Variables a registrar por cada llamada

- prompt_hash (SHA256 del prompt enviado)
- previous_prompt_hash (SHA256 del prompt inmediatamente anterior)
- decision (accion + parametro)
- cache_prompt_flag (true o false)
- cache_tokens (si disponible en la respuesta o el log)
- load_duration
- prompt_eval_duration
- eval_duration
- total_duration
- timestamp

---

## 5. Criterio de interpretacion

**Si S* da siempre el mismo resultado en los seis tests:**
- H-CARRY-0 confirmada.
- El runtime NO tiene carry-over detectable.
- El benchmark causal puede usar orden aleatorio y el carry-over queda descartado como confusor.

**Si S* cambia segun el prompt anterior:**
- H-CARRY-1 confirmada.
- El runtime SI tiene carry-over.
- El benchmark causal esta contaminado por orden.
- Hay que redisenar el benchmark con randomizacion de orden por contexto.

**Si S* cambia solo en algunos tests:**
- Carry-over condicionado a alguna caracteristica especifica del prompt previo (longitud, contenido, cache status).
- Hay que investigar esa caracteristica.
---

## 6. Orden de ejecucion

**Paso 1:** Tests 1 y 2 (repeticion pura y prompt neutral).
Razon: los mas simples. Si ya fallan, no hace falta seguir.

**Paso 2:** Tests 3, 4 y 5 (precedencia por condicion).
Razon: determinan si el prompt anterior especifico importa.

**Paso 3:** Test 6 (las seis permutaciones).
Razon: el mas informativo pero el mas costoso.

Cada paso solo se ejecuta si el anterior no revelo un confusor bloqueante.

---

## 7. Lo que NO se hace

NO se toca retrieval, prompt, memoria ni backend hasta tener los resultados.

NO se reformula el benchmark causal todavia.

NO se descartan los datos actuales. El bench_100.json y bench_100_heldout.json se conservan como evidencia exploratoria.

---

## 8. Cierre

**Lo que se afirma:**

El benchmark causal del memo 62 esta potencialmente contaminado por un confusor entre tratamiento (memoria) y posicion en la secuencia (orden A -> A_prima -> B). Si el runtime de Ollama tiene carry-over entre prompts consecutivos, la comparacion B - A_prima no aísla el efecto de la memoria.

**Lo que se necesita:**

Determinar experimentalmente si S* cambia segun el prompt anterior antes de reformular el benchmark.

**Proximo paso:**

Implementar runtime_carryover.py con los seis tests. Ejecutar Test 1 y Test 2 primero. Reportar resultados antes de seguir.

---

*Documento cerrado. Se puede proceder a implementar runtime_carryover.py.*
*Fecha: 2026-10-05.*
*Registrado en EXPEDIENTE/65.*
