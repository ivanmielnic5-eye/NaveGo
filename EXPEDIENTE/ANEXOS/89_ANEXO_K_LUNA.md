# ANEXO K — LUNA / ARQUITECTURA DE TRES CAPAS Y NAVEGO-NLU-1

**Fecha:** 2026-10-13
**Origen:** consulta a Luna sobre la arquitectura Intérprete → Verificador → Decisor.
**Contenido:** respuesta completa de Luna, sin resumir.

---

Mi evaluación: es una línea de investigación sólida para NAVEGO, y probablemente más útil que seguir intentando demostrar que un LLM puede reemplazar una regla de Python. Pero hay que separar dos cosas: la arquitectura propuesta es razonable; las afirmaciones sobre Alexa no demuestran, por sí solas, que esa arquitectura sea la mejor para Timonel ni que un modelo de 8B pueda implementarla con suficiente fiabilidad.

El cambio conceptual más importante es este: en vez de preguntarnos si el LLM puede tomar buenas decisiones de navegación, investigamos si puede convertir instrucciones humanas ambiguas o variables en una representación formal que un sistema determinista pueda verificar y ejecutar.

Eso plantea una hipótesis mucho más concreta y permite diseñar un experimento limpio.

## 1. Qué rescataría de la propuesta

Capa 1 — Intérprete LLM

Convierte una instrucción en lenguaje natural en una especificación estructurada: intención, parámetros, restricciones y, si hace falta, incertidumbres.

Capa 2 — Validador Python

Comprueba el esquema, los tipos, los rangos, los campos obligatorios, las contradicciones y las restricciones de seguridad. Puede rechazar una especificación o pedir aclaraciones.

Capa 3 — Decisor y ejecutor determinista

Aplica las reglas formales al estado real de navegación. La ejecución física queda sujeta a interbloqueos y supervisión de seguridad independientes.

Esta separación tiene una ventaja metodológica importante: permite medir por separado si el modelo entendió la instrucción, si el validador detectó una especificación inválida y si el decisor aplicó correctamente la política. Si el sistema falla, podemos localizar la causa en vez de atribuírsela genéricamente al "LLM".

Un matiz: el validador no puede demostrar que una especificación sea semánticamente correcta solo porque el JSON sea válido. `{"intent":"ir_a","rumbo":270}` puede ajustarse al esquema y, aun así, ser incorrecto respecto de lo que pidió el usuario o peligroso en el estado actual.

## 2. La analogía con Alexa es útil, pero tiene límites

La documentación oficial de Alexa confirma que el modelo de interacción se construye con intents, slots, expresiones de ejemplo y, opcionalmente, un modelo de diálogo que puede solicitar, validar y confirmar los datos que faltan. Es un antecedente concreto para diseñar la interfaz formal de Timonel.

Pero haría tres correcciones a la interpretación propuesta:

- Alexa no demuestra que el intérprete tenga que ser un LLM. Su arquitectura de intents y slots es anterior a la ola actual de LLM; el patrón útil es la separación entre comprensión y ejecución, no necesariamente la tecnología concreta usada en la primera capa.
- "Más de 70 modelos" no demuestra que varios modelos especializados sean mejores para NAVEGO. Aunque la cifra y la descripción de Alexa+ sean exactas en su contexto, no prueban que necesitemos múltiples modelos, ni que un modelo pequeño no alcance para el alcance inicial.
- Que Alexa use una arquitectura a escala comercial no valida automáticamente la seguridad de un sistema de navegación. Interpretar "poné las luces al 50 %" y determinar una acción segura con sensores contradictorios, inercia, obstáculos y restricciones físicas son problemas de distinto riesgo.

Por eso tomaría Alexa como referencia arquitectónica, no como evidencia experimental de que nuestra solución ya está validada.

## 3. La pregunta de investigación que formularía

Separaría la hipótesis en dos:

H1a — Capacidad de interpretación. Dado un comando en lenguaje natural y un contrato de acciones definido, ¿puede el modelo de 8B producir una especificación formal semánticamente equivalente a la intención del usuario?

H1b — Valor añadido. ¿Esa interpretación con LLM aporta una ventaja práctica frente a una alternativa competente sin LLM, una vez incluidos validación, errores, latencia, coste y mantenimiento?

Esta distinción importa. Si el LLM transforma correctamente el lenguaje a JSON, eso demuestra una capacidad de interpretación en las condiciones ensayadas; no demuestra todavía que el LLM sea necesario ni que mejore el sistema completo.

Y cambiaría una frase de la propuesta: el decisor Python no debería aplicar ciegamente el intent que recibió. Debe aplicar la política de navegación al estado actual y a las restricciones duras, incluso si eso significa rechazar una instrucción perfectamente interpretada.

## 4. El experimento que haría primero: NAVEGO-NLU-1

No empezaría por probar Alexa entera ni por entrenar otro modelo. Haría un experimento acotado para medir exclusivamente la traducción de lenguaje natural a una especificación formal.

ENTRADA

"Mantené el rumbo, pero si el obstáculo está a menos de 20 metros, frená. No superes los 3 nudos."

SALIDA DEL LLM

{   "intent": "mantener_rumbo",   "constraints": [     {       "condition": "distancia_obstaculo < 20,       "action": "frenar"     },     {       "condition": "true",       "action": "velocidad_maxima",       "value": 3,       "unit": "kn"     }   ],   "missing_fields": [],   "needs_clarification": false }

VERIFICADOR PYTHON

Revisa estructura, unidades, rangos, semántica permitida y compatibilidad con el contrato. Rechaza cualquier campo o acción no admitidos.

DECISOR PYTHON

Recibe una especificación validada y el estado de los sensores. Decide si puede ejecutar una acción permitida, debe rechazarla o necesita más información.

El ejemplo es ilustrativo, no un contrato náutico listo para usar. En particular, hay que definir qué significa `frenar`, cómo se prioriza ante otras condiciones y qué hacer si el sensor de distancia falla. Esos detalles deben fijarse antes de evaluar.

### Diseño mínimo

| Elemento            | Propuesta                                                                                            |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| Contrato            | Un conjunto cerrado de intents, slots, unidades y restricciones permitidas                           |
| Casos               | Comandos simples, combinaciones de restricciones, paráfrasis, ambigüedad y datos ausentes            |
| Referencia correcta | Especificación formal adjudicada por reglas y revisores independientes antes de ejecutar las pruebas |
| Modelo              | El mismo modelo de 8B, con versión, prompt y configuración congelados                                |
| Baseline            | Parser basado en reglas o NLU convencional, más un baseline de entrada ya estructurada               |
| Evaluación          | Exactitud semántica de los campos, errores críticos, abstenciones, latencia y coste                  |
| Ejecución           | Primero en simulación; sin autoridad directa sobre el barco                                          |

El baseline de entrada estructurada es un control de techo, no un competidor equivalente: permite medir cuánto error introduce la interpretación frente al error del resto del sistema. El parser sin LLM sí sirve como competidor, siempre que se diseñe competentemente y se le permita manejar el mismo contrato.

No dividiría aleatoriamente paráfrasis casi idénticas entre entrenamiento y test. Separaría familias de instrucciones, combinaciones de restricciones y formas lingüísticas para reducir la contaminación entre conjuntos.
## 5. Cómo evitar confundir obediencia con comprensión

Incluiría cuatro grupos de pruebas:

1. Paráfrasis semánticamente equivalentes. Variar la formulación sin cambiar la especificación correcta. La salida debería conservar la misma semántica.
2. Contrafactuales. Cambiar un único valor o condición —por ejemplo, 20 a 10 metros— y comprobar que solo cambian los campos correspondientes.
3. Conflictos entre instrucción y estado. Pedir una acción que el estado de navegación vuelve inadmisible. El intérprete puede representar la solicitud; el decisor debe aplicar las restricciones de seguridad independientemente.
4. Información insuficiente o contradictoria. Omitir unidades, introducir sensores en conflicto o usar condiciones ambiguas. El sistema debe pedir aclaración, abstenerse o entrar en el estado seguro definido de antemano, según el caso.

Hay una distinción crucial: que el modelo reproduzca una regla presente en el prompt no es un defecto si su tarea es interpretar ese contrato. Lo que no debemos confundir es esa capacidad con haber aprendido una política general de navegación. Para evaluar la generalización, hay que variar las expresiones y los casos sin cambiar las reglas de referencia; y, en otra fase, variar el contrato de manera controlada.

## 6. Criterios de falsación antes de ejecutar

Preinscribiría criterios por dimensión, sin declarar éxito solo por una exactitud global alta.

- Falla de interpretación: el modelo cambia el significado de una instrucción equivalente, altera una condición crítica o inventa un valor obligatorio.
- Falla de robustez: pequeñas paráfrasis producen especificaciones semánticamente distintas sin justificación.
- Falla de seguridad de la arquitectura: una especificación inválida o una condición de seguridad incumplida consigue llegar a ejecución. La tolerancia para ese tipo de fallo debe fijarse por análisis de riesgo; no asumiría que cero fallos observados equivalen a riesgo cero.
- Sin valor comparativo demostrado: el parser sin LLM alcanza resultados equivalentes con menor coste, menor latencia y mantenimiento comparable.
- Evidencia favorable al LLM: mejora de una métrica práctica predefinida —por ejemplo, cobertura de instrucciones válidas no previstas literalmente— sin degradar las métricas críticas de seguridad.

No fijaría todavía un umbral universal del 95 % ni un tamaño de muestra definitivo. Primero definiría el perfil de riesgo, la tasa de error tolerable y el margen de mejora que justificaría incorporar un modelo.

## 7. Qué sabemos y qué sigue abierto

Respaldado por la documentación de Alexa

Intents, slots, ejemplos de expresiones, validación de valores y diálogos para obtener o confirmar campos faltantes son patrones documentados.

Inferencia de diseño para NAVEGO

Separar interpretación, validación y decisión facilita la auditoría, el aislamiento de fallos y la comparación experimental. Es una hipótesis de ingeniería razonable, pero su eficacia concreta debe medirse.

No demostrado todavía

Que el modelo de 8B interprete comandos náuticos de forma robusta; que generalice a contratos nuevos; que supere a un parser bien diseñado; y que el sistema completo sea seguro en condiciones reales.

## Mi recomendación

Adoptaría el patrón Intérprete → Verificador → Decisor como arquitectura candidata de NAVEGO, pero no afirmaría todavía que es la arquitectura definitiva ni que Alexa la valida para navegación.

El siguiente paso debería ser redactar un contrato mínimo de Timonel y el protocolo de NAVEGO-NLU-1, con los casos, baselines y criterios de falsación congelados antes de evaluar el modelo. Eso conecta la investigación de Alexa con la hipótesis H1 sin mezclar interpretación lingüística, aprendizaje de políticas y control físico.

La pregunta que vale la pena responder primero no es si el LLM puede navegar. Es si convierte lenguaje humano en una representación formal con suficiente fidelidad y ventaja práctica como para justificar su presencia en el sistema.
