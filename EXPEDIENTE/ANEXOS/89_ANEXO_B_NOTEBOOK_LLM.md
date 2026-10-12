Aquí tienes las referencias científicas, publicaciones recientes y técnicas metodológicas concretas para los tres pedidos del benchmark del agente **Timonel**:

---

### PEDIDO 1 — Prompt con T variable y orden aleatorio de acciones

#### 1. When Counterbalancing Hides the Bias: Access-Conditioned Position Lock in Forced-Choice LLM Evaluation
* **URL:** [suspicious link removed]
* **Resumen:** Examina cómo la permutación u ordenamiento aleatorio de opciones en prompts de elección forzada puede simplemente "promediar" el sesgo posicional sin eliminarlo si el modelo sufre de *position-lock*. Propone un diagnóstico formal para aislar la señal real de decisión del sesgo de posición.
* **Código / Implementación:** Incluye un protocolo de diagnóstico en 5 pasos para medir y aislar el *position lock* vs. la preferencia semántica en decisiones discretas.

#### 2. Pair Difficulty Matters: Rethinking Pairwise LLM-as-a-Judge Evaluation and Consistency
* **URL:** [suspicious link removed]
* **Resumen:** Modela la geometría de las decisiones binarias y pareadas bajo el modelo Bradley-Terry, mostrando que el sesgo de posición se concentra en pares con brecha de dificultad estrecha (*close-rank gap*). Demuestra cómo evaluar la consistencia condicional a la brecha de dificultad.
* **Código / Implementación:** Repositorio público disponible en GitHub (`brunobrocai/PairDifficulty`) con scripts para agregación de preferencias y control de sesgo posicional.

#### 3. Words Speak Louder Than Order: A Behavioral Evaluation of Gemma 4
* **URL:** [suspicious link removed]
* **Resumen:** Mide la magnitud del sesgo posicional a través de plantillas de prompts permutadas. Formaliza configuraciones de cruzamiento de 4 vías (*4-way crossing configurations*) para evaluar decisiones en presencia de variaciones en la ordenación de las acciones.
* **Código / Implementación:** Define tablas de diseño factorial de 4 bloques para alternar el orden de las opciones de respuesta sin alterar el significado semántico.

---

### PEDIDO 2 — Análisis por logprobs y curva psicométrica

#### 1. Item Response Scaling Laws: A Measurement Theory Approach to Generalizable Neural Performance Prediction
* **URL:** [suspicious link removed]
* **Resumen:** Extiende la Teoría de Respuesta al Ítem (IRT) a redes neuronales y LLMs utilizando distribuciones Beta sobre las probabilidades logarítmicas (*logprobs*) de tokens de respuesta, ajustando curvas de capacidad y umbral \\(P(\text{correcto}) = \sigma(k \cdot (\hat{T} - d))\\).
* **Código / Implementación:** Formulación matemática con pérdida Beta para ajustar curvas de discriminación (\\(k\\)) y umbral (\\(d\\)) directamente desde logprobs continuos.

#### 2. Latency-Response Theory Model: Evaluating Large Language Models via Response Accuracy and CoT Length
* **URL:** https://arxiv.org/abs/2512.07019
* **Resumen:** Propone el modelo LaRT que combina precisión de respuesta con longitud del razonamiento o incertidumbre latente mediante un algoritmo Expectation-Maximization (EM) estocástico para caracterizar la curva de capacidad del modelo frente a la dificultad del ítem.
* **Código / Implementación:** Código fuente y datasets disponibles públicamente para estimación de parámetros IRT en benchmarks de decisión.

#### 3. Lost in Benchmarks? Rethinking Large Language Model Benchmarking with Item Response Theory (PSN-IRT)
* **URL:** https://arxiv.org/abs/2505.15055
* **Resumen:** Introduce un marco de IRT apoyado en redes Pseudo-Siamesas (PSN-IRT) para estimar parámetros de discriminación y nitidez (*sharpness*) en tareas de decisión binaria de LLMs, separando la habilidad latente de las características del ítem.
* **Código / Implementación:** Arquitectura de red neuronal para ajustar parámetros \\(a_i\\) (sharpness) y \\(b_i\\) (threshold) en preguntas de decisión binaria.

---

### PEDIDO 3 — Evaluación de invarianza

#### 1. Reasons or Rhetoric? A Counterfactual Audit of LLM Judges in Multi-Agent Debate
* **URL:** [suspicious link removed]
* **Resumen:** Propone el principio de **Invarianza Contrafactual** para verificar si las decisiones de un agente cambian cuando se modifican aspectos superficiales de presentación (orden de enumeración, formato, variables irrelevantes) pero se mantiene idéntico el contenido semántico.
* **Código / Implementación:** Protocolo de auditoría contrafactual pareada comparando salidas estructuradas vs no estructuradas bajo 36.000 evaluaciones.

#### 2. A Judge Should Know What Changed: Construct Validity for LLM-as-a-Judge Evaluation
* **URL:** [suspicious link removed]
* **Resumen:** Formaliza la validez de constructo dividiendo la evaluación en dos ejes independientes: la **Sensibilidad** a cambios semánticos relevantes y la **Invarianza** ante transformaciones irrelevantes (formato, variables sintácticas, distractores).
* **Código / Implementación:** Definición matemática del perfil \\(V(J) = (S, R)\\) para medir sensibilidad e inestabilidad ante perturbaciones del entorno.

#### 3. When Names Change Verdicts: Intervention Consistency Reveals Systematic Bias in LLM Decision-Making
* **URL:** [suspicious link removed]
* **Resumen:** Aplica pruebas de invarianza y consistencia de intervención reemplazando variables no relacionadas (nombres, identificadores, metadatos no tácticos) para auditar la presencia de correlaciones espurias en decisiones de LLMs.
* **Código / Implementación:** Framework CAFFE para generación de casos de prueba contrafactuales pareados en tareas de decisión.

---

### 💡 5 Prácticas Comunes Encontradas en la Literatura

1. **Permutación y Contrabalanceo Pareado (*Order Swapping*)**: Para controlar el sesgo posicional, cada caso de prueba se evalúa en ambas orientaciones (Opción A/B y B/A). Las decisiones solo se consideran sólidas si el modelo mantiene su elección semántica independientemente del orden de los tokens.
2. **Extracción Directa de Logprobs en el Unembed Header**: Para medir la curva psicométrica \\(P(\text{acción}) = \sigma(k \cdot (\hat{T} - d))\\), se extrae el logprob normalizado de los tokens objetivos (ej. `TERMINAR` vs `CONTINUAR`) directamente desde los logits de salida (`vLLM` con `logprobs=True` o `HuggingFace` `outputs.logits`), aplicando Softmax sobre el vocabulario reducido de acciones válidas.
3. **Modelado Psicométrico con Teoría de Respuesta al Ítem (IRT)**: En lugar de medir precisión binaria cruda (0/1), se ajustan curvas logísticas de 2 parámetros (2PL-IRT) para caracterizar el **umbral de decisión (\\(\hat{T}\\))** y la **nitidez/discriminación (\\(k\\))**, identificando si el modelo duda cerca del umbral o responde con incertidumbre.
4. **Pruebas de Invarianza Contrafactual (*Invariance / Intervention Testing*)**: Para descartar que el modelo use variables espurias (como el nombre del barco, hora simulada o ID del waypoint), se inyecta ruido aleatorio sobre las variables irrelevantes. Si la acción elegida o la probabilidad del token cambia, se detecta una correlación espurio-sintáctica.
5. **Estratificación por Brechas de Dificultad (*Rank-Gap Stratification*)**: Los bancos de prueba se dividen en bandas de distancia al umbral (\\(|d - T|\\)). La evaluación no se reporta como una métrica escalar única, sino como un perfil condicional a la dificultad para evitar que las decisiones triviales oculten los fallos cerca del umbral.

---

⚓ ¿Te gustaría que diseñemos el script de evaluación en Python para calcular la curva psicométrica y la estimación de parámetros IRT a partir de las salidas de vLLM o HuggingFace?
