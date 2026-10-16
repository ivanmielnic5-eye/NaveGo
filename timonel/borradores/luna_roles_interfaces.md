<!-- ingesta: 2026-10-13 19:10 -->
# BORRADOR — LUNA: ROLES, INTERFACES Y ROADMAP

**Fecha:** 2026-10-13
**Estado:** BORRADOR. Fuera del expediente hasta consolidacion con Claude.
**Origen:** validacion de la respuesta de Claude sobre arquitectura de roles.

---

## 1. Encuadre: roles con interfaces

Correcto, con una reserva: descartaria multiagentes como requisito
arquitectonico, no como posibilidad futura. La unidad fundamental es
el rol con contrato intercambiable: misma entrada, misma semantica y
misma salida, aunque cambie la implementacion.

Se pierde algo si eliminamos el marco multiagente por completo: la
posibilidad de deliberacion paralela, contraste entre evaluadores o
especializacion independiente. Pero eso solo se justifica si un
experimento demuestra valor adicional frente a la coordinacion y
latencia que introduce.

## 2. Roadmap

La secuencia de Claude es razonable, pero agregaria dos controles
explicitos:

- Antes del interprete: contrato formal, semantica de mision, conjunto
  de pruebas y baseline Python congelado. Sin eso, no hay comparacion
  valida.
- Antes del lazo cerrado: una fase propia de validacion de seguridad en
  simulacion, con criterios de aceptacion y rechazo.

F1-F4 no se subsumen completamente:

- F1, umbral variable: encaja en F0, si queda parametrizado desde el
  comienzo.
- F2, composicion de condiciones: puede probarse entre interprete y
  verificador; requiere casos de prueba especificos.
- F3, seguridad simulada: debe conservar un hito de validacion propio.
- F4, abstencion y recuperacion: debe ser un requisito explicito del
  contrato y tener pruebas propias; no alcanza con mencionarlo dentro
  de la verificacion.

## 3. Bugs y otros desajustes

boundary_violation: si, si 500 m es una restriccion dura. En el
ranking normal, al estar ultimo, solo desempata; una accion que viola
el limite puede ganar por progresar mas. Debe aplicarse un veto previo
al ranking. Si todas las acciones son inviables, hace falta una
politica explicita de emergencia, no elegir silenciosamente una como
valida.

El 0,3 kn: duplicacion real; bug semantico todavia no demostrado.
Centralizarlo en la configuracion de mision es razonable, pero
conservar campos diferenciados --por ejemplo, sog_objetivo_frenado,
v_max_probe y umbral_llegada_lenta-- si representan conceptos
distintos. No deben quedar iguales por obligacion.

Otros desajustes del inventario:

- T variable en el banco, pero umbral de terminar fijado en 15 m.
- terminar exige proximidad, pero la condicion de exito debe definir
  tambien que velocidad de llegada es aceptable.
- El ranking cambia segun el regimen de peligro: los criterios y sus
  prioridades necesitan una especificacion comun y testeable.
- frenar apunta a 0,3 kn; no equivale a detenerse. No confundir
  objetivo de velocidad con criterio de exito.
- rumbo e ir_a pueden producir trayectorias parecidas, pero no tienen
  la misma interfaz ni necesariamente la misma dinamica. La comparacion
  debe reconocer esa diferencia.

Estos son diagnosticos derivados del inventario disponible, no una
nueva auditoria del codigo.

## 4. Quien decide en A3 y como medirlo

Si: es una tension arquitectonica central. En A2/A3, el LLM selecciona
la accion; en la alternativa hibrida, el LLM interpreta la intencion y
Python decide o controla la accion fisica. Son hipotesis distintas y
no deben mezclarse en una misma comparacion.

Mediria cada rol por separado:

- Interprete: exactitud de intencion y parametros, errores de unidades,
  campos faltantes y salidas invalidas.
- Verificador: restricciones violadas que acepta (falsos aceptados),
  ordenes validas que rechaza, y deteccion de entradas ambiguas o
  incompletas.
- Decisor: regret frente al baseline/oraculo, exito de mision,
  violaciones de restricciones y estabilidad. En la arquitectura
  hibrida, medir ademas el aporte marginal del LLM frente a Python
  solo.
- Integracion: resultados de episodios completos, fallos de
  recuperacion, latencia y comportamiento ante datos degradados,
  manteniendo escenarios y semillas comparables.

Mi recomendacion: fijar ahora las interfaces y la autoridad de
decision de cada variante experimental. No elegir todavia una
arquitectura ganadora. Primero demostrar, con pruebas separadas y
despues integradas, que aporta cada rol y que errores introduce.
