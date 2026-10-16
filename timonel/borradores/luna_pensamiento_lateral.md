# Evaluación lateral — Arquitectura de comunicación de Timonel

Veredicto general: las ideas 1 y 3 contienen posibilidades técnicas reales; la 2 es una metáfora que puede inspirar diseño, pero no demuestra una ventaja; la 4 es viable si significa composición dinámica de módulos, no multiplicación autónoma de agentes.

## 1. Evaluación de las cuatro ideas

1\. Espacio de decisión circular de 360° — viable con límites. Un ángulo puede representar rumbo; no representa por sí solo todas las decisiones de navegación. La idea se vuelve técnicamente útil si el círculo codifica una variable continua y Python recibe una salida acotada, con incertidumbre y validación. Si solo sustituye cuatro etiquetas por un ángulo, no simplifica nada.

2\. Teselaciones de Penrose — metáfora útil, no arquitectura demostrada. Dos tipos de mensajes no garantizan cubrir todas las decisiones posibles ni evitar ambigüedades. La no periodicidad de una teselación no aporta por sí misma propiedades de completitud, seguridad o cobertura semántica. Como mecanismo literal de comunicación: especulativo; como inspiración visual para explorar estados y transiciones: aceptable.

3\. Híbrido analógico-digital — la idea más prometedora. La analogía tiene fundamento técnico: sistemas híbridos combinan variables continuas y estados discretos. La dinámica del barco y sus sensores son continuos; los permisos, las restricciones y los estados de misión son discretos. El LLM, sin embargo, no es literalmente un componente analógico: es un sistema digital probabilístico. La correspondencia útil es interpretación aproximada frente a control determinista, no analógico frente a digital en sentido físico.

4\. Agentes que se multiplican o dividen — viable como modularidad dinámica. Activar módulos especializados según la tarea es una idea conocida en sistemas de expertos, enrutamiento de modelos y arquitecturas mixture-of-experts. Crear agentes completos que se repliquen y coordinen dinámicamente puede añadir latencia, costes y fallos de coordinación. La oportunidad está en recombinar capacidades existentes, no en multiplicar agentes por sí mismo.

## 2. ¿Existe literatura sobre el híbrido analógico-digital con LLM?

Sí, aunque la terminología más útil no parece ser «LLM analógico-digital», sino control híbrido supervisado por lenguaje natural.

- LLM + PID: un trabajo de 2026 sobre control de procesos estudia el LLM como supervisor de un controlador PID, y señala riesgos de estabilidad y traducción de símbolos a acciones físicas.&#x20;

  [image](https://www.google.com/s2/favicons?domain=https://www.sciencedirect.com\&sz=32)

  ScienceDirect

  +1

- LLM + MPC + Control Barrier Functions (CBF): LaMPC-CBF estudia cómo traducir instrucciones lingüísticas a parámetros de optimización y restricciones de seguridad para control robótico. Es un antecedente especialmente cercano a la separación entre lenguaje y ejecución segura.&#x20;

  [image](https://www.google.com/s2/favicons?domain=https://research.knu.ac.kr\&sz=32)

  Kyungpook National University(KNU)

- Enrutamiento dinámico de modelos: existe literatura sobre elegir modelos según la complejidad de cada consulta, sin mantener todos activos para todas las tareas.&#x20;

  [image](https://www.google.com/s2/favicons?domain=https://arxiv.org\&sz=32)

  arXiv



## 3. Ubicación en el roadmap y costo relativo

| Idea                     | Fase futura                                                          | Costo relativo                                                  |
| ------------------------ | -------------------------------------------------------------------- | --------------------------------------------------------------- |
| Espacio circular         | Exploración después de F2; solo si aparece una variable angular útil | Bajo                                                            |
| Teselaciones de Penrose  | Archivo de ideas; sin fase asignada                                  | Bajo para conceptualizar; incierto para justificar técnicamente |
| Híbrido lenguaje-control | Investigación paralela tras estabilizar F1–F3                        | Medio-alto                                                      |
| Agentes recombinables    | Fase de optimización, si un único intérprete demuestra límites       | Medio-alto                                                      |

No abriría ninguna fase ahora. La tercera idea merece una ficha de investigación futura; la cuarta, una nota condicionada a que haya evidencia de que la modularidad aporta ventajas.

## 4. El posible atajo escondido

El candidato más interesante no es un modelo nuevo ni una geometría exótica: usar el LLM solo para cambiar parámetros de un controlador determinista ya existente.

En vez de pedirle que elija entre muchas acciones físicas, podría interpretar conceptos como «más conservador», «priorizar la llegada» o «mantener mayor separación» y traducirlos a parámetros acotados. Un controlador y un filtro de seguridad independientes conservarían la autoridad sobre la ejecución. La literatura sobre LLM + MPC + CBF ofrece un antecedente concreto, aunque no valida automáticamente su aplicación náutica.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://research.knu.ac.kr\&sz=32)

Kyungpook National University(KNU)



Veredicto: la idea 3 merece quedar registrada como hipótesis de arquitectura híbrida; la idea 4, como posible optimización; la 1, como representación alternativa solo si resuelve un problema concreto. La 2 no justifica inversión técnica por ahora. El atajo potencial es reducir la autoridad del LLM y aprovechar mejor los controladores existentes, no aumentar la complejidad del sistema.