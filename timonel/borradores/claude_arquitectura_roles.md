

<!-- ingesta: 2026-10-13 19:02 -->

# BORRADOR — CLAUDE: ARQUITECTURA DE ROLES E INTERFACES

**Fecha:** 2026-10-13
**Estado:** BORRADOR. Fuera del expediente hasta validacion con Luna.
**Origen:** consulta a Claude sobre Alexa, multiagentes, y arquitectura
de Timonel.

---

## Dos hallazgos en el inventario

**Hallazgo 1: boundary_violation es el ultimo elemento del ranking.**

En entrenador_v2.py, el sort es:
(not mission_complete, -progreso_medio, -alineacion_deg, boundary_violation)

Si el sort es ascendente, boundary solo desempata. Una accion que cruza
los 500 m puede ganar si progresa mas. Una restriccion dura debe ser un
FILTRO PREVIO (veto), no un criterio de orden.

**Hallazgo 2: el 0.3 nudos aparece en tres lugares.**
- Default de frenar.
- v_max del probe.
- Implicitamente, "baja velocidad" en terminar.

Es un contrato implicito, igual que T=15. Deberia estar en la
configuracion de mision, no disperso.

## 1. ¿Alcanzan 3 roles?

Alcanzan 3 funciones (interprete, verificador, decisor), pero el
tercero que veo en el codigo es ejecutor (el PID). El decisor es Python
solo en la arquitectura hibrida; en A2/A3 el LLM decide.

Esa tension importa para medir. Si el producto final es "LLM
interpreta, Python decide", cada rol necesita su propia unidad de
prueba: extraccion texto->spec con coincidencia exacta para el
interprete, bloqueo correcto para el verificador, regret para el
decisor. Medir al LLM decidiendo mide el brazo monolitico, no el
pipeline.

- Monitor de estado: modulo deterministico (estimador de sensores y
  calidad de informacion). No es un agente; pertenece a la fase
  ulterior del Director.
- Verificador de seguridad vs. de contrato: un solo modulo con dos
  conjuntos de reglas. Las fuentes de verdad son distintas (fisica vs.
  mision), los agentes no.
- Gestor de dialogo: una politica, no un modelo; solo hace falta con
  abstencion o confirmacion. Diferirlo.
- Sobra pensar en "multiagentes": los 70+ modelos de Alexa cubren
  amplitud de dominios; NAVEGO tiene uno.

## 2. ¿Intents/slots?

- Sirve en la capa de comandos ("anda a la boya 3, max. 2 nudos"):
  slots tipificados, con unidades normalizadas a SI en la salida del
  interprete y validacion de rango.
- Es demasiado rigido para contratos: no expresa "excepto si",
  prioridades ni conjunciones. Para eso hace falta un esquema
  declarativo chico (el del motor P-struct).
- Tomaria de Alexa dos cosas mas: la confianza del NLU con intent de
  fallback (el "no entendi" del interprete es la base de la
  abstencion) y la confirmacion en slots de alto riesgo.

## 3. ¿Fijo o modular?

- Roles fijos como interfaces (esquemas JSON), implementaciones
  intercambiables. "Activar modulos por tarea" exige un router, que
  es otro punto de falla con sus propias pruebas.
- Lo "recombinable" que si conviene: intercambiar la implementacion de
  un rol (interprete LLM <-> P-text <-> motor). Con interfaces
  identicas, los brazos de A3 son enchufables, que es lo que la
  comparacion necesita.
- Los modulos opcionales (dialogo, monitor) se activan por bandera en
  la configuracion de mision, no por decision dinamica.

## 4. Verifier tax

- No reintentar hasta que algo pase (best-of-n contra el verificador
  selecciona justo lo que lo engana). Un reintento como maximo, y
  despues un fallback.
- Verificar el conjunto de candidatos y rankear solo entre los
  aprobados, en vez de probar uno por uno.
- Fallback seguro predefinido y ordenado (por ejemplo, mantener rumbo
  y velocidad controlada, o pedir confirmacion).
- Verificador con veredicto y razon estructurada, nunca un "reintenta"
  abierto.
- Medirlo: tasa de bloqueos y regret post-bloqueo (utilidad de la
  accion finalmente ejecutada contra la mejor aprobada segun el
  Entrenador). Preregistrar el umbral.
- Con el simulador actual solo se puede probar con el boundary de 500
  m; es suficiente para un primer test.

## 5. detener / ajustar_velocidad / frenar

- Separacion por que compromete cada cosa, siguiendo la cascada:
  primitivas = setpoints (rumbo_obj, sog_obj, y ir_a, que genera
  rumbo_obj); el PID de rumbo ejecuta el primero y haria falta un lazo
  de velocidad para el segundo.
- frenar y ajustar_velocidad colapsan en una primitiva: fijar sog_obj.
  detener es una intencion (sog_obj ~ 0 mas una condicion de llegada),
  no una primitiva.
- Limitacion fisica a revisar con el Director: un velero no se detiene
  "a voluntad" (sin motor, se desacelera con la proa al viento o con
  maniobras). Que mecanismo representa frenar en Polaris es una
  decision nautica, no del equipo tecnico.

## 6. Orden de fases

- F0 es correcta y bloqueante: debe ser un test automatico de
  configuracion unica (T y v_max leidos de un solo lugar por banco,
  entrenador, acciones y simulador). Es barato y las etiquetas de A3
  dependen de el.
- Falta el interprete como fase propia (texto->spec) antes de las
  pruebas de decision.
- Falta el verificador aislado (bloqueo correcto y tasa de falsos
  bloqueos) antes de integrarlo.
- Lo ultimo: integracion de punta a punta en lazo cerrado.
- Orden propuesto: F0 config unica -> interprete -> verificador
  aislado -> decisor/Entrenador alineado -> integracion en lazo
  cerrado. Monitor y dialogo despues.
