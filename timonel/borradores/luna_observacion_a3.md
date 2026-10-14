# BORRADOR — LUNA: OBSERVACION DE RESULTADOS A3

**Fecha:** 2026-10-14
**Estado:** BORRADOR.
**Origen:** consulta sobre resultados A3.

---

## 1. Observaciones principales

- A3 visible esta saturado: SFT obtiene 100% en train, val,
  interpolacion y extrapolacion; 99.3% en test balanceado. P-text y
  P-struct tambien obtienen 100% en los tests visibles. Este banco no
  distingue entre las tres soluciones.
- El SFT aprendio algo que BASE no consigue: la diferencia es muy
  grande tanto en A3 como en F-held. BASE obtiene apenas 3.3% en
  F-held F1 y 40.3% en F2.
- F-held F1 no discrimina entre metodos: SFT, P-text y P-struct
  obtienen 100%. No demuestra superioridad del LLM.
- F-held F2 es el resultado mas informativo: SFT obtiene 97.7%,
  P-text 50% y P-struct 100%.

## 2. Que destaca en F-held F2

Si las clases reales estan balanceadas en 150/150, los resultados del
SFT implican:

- 150/150 casos terminar correctamente clasificados.
- 143/150 casos ir_a correctamente clasificados.
- 7 casos ir_a clasificados erroneamente como terminar.

Es un error asimetrico: el modelo conserva la deteccion de terminar
pero no respeta la restriccion adicional de velocidad en 7 casos. Si
terminar representa declarar mision completada, estos falsos
positivos son mas relevantes que el porcentaje agregado.

IC 95% de SFT en F2: aproximadamente [95.3, 98.9]. Si sigue vigente
el criterio previo de 99% por familia, F2 no lo alcanza.

## 3. Que significa SFT frente a P-text?

SFT generaliza mucho mejor que este parser regex concreto a las
formulaciones retenidas de F2.

P-text cae al 50%, lo que podria indicar que sus reglas dejan de
reconocer las expresiones de velocidad y terminan comportandose como
una prediccion constante en un conjunto balanceado.

No demuestra que el LLM sea superior a Python en general: un parser
mas robusto o un sistema determinista con representacion estructurada
pueden resolver la regla. P-struct obtiene 100% porque no necesita
interpretar el prompt; hay que tratarlo como referencia de la logica
de decision, no como competidor equivalente en comprension
linguistica.

## 4. Que falta aclarar

1. Confirmar la distribucion real de clases de F-held F2 y las
   matrices de confusion completas de SFT y P-text.
2. Verificar si P-struct recibe d, v, T y v_max como datos
   estructurados que el SFT debe extraer del texto.
3. Analizar manualmente los siete errores de SFT.
4. Confirmar que las 600 formulaciones de F-held no se usaron para
   ajustar prompts, hiperparametros o reglas despues de observar
   resultados.

Conclusion: estos resultados respaldan una capacidad de
generalizacion linguistica del SFT sobre las formulaciones de F-held
evaluadas, pero no establecen superioridad general sobre Python ni
satisfacen todavia el umbral previo de 99% en F2. El siguiente paso
mas informativo es auditar los errores direccionales, no generar mas
datos inmediatamente.
