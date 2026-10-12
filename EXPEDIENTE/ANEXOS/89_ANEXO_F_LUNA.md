# ANEXO F — LUNA / REVISION DE LA PROPUESTA DE CLAUDE

**Fecha:** 2026-10-12
**Origen:** consulta a Luna sobre la propuesta de Claude (anexo E) tras el cierre de Banco A.
**Contenido:** respuesta completa de Luna, sin resumir.

---

## RESPUESTA — Revision tecnica de las ocho dudas

Ivan, el documento que adjuntaste cambia de manera importante la
evaluacion de Banco A. Voy a separar los problemas metodologicos de
las decisiones de diseno, porque no conviene implementar la corrida
A2 hasta resolver los primeros.

[...PEGAR ACA TODO EL TEXTO DE LUNA, DESDE "Hay dos hechos
especialmente relevantes..." HASTA EL FINAL "...limitacion real del
modelo para generalizar la regla."]Iván, el documento que adjuntaste cambia de manera importante la evaluación de Banco A. Voy a separar los problemas metodológicos de las decisiones de diseño, porque no conviene implementar la corrida A2 hasta resolver los primeros.

Hay dos hechos especialmente relevantes en el material:

- La comparación del 52,3 % frente al 51,5 % no es una comparación controlada entre el modelo base y el SFT. Se utilizaron infraestructuras diferentes, por lo que esa diferencia no permite atribuir el resultado exclusivamente al entrenamiento.
- El SFT A1 calculó la pérdida sobre la secuencia completa, incluidos los prompts. Por eso, el `loss = 0,053` no demuestra que el modelo haya aprendido la regla de decisión; podría reflejar, en parte, el aprendizaje del formato y de los tokens de entrada.

También hay un tercer punto importante en el código: el evaluador extrae el primer `1` o `2` que encuentra en la respuesta. Eso puede ocultar salidas malformadas. Además, cuando las decisiones de las dos presentaciones no coinciden, el resultado se marca como inconsistente y cuenta como fallo en `acierto`. Hay que medir ambos fenómenos por separado.

## Revisión técnica de las ocho dudas

Base de análisis: el expediente adjunto, el código completo de `runner_banco_A.py` y los antecedentes recuperados del proyecto. No ejecuté código ni modifiqué archivos. No dispongo del contenido íntegro del anexo E en este mensaje, así que evalúo los criterios de Claude que aparecen transcritos, no cada detalle de su implementación.

### 1. ¿El colapso a `ir_a` demuestra que el SFT no aprendió?

Veredicto: el colapso es evidencia de que el sistema evaluado no demuestra la capacidad buscada; todavía no identifica por sí solo la causa.

Hechos documentados:

- El modelo base obtuvo 52,3 % en 750 casos confirmatorios mediante Ollama.
- El SFT obtuvo 51,5 % en 200 casos de validación mediante Hugging Face.
- El SFT predijo la clase `2` en todos los fallos descritos y su porcentaje coincide con la proporción de esa clase.
- El entrenamiento no enmascaró los prompts.

No es correcto concluir que las diferencias de infraestructura explican el colapso. Son una fuente de confusión experimental, no una explicación demostrada.

Tampoco es correcto concluir que el modelo necesariamente no aprendió nada. Podría haber aprendido patrones que la evaluación no detecta, aunque la evidencia actual no demuestra que los haya aprendido.

Verificación necesaria, en este orden:

1. Auditar el parser y comprobar las salidas crudas del SFT. El código usa `re.search(r"[12]", texto)`, que acepta el primer dígito encontrado, incluso si la salida contiene texto adicional. Debe medirse la tasa de respuestas válidas y no válidas por separado.
2. Ejecutar base y SFT sobre los mismos ejemplos, con la misma plantilla, tokenización, precisión numérica, política de generación y decodificación.
3. Verificar el contrabalanceo semántico: al invertir las posiciones de las acciones, la acción elegida debería mantenerse, aunque cambie el número.
4. Medir la sensibilidad a \\(T\\), incluyendo los valores no vistos, y estimar el umbral efectivo del modelo.

Hay además una anomalía previa que merece atención: el propósito original exige distancia menor que \\(T\\) y baja velocidad, mientras que el estado y las etiquetas solo utilizan distancia y umbral. Esta contradicción puede introducir ambigüedad, pero no está demostrado que explique por sí sola el colapso.

### 2. ¿Conviene ampliar los valores de \\(T\\) de 4 a 11 durante el entrenamiento?

Veredicto: coincido parcialmente con Claude. Ampliar los valores es razonable, pero no demuestra por sí mismo que el modelo aprendió una regla general.

Un conjunto más amplio de umbrales puede reducir la posibilidad de que el modelo memorice cuatro valores concretos. Sin embargo, once valores también pueden memorizarse. La cantidad de valores no garantiza generalización.

La prueba debe conservar tres propiedades:

- Los umbrales de evaluación confirmatoria deben ser distintos de todos los usados durante el entrenamiento.
- Los ejemplos deben cubrir distancias a ambos lados del umbral, incluyendo la zona crítica.
- La distribución de etiquetas debe estar equilibrada o, como mínimo, documentada para evitar que predecir siempre una clase parezca un resultado aceptable.

El costo oculto es que, si se mantiene fijo el presupuesto de entrenamiento, aumentar la diversidad de umbrales puede reducir la cantidad de ejemplos por umbral o por estrato. También cambia el experimento respecto de A1, de modo que A2 no debe presentarse como una simple corrección aislada de un único defecto.

Recomendación: ampliar los valores de \\(T\\) puede formar parte de A2, pero el criterio de éxito debe ser que el umbral efectivo siga al umbral presentado en valores nunca vistos, no simplemente que aumente la exactitud.

### 3. ¿Mostrar \\(d\\) con un decimal o con ocho decimales?

Veredicto: no es indistinto. Coincido con la exigencia de consistencia de los datos, pero no considero que ocho decimales sean universalmente necesarios.

La condición fundamental es que la etiqueta se calcule utilizando exactamente el valor que ve el modelo.

Por ejemplo, supongamos que la distancia interna es 14,96 m y \\(T=15,00\\) m.

- Si se muestra `15,0`, la comparación visible indica que \\(d=T\\), por lo que la etiqueta es `ir_a`.
- Si se muestra `14,96000000`, la comparación indica \\(d\<T\\), por lo que la etiqueta es `terminar`.

Si se etiqueta usando la distancia interna y se muestra un valor redondeado que cambia la relación con \\(T\\), el conjunto de entrenamiento contiene contradicciones.

Mi recomendación es:

- Definir una representación decimal determinista para \\(d\\) y \\(T\\).
- Calcular las etiquetas a partir de los valores representados.
- Evitar que los casos cercanos al umbral se etiqueten de forma incoherente.
- Evaluar por separado la sensibilidad a la precisión numérica.

Ocho decimales ofrecen una representación precisa, pero no necesariamente más útil para el modelo. Un decimal podría bastar para una tarea definida a esa resolución, siempre que se regenere el banco de manera coherente.

### 4. ¿Puntaje forzado o generación de respuestas?

Veredicto: el puntaje forzado es válido como medida principal de preferencia entre las dos respuestas, pero no sustituye completamente la evaluación mediante generación.

Con forced-choice scoring se comparan las probabilidades asignadas a las respuestas candidatas, condicionadas al mismo contexto. Esto permite evaluar qué opción prefiere el modelo sin depender de que produzca una salida bien formada.

Sus ventajas son:

- Menos dependencia de errores de formato y del parser.
- Comparación cuantitativa de las alternativas.
- Mayor facilidad para analizar cambios de preferencia entre base y SFT.

Sus limitaciones son importantes:

- Una respuesta puede recibir mayor probabilidad que otra sin que el modelo la genere efectivamente con la política de decodificación elegida.
- Las probabilidades de secuencias completas pueden favorecer respuestas según su longitud y tokenización.
- Si se puntúan los números `1` y `2`, el resultado puede reflejar sesgos de token, no comprensión de la acción semántica.

La implementación debe puntuar las respuestas exactas `1` y `2`, con el mismo prefijo y una normalización documentada. Conviene comprobar también los identificadores de tokens y la probabilidad del siguiente token en el punto de decisión.

Coincido con Claude en usar el puntaje forzado como evaluación principal, siempre que la generación siga siendo una comprobación independiente. Una muestra de 40 casos puede servir como control de humo, pero es insuficiente para demostrar una concordancia de al menos 98 % con precisión estadística sólida. Esa muestra debe incluir ambos órdenes, casos cercanos al umbral y casos lejanos.

### 5. ¿Son razonables las compuertas propuestas?

Claude propone:

| Criterio                               | Evaluación                                                                                 |
| -------------------------------------- | ------------------------------------------------------------------------------------------ |
| `train ≥ 0,99`                         | Insuficiente como prueba de aprendizaje; puede reflejar memorización.                      |
| `AUC val ≥ 0,60`                       | Umbral provisional posible, pero no demuestra generalización ni seguimiento de \\(T\\).    |
| Concordancia generación/puntaje ≥ 0,98 | Útil como control técnico, pero necesita tamaño muestral y tolerancia definidos.           |
| Exactitud lejana ≥ 0,95                | Útil para comprobar casos sencillos, aunque puede ocultar fallos cerca del umbral.         |
| \\(\|\hat T-T\| ≤ 1,0\\) m             | Potencialmente útil, pero debe definirse cómo se estima \\(\hat T\\) y en qué condiciones. |

No aprobaría estas cinco cifras como compuertas definitivas sin una justificación previa. No son necesariamente malas, pero el expediente disponible no demuestra que estén calibradas para el objetivo.

Para Fase 1a, las compuertas principales deberían evaluar:

1. Seguimiento del umbral efectivo respecto de \\(T\\).
2. Desempeño sobre umbrales no vistos.
3. Comportamiento a ambos lados de \\(T\\).
4. Invariancia semántica al invertir el orden de las acciones.
5. Diferencia entre el modelo base y el SFT bajo condiciones emparejadas.

La exactitud global y el loss deben ser métricas complementarias. La decisión de éxito o fracaso debe basarse en criterios definidos antes de observar los resultados confirmatorios.

### 6. ¿Excluir los casos con \\(|d-T|<0,3\\) m?

Veredicto: no los excluiría del experimento completo.

La exclusión puede servir para un análisis secundario de casos no ambiguos, pero elimina precisamente la región que permite medir si el umbral efectivo está donde debería estar.

Propongo tres estratos:

- Lejanos: casos claramente por debajo o por encima de \\(T\\).
- Cercanos: casos dentro de una distancia definida del umbral.
- Exactos: casos en los que el valor representado satisface \\(d=T\\).

La igualdad debe seguir la regla ya documentada: \\(d\<T\\) implica `terminar`; \\(d\geq T\\) implica `ir_a`.

Se puede excluir una banda de la métrica principal de exactitud robusta si hay una justificación previa, pero los casos excluidos deben mantenerse en un análisis crítico separado. Si desaparecen por completo del banco confirmatorio, se debilita la prueba central de Fase 1a.

### 7. ¿Basta con añadir `train_on_responses_only`?

Veredicto: no. Coincido con Claude en incorporar el enmascaramiento, pero debe verificarse que funcione sobre el formato real.

No basta con que la función se ejecute sin errores. Hay que comprobar el resultado efectivo de la construcción de etiquetas de entrenamiento.

Controles mínimos:

1. Versión y compatibilidad: registrar las versiones exactas de Unsloth, TRL, Transformers y el modelo/tokenizer.
2. Separadores reales: identificar en la plantilla de Llama 3.1 los límites exactos entre instrucciones, contenido del usuario y respuesta del asistente.
3. Máscara efectiva: inspeccionar varios ejemplos tokenizados y verificar que los tokens del prompt tienen etiqueta `-100`, mientras que los tokens de la respuesta que deben entrenarse conservan sus etiquetas.
4. Respuesta vacía o máscara incorrecta: comprobar que no se esté entrenando accidentalmente con cero tokens de respuesta, o con una porción distinta de la prevista.
5. Formato de datos: verificar que el texto de entrenamiento coincide con el formato usado para generar las respuestas y que la secuencia no introduce delimitadores duplicados.
6. Prueba de regresión: guardar ejemplos de entrada, tokens, máscaras y etiquetas para poder reproducir la comprobación.

El loss debe volver a medirse después de aplicar la máscara. No hay que comparar directamente el `loss = 0,053` de A1 con el de A2 como si midieran exactamente lo mismo.

Además, el enmascaramiento no corrige por sí solo la contradicción sobre la velocidad ni la inconsistencia potencial entre la distancia mostrada y la etiqueta.

### 8. ¿La baja velocidad pertenece a Fase 1a o a Fase 1b?

Veredicto: recomiendo retirarla del objetivo operativo de Fase 1a y tratarla como una capacidad separada hasta que exista una decisión explícita del Director.

La justificación es experimental, no semántica:

- Las etiquetas actuales dependen únicamente de \\(d\\) y \\(T\\).
- El estado que recibe el modelo no incluye velocidad.
- El prompt original exige una condición adicional que el experimento no implementa.

Por tanto, no se puede evaluar correctamente la aplicación del criterio documentado mientras el texto exija una variable que no está presente en los datos.

La decisión de incluir velocidad en una fase posterior no significa que sea irrelevante para la navegación real. Significa que hay que definir otro constructo, con velocidad explícita en el estado, etiquetas que incorporen esa variable y pruebas de interacción entre distancia y velocidad.

Si el Director decide que la baja velocidad es esencial para Fase 1a, hay que actualizar coherentemente el objetivo, el estado, las etiquetas y los criterios de evaluación antes de entrenar.

## Recomendación consolidada para A2

Mi conclusión es que la propuesta de Claude es una buena base de trabajo, pero no aprobaría su implementación sin corregir y verificar primero el diseño de evaluación.

## Orden recomendado de trabajo

1. Auditar el parser, las salidas crudas y la plantilla de evaluación de A1.
2. Definir el contrato exacto de entrada, representación decimal y etiquetas, sin la condición de velocidad.
3. Diseñar los splits y fijar previamente las métricas y compuertas, reservando los umbrales confirmatorios no vistos.
4. Implementar y verificar el enmascaramiento de respuestas con inspección de tokens y etiquetas.
5. Entrenar A2 y evaluar base y SFT de forma emparejada, con puntaje forzado y comprobación de generación.
6. Analizar por separado los casos lejanos, cercanos y exactos, y decidir con los resultados si se cumple Fase 1a.

### Lo que todavía no está demostrado

- Que la diferencia de infraestructura sea la causa del colapso.
- Que once umbrales de entrenamiento sean la configuración óptima.
- Que los umbrales numéricos de las compuertas de Claude estén calibrados.
- Que el puntaje forzado y la generación concuerden suficientemente en el conjunto completo.
- Que el enmascaramiento propuesto sea correcto para las versiones y plantillas exactas del entorno de entrenamiento.

El siguiente paso no es ejecutar A2 inmediatamente, sino cerrar esas especificaciones y convertirlas en controles reproducibles. Así, si A2 vuelve a fallar, podremos distinguir entre un defecto del pipeline, un problema de entrenamiento y una limitación real del modelo para generalizar la regla.