# BORRADOR — CLAUDE: HIPOTESIS COLABORATIVA

**Fecha:** 2026-10-14
**Estado:** BORRADOR.
**Origen:** consulta sobre hipotesis colaborativa.

---

**Correccion propia:** como todos los items de fheld_f2 tienen d<T, un
parser que ignorara la velocidad sacaria 0.500 exacto, no el 0.75-0.83
que estime. Y la hipotesis de unidades no la respalda la auditoria.
Quedan sin explicar los 7 falsos terminar del SFT.

## 1. Circuito de roles

- Alcanza con tres funciones mas un ejecutor (PID/bridge), que va
  fuera del circuito.
- Interprete: texto -> spec estructurada (el formato de F0, con
  procedencia, confianza y "no entendi").
- Verificador: valida en dos puntos: la spec (rangos, unidades,
  invariantes, conflictos) y la accion propuesta.
- Decisor: (spec validada, estado) -> accion, determinista.
- Observacion: hoy el decisor real es Qwen + reglas, asi que la
  arquitectura propuesta es un cambio respecto del sistema actual,
  no una descripcion.
- A3 midio texto+estado -> accion de punta a punta: mezcla
  interprete y decisor. No es una medicion del interprete.

## 2. Medicion por rol (oraculo en el lugar de cada uno)

- Interprete: coincidencia exacta de spec contra spec dorada, por
  campo y por item. F-held ya tiene specs doradas. Hace falta un SFT
  con objetivo texto -> spec (cambio de target respecto de A3).
  Medir tambien la calibracion de "no entendi" y el error critico
  (valor que relaja una restriccion).
- Verificador: sin LLM. Pruebas por mutacion: specs fuera de rango,
  unidades confundidas, contradicciones, y acciones con
  admisibilidad conocida. Falsos pases (criticos) y falsos bloqueos,
  mas el regret post-bloqueo.
- Decisor: con spec dorada, calidad de accion contra el Entrenador y
  en lazo cerrado.
- Descomposicion del error de punta a punta: correr el circuito con
  un oraculo en cada rol, uno por vez.

## 3. Conexion con Godot/DHS/Qwen

- "Llega a Puerto Esperanza" es un indicador de exito, no una linea
  de base comparativa. Falta la distribucion de resultados del
  sistema actual: N episodios con semillas de viento y condiciones
  iniciales variadas, midiendo exito, tiempo, violaciones, bloqueos
  y latencia.
- El LLM no se prueba donde el sistema actual ya funciona, sino
  cuando el contrato cambia por episodio (T, v_max). Qwen + reglas
  con T fijo termina a 15 m aunque el contrato pida 5 m.
- Dos familias de episodios: E-base (contrato actual; no
  inferioridad) y E-contrato (contrato variado; cumplimiento).
- Evaluador independiente: una funcion que juzga con telemetria de
  Godot y la misma MisionConfig (la funcion de etiquetado de F0), no
  el agente.
- Brazos (mismas semillas, comparacion pareada):
  - R0: sistema actual.
  - R1: spec dorada -> decisor Python + PID. Techo del circuito; no
    requiere entrenar nada.
  - R2: texto -> interprete LLM -> verificador -> decisor.
  - R3, opcional: texto -> P-text, para ver el fallo de cobertura en
    lazo cerrado.
- Orden: F0 en el DHS primero (episodios parametrizados por la config
  y su hash), despues R0 vs R1, despues R2.
- Con N=100 por brazo, el IC de una tasa del 80% es +-8 puntos.
- Subproducto: los episodios producen la evidencia dinamica
  reservada en F0 (velocidad al cruzar T).
- Cautela: LLM-A3 se entreno con estados estaticos (d, v) y decide
  acciones; en Godot habria que cuidar la latencia (~1 Hz en el lazo
  externo) y el formato del estado.

## 4. Evitar dos proyectos

- Artefactos compartidos: MisionConfig con hash, funcion de
  etiquetado/evaluacion unica y el manifiesto de identidad del
  ensayo. Los bancos offline y los episodios online salen de lo
  mismo.
- Flujo en dos sentidos: ninguna afirmacion online sobre un rol sin
  evidencia offline de ese rol; cada falla online se convierte en
  caso de regresion offline (mineria de fallas).
- Un solo expediente y un solo backlog.

## 5. Hipotesis de trabajo (falsable)

- H-circuito: un pipeline [interprete LLM -> verificador -> decisor
  determinista] cumple contratos variados y formulados libremente con
  no inferioridad respecto del sistema actual en contratos fijos y
  mejor cumplimiento en contratos variados, sin aumentar violaciones
  de restricciones.
- Evitaria "se complementan": no dice que resultado la refutaria.
- Alcance a declarar: relativa a esta distribucion de formulaciones y
  a la fisica de Polaris, con parametros todavia sin validar.
