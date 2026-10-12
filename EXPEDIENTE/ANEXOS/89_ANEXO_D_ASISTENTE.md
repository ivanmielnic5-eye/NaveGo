# ANEXO D — ASISTENTE / BANCO A

**Fecha:** 2026-10-12
**Origen:** analisis tecnico del run SFT / Fase 1a.

---

## INFORME 1 — Lectura del log_history

step 10 | loss 2.0000 | grad_norm 4.49
step 20 | loss 0.1206 | grad_norm 0.39
step 30 | loss 0.0596 | grad_norm 0.30
step 50 | loss 0.0540 | grad_norm 0.06 | eval_loss 0.0542
step 100 | loss 0.0535 | eval_loss 0.0533
step 150 | loss 0.0539 | eval_loss 0.0529

La loss cae de 2.00 a 0.05 en los primeros 20 steps y se plancha.
eval_loss cerca de train_loss en los tres checkpoints. No hay
overfitting clasico.

La evaluacion del SFT sobre val: 103/200 = 51.5%. Todos los fallos
con patron real='1' pred='2'. Colapso a la clase mayoritaria.

---

## INFORME 2 — Hallazgo: contradiccion prompt/etiqueta

Al cruzar prompt_banco_A.py con generar_banco_A.py aparece un
problema de diseno no documentado en el memo 89:

- PROMPT: declara que terminar requiere d < T Y que el barco este
  navegando a baja velocidad.
- ESTADO: solo entrega d y T. No entrega velocidad.
- ETIQUETA: d < T entonces terminar, sin velocidad.

Consecuencia: el modelo lee un contrato que no puede verificar
completamente. La segunda condicion es invisible. El colapso a ir_a
es consistente con una lectura conservadora del contrato incompleto.

Correccion metodologica: el prompt y el generador deben describir
exactamente la misma tarea. Si la velocidad no forma parte del
criterio, no debe aparecer en el proposito. Si si forma parte, debe
estar en el estado y en las etiquetas.

Este hallazgo no estaba en el memo 89. Es evidencia tecnica
verificable por codigo.

---

## INFORME 3 — Lectura de la respuesta de Luna

Puntos donde Luna tiene razon (y el asistente se habia excedido):

1. El calculo -ln(0.95) ~ 0.051 es para un token, no para un
   promedio de secuencia. Se retira esa afirmacion como estaba.
2. grad_norm bajo no implica que el modelo dejo de aprender.
   Puede ser convergencia.
3. eval_loss cerca de train_loss no descarta todo. Si ambas estan
   dominadas por la plantilla, no distinguen aprendizaje de colapso.

Puntos donde Luna coincide con los documentos:

1. Banco A es Fase 1a, no smoke test.
2. La contradiccion prompt/etiqueta es real.
3. La correccion metodologica es inequivoca.
4. La senal de parada del memo 89 no esta formalmente activada.
5. No reentrenar todavia. Aislar primero el fallo.

Puntos donde Luna va mas alla:

1. Propone un prompt saneado v1.0 (sin mencion a velocidad, d con
   8 decimales).
2. Propone verificar el enmascaramiento del loss antes de reentrenar.
3. Propone comparacion emparejada base vs SFT sobre los mismos
   contextos.
4. Clasifica Fase 1a como no respaldada por el checkpoint actual.

Observacion del asistente: la propuesta de Luna de d con 8 decimales
cambia el problema (lo hace mas dificil), no solo lo sanea. Es una
decision de diseno que requiere aprobacion del Director.
