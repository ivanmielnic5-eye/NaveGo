# REVISION DEL DISENO EXPERIMENTAL — Memoria externa en Timonel — 2026-10-05

**Proyecto:** Timonel (agente LLM local que pilota Polaris en simulador Python)
**Autor:** Directora de Investigacion
**Estado:** revision cerrada. Reemplaza partes del memo 60.
**Origen:** consulta a GPT-4 + consulta a Claude. Convergencia en 10 puntos.

---

## 0. Por que esta revision

El memo 60 cerro un diseno experimental falsable. Ese diseno tenia dos problemas que se detectaron al implementar el oraculo:

**Problema 1:** la metrica primaria era "accuracy de decision" (coincidencia exacta con el oraculo). Esto es demasiado binario — trata un empate tecnico igual que una eleccion desastrosa.

**Problema 2:** el oraculo de 30s aislado premia la inaccion cuando el barco esta desalineado. Un agente que aprenda de esto aprende a quedarse quieto.

Ambos problemas los detectamos antes de correr el benchmark grande. Pausamos. Consultamos a GPT-4 y a Claude. Esta revision consolida las correcciones.

**Lo que NO cambia:**
- La pregunta de investigacion (si la memoria mejora las decisiones).
- La exigencia de falsabilidad popperiana.
- La estructura general A/B/C/D del benchmark.
- El principio de seguridad primero.

**Lo que SI cambia:**
- La metrica primaria: de "accuracy" a "regret".
- El diseno del oraculo: sin capa de continuacion, con horizontes multiples.
- El procedimiento: se agrega validacion del oraculo + test de pilotaje puro antes del benchmark.

---

## 1. Cambio de metrica: de accuracy a regret

**Antes (memo 60):**
accuracy = % de decisiones que coinciden exactamente con el oraculo.

**Ahora (memo 61):**
regret = J_mejor - J_elegida

Donde J es el valor de la decision segun el criterio lexicografico del oraculo (seguridad > progreso > alineacion).

**Por que:**
- Accuracy tira informacion. Si el oraculo dice A y Qwen dice B, y la diferencia entre A y B es 0.93m, accuracy lo cuenta igual que si Qwen hubiera elegido la peor opcion.
- Regret conserva la magnitud. "0.93m de diferencia" es mejor que "15.4m de diferencia".
- Regret mide cuanto peor fue la decision, no si coincidio.

**Reportes obligatorios con regret:**
- mean_regret
- median_regret
- p90_regret

El promedio solo puede ocultar una cola de decisiones muy malas. Por eso tambien se reportan mediana y percentil 90.

---

## 2. Separacion de seguridad y regret

**Regla:** la violacion de seguridad no se mezcla con regret.

**Metricas separadas:**
- METRICA A — Safety violation rate: cantidad de decisiones que violan una restriccion dura / total de decisiones.
- METRICA B — Action regret: solo sobre decisiones seguras.

**Gate:**
- Si safety_violation_rate > umbral → FAIL, sin importar el regret.
- Si no → evaluar regret.

**Por que:**
Si metemos regret = infinito en el promedio, dos o tres catastrofes dominan el resultado y la metrica deja de medir calidad de decision. Pasa a medir "hubo o no catastrofe". No queremos eso.

La seguridad es un gate duro. La calidad de decision se mide aparte, solo sobre decisiones seguras.

**Umbral de safety_violation_rate:** a definir antes de correr el benchmark (memo 62 o documento aparte).

---

## 3. Retiro de la capa de continuacion

**Antes (memo 60, propuesta original de GPT-4):**
El oraculo debia, despues de ejecutar la receta, dejar que un controlador determinista continuara la navegacion. Medir el resultado final de esa continuacion.

**Ahora (memo 61):**
Sin capa de continuacion en el oraculo. Se retira.

**Por que:**
- Introducir un controlador de continuacion agrega un segundo componente sin validar.
- Si algo falla, no sabemos si fue el oraculo o el controlador de continuacion.
- Duplica la ambiguedad que queriamos evitar.

**Alternativa adoptada:**
Usar el barrido de horizontes (5/15/30/45s). Una receta cuya curva de progreso sigue mejorando con el tiempo esta mostrando que se arma bien a futuro, sin necesidad de simular mas.

La composicion global (si el oraculo sirve para misiones completas) se prueba aparte en el Oracle-Pure Pilot (seccion 5).

---

## 4. Horizontes multiples: 5 / 15 / 30 / 45 segundos

**Antes (memo 60):** horizonte unico de 30s.

**Ahora (memo 61):** 4 horizontes — 5s, 15s, 30s, 45s.

**Razon de la eleccion:**
- 5s: efecto inmediato de la receta.
- 15s: maniobra parcial.
- 30s: aproximadamente una maniobra completa (dato: Polaris gira 360 en ~53s a timon a fondo, ~30s para media maniobra).
- 45s: consecuencia extendida (~1.5 maniobras).

No usar 60 ni 120 en esta etapa. Esos horizontes empiezan a mezclar "el valor de esta decision" con "el valor de varias decisiones futuras". El oraculo debe evaluar UNA decision.

**Semantica de la receta respecto al horizonte:**

Una receta puede no controlar activamente los 45s completos. Si una receta termina a los 30s, que pasa entre 30 y 45?

**Decision:** adoptar la semantica que ya tenga Timonel. No inventar una nueva regla. Se documenta en memo 62 al momento de implementar, tras revisar el contrato real de las recetas.

**Uso de la curva de progreso:**

Con los 4 horizontes, se construye la curva de progreso de cada receta:


Con los 4 horizontes, se construye la curva de progreso de cada receta:


Con los 4 horizontes, se construye la curva de progreso de cada receta:

  5s | 15s | 30s | 45s
  ---------- | --------- | --------- | ---------
  receta A  | ... | ... | ...
  receta B  | ... | ... | ...
  receta C  | ... | ... | ...

Una receta cuya curva sigue mejorando con el tiempo esta mostrando que se arma bien a futuro. Una que mejora y despues empeora tiene overshoot. Una que no mejora nunca es inutil.

Clasificacion de curvas:
- mejora inmediata: progreso positivo en 5s y sigue creciendo.
- mejora tardia: progreso negativo en 5s, positivo en 30s.
- estable: progreso constante.
- overshoot: mejora y despues empeora.
- deterioro: empeora con el tiempo.

Esto da informacion sin necesidad de simular continuacion.

## 5. Oracle-Pure Pilot — validacion contra la realidad

**Proposito:** validar que las decisiones del oraculo COMPONEN una politica que llega a la meta.

**Procedimiento:**

Episodio completo sin Qwen, sin memoria:
1. Estado inicial.
2. El oraculo elige la mejor receta.
3. Un controlador determinista la ejecuta.
4. Nuevo estado.
5. El oraculo elige otra vez.
6. Repetir hasta llegar o timeout.

**Mediciones:**
- success_rate (tasa de llegada a la meta).
- time_to_goal.
- grounding_rate (encalladuras).
- collision_rate.
- overshoot.
- path_efficiency.

**Diagnostico que permite:**

Si el oraculo local es bueno (validacion interna pasa) PERO el Oracle-Pure Pilot tiene success_rate bajo:
-> la metrica local del oraculo NO compone.
-> NO es problema de Qwen.
-> NO es problema de memoria.
-> Es problema de la funcion con la que definimos buena accion.

Esto ahorra trabajo. Si no compone, no tiene sentido seguir con la memoria.

**Si el oraculo local es bueno Y el Oracle-Pure Pilot funciona:**
-> recien ahi el benchmark de memoria tiene sentido.

---

## 6. Definir near-tie antes de correr

**Problema:** si dos recetas dan progreso 12.10 y 12.08, el oraculo declara ganador y perdedor. Pero la diferencia esta dentro del ruido del simulador.

**Solucion:** definir NEAR_TIE antes de correr.

NEAR_TIE = diferencia < epsilon

epsilon debe salir de la resolucion efectiva del simulador. Se calcula midiendo la variacion del mismo estado inicial repetido N veces.

**Uso:**
- Si dos recetas estan dentro de NEAR_TIE, ambas son validas. El oraculo devuelve multiples respuestas correctas.
- Si Qwen elige cualquiera de las dos, no cuenta como regret.

Sin esto, el criterio de 70-80 por ciento winner coincidence castiga al oraculo por oscilaciones numericas sin significado fisico.

---

## 7. Tunneling en colisiones — verificar

**Problema:** si evaluamos posicion a 60 Hz, una colision rapida puede pasar entre dos frames sin detectarse.

**Verificacion:**
No alcanza con chequear posicion(t). Hay que chequear si el segmento entre posicion(t-dt) y posicion(t) cruzo una region prohibida.

Conceptualmente:
posicion(t-dt) ---segmento--- posicion(t)
         |
         v
interseccion con obstaculo o area de encalladura

**Accion:** antes de implementar el oraculo definitivo, verificar si las geometrias actuales permiten resolucion con segment intersection / swept test simple. No agregar motor de colisiones sofisticado todavia.

---

## 8. Escritura en memoria gatillada por resultado real

**Regla:** la entrada a memoria NO depende del veredicto del oraculo. Depende del resultado real de la ejecucion.

**Incorrecto:** el oraculo dice buena -> guardar en memoria.

**Correcto:**
1. Decision.
2. Se ejecuta.
3. Episodio produce resultado.
4. Resultado se registra.
5. Memoria candidata.

**Trazabilidad obligatoria.** Cada entrada de memoria guarda:
- oracle_version.
- physics_version.
- scenario_version.
- policy_version.

Razon: si dentro de seis meses cambiamos el criterio del oraculo, no queremos mezclar una experiencia validada bajo oracle-v1 con otra validada bajo oracle-v2. Mismo patron de filter_version que ya usa NaveGo.

---

## 9. Memoria con experiencias favorables Y desfavorables

**Regla:** no guardar solo exitos.

Una experiencia negativa puede ser util:
estado S + receta X + resultado malo -> ensena no hacer X desde S.

La memoria debe distinguir al menos:
- experiencia favorable.
- experiencia desfavorable.

Ambas respaldadas por el resultado real, no por la opinion del oraculo.

---

## 10. Orden experimental definitivo

El orden cambia respecto al memo 60. Ya no empezamos por el benchmark de memoria.

Etapa 1 - ORACLE VALIDATION:
- 10 estados controlados.
- 4 horizontes (5, 15, 30, 45s).
- Metricas separadas: safety rate + regret.
- Criterios numericos definidos antes.
- PASA o FALLA.

Etapa 2 - ORACLE-PURE PILOT:
- Episodios completos con oraculo + controlador determinista.
- Sin Qwen. Sin memoria.
- Medicion: tasa real de llegada a la meta.
- Si no llega, el oraculo no compone.

Etapa 3 - solo si las dos anteriores pasan:
- BENCHMARK de memoria A/B/C/D.
- A = Qwen sin memoria.
- B = Qwen con retrieval actual.
- C = Qwen con memoria curada.
- D = Qwen con memoria enganosa.
- Seeds emparejadas.
- Metrica primaria: regret. Gate: safety rate.

La logica:
oraculo valido -> oraculo compone -> metrica valida -> memory evaluation.

---

## 11. Lo que NO se hace en esta fase

- No continuacion determinista dentro del oraculo.
- No embeddings.
- No aumento de corpus.
- No cambio de Qwen.
- No benchmark de 200 seeds todavia.
- No motor de colisiones sofisticado.

---

## 12. Cierre

Esta revision reemplaza las secciones correspondientes del memo 60. Lo que no contradice al 60, sigue vigente.

La cadena causal queda:
oraculo valido -> oraculo compone -> metrica valida -> memory evaluation.

Solo se pasa a la etapa siguiente si la anterior pasa.

---

*Documento cerrado. Si se necesita modificar, se crea un 62_REVISION_2.md.*
*Fecha: 2026-10-05.*
*Registrado en EXPEDIENTE/61.*
