# BORRADOR — LUNA: CRITERIO DE CONTAMINACION (CORRECCION)

**Fecha:** 2026-10-13
**Estado:** BORRADOR.
**Origen:** correccion a criterio demasiado estricto sobre
contaminacion de F-held.

---

DeepSeek esta aplicando un criterio de contaminacion demasiado
amplio. Distingo cuatro cosas:

1. Conocer el proyecto y su hipotesis. No descalifica al autor. Para
   generar formulaciones validas, el autor necesariamente debe
   conocer la regla abstracta: d < T AND v <= v_max.

2. Haber visto las formulaciones concretas de F_train/F_dev, sus
   etiquetas o el analisis de errores. Esto si compromete la
   independencia.

3. Conocer resultados agregados (ej. P-text=100% en A3). No equivale
   a haber visto items retenidos, pero puede sesgar el diseno.
   Registrarlo.

4. Usar un LLM en sesion nueva. Que el mismo modelo se haya usado en
   otras conversaciones no implica que la sesion nueva reciba ese
   contexto. La independencia contextual depende de no transferir
   historial, memoria, archivos ni recuperacion del proyecto.

La elegibilidad debe decidirse por exposicion efectiva y
procedimiento, no por identidad del investigador, proveedor o
modelo.

Sobre el CEO: si no vio las formulaciones especificas ni los
analisis de errores, no corresponde declararlo contaminado
automaticamente. Su desconocimiento tecnico tampoco demuestra
independencia; lo relevante es que materiales vio.

Sobre LLM en sesion limpia: no descartarlo solo porque comparte
familia con una instancia previa. Aceptarlo como autor con
independencia contextual documentada, siempre que la sesion no
reciba informacion previa. No afirmar independencia absoluta del
modelo ni ausencia de exposicion en su entrenamiento.

Propuesta: auditar que vio cada candidato antes de resignarse a
F-held exploratorio. Si existe una via de generacion aislada, con
consigna sellada, sin items ni errores previos y con validacion
ciega, evaluar si satisface los requisitos confirmatorios definidos
de antemano.

No confundir rigor con exigir una pureza imposible de demostrar.
Definir que independencia necesita medir F-held, que amenazas la
comprometen y cuales son limitaciones declarables.


---

## SEGUNDA RESPUESTA: EVALUACION HONESTA

No veo motivos suficientes para considerar contaminada toda la
investigacion. Si veo un riesgo metodologico concreto en como se
construya y se interprete F-held. No son lo mismo.

### Lo que me preocupa y lo que no

1. No me preocupa que el CEO participe en decisiones. Con lo
   contado, no hay base para declararlo contaminado por conocer el
   proyecto. La cuestion es si vio las formulaciones especificas
   que deben quedar retenidas, sus etiquetas o los errores concretos
   de P-text.

   Que entienda poco de los detalles tecnicos no demuestra
   independencia por si solo; tampoco la invalida. Importa que
   informacion recibio realmente.

2. Si me preocupa que la instancia que consulta (Director de
   Investigacion actual), Claude o Notebook LLM generen el F-held
   confirmatorio despues de haber visto las formulaciones de
   desarrollo. No por incapacidad de proponer frases nuevas, sino
   porque no podemos garantizar que no reproduzcamos patrones
   conocidos. Una sesion nueva reduce contaminacion contextual, pero
   no convierte otra conversacion del mismo modelo en familia
   independiente.

3. No me preocupa que el autor conozca la regla abstracta. Es
   inevitable y necesario. El riesgo aparece si ve ejemplos concretos
   retenidos, respuestas, errores del sistema evaluado, o si adapta
   frases despues de conocer el rendimiento.

4. Tampoco considero que el 100% de A3 este invalidado. Es un
   resultado valido para el banco y protocolo con que se obtuvo. Lo
   que no demuestra por si solo es generalizacion a formulaciones
   independientes. Precisamente para eso necesitamos F-held.

### Diagnostico global

No veo senal de alarma que justifique frenar el proyecto. Lo pondria
en amarillo para la interpretacion de resultados, no en rojo por
contaminacion.

Tres problemas distintos:

| Riesgo | Evaluacion |
| --- | --- |
| Fuga de items al modelo evaluado | No hay evidencia en A3 |
| Autor de F-held expuesto a formulaciones de desarrollo | Riesgo real para instancias que las vieron; evitable |
| Decisiones metodologicas tomadas despues de ver resultados | Existe posibilidad; no invalida exploratorio; congelar protocolo confirmatorio |

La literatura sobre evaluacion de LLM advierte que parafrasear
ejemplos conocidos no garantiza eliminar contaminacion. Importa mas
controlar procedimiento y documentar limites que exigir independencia
absoluta imposible de certificar.

### Que haria

No demorar el proyecto buscando autor ideal. Congelar consigna de
F-held, abrir sesion realmente aislada (sin historial, memoria ni
archivos), generar sin mostrar ejemplos de desarrollo ni errores de
P-text.

Eso permitiria describirlo como F-held generado por una instancia
contextualmente aislada. No afirmar independencia de familia de
modelos si se usa el mismo modelo subyacente.

Despues: validar formulaciones y etiquetas con criterios fijados
previamente, congelar archivos, ejecutar P-text.

Ademas: esta instancia (Luna) no deberia actuar como autora del
F-held confirmatorio. Vio material de desarrollo. Si puede ayudar a
revisar protocolo e interpretar resultados, sin fingir independencia.

Sobre el CEO: no excluirlo por ser CEO ni por conocer el proyecto.
Evaluar su exposicion concreta a los items retenidos, no su cargo.
Si no vio esos items, hay diferencia metodologica con instancias que
si los vieron.

Conclusion: la investigacion no esta desacreditada. El resultado de
A3 tiene alcance limitado. F-held puede disenarse de forma
defendible. No necesitamos pureza absoluta. Necesitamos saber que
afirmacion respalda cada experimento y no presentar evidencia
exploratoria como confirmatoria.
