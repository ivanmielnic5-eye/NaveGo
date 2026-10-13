# ANEXO I — CLAUDE / PROBE F2 Y AJUSTES A LA ETAPA 1 DE A3

**Fecha:** 2026-10-13
**Origen:** consulta a Claude tras el resultado del probe F2.
**Contenido:** respuesta completa de Claude, sin resumir.

---

# Probe F2 y ajustes a la etapa 1 de A3

No vi el anexo H ni la sección 25 como adjuntos; trabajo con los números de tu mensaje.

## Lectura del probe: qué sostengo y qué corrijo

**Hechos:** SFT 49/50 en Q2 y 199/200 global; base 6/50 en Q2 y 0,345 global.

**Inferencia aritmética:** si cada cuadrante tiene 50 contextos (supuesto mío), el único error global es el de Q2, así que **Q1, Q3 y Q4 dieron 50/50**. Esto descarta la lectura "ante cualquier cláusula extra, el modelo se vuelve conservador (`ir_a`)": acertó los casos donde la cláusula sí se cumple (Q1).

**Intervalos de Wilson 95%:** Q2 49/50 → [0,895; 0,997]; global 199/200 → [0,972; 0,999]. Con n=50 se excluye el azar con claridad, pero **no** se demuestra "≥0,95 con confianza". Pasa el cribado preregistrado, nada más.

**Lo que me parece mal interpretado:**

1. **La base no es control de lectura de cláusula.** Colapsa a `terminar` en los 4 cuadrantes, es decir, **ignora también `d<T`**: no está haciendo la tarea. Los "86 puntos" miden que la base no resuelve nada, no que no lea la velocidad. El control informativo es **dentro del SFT**.
2. **La lectura del Director es una hipótesis razonable, no un hecho.** El probe solo cubre **una** cláusula conjuntiva (velocidad ≤ v_max), en el estilo de plantilla de F1.
3. **Dos alternativas siguen vivas y se separan con controles baratos (solo puntuar, sin entrenar):**
   - **Placebo:** estado con `v` visible, contrato **sin** cláusula de velocidad. Correcto: `terminar` sii `d<T`. Si el modelo pasa a `ir_a` cuando `v` es alta, usa la velocidad como señal de cautela y no lee la cláusula.
   - **v_max variable:** misma `v`, contrato con distinto `v_max` (cruzando `v`). Si el modelo juzga "alta" por la magnitud de `v` sin mirar `v_max`, falla aquí. **Pregunta:** ¿se varió `v_max` en el probe? Si fue constante, este control es obligatorio.

**Consecuencia para el protocolo:** mi regla de cribado decía que si A2 pasaba el probe, el LLM de la etapa 1 sería **el adaptador de A2 congelado**. Pasa, así que **"sin reentrenamiento" se vuelve literal** y LLM-A3 (reentrenado en F1+F2) pasa a brazo secundario. Una salvedad de alcance: un adaptador es **una semilla**; la conclusión vale para ese artefacto, no para la receta de entrenamiento (para eso harían falta semillas; ¿cuántas tuvo A2?).

## 1. H1b-interfaz

### a) Potencia de McNemar

- **El n relevante no es 600.** Son los pares en **F-held** (formulación retenida): 200 por familia = **400**. En F-train, P-text rinde ≈100% y diluye el efecto.
- **Aproximación normal (α=0,01 bilateral, potencia 80%):** hacen falta n ≥ ~1170·q pares para detectar 10 puntos, y n ≥ ~4670·q para 5 puntos, con q = proporción de pares discordantes.

| Efecto | q=0,11 | q=0,20 | q=0,30 |
|---|---|---|---|
| 10 pts, n=400 | ≈1,00 | ≈0,97 | ≈0,86 |
| 5 pts, n=400 | ≈0,95 | ≈0,37 | ≈0,18 |

(Para 5 puntos, 80% de potencia pide ~500 pares con q=0,10 y ~900 con q=0,20.)

**Conclusión:** para 10 puntos, n=400 alcanza si q ≤ ~0,34. Si el efecto esperado es menor, subí F-held a 300 por familia (600 pares); el costo es solo puntuar.

**Corrección a mi propio criterio:** el segundo criterio (LLM a ≤1 punto de P-struct en formulación estándar) está **mal dimensionado**. P-struct es 100% por construcción, así que se reduce a probar error ≤1%, y con 0 errores eso necesita ~300 casos (3/n). Con 200 casos de formulación estándar la cota es 1,5%. Dos arreglos: subir a 300 contextos estándar, o ampliar el margen a **2 puntos** (n ≥ 150).

### b) P-text justo

- **Autor:** un asistente de código bajo una consigna fija ("escribí el mejor parser posible para esta gramática, maximizando exactitud en F-dev"), no el operador con interés en el resultado.
- **Iteraciones:** versión 1 a partir de la gramática y ~20 ejemplos de F-train; hasta K=5 rondas de corrección guiadas por fallos en F-dev; parar al llegar a ≥99% en F-dev o al agotar el presupuesto. Todo se registra.
- **Contra qué:** solo F-train y F-dev. **F-held queda sellado**: su hash se confirma en el repo antes de empezar y se abre después de congelar P-text.
- **Dimensiones de variación:** declárense de antemano (unidades, sinónimos, orden, cláusulas irrelevantes) pero no las instancias. Es lo que sabría un ingeniero real.
- **Autor de F-held:** una tercera parte, con la consigna de "máxima diversidad natural que un operador usaría".

### c) Circularidad y sandbagging

1. **Separación de roles:** el autor de P-text, el de F-held y quien lee resultados son distintos.
2. **Mejor de k:** dos implementaciones independientes de P-text; se congela la mejor en F-dev.
3. **Asimetría a favor del baseline:** una ronda adicional de "red team del baseline" (otra parte intenta mejorarlo en F-dev) antes del congelado.
4. **Criterio de parada y umbral preregistrados.**
5. **Post-hoc separado:** tras abrir F-held, clasificar los fallos de P-text (bug, límite del parser, variación imprevista) y reportar también la versión con los bugs corregidos, **sin usarla** en el criterio primario. Muestra cuánto de la brecha es trivial.

**Limitación a declarar:** H1b-interfaz es **relativa a la distribución de formulaciones** que incluye F-held. Más diversidad hace caer a P-text. El resultado se reporta como función de esa distribución, no como ventaja general.

## 2. Esfuerzo humano

**a) Estandarización.** "Ediciones" y commits son unidades arbitrarias. Mejor:
- **Cobertura con cero ediciones** (automática): exactitud con el código **congelado** sobre contratos nuevos. Es F-held, ya medido.
- **Diff mínimo:** líneas agregadas más eliminadas (`git diff --numstat`) entre el commit base y el primero que pasa una **suite de aceptación** del contrato (~20 contextos por contrato).
- **Tiempo activo** hasta pasar la suite (cronómetro).

**b) ¿Confirmatorio con un solo operador?** No sobre "el esfuerzo humano" en general: sin población no hay inferencia. **Sí** sobre el **artefacto**: la cobertura con cero ediciones y el diff mínimo son mediciones deterministas y replicables por cualquiera. Lo del tiempo de operador es **descriptivo**, con una lista fija de 6-10 contratos nuevos, orden contrabalanceado entre caminos (para el efecto aprendizaje) y sin generalizar.

**c) ¿Tiempo de reacción más limpio?** Solo si se define como **tiempo hasta pasar la suite de aceptación**. Si no, mide velocidad de un sistema que puede equivocarse. Es automático para el LLM (segundos de inferencia) y manual para Python; compara segundos con minutos u horas, así que no sustituye la cobertura con cero ediciones. Cuando el LLM no pasa la suite, el costo es "reentrenar", que no es comparable con editar código: declarar la inconmensurabilidad en vez de forzar una escala común.

## 3. El fallo único de Q2

**a) ¿Ruido o sistemático?** Con n=50 no se puede decir. Con error real de 1%, P(≥1 fallo en 50) ≈ 0,39; con 5%, P(≤1 fallo) ≈ 0,28. Un fallo es compatible con ambos. Para aislarlo en la etapa 1, tres pasos de bajo costo:
1. **Margen del caso:** |d−T| y |v−v_max|, y su diferencia de log-probs. Cerca de 0 es ruido de frontera; error confiado es sistemático.
2. **Re-puntuar con el orden de acciones invertido** y con una paráfrasis: si se corrige, es artefacto de posición o de redacción.
3. **Muestreo de vecindad:** ~20-30 contextos perturbando d, v y v_max en torno al caso. Si el fallo se repite en una región, es sistemático.

**b) Registrar o esperar a que se diluya.** **Registrar siempre**, con prompt, d, T, v, v_max, log-probs y estrato, en un `errores.jsonl`. Diluirlo es lo que esconde la estructura. El análisis de errores es exploratorio y no altera los criterios confirmatorios.

**c) Análisis cerca del límite.**
- **Oversamplear la esquina** (|d−T| y |v−v_max| pequeños a la vez): ~20% de los contextos de F2, de modo que la celda doble-cercana tenga n suficiente.
- **Umbrales efectivos para ambas variables:** ajustar la diferencia de log-probs contra los márgenes (T−d) y (v_max−v) y estimar T̂ y v̂_max con IC (como ya se hace con T̂). **Requiere variar v_max.**
- **Semántica de la conjunción:** comparar un ajuste aditivo contra uno guiado por el **mínimo** de los dos márgenes (un AND debería depender del margen más chico).

## Ajustes al protocolo (resumen)

1. **Etapa 0b (solo puntuar):** placebo (v visible sin cláusula) y v_max variable, antes de comprometer la etapa 1.
2. **LLM de la etapa 1 = adaptador de A2 congelado**; LLM-A3 reentrenado queda como brazo secundario.
3. **F-held:** n=300 por familia si se espera efecto de 5 puntos; sellado y autor independiente.
4. **Criterio de no inferioridad:** margen de 2 puntos, o 300 contextos estándar.
5. **P-text:** procedimiento de la sección 1b-c.
6. **Esfuerzo:** cobertura con cero ediciones (confirmatoria sobre el artefacto) más diff mínimo; tiempo del operador, descriptivo.
7. **Errores:** `errores.jsonl` obligatorio, con re-puntuación por orden y paráfrasis, y esquina oversampleada.