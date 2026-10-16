# MEMO TÉCNICO DE REFERENCIA

## NAVEGO – Polaris – Timonel

### Estado del sistema, arquitectura actual y hoja de ruta de navegación autónoma

**Fecha:** 15 de octubre de 2026  
**Tipo de documento:** Registro técnico de estado y planificación  
**Propósito:** Preservar las observaciones, los hallazgos de código, las decisiones arquitectónicas y la hoja de ruta acordada para las próximas semanas y meses.

---

## 1. Resumen ejecutivo

NAVEGO dispone de una base experimental que permite estudiar navegación autónoma mediante una combinación de simulación tridimensional, telemetría, control programático y modelos de lenguaje.

Durante las pruebas con Polaris observamos que la embarcación se alejó considerablemente del muelle y posteriormente volvió a aproximarse, hasta situarse sobre la zona del muelle o muy cerca de ella, en presencia de viento y movimiento del agua. El usuario informó que había llegado a estar a unos 500 metros y que regresó sin ancla, soga ni mecanismo de apagado que la mantuviera fija.

Este comportamiento constituye una observación experimental relevante. No debe confundirse, sin embargo, con una demostración de todas las capacidades de navegación autónoma: todavía tenemos que establecer qué parte del resultado depende del controlador, qué parte depende de la física simulada y cómo se comporta el sistema en condiciones nuevas y reproducibles.

La inspección del código permitió resolver una duda fundamental:

**El proceso Timonel que estaba activo toma actualmente sus decisiones de movimiento mediante una ley de control determinista escrita en Python. No consulta al LLM en cada ciclo de navegación.**

Esto es importante porque nos proporciona un punto de partida concreto: un controlador de referencia que podemos medir y comparar con futuras versiones que incorporen un LLM, un planificador de rutas, un verificador de seguridad o una política aprendida.

La dirección acordada es avanzar hacia un sistema modular, evaluable y capaz de aprender de experiencias reproducibles, sin exigir que un único modelo de lenguaje resuelva todos los problemas de navegación.

## 2. Estado observado el 15 de octubre de 2026

### 2.1. Comportamiento de Polaris

Durante las pruebas se observaron las siguientes circunstancias:

- La embarcación se encontraba inicialmente a gran distancia del muelle.
- El usuario observó que volvió a aproximarse y terminó junto al muelle.
- El entorno incluía viento intenso y movimiento del agua.
- No había un ancla ni una soga que explicaran que el barco permaneciera sujeto.
- En la fase final, la embarcación continuaba moviéndose y corrigiendo su posición en las inmediaciones del destino.

En una de las inspecciones, la telemetría registraba una distancia al objetivo de aproximadamente 497 metros. En una captura posterior, el barco estaba a unos pocos metros de la meta.

El registro de 30 segundos obtenido a las 04:34 del 15 de octubre mostró:

| Hora local | Distancia a la meta | SOG |
|---|---:|---:|
| 04:34:15 | 8,354 m | 1,591 kn |
| 04:34:20 | 7,536 m | 0,631 kn |
| 04:34:25 | 10,077 m | 1,375 kn |
| 04:34:30 | 12,584 m | 0,499 kn |
| 04:34:35 | 9,702 m | 2,079 kn |
| 04:34:40 | 8,023 m | 0,741 kn |
| 04:34:45 | 8,147 m | 0,234 kn |

El viento aparente registrado en esas muestras oscilaba aproximadamente entre 36,9 y 40,2 nudos.

**Interpretación:** el barco alcanzó la zona del destino y se mantuvo cerca, pero la distancia no fue monótonamente decreciente ni permaneció fija. La SOG también fluctuó. Estos datos son compatibles con una aproximación seguida de movimiento residual y deriva en el entorno simulado.

No debemos llamar a esto estacionamiento perfecto, fondeo ni mantenimiento garantizado de posición. Tampoco debemos restarle valor a la aproximación observada: es un comportamiento que merece convertirse en una prueba repetible.

### 2.2. Procesos y archivos observados

En la inspección realizada a las 04:33:15 del 15 de octubre:

- Se encontró activo el proceso `python -u timonel.py`, PID 28889.
- El archivo `telemetria.jsonl` seguía actualizándose.
- El archivo `comandos.jsonl` también seguía actualizándose.
- La telemetría incluía posición, rumbo, rumbo sobre el fondo, velocidad sobre el fondo, distancia a la meta, viento aparente y otras variables.
- Los comandos incluían timón, avance, duración de las órdenes, fuente y nota.

Rutas observadas:

`~/navego_recuperado/timonel/timonel.py`

`~/.local/share/godot/app_userdata/interfaz/timonel/telemetria.jsonl`

`~/.local/share/godot/app_userdata/interfaz/timonel/comandos.jsonl`

Estos archivos constituyen una primera interfaz observable entre el entorno de simulación y el controlador.

## 3. Hallazgo fundamental: ¿quién está manejando el barco?

La inspección del código permitió responder la pregunta que veníamos planteando: ¿maneja Python por sí solo o un LLM le indica a Python qué hacer?

### 3.1. El controlador que se ejecuta actualmente

En `timonel/timonel.py` encontramos una función denominada:

`def timon_python(px, pz, hdg, meta_x=36.0, meta_z=-6.0)`

Esta función calcula una orden de movimiento usando la posición actual, el rumbo y la posición de la meta.

Su lógica observada es la siguiente:

1. Calcula la distancia a la meta.
2. Calcula el ángulo hacia la meta.
3. Compara ese ángulo con el rumbo actual.
4. Decide si debe aplicar timón a un lado, al otro o mantenerlo en cero.
5. Decide si debe aplicar avance según el desvío angular.
6. Cuando la distancia es inferior a 10 metros, devuelve timón cero y avance cero.

La zona de llegada está definida por:

`if dist < 10.0: return 0, 0`

La lógica de timón utiliza un umbral de 15 grados. La lógica de avance detiene el impulso cuando el error angular supera los 45 grados.

En el ciclo principal, `main()`, el programa lee la telemetría y llama directamente a `timon_python()`. Después escribe el resultado en `comandos.jsonl` con `fuente="python"`.

Cada ciclo utiliza un intervalo configurado de tres segundos y escribe órdenes con duraciones de 1.500 milisegundos.

Por lo tanto, el comportamiento observado corresponde al funcionamiento de un controlador Python basado en reglas, ejecutándose dentro de un entorno dinámico.

### 3.2. ¿Dónde está el LLM?

El código también contiene una función llamada `consultar_dsh(muestras)`.

Esta función construye un prompt con variables de navegación y realiza una solicitud HTTP a Ollama. El modelo configurado en `timonel.py` es `qwen2.5-coder:3b`, a través de `/api/generate`.

Sin embargo, **la función está definida, pero el ciclo principal que inspeccionamos no la llama**. El ciclo utiliza `timon_python()`.

Por eso no debemos afirmar que el Qwen 3B estaba conduciendo a Polaris durante esta prueba. El código inspeccionado indica lo contrario.

También existe `timonel/agente_llm.py`, que contiene una integración separada con Ollama y una interfaz para solicitar decisiones de navegación de alto nivel. Allí aparecen acciones como `corregir_rumbo`, `ir_a_punto`, `frenar` y `terminar`.

La existencia de esa integración no demuestra que esté conectada al lazo de control que condujo a Polaris en esta sesión.

### 3.3. Conclusión técnica

La arquitectura actual contiene componentes de control determinista y componentes de decisión mediante LLM, pero no están necesariamente conectados entre sí en la ruta de ejecución activa.

Esto no invalida el experimento. Nos permite establecer una línea base:

- **Controlador actual:** Python determinista.
- **Entorno de prueba observado:** Godot/Polaris.
- **Interfaz observable:** archivos JSONL de telemetría y comandos.
- **Integración LLM:** existe código, pero falta demostrar su participación efectiva en el lazo de navegación activo.
- **Aprendizaje automático:** no queda demostrado por la prueba de aproximación al muelle.

Antes de atribuir al LLM una mejora de navegación, debemos verificar qué proceso está tomando las decisiones y registrar explícitamente su fuente.

## 4. Aporte de Godot al sistema

Godot no aporta solamente una representación visual del barco. Puede convertirse en un laboratorio físico y geométrico para probar decisiones de navegación.

### 4.1. Laboratorio físico

Permite observar la trayectoria, la orientación, las oscilaciones y las interacciones entre la embarcación y el entorno.

Podemos reproducir una situación y observar cómo cambia al modificar una condición. Si la física está suficientemente instrumentada, podemos estudiar los efectos de viento, corriente, inercia y otras fuerzas simuladas.

### 4.2. Banco de obstáculos

Godot puede representar boyas, muelles, paredes, embarcaciones, corredores y otros objetos.

No obstante, debemos comprobar que los objetos tienen colisiones físicas y que el controlador recibe información suficiente para detectarlos. Ver un objeto en pantalla no significa que Timonel sepa que existe.

La navegación entre obstáculos requerirá observaciones del entorno, una representación geométrica útil para decidir y un mecanismo para rechazar maniobras inseguras.

### 4.3. Inspección visual de fallos

Podemos relacionar las órdenes, el rumbo y la trayectoria observada en pantalla. Eso facilita detectar por qué una maniobra falló, dónde comenzó a derivar o qué obstáculo dejó demasiado cerca.

La representación visual debe servir para inspeccionar y comprender el comportamiento, no para sustituir las mediciones.

### 4.4. Límites del simulador

Un mundo tridimensional no es automáticamente un modelo náutico realista.

Para simular correctamente el riesgo de encallamiento, por ejemplo, hacen falta un fondo con profundidades, un calado de la embarcación y una regla que determine cuándo la profundidad disponible es insuficiente.

Del mismo modo, el movimiento del agua debe estar implementado en la física si queremos estudiar sus efectos. No debemos suponer que una variable meteorológica o un objeto visual produce efectos físicos si no comprobamos que el simulador los aplica.

## 5. Arquitectura objetivo

La arquitectura de trabajo acordada separa responsabilidades. No requiere una estructura de múltiples agentes autónomos: propone roles con interfaces intercambiables.

La separación permite sustituir la implementación de un rol —por ejemplo, un LLM por un motor determinista— sin rehacer todo el sistema.

### 5.1. Entorno: Godot o simulador Python

Responsabilidades:

- Mantener el estado de la embarcación.
- Aplicar la física.
- Representar obstáculos y geometría.
- Producir telemetría.
- Permitir reiniciar y reproducir situaciones experimentales.

### 5.2. Planificador de navegación

Responsabilidades:

- Definir una ruta y puntos intermedios.
- Elegir cómo atravesar un espacio disponible.
- Gestionar aproximaciones al destino.
- Considerar obstáculos, restricciones geométricas y, cuando estén disponibles, restricciones de profundidad.

El planificador no debe confundirse con el controlador de bajo nivel. Elegir una ruta no es lo mismo que ejecutar cada movimiento del timón.

### 5.3. Controlador Python

Responsabilidades:

- Corregir el rumbo.
- Regular el avance.
- Reducir velocidad cuando corresponda.
- Ejecutar las maniobras.
- Aplicar límites y protecciones.
- Mantener una respuesta operativa predecible.

El controlador determinista actual es un candidato natural para la línea base inicial.

### 5.4. LLM y aprendizaje

El LLM puede resultar útil para seleccionar alternativas de navegación, interpretar un estado resumido o proponer una maniobra de alto nivel.

También puede participar en un sistema híbrido en el que el LLM ajuste parámetros dentro de límites definidos y Python conserve la autoridad de ejecución.

El LLM no tiene por qué calcular cada pequeño movimiento del timón. Puede ser más útil cuando tiene que elegir entre alternativas de navegación.

Una política aprendida tampoco debe reemplazar automáticamente al controlador anterior. Debe demostrar su utilidad en pruebas independientes.

### 5.5. Verificación y seguridad

El sistema debe contar con una capa independiente que compruebe si una acción es admisible antes de ejecutarla.

Una orden procedente del LLM no debe ejecutarse simplemente porque el modelo la haya propuesto.

La arquitectura debe contemplar, como mínimo:

- Rechazo de acciones que violen límites de seguridad.
- Validación de parámetros.
- Tratamiento explícito de estados desconocidos.
- Política definida cuando ninguna acción candidata es admisible.
- Abstención cuando no hay información suficiente.
- Registro de las decisiones y los motivos de aceptación o rechazo.

## 6. Ruta de trabajo para las próximas semanas y meses

La planificación debe priorizar resultados medibles y no solamente incorporar más componentes.

### Etapa 0. Contrato, configuración y línea base

Antes de ampliar el sistema, establecer un contrato de misión inequívoco.

Debe incluir:

- Un objeto de configuración de misión inmutable por contexto.
- Identificador y versión.
- Representación canónica y hash SHA-256.
- Procedencia y estado de cada valor.
- Validación explícita de los parámetros.
- Límites y reglas de aceptación.
- Ausencia de valores predeterminados silenciosos que cambien el significado de una misión.

La misma configuración debe ser compartida por el banco de pruebas, el entrenador, el simulador y las acciones.

Hay que preservar el perfil `A2_legacy`, su hash y su semántica de regresión para no cambiar inadvertidamente la interpretación de pruebas anteriores.

En paralelo, debemos congelar y medir el controlador Python actual. Su comportamiento será la referencia contra la que compararemos las versiones futuras.

**Criterio de salida:** la misma situación de entrada produce un resultado reproducible y medible; conocemos los parámetros y podemos identificar exactamente la versión evaluada.

### Etapa 1. Intérprete

El intérprete debe transformar el estado disponible y la misión en una representación estructurada y verificable.

No debe inventar datos que no existan en la telemetría ni ocultar incertidumbres.

**Criterio de salida:** entradas y salidas contractuales, errores detectables y pruebas específicas de interpretación.

### Etapa 2. Verificador aislado

El verificador debe evaluar si las acciones propuestas son admisibles, sin depender de que el componente que las propone sea un LLM o un motor determinista.

La violación de límites, representada por una condición como `boundary_violation`, debe actuar como veto previo y no como un simple criterio de desempate.

Si todas las acciones candidatas son inviables, la política de emergencia debe estar definida explícitamente.

**Criterio de salida:** las acciones peligrosas o inválidas se rechazan de manera reproducible, y los casos sin acciones admisibles tienen una respuesta definida.

### Etapa 3. Decisor alineado

Una vez que existen contrato, intérprete y verificador, se puede evaluar el decisor.

Hay dos alternativas principales:

1. El LLM elige una acción entre las opciones permitidas.
2. El LLM propone ajustes acotados a un controlador y Python conserva la autoridad de ejecución.

No debemos asumir que una opción es superior sin medirla.

Las métricas deben distinguir los errores del intérprete, los rechazos del verificador, la calidad de las decisiones y los fallos de integración.

**Criterio de salida:** comparación con la línea base en un conjunto de situaciones conocidas y otro de situaciones nuevas.

### Etapa 4. Integración en lazo cerrado

El sistema debe integrar observación, decisión, verificación, ejecución y nueva observación.

No basta con que el modelo emita un JSON válido. La orden debe producir un comportamiento útil en el entorno.

Las pruebas deben registrar el estado anterior, la acción propuesta, la acción aceptada, el resultado físico y el estado posterior.

**Criterio de salida:** el lazo completo funciona, los errores se detectan y las métricas de navegación mejoran respecto de la línea base sin degradar la seguridad.

### Hitos de seguridad y abstención

La seguridad y la abstención necesitan hitos explícitos, aunque se trabajen transversalmente:

- **Seguridad:** el sistema no debe ejecutar acciones que violen restricciones obligatorias.
- **Abstención:** debe reconocer cuándo no puede decidir de manera suficientemente fundada.
- **Emergencia:** debe existir una respuesta definida cuando no hay una acción segura disponible.

No debemos considerar estos hitos superados solo porque el barco llegue al destino en un escenario favorable.

## 7. Próximos escenarios de navegación

Una vez consolidada la línea base, las pruebas pueden avanzar desde la aproximación al muelle hacia problemas más difíciles.

### 7.1. Aproximación y mantenimiento de posición

Objetivos:

- Medir la distancia al destino a lo largo del tiempo.
- Distinguir reducción de distancia, sobrepaso y deriva.
- Medir la velocidad residual.
- Comprobar la reacción del controlador ante viento intenso.
- Determinar si las órdenes de frenado tienen el efecto esperado.

La proximidad al muelle no debe tratarse como si el barco estuviera físicamente amarrado.

### 7.2. Interposición de objetos y colisiones

Introducir obstáculos en la ruta y comprobar si el sistema:

- Los detecta.
- Estima su posición relativa.
- Reconoce cuándo una trayectoria deja de ser segura.
- Modifica la ruta o la maniobra.
- Evita colisiones en pruebas repetidas.

Hay que distinguir la detección visual de la detección accesible al controlador. También se debe verificar que las colisiones estén implementadas físicamente en el simulador.

### 7.3. Espacios estrechos

Incorporar corredores y pasos con anchura limitada.

El sistema deberá considerar la geometría de la embarcación, el margen de seguridad, su velocidad y la capacidad de corregir el rumbo.

El éxito no consiste solo en atravesar el paso, sino en hacerlo de forma reproducible y sin vulnerar los márgenes definidos.

### 7.4. Profundidad y encallamiento

Incorporar datos de profundidad y un modelo de calado.

El sistema debe poder determinar cuándo no dispone de profundidad suficiente, cuándo falta información y cuándo debe abstenerse o elegir otra ruta.

Esta capacidad requiere un modelo de fondo y reglas físicas explícitas. No se obtiene automáticamente de una escena 3D.

### 7.5. Combinación de dificultades

Después de validar los escenarios individuales, combinar viento, obstáculos, pasos estrechos y restricciones de profundidad.

Las combinaciones deben aumentar progresivamente en dificultad. Si aparecen fallos, necesitamos poder identificar qué condición los produjo.

## 8. Aprendizaje nocturno y funcionamiento sin Godot

El sistema puede realizar tareas útiles mientras el usuario descansa, pero debemos distinguir tres actividades diferentes.

### 8.1. Análisis offline

Python puede analizar telemetría y comandos almacenados, calcular métricas, clasificar fallos, generar informes y preparar conjuntos de datos sin que Godot esté activo.

Esto no requiere que el barco esté navegando en ese momento.

### 8.2. Entrenamiento con datos existentes

Si disponemos de datos suficientes, etiquetas o una función objetivo definida, un proceso de entrenamiento puede ejecutarse sin Godot.

Sin embargo, el entrenamiento necesita una tarea bien definida, datos adecuados, recursos computacionales y pruebas posteriores. No basta con mantener un proceso abierto durante la noche.

### 8.3. Aprendizaje mediante nuevas experiencias simuladas

Para generar nuevas experiencias físicas, el sistema necesita un entorno capaz de avanzar y devolver observaciones.

Puede ser Godot o un simulador Python, siempre que este último represente adecuadamente las variables relevantes para la tarea.

Por eso propongo investigar primero cuánto podemos hacer con el simulador Python que ya existe. Si permite ejecutar episodios reproducibles, podemos utilizarlo para experimentar más rápidamente y reservar Godot para inspección visual y validación de escenarios.

### 8.4. Condiciones para una ejecución nocturna segura

Antes de dejar un proceso funcionando durante horas, debemos contar con:

- Un conjunto de escenarios delimitado.
- Un registro persistente de entradas, decisiones, resultados y errores.
- Límites de recursos y tiempo.
- Recuperación ante errores.
- Separación entre datos de entrenamiento y datos de evaluación.
- Una política que impida modificar automáticamente el controlador estable.
- Un informe final que permita revisar qué se ejecutó y qué resultados obtuvo.

**No está demostrado todavía que el sistema actual aprenda de manera autónoma durante la noche.** Sí tenemos una base desde la que construir procesos de análisis y experimentación nocturna.

## 9. Evaluación objetiva de resultados

Cada nueva versión debe compararse con una línea base mediante escenarios reproducibles.

Entre las métricas iniciales propongo:

- Porcentaje de llegadas exitosas.
- Tiempo hasta el destino.
- Distancia recorrida.
- Error de posición al llegar.
- Error de rumbo durante la aproximación.
- Velocidad residual en la zona de llegada.
- Número de colisiones.
- Número de violaciones de límites.
- Número de abstenciones y motivos.
- Número de órdenes rechazadas por el verificador.
- Tiempo de cálculo por decisión.
- Errores de comunicación y fallos del lazo.
- Variabilidad entre repeticiones del mismo escenario.

No todas las métricas se aplican a todos los escenarios. Por ejemplo, las colisiones y las violaciones de límites son fundamentales en pruebas con obstáculos, mientras que la velocidad residual y el error de posición son importantes en aproximaciones al muelle.

Los resultados deben separar los casos utilizados para ajustar el sistema de los casos reservados para evaluar si la mejora se generaliza.

## 10. Qué podemos aspirar a lograr en un par de meses

Si dedicamos varias horas de trabajo por día y mantenemos una secuencia ordenada, considero razonable aspirar a los siguientes resultados:

**Primer objetivo:** una línea base de navegación documentada, con mediciones repetibles y una distinción inequívoca entre las decisiones de Python y las del LLM.

**Segundo objetivo:** un entorno experimental con obstáculos y escenarios de dificultad creciente, capaz de producir registros comparables.

**Tercer objetivo:** una arquitectura modular en la que el intérprete, el verificador, el decisor y el controlador puedan probarse por separado.

**Cuarto objetivo:** un proceso de experimentación offline o nocturno que genere resultados auditables sin depender de la presencia del usuario durante cada episodio.

**Quinto objetivo:** una primera comparación rigurosa entre el controlador determinista y una alternativa con LLM o una política aprendida.

Estos objetivos son una planificación, no una garantía de que se alcanzarán en una fecha exacta. El ritmo dependerá de la calidad de la física, la disponibilidad de datos, los errores de integración y los resultados de las pruebas.

No es necesario resolver toda la navegación para conseguir avances significativos. Una mejora medible en un problema acotado ya constituye un resultado útil.

## 11. Principios de ingeniería que debemos conservar

1. **Evidencia por encima de certeza:** registrar qué se observó y qué se infiere.
2. **Separación de responsabilidades:** entorno, interpretación, planificación, decisión, verificación y control no deben confundirse.
3. **Reproducibilidad:** poder repetir una situación y comparar resultados.
4. **Seguridad verificable:** las protecciones no dependen de la buena voluntad del LLM.
5. **Datos persistentes:** conservar telemetría, órdenes, errores y procedencia de los resultados.
6. **Cambios comparables:** medir cada versión contra una referencia conocida.
7. **Aprendizaje controlado:** una política nueva se evalúa antes de reemplazar a la anterior.
8. **Incertidumbre explícita:** si faltan datos para una decisión segura, el sistema debe poder abstenerse.
9. **Modularidad real:** los roles deben tener interfaces que permitan intercambiar sus implementaciones.
10. **No confundir visualización con conocimiento:** que Godot muestre un objeto no significa que el controlador pueda detectarlo.

## 12. Decisiones y acciones pendientes

- [ ] Conservar el controlador Python actual como línea base identificable.
- [ ] Confirmar mediante registros qué componente decide y qué componente ejecuta cada orden.
- [ ] Registrar de forma correlacionada telemetría, comandos, timestamps y resultados.
- [ ] Verificar qué partes de la física de Godot están implementadas y cuáles son solo representación visual.
- [ ] Definir y congelar el contrato de misión y sus parámetros.
- [ ] Establecer pruebas de regresión para el controlador existente.
- [ ] Desarrollar el intérprete y el verificador con pruebas aisladas.
- [ ] Evaluar por separado el decisor LLM y el controlador determinista.
- [ ] Diseñar escenarios de colisión e interposición de objetos.
- [ ] Incorporar corredores estrechos y restricciones de profundidad.
- [ ] Investigar la ejecución de episodios en el simulador Python sin Godot.
- [ ] Definir un procedimiento seguro para análisis y entrenamiento nocturnos.
- [ ] Establecer métricas de éxito, seguridad, estabilidad y coste computacional.
- [ ] Mantener separados los datos de ajuste y los de evaluación final.

## 13. Conclusión

NAVEGO dispone de una base valiosa: una embarcación simulada, un entorno tridimensional, un controlador Python inspeccionable, telemetría persistente y componentes de integración con modelos de lenguaje.

El comportamiento observado de Polaris demuestra que vale la pena investigar y medir el sistema de control en su entorno dinámico. El análisis del código, a su vez, permite precisar que la navegación observada se produjo mediante el controlador determinista de Python, no mediante una decisión del LLM en cada ciclo.

La oportunidad de trabajo está en convertir esta base en un laboratorio experimental de navegación: reproducir situaciones, identificar fallos, comparar controladores, introducir obstáculos, validar restricciones y aprender de resultados registrados.

La meta no es que un LLM haga todo. La meta es construir un sistema en el que cada componente cumpla una función definida, cada mejora pueda medirse y cada afirmación de capacidad tenga evidencia detrás.

**La siguiente etapa no consiste en agregar complejidad por agregarla. Consiste en convertir lo que ya funciona en una referencia medible y utilizarla para desarrollar, paso a paso, navegación más robusta, segura y capaz de generalizar.**
