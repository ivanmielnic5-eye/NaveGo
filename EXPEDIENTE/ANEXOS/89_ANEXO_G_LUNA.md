# ANEXO G — LUNA / PROPUESTA A3 (ADAPTACION DE CONTRATOS)

**Fecha:** 2026-10-13
**Origen:** consulta a Luna tras el resultado de A2.
**Contenido:** respuesta completa de Luna, sin resumir.

---

## RESPUESTA — Hacia la hipotesis de fondo (H1)

Ivan, mi recomendacion es que el proximo experimento no intente
demostrar que el LLM puede resolver una navegacion mas compleja en
terminos generales. Tiene que aislar una afirmacion mas concreta:

¿Un LLM entrenado puede adaptarse a cambios en el contrato de decision,
sin reentrenamiento, y aportar una ventaja medible frente a un sistema
convencional que recibe la misma informacion y puede actualizarse bajo
las mismas condiciones?

Esta formulacion pone a prueba H1 sin convertir la debilidad artificial
de Python en una ventaja aparente para el LLM.

Hay una distincion central: A2 aporta evidencia favorable a la
capacidad de aprender la regla de Fase 1a, segun los resultados que
compartiste. No demuestra todavia que el LLM sea util como agente de
navegacion. Una regla determinista que ambos sistemas pueden ejecutar
no constituye, por si sola, una ventaja del LLM.

## 1. Que sabemos despues de A2 y que sigue abierto

Resultado respaldado por el informe de A2:

El SFT obtuvo exactitud del 100 por ciento en los conjuntos de
interpolacion y extrapolacion informados mediante puntaje forzado. Los
umbrales efectivos de interpolacion estuvieron a menos de 0,15 m de
los valores objetivo.

Limite de esa conclusion:

La evaluacion principal fue por puntaje forzado. Aunque se informa
concordancia de generacion en 200 casos, falta ver el analisis de
invariancia semantica y los resultados detallados por estrato para
evaluar toda la evidencia.

Hipotesis todavia sin probar:

Que el LLM pueda interpretar cambios de contrato, resolver conflictos
entre restricciones y manejar informacion incompleta mejor que un
baseline convencional competitivo, sin recibir la solucion explicita
en el prompt.

Hay dos matices metodologicos que conservaria en el expediente:

- La diferencia entre A1 y A2 no demuestra que el enmascaramiento haya
  sido la unica causa de la mejora: tambien se corrigio la
  contradiccion del prompt, cambio el banco y cambio el protocolo de
  evaluacion.

- Que el SFT obtenga 100 por ciento para T=6 y T=32 es evidencia
  favorable en esos conjuntos, pero no demuestra generalizacion
  extrapolativa universal. Tampoco basta para caracterizar su
  incertidumbre fuera del dominio evaluado.

Por tanto, documentaria A2 como evidencia de aprendizaje de la regla
bajo las condiciones del experimento, no como validacion global de
Timonel.

## 2. Que dimension conviene probar primero

Coincido con tu eleccion de la dimension 2: adaptacion a cambios de
contrato sin reentrenamiento. Es la mas directa para convertir H1 en
una hipotesis falsable, con una salvedad importante.

Un if escrito para una regla fija no se adapta si cambia la regla.
Pero un motor de politicas configurable si puede hacerlo sin modificar
su codigo, cambiando su configuracion. Comparar el LLM con el primer
sistema seria una prueba artificialmente favorable al LLM.

Por eso separaria dos preguntas:

1. Adaptacion semantica: ¿el LLM puede interpretar una nueva regla
   expresada en lenguaje natural y aplicarla correctamente?

2. Valor practico: ¿esa capacidad ofrece alguna ventaja frente a un
   sistema convencional configurable, considerando exactitud,
   seguridad, esfuerzo de actualizacion y mantenimiento?

La primera evalua una capacidad del LLM. La segunda es la que importa
para H1.

### Tarea minima propuesta: adaptacion a contratos de navegacion

El agente recibe un estado y un contrato que determina cuando puede
declarar una mision terminada y cuando debe continuar navegando.

El contrato inicial usa la regla ya estudiada: d < T implica terminar.

Despues se presentan contratos modificados. Por ejemplo:

- Contrato A: terminar cuando la distancia sea menor que T.
- Contrato B: terminar cuando la distancia sea menor que T y la
  velocidad sea inferior a un limite.
- Contrato C: terminar cuando la distancia sea menor que T, excepto si
  existe un obstaculo en la zona de seguridad.
- Contrato D: ante un sensor critico ausente o contradictorio,
  abstenerse de declarar la mision terminada y solicitar verificacion.

Los contratos B, C y D son ejemplos de diseno experimental, no
capacidades que el proyecto haya demostrado.

La dificultad no deberia provenir de redactar instrucciones confusas.
Debe provenir de tener que aplicar correctamente condiciones nuevas,
combinaciones de condiciones y restricciones de seguridad que no
fueron vistas juntas durante el entrenamiento.

## 3. Como comparar el LLM con Python sin debilitar el baseline

Usaria tres sistemas experimentales.

A. LLM SFT con contrato actualizado. El modelo entrenado recibe el
nuevo contrato en lenguaje natural y el estado actual. No se modifica
el modelo ni se vuelve a entrenar.

B. Motor de politicas Python configurable. Recibe el mismo contrato
representado en una especificacion estructurada equivalente. El codigo
de interpretacion permanece fijo; solo cambia la configuracion de la
politica.

C. Arbol de decision. Se entrena con los datos de referencia
disponibles, sin acceso al conjunto confirmatorio.

Los tres sistemas deben recibir la misma informacion factual del
estado, estar sujetos a las mismas restricciones y evaluarse sobre los
mismos casos.

### Que resultado demostraria valor?

Si el LLM obtiene 99 por ciento y Python 100 por ciento, no hay
evidencia de ventaja decisional del LLM. Podria haber valor en la
interfaz en lenguaje natural, pero habria que medirlo aparte.

Si ambos alcanzan exactitud equivalente, pero el LLM permite que un
operador introduzca contratos nuevos sin intervencion de un
desarrollador, podria existir una ventaja de usabilidad o coste de
adaptacion.

Si el LLM interpreta mal una restriccion critica que el motor Python
aplica correctamente, el resultado seria evidencia en contra de usar
el LLM como decisor autonomo para ese tipo de contrato.

La ventaja no debe definirse como "Python no puede hacerlo". Debe
definirse como una mejora mensurable en una tarea realista, frente a
un baseline competente.

## 4. Protocolo concreto para el proximo experimento

Propongo denominarlo provisionalmente A3 — Adaptacion de contratos sin
reentrenamiento.

### 4.1 Hipotesis

- H1a — Capacidad: el LLM aplica correctamente contratos nuevos sin
  actualizar sus pesos.
- H1b — Valor comparativo: el LLM ofrece una ventaja practica frente
  al motor Python configurable, en al menos una dimension predefinida
  y relevante para el proyecto.
- H0: no se observa esa ventaja bajo las condiciones evaluadas.

H1a y H1b no deben confundirse. Un resultado favorable para H1a no
confirma H1b.

### 4.2 Diseno experimental

Fase 0: Congelar la especificacion. Definir los contratos, las
variables de estado, las acciones validas, las prioridades, las
condiciones de abstencion y las etiquetas de referencia.

Fase 1: Preparar el conjunto confirmatorio. Generar casos nuevos con
combinaciones de condiciones no utilizadas en entrenamiento ni para
ajustar las compuertas.

Fase 2: Evaluacion emparejada. Ejecutar el LLM SFT y los baselines
sobre los mismos casos, con el mismo contrato semantico y las mismas
restricciones.

Fase 3: Medir el valor operativo. Comparar exactitud, errores
criticos, abstenciones correctas, esfuerzo de adaptacion y necesidad
de intervencion humana.

### 4.3 Tamano y composicion

Propongo 1.200 casos confirmatorios, distribuidos en cuatro familias
de contratos, con 300 casos por familia. Es una propuesta inicial, no
un tamano muestral validado estadisticamente.

Las cuatro familias serian:

1. Regla base con cambios en el umbral.
2. Condicion adicional de velocidad.
3. Restriccion de seguridad con prioridad sobre la condicion de
   finalizacion.
4. Informacion incompleta o contradictoria que requiera abstencion o
   verificacion.

Los casos deben estratificarse por proximidad a los umbrales,
combinaciones de variables y resultado esperado. La particion debe
realizarse por escenarios o combinaciones, no simplemente por filas
aleatorias.

La exactitud no debe ser la unica metrica. Deben medirse tambien:
- Errores criticos de seguridad.
- Cumplimiento de las prioridades del contrato.
- Tasa de abstencion y tasa de abstencion incorrecta.
- Sensibilidad a cambios de redaccion equivalentes.
- Coste y tiempo necesarios para introducir un contrato nuevo.

### 4.4 Criterios de falsacion preregistrados

| Criterio | Regla propuesta |
| --- | --- |
| Capacidad de adaptacion | Exactitud global del LLM >= 95 por ciento, con limite inferior del IC del 95 por ciento >= 90. |
| Seguridad | Cero errores criticos observados en el conjunto confirmatorio. |
| Cumplimiento de contrato | Ninguna familia puede quedar oculta detras del promedio global. |
| Robustez de redaccion | Las parafrasis semanticamente equivalentes no deben producir cambios injustificados de accion. |
| Ventaja comparativa | Se define previamente una metrica primaria de valor practico y un margen de relevancia. |

Los umbrales numericos anteriores son propuestas de preregistro, no
valores derivados de A2 ni limites cientificamente calibrados.

Para H1b no basta con superar el 95 por ciento de exactitud. Si el
motor Python tambien lo alcanza, H1b solo puede recibir apoyo si se
demuestra una ventaja practica adicional en la dimension elegida.

## 5. Como distinguir capacidad de obediencia al prompt

Cuatro pruebas complementarias.

A. Contrafactuales del estado. Mantener fijo el contrato y modificar
una variable decisiva del estado.

B. Parafrasis del contrato. Presentar el mismo contrato con redacciones
distintas, sin cambiar su significado.

C. Conflicto entre texto y datos. Incluir casos de control en los que
una descripcion incidental sugiera una accion, pero los datos y el
contrato determinen la contraria.

D. Contratos contradictorios o incompletos. Si faltan datos necesarios
o dos clausulas tienen prioridades incompatibles, el modelo no debe
inventar una resolucion. La salida correcta puede ser abstenerse y
solicitar verificacion.

## 6. Como construir la curva de potencial y limitaciones

Matriz de capacidades, con evidencia positiva, limites conocidos y
estado de validacion.

| Dimension | Evidencia actual | Proxima prueba |
| --- | --- | --- |
| Regla determinista simple | A2 resultados favorables en umbrales no vistos. | Replicacion y analisis de invariancia semantica. |
| Adaptacion a contratos | Sin demostrar. | A3, sin reentrenamiento. |
| Lenguaje natural | No aislado experimentalmente. | Contratos equivalentes con parafrasis y ambiguedad controlada. |
| Informacion incompleta | Sin demostrar. | Casos de abstencion y solicitud de verificacion. |
| Sensores contradictorios | Sin demostrar. | Casos con conflictos de sensores y prioridades explicitas. |
| Conocimiento nautico | Sin demostrar. | Escenarios nauticos con referencias externas. |
| Planificacion y control | Sin demostrar. | Simulacion con restricciones fisicas. |

### Cuando concluir que el LLM no sirve para esta tarea?

Condiciones de falsacion por capacidad y por dominio:

- Adaptacion: si falla sistematicamente al aplicar contratos nuevos,
  pese a que las clausulas son explicitas.
- Ventaja comparativa: si el motor Python alcanza un rendimiento
  equivalente o superior y la interfaz del LLM no produce mejoras
  mensurables.
- Seguridad: si el modelo viola restricciones criticas por encima del
  limite preregistrado.
- Robustez: si pequenas parafrasis o variaciones irrelevantes del
  estado cambian decisiones criticas.

## 7. Como documentar las limitaciones de A1 y A2

Clasificarlas en tres categorias:

- Limitaciones observadas: resultados directamente respaldados por las
  corridas, como el colapso a ir_a en A1.
- Limitaciones metodologicas: condiciones que impiden atribuir una
  causa con seguridad, como los cambios simultaneos entre A1 y A2.
- Capacidades no evaluadas: adaptacion a contratos, manejo de
  ambiguedad, informacion faltante y sensores contradictorios.

La afirmacion de que el enmascaramiento es necesario debe formularse
con cuidado: en A1 se calculo la perdida sobre la secuencia completa y
en A2 se verifico el enmascaramiento. La diferencia entre ambos
resultados es compatible con una mejora metodologica, pero no aisla
causalmente el efecto del enmascaramiento.

## Mi recomendacion final

Avanzaria con A3, centrado en adaptacion de contratos sin
reentrenamiento. No pasaria todavia a una tarea de navegacion fisica
integral.

El resultado de A3 deberia poder terminar en cualquiera de estas tres
conclusiones:

1. El LLM demuestra adaptacion y aporta una ventaja practica medible.
2. El LLM demuestra adaptacion, pero no aporta una ventaja frente al
   baseline competente.
3. El LLM no demuestra adaptacion robusta bajo las condiciones
   preregistradas.

Las tres serian resultados utiles para el proyecto.

Una precision documental: tome los resultados y referencias de A2 tal
como los presentaste, sin ejecutar nada. Para convertir esta propuesta
en una revision definitiva del constructo y de la hipotesis H1,
faltaria contrastarla con el contenido integro del anexo C, las
secciones 19-22 del memo 89 y los anexos E y F.Iván, mi recomendación es que el próximo experimento no intente demostrar que el LLM puede resolver una navegación más compleja en términos generales. Tiene que aislar una afirmación más concreta:

¿Un LLM entrenado puede adaptarse a cambios en el contrato de decisión, sin reentrenamiento, y aportar una ventaja medible frente a un sistema convencional que recibe la misma información y puede actualizarse bajo las mismas condiciones?

Esta formulación pone a prueba H1 sin convertir la debilidad artificial de Python en una ventaja aparente para el LLM.

Hay una distinción central: A2 aporta evidencia favorable a la capacidad de aprender la regla de Fase 1a, según los resultados que compartiste. No demuestra todavía que el LLM sea útil como agente de navegación. Una regla determinista que ambos sistemas pueden ejecutar no constituye, por sí sola, una ventaja del LLM.

## 1. Qué sabemos después de A2 y qué sigue abierto

Resultado respaldado por el informe de A2

El SFT obtuvo exactitud del 100 % en los conjuntos de interpolación y extrapolación informados mediante puntaje forzado. Los umbrales efectivos de interpolación estuvieron a menos de 0,15 m de los valores objetivo.

Límite de esa conclusión

La evaluación principal fue por puntaje forzado. Aunque se informa concordancia de generación en 200 casos, falta ver el análisis de invariancia semántica y los resultados detallados por estrato para evaluar toda la evidencia.

Hipótesis todavía sin probar

Que el LLM pueda interpretar cambios de contrato, resolver conflictos entre restricciones y manejar información incompleta mejor que un baseline convencional competitivo, sin recibir la solución explícita en el prompt.

Hay dos matices metodológicos que conservaría en el expediente:

- La diferencia entre A1 y A2 no demuestra que el enmascaramiento haya sido la única causa de la mejora: también se corrigió la contradicción del prompt, cambió el banco y cambió el protocolo de evaluación.
- Que el SFT obtenga 100 % para \\(T=6\\) y \\(T=32\\) es evidencia favorable en esos conjuntos, pero no demuestra generalización extrapolativa universal. Tampoco basta para caracterizar su incertidumbre fuera del dominio evaluado.

Por tanto, documentaría A2 como evidencia de aprendizaje de la regla bajo las condiciones del experimento, no como validación global de Timonel.

## 2. ¿Qué dimensión conviene probar primero?

Coincido con tu elección de la dimensión 2: adaptación a cambios de contrato sin reentrenamiento. Es la más directa para convertir H1 en una hipótesis falsable, con una salvedad importante.

Un `if` escrito para una regla fija no se adapta si cambia la regla. Pero un motor de políticas configurable sí puede hacerlo sin modificar su código, cambiando su configuración. Comparar el LLM con el primer sistema sería una prueba artificialmente favorable al LLM.

Por eso separaría dos preguntas:

1. Adaptación semántica: ¿el LLM puede interpretar una nueva regla expresada en lenguaje natural y aplicarla correctamente?
2. Valor práctico: ¿esa capacidad ofrece alguna ventaja frente a un sistema convencional configurable, considerando exactitud, seguridad, esfuerzo de actualización y mantenimiento?

La primera evalúa una capacidad del LLM. La segunda es la que importa para H1.

### Tarea mínima propuesta: adaptación a contratos de navegación

El agente recibe un estado y un contrato que determina cuándo puede declarar una misión terminada y cuándo debe continuar navegando.

El contrato inicial usa la regla ya estudiada:

\\[ d\<T \Rightarrow \text{terminar} \\]

Después se presentan contratos modificados. Por ejemplo:

- Contrato A: terminar cuando la distancia sea menor que \\(T\\).
- Contrato B: terminar cuando la distancia sea menor que \\(T\\) y la velocidad sea inferior a un límite.
- Contrato C: terminar cuando la distancia sea menor que \\(T\\), excepto si existe un obstáculo en la zona de seguridad.
- Contrato D: ante un sensor crítico ausente o contradictorio, abstenerse de declarar la misión terminada y solicitar verificación.

Los contratos B, C y D son ejemplos de diseño experimental, no capacidades que el proyecto haya demostrado.

La dificultad no debería provenir de redactar instrucciones confusas. Debe provenir de tener que aplicar correctamente condiciones nuevas, combinaciones de condiciones y restricciones de seguridad que no fueron vistas juntas durante el entrenamiento.

## 3. Cómo comparar el LLM con Python sin debilitar el baseline

Usaría tres sistemas experimentales.

A. LLM SFT con contrato actualizado

El modelo entrenado recibe el nuevo contrato en lenguaje natural y el estado actual. No se modifica el modelo ni se vuelve a entrenar.

B. Motor de políticas Python configurable

Recibe el mismo contrato representado en una especificación estructurada equivalente. El código de interpretación permanece fijo; solo cambia la configuración de la política.

C. Árbol de decisión

Se entrena con los datos de referencia disponibles, sin acceso al conjunto confirmatorio. Sirve para medir cuánto puede resolverse mediante aprendizaje convencional sobre las mismas variables.

Los tres sistemas deben recibir la misma información factual del estado, estar sujetos a las mismas restricciones y evaluarse sobre los mismos casos. La representación del contrato puede diferir según el método, pero su semántica debe verificarse independientemente.

El árbol de decisión es un baseline útil, pero no sustituye al motor configurable: responde a una pregunta distinta. Tampoco usaría un controlador PID o un MPC como baseline principal de esta primera prueba. PID y MPC tienen sentido cuando se evalúa control dinámico, trayectoria y restricciones físicas; no son comparadores directos de interpretación de contratos en lenguaje natural.

### ¿Qué resultado demostraría valor?

Si el LLM obtiene 99 % y Python 100 %, no hay evidencia de ventaja decisional del LLM. Podría haber valor en la interfaz en lenguaje natural, pero habría que medirlo aparte.

Si ambos alcanzan exactitud equivalente, pero el LLM permite que un operador introduzca contratos nuevos sin intervención de un desarrollador, podría existir una ventaja de usabilidad o coste de adaptación. Habría que medir el tiempo humano, los errores de especificación y la necesidad de revisión.

Si el LLM interpreta mal una restricción crítica que el motor Python aplica correctamente, el resultado sería evidencia en contra de usar el LLM como decisor autónomo para ese tipo de contrato.

La ventaja no debe definirse como «Python no puede hacerlo». Debe definirse como una mejora mensurable en una tarea realista, frente a un baseline competente.

## 4. Protocolo concreto para el próximo experimento

Propongo denominarlo provisionalmente A3 — Adaptación de contratos sin reentrenamiento. El nombre es una propuesta; no presupone una decisión documental del proyecto.

### 4.1 Hipótesis

- H1a — Capacidad: el LLM aplica correctamente contratos nuevos sin actualizar sus pesos.
- H1b — Valor comparativo: el LLM ofrece una ventaja práctica frente al motor Python configurable, en al menos una dimensión predefinida y relevante para el proyecto.
- H0: no se observa esa ventaja bajo las condiciones evaluadas.

H1a y H1b no deben confundirse. Un resultado favorable para H1a no confirma H1b.

### 4.2 Diseño experimental

### Diseño propuesto

Fase 0

Congelar la especificación

Definir los contratos, las variables de estado, las acciones válidas, las prioridades, las condiciones de abstención y las etiquetas de referencia.

Fase 1

Preparar el conjunto confirmatorio

Generar casos nuevos con combinaciones de condiciones no utilizadas en entrenamiento ni para ajustar las compuertas.

Fase 2

Evaluación emparejada

Ejecutar el LLM SFT y los baselines sobre los mismos casos, con el mismo contrato semántico y las mismas restricciones.

Fase 3

Medir el valor operativo

Comparar exactitud, errores críticos, abstenciones correctas, esfuerzo de adaptación y necesidad de intervención humana.

### 4.3 Tamaño y composición

Como punto de partida para la planificación, propongo 1.200 casos confirmatorios, distribuidos en cuatro familias de contratos, con 300 casos por familia. Es una propuesta inicial, no un tamaño muestral validado estadísticamente.

Las cuatro familias serían:

1. Regla base con cambios en el umbral.
2. Condición adicional de velocidad.
3. Restricción de seguridad con prioridad sobre la condición de finalización.
4. Información incompleta o contradictoria que requiera abstención o verificación.

Los casos deben estratificarse por proximidad a los umbrales, combinaciones de variables y resultado esperado. La partición debe realizarse por escenarios o combinaciones, no simplemente por filas aleatorias, para evitar que variantes casi idénticas aparezcan en entrenamiento y prueba.

La exactitud no debe ser la única métrica. Deben medirse también:

- Errores críticos de seguridad.
- Cumplimiento de las prioridades del contrato.
- Tasa de abstención y tasa de abstención incorrecta.
- Sensibilidad a cambios de redacción equivalentes.
- Coste y tiempo necesarios para introducir un contrato nuevo.

### 4.4 Criterios de falsación preregistrados

Antes de generar o consultar los resultados confirmatorios, dejaría definidos los siguientes criterios provisionales:

| Criterio                 | Regla propuesta                                                                                                                      |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Capacidad de adaptación  | Exactitud global del LLM ≥ 95 %, con límite inferior del IC del 95 % ≥ 90 %.                                                         |
| Seguridad                | Cero errores críticos observados en el conjunto confirmatorio.                                                                       |
| Cumplimiento de contrato | Ninguna familia puede quedar oculta detrás del promedio global; se informan resultados individuales.                                 |
| Robustez de redacción    | Las paráfrasis semánticamente equivalentes no deben producir cambios injustificados de acción.                                       |
| Ventaja comparativa      | Se define previamente una métrica primaria de valor práctico y un margen de relevancia, comparando con el motor Python configurable. |

Los umbrales numéricos anteriores son propuestas de preregistro, no valores derivados de A2 ni límites científicamente calibrados. Deben revisarse antes de ejecutar A3.

En particular, cero errores críticos observados no demuestra que la tasa real de error sea cero. La incertidumbre debe informarse y el tamaño muestral debe calcularse en función de la tasa de fallo que se pretenda descartar.

Para H1b no basta con superar el 95 % de exactitud. Si el motor Python también lo alcanza, H1b solo puede recibir apoyo si se demuestra una ventaja práctica adicional en la dimensión elegida. Si no aparece esa ventaja, H1b no queda respaldada aunque H1a resulte favorable.

## 5. Cómo distinguir capacidad de obediencia al prompt

Este control es fundamental porque un LLM puede parecer competente cuando la respuesta está sugerida por la redacción, incluso si no integra correctamente el estado.

Usaría cuatro pruebas complementarias.

A. Contrafactuales del estado. Mantener fijo el contrato y modificar una variable decisiva del estado. La acción debe cambiar cuando la regla lo exige y mantenerse cuando la variable no es relevante.

B. Paráfrasis del contrato. Presentar el mismo contrato con redacciones distintas, sin cambiar su significado. Medir la tasa de decisiones semánticamente equivalentes.

C. Conflicto entre texto y datos. Incluir casos de control en los que una descripción incidental o una formulación contextual sugiera una acción, pero los datos y el contrato determinen la contraria. La etiqueta de referencia debe derivarse del contrato formal, no de una preferencia subjetiva del evaluador.

D. Contratos contradictorios o incompletos. Si faltan datos necesarios o dos cláusulas tienen prioridades incompatibles, el modelo no debe inventar una resolución. La salida correcta puede ser abstenerse y solicitar verificación.

Conviene distinguir entre las condiciones de evaluación y el prompt de instrucción: el contrato debe aportar las reglas de la tarea, mientras que la plantilla de instrucción debe limitarse a describir el formato de salida y las restricciones generales. Si el prompt incluye ejemplos que revelan las respuestas del conjunto confirmatorio, la prueba deja de ser válida.

También compararía las decisiones del modelo con un evaluador determinista independiente que aplique la especificación formal. El evaluador debe permanecer oculto al modelo durante la inferencia y generar las etiquetas antes de observar sus resultados.

## 6. Cómo construir la curva de potencial y limitaciones de Timonel

No intentaría condensar toda la capacidad del agente en una sola puntuación. Construiría una matriz de capacidades, con evidencia positiva, límites conocidos y estado de validación.

| Dimensión                 | Evidencia actual                                        | Próxima prueba                                                                  |
| ------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Regla determinista simple | A2 informa resultados favorables en umbrales no vistos. | Replicación y análisis de invariancia semántica.                                |
| Adaptación a contratos    | Sin demostrar.                                          | A3, sin reentrenamiento.                                                        |
| Lenguaje natural          | No aislado experimentalmente.                           | Contratos equivalentes con paráfrasis y ambigüedad controlada.                  |
| Información incompleta    | Sin demostrar.                                          | Casos de abstención y solicitud de verificación.                                |
| Sensores contradictorios  | Sin demostrar.                                          | Casos con conflictos de sensores y prioridades explícitas.                      |
| Conocimiento náutico      | Sin demostrar.                                          | Escenarios náuticos con referencias externas y evaluación independiente.        |
| Planificación y control   | Sin demostrar.                                          | Simulación con restricciones físicas y comparación con controladores adecuados. |

Esta matriz debería registrar, para cada dimensión, el dominio evaluado, los datos utilizados, los baselines, el tamaño de muestra, las métricas, los intervalos de confianza, los fallos y las condiciones bajo las cuales la conclusión deja de ser válida.

### ¿Cuándo concluir que el LLM no sirve para esta tarea?

No concluiría que «el LLM no sirve» después de un único experimento fallido. Sí establecería condiciones de falsación por capacidad y por dominio.

Por ejemplo:

- Adaptación: si falla sistemáticamente al aplicar contratos nuevos, pese a que las cláusulas son explícitas y el pipeline está validado, la hipótesis de adaptación sin reentrenamiento pierde apoyo.
- Ventaja comparativa: si el motor Python alcanza un rendimiento equivalente o superior y la interfaz del LLM no produce mejoras mensurables de coste, usabilidad o mantenimiento, no habría evidencia de valor adicional en esa dimensión.
- Seguridad: si el modelo viola restricciones críticas por encima del límite preregistrado, no debe utilizarse como decisor autónomo en ese dominio.
- Robustez: si pequeñas paráfrasis o variaciones irrelevantes del estado cambian decisiones críticas, la capacidad no es suficientemente estable para ese uso.

Las conclusiones deben quedar acotadas: «no demuestra utilidad para adaptación de contratos en las condiciones ensayadas» es defendible; «los LLM no sirven para navegación» no lo sería.

## 7. Cómo documentar las limitaciones de A1 y A2

Las limitaciones deben formar parte del constructo de Timonel, no quedar relegadas a observaciones informales.

Recomiendo clasificarlas en tres categorías:

- Limitaciones observadas: resultados directamente respaldados por las corridas, como el colapso a `ir_a` en A1 bajo el protocolo descrito.
- Limitaciones metodológicas: condiciones que impiden atribuir una causa con seguridad, como los cambios simultáneos entre A1 y A2.
- Capacidades no evaluadas: adaptación a contratos, manejo de ambigüedad, información faltante y sensores contradictorios.

La afirmación de que el enmascaramiento es necesario para que el loss sea informativo debe formularse con cuidado: en A1 se calculó la pérdida sobre la secuencia completa y en A2 se verificó el enmascaramiento de los tokens de respuesta. La diferencia entre ambos resultados es compatible con una mejora metodológica, pero no aísla causalmente el efecto del enmascaramiento.

## Mi recomendación final

Avanzaría con A3, centrado en adaptación de contratos sin reentrenamiento. No pasaría todavía a una tarea de navegación física integral: primero necesitamos saber si el LLM interpreta contratos cambiantes de manera robusta y si esa capacidad aporta algo que un sistema convencional configurable no proporcione.

El resultado de A3 debería poder terminar en cualquiera de estas tres conclusiones:

1. El LLM demuestra adaptación y aporta una ventaja práctica medible.
2. El LLM demuestra adaptación, pero no aporta una ventaja frente al baseline competente.
3. El LLM no demuestra adaptación robusta bajo las condiciones preregistradas.

Las tres serían resultados útiles para el proyecto. Ninguna debe darse por decidida antes del experimento.

Una precisión documental: tomé los resultados y referencias de A2 tal como los presentaste, sin ejecutar nada. Para convertir esta propuesta en una revisión definitiva del constructo y de la hipótesis H1, faltaría contrastarla con el contenido íntegro del anexo C, las secciones 19–22 del memo 89 y los anexos E y F. No asumiría que las recomendaciones de esta respuesta ya fueron incorporadas al expediente ni que A3 está formalmente aprobado.