# CAMBIO DE REGIMEN DE INFERENCIA DURANTE EL BENCHMARK

**Proyecto:** Timonel (agente LLM local sobre Polaris)
**Autor:** Directora de Investigacion
**Estado:** benchmark causal NO INTERPRETABLE todavia. Se requiere revision metodologica.
**Origen:** ejecucion del benchmark de memoria (memo 62) con dos corridas de N=100.

---

## 0. Por que este memo

El memo 62 definio el benchmark causal: A (estado solo), A_prima (estado + historial), B (estado + historial + memoria) sobre contextos congelados.

El memo 63 documento un defecto de retrieval (misaligned experience replay).

Este memo documenta un problema mas profundo, descubierto al correr el benchmark: el REGIMEN DE INFERENCIA del agente base cambio durante la ejecucion del benchmark. Eso invalida el benchmark como estimacion causal de efecto de memoria.

**Regla metodologica:** este memo NO afirma que la memoria sea buena ni mala. Registra que el benchmark actual no permite afirmarlo todavia.

---

## 1. Los cuatro hechos

1. El benchmark no mantuvo un regimen de inferencia estable.
2. La politica de A cambio durante la evaluacion.
3. El signo del efecto (B - A) cambio segun el regimen.
4. Por tanto, el benchmark no permite todavia estimar un efecto global de memoria.

---

## 2. Evidencia del cambio de regimen

Se corrieron dos benchmarks de N=100 contextos cada uno sobre el mismo banco (COMMON_CONTEXT_001.json, 350 contextos).

### Benchmark 1 (contextos 0-99)

- A = corregir_rumbo en 100/100 contextos. Regimen B estable.
- B intervino en 13/100 contextos.
- Cuando intervino: 11 mejoras, 1 empeoramiento, 1 sin cambio.
- Regret medio A: 23.36m. Regret medio B: 19.20m.
- Diferencia media: 4.16m a favor de B.
- IC 95% bootstrap pareado: [1.76, 7.03]. No incluye cero.
- McNemar: B mejor 11, A mejor 1, empates 88.

### Benchmark 2 (contextos 100-199, held-out)

- A = corregir_rumbo en contextos 0-16 del held-out. Regimen B.
- Contexto 16: A = ? (transicion).
- A = ir_a_punto desde contexto 17 en adelante. Regimen A.
- El regimen cambio DENTRO del benchmark, no entre benchmarks.
- Con regimen A, muchos A ya tenian regret 0.0 (A elegia bien).
- B interfirio en multiples contextos donde A estaba bien:
  - ctx 53 (held-out): A=0.0 -> B=53.16
  - ctx 55 (held-out): A=0.0 -> B=75.29
  - ctx 56-58 (held-out): A=0.0 -> B=95.98
  - ctx 94 (held-out): A=0.0 -> B=80.3
  - ctx 74-75 (held-out): A=0.0 -> B=60.64, 62.0

---

## 3. La interaccion observada

Lo que la evidencia permite afirmar es una INTERACCION entre el regimen de inferencia del agente base y el efecto de la memoria. No una ley general.

**Regimen B (A malo):**
- A elige corregir_rumbo con regret alto.
- B interviene y cambia a ir_a_punto.
- Regret baja de 48-70 a 0.
- B mejora.

**Regimen A (A bueno):**
- A ya elige ir_a_punto con regret 0.
- B interviene e introduce corregir_rumbo.
- Regret sube de 0 a 50-95.
- B perjudica.

**Frase precisa:**

La memoria externa cambia el comportamiento observado. El signo del efecto depende del regimen de inferencia del agente base. Cuando A ya esta bien, B puede interferir. Cuando A esta mal, B puede corregir.

---

## 4. Lo que NO podemos afirmar

NO podemos afirmar:

- Que la memoria sea buena.
- Que la memoria sea mala.
- Que la memoria amplifique errores y aciertos (eso requeriria un diseno que controle regimen).

El benchmark no permite estimar un efecto global de memoria porque A cambio de regimen DENTRO del mismo benchmark. Cualquier comparacion A vs B mezcla dos cosas: el efecto de la memoria y el estado latente del agente base.

---

## 5. Por que el protocolo "mismo bloque" no alcanzo

El memo 63 (seccion 8) propuso el protocolo: A, A_prima y B dentro del mismo bloque, sin detener Ollama entre condiciones. Eso protege la comparacion DENTRO de un contexto (las tres condiciones ven el mismo estado latente).

Pero no protege la comparacion ENTRE benchmarks. Si el regimen cambia a mitad de la corrida, la comparacion agregada A vs B a lo largo del benchmark mezcla regimenes.

**Lo que se necesita:** un diseno que controle o mida el regimen como variable explicita.
---

## 6. Tres caminos posibles

### Camino 1 — Forzar un regimen unico

Encontrar configuracion de backend/servicio que produzca el mismo regimen durante todo el benchmark. El mas limpio si se logra.

### Camino 2 — Medir regimen como factor

Disenio factorial: memoria OFF/ON x regimen A/B. Pregunta: hay interaccion memoria x regimen? Requiere clasificador de regimen independiente del benchmark.

### Camino 3 — CPU como instrumento de referencia

Si CPU produce regimen reproducible, hacer el benchmark causal alli. Mantener GPU como experimento de rendimiento.

Dado que el objetivo es tomar una decision de diseno sobre memoria (no publicar un paper sobre GPU inference), el Camino 3 es perfectamente aceptable si es necesario.

---

## 7. Lo que NO se hace

NO se agrupan los 350 contextos a posteriori eligiendo el regimen que conviene. Si se agrupa por regimen, la regla de clasificacion tiene que estar definida ANTES de mirar el resultado.

NO se recalcula el benchmark con conclusiones post-hoc.

NO se modifica runner, retrieval, prompt ni memoria hasta decidir la metodologia.

---

## 8. Consultas externas

Se consulta a GPT-4 y Claude con la misma pregunta y el mismo dataset resumido. Preguntas centrales:

1. Como controlar o medir formalmente un cambio de regimen del agente base durante el benchmark?

2. Conviene: (A) forzar un regimen, (B) medir regimen y estratificar, (C) usar regimen como factor experimental, (D) abandonar este backend para evaluacion?

3. Como identificar el efecto de memoria cuando el tratamiento interactua con un estado latente del agente base?

4. Conviene declarar invalido el benchmark actual como estimacion causal, pero conservarlo como evidencia exploratoria de interaccion?

---

## 9. Cierre

**Lo que se preserva:**
- Memo 62: diseno del benchmark.
- Memo 63: defecto de retrieval.
- Bench_100.json: regimen B (A=corregir_rumbo 100/100).
- Bench_100_heldout.json: regimen A con transicion a mitad de corrida.

**Lo que se afirma:**

El cambio de regimen de inferencia es ahora una variable experimental reconocida, no una sospecha ignorable. Evidencia externa: issues de llama.cpp documentan no determinismo en ROCm/RDNA3 con temperature=0, incluyendo Qwen2.5-Coder entre los modelos afectados.

**Conclusion operativa:**

El benchmark causal no es interpretable todavia. Se requiere decision metodologica antes de seguir corriendo.

---

*Documento cerrado. Si se necesita modificar, se crea un 65_REVISION_4.md.*
*Fecha: 2026-10-05.*
*Registrado en EXPEDIENTE/64.*

---

## 10. ENMIENDA (2026-10-05 tarde)

**Motivo:** revision externa del memo senalo que la seccion 2 afirma mas de lo que los datos permiten sostener. La frase original decia: el regimen cambio dentro del benchmark, no entre benchmarks.

**Correccion:** el cambio observado entre los contextos 16 y 17 (dentro del held-out) NO demuestra por si solo un cambio de regimen de inferencia. Puede ser dos cosas distintas:

(a) Cambio de regimen de inferencia del runtime.
(b) Cambio de la politica de Qwen porque los contextos 17-100 son estados diferentes a los 0-16. No es regimen, es la politica respondiendo a estados distintos.

El benchmark actual NO permite distinguir (a) de (b). La redaccion correcta es:

Durante el benchmark, la politica de A cambio de predominio corregir_rumbo a predominio ir_a_punto. Dado que previamente se observo que el mismo contexto puede producir dos resultados distintos entre bloques de ejecucion, queda abierta la hipotesis de que este cambio corresponda a una transicion del regimen de inferencia. El benchmark actual no permite distinguir ambas explicaciones.

---

## 11. Segunda enmienda — confusor de orden A -> A_prima -> B

**Hallazgo adicional:** el disenio del benchmark ejecuta A, A_prima y B en orden fijo dentro de cada contexto. Si el runtime de Ollama tiene estado interno (cache de prompt, estado del runner, cache del modelo) que depende del prompt inmediatamente anterior, entonces B no se evalua bajo las mismas condiciones que A o A_prima.

**Consecuencia:** la diferencia B - A_prima puede venir de:
- El efecto de la memoria (tratamiento).
- El efecto de la posicion en la secuencia (confusor).
- El efecto del largo del prompt (variable tecnica asociada al tratamiento).
- Cualquier combinacion de las anteriores.

El benchmark actual no separa estos efectos.

**Implicancia:** antes de reformular el benchmark causal hay que determinar si el runtime tiene carry-over entre prompts consecutivos. Eso es el objetivo del experimento RUNTIME-CARRYOVER-001, documentado en el memo 65.
