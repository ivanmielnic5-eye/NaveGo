# BORRADOR — ALEXA Y MULTIAGENTES: QUE RESCATAR PARA NAVEGO

**Fecha:** 2026-10-13
**Estado:** BORRADOR. Fuera del expediente hasta validacion con Claude.
**Origen:** consolidacion de discusiones del 2026-10-13 sobre Alexa,
arquitectura de 3 capas, y multiagentes.

---

## 1. Como funciona Alexa

Alexa separa el problema en tres partes claras:

1. ASR (Speech-to-Text): convierte voz en texto.
2. NLU (Natural Language Understanding): traduce el texto a estructura
   formal. Produce un Intent (la accion) y Slots (los argumentos).
   Ejemplo: "poné las luces del living al 50%" ->
   {intent: "SetBrightness", slots: {device: "living", value: "50%"}}.
3. Intent Handler: recibe la estructura y ejecuta. Deterministico.

El NLU no decide. Traduce. La decision la toma el backend deterministico.

Alexa+ (2025-2026) rehizo la arquitectura: paso de un sistema
deterministico a uno con mas de 70 modelos LLM orquestados en Bedrock.
Cada modelo con su rol. No uno monolitico.

## 2. Que es rescatable

- Separacion intencion / ejecucion. El LLM traduce, el decisor ejecuta.
- Intents + Slots como puente formal. No texto libre. Estructura fija.
- El patron es anterior a los LLMs. No depende de la tecnologia.
- Orquestacion de multiples modelos: viable si se justifica.
- Verificador con guardrails explicitos.

## 3. Que NO es rescatable (limites marcados por Luna, anexo K)

- Alexa no demuestra que el interprete tenga que ser un LLM.
- "70+ modelos" no prueba que NAVEGO necesite varios modelos.
- Alexa no valida seguridad en navegacion. Interpretar "luces al 50%"
  y decidir con sensores contradictorios son problemas de distinto
  riesgo.
- La escala comercial no valida nuestra implementacion.
## 4. Los roles para Timonel

La arquitectura de 3 capas que ya tenemos:

1. Interprete (LLM): traduce lenguaje natural a spec formal (JSON).
2. Verificador (Python): valida estructura, tipos, rangos, semantica.
3. Decisor (Python): aplica la politica al estado. Deterministico.

Pregunta: ¿3 roles alcanzan o se necesitan mas?

Candidatos a roles adicionales:

- Monitor de estado: chequea que la spec sea compatible con el estado
  actual (¿el sensor funciona? ¿los datos son frescos?).
- Verificador de seguridad: chequea restricciones duras (¿frenar no
  colisiona?). Independiente del decisor.
- Gestor de dialogo: pide aclaraciones cuando la spec esta incompleta
  o ambigua.

Hipotesis de Luna (anexo K): no son "capas" fijas. Son roles con
contratos. Cada uno auditable por separado. Cada uno puede fallar sin
contaminar a los demas.

## 5. ¿3-4 agentes fijos o recombinables?

Dos posibilidades:

A. Conjunto fijo de 3-4 agentes, siempre activos.
   Simple. Predecible. Costo de GPU constante.

B. Conjunto modular que se activa segun la tarea.
   Menos GPU cuando no hace falta. Mas complejo de coordinar.
   Riesgo: fallos de coordinacion, latencia.

La idea del Director: menos agentes que Alexa (que tiene 70+), pero
que se puedan multiplicar o dividir segun lo que el sistema necesite.

Luna (pensamiento lateral) aclara: la oportunidad esta en recombinar
capacidades existentes, no en multiplicar agentes por si mismo.
Multiplicar sin justificacion agrega latencia, costos y fallos.
## 6. Preguntas abiertas para Claude

1. ¿3 roles (interprete, verificador, decisor) alcanzan para Timonel,
   o hacen falta los candidatos del punto 4?

2. Si hacen falta mas, ¿conviene un conjunto fijo (A) o modular (B)?
   ¿Como se evita que la modularidad se convierta en un proyecto
   paralelo?

3. ¿El "verifier tax" (Luna, pensamiento lateral) aplica aca? Si un
   verificador bloquea acciones inseguras pero el sistema busca
   alternativas, ¿el problema se traslada?

4. ¿Como se conecta esto con el protocolo F0-F4 del analisis de Luna?
   ¿El mapa de roles va antes o despues de F0?

5. ¿Hay algun riesgo de sobre-ingenieria con 3-4 roles? ¿Se puede
   empezar con menos?

## 7. Lo que NO se decide todavia

- No se elige cuantos roles.
- No se implementa nada.
- No se cierra la arquitectura.
- Todo esto espera validacion con Claude y con el Director.

El principio que si queda firme:
- Menos agentes que Alexa, no mas.
- Roles con contratos, no capas fijas.
- Recombinar, no multiplicar.
- Cada pieza entra cuando hay un problema concreto, no antes.
