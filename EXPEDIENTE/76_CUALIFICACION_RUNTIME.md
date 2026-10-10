# CUALIFICACION DEL RUNTIME — Protocolo

**Fecha:** 2026-10-10
**Autor:** Directora de Investigacion
**Estado:** CONGELADO. Base para implementar el test.
**Complementa:** memos 65, 73 y 75.

---

## 0. Proposito

Antes de correr el benchmark contra el banco CC002, cualificar el runtime de Ollama:

1. Confirmar que el carry-over reportado en memo 65 sigue presente.
2. Medir la magnitud con las senales que expone Ollama 0.34.0.
3. Definir la politica operativa para el benchmark.

---

## 1. SENALES DISPONIBLES (verificado 2026-10-10)

Ollama /api/generate expone:
- total_duration
- load_duration
- prompt_eval_count
- prompt_eval_cached_count (clave para carry-over)
- prompt_eval_duration
- eval_count
- eval_duration
- context (array de tokens de la KV cache)

NO expone logprobs por default. Se puede pedir con logprobs=true, top_logprobs=N.

---

## 2. DEFINICIONES

**S* (sentinel):** contexto fijo, siempre el mismo input. Se usa para detectar cambios de regimen.

**Predecesor:** prompt ejecutado inmediatamente antes de S*.

**Cache hit:** prompt_eval_cached_count > 0.

**Respuesta estable:** mismo par (accion, parametro) en todas las corridas.

---

## 3. DISENO DEL TEST

### Test A — Repetibilidad pura de S*
- Correr S* 5 veces seguidas, sin predecesores.
- Medir: variacion de respuesta, cache hits, tiempos.
- Esperado: identico.

### Test B — Sensibilidad al predecesor
- Predecesores: prompt neutral, prompt de dominio A, prompt de dominio B, prompt largo.
- Correr S* despues de cada uno, 3 veces por predecesor.
- Medir: variacion de la respuesta de S*.

### Test C — ollama stop entre casos
- Repetir Test B, insertando ollama stop entre cada corrida.
- Medir: variacion y cache hits.

### Test D — Regimen a lo largo del tiempo
- 20 corridas de S* con ollama stop + recarga, espaciadas.
- Medir: cambios de regimen (accion o parametro distinto).

---

## 4. CRITERIOS

- **Carry-over confirmado:** S* cambia de respuesta segun predecesor (Test B).
- **ollama stop eficaz:** Test C da respuesta estable.
- **Regimen estable:** Test D da 20/20 identicas.
- **Cache hit 0 tras stop:** prompt_eval_cached_count = 0 en la primera corrida tras stop.

---

## 5. POLITICA OPERATIVA RESULTANTE

Segun resultados:

**Si ollama stop elimina carry-over:**
- Benchmark usa ollama stop entre contextos.
- Costo: ~1-2s por contexto (carga del modelo).
- 600 contextos x 3 condiciones = 1800 stops = ~30-60 min extra.

**Si ollama stop NO elimina carry-over:**
- Benchmark usa orden aleatorio y registra predecesor como variable.
- Analisis estratificado por predecesor.

---

## 6. LO QUE NO SE HACE

- No se modifica retrieval, prompt, banco ni memoria.
- No se cambia el modelo.
- No se corren benchmarks de decision todavia.
- No se optimiza nada antes de tener resultados.

---

## 7. IMPLEMENTACION

Archivo a crear: timonel/cualificar_runtime.py.
Salida: JSON con resultados de los 4 tests.

Despues del memo 76: si Test A-D pasan, commit del protocolo.

---

## 8. FIRMA

**Estado:** CONGELADO.
**Proximo paso:** implementar cualificar_runtime.py.
**Regla:** sin este memo commiteado, no se corre el benchmark CC002.
