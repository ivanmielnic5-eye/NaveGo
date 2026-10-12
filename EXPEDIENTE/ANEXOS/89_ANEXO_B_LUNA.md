La primera decisión estratégica que tomaría es no avanzar todavía a la Fase 2 como si la Fase 1 hubiera demostrado discriminación real.

CC003 v4 obtuvo 100 % en una tarea de aplicación del criterio de finalización. Ese resultado puede ser válido para esa capacidad concreta, pero no demuestra que Timonel sepa elegir entre cuatro acciones ni que un LLM aporte valor frente a Python.

La hoja de ruta necesita definir no solamente qué complejidad se agrega en cada fase, sino qué capacidad nueva se pretende demostrar, contra qué referencia se compara y qué resultado obligaría a reconocer que esa capacidad no está presente.

## 1. Constructo de cada una de las siete fases

Por constructo entiendo la capacidad concreta que queremos medir, no la función que programamos ni el resultado que esperamos obtener.

Cada fase debería tener una hipótesis falsable, una métrica primaria, un baseline y una condición de cierre. Las métricas exactas y sus umbrales deben fijarse antes de observar los resultados confirmatorios.

### Fase 1 — ABC motor: selección de acciones

Pendiente de demostrar discriminación

Constructo: el agente selecciona una acción adecuada según el estado, el objetivo y las restricciones, entre `corregir_rumbo`, `ir_a_punto`, `frenar` y `terminar`.

Hipótesis falsable: el agente generaliza la selección de acciones a estados no vistos y obtiene resultados superiores a un baseline sencillo, sin colapsar en una sola acción.

Éxito: mejora sobre la política trivial y demuestra discriminación por clase en el conjunto confirmatorio. Los parámetros son válidos y el resultado de navegación no empeora más allá de los límites predefinidos respecto del piloto Python.

Falsación: el modelo colapsa, no supera el baseline, falla sistemáticamente en alguna acción crítica o acierta las etiquetas sin mejorar el resultado operacional.

Bloqueante para Fase 2: aclarar el valor añadido del LLM frente a Python y validar el entorno y la referencia de evaluación.

Un punto importante: CC003 v4 demostró la aplicación de un criterio de finalización con dos acciones, no el constructo completo de cuatro acciones. Si Fase 1 se define como ABC motor de cuatro acciones, todavía no está cerrada bajo esa definición. Puede darse por cerrada únicamente la subprueba de finalización, con ese alcance explícito.

### Fase 2 — Obstáculos en superficie

Constructo: el agente incorpora obstáculos estáticos y dinámicos al decidir una trayectoria, conservando la viabilidad de llegar a la meta.

Hipótesis falsable: cuando aparece un obstáculo relevante, el sistema modifica la trayectoria de manera segura; cuando el obstáculo no afecta a la ruta, no introduce desvíos innecesarios.

Éxito: satisface los márgenes de seguridad y mantiene una tasa de llegada y un costo de trayectoria dentro de los criterios predefinidos, frente a escenarios comparables sin obstáculos.

Falsación: colisiones, incumplimientos de distancia mínima o ausencia de reacción ante obstáculos que invaden la trayectoria prevista.

Bloqueante para Fase 3: modelo de obstáculos verificado, márgenes de seguridad definidos y pruebas de colisión reproducibles.

Hay una pregunta arquitectónica previa: ¿las acciones actuales permiten representar una evasión segura? Si `ir_a` siempre conduce a una meta fija y no se permiten puntos intermedios, quizás haga falta ampliar el espacio de acciones.

### Fase 3 — Maniobras finas: muelles y canales de 2–3 m

Constructo: el agente logra control geométrico preciso en espacios restringidos, respetando el ancho disponible y las limitaciones de maniobra.

Hipótesis falsable: mantiene las tolerancias de trayectoria y llegada establecidas en escenarios estrechos no vistos, sin aumentar los contactos ni las invasiones de límites.

Éxito: tasas de maniobra satisfactoria, error lateral, distancia mínima a obstáculos y tiempo dentro de los límites previamente establecidos, comparados con un controlador determinista.

Falsación: no alcanza la precisión objetivo, incurre en contactos o solo logra el resultado cuando se le proporcionan trayectorias prácticamente resueltas.

Bloqueante para Fase 4: dinámica de maniobra y posicionamiento validada a la escala de los márgenes de 2–3 m; controlador de bajo nivel y errores de posición documentados.

### Fase 4 — Velas, viento y bordadas

Constructo: el sistema elige cursos y maniobras de vela adecuados a la dirección e intensidad del viento, las restricciones de navegación y el destino.

Hipótesis falsable: adapta sus decisiones a variaciones relevantes de viento y obtiene mejor progreso hacia la meta que una política de referencia, sin violar las restricciones de navegación definidas.

Éxito: mejora o satisface criterios predefinidos de velocidad efectiva hacia la meta, tiempo de llegada y factibilidad de la ruta en escenarios de viento no vistos.

Falsación: no adapta las decisiones al viento, elige maniobras inviables o no aporta valor frente a la política de referencia.

Bloqueante para Fase 5: modelo de propulsión a vela y acciones disponibles definidos. El conjunto actual de cuatro acciones no representa explícitamente el trimado de velas ni las bordadas; esa parte de la interfaz del agente debe diseñarse.

### Fase 5 — Fondo, calado, batimetría y sensores

Constructo: el sistema integra profundidad disponible, calado, incertidumbre de cartas y mediciones para elegir rutas navegables.

Hipótesis falsable: evita zonas con profundidad insuficiente y conserva el margen bajo quilla establecido, incluso ante errores de sensado y cartografía.

Éxito: cumple los márgenes de profundidad en un conjunto de rutas y condiciones no vistos, con una tasa de tránsito satisfactorio dentro del criterio fijado.

Falsación: incursiones en zonas de riesgo, sobreestimación de la profundidad o decisiones que no cambian ante información que vuelve inviable una ruta.

Bloqueante para Fase 6: batimetría, calado, variación del nivel del agua y modelo de incertidumbre de los sensores suficientemente definidos para el objetivo del test.

### Fase 6 — Olas y orientación respecto del oleaje

Constructo: el agente selecciona orientación y maniobras considerando la dirección y el estado del oleaje, sin sacrificar innecesariamente la progresión hacia el destino.

Hipótesis falsable: adapta sus decisiones a cambios relevantes del oleaje y reduce las consecuencias adversas definidas en el modelo respecto de un baseline, manteniendo condiciones de navegación aceptables.

Éxito: satisface límites predefinidos de movimiento, aceleraciones, estabilidad y progreso, en diferentes direcciones e intensidades de oleaje.

Falsación: las decisiones ignoran el oleaje o el sistema empeora los indicadores de seguridad o estabilidad respecto de la referencia.

Bloqueante para Fase 7: dinámica de olas y respuesta del casco definidas y validadas para los indicadores elegidos. Una regla geométrica sobre la dirección de las olas no basta para demostrar seguridad.

### Fase 7 — Mar picado y análisis Penrose/wavelets

Constructo: todavía necesita definición. «Lectura compleja del entorno» no es una hipótesis falsable y no especifica qué información se recibe, qué se debe inferir ni cómo intervienen Penrose y wavelets.

Como propuesta, dividiría esta fase en dos capacidades separadas:

1. Percepción y análisis de señales: estimar propiedades relevantes del oleaje a partir de señales o series temporales.
2. Decisión bajo incertidumbre: utilizar esas estimaciones para recomendar acciones y gestionar la incertidumbre.

Hipótesis falsable: las técnicas propuestas extraen características reproducibles de señales no estacionarias y esas características permiten tomar decisiones mejores que las de una referencia sencilla.

Éxito: errores de estimación y resultados de navegación dentro de umbrales predefinidos, superiores a los baselines elegidos.

Falsación: las características no se recuperan de forma fiable, no generalizan a señales nuevas o no aportan valor decisional frente a métodos simples.

Bloqueante: precisar qué significa Penrose en esta arquitectura, qué datos procesa, cuál es su salida y qué ventaja se espera de ese método frente a wavelets u otras técnicas.

No cerraría el constructo de Fase 7 hasta responder esas preguntas.

## 2. Los bloqueos entre fases

La hoja de ruta parece lineal, pero las fases añaden dimensiones diferentes: percepción, decisiones, control preciso y física ambiental. No son necesariamente siete escalones de una misma capacidad.

Aplicaría estos bloqueos comunes:

| Bloqueo                  | Qué debe resolverse                                                                       |
| ------------------------ | ----------------------------------------------------------------------------------------- |
| Validez del entorno      | La simulación representa adecuadamente el fenómeno para la afirmación que se quiere hacer |
| Validez de la referencia | Las etiquetas y las métricas realmente reflejan el objetivo declarado                     |
| Capacidad mínima         | El sistema supera los baselines relevantes en la capacidad de la fase                     |
| Seguridad operacional    | Las restricciones críticas se cumplen, incluidos los casos fuera de distribución          |
| Reproducibilidad         | El resultado puede repetirse con artefactos, estados y configuraciones congelados         |

Los marcos de verificación y validación de modelos recomiendan definir explícitamente el uso previsto y sus criterios de aceptación; no existe un umbral universal de validez independiente de la aplicación.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://standards.nasa.gov\&sz=32)

Standards

+1



Un sistema puede superar una fase de percepción y seguir fallando en la selección de acciones. También puede disponer de un buen selector de acciones y no tener un controlador capaz de ejecutarlas con precisión. Los resultados deben mantenerse separados.

## 3. Las preguntas que no nos estamos haciendo

Estas son, a mi juicio, las preguntas de mayor riesgo para el proyecto.

### ¿Estamos midiendo copiloto o piloto automático?

El objetivo declarado es asistir al capitán de un velero real, pero buena parte de la hoja de ruta mide si el LLM selecciona y ejecuta acciones.

Hay que decidir qué responsabilidad tendrá:

- ¿Recomendar una maniobra para que la confirme el capitán?
- ¿Ejecutar directamente una acción?
- ¿Supervisar un controlador determinista?
- ¿Detectar situaciones que requieren intervención humana?

Estas funciones no requieren las mismas capacidades. La calidad de una recomendación debe incluir su utilidad para el capitán, la posibilidad de verificarla y la gestión de la incertidumbre.

Los principios de supervisión humana y definición de condiciones de operación segura también aparecen en el marco de seguridad de la Organización Marítima Internacional para buques de superficie autónomos. Ese código no implica por sí solo que Timonel quede sujeto a su régimen regulatorio, pero sirve como referencia metodológica para diseñar límites de operación y mecanismos de supervisión.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.imo.org\&sz=32)

Organización Marítima Internacional

+1



### ¿Qué aporta el LLM que no aporte ya Python?

Esta es la pregunta económica y científica central.

Si un controlador determinista realiza una maniobra mejor, más rápido y de manera reproducible, hay que justificar qué tarea se delega al LLM: interpretar instrucciones del capitán, integrar información heterogénea, recomendar cursos alternativos o gestionar ambigüedad, por ejemplo.

No hace falta que el LLM gane en todas las decisiones para ser útil. Pero sí hay que medir una contribución concreta y no atribuirle valor solamente porque forma parte del sistema.

### ¿Estamos separando bien percepción, planificación y control?

En las fases actuales, estas capacidades pueden confundirse:

- El estado puede estar calculado exactamente por Polaris.
- El LLM puede recibir coordenadas y velocidades ya procesadas.
- El controlador puede corregir el rumbo automáticamente.

Un buen resultado en esas condiciones no demuestra que el LLM pueda interpretar sensores reales, estimar el estado del barco ni generar controles precisos.

Para evitar confusiones, cada fase debe decir qué información se entrega al modelo y cuáles son las transformaciones efectuadas previamente por software determinista.

### ¿Qué pasa cuando el estado es desconocido o contradictorio?

La hoja de ruta debería definir qué hace Timonel cuando:

- faltan datos;
- dos sensores discrepan;
- la estimación es incierta;
- ninguna acción parece segura;
- el entorno queda fuera del dominio probado.

Un copiloto no debería verse obligado a elegir una acción entre las disponibles si todas resultan dudosas. «Solicitar confirmación», «mantener un estado seguro» o «delegar al capitán» pueden ser salidas necesarias, siempre que su semántica esté definida.

### ¿Cómo se evita medir solo memorización?

Cada fase necesita escenarios de prueba que no puedan resolverse por duplicación o por simple reconocimiento de una familia de estados.

La separación de conjuntos debería realizarse por familias de escenarios, condiciones iniciales, semillas o configuraciones relacionadas, según el dominio. El identificador de un contexto no basta para demostrar independencia.

También hay que medir el rendimiento por condiciones y por fallos críticos, no solamente el promedio global.

### ¿Cómo se determina si el sistema es seguro?

La seguridad no debería derivarse de una accuracy general. Una política con gran porcentaje de decisiones correctas puede seguir siendo inaceptable si incurre en una colisión o recomienda una maniobra peligrosa en un escenario crítico.

Necesitamos límites operacionales, análisis de fallos, condiciones de abstención y una política de respaldo determinista. Antes de cualquier ensayo real, estos aspectos requieren evidencia de seguridad propia.

## 4. ¿Qué debería hacernos parar y repensar?

Hay cuatro señales que justificarían revisar la dirección del proyecto.

Primera: el LLM no aporta valor incremental medible frente a Python en tareas que se consideran importantes para un copiloto.

Segunda: la validez de la simulación o de las etiquetas depende de parámetros o criterios arbitrarios que cambian las conclusiones bajo variaciones plausibles.

Tercera: el sistema viola restricciones críticas, y el respaldo no consigue impedirlo de forma demostrable.

Cuarta: la fase demuestra otra capacidad distinta de la que se había declarado. Por ejemplo, una accuracy perfecta al aplicar un umbral fijo no equivale a discriminación general entre maniobras.

Estas señales no obligan siempre a abandonar el proyecto. Pueden indicar que hay que cambiar el rol del LLM, mejorar el simulador o redefinir el constructo. Pero no deberían resolverse cambiando retrospectivamente la métrica de éxito.

## 5. Antes de avanzar a Fase 2, ¿qué es X?

X es cerrar la especificación y la evaluación de Fase 1, y decidir qué contribución concreta se espera del LLM en un sistema de copiloto.

Exigiría cinco entregables:

1. Constructo aprobado: una definición falsable de qué significa discriminar acciones, distinta de aplicar un umbral conocido.
2. Referencia válida para ese alcance: el Entrenador, el simulador y sus condiciones de uso suficientemente verificados para sostener las conclusiones.
3. Baseline Python: rendimiento y fallos documentados sobre los mismos escenarios, con las mismas condiciones iniciales.
4. Evaluación confirmatoria: conjuntos independientes, sin fuga de información, con resultados por acción y métricas operacionales predefinidas.
5. Criterio de avance: un umbral de aceptación fijado antes de examinar resultados, incluidos límites de seguridad y evidencia de contribución del LLM.

Si el objetivo inmediato es empezar a desarrollar obstáculos, se puede hacerlo como una línea paralela de modelado del entorno. Lo que no se debe hacer es presentar ese avance como una demostración de mayor capacidad del agente si Fase 1 aún no la acreditó.

Mi decisión sería mantener la hoja de ruta, pero convertir cada fase en una hipótesis verificable con criterios de cierre, no en una lista de funcionalidades.

La meta no es llegar a Fase 7 porque se implementaron las seis anteriores. Es construir evidencia acumulativa de qué sabe hacer Timonel, en qué condiciones, con qué límites y qué valor aporta al capitán que utiliza el sistema.