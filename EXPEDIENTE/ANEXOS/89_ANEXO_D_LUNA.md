# ANEXO D — LUNA / BANCO A

**Fecha:** 2026-10-12
**Origen:** consulta sobre el análisis de Banco A tras el run SFT.
**Contenido:** respuestas completas de Luna, sin resumir.

---

## RESPUESTA 1 — Cierre parcial del diagnóstico

La evidencia nueva permite cerrar una parte importante del diagnóstico.
Mi conclusión es que Banco A fue documentado como una prueba de
generalización del umbral, no solamente como un smoke test de
infraestructura; el checkpoint SFT no demuestra esa capacidad y el
motivo exacto del fallo sigue sin estar aislado.

### 1. Encuadre: ¿Banco A era un smoke test o Fase 1a?

Según los documentos aportados, era Fase 1a. No considero legítimo
reclasificarlo retroactivamente como exclusivamente un smoke test.

El commit 24c53b8 especifica umbrales de entrenamiento y validación,
umbrales reservados para confirmación y la hipótesis de generalización
a valores de T no vistos. El memo 89 define explícitamente esa
capacidad y sus criterios de falsación.

La distinción que haría es:

- Infraestructura: dataset carga, entrenamiento termina, adaptador se
  guarda y recupera, modelo genera respuesta procesable.
- Capacidad de Fase 1a: el modelo aplica la comparación entre
  distancia y umbral, generalizando a valores de T que no vio.

La primera parece haber funcionado. La segunda no quedó demostrada.

Para sostener que el propósito principal era exclusivamente
infraestructura haría falta una decisión contemporánea y versionada
que limitara expresamente el alcance de Banco A a eso.

### 2. La contradicción entre el prompt y las etiquetas

Es un defecto real y una explicación plausible del colapso a ir_a,
pero no está demostrado que sea su única causa.

El prompt dice que la misión se considera completa cuando se cumplen
dos condiciones: distancia menor que T y baja velocidad. Sin embargo,
no muestra la velocidad. El generador etiqueta exclusivamente mediante
d < T, sin consultar la velocidad.

Desde el punto de vista de los datos, la etiqueta es determinista a
partir de d y T. Desde el punto de vista del contrato escrito, el
modelo no puede verificar la condición de baja velocidad.

La corrección metodológica es inequívoca: el prompt y el generador
de etiquetas deben describir exactamente la misma tarea.

### 3. Qué significa realmente el loss = 0,053

El log muestra una caída rápida de la pérdida y una meseta temprana.
Pero esa pérdida no demuestra que el modelo haya aprendido a
discriminar ni que haya dejado de aprender exactamente en el paso 20.

Si se confirma que el entrenamiento incluyó la pérdida de todos los
tokens del prompt, la interpretación cambia de forma importante. El
texto fijo de la plantilla representa una parte considerable de cada
secuencia.

No aceptaría como demostradas estas afirmaciones:
- Que 0,053 es la firma inequívoca de predecir la clase mayoritaria.
- Que el gradiente bajo demuestra ausencia de aprendizaje útil.
- Que la similitud entre train_loss y eval_loss descarta todo
  problema de ajuste.

La evidencia directa del problema decisional es otra: en validación,
el SFT obtuvo 103/200 y colapsó a ir_a.

### 4. ¿Se activó la señal de parada del memo 89?

Todavía no está demostrado mediante una comparación directa y
emparejada. SFT: 103/200 = 51,5% sobre validación. Modelo base sin
SFT: 392/750 = 52,3% sobre confirmatorio. Son conjuntos distintos.

No es metodológicamente correcto interpretar la proximidad de esos
porcentajes como una comparación estadística de los dos modelos.

Para resolverlo hay que comparar el modelo base y el SFT sobre
exactamente los mismos contextos, usando el mismo prompt, parser y
procedimiento de evaluación.

### 5. Qué falta medir

1. Verificar el notebook: cómo se construyeron los ejemplos, qué
   función de pérdida se utilizó, si el prompt fue enmascarado.
2. Reconciliar prompt y etiquetas. Baseline determinista sobre train,
   val y confirmatorio. Comprobar que d < T se comporta como se
   especificó, incluido el caso d = T.
3. Comparar base y SFT sobre la misma muestra. Lo más informativo
   sería evaluar ambos sobre los 750 contextos confirmatorios con el
   modelo SFT congelado.
4. Medir generalización directamente. Tasa de terminar por T,
   matriz de confusión, validez de salida, umbral efectivo estimado
   en T no vistos.

No entrenaría otro checkpoint antes de resolver estas cuestiones.

### 6. ¿Fase 1a refutada, inconclusa o pendiente de rediseño?

La hipótesis de generalización del umbral no está respaldada por el
checkpoint actual y falla en la validación reportada. La conclusión
confirmatoria sobre generalización a umbrales no vistos queda
pendiente de una evaluación con el checkpoint congelado.

Eso no equivale a refutar universalmente que Llama 3.1 8B pueda
aprender la comparación.

### Recomendación final

No reentrenaría Banco A simplemente con otro seed ni cambiaría la
cantidad de pasos todavía. Primero verificaría la pérdida aplicada,
eliminaría la contradicción entre prompt y etiquetas y haría una
comparación emparejada entre el modelo base y el SFT.

---

## RESPUESTA 2 — Implementación saneada propuesta

Preparé una primera implementación saneada para Timonel, Banco A,
Fase 1a. Elegí corregir el prompt y dejar listo un pequeño
constructor en Python, en lugar de intentar entrenar otro modelo sin
tener todavía el notebook y el generador de datos originales.

La idea es corregir los problemas metodológicos conocidos sin
modificar el objetivo del experimento: comprobar si el modelo aplica
el criterio de finalización cuando cambia el umbral T.

### El prompt que propongo ejecutar

=== PROPOSITO ===
Llevar el barco hasta la meta.
La mision se considera cumplida cuando la distancia a la meta es
menor que el umbral de mision T.

=== ESTADO ACTUAL ===
- Distancia a la meta: {d_visible} metros
- Umbral de mision (T): {T_visible} metros

=== ACCIONES DISPONIBLES ===
1. {accion_opcion_1}
2. {accion_opcion_2}

Significado de las acciones:
- terminar: declara la mision como cumplida.
- ir_a: navega hacia la meta, corrigiendo el rumbo automaticamente.

=== TAREA ===
Elegi la opcion que mejor contribuya al proposito.

Responde UNICAMENTE con el numero de opcion elegida: 1 o 2.

Este texto conserva la definicion del objetivo, pero elimina una
contradiccion: la version anterior decia que para terminar el barco
debia estar navegando a baja velocidad, aunque el estado no incluia
la velocidad y las etiquetas se generaban solo con distancia y umbral.

Tres condiciones a respetar:

1. La distancia que ve el modelo y la que determina la etiqueta deben
   coincidir. El constructor presenta d con ocho decimales y T con dos.
2. La etiqueta sigue el orden de las opciones. Si terminar es opcion 1,
   la respuesta objetivo sera 1. Si es opcion 2, sera 2.
3. En el limite exacto, d = T, corresponde ir_a. La condicion es
   estricta.

Mi recomendacion es no volver a entrenar todavia con una modificacion
aislada del prompt.

---

## RESPUESTA 3 — Sobre la gobernanza documental

Ivan, yo le responderia a DeepSeek sin elegir todavia entre el memo 89
y el 90. El problema que plantea es legitimo: hay evidencia de una
consolidacion en la seccion 9, pero no tenemos verificada la regla
documental que determina si esa firma cierra el memo completo o
solamente el estado de ese momento.

Instrucciones:

1. Buscar la regla vigente. Inspeccionar memos metodologicos,
   convenciones documentales y antecedentes del repositorio.
2. Verificar el alcance de la firma del memo 89.
3. Reconstruir la cronologia de Banco A.
4. Verificar la convencion de anexos.
5. Presentar una recomendacion fundamentada.

Restricciones: no modificar archivos, no crear memos ni anexos, no
ejecutar commits. Separar hechos comprobados, inferencias y preguntas
pendientes. Si no se encuentra regla explicita, declararlo.

Recomendacion provisional: no crear todavia el memo 90 ni extender el
89 sin verificar la regla documental.
