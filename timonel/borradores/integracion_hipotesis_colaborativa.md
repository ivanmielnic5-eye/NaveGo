# BORRADOR — INTEGRACION DE LAS HIPOTESIS COLABORATIVAS

**Fecha:** 2026-10-14
**Estado:** BORRADOR. Espera decision del Director.
**Fuentes:** borradores claude_hipotesis_colaborativa.md,
luna_hipotesis_colaborativa.md.

---

## 1. Donde coinciden

Claude y Luna coinciden en el fondo:

1. **No es "LLM vs Python".** Es como se complementan. La pregunta
   no es quien gana, es como se articulan.

2. **Circuito minimo:** interprete + verificador + decisor. El
   ejecutor (PID/controlador) queda fuera del circuito.

3. **Medicion por rol.** Cada rol con su oraculo. No mezclar metricas
   entre interprete, verificador y decisor.

4. **A3 midio punta a punta.** Texto+estado -> accion. Mezcla
   interprete y decisor. No es una medicion del interprete puro.

5. **P-struct no es competidor equivalente.** Recibe spec
   estructurada mientras el LLM debe extraerla. Es techo de logica,
   no comparacion de entradas.

6. **Conexion con Godot: progresiva.** No reemplazar la conduccion
   actual. Probar primero la interfaz, despues el lazo.

7. **Evitar dos proyectos paralelos.** Artefactos compartidos entre
   offline y online. Un solo backlog.

8. **Hipotesis falsable, no "se complementan".** "Se complementan"
   no dice que resultado la refutaria.

## 2. Donde se complementan

Los aportes son distintos y no se contradicen:

**Claude aporta:**
- Brazos R0-R3 (R0 actual, R1 spec dorada + Python, R2 LLM,
  R3 P-text).
- Familias E-base y E-contrato (con contrato fijo vs variable).
- N=100 por brazo, IC +-8 puntos.
- Subproducto: la evidencia dinamica reservada de F0 sale de los
  episodios online.
- H-circuito como formulacion unica.

**Luna aporta:**
- Cuarta funcion: supervisor de seguridad (barrera operativa
  independiente).
- Descomposicion de la hipotesis en H1c-a (interpretativa) y H1c-b
  (operacional).
- Tabla de metricas por rol, mas fina.
- Intent tipado como contrato puente.
- Integracion progresiva en 3 pasos (interfaz -> Godot -> lazo).

**Los dos se combinan:** los brazos de Claude se ejecutan sobre la
integracion progresiva de Luna. Las familias E-base/E-contrato son
consistentes con la descomposicion H1c-a/H1c-b.

## 3. Donde discrepan

**Rol count:**
- Claude: 3 funciones (interprete, verificador, decisor) + ejecutor
  fuera.
- Luna: 4 funciones (+ supervisor de seguridad).

**Hipotesis:**
- Claude: H-circuito unica.
- Luna: H1c con dos sub-hipotesis separables (a: interpretativa,
  b: operacional).

**Puente:**
- Claude: MisionConfig con hash.
- Luna: Intent tipado.

**Ninguna de las dos diferencias es contradictoria.** Son niveles de
detalle distintos:
- Supervisor de seguridad = barrera que Claude no menciona pero que
  no niega.
- H1c-a/H1c-b = refinamiento de H-circuito. No es otra hipotesis, es
  la misma desdoblada.
- MisionConfig e Intent son complementarios: Intent es el contrato
  que el interprete produce, MisionConfig es la config que el
  decisor consume. Uno puede contener al otro.


## 4. Propuesta consolidada

### 4.1 Circuito de roles

1. **Interprete (LLM).** Texto -> Intent tipado (objetivo,
   restricciones, parametros, unidades, campos desconocidos). No
   elige maniobras. No ejecuta.
2. **Verificador (Python).** Valida Intent: esquema, tipos, rangos,
   coherencia con MisionConfig. Acepta, rechaza o pide aclaracion.
3. **Supervisor de seguridad (Python).** Valida la accion propuesta
   frente a restricciones operativas y estado dinamico. Puede
   vetarla independientemente.
4. **Decisor (Python).** Recibe Intent verificado, telemetria y
   estado de mision. Aplica politica determinista. Elige accion.

El controlador de bajo nivel y la fisica de Godot completan el
sistema. No son funciones del circuito.

### 4.2 Medición por rol

| Rol | Que se mide | Baseline / referencia |
| --- | --- | --- |
| Interprete | Exactitud semantica del Intent. Errores de unidades. Campos invalidos. Deteccion de ambiguedad. | Spec dorada. |
| Verificador | Falsos aceptados. Falsos rechazos. Deteccion de inconsistencias. | Mutaciones controladas. |
| Supervisor | Violaciones no detectadas. Veto indebido. Latencia de veto. | Politica de seguridad. |
| Decisor | Exito de mision. Calidad de accion. Repetibilidad. | Entrenador / P-struct. |

**Descomposicion del error:** correr el circuito con oraculo en cada
rol, uno por vez. Asi se aisla que rol contribuye a que error.

### 4.3 Integracion con el sistema real

**Paso 1 - Prueba de interfaz (offline).**
El interprete recibe instrucciones reales o grabadas. Produce Intent.
El verificador valida. Comparar contra etiquetas de referencia.

**Paso 2 - Reproduccion en Godot/DHS.**
Comparar `Qwen + reglas` (actual) contra una variante donde solo
cambia el interprete. Mantener identicos el decisor, la config y el
controlador. Mide el aporte aislado del interprete.

**Paso 3 - Lazo cerrado.**
Variante integrada en simulacion. Escenarios, estados iniciales y
condiciones comparables. Registrar veto, trayectoria, llegada a
Puerto Esperanza, fallos y recuperacion.

### 4.4 Familias de episodios

- **E-base:** contrato actual (T fijo, v_max fijo). Mide **no
  inferioridad**.
- **E-contrato:** contrato variado por episodio (T y v_max
  distintos). Mide **cumplimiento**.
- Qwen + reglas con T fijo termina a 15m aunque el contrato pida 5m.
  Ahi el LLM podria aportar.

### 4.5 Brazos (comparacion pareada, mismas semillas)

- **R0:** sistema actual.
- **R1:** spec dorada -> decisor Python + PID. Techo del circuito.
  No requiere entrenar nada.
- **R2:** texto -> interprete LLM -> verificador -> decisor.
- **R3** (opcional): texto -> P-text, para ver el fallo de cobertura
  en lazo cerrado.

Con N=100 por brazo, el IC de una tasa del 80% es +-8 puntos.

### 4.6 Hipotesis consolidada

**H1c:** en instrucciones nauticas semanticamente equivalentes pero
formuladas de distintas maneras, un interprete LLM mejora la
conversion a intenciones estructuradas validas respecto del
interprete actual, manteniendo invariantes la politica decisora y el
controlador. Esa mejora se traduce en mayor exito de mision o menor
tasa de fallos, sin degradar la seguridad mas alla de limites
predefinidos.

**H1c-a (interpretativa):** el LLM mejora la exactitud semantica
fuera de distribucion.

**H1c-b (operacional):** esa mejora produce beneficio medible en
Godot/DHS respecto de Qwen + reglas, sin aumentar violaciones ni
introducir latencia inaceptable.

**Estado actual:**
- A3 aporta evidencia para **H1c-a**.
- H1c-b **no** esta establecida todavia.

### 4.7 Falsabilidad

**H1c-a se refuta si:** el LLM no supera a P-text en exactitud
semantica del Intent en instrucciones retenidas.

**H1c-b se refuta si:** el LLM no mejora el exito de mision o
aumenta violaciones de seguridad o introduce latencia inaceptable.

**"Se complementan" NO es falsable.** Por eso no se usa como
hipotesis.

## 5. Preguntas para el Director

1. **Aprobar el circuito de 4 funciones** (interprete, verificador,
   supervisor, decisor) o quedarse con 3 (interprete, verificador,
   decisor)?

2. **Aprobar la descomposicion H1c-a / H1c-b** o mantener una
   hipotesis unica?

3. **El cambio de target del SFT:** para medir el interprete puro
   hace falta entrenar texto -> Intent (no texto -> accion como A3).
   Esto implica un **A4**, no una continuacion de A3. ¿Se avanza con
   eso?

4. **Prioridad entre pistas:**
   - Pista 1 (offline, roles): A4 texto -> Intent.
   - Pista 2 (online, conduccion): integrar en Godot/DHS.

   ¿Cual va primero?

5. **El supervisor de seguridad** es una funcion nueva. ¿Se
   implementa desde el inicio, o se difiere a una fase posterior?

## 6. Lo que NO se decide aca

- No se implementa nada.
- No se entrena nada.
- No se cambia el sistema actual.
- Todo esto espera aprobacion del Director.
