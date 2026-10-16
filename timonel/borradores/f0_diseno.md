<!-- ingesta: 2026-10-13 19:14 -->
# BORRADOR — DISENO DE F0 (ALINEACION CONTRACTUAL)

**Fecha:** 2026-10-13
**Estado:** BORRADOR. Fuera del expediente hasta validacion final.
**Origen:** consolidacion de Claude (arquitectura_roles) y Luna
(roles_interfaces). F0 es el primer paso obligado del roadmap.

---

## 1. Objetivo de F0

F0 es una fase de alineacion contractual. No entrena, no interpreta, no
verifica. Prepara el terreno para que las fases siguientes sean
medibles.

**Por que es bloqueante:** sin F0, un fallo se atribuye al modelo
cuando en realidad banco, entrenador, acciones y simulador estan
midiendo cosas distintas. Ya lo vimos con T: el banco usa T variable,
el simulador lo tiene fijo en 15.0.

**Criterio central:** banco y simulador coinciden en los casos de
referencia.

## 2. Config unica de mision

Todos estos valores viven en un solo lugar. Ningun componente los
tiene hardcodeados.

| Campo | Uso | Valor actual |
| --- | --- | --- |
| T | umbral de llegada | fijo en 15.0 (hardcodeado) |
| v_max | velocidad maxima de llegada | aparece en el probe, en el banco, y como 0.3 |
| sog_objetivo_frenado | objetivo de frenar | 0.3 por default |
| umbral_llegada_lenta | condicion de "baja velocidad" | implicito, sin definir |

**Pendiente de decision del Director:** si estos cuatro son el mismo
concepto o son cuatro distintos. Luna marco: no deben quedar iguales
por obligacion. Pueden ser conceptos separados que hoy comparten valor
por casualidad.

**Propuesta tecnica:** archivo unico de configuracion de mision
(JSON o YAML), leido por:
- acciones.py (para terminar y frenar)
- entrenador_v2.py (para evaluar misiones)
- banco (para generar etiquetas)
- simulador (para saber cuando la mision termina)

Cambiar un valor requiere cambiar un solo archivo.


<!-- ingesta: 2026-10-13 19:14 -->
## 3. Contrato formal de mision

Definir, en lenguaje formal, que significa:

- **Mision exitosa.** Criterio de llegada. ¿Solo distancia? ¿Distancia
  Y velocidad? ¿Tiempo maximo?
- **Llegada con velocidad aceptable.** ¿Que velocidad es "baja"? ¿En
  que unidades? ¿Es requisito o recomendacion?
- **Abstencion.** Cuando el sistema NO debe decidir. Falta un dato,
  sensores contradictorios, contrato incompleto.

**Pendiente de decision del Director:** estos tres son dominio
nautico. El equipo tecnico propone estructura. El Director decide
criterio.

**Lo que el contrato debe permitir:**
- Verificar una mision de forma automatica (criterio booleano).
- Generar etiquetas de referencia para el banco.
- Evaluar acciones sin ambiguedad.

## 4. Baseline P-struct minimo

Es el motor Python determinista que se compara contra el LLM en A3.
Recibe una spec formal (JSON) y el estado actual. Aplica reglas.

**Que hace:**
- Lee el contrato desde la config unica.
- Aplica el criterio de mision.
- Devuelve accion (terminar / ir_a / frenar / abstenerse).

**Que NO hace:**
- No interpreta lenguaje natural.
- No decide con informacion incompleta sin politica explicita.

**Como se congela:**
- Version fija, hash registrado.
- Tests de regresion sobre casos de referencia.
- Cambios requieren justificacion y nueva version.

## 5. Desajustes del inventario a resolver en F0

Los que marco Luna, derivados del inventario:

- T variable en el banco vs T fijo en terminar. → config unica.
- terminar exige proximidad, no velocidad de llegada. → contrato.
- Ranking cambia segun regimen (normal vs peligro inminente). →
  especificacion comun y testeable.
- frenar apunta a 0.3 kn, no equivale a detenerse. → separar
  concepto de objetivo de velocidad y criterio de exito.
- rumbo e ir_a tienen interfaces distintas pero trayectorias
  parecidas. → la comparacion debe reconocer la diferencia.
- boundary_violation es desempate, no veto. → filtro previo.

## 6. Criterios de salida de F0

F0 esta completa cuando:

1. Existe el archivo de config unica de mision.
2. Existe el contrato formal de mision (escrito y congelado).
3. Existe el baseline P-struct minimo (con tests de regresion).
4. Banco, entrenador, acciones y simulador leen de la config unica.
5. Los 6 desajustes del punto 5 estan resueltos o explicitamente
   diferidos con justificacion.
6. Los casos de referencia coinciden entre banco y simulador.

**Lo que NO es F0:**
- No es entrenar.
- No es el interprete LLM.
- No es el verificador.
- No es la integracion.
