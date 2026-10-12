# Hipótesis central y reordenamiento de fases

Una corrección mía antes de empezar: dije que el condicionamiento por contrato era "lo único" que el LLM aporta sobre un árbol. Es demasiado fuerte. Es lo **más directamente testeable ahora**, no lo único posible (también están la interfaz en lenguaje, la explicación y el conocimiento náutico previo).

## A. Hipótesis central

### A1. ¿Central o auxiliar?

Con la aclaración del Director hay **dos hipótesis distintas** que conviene separar:

- **H1, competencia aprendida (el ABC):** el modelo incorpora conocimiento de decisión náutica a partir de datos, y rinde bien en estados no vistos y en lazo cerrado.
- **H2, condicionamiento por contrato:** la decisión sigue los cambios de la especificación escrita, sin reentrenar.

Para "modelo de aprendizaje de navegación", la central es **H1**. H2 es la **hipótesis diferencial**: sin ella, H1 no se distingue de "un árbol también lo aprende". Y las dos se juntan en una sola idea: en navegación real la tolerancia de llegada o el margen de seguridad **dependen de la misión**, así que saber el ABC incluye saber que la decisión es función del estado **y** de la especificación. Mi recomendación: H1 como central, y H2 como propiedad que se testea dentro de H1.

### A2. Operacionalización por fase

El **tipo de parámetro del contrato** crece con la fase, mientras que la **forma del test** (contrafácticos) se mantiene:

| Fase | Parámetro del contrato que varía |
|---|---|
| 1 | tolerancia de llegada T, velocidad máxima de llegada |
| 2 | margen de seguridad S |
| 3 | tolerancia fina, velocidad de aproximación |
| 4 | ángulo mínimo al viento propio del barco |
| 5 | calado y margen bajo quilla |
| 6 | criterio de exposición a la ola |
| 7 | umbrales de estado de mar para cancelar |

La progresión de exigencia sería: umbral escalar → varios parámetros → **pesos de objetivos en texto** ("priorizá seguridad sobre velocidad") → parámetros de incertidumbre.

### A3. Qué la refutaría (y cuándo el proyecto "no tiene valor")

Los umbrales numéricos los tienen que fijar ustedes **antes** de correr (no tengo sus datos para proponer cifras). El procedimiento sería:

- **H2 refutada** si, en ≥3 semillas y con la curva de aprendizaje ya aplanada, el umbral efectivo no sigue a T en umbrales o formulaciones **no vistas** (error mayor que un ε fijado de antemano, por ejemplo del orden del bin más fino de tu diseño), aunque el modelo sea competente en distribución.
- **H1 refutada** si en lazo cerrado el modelo rinde peor que un baseline clásico por un margen fijado de antemano, incluso con muchos más ejemplos.

Mi lectura del valor (juicio mío):

| Resultado | Consecuencia |
|---|---|
| H1 falsa | El enfoque SFT sobre LLM no es viable para esta tarea |
| H1 verdadera, H2 falsa | Es destilación de política y un árbol o MLP lo hace más barato. El valor migra a la metodología de evaluación (checks, baselines) y habría que buscar otra propiedad específica del LLM |
| H1 y H2 verdaderas, pero un parser más una regla igualan al LLM | Valor limitado a flexibilidad de interfaz |

### A4. Cómo distinguirla de "el modelo obedece reglas"

Con honestidad: **con 2 acciones y un umbral escalar no se puede**. Seguir el contrato *es* obedecer la regla. Por eso la Fase 1a es una prueba unitaria. Las dos señales que sí separan:

- **Derivación:** el contrato declara objetivos y restricciones, no la regla de decisión, y la acción óptima sale de resolver algo (geometría, trade-off), no de evaluar una condición escrita. Aparece desde la 1b y claramente en la Fase 2: "margen S" no dice qué hacer, hay que predecir si se viola.
- **Variación lingüística:** paráfrasis, unidades distintas (por ejemplo "0,01 millas náuticas", sabiendo que 1 mn = 1852 m), cláusulas irrelevantes y formulaciones no vistas.

Un riesgo a asumir: **un árbol al que le des los parámetros del contrato ya parseados también resuelve la variación de T**. La ventaja del LLM es entonces el texto libre. Si un parser (regex) más una regla iguala al LLM, H2 se reduce a "parsing flexible", que es una ventaja débil. Para que sea fuerte, hay que apuntar a derivación con conocimiento náutico implícito, lo que es un terreno más especulativo pero testeable contra convenciones documentadas.

### A5. Qué cambia en el próximo test

1. **T variable con valores no vistos** (la celda que ya tenés).
2. **Pares contrafácticos:** mismo estado, contrato distinto.
3. **Formulaciones del contrato variadas, con algunas retenidas para test**, incluyendo conversiones de unidades.
4. **Baselines:** modelo base sin SFT, regla con T parseado (techo), árbol con los parámetros como features, y regex más regla.
5. **Test 1b** con contrato de ≥2 parámetros. Aviso: una conjunción de dos umbrales (por ejemplo `dist<T y velocidad≤v` → terminar; `dist<T y velocidad>v` → frenar) **sigue siendo una regla determinista** y un árbol la resuelve. Sirve como ABC, no como evidencia de derivación.
6. Lo de siempre: semillas, estratos con IC, manifiesto y preregistro.

## B. Reordenamiento de fases

### B1-B2. Clase de decisión por fase

Clases que uso: **C0** umbral declarado, **C1** multivariable con interacción, **C2** trade-offs (objetivos en conflicto), **C3** incertidumbre (observación ruidosa), **C4** secuencial/planificación en lazo cerrado.

| Fase | Clase principal | Nota |
|---|---|---|
| 1a contrato | C0 | Prueba unitaria |
| 1b 4 acciones | C1 | |
| 2 Obstáculos | C1 → C2 | Progreso vs. margen. Otras embarcaciones suman C4 y reglas documentadas (COLREG) |
| 3 Maniobras finas | C4 | Tolerancia estrecha. Depende de un controlador |
| 4 Velas | C2 + C4 | VMG vs. rumbo directo, bordadas multitramo, zona de no-navegación como restricción dura |
| 5 Fondo | C0 (determinista) → C3 (con ruido de sensor) | |
| 6 Olas | C2 + C3 | Necesita un modelo de estabilidad |
| 7 Mar picado | C3 | Percepción, front-end separado |

### B3. Orden propuesto y bloqueos

**Infraestructura transversal (no es una fase):** lazo cerrado con métricas, cascada LLM→PID, manifiesto y checks, y la **observación como módulo** (ver sección 3).

1. **1a**: puerta de todo.
2. **1b** y **5-determinista** en paralelo. La 5-det es una segunda instancia de C0 con otra variable (calado y margen declarados): sirve de test de **transferencia** del condicionamiento por contrato.
3. **2** (estáticos primero, móviles después).
4. **3 y 4**, paralelizables entre sí tras la 2. Si la Fase 3 incorpora viento, la 4 va antes.
5. **5-incierta, 6 y 7**, junto con la fase ulterior de copilot.

**Dependencias duras:**
- 1a bloquea todo.
- 1b bloquea la 2.
- Lazo cerrado bloquea 2, 3 y 4.
- Polar documentada bloquea la 4 (se puede preparar en paralelo desde ya).
- Modelo de sensor bloquea 5-inc y 7.
- Modelo de estabilidad bloquea la 6.

**Paralelizable ya:** el **front-end de percepción** (wavelets) se puede construir y validar solo contra señales sintéticas con verdad conocida, sin LLM.

### B4. ¿Qué fases deberían ir al final?

La **7**, la **6** y la **5-incierta**, porque su dificultad es la **calidad de la información**, que es justo lo que el Director dejó para la fase ulterior. Tiene sentido juntarlas con ella.

### B5. La más importante para demostrar la hipótesis

**La Fase 2 en su forma estática (2a).** Es la primera donde el contrato no se reduce a un escalar: hay que predecir si se viola el margen S, existe un baseline clásico (regla geométrica) contra el que medir, la métrica es objetiva (colisión y distancia mínima) y la física que exige es poco (cinemática). Detrás de la 1a, que es su puerta.

## 3. Lo que deberían saber y no preguntaron

- **Diseñen ya la observación como módulo:** `observación = f(estado_verdadero, modelo_de_sensor)` con un sensor identidad por ahora. No contradice al Director (la calidad de información sigue siendo fase ulterior) y evita reescribir los prompts después.
- **Escriban el "currículo" del ABC como lista explícita** de conceptos (llegar con tolerancia, mantener rumbo, frenar, margen de obstáculo, reglas de paso, viento), cada uno con su prueba. Sin esa lista, "aprendió el ABC" no es falsable.
- **Acoten el alcance del claim:** con etiquetas del simulador con parámetros inventados, es "ABC **en Polaris**".
- **Fijen el criterio de salida antes de abrir cada fase.** La hoja de ruta se reordenó "hoy" tras resultados; está bien, pero que sea la última vez sin criterios previos.