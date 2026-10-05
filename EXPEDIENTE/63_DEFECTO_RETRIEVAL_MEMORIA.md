# DEFECTO DE RETRIEVAL EN MEMORIA EXTERNA — Timonel — 2026-10-05

**Proyecto:** Timonel (agente LLM local que pilota Polaris en simulador Python)
**Autor:** Directora de Investigacion
**Estado:** hallazgo documentado. Requiere correccion antes del benchmark completo.
**Origen:** benchmark local (memo 62) con N=5 contextos congelados.

---

## 0. Por que este memo

El memo 62 definio el benchmark local: 3 condiciones (A, A_prima, B) sobre 350 contextos congelados, midiendo regret contra el oraculo multi-horizonte.

Corrimos un test exploratorio de N=5 contextos. Encontramos un defecto reproducible.

Este memo documenta:
1. El hallazgo con evidencia.
2. El mecanismo causal que lo produce.
3. La correccion que corresponde (contrato de recuperacion v2).
4. El plan de regresion y validacion.

**Regla metodologica:** este memo NO reescribe el resultado del memo 62. Preserva la version original. Define la version corregida. Ambas quedan registradas.

---

## 1. El hallazgo

Corrida de N=5 contextos con 3 condiciones (A, A_prima, B):



**Patron detectado:**

- **A_prima difiere de A en 2/5 contextos.** Cuando cambia, mejora drasticamente (48.5 a 0.0). El historial conversacional aporta valor.
- **B es identico a A en 5/5 contextos.** La memoria externa revierte la mejora del historial.
- **Regrets muy altos (30-49m).** El oraculo elige recetas con mucho mejor progreso que Qwen.

**Frase clave:** el historial conversacional esta demostrando valor; la memoria externa esta introduciendo ruido.
---

## 2. Investigacion del contexto 2

Analizamos el contexto 2 (donde B revierte la mejora):

**Estado:**
- Barco a media distancia de meta.
- Desvio bajo.

**Decision del oraculo:** ir_a_punto. Regret esperado = 0.0.

**Lo que inyecta la memoria:**

EXPERIENCIAS PREVIAS (situaciones parecidas):
  1. dist=61m desvio=3deg sog=3.2kn -> corregir_rumbo(objetivo=359) exito=True
  2. dist=53m desvio=5deg sog=3.4kn -> corregir_rumbo(objetivo=92)  exito=False
  3. dist=53m desvio=5deg sog=3.4kn -> corregir_rumbo(objetivo=94)  exito=False

**Lo que decide Qwen 1.5B:** corregir_rumbo. Regret = 48.5.

**Mecanismo causal:**

1. El retrieval recupera 5 experiencias similares.
2. El filtro de consenso deja 3.
3. 2 de las 3 estan marcadas con exito=False.
4. Qwen 1.5B lee el bloque y copia la accion corregir_rumbo.
5. No discrimina el flag exito=False.

**Diagnostico:** misaligned experience replay. La memoria recupera experiencias que parecen relevantes pero llevan a decisiones malas. Qwen 1.5B las obedece porque no distingue entre hacer esto y evitar esto.

---

## 3. El defecto de diseno

**No es un bug del codigo.** Es un defecto de diseno de la version actual de la memoria, denominada MEMORY-v1.

**Enunciado del defecto:**

La arquitectura actual de la memoria no posee un mecanismo fiable para convertir experiencias negativas en conocimiento negativo. Un modelo chico, como Qwen 1.5B, trata cualquier experiencia con estado parecido como recomendacion positiva, sin importar el flag de exito.

**Consecuencia:**

El contrato de recuperacion actual permite que experiencias fallidas contaminen las decisiones del agente. Eso introduce un sesgo sistematico hacia las acciones que estan sobre-representadas en la memoria, sin importar si esas acciones fueron exitosas o no.
---

## 4. Contrato de recuperacion v2 (MEMORY-v2)

**Principio rector:**

Las experiencias exitosas pueden entrar como recomendacion positiva. Las experiencias fallidas NO entran como recomendacion positiva en esta version.

**Razon:** Qwen 1.5B no discrimina el flag exito=False en el prompt. Un modelo mas grande podria hacerlo, pero el que usamos no. Entonces la carga de filtrar tiene que estar en el retrieval, no en el LLM.

**Implementacion:**

- Cambiar solo_exitos=False por solo_exitos=True en la llamada a recuperar_similares.
- Las experiencias fallidas se conservan en la base de datos, para analisis futuro. No se borran.
- Cuando exista una representacion explicita de evitar (por ejemplo, un bloque EXPERIENCIAS A EVITAR), se podran reincorporar. Pero no en esta version.

**Trazabilidad:** cada entrada de memoria lleva:

- oracle_version
- physics_version
- scenario_version
- policy_version
- outcome (exito o fallo)

**Version congelada:** la version anterior se denomina MEMORY-v1 y queda intacta. La version corregida es MEMORY-v2.

---

## 5. Plan de regresion

**Antes de correr el benchmark de 350 contextos:**

1. Aplicar el fix de MEMORY-v2 (solo_exitos=True).
2. Repetir los 5 contextos que mostraron el defecto.
3. Comparar:

   Contexto 2 con MEMORY-v1: B=corregir_rumbo, regret=48.5
   Contexto 2 con MEMORY-v2: B=? (esperado: ir_a_punto, regret=0.0)

**Criterios:**

- Si B-v2 mejora en los 2 contextos problematicos: el fix funciona. Escalar a 350.
- Si B-v2 sigue igual que v1: el defecto es mas profundo. Revisar prompt y modelo.
- Si B-v2 mejora pero menos de lo esperado: documentar el efecto parcial.

**No se reescribe el resultado de MEMORY-v1.** Se preserva como referencia.

---

## 6. Preservacion del resultado original

El resultado N=5 de MEMORY-v1 se guarda como MEMORY_DEFECT_001.json. Contiene:

- Los 5 contextos evaluados.
- Las decisiones de A, A_prima y B con MEMORY-v1.
- Los regrets correspondientes.
- El analisis del contexto 2 con el bloque de experiencias inyectado.

Sirve como regresion: si en el futuro se cambia el retrieval o el prompt, se puede repetir sobre los mismos 5 contextos y comparar.

---

## 7. Cierre

**Hallazgo mas importante:** no es que la memoria externa falle. Es que la implementacion actual de la memoria, MEMORY-v1, no distingue entre experiencias para imitar y experiencias para evitar. Un modelo chico las trata igual.

**Lo que se preserva:** el resultado del memo 62 no se reescribe. Se anota como el comportamiento de MEMORY-v1.

**Lo que se corrige:** se define MEMORY-v2 con contrato de recuperacion que solo usa experiencias exitosas como recomendacion positiva.

**Lo que se valida:** los 5 contextos de regresion. Si pasan, escalamos a 350 contextos.

---

*Documento cerrado. Si se necesita modificar, se crea un 64_REVISION_3.md.*
*Fecha: 2026-10-05.*
*Registrado en EXPEDIENTE/63.*
