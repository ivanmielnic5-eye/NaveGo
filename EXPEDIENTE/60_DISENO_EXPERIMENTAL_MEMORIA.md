# DISEÑO EXPERIMENTAL — Memoria externa en Timonel — 2026-10-05

**Proyecto:** Timonel (agente LLM local que pilota Polaris en simulador Python)
**Autor:** Directora de Investigación
**Estado:** diseño previo a ejecución. No se corre ningún test hasta cerrar este documento.
**Marco:** hipótesis falsable según Popper.

---

## 0. Por qué este documento

Los tests realizados entre el 2026-10-04 y el 2026-10-05 no siguieron un diseño experimental explícito. Se corrieron batches A/B sucesivos modificando simultáneamente modelo, prompt, retrieval y corpus. Los resultados fueron ambiguos: en 5 mediciones, 4 refutan o no confirman la hipótesis implícita ("la memoria mejora el éxito"), 1 la confirma pero dentro de la varianza esperada.

**Consecuencia:** no podemos decir ni que la memoria aporta ni que no aporta. El diseño no permite concluir.

Este documento cierra ese hueco. Define la conjetura, la predicción, el criterio de falsación, las variables y el procedimiento **antes** de correr cualquier test.

---

## 1. Pregunta de investigación

**Una sola:**

> ¿La memoria externa mejora la calidad de las decisiones individuales del agente, medida contra un oráculo myopic, en misiones multi-meta con viento?

**Aclaración:** no preguntamos si mejora el éxito de misión. Esa es una pregunta distinta, derivada, y ya sabemos que el éxito depende mayormente de la física (viento vs velocidad del barco). La pregunta primaria es sobre **calidad de decisión**.

---

## 2. Conjetura audaz (Popper)

> **La memoria externa mejora la accuracy de decisión del agente en al menos 10 puntos porcentuales, medida contra un oráculo myopic, con seed emparejada y N≥100 estados evaluados.**

**Por qué es audaz:**
- Es una afirmación numérica concreta (10 pp).
- Prohíbe observaciones: si la diferencia es <10 pp, la conjetura se refuta.
- No es un "puede que" — es un "es al menos".

**Por qué es falsable:**
- El oráculo myopic produce una decisión objetiva por estado (según criterio lexicográfico definido abajo).
- Comparamos la decisión de Qwen contra la del oráculo.
- Contamos coincidencias con y sin memoria.
- La diferencia de tasas de coincidencia es medible.

---

## 3. Definiciones operativas

**Accuracy de decisión:**
Porcentaje de decisiones del agente que coinciden con la decisión del oráculo myopic, en el mismo estado.

**Estado evaluado:**
Tupla (posición, heading, sog, meta actual, viento). Se registra al momento de cada consulta al LLM.

**Seed emparejada:**
El mismo seed genera las mismas metas y el mismo viento para las condiciones A (sin memoria) y B (con memoria). Cada estado evaluado en A tiene un gemelo en B.

---

## 4. Lo que este diseño NO va a poder concluir

**Declaración explícita, antes de correr:**

- No vamos a poder concluir que la memoria "aprende" en sentido fuerte.
- No vamos a poder generalizar más allá del contexto específico (2 metas, viento 0-40 kn, Qwen 1.5B).
- No vamos a poder afirmar causalidad sobre el éxito de misión (solo sobre calidad de decisión).
- No vamos a poder extrapolar a otras tareas fuera del dominio de navegación simple.

---

*Documento en construcción. Tanda 1 de 3 completada.*
*Registrado en EXPEDIENTE/60.*

---

## 5. Oráculo myopic

**Definición:** dado un estado (posición, heading, sog, meta actual, viento), el oráculo simula las 3 recetas disponibles con un horizonte fijo y elige la mejor según criterio lexicográfico.

**Recetas disponibles:**
1. `corregir_rumbo(rumbo_hacia_meta)` — girar la proa hacia la meta.
2. `ir_a_punto(meta)` — navegar hacia la meta.
3. `frenar()` — detener el barco.

**Horizonte:** 30 segundos de simulación por receta.

**Criterio lexicográfico (en orden):**

1. **Seguridad (booleano):** el barco no debe salir de un radio de 500m del origen ni quedar fuera de la zona de operación. Si una receta viola la seguridad, se descarta.
2. **Progreso (metros):** entre las recetas seguras, la que más reduce la distancia a la meta actual.
3. **Alineación (grados):** desempate si el progreso es similar. Menor desvío angular final respecto al rumbo hacia la meta.

**Salida del oráculo:** el nombre de la receta ganadora. Solo se consideran "empates" si dos recetas tienen progreso y alineación dentro del 5% — en ese caso el oráculo devuelve múltiples respuestas válidas.

**Limitación declarada:** el oráculo es "myopic" (miope). Solo ve 30 segundos hacia adelante. No sabe si una decisión hoy es mejor para la misión completa de mañana. Por eso mide **calidad de decisión local**, no óptimo global.

---

## 6. Variables

**Independiente (única):**
- Presencia de memoria externa en el prompt. (ON / OFF)

**Dependiente (única):**
- Accuracy de decisión: % de coincidencia entre la decisión del agente y la del oráculo.

**Controladas (no cambian entre A y B):**
- Modelo: Qwen 2.5 Coder 1.5B (el más rápido y ya validado).
- Prompt: versión actual con memoria al final (v4 con bloque de experiencias al final).
- Retrieval: filtro duro + filtro de consenso (versión de hoy).
- Corpus: congelado al inicio del experimento. No se agregan decisiones durante el test.
- Seeds: 5 seeds fijas (1111, 2222, 3333, 4444, 5555).
- Tipo de misión: 2 metas.
- Viento: aleatorio en [0, 40] kn, direcciones variables, mismo seed para A y B.
- Timeout por corrida: 300s simulados.
- Límite de pasos por corrida: 15.

**Registradas pero no controladas (exploratorias):**
- Tasa de éxito de misión.
- Pasos promedio.
- Tiempo total.
- Fracasos por rendición prematura.

---

## 7. Procedimiento

**Fase 1 — Corpus congelado.**

Antes de correr el experimento, se detiene la escritura en la base de memoria. Se registra el hash del archivo `memoria.db`.

**Fase 2 — Recolección de estados.**

Para cada seed en {1111, 2222, 3333, 4444, 5555}:

1. Se corre una corrida con memoria OFF. Se registran todos los estados evaluados y las decisiones tomadas.
2. Se corre la misma corrida con memoria ON (mismo seed, misma meta, mismo viento). Se registran todos los estados y decisiones.
3. Los estados de A y B son idénticos (mismo seed → mismo estado físico en cada paso).

**Fase 3 — Evaluación con oráculo.**

Para cada estado registrado (los mismos en A y B), se corre el oráculo myopic. Se obtiene la decisión del oráculo.

**Fase 4 — Comparación.**

Para cada estado:
- ¿La decisión del agente en A coincide con la del oráculo?
- ¿La decisión del agente en B coincide con la del oráculo?

Se calcula:
- Accuracy A: total coincidencias en A / total estados.
- Accuracy B: total coincidencias en B / total estados.
- Delta: Accuracy B − Accuracy A.

**Fase 5 — Análisis estadístico.**

- Test de McNemar sobre los pares discordantes.
- Reportar: Accuracy A, Accuracy B, Delta, IC 95% del Delta, p-value.
- Métricas exploratorias: éxito de misión en A y B.

---

## 8. Criterio de falsación

**La conjetura se refuta si:**

- El Delta de accuracy es **< 10 pp** (umbral declarado en la conjetura).
- **O** el intervalo de confianza del 95% del Delta **incluye el cero**.
- **O** el p-value de McNemar es **> 0.05**.

**La conjetura se confirma si:**

- El Delta de accuracy es **≥ 10 pp**.
- **Y** el IC 95% excluye el cero (límite inferior > 0).
- **Y** el p-value de McNemar es **≤ 0.05**.

**Zona gris (ni confirmación ni refutación):**

- Delta entre 5 y 10 pp, significativo estadísticamente.
- Resultado: "efecto positivo pero menor al umbral declarado". Se reporta como tal.

---

## 9. Tamaño de muestra

**Objetivo:** detectar una diferencia de 10 pp en accuracy con potencia estadística >= 0.8.

- N=100 estados por condición puede detectar diferencias de ~10 pp con potencia razonable (McNemar).
- Si la tasa base es muy alta (>80%) o muy baja (<20%), la potencia baja.
- N>=500 estados evaluados por condición. Si hay menos, no se corre el análisis.

---

## 10. Análisis planeado

Tabla de contingencia McNemar:

| | B acierta | B falla |
|---|---|---|
| A acierta | a | b |
| A falla | c | d |

- b = A acierta y B falla (memoria perjudicó).
- c = A falla y B acierta (memoria ayudó).

Estadístico: chi2 = (b-c)^2 / (b+c) si b+c > 25. Binomial exacto si b+c <= 25.

Reportes obligatorios: Accuracy A, Accuracy B, Delta (pp), IC 95% (bootstrap 10.000 resamples), b, c, p-value McNemar, veredicto.

Reportes exploratorios (no decisivos): éxito de misión, fracasos, tiempo real.

---

## 11. Limitaciones declaradas

1. Oráculo myopic: solo ve 30s. No captura óptimo global.
2. Modelo único: solo Qwen 1.5B.
3. Tarea específica: 2 metas con viento. No extrapola a otros dominios.
4. Corpus congelado: el actual (~8000 decisiones).
5. Métrica única primaria: accuracy contra oráculo myopic.
6. Sesgo geométrico del corpus: más desvíos positivos que negativos.

---

## 12. Reglas metodológicas (popperianas)

1. No cambiar el diseño después de empezar a correr.
2. No correr tests hasta que este documento esté cerrado y commiteado.
3. Reportar todos los resultados, incluyendo los que no favorecen la conjetura.
4. No declarar victoria con N < 500.
5. Cada test posterior se hace bajo diseño explícito. Prohibido "veamos si sale".
6. Toda hipótesis debe ser falsable.
7. Cambiar de opinión frente a la evidencia, no frente a la expectativa.

---

*Documento cerrado. Una vez commiteado, queda congelado.*
*Si se necesita modificar, se crea un 61_REVISION_DISENO_EXPERIMENTAL.md.*

*Fecha: 2026-10-05*
*Registrado en EXPEDIENTE/60.*
