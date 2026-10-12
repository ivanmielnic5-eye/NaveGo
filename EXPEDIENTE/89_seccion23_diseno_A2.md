# SECCION 23 — DISENO DE A2 (FASE 1A, REV. 2)

**Fecha:** 2026-10-12
**Autor:** Direccion de Investigacion
**Estado:** DISENO. No ejecutado.
**Referencias:** memo 89 secciones 20-22, anexos D (Luna), E (Claude), F (Luna).

---

## 23.1 Motivacion

El run A1 (Banco A) no respaldo la capacidad de Fase 1a. La auditoria
del runner (2026-10-12) confirmo:

- 810 contextos evaluados con Llama 3.1 8B base sin SFT.
- 810/810 respuestas validas (solo digito).
- 808/810 consistentes (99.8%).
- 420/810 aciertos = 51.9%.
- p_term_unbiased = 0.0000 en TODOS los contextos.
- Decision: 808 "ir_a", 2 "None". Cero "terminar".

Conclusion: el colapso a "ir_a" no es del parser, no es de la
inconsistencia posicional, no es del SFT. Es del modelo frente al
prompt de A1.

Se identifico una contradiccion de diseno no documentada antes:
el prompt declara que "terminar" requiere d < T Y baja velocidad,
pero el estado solo entrega d y T, y la etiqueta solo usa d < T.
El modelo lee un contrato que no puede verificar completamente.

A2 corrige esa contradiccion, rediseña el banco y establece criterios
de exito/falsacion preregistrados antes de entrenar.

## 23.2 Decisiones de diseno

Decisiones tomadas por la Direccion, incorporando las propuestas de
Claude (anexo E) y las correcciones de Luna (anexo F):

1. Sin velocidad. El prompt de A2 no menciona velocidad.
2. Respuesta en palabra ("ir_a" / "terminar"), no en digito.
3. d y T con 1 decimal. Etiqueta calculada sobre el valor mostrado.
4. NO se excluyen los casos cercanos al umbral (|d-T| < 0.3).
5. 11 valores de T en train, no 4.
6. Puntaje forzado como metodo principal, con verificacion de
   generacion como compuerta.
7. Compuertas tecnicas fijadas antes de entrenar, no compuertas
   numericas arbitrarias heredadas de Claude.
8. Criterio principal: el umbral efectivo sigue a T en valores no
   vistos.

---

## 23.3 Contrato de A2

El prompt de A2 define el objetivo y las acciones. NO incluye la
regla de decision. La regla se aprende de los ejemplos.

Prompt exacto (plantilla, con placeholders):

    === PROPOSITO ===
    Llevar el barco hasta la meta.
    La mision se considera completa cuando la distancia a la meta es
    menor que {T} metros.

    === ESTADO ACTUAL ===
    - Distancia a la meta: {d} metros

    === ACCIONES DISPONIBLES ===
    {acciones}

    === TAREA ===
    Elegi la accion que mejor contribuya al proposito.
    Responde UNICAMENTE con JSON: {"accion": "<nombre>"}

Donde:
- {T}: valor del umbral, 1 decimal.
- {d}: valor de la distancia, 1 decimal.
- {acciones}: lista de 2 acciones, orden aleatorizado por contexto.
  Formato:
    - ir_a: seguir navegando hacia la meta.
    - terminar: declarar la mision como cumplida.

Regla de etiquetado (calculada sobre el valor MOSTRADO):
- Si d_mostrado < T_mostrado -> terminar
- Si d_mostrado >= T_mostrado -> ir_a

El caso d = T pertenece a ir_a (la condicion es estricta).

Respuesta esperada (formato exacto):
    {"accion": "ir_a"}    o    {"accion": "terminar"}

## 23.4 Reglas de consistencia

Se verifican por codigo antes de generar el banco:

1. La plantilla no contiene digitos propios (solo placeholders).
2. La etiqueta coincide con la comparacion sobre el valor mostrado.
3. Ningun T de test aparece en train.
4. El prompt no menciona velocidad, nudos, viento ni otros campos.
5. Val no duplica (T, d) de train.
6. Ambas acciones aparecen con igual frecuencia en cada estrato.

---

## 23.5 Estructura del banco A2

Splits y tamaños:

    Split          T                          N por celda    Total
    -------------  -------------------------  -------------  -----
    train          {8,10,12,14,16,18,20,22,    7              616
                    24,26,28}
    val            mismos que train           2              176
    test_interp    {11, 17, 23}               25             600
    test_extrap    {6, 32}                    25             400

Cada celda (T x 4 bins x 2 lados) tiene igual cantidad por lado.

Bins de |d - T| (en metros):
- (0.3, 1.0): muy cerca del umbral
- (1.0, 2.0): cerca
- (2.0, 4.0): lejos
- (4.0, 8.0): muy lejos

El limite inferior de 0.3 se debe a la resolucion de 1 decimal:
con valores mostrados a 1 decimal, |d-T| < 0.3 no garantiza que
d != T. Los casos |d-T| < 0.3 se excluyen SOLO de la metrica
principal, pero se incluyen en un estrato diagnostico separado
(caso d = T).

## 23.6 Decisiones respecto de las propuestas de Claude y Luna

Aceptadas de Claude:
- 11 valores de T en train.
- Puntaje forzado como metodo principal.
- Comparacion emparejada base vs SFT con disable_adapter.
- Splits train / val / test_interp / test_extrap.
- Sin mencion a velocidad en el prompt.

Aceptadas de Luna:
- No excluir |d-T| < 0.3 del experimento (solo de la metrica
  principal).
- Medir tasa de respuestas validas y consistentes por separado.
- Verificacion de enmascaramiento por inspeccion de tokens (no solo
  ejecutar la funcion).
- Invariancia semantica al invertir el orden de las acciones.

Rechazadas o modificadas:
- Las 5 compuertas numericas de Claude (0.99, 0.60, 0.98, 0.95,
  1.0m): se reemplazan por compuertas tecnicas fijadas antes de
  entrenar.
- Verificacion de generacion sobre 40 casos: se aumenta a 200 casos,
  cubriendo ambos ordenes, cercanos y lejanos.
- Respuesta en digito: se cambia a palabra.

---

## 23.7 Compuertas tecnicas (bloquean si fallan)

Se verifican ANTES de entrenar o durante el entrenamiento. Si alguna
falla, el run es INVALIDO. No refuta nada sobre el modelo.

1. Enmascaramiento verificado por inspeccion de tokens:
   los tokens del prompt tienen label -100, los de la respuesta
   conservan su label. Se imprimen 3 ejemplos con sus mascaras.

2. Numero de tokens supervisados por ejemplo:
   debe ser igual al numero de tokens de la respuesta JSON esperada
   (aproximadamente 8-12 tokens). Si es ~200, el enmascaramiento
   fallo.

3. Concordancia puntaje forzado vs generacion:
   se mide sobre 200 contextos. Se reporta el porcentaje. No hay
   umbral fijo; se usa como control de calidad del metodo.

4. Exactitud en train (puntaje forzado, 200 ejemplos):
   >= 0.95. Si no, el modelo no ajusto ni el formato. Compuerta
   tecnica, no de aprendizaje.

## 23.8 Criterios de veredicto (preregistrados)

Se evaluan SOLO despues de pasar las compuertas. Orden de prioridad:

VEREDICTO 1 — INVALIDO / SIN SENAL
  Falla una compuerta. No concluyente sobre el modelo.

VEREDICTO 2 — SFT NO APORTA
  La base ya saca >= 0.95 en el estrato lejano de test_interp.
  Activa la senal de parada del memo 89 seccion 5.

VEREDICTO 3 — NO APRENDIO (MEMORIZA)
  En al menos 2 de los 3 T de interpolacion, el umbral efectivo
  estimado cae a <= 0.5 m de algun T visto y a >= 0.7 m del T
  verdadero.

VEREDICTO 4 — APRENDIO (FASE 1A, INTERPOLACION)
  - Exactitud >= 0.95 en estrato lejano (|d-T| >= 2) con limite
    inferior de Wilson >= 0.90, Y
  - |T_efectivo - T| <= 1.0 m en cada uno de los 3 T de
    interpolacion.

VEREDICTO 5 — INCONCLUSO
  Todo lo demas.

La extrapolacion (T = 6 y 32) se reporta pero no condiciona el
veredicto. La invariancia semantica (invertir orden de acciones)
se reporta como metrica secundaria.

## 23.9 Estimacion del umbral efectivo

Para cada T no visto:
- Tomar los contextos con |d - T| <= 4 m.
- Calcular la diferencia de log-probabilidades:
  lp(terminar) - lp(ir_a) para cada contexto.
- Ajustar una regresion lineal de esa diferencia contra d.
- El umbral efectivo T_efectivo es el punto donde la recta cruza
  cero.
- Intervalo de confianza por bootstrap (1000 remuestreos).
- Si la pendiente no es negativa, T_efectivo queda indefinido
  ("sin umbral").

Esto es lo que se compara con T verdadero.

## 23.10 Metodo de puntaje forzado

Para cada contexto:
1. Construir el prompt con chat template de Llama 3.1.
2. Calcular log-probabilidad de las dos respuestas completas:
   '{"accion": "ir_a"}' y '{"accion": "terminar"}'.
3. Diferencia = lp(terminar) - lp(ir_a).
4. Decision = "terminar" si diferencia > 0, "ir_a" si < 0.

Base y SFT se evaluan con el mismo procedimiento, sobre los mismos
contextos. La base se puntua con disable_adapter().

La generacion se usa como compuerta tecnica, no como metodo
principal.

---

## 23.11 Plan de ejecucion

Orden estricto. Cada paso produce un artefacto verificable.

PASO 1 — Generador de A2
  Script Python que produce los 4 splits (train, val, test_interp,
  test_extrap) como JSONL + manifiesto.json con hashes.
  Verifica las reglas de consistencia (seccion 23.4) y aborta si
  alguna falla.
  Artefacto: bancoA2/{train,val,test_interp,test_extrap}.jsonl
             bancoA2/manifest.json

PASO 2 — Preregistro de A2
  Congelar por commit: splits, compuertas, criterios de veredicto,
  metodo de puntaje forzado, metodo de estimacion de T_efectivo.
  Una vez commiteado, no se modifica hasta despues de la evaluacion.
  Artefacto: commit en rama experimento-v4-admin.

PASO 3 — Notebook de entrenamiento A2
  Notebook Kaggle con:
  - Carga del banco A2.
  - Chat template Llama 3.1.
  - SFTTrainer con train_on_responses_only verificado.
  - Compuerta de enmascaramiento (seccion 23.7 punto 1 y 2).
  - Entrenamiento con 3 semillas.
  Artefacto: timonel_sft_A2_kaggle.ipynb + outputs_A2/{seed1,2,3}/

PASO 4 — Evaluacion A2
  Sobre los splits test_interp y test_extrap:
  - Puntaje forzado base vs SFT (emparejado).
  - Estimacion de T_efectivo por T no visto.
  - Analisis por estratos (lejanos / cercanos / d = T).
  - Invariancia semantica (invertir orden de acciones).
  - Verificacion de generacion sobre 200 casos.
  Artefacto: eval_A2_{base,sft}.jsonl + informe de veredicto.

PASO 5 — Veredicto
  Aplicar los criterios de la seccion 23.8 en orden.
  Reportar en memo 89 (nueva seccion) o en anexo nuevo.

## 23.12 Lo que NO se hace todavia

- NO se reentrena A1 con otro seed ni mas steps.
- NO se toca el confirmatorio de A1.
- NO se pasa a Fase 1b (velocidad, frenar).
- NO se abren nuevas consultas a Claude o Luna hasta tener
  resultados de A2.
- NO se reescribe la propuesta de Claude: se la usa como base y se
  la corrige segun Luna y la auditoria.

## 23.13 Firma

**Estado:** DISENO CONGELADO a la espera de implementacion.
**Proximo paso:** PASO 1 (generador de A2).
**Responsable:** Direccion de Investigacion.
**Regla:** calidad primero, performance despues.
