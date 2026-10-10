# HALLAZGOS DE INVESTIGACION EXTERNA — Aplicables a Timonel

**Fecha:** 2026-10-11
**Autor:** Directora de Investigacion (con acceso a internet)
**Estado:** ABIERTO. Insumo para mejorar las variantes de prompt.
**Complementa:** memos 73, 74, 75, 76, 77.

---

## 0. Proposito

Traer el estado del arte sobre como se ensena a LLMs a operar en entornos
agenticos, especificamente sobre seleccion de acciones. Luna y Llama no
tienen acceso a internet. Esa responsabilidad es mia.

---

## 1. HALLAZGO PRINCIPAL: COMPASSNav — CAMBIO DE PARADIGMA

Paper: CompassNav (ICLR 2026). Steering From Path Imitation to Decision
Understanding in Navigation.

Idea central: el paradigma dominante de "imitar trayectorias expertas"
limita la capacidad del agente. Proponen un cambio de paradigma: construir
agentes que "no solo sigan, sino que entiendan como navegar".

Como lo hacen:
- Dataset de 22k trayectorias (Compass-Data-22k).
- El subset de RFT anota TODAS las acciones factibles con distancias
  geodesicas A*.
- Reward function hibrida que adapta su feedback a la certeza de la
  decision: señales decisivas para acciones optimas, señales mas suaves
  para explorar alternativas.
- Receta: SFT + RFT (Reinforcement Fine-Tuning).

Resultado: agente 7B alcanza estado del arte en Goal navigation, superando
incluso a modelos propietarios mas grandes. Funciona en robot real.

IMPLICACION PARA NOSOTROS:
El exito de CompassNav sugiere que la clave NO es solo dar la accion
correcta en el prompt. Es dar el "paisaje de decisiones" completo:
todas las acciones factibles con su calidad relativa. Eso es distinto
a reglas condicionales (que dan la respuesta) y distinto a un contrato
pobre (que solo describe acciones sin consecuencias).

---

## 2. ACTION SPACE Y PROMPT CONTRACT

Hallazgo de literatura (Berkeley, 2024-2026):
"our input prompt contains a description of the task, the legal action
space of the current observation, and the desired output format."

Es decir: el prompt debe incluir las ACCIONES LEGALES (admisibles) en el
estado actual, no solo las acciones disponibles en general.

Diferencia clave:
- Acciones disponibles: las 4 siempre.
- Acciones admisibles en este estado: subconjunto que tiene sentido.
  Ej: si dist > 15m, "terminar" NO es admisible.

IMPLICACION PARA NOSOTROS:
El prompt actual lista las 4 acciones siempre. Una mejora seria listar
solo las admisibles dado el estado, y marcar las no admisibles. Esto NO
es una regla condicional (no dice CUAL elegir). Es especificacion del
espacio de accion.

---

## 3. PROMPT COMO CONTRATO (Prompt-as-Contract)

Hallazgo de literatura de ingenieria de agentes:
El prompt no es una "oracion de comando" sino un "contrato de entrada-salida".
Debe tener:
1. Proposito (que intenta lograr el agente).
2. Restricciones (que NO puede hacer).
3. Contrato de herramienta (que recibe, que devuelve).
4. Condiciones de finalizacion (cuando la tarea esta completa).

La debilidad de prompts pobres esta en MEZCLAR estos componentes.
Separados, el modelo puede procesarlos mejor.

IMPLICACION PARA NOSOTROS:
Nuestro prompt actual mezcla estado, acciones y pedido de JSON en un solo
bloque. Una mejora es SEPARAR:
- PROPOSITO (mision general).
- ESTADO (datos actuales).
- ESPACIO DE ACCION (que acciones existen, que hace cada una).
- ACCIONES ADMISIBLES (subconjunto valido para este estado).
- FORMATO (JSON).
- RESTRICCIONES (terminar solo si dist<15m).

---

## 4. FINE-TUNING: SFT + DPO

Evidencia solida de multiple fuentes:
- Qwen3-4B Agent Trajectory DPO Adapter (HuggingFace, 2026):
  Entrena Qwen3-4B con LoRA + DPO sobre SFT previo.
  Fallos objetivo: "action loops" (seleccionar la misma accion sin
  progreso), "premature task success" (decir que termino antes de
  lograrlo), "irrelevant exploration".
  Nuestro Qwen 3B/7B colapsa a corregir_rumbo = "action loop" clasico.

- Verified Critical Step Optimization (CSO, Tencent AI Lab):
  Identifica "critical steps" donde acciones alternativas cambian el
  resultado. Usa DPO con datos verificados. Mejora 37% y 26% sobre SFT.
  Supervision en solo 16% de los pasos.

- SPaRK (Stanford, 2026): Entrena Llama-3.1 8B con PPO offline para
  seleccion de herramientas.
  Baseline Llama-3.1 8B: 22.4% accuracy.
  SFT: 26.2%.
  PPO estandar: 33.0%.
  SPaRK (con diversidad de herramientas): 40.8%.
  → Llama 3.1 8B PUEDE mejorar sustancialmente con entrenamiento.

IMPLICACION PARA NOSOTROS:
Si el zero-shot con contrato completo falla, SFT+DPO con el banco CC002
es un camino documentado y con precedentes. No es un salto al vacio.

---

## 5. ARQUITECTURAS HIBRIDAS (neuro-simbolico)

Evidencia de multiple papers:
- VL-Nav (DARPA TIAMAT): sistema neuro-simbolico con planificador de
  tareas + grafo de escena 3D simbolico. 83.4% exito indoor, 86.3% real.
- SGIM-STAR (NeurIPS 2025): alterna entre Q-learning Navigator y LLM
  Navigator. Consulta al LLM solo cuando es beneficioso.
- DORAEMON: Action Proposer genera acciones candidatas, Policy-VLM evalua
  para decision final.

IMPLICACION PARA NOSOTROS:
Una arquitectura hibrida (LLM propone, logica simbolica filtra) es una
alternativa documentada. No es rendirse: es una decision de ingenieria
con precedentes solidos.

---

## 6. ACCIONES ADMISIBLES: EL PUNTO MEDIO

Hallazgo concreto del prompt de GiGPO-Qwen2.5-7B-Instruct-ALFWorld:
"Your admissible actions of the current situation are: [{admissible_actions}]."

Esto es EL PUNTO MEDIO entre reglas y contrato pobre:
- No le dice QUE elegir.
- Le dice QUE PUEDE elegir.
- Le da el espacio de decision filtrado por validez.

En nuestro caso, para cada estado:
- Si dist < 15m: admisibles = {corregir_rumbo, ir_a_punto, frenar, terminar}.
- Si dist >= 15m: admisibles = {corregir_rumbo, ir_a_punto, frenar}.
  (terminar NO es admisible porque seria invalido).

Eso NO es una regla condicional estado->accion. Es especificacion de
validez.

---

## 7. RECOMENDACIONES CONCRETAS PARA LAS VARIANTES

Enriquecer las 3 variantes preregistradas en memo 77 con:

### VB revisada (contrato corregido)
Agregar:
1. Separacion clara de secciones (proposito, estado, acciones, formato).
2. Seccion de ACCIONES ADMISIBLES en el estado actual.
3. Consecuencias de cada accion (no solo "que hace" sino "que pasa si").

### VC revisada (contrato + enfasis visual)
Agregar:
1. Todo lo de VB.
2. Campos criticos en MAYUSCULAS.
3. Separadores visuales (===) entre secciones.
4. Distancia a meta con umbral explicito al lado.

### Nueva VD (few-shot estructurado)
Agregar:
1. Todo lo de VB.
2. 4-8 ejemplos resueltos, uno por accion, con distintos estados.
3. Los ejemplos usan estados del split DESARROLLO (no confirmatorio).

---

## 8. BASELINES QUE FALTAN (segun Luna + literatura)

1. Aleatorio uniforme: 25%.
2. Prediccion constante (siempre la clase mayoritaria): 25% en CC002.
3. Politica explicita simple: implementar despues como control.
4. Piloto Python: comparador operacional.
5. Oraculo: referencia de etiquetas.

Los primeros 2 son triviales de implementar. Los otros 3 ya existen.

---

## 9. LO QUE NO SE HACE TODAVIA

- No se fine-tunea. Primero hay que agotar el zero-shot con contrato.
- No se cambia de modelo. Llama 3.1 8b es el candidato actual.
- No se toca el confirmatorio.
- No se corre el benchmark formal hasta tener el prompt calibrado.

---

## 10. FIRMA

**Estado:** ABIERTO. Insumo para revisar memo 77.
**Proximo paso:** actualizar las variantes del memo 77 con estos hallazgos.
**Referencia:** investigacion externa 2026-10-11.
