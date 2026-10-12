Con la aclaración del Director, corrijo una parte importante de mi recomendación anterior: la hipótesis «la decisión cambia apropiadamente cuando cambia el contrato del prompt, sin reentrenar» no debería ser la hipótesis central de la fase actual. Es una hipótesis auxiliar sobre adaptabilidad a instrucciones, más relevante para la futura arquitectura de copiloto.

Ahora el objetivo es otro: demostrar que Timonel aprende el ABC de la navegación y selecciona acciones en función del estado, en lugar de limitarse a repetir una regla proporcionada.

# A. Validación de la hipótesis central

## 1. ¿Cuál debería ser la hipótesis central?

Formularía la hipótesis principal así:

> H1 — Política de navegación condicionada por el estado. Tras entrenarse con ejemplos del dominio, Timonel selecciona entre las acciones disponibles en función del estado observable y del objetivo de navegación, generaliza a estados no vistos y consigue un rendimiento superior a baselines simples predefinidos, bajo un entorno y un criterio de evaluación validados.

Esta formulación tiene cuatro componentes comprobables:

- Dependencia del estado: no emite siempre la misma acción.
- Corrección: las decisiones son apropiadas para el objetivo definido.
- Generalización: funciona en estados que no aparecieron durante el entrenamiento.
- Valor incremental: aporta algo frente a una regla simple o un controlador Python.

No basta con cumplir uno. Usar las cuatro acciones no prueba corrección; acertar el 100 % de un umbral conocido no prueba generalización; superar un baseline trivial por unos pocos puntos no demuestra una ventaja práctica.

La hipótesis de adaptación al contrato quedaría aparte:

> H2 — Adaptabilidad a instrucciones. Sin reentrenamiento, Timonel adapta correctamente sus decisiones cuando cambia el objetivo o las restricciones que debe cumplir.

H2 puede ser importante para el copiloto futuro, cuando un capitán establezca prioridades diferentes. Pero no reemplaza H1 en la etapa actual.

También corrijo otra parte de mi razonamiento anterior: adaptarse a instrucciones no es la única capacidad potencialmente valiosa de un LLM. Puede aportar interpretación semántica, manejo de instrucciones flexibles o transferencia entre tareas. Esas capacidades deben evaluarse por separado; no hay que presuponerlas.

## 2. ¿Cómo se operacionaliza la hipótesis en las siete fases?

La hipótesis central no tiene que convertirse en exactamente el mismo test siete veces. Se mantiene el criterio transversal de aprender una política condicionada por el estado, mientras cambia la capacidad específica que se evalúa en cada fase.

| Fase                                | Constructo específico                        | Qué demostraría aprendizaje                                                                |
| ----------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 1. ABC motor                        | Selección entre cuatro acciones              | Elige la acción apropiada según estado, objetivo y restricciones, en situaciones no vistas |
| 2. Obstáculos                       | Evitación y planificación restringida        | Cambia su plan ante obstáculos relevantes y mantiene una trayectoria segura                |
| 3. Maniobras finas                  | Control preciso en espacios estrechos        | Cumple tolerancias geométricas y de maniobra no vistas                                     |
| 4. Velas y viento                   | Decisión condicionada por dinámica ambiental | Adapta las maniobras al viento y las restricciones de navegación                           |
| 5. Fondo y calado                   | Navegación con restricciones de profundidad  | Evita rutas inviables y mantiene márgenes bajo quilla                                      |
| 6. Olas                             | Decisión bajo perturbaciones dinámicas       | Adapta la navegación a cambios del oleaje y cumple los objetivos operacionales             |
| 7. Mar picado y análisis de señales | Percepción y decisión bajo incertidumbre     | Extrae información relevante de señales y la usa para mejorar decisiones en estados nuevos |

Cada fase debe definir una métrica primaria, un baseline, un conjunto confirmatorio y un criterio de falsación.

Por ejemplo, en Fase 2, una prueba válida no es simplemente comprobar que el modelo cambia de acción cuando aparece una boya. Debe verificar si el cambio evita una colisión, conserva la factibilidad de la ruta y resulta mejor que una política de referencia.

## 3. ¿Qué refutaría la hipótesis central?

Hay que distinguir entre refutar una hipótesis y declarar que todo el proyecto carece de valor.

Para Fase 1, registraría antes del experimento condiciones como estas:

La hipótesis no queda respaldada si, sobre un conjunto confirmatorio independiente y con el entorno y las etiquetas validados:

- el modelo colapsa en una acción o no discrimina las situaciones relevantes;
- no supera el baseline predefinido dentro de la incertidumbre estadística y del margen de relevancia práctica;
- solo funciona cuando la regla particular de decisión está escrita en el prompt;
- sus decisiones no producen resultados operacionales aceptables frente al piloto Python.

No fijaría ahora un porcentaje universal de accuracy. El umbral debe derivarse del uso previsto y de la diferencia de rendimiento que justificaría mantener el componente LLM.

Si H1 falla para Llama 3.1 8B con el entrenamiento y el entorno evaluados, queda refutada esa afirmación para esa configuración. No prueba que todos los LLM sean incapaces ni que la arquitectura de copiloto no pueda aportar valor de otra manera.

## 4. ¿Cómo se distingue aprendizaje de obediencia?

La distinción exige controles experimentales, no una redacción ingeniosa del prompt.

Usaría tres condiciones separadas:

| Condición                                               | Qué mide                                        |
| ------------------------------------------------------- | ----------------------------------------------- |
| Regla explícita en el prompt                            | Capacidad de ejecutar una política especificada |
| Objetivo y semántica de acciones, sin regla de decisión | Capacidad de aplicar lo aprendido al estado     |
| Cambio del objetivo o contrato sin reentrenar           | Adaptabilidad a instrucciones nuevas            |

La segunda es la condición principal para H1.

Para que sea convincente, necesita estados de prueba que varíen en dimensiones relevantes y combinaciones que no estén memorizadas del entrenamiento. Incluiría pares contrafactuales: cambiar una variable del estado debe cambiar la decisión cuando corresponda, mientras que modificar un dato irrelevante no debe provocar cambios arbitrarios.

Hay una limitación importante en CC003: como solo intervienen `ir_a` y `terminar` y el propósito contiene el umbral de 15 m, la política está prácticamente determinada. Ese banco sirve para medir la aplicación del criterio de finalización, pero no puede demostrar la discriminación general de H1.

## 5. ¿Qué cambia en el próximo test?

Antes de diseñar otro prompt, definiría el objeto de evaluación: las cuatro acciones, su semántica, el objetivo de navegación y el criterio de utilidad.

Después haría lo siguiente:

1. Validar el simulador y el Entrenador para el uso previsto.
2. Crear un conjunto de desarrollo y otro confirmatorio separado por familias de escenarios relacionadas.
3. Entrenar únicamente con el conjunto de desarrollo.
4. Comparar sobre el confirmatorio el modelo entrenado, una regla simple, el piloto Python y la referencia del Entrenador.
5. Medir exactitud balanceada, rendimiento por acción, calidad de parámetros y resultado operacional.

El cambio fundamental es que ya no buscamos un prompt que produzca la respuesta deseada. Buscamos evidencia de una política aprendida que funcione en estados nuevos.

# B. Reordenamiento de las fases por clase de problema

No conservaría el orden actual simplemente porque pasa de un entorno aparentemente sencillo a otro más complejo. Ordenaría las fases según el tipo de razonamiento y control que se quiere evaluar.

La secuencia siguiente es una propuesta metodológica, no una afirmación de que una fase deba completarse íntegramente antes de que pueda investigarse otra.

## 1. Secuencia propuesta

## 1

ABC motor — Decisión condicionada por el estado

Problema: selección multivariable

Seleccionar entre las cuatro acciones teniendo en cuenta rumbo, distancia, velocidad y las condiciones relevantes. El umbral terminal debe seguir siendo una subprueba, no la evidencia principal de aprendizaje.

## 2

Velas y viento — Decisión dinámica multivariable

Problema: dinámica y trade-offs

El viento modifica las posibilidades de avance, los rumbos alcanzables y la conveniencia de una maniobra. Es una buena extensión para comprobar si la política responde a interacciones entre variables, siempre que el modelo de dinámica de vela exista y esté validado.

## 3

Obstáculos en superficie — Planificación con restricciones

Problema: factibilidad y trade-offs

El agente debe conservar el objetivo de navegación sin atravesar regiones no factibles. La evaluación debe comparar rutas y resultados, no solamente la elección puntual de una acción.

## 4

Fondo y calado — Restricciones con información incompleta

Problema: seguridad e incertidumbre

Combina planificación con restricciones duras y errores de medición o cartografía. El constructo debe incluir el tratamiento de la incertidumbre de profundidad, no solo una comparación geométrica de rutas.

## 5

Maniobras finas — Control preciso restringido

Problema: precisión y control

Entrar en un muelle o pasar un canal de 2–3 m requiere considerar la dinámica del casco, el controlador de bajo nivel, el error de posición y los márgenes de seguridad. Es una prueba de precisión y factibilidad, no una simple ampliación del selector de acciones.

## 6

Olas — Decisión bajo perturbaciones temporales

Problema: dinámica variable

El modelo debe adaptar las decisiones al estado del mar y a cómo evoluciona la embarcación, conservando el objetivo operacional.

## 7

Mar picado — Percepción incierta e integración

Problema: inferencia bajo incertidumbre

Integrar señales complejas, estimación del estado y decisiones bajo perturbaciones. La parte de Penrose/wavelets necesita definirse por separado: qué señal entra, qué propiedad estima y cómo esa salida cambia una decisión.

Esta secuencia sitúa primero la selección de acciones y el manejo de dinámica multivariable; después incorpora restricciones de planificación y precisión; finalmente aborda la incertidumbre temporal y la integración de señales complejas.

El orden no significa que las olas sean necesariamente más difíciles que los obstáculos en todos los aspectos. Significa que sus exigencias experimentales son distintas.

## 2. ¿Qué fases son realmente bloqueantes?

Hay dependencias técnicas que sí bloquearía y otras que permitiría avanzar en paralelo.

| Dependencia                                 | Decisión                                                                                                       |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Verificación del simulador y del Entrenador | Bloqueante para generar etiquetas y hacer afirmaciones sobre corrección                                        |
| ABC de cuatro acciones                      | Bloqueante para afirmar que se aprendió esa capacidad; no impide desarrollar otros módulos en paralelo         |
| Dinámica de velas                           | Bloqueante para validar decisiones relacionadas con ceñida y bordadas                                          |
| Modelo de obstáculos y geometría            | Bloqueante para validar evitación y maniobras estrechas                                                        |
| Batimetría y modelo de incertidumbre        | Bloqueante para afirmar que el sistema decide de forma segura frente a restricciones de profundidad            |
| Modelo y observación de olas                | Bloqueante para el benchmark decisional de oleaje, pero no para desarrollar previamente el análisis de señales |

### Qué haría en paralelo

- Obstáculos y batimetría: pueden avanzar en paralelo si comparten la representación espacial, el sistema de coordenadas y la interfaz de planificación.
- Velas y oleaje: se pueden desarrollar modelos físicos preliminares en paralelo, aunque la validación integrada depende de tener control y dinámica coherentes.
- Wavelets y análisis de señales: pueden probarse tempranamente sobre señales sintéticas o registradas. Lo que debe esperar es afirmar que mejoran decisiones náuticas hasta validar la relación entre la señal y la dinámica del barco.
- Arquitectura futura del copiloto: las cuestiones de operación offline, calidad de la información, supervisión del capitán y abstención pueden diseñarse como una línea separada. No necesitan presentarse como resultados de aprendizaje de navegación de la fase actual.

## 3. ¿Qué es lo que más sentido tiene mover al final?

El componente de integración de mar picado, estimación del estado y decisión bajo incertidumbre sí debe estar al final de la progresión integrada, porque depende de que funcionen las capacidades anteriores.

Pero no retrasaría todo el trabajo con wavelets hasta Fase 7. Una técnica de análisis de señales puede evaluarse de forma aislada mucho antes; lo que requiere la integración final es demostrar que su salida es fiable y útil para la decisión.

Tampoco mezclaría ese trabajo con la pregunta actual de si el LLM aprende el ABC. Son hipótesis diferentes.

## 4. ¿Qué fase demuestra mejor la hipótesis central?

Fase 1, pero únicamente si se redefine como selección generalizable entre las cuatro acciones y no como aplicación del umbral de finalización.

Es el primer lugar donde puede comprobarse si el modelo responde a variaciones relevantes del estado y aprende una política que no se reduce a una condición conocida.

El test debería incluir:

- Estados de desarrollo y confirmatorios independientes.
- Contrafactuales en que cambie una variable decisiva.
- Casos en que una variable cambie sin alterar la acción óptima.
- Comparación contra el baseline determinista y Python.
- Métricas por acción y de resultado operacional.
- Parámetros evaluados por separado de la elección de acción.

Si H1 no se demuestra en esa fase, avanzar puede seguir siendo útil para desarrollar modelos del entorno, controladores o percepción. Pero no conviene presentar la acumulación de fases como evidencia de que el LLM aprendió a navegar.

# C. Las preguntas que faltan y la decisión inmediata

Hay tres cuestiones que resolvería antes de congelar esta hoja de ruta.

Primera: qué quiere decir «aprender el ABC». ¿Se pretende reproducir la política del Entrenador, aproximar una política de navegación útil o demostrar que un LLM aporta algo distinto de un controlador clásico? Pueden relacionarse, pero no son el mismo criterio de éxito.

Segunda: qué decisiones puede representar el espacio de acciones. Las cuatro acciones actuales pueden bastar para ciertos escenarios iniciales, pero no necesariamente para elegir un waypoint alternativo, ajustar velas o ejecutar una evasión. Las limitaciones del espacio de acciones deben separarse de las limitaciones del modelo.

Tercera: cómo se establece la referencia. La función de utilidad del Entrenador y la validez de Polaris son condiciones previas a cualquier conclusión sobre aprendizaje. Si la etiqueta es incorrecta, ni una accuracy baja ni una accuracy alta responden de forma fiable a la hipótesis.

### Mi recomendación concreta

Antes de empezar Fase 2 como evaluación del agente, cerraría un documento de una página con:

1. H1 como hipótesis central de aprendizaje de la política.
2. H2 como hipótesis auxiliar de adaptación a instrucciones.
3. Los baselines y métricas para la Fase 1 de cuatro acciones.
4. El criterio de falsación y las condiciones de validez del simulador y del Entrenador.
5. Las dependencias de las fases siguientes.

El objetivo es que cada fase produzca evidencia nueva y falsable, no solamente que añada funcionalidad. La fase actual debe demostrar si Timonel aprende a tomar decisiones de navegación a partir del estado; las capacidades de copiloto y adaptación flexible se pueden evaluar después, como una línea explícita de investigación.
