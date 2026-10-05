# REVISION 2 DEL DISENO EXPERIMENTAL — Memoria externa en Timonel — 2026-10-05

**Proyecto:** Timonel (agente LLM local que pilota Polaris en simulador Python)
**Autor:** Directora de Investigacion
**Estado:** revision cerrada. Reemplaza partes del memo 61.
**Origen:** consulta a GPT-4 + consulta a Claude + consulta a Notebook LLM. Convergencia en correccion conceptual.

---

## 0. Por que esta segunda revision

El memo 61 corrigio un problema del memo 60 (regret vs accuracy, sin capa de continuacion, Oracle-Pure Pilot). Pero al empezar a implementar el benchmark de memoria detectamos un error conceptual mas profundo.

**El error:** estabamos congelando el ESTADO FISICO como unidad experimental. Pero el agente no decide desde el estado fisico — decide desde un CONTEXTO que incluye historial.

Analogia: dos cirujanos no estan en la misma situacion solo porque el paciente es el mismo, si uno tiene la historia clinica completa y el otro no.

**Consecuencia:** el benchmark debe medir sobre COMMON-CONTEXT (estado + historial), no sobre COMMON-STATE (solo estado).

---

## 1. Correccion conceptual: COMMON-CONTEXT

**Antes (memo 61):** la unidad experimental era el estado fisico S. A y B deciden desde el mismo S.

**Ahora (memo 62):** la unidad experimental es el contexto C = (S, H). Donde:
- S = estado fisico actual.
- H = historial de contexto disponible al agente.
- C = contexto completo desde el cual decide.

A y B reciben exactamente el mismo C, salvo por la disponibilidad de memoria externa.

Esto lleva a tres condiciones experimentales, no dos.

---

## 2. Las tres condiciones (opcion Z)

**A:** estado solo. Sin historial. Sin memoria.
**A_prima:** estado + historial. Sin memoria.
**B:** estado + historial + memoria.

Contrastes:

- **A_prima - A:** efecto del historial.
- **B - A_prima:** efecto marginal de la memoria externa.
- **B - A:** efecto total del sistema.

**Contraste primario: B - A_prima.** Eso aisla el efecto de la memoria sin confundirlo con el efecto del historial.

**Por que no usar X (A y B con historial):** el A original en produccion NO tiene historial. Medir A con historial no es medir el A real.

**Por que no usar Y (A solo estado, B con todo):** B - A mezcla historial + memoria. No permite atribuir causalmente el efecto a la memoria.

**Nota:** existe una opcion W (factorial 2x2 completo: A, A_prima, C, B). Agrega C = estado + memoria sin historial. Permite medir interaccion historial x memoria. No es obligatoria en esta fase.

---

## 3. Origen del historial

Cada COMMON-CONTEXT debe tener un historial H causalmente compatible con el estado S. No se puede mezclar el historial de una corrida con el estado de otra.

**De donde sacar el historial:** banco de trayectorias generado por mezcla de politicas independientes de A y B.

- P1: baseline determinista.
- P2: Qwen sin memoria.
- P3: Qwen con memoria.
- P4: oraculo puro.
- P5: variantes perturbadas.

**Por que mezcla:** no queremos que el historial venga solo de A (favorece una distribucion) ni solo de B (opuesto). Ni solo del oraculo (todos los estados serian nominales). La mezcla representa distintas formas plausibles de llegar a un estado.

**Cada COMMON-CONTEXT conserva:**
- historial real (secuencia de estados + acciones previas).
- estado exacto producido por ese historial.
- origen de la politica que lo genero (para auditoria).

El origen NO se le informa a Qwen.

**Estratificacion:** los contextos se estratifican por:
- distancia a meta (cerca / lejos).
- error angular (bajo / alto).
- viento (bajo / alto).
- fase de mision (primera meta / segunda meta).

Razon: evitar terminar con 200 contextos donde 170 son faciles y 20 son extremos. La distribucion debe representar la region donde queremos medir el efecto.

---

## 4. Historial operativo minimo

No se pasa el historial completo de 14 pasos. Eso introduciria una variable de "longitud del prompt" que perjudicaria a B por pura carga contextual.

**Historial operativo minimo:**
- ultimos K estados.
- ultimas K acciones.
- tiempo desde ultima maniobra.
- tendencia de heading.
- tendencia de SOG.
- fase de mision.

K se define segun el contrato real de Timonel. No se inventa.

---

## 5. Memoria congelada (evitar cold-start y leakage)

**Problema:** si B arranca con SQLite vacia, esta en cold-start artificial. Si la memoria se construye con los propios casos de evaluacion, hay leakage.

**Solucion:**
1. Construir un snapshot de memoria antes del benchmark.
2. Congelarlo. No cambia durante el benchmark.
3. Verificar que no contiene ninguno de los contextos de evaluacion.

**Protocolo:**
- TRAINING MEMORY SNAPSHOT (preconstruido, congelado).
- COMMON-CONTEXT benchmark (usa el snapshot, no modifica).

---

## 6. Versiones congeladas

No solo se congela el COMMON-CONTEXT. Tambien:

- MEMORY_SNAPSHOT (la base SQLite usada por B).
- PROMPT_VERSION (el prompt exacto que usa Qwen).
- RECIPE_VERSION (las recetas).
- ORACLE_VERSION (el oraculo).
- SIMULATOR_VERSION (el simulador).

Cada uno lleva un identificador y un hash. Si mañana cambiamos cualquier cosa, el experimento anterior no se puede confundir con el nuevo.

---

## 7. Tamano muestral

**N=200 COMMON-CONTEXTS.**

Cada contexto genera 3 ejecuciones (A, A_prima, B). Total: 600 ejecuciones.

**PERO N estadistico = 200.** No 600. Los contextos son las unidades experimentales. Las ejecuciones estan pareadas dentro de cada contexto.

**Justificacion:** para detectar 10 pp de diferencia en regret con potencia 0.8, N=96 (asumiendo sigma_d=0.35). N=160 cubre sigma_d=0.45. N=200 da margen.

**Antes del experimento definitivo:** piloto de 50-100 contextos para estimar varianza real. Despues se decide N definitivo.

---

## 8. Analisis estadistico

**Contraste primario:** B - A_prima (efecto de la memoria sin confundir con historial).

**Test:** bootstrap pareado BCa (10.000 resamples).

**Por que no Wilcoxon:** cuando A y B toman la misma decision, la diferencia es 0. Wilcoxon las ignora o requiere correccion de Pratt. Bootstrap BCa las maneja de forma nativa.

**Unidad del bootstrap:** COMMON-CONTEXT. Nunca tokens, decisiones fragmentadas, ni estados dependientes como iid.

**Reportes obligatorios:**
- Media del delta (regret A_prima - regret B).
- Mediana del delta.
- IC 95% (BCa).
- Proporcion de empates.
- p-value.

**Contrastes secundarios:**
- B - A (efecto total).
- A_prima - A (efecto historial).

**Correccion de multiplicidad:** si se reportan los 3 contrastes, aplicar Holm-Bonferroni.

**Metrica de seguridad separada:** safety violation rate se reporta como gate duro independiente del regret.

---

## 9. Local vs Global — dos experimentos

**Benchmark LOCAL (COMMON-CONTEXT):**

Pregunta: dado exactamente el mismo contexto, la memoria cambia la calidad de la decision?

- 200 contextos congelados.
- 3 condiciones (A, A_prima, B).
- Metrica: regret pareado contra oraculo.
- Gate: safety violation rate.

**Benchmark GLOBAL (FULL MISSIONS):**

Pregunta: la disponibilidad de memoria produce mejores misiones completas?

- N corridas completas.
- 2 condiciones (A, B).
- Metrica: tasa de exito, tiempo, eficiencia de trayectoria.
- Unidad experimental: la corrida.

**Los dos se complementan:**

- LOCAL mejora, GLOBAL no: problema de composicion (decisiones buenas no llevan a mision buena).
- GLOBAL mejora, LOCAL no: efecto acumulativo que la metrica local no captura.
- Ninguno mejora: hipotesis de memoria debilitada.
- Ambos mejoran: memoria aporta valor comprobable.

---

## 10. Orden experimental definitivo

**Etapa 1 (cerrada):** Oracle Validation PASS. 3/3 criterios.
**Etapa 2 (cerrada):** Oracle-Pure Pilot PASS. 100/100 misiones.

**Etapa 3a:** construir COMMON-CONTEXT-001 (200 contextos congelados).
**Etapa 3b:** construir snapshot de memoria congelado.
**Etapa 3c:** correr A, A_prima, B sobre los 200 contextos.
**Etapa 3d:** evaluar con oraculo (regret + safety).
**Etapa 3e:** analisis estadistico (bootstrap pareado BCa).

**Etapa 4:** benchmark GLOBAL (misiones completas A vs B).

**Etapa 5:** recien ahi, si hay efecto positivo, ajustar retrieval.

---

## 11. Lo que NO se hace en esta fase

- No se afina el retrieval todavia.
- No se cambia Qwen.
- No se agrega capa de continuacion al oraculo.
- No se hacen embeddings.
- No se aumenta el corpus.
- No se corre el benchmark de 500 seeds.

Primero queremos saber si, con un experimento correctamente aislado, existe siquiera un efecto de memoria.

---

## 12. Cierre

Esta revision reemplaza las secciones correspondientes del memo 61.

**La correccion conceptual mas importante:**

Antes preguntabamos: la memoria ayuda cuando A y B parten del mismo ESTADO?

Ahora preguntamos: la memoria ayuda cuando A y B reciben exactamente la misma informacion disponible del presente (contexto), y la unica diferencia experimental es la memoria externa?

Esto lleva naturalmente de COMMON-STATES a COMMON-CONTEXTS.

Y una vez establecido eso, el resultado del benchmark GLOBAL respondera:

Esa mejora local, si existe, realmente compone en una mejora de la mision?

Esa es la cadena experimental limpia.

---

*Documento cerrado. Reemplaza partes del memo 61.*
*Si se necesita modificar, se crea un 63_REVISION_3.md.*
*Fecha: 2026-10-05.*
*Registrado en EXPEDIENTE/62.*
