# BORRADOR — LUNA: HIPOTESIS COLABORATIVA

**Fecha:** 2026-10-14
**Estado:** BORRADOR.
**Origen:** consulta sobre hipotesis colaborativa.

---

## 1. Circuito de roles: tres funciones logicas, con una cuarta
## barrera operativa

La separacion propuesta es correcta, pero no alcanza para controlar
un barco.

1. Interprete LLM: transforma lenguaje natural en un objeto Intent
   tipado: objetivo, restricciones, parametros, unidades y campos
   desconocidos. No elige maniobras ni ejecuta acciones.
2. Verificador Python: valida esquema, tipos, rangos, coherencia con
   MisionConfig y condiciones de aceptacion. Puede aceptar, rechazar
   o pedir aclaracion. No debe confiar en que el LLM haya
   interpretado correctamente por el mero hecho de producir JSON
   valido.
3. Decisor Python: recibe intencion verificada, telemetria y estado
   de mision; aplica una politica determinista y selecciona la
   accion.
4. Supervisor de seguridad: controla las acciones propuestas frente a
   restricciones operativas y condiciones dinamicas antes y durante
   la ejecucion. Debe poder vetarlas independientemente del
   interprete y del decisor.

El controlador de bajo nivel y la fisica de Godot completan el
sistema, pero no son funciones del interprete.

Esta separacion coincide con arquitecturas recientes de navegacion
robotica que combinan especificaciones linguisticas, representacion
del entorno y filtros de seguridad basados en control. Es un
precedente arquitectonico, no una validacion de NAVEGO.

## 2. Metricas por rol, sin mezclar responsabilidades

| Rol | Metricas principales |
| --- | --- |
| Interprete | Exactitud semantica de intencion y parametros, errores de unidades, campos invalidos, deteccion de ambiguedad y consistencia ante parafrasis. |
| Verificador | Falsos aceptados, falsos rechazos, deteccion de inconsistencias y porcentaje de entradas resueltas sin ejecucion insegura. |
| Decisor | Exito de mision, rendimiento frente a una politica de referencia, calidad de accion y repetibilidad ante estados identicos. |
| Supervisor de seguridad | Violaciones de restricciones, acciones peligrosas vetadas, falsas alarmas y fallos de deteccion. |

La evaluacion integrada debe agregar exito de mision, seguridad,
recuperaciones, latencia y costo computacional. No sustituye las
metricas individuales: un exito final puede ocultar errores
compensados entre roles.

Para el interprete, la referencia debe ser una etiqueta semantica
independiente. Para el decisor, debe ser una politica y un estado de
entrada comunes.

## 3. Conexion con Godot, DHS, Qwen y Puerto Esperanza

No reemplazaria todavia la conduccion autonoma existente. Haria una
integracion progresiva:

- Primero, prueba de interfaz: el interprete recibe instrucciones
  reales o grabadas; produce Intent; el verificador lo valida.
  Comparar con etiquetas de referencia y con el comportamiento
  actual.
- Despues, reproduccion en Godot/DHS: comparar la conduccion actual
  Qwen + reglas contra una variante donde el nuevo interprete
  sustituye unicamente la funcion de interpretacion. Mantener
  identicos el decisor, la configuracion de mision y el controlador
  para aislar el aporte del interprete.
- Finalmente, lazo cerrado: habilitar la variante integrada en
  simulacion, con escenarios, estados iniciales y condiciones
  ambientales comparables; registrar veto de seguridad, trayectoria,
  llegada a Puerto Esperanza, fallos y recuperacion.

P-struct no es un competidor directamente equivalente si recibe la
especificacion estructurada mientras el LLM debe extraerla del
lenguaje. Es una referencia util para evaluar la logica posterior a
la interpretacion, no una comparacion de entradas identicas.

## 4. Evitar dos proyectos paralelos

El contrato Intent debe ser el puente obligatorio entre investigacion
y producto.

El banco offline evalua si el interprete transforma formulaciones en
ese contrato. El harness online consume exactamente el mismo esquema,
con la misma semantica de campos, unidades y validaciones. Cada
ejecucion debe permitir reconstruir la cadena:

instruccion -> Intent -> verificacion -> decision -> accion -> resultado

Asi, cada hallazgo offline puede convertirse en una prueba
reproducible de integracion. Si F-held mide una habilidad que el
runtime nunca utiliza, esa habilidad no demuestra valor operacional.

## 5. Hipotesis colaborativa mejor formulada

H1c: en instrucciones nauticas semanticamente equivalentes pero
formuladas de distintas maneras, un interprete LLM mejora la
conversion a intenciones estructuradas validas respecto del
interprete actual, manteniendo invariantes la politica decisora y el
controlador; esa mejora se traduce en mayor exito de mision o menor
tasa de fallos sin degradar la seguridad mas alla de limites
predefinidos.

Tiene dos pruebas separables:

- H1c-a, interpretativa: mejora la exactitud semantica fuera de
  distribucion.
- H1c-b, operacional: esa mejora produce un beneficio medible en
  Godot/DHS respecto de Qwen + reglas, sin aumentar violaciones de
  seguridad ni introducir una latencia inaceptable.

A3 aporta evidencia para investigar H1c-a; todavia no establece
H1c-b. Los siete errores ir_a -> terminar de F-held F2 refuerzan la
necesidad de medir los errores direccionales, no solo la exactitud
total.

Recomendacion: no plantear "LLM contra Python", sino probar si anadir
interpretacion linguistica generalizable a un sistema determinista
mejora la conduccion real. El experimento decisivo no es otro banco
aislado: es una comparacion controlada en la que solo cambia el
interprete y se mantiene constante el resto del circuito.
