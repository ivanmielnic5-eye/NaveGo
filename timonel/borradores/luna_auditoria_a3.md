# BORRADOR — LUNA: AUDITORIA DE ERRORES A3

**Fecha:** 2026-10-14
**Estado:** BORRADOR.
**Origen:** consulta sobre auditoria de errores A3.

---

## 1. Patron principal: F2 falla en la conjuncion

Los 7 errores de F-held F2 tienen la misma estructura logica: d<T,
pero v>v_max. El modelo parece dar prioridad a la condicion de
distancia y no aplicar consistentemente la restriccion de velocidad.

Lo importante: los errores con diferencias de velocidad grandes no se
explican simplemente por ambiguedad en el limite. Los diff_lp de
15-18, si son diferencias de log-probabilidad comparables, indican
una preferencia fuerte por la respuesta equivocada. Investigar primero
una posible falla de composicion de condiciones, sin descartar
artefactos del metodo de puntuacion.

## 2. Los errores de frontera son una senal, no una conclusion

En test_balanceado aparecen dos errores en cada direccion:

- v = v_max: el modelo elige ir_a, aunque la igualdad debe admitirse.
- v - v_max = 0.11: el modelo elige terminar, aunque la velocidad
  excede el limite.

Es compatible con un aprendizaje imperfecto de la frontera, pero dos
casos por patron no bastan para concluir que aprendio < en lugar de
<=.

Para verificarlo, generaria pares controlados que difirieran
unicamente en la velocidad: v_max - eps, v_max y v_max + eps, con la
misma distancia, formulacion y umbral. Repetir con varios valores de
v_max.

## 3. Puntaje forzado frente a generacion libre

Los indices 1 y 91 tienen diff_lp positivo (favorece terminar) pero
generacion libre produce ir_a.

No invalida automaticamente la medicion principal si el puntaje
forzado se definio previamente. Si demuestra que mide una propiedad
distinta de la respuesta que el modelo produciria libremente.

Propongo:
- Mantener el puntaje forzado como metrica primaria si fue
  preespecificado.
- Evaluar generacion libre en TODOS los items, no solo en los
  errores.
- Auditar como se calculo diff_lp: primer token o secuencia completa,
  tokenizacion de ambas etiquetas, prefijo, espacios y normalizacion
  por longitud.

## 4. Que indican los errores alejados del limite

Los casos con v - v_max > 0.9 refuerzan la hipotesis de que el modelo
no integra de forma fiable la clausula de velocidad. Sin embargo, los
datos no permiten distinguir aun entre:

- Falla al comparar valores numericos.
- Falla al combinar dos condiciones.
- Dependencia de ciertas formulaciones de F-held.
- Sesgo hacia terminar inducido por la puntuacion o el formato.
- Error de etiqueta o inconsistencia en el contexto original.

## 5. Que falta mirar

Prioridad inmediata: cruzar los errores con formulacion, plantilla,
valores numericos, tokenizacion y ejemplos correctos equivalentes.
Recalcular las etiquetas mediante un oraculo independiente.

Lectura provisional: A3 muestra una debilidad especifica en la
aplicacion de la restriccion de velocidad, mas clara en F-held F2 que
en el test balanceado. No cambiaria el criterio de exito ni entrenaria
otra version hasta separar el fallo semantico del posible artefacto
de evaluacion.
