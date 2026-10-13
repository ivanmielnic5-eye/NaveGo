# ANEXO J — CLAUDE / REFORMULACION CON ANEXO H Y SECCION 25 A LA VISTA

**Fecha:** 2026-10-13
**Origen:** tercera consulta a Claude, con el anexo H y la seccion 25 completos.
**Contenido:** reformulacion de la respuesta anterior de Claude.

---

# Reformulacion con el anexo H y la seccion 25 a la vista

## Balance

| Categoria | Contenido |
|---|---|
| **Cambia** | - Lectura del probe: queda mas debilitada de lo que decia mi respuesta anterior (v_max constante en 0,3 nudos, ver seccion 1). - Brazo LLM primario de H1b-interfaz: corrijo mi propia recomendacion; el primario pasa a ser LLM-A3 (equidad de exposicion, ver seccion 2). - Que esperar para cerrar el fallo de Q2 y la invariancia: no hace falta esperar a la etapa 1; se pueden resolver en la 0b. - Inferencia aritmetica de Q1/Q3/Q4 = 50/50: ya no es inferencia, la tabla lo confirma. |
| **Se mantiene** | Potencia de McNemar y su formula; sobre F-held como n relevante; procedimiento de P-text (autor, sellado, mejor de k, red team); protocolo de esfuerzo (cobertura con cero ediciones confirmatoria sobre el artefacto, tiempo del operador descriptivo); margen de no inferioridad de 2 puntos o 300 contextos estandar; analisis de la esquina y T_hat/v_hat_max; errores.jsonl. |
| **Ya cubierto (no duplicar)** | La seccion 25.4 recoge mis cautelas de alcance (un experimento, no mide LLM vs. parser, Q2 = 0,98, conclusion sobre el artefacto). Ya no hace falta repetirlas. |

## 1. Cambia la lectura del probe?

**Se confirma:** Q1, Q3 y Q4 = 50/50 en el SFT; Q2 = 49/50. El unico error global es el de Q2.

**Cambia, por el dato nuevo de que v_max fue constante (0,3 nudos):**

- **0,3 nudos es casi detenido.** Con ese corte, un modelo puede decidir "ir_a" por una prior del mundo ("un barco que se mueve no termino"), sin leer la clausula. El probe no distingue "leyo v <= 0,3" de "v distinta de ~0 -> todavia navega".
- **El control decisivo** son los casos que contradicen esa prior: v_max alto y v moderada (por ejemplo v=1,5 con v_max=2,0, d<T) -> correcto es terminar aunque el barco se mueva. Si el modelo responde ir_a ahi, usa la prior, no el contrato.
- **Una semilla, y los checkpoints no son replicas.** 50/100/150/154 son instantaneas correlacionadas del mismo run. Sirven para ver cuando aparece el comportamiento (descriptivo), no para estimar variabilidad.
- **La base es un control todavia peor de lo que parecia.** Colapsa a terminar cuando el prompt menciona velocidad (49, 44, 37, 49 de 50) y su sensibilidad a d no es consistente: en Q2 predice terminar 44/50 y en Q4 (d>=T) 49/50, es decir mas terminar cuando d>=T. La metrica de titular tendria que ser el contraste dentro del SFT (mismo d y T, cruzando v_max), no SFT vs. base.

**Lo que sigue en pie:** el SFT hizo algo que la base no, y 199/200 no es azar. Pero la frase de 25.3 ("aprendio a terminar solo cuando TODAS las condiciones se cumplen") es una hipotesis a confirmar, no un resultado.

## 2. Cambia algo de las tres preguntas?

**H1b-interfaz.** Un cambio mio, a partir de 25.7. Antes recomende que el LLM de la etapa 1 fuera el adaptador A2 congelado y LLM-A3 secundario. Lo corrijo: P-text se desarrolla con F-train y F-dev; el adaptador A2 solo vio la plantilla F-train. Compararlo contra P-text es asimetrico en contra del LLM. Por equidad de exposicion:
- **Primario de H1b-interfaz:** LLM-A3 (entrenado con F-train y F-dev) vs. P-text.
- **A2 congelado:** brazo de H1a, la lectura literal de "sin reentrenamiento" (cero exposicion a parafrasis), evaluado tambien en F-held.

Una economia razonable: entrenar LLM-A3 despues de ver como rinde A2 congelado en 0b. Si A2 pasa todo con holgura, A3 ya no es necesario para H1a (sigue siendolo para el primario de H1b).

**Esfuerzo humano.** Se mantiene. Un matiz: el unico operador es el Director, y no es ciego a las hipotesis. Razon de mas para que la medicion confirmatoria sea sobre el artefacto (cobertura con cero ediciones, diff minimo) y el tiempo de operador quede descriptivo.

**Fallo de Q2.** Se mantiene todo, mas tres cosas nuevas:
- Los checkpoints se pueden re-puntuar sobre el probe: un fallo que aparece o desaparece entre 100/150/154 sugiere frontera; uno que persiste, sistematico. Son correlacionados, asi que es indicio, no prueba.
- Necesito el contexto fallido (d, T, v). Con v_max=0,3, mira si v estaba cerca de 0,3.
- La invariancia al orden y la vecindad del fallo no requieren datos nuevos de entrenamiento: se resuelven en 0b, no en la etapa 1.

## 3. Etapa 0b: aparte o integrada?

**Las dos cosas.** Como compuerta (barata, solo puntuar) y como estratos permanentes de la etapa 1, para que el resultado confirmatorio no dependa del probe de v_max constante.

**Especificacion (adaptador A2 congelado, solo puntuar):**

| Bloque | Contextos | Que prueba | Criterio de cribado (propuesto) |
|---|---|---|---|
| **B1 Placebo:** v visible, sin clausula de velocidad; (d<T / d>=T) x (v baja / v alta), 25 c/u | 100 | Que el modelo ignore v cuando el contrato no la menciona | Exactitud >=0,95 y, en (d<T, v alta), tasa de terminar >=0,95 |
| **B2 v_max variable:** v_max en {0,3; 0,6; 1,0; 2,0; 4,0}; v = v_max +- {0,1; 0,2; 0,5}; incluye casos que contradicen la prior (v moderada con v_max alto -> terminar) | ~120 | Que el cruce de v con v_max cambie la decision | Exactitud >=0,95 y >=0,90 en el subconjunto contra-prior |
| **Pares contrafacticos** (mismo d, T, v; solo cambia v_max) | ~50 pares | Contraste dentro del SFT | Fraccion de pares con cambio de decision correcto |
| **Re-puntuado con orden de acciones invertido** (probe + 0b) | sin datos nuevos | Invariancia | Decisiones identicas, salvo casos de frontera |
| **Vecindad del fallo de Q2** | ~30 | Ruido o region de fallo? | Descriptivo |
| **Checkpoints 50/100/150/154** sobre el probe | sin datos nuevos | Cuando aparece el comportamiento | Descriptivo |

El costo es proporcional a tu cifra de ~25 min por evaluacion; no tengo el n de esa evaluacion para estimarlo mejor.

**Regla de decision tras 0b:**
- **Pasa B1 y B2:** A2 congelado es el brazo H1a de la etapa 1, y el probe queda como "lee la clausula con umbral variable (para este artefacto)".
- **Falla B1 (usa la velocidad como senal de cautela) o B2 (usa la magnitud de v e ignora v_max):** el resultado del probe se reinterpreta como heuristica. La etapa 1 exige entrenar LLM-A3 con v_max variable y placebo, y el adaptador A2 queda registrado como "no demuestra lectura".

**Principio general para las familias siguientes:** cada familia nueva trae su placebo (la variable aparece en el estado, sin clausula en el contrato) y sus casos contra-prior. Para F3 (seguridad), por ejemplo, un obstaculo presente sin clausula de seguridad.

## 4. Correcciones sugeridas a la redaccion del memo

- **25.2/25.3:** el titular "86 puntos vs. base" mezcla dos cosas. Agregar el contraste dentro del SFT como metrica principal y aclarar que la base no resuelve la tarea de F2 en ningun cuadrante.
- **25.5:** "ya generaliza a una familia nueva" es demasiado fuerte. Mas exacto: "generaliza a un conjunto adicional con umbral fijo; pendiente 0b". Y la frase sobre "INTERPRETE de contratos, no decisor autonomo" es una hipotesis de uso, no algo que el probe haya examinado.
- **25.6:** invariancia y fallo de Q2 pasan a la etapa 0b, no a la 1.
- **25.7:** reordenar. Primero 0b; despues etapa 1 con LLM-A2 congelado como brazo H1a y LLM-A3 (1 semilla) como primario de H1b-interfaz, entrenado solo tras 0b.