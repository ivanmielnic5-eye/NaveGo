# MEMO CONSOLIDADO — Estado del proyecto y plan de accion

**Fecha:** 2026-10-11
**Autor:** Directora de Investigacion
**Estado:** CONSOLIDADO. Reemplaza a los memos 86-88 como documento de referencia.
**Complementa:** memos 83, 84, 85, 86 (parcialmente obsoleto), 87, 88.
**Consultas externas:** Luna GPT, Claude, Notebook LLM.

---

## 0. Proposito

Este memo consolida:
- El uso previsto de Polaris.
- Los 3 hallazgos activos.
- La sintesis de las 3 consultas externas.
- El plan de accion acordado.
- Las reglas duras del proyecto.
- El proximo paso concreto.

Es el documento de referencia del proyecto a partir de ahora.

> **PREMISA FUNDAMENTAL DEL PROYECTO (2026-10-11)**
>
> La calidad se busca activamente en todas las áreas del sistema.
> No se aceptan autolimitaciones por inercia.
> Al tocar cualquier módulo, se revisan los supuestos heredados antes
> de aceptarlos.

---


---

## 1. USO PREVISTO DE POLARIS (Opcion B)

Polaris es un simulador sintetico diseñado para evaluar agentes de decision
en tareas de navegacion. Las decisiones optimas se definen DENTRO de Polaris,
usando su fisica y su funcion de utilidad. NO se afirma que las decisiones
correctas en Polaris sean correctas en un velero real.

El objetivo proximo es un benchmark sintetico reproducible, con reglas
explicitas, fisica verificada y analisis de sensibilidad documentado.

El objetivo final —un copiloto para veleros reales— requerira validacion
fisica contra un velero documentado y transferencia sim-to-real como
fases posteriores.

Consecuencias operativas:
- El benchmark se limita a Polaris.
- La fisica se audita en la medida necesaria para analisis de sensibilidad.
- Las afirmaciones sobre navegacion real se reservan para cuando exista
  validacion fisica.

---

## 2. LOS 3 HALLAZGOS ACTIVOS

### HALLAZGO 1 — Bug del Entrenador v1 (comparacion injusta)

En _simular_receta, cada receta corre hasta que TERMINA o hasta timeout.
Pero las recetas tienen duraciones efectivas distintas:

- corregir_rumbo: termina cuando alineado (~15s).
- ir_a_punto: corre el horizonte completo.
- frenar: termina cuando lento (~30s).

Medir "distancia final" favorece a la receta mas larga.

Diagnostico inicial (memo 86): "67% de error del Entrenador".
Era ARTEFACTO del bug, no error del Entrenador.
Reconocimiento en memo 87. Correccion propuesta en memo 88.

### HALLAZGO 2 — Parametros del simulador no justificados

Solo 2 de ~20 parametros tienen referencia documental:

- VIENTO_FUERZA_POR_NUDO: "calibrado para viento realista" (memo 58).
- "Fisica avanzada (ver EXPEDIENTE/58)".

Los demas (MASA, AVANCE_FORCE, TIMON_TORQUE, FORWARD_DRAG, etc.):
- Sin documentacion de origen.
- Sin tests de validacion.
- Sin calibracion contra velero real.

Implicancia: el ground truth refleja nuestros parametros, no la realidad.
Riesgo: si cambiamos AVANCE_FORCE, las etiquetas cambian (sensibilidad).

### HALLAZGO 3 — Recetas con parametros de comando inventados

Las recetas v1 y v2 usan parametros de comando sin justificacion:
- timon_ms=500 vs 800.
- avance_ms=500 vs 1000.
- Ciclos de 0.5s vs 1.0s.

Test empirico: desde el mismo estado, corregir_rumbo_v2 avanzo MAS que
ir_a_punto_v2 (absurdo). Confirma que los parametros no tienen criterio.

Investigacion externa (Notebook LLM): en robotica marina real NO se usan
secuencias temporizadas fijas. Se usa CONTROL EN CASCADA:

- Inner loop: PID que mueve el timon a 10 Hz.
- Outer loop: MPC/Line-of-Sight que decide el rumbo.
- El LLM deberia estar en el outer loop, no emitiendo comandos al timon.

---

## 3. SINTESIS DE LAS 3 CONSULTAS

### Luna GPT

- Proponer VVUQ (NASA-STD-7009B, ASME) como marco.
- Tres niveles: fisica real / simulador / Entrenador. No saltar del 3 al 1.
- Benchmark sintetico PUEDE ser valido con limitaciones explicitas.
- Copiloto real NO, sin validacion fisica.
- Separar 3 capas: accion alto nivel / controlador bajo nivel / criterio exito.
- Orden de 6 pasos: congelar, definir uso, arreglar Entrenador, validar
  parametros, congelar v2, reetiquetar y reentrenar.
- 3 reglas duras (ninguna etiqueta es verdad absoluta, no cambiar fisica
  para mejorar accuracy, no extrapolar del sintetico al real).

### Claude

- Coincide en lo central. Discrepa en:
  - "Validar parametros" no se puede sin velero real. Hacer analisis de
    sensibilidad: perturbar +-30% y medir cuantas etiquetas cambian.
  - NASA-STD y ASME son excesivos. Usar como vocabulario, no como proceso.
  - El 65% del SFT mide IMITACION del Entrenador, no capacidad de navegar.
    Hasta que el Entrenador este arreglado, ese numero no significa nada.
- Agrega:
  - NO migrar a Gazebo/MuJoCo (no tienen hidrodinamica de velero).
  - Falta baseline (clase mayoritaria, heuristica simple).
  - El confirmatorio puede estar contaminado. Generar uno nuevo.
  - Interfaz del LLM reformulada: rumbo(theta), ir_a(punto), frenar.
    Sin la etiqueta "corregir_rumbo a 90", que mezcla intencion con ejecucion.
  - Evaluacion pasa a regret en lazo cerrado.
  - Empates: etiqueta blanda o descartar.
- 5 reglas duras: procedencia de parametros, tests de sanidad, comparacion
  justa automatizada, orden de sospecha, versionado de etiquetas.
- Proximo paso: corregir Entrenador + experimento de sensibilidad.

### Notebook LLM

- Validacion de simuladores: DAS (velero real instrumentado), validacion
  cruzada, metricas L2 de divergencia.
- Metodologia top-down: Model-Based Verification & Validation.
- Recetas vs controladores: PID/MPC, no secuencias temporizadas.
  Papers: "Intelligent Sailing Model for Open Sea Navigation" (arXiv 2025),
  "Waypoint Navigation Using Wind Sensing" (Aston University).
- Domain Randomization: variar masa/viento/rozamiento durante entrenamiento.
- 5 practicas de la industria: PID, DR, validacion con ensayos reales,
  cascada outer/inner, metrica L2.

---

## 4. CONSENSOS Y DIVERGENCIAS

### Consensos (los 3 coinciden)
1. El bug del Entrenador es real. Corregirlo.
2. Los parametros del simulador no estan justificados.
3. Las recetas estan mal por arquitectura. Cascada + PID es el camino.
4. Congelar evidencia historica antes de tocar nada. HECHO (tag git).
5. No extrapolar del benchmark sintetico a navegacion real.
6. El proyecto tiene valor como investigacion, con limites declarados.

### Divergencias (donde Claude corrige a Luna)
1. "Validar parametros" no se puede sin velero real. Claude propone
   analisis de sensibilidad en vez de validacion.
2. NASA-STD-7009B y ASME son excesivos para esta etapa.
3. El 65% del SFT no mide capacidad, mide imitacion.

### Adoptado
- Enfoque de Claude: analisis de sensibilidad primero, validacion real
  despues. NASA-STD como vocabulario, no como proceso.
- Reconocer que el 65% no significa nada hasta arreglar el Entrenador.

---

## 5. PLAN DE ACCION (6 PASOS ADOPTADOS)

1. Congelar evidencia historica. HECHO (tag evidencia-pre-auditoria-fisica).
2. Definir uso previsto. HECHO (seccion 1 de este memo).
3. Arreglar el Entrenador con continuacion comun + tests de sanidad.
   Ademas: experimento de sensibilidad sobre los 300 contextos de desarrollo.
4. Pasar a arquitectura en cascada (PID inner, LLM outer).
5. Documentar procedencia de parametros + analisis de sensibilidad.
6. Congelar v2, reetiquetar con confirmatorio NUEVO (semillas nuevas)
   y reentrenar.

Criterio de "terminado" del paso 3:
- Fraccion de etiquetas estables (numero concreto).
- Lista de tests de sanidad pasando.

---

## 6. REGLAS DURAS CONSOLIDADAS

1. La etiqueta es funcion de (version del simulador, utilidad, conjunto
   de acciones, horizonte). Se reporta como "acuerdo con Entrenador vX",
   nunca como "correccion".

2. No cambiar fisica ni utilidad despues de ver resultados del LLM para
   mejorar accuracy. Los cambios por defectos documentados se permiten
   con subida de version y reporte antes/despues.

3. No extrapolar del benchmark sintetico a navegacion real sin validacion
   fisica suficiente. Todo informe declara a que nivel aplica.

4. Procedencia de parametros: cada parametro lleva etiqueta
   (documentado / estimado / inventado) + rango. Los inventados entran
   obligatoriamente en analisis de sensibilidad.

5. Tests de sanidad antes de etiquetar: monotonia, simetria, ordenamientos
   obvios. El "test del absurdo" pasa a ser regresion permanente.

6. Comparacion justa automatizada: verificar que el puntaje de ninguna
   alternativa depende de su propia duracion.

7. Orden de sospecha ante resultado anomalo: auditar primero la medicion,
   despues el pipeline, recien al final el modelo.

8. Versionado de etiquetas: cada etiqueta registra version del simulador,
   del Entrenador, funcion de utilidad y horizonte.

9. No usar el confirmatorio para decidir diseño. Si se uso para
   diagnostico, generar uno nuevo con semillas nuevas.

10. **Revision de supuestos heredados.** Al modificar cualquier modulo del
    sistema, revisar y declarar el estatus de cada supuesto heredado:
    - justificado (se documenta la razon y sigue igual)
    - inercia (se cambia con criterio)
    - sin justificar (se investiga antes de tocarlo)

    Los marcados como inercia se corrigen. Los marcados como sin justificar
    se investigan. Los justificados se preservan.


---

## 7. PROXIMO PASO CONCRETO — EXPERIMENTO DE SENSIBILIDAD

Diseñar (sin codigo todavia) el experimento que responde:

> ¿Cuanto cambian las etiquetas del banco CC002 al perturbar los
> parametros no documentados del simulador en +-30%?

Parametros a perturbar:
- AVANCE_FORCE (6000 N)
- TIMON_TORQUE (886 N.m)
- FORWARD_DRAG (0.0134)
- LATERAL_DRAG (0.05)
- WATER_ANGULAR_DRAG (0.005)
- MASA (3500 kg)

Metodologia:
1. Baseline: etiquetar los 300 contextos de desarrollo con parametros actuales.
2. Para cada perturbacion: reetiquetar los 300 contextos.
3. Comparar: fraccion de etiquetas que cambian.
4. Reportar: por parametro, cuantas etiquetas cambian.

Interpretacion:
- Si < 5% cambian: el banco tiene señal defendible.
- Si 5-20% cambian: hay señal pero con caveat.
- Si > 20% cambian: el banco refleja solo nuestros parametros, no la
  situacion subyacente.

Ese numero es el que orienta todo lo demas.

---

## 8. LO QUE NO SE HACE TODAVIA

- NO se re-entrena el SFT.
- NO se toca el confirmatorio.
- NO se migra a otro simulador.
- NO se implementa el PID todavia.
- NO se escribe mas memos intermedios hasta tener resultados del
  experimento de sensibilidad.

---

## 9. FIRMA

**Estado:** CONSOLIDADO.
**Proximo paso:** diseñar el experimento de sensibilidad (sin codigo).
**Regla:** calidad primero, performance despues.


---

## 10. DISENO DEL EXPERIMENTO DE SENSIBILIDAD (detalle)

### 10.1 Objetivo

Medir cuanto cambian las etiquetas del banco CC002 al perturbar los
parametros no documentados del simulador. El resultado es un numero
concreto que orienta el resto del proyecto.

Pregunta operativa:
> Si mis parametros estan mal por +-30%, ¿mi banco de etiquetas sigue
> siendo valido?

### 10.2 Parametros a perturbar

Los 6 parametros principales no documentados. Cada uno se perturba
individualmente (no todos juntos).

| Parametro | Valor actual | Rango de perturbacion |
|-----------|-------------|----------------------|
| AVANCE_FORCE | 6000 N | [4200, 7800] |
| TIMON_TORQUE | 886 N.m | [620, 1150] |
| FORWARD_DRAG | 0.0134 | [0.0094, 0.0174] |
| LATERAL_DRAG | 0.05 | [0.035, 0.065] |
| WATER_ANGULAR_DRAG | 0.005 | [0.0035, 0.0065] |
| MASA | 3500 kg | [2450, 4550] |

Rango: +-30% del valor original (excepto masa que es +-30% tambien).

### 10.3 Metodologia

Para cada parametro:

1. BASELINE: etiquetar los 300 contextos de desarrollo con parametros actuales.
   El resultado es el conjunto de etiquetas de referencia.
2. PERTURBACION ALTA: reetiquetar los 300 contextos con el parametro a +30%.
3. PERTURBACION BAJA: reetiquetar los 300 contextos con el parametro a -30%.
4. COMPARAR: cuantas etiquetas cambiaron vs baseline.

Metrica principal:
- Fraccion de contextos cuya accion_optima cambia.

Metrica secundaria:
- Distribucion de cambios por clase original (que clases son mas fragiles).
- Distribucion de cambios por familia (terminal, cerca, medio, lejos).

### 10.4 Parametros de control del experimento

- Semilla aleatoria del simulador: FIJA (no se varia).
- Viento: el del contexto (no se modifica).
- Horizonte del Entrenador: el del v2 (post correccion de continuacion comun).
- Razon (decision de Claude): medir sensibilidad sobre etiquetas que
  sabemos que estan mal no informa. Primero arreglar el Entrenador,
  despues medir sensibilidad sobre etiquetas correctas.

### 10.4.bis ORDEN DE EJECUCION CORREGIDO

Segun Claude:

1. Arreglar el Entrenador (continuacion comun + test del absurdo como regresion).
2. Verificar que el test del absurdo ya no pasa.
3. Correr el experimento de sensibilidad sobre el Entrenador arreglado.
4. Despues de sensibilidad: decidir si migrar a cascada o no.

El fix de continuacion comun debe escribirse de forma REUTILIZABLE,
porque sirve igual para la futura arquitectura en cascada (comparar
decisiones del outer loop con el mismo horizonte).

### 10.5 Criterio de interpretacion

Para cada parametro perturbado:

- Si < 5% de etiquetas cambian: parametro poco sensible.
  El banco tiene señal defendible contra perturbaciones de ese parametro.

- Si 5-20% cambian: parametro moderadamente sensible.
  Hay señal pero con caveat. Se reporta el rango.

- Si > 20% cambian: parametro muy sensible.
  El banco refleja solo nuestros valores especificos, no la situacion
  subyacente. Requiere analisis adicional.

Criterio global:
- Si TODOS los parametros son < 5%: el banco es robusto. Podemos
  avanzar con confianza.
- Si alguno es > 20%: hay que decidir si:
  a) Investigar el parametro especificamente.
  b) Rediseñar el banco con Domain Randomization (entrenar contra
     distribucion de parametros en vez de un valor puntual).

### 10.6 Formato de reporte

Tabla final del experimento:

| Parametro | Perturbacion | Etiquetas cambiadas | % | Interpretacion |
|-----------|-------------|---------------------|---|----------------|
| AVANCE_FORCE | -30% | ? | ? | ? |
| AVANCE_FORCE | +30% | ? | ? | ? |
| TIMON_TORQUE | -30% | ? | ? | ? |
| ... | ... | ... | ... | ... |

Mas:
- Grafico de barras: % de cambio por parametro.
- Detalle: 5 ejemplos de contextos que cambian, con parametro y accion.
- Analisis: que clases/familias son mas fragiles.

### 10.7 Tiempo estimado

- Implementar el experimento: 1 hora.
- Correr el experimento: ~10 min por parametro × 2 perturbaciones × 6 parametros = 2 horas.
- Analisis: 30 min.

Total: ~4 horas.

### 10.8 Lo que NO se hace

- NO se reetiqueta el confirmatorio.
- NO se cambia el Entrenador todavia.
- NO se varia el viento.
- NO se perturban varios parametros juntos (primero individual, después combinado si es necesario).

### 10.9 Resultado esperado

El experimento va a dar UN NUMERO por parametro.
Ese numero es lo que define si el banco actual sirve o no.


---

## ANEXO A — INVENTARIO DE SUPUESTOS DEL SIMULADOR

**Fecha:** 2026-10-11
**Origen:** aplicacion de Regla 10 (revision de supuestos heredados).

Clasificacion:
- **Justificado:** tiene razon documentada y verificable.
- **Inercia:** sin razon, pero se puede cambiar facilmente.
- **Sin justificar:** no se sabe por que esta asi. Requiere investigacion.

### Tabla de supuestos

| # | Supuesto | Ubicacion | Estatus | Accion propuesta |
|---|----------|-----------|---------|------------------|
| 1 | "Replica la fisica de Godot (Jolt)" | Cabecera | Sin justificar | Investigar si se verifico contra Godot |
| 2 | Constantes fisicas "extraidas del codigo Godot" | Constantes | Sin justificar (18/20) | Investigar origen de cada una |
| 3 | `timon: int` | aplicar_comando | Inercia | Cambiar a `float` |
| 4 | `avance: int` | aplicar_comando | Inercia | Cambiar a `float` |
| 5 | `timon_activo: int = 0` | Atributo Barco | Inercia | Cambiar a `float` |
| 6 | `avance_activo: int = 0` | Atributo Barco | Inercia | Cambiar a `float` |
| 7 | Runner fuerza `int(...)` al leer | Runner | Inercia | Cambiar a `float(...)` |
| 8 | Comando como ventana temporal | aplicar_comando | Sin justificar | Investigar diseno |
| 9 | MASA = 3500.0 | Constantes | Sin justificar | Investigar origen |
| 10 | AVANCE_FORCE = 6000.0 | Constantes | Sin justificar | Investigar origen |
| 11 | TIMON_TORQUE = 886.0 | Constantes | Sin justificar | Investigar origen |
| 12 | Resto de constantes (~15) | Constantes | Sin justificar | Investigar origen |
| 13 | Aplicacion de fuerzas por ventana | paso() | Sin justificar | Investigar diseno |
| 14 | prop_wash con `avance != 0` | paso() | Sin justificar | ¿Por que no proporcional? |

### Orden de revision propuesto

1. **Grupo 1 (tipos):** supuestos 3-7. Bloquean el PID continuo.
2. **Grupo 2 (constantes fisicas):** supuestos 9-12. Bloquean la validez
   del ground truth.
3. **Grupo 3 (diseno):** supuestos 1, 2, 8, 13, 14. Requieren analisis
   mas profundo.

### Regla aplicable

Cada cambio se documenta con: supuesto afectado, estatus previo, cambio
aplicado, justificacion. Se hace backup `.pre-<etapa>` antes de tocar.



---

## 11. RESULTADO DEL ENTRENADOR v2

### 11.1 El fix

El Entrenador v2 corrige el bug del v1 (comparacion injusta).
Cada accion corre TODO el horizonte. Todas comparables.

Se implementaron:
- acciones.py: interfaz de alto nivel (rumbo, ir_a, frenar, terminar).
- controlador_pid.py: PID de rumbo continuo (Cand 4).
- entrenador_v2.py: Entrenador con continuacion comun.

### 11.2 Comparacion v1 vs v2 (300 contextos de desarrollo)

Con horizontes DEFAULT [5, 15, 30, 45]:
- Cambios: 183/300 (61.0%).
- Distribucion v2: ir_a=137, terminar=89, frenar=60, rumbo=14.

Con horizontes LARGOS [5, 15, 30, 60, 120, 240]:
- Cambios vs banco (v1): 225/300 (75.0%).
- Distribucion v2: ir_a=203, terminar=93, frenar=4, rumbo=0.

### 11.3 Lectura del resultado

TRES DE CADA CUATRO etiquetas del banco CC002 estan mal.

El bug del v1 + el horizonte corto producen etiquetas que no
representan el comportamiento real del barco a largo plazo.

### 11.4 Analisis de las 4 acciones

**ir_a**: navega a la meta con recalculo continuo del rumbo.
Es la accion dominante. Gana 203/300.

**terminar**: accion logica terminal. Sube a 93 (desde 75).
14 contextos mas son reconocidos como terminales con horizonte largo.

**frenar**: cae a 4 (desde 75). Con horizonte largo, casi nunca
gana porque ir_a siempre progresa mas. Esto no significa que frenar
sea inutil — la funcion de utilidad actual no premia "llegar suave"
ni "no sobrepasar la meta". Pendiente: rediseñar la utilidad para
reconocer cuando frenar ayuda.

**rumbo**: cae a 0 con horizontes largos. NO ES INERCIA. El test
con thetas arbitrarios (0, 45, 90, 135, 180, 225, 270, 315) muestra
que cada angulo da un resultado distinto y coherente. El problema
es que el Entrenador v2 fuerza theta = rumbo_a_meta, haciendo que
rumbo e ir_a apunten al mismo lugar. En este contexto (una meta
unica, sin obstaculos), ir_a domina.

Correccion de diseño pendiente: rumbo sin stop condition a horizontes
largos produce progresos NEGATIVOS (el barco pasa de largo la meta
y sigue). Documentar y decidir si:
  a) rumbo deberia tener un stop condition (parar al llegar).
  b) rumbo es accion para fases futuras (obstaculos, direccion
     especifica por X tiempo).

Decision del Director: mantener rumbo como accion disponible, como
inversion a futuro. Documentar el estado actual.

### 11.5 Conclusiones

- El Entrenador v2 es la base correcta. Las comparaciones son justas.
- El banco CC002 actual no sirve para entrenar. Hay que reetiquetar.
- frenar necesita rediseño de la funcion de utilidad.
- rumbo queda como accion futura, sin utilidad inmediata en este
  contexto (meta unica sin obstaculos).
- El SFT (memo 83) fue entrenado con etiquetas 75% incorrectas. Su
  65% no mide capacidad, mide imitacion del v1 buggeado.

### 11.6 Proximos pasos (orden)

1. Documentar este hallazgo en Anexo A (acciones).
2. Diseñar la funcion de utilidad del Entrenador v2 (para decidir
   si frenar puede ganar en algun contexto).
3. Correr el experimento de sensibilidad (Grupo 2 del Anexo A).
4. Reetiquetar CC002 con el Entrenador v2 final.
5. Generar confirmatorio NUEVO con semillas nuevas.
6. Reentrenar el SFT.



---

## 12. FUNCION DE UTILIDAD DEL ENTRENADOR v2

### 12.1 Definicion (por el Director)

Orden jerarquico estricto:

1. **Estar a salvo. No naufragar.** Gate duro. Si la accion viola
   seguridad, se descarta sin importar nada mas.
2. **Llegar bien, enteros.** Mission complete. El objetivo primario.
3. **Precision + eficiencia.** Llegar cerca y sin sobrepasarse.

El resto (alineacion, suavidad) son criterios de desempate secundarios.

### 12.2 Traduccion a la funcion de ranking

Estructura correcta:

    Si boundary_violation: descartar accion (score = -infinito)
    Si no:
        rank = (not mission_complete, -progreso_medio, -alineacion_deg)

NOTA: el orden actual en entrenador_v2.py es
    (not mission_complete, boundary_violation, -progreso_medio, -alineacion)
que tiene los dos primeros INVERTIDOS respecto a la decision del Director.
Hay que corregir el orden.

### 12.3 Justificacion de cada componente

- **boundary_violation (seguridad):** es una penalizacion jerarquica,
  NO un gate absoluto. Aclaracion del Director (2026-10-11):

  > "Tener cuidado que estar a salvo o no naufragar no congele la accion
  >  siempre. Salvo si tiene un peligro inminente, que sea peor que estar
  >  quieto."

  Regla corregida:
  - Si el peligro es INMINENTE (distancia al limite < X metros Y velocidad
    hacia afuera): la accion que aleja del limite gana. Gate duro.
  - Si NO hay peligro inminente: boundary_violation es criterio de
    desempate. La accion que menos viola gana entre las que empatan.
  - Si TODAS las acciones violan: la que MENOS viola gana. No se congela.
  - Si NINGUNA viola: ranking normal por (mission_complete, progreso, alineacion).

  Justificacion: caminar con cuidado cerca de un rio es mas seguro que
  quedarse parado en medio de una crecida. El sistema debe poder ACCIONAR
  cuando es mejor accionar que quedarse quieto.

- **mission_complete (llegar):** sin esto, no hay mision. Es el objetivo
  primario y define el exito.

- **progreso_medio (precision + eficiencia):** la integracion trapezoidal
  de los horizontes captura ambas cosas a la vez:
    - Si el barco llega mas rapido -> promedio mas alto.
    - Si el barco se sobrepasa y se aleja -> promedio mas bajo.
    - Si el barco se queda quieto -> promedio bajo.

- **alineacion_deg (desempate):** entre dos acciones con progreso similar,
  preferir la que apunta mas cerca de la meta.

### 12.4 Sobre "llegar sin sobrepasarse"

El progreso medio ya penaliza implicitamente el sobrepaso: si el barco
pasa la meta y se aleja, los horizontes tardios bajan el promedio.
Pero no es explicito. Pendiente de evaluar si hace falta una dimension
adicional de "precision terminal" (distancia al horizonte maximo).

### 12.5 Sobre frenar

Con este orden, frenar solo puede ganar si:
- El barco esta muy cerca de la meta, con velocidad alta, y
- Su progreso medio (por seguir avanzando y sobrepasarse) es menor que
  el de frenar (que se queda justo en la meta).

Eso PUEDE pasar en contextos terminales con sog alta. Hay que medirlo
despues de corregir el orden.

### 12.6 Decision

Aplicar el orden correcto en entrenador_v2.py:
1. Primero filtrar por boundary_violation.
2. Despues rankear por (mission_complete, progreso_medio, alineacion).



---

## 13. FASE 7 — VISION AVANZADA (documentacion de ideas)

### 13.1 Origen de las ideas

Estas ideas no son improvisadas. Vienen del proyecto anterior del Director
llamado "Ojo de Gaia", que era un sistema para leer la complejidad del
iris humano. De ahi surge el conocimiento de:

- Teselaciones de Penrose.
- Wavelets aplicadas a senales complejas.
- Cartografia y proyecciones (McDonnell, Buckminster Fuller).
- El problema de simplificar estructuras circulares en planos rectos.

Ese proyecto quedo cerrado pero las herramientas matematicas quedaron.
Se reutilizan en Fase 7 cuando el simulador tenga olas y sensores.

### 13.2 Teselaciones de Penrose

**Que son:** patrones que cubren el plano sin huecos ni superposiciones,
con solo dos formas (cometa y flecha), pero que NO son periodicos.
Es decir, el patron nunca se repite exactamente igual.

**Historia real:**
- Roger Penrose las describio en 1974.
- Fue nombrado caballero en 1994, mismo ano en que TU Dortmund inauguro
  un piso con teselados de Penrose. De ahi la confusion de fechas.
- Penrose gano el Nobel de Fisica en 2020, pero por agujeros negros,
  no por las teselaciones.

**Conexion con cuasicristales:**
- Dan Shechtman gano el Nobel de Quimica en 2011 por descubrir
  cuasicristales.
- Paul Steinhardt (Princeton) propuso que los teselados de Penrose
  podian existir como estructura atomica real.
- Se demostro que si. Es la version fisica de los teselados.

**Aplicacion potencial en Fase 7:**
- Codificacion eficiente de informacion visual.
- Deteccion de patrones en el "ojo" del barco.
- Representacion de estados del mar.

### 13.3 Wavelets (transformada de ondiculas)

**Que son:** una herramienta matematica para analizar senales
NO estacionarias. A diferencia de Fourier (que da el promedio de
frecuencias en toda la senal), las wavelets dan la evolucion en el
tiempo Y en la frecuencia al mismo tiempo.

**Ejemplo:**
- Fourier: "en esta hora hubo olas de 10s y 5s".
- Wavelet: "minuto 3 ola de 10s, minuto 5 cambio a 5s, minuto 7
  volvio a 10s".

**Wavelet de Morlet:** la mas usada para analisis de olas marinas.
Su forma se parece a una ola de mar con pequenas oscilaciones en los
bordes.

**Aplicaciones reales en industria naval:**
- Estimar direccion y periodo de olas desde radar marino.
- Filtrar movimiento del barco para posicionamiento dinamico.
- Predecir movimiento del barco en olas irregulares.

**Aplicacion en Fase 7:**
- Leer la complejidad de las olas.
- Detectar patrones (convergencias, direcciones, periodos).
- Alimentar al agente con una representacion matematica de la ola.

### 13.4 Cartografia y proyecciones

**Porter W. McDonnell:** autor del libro "Introduction to Map
Projections". Referencia en la materia. Cubre desde los principios
matematicos hasta tipos especificos (equidistantes, area equivalente,
etc.).

**Buckminster Fuller:** creo la proyeccion Dymaxion en 1943.
Convierte el globo en un icosaedro desplegable. Sin distorsiones
importantes. Muestra la Tierra como continente continuo.

**Ojo de Gaia (mision ESA):** la camara de mil millones de pixeles
de la mision Gaia de la Agencia Espacial Europea. Mapeo la Via Lactea.
Uso proyecciones como la equirectangular para presentar el mapa del
cielo en un plano.

**Aplicacion en Fase 7:**
- Leer la circularidad del ojo (o del mar) en un plano recto.
- Simplificar estructuras complejas sin perder informacion critica.
- Mapear el entorno cuando el barco tenga sensores completos.

### 13.5 Estado actual

- **Documentado:** si.
- **Implementado:** no.
- **Pendiente:** llegar a Fase 7 en el roadmap.
- **Requiere:**
  1. Simulador con olas modeladas.
  2. Sensores que capten la ola (radar, boya, camara).
  3. Representacion matematica de la senal (wavelet, Fourier, etc.).
  4. Agente que aprenda a responder a esa representacion.

### 13.6 Nota

Estas ideas son para la ultima fase. No se saltean etapas. Pero
documentarlas ahora evita que se pierdan. Cuando lleguemos, vamos a
tener todas las piezas listas.



---

## 14. HALLAZGO — Regla de decision disfrazada de contrato

### 14.1 El problema

El prompt de CC003 (heredado de CC002) incluye esta linea:

> "terminar: declara mision cumplida. Valida SOLO si dist < 15m."

Eso NO es contrato de tarea. Es REGLA DE DECISION. Le dice
explicitamente al modelo cuando usar terminar. El modelo no necesita
discriminar: solo comparar "dist < 15".

El memo 73 (decision 4) ya decia: "se elimina la regla de decision del
prompt". Y Luna en su respuesta al memo 86 ya advertia sobre la
diferencia entre contrato de tarea y regla de decision.

Pero cuando armamos el prompt de CC003, copiamos el de CC002 sin
revisar. Error de aplicacion, no de conocimiento.

### 14.2 Evidencia

Baseline trivial: "if dist < 15: terminar; else: ir_a".
Resultado: 76/76 = 100% en el confirmatorio CC003.

El LLM tambien saco 100%. Pero el LLM no aporta nada que la regla
trivial no diera ya. Mide obediencia, no discriminacion.

### 14.3 La distincion

**Contrato de tarea** (va en el prompt):
- Que hace cada accion.
- Cual es el proposito de la mision.
- Cual es el formato de salida.

**Regla de decision** (NO va en el prompt):
- Que accion elegir ante que estado.
- Umbrales de decision (dist < 15m, desvio > 30, etc.).

### 14.4 Rediseno del prompt

Prompt limpio (v2):

- PROPOSITO: "Llevar el barco a la meta. La mision esta completa
  cuando el barco llega a la meta." (sin especificar el umbral)
- ACCIONES:
  - ir_a: navega hacia la meta corrigiendo rumbo automaticamente.
  - terminar: declara la mision como cumplida.
  (sin "Valida SOLO si dist < 15m")

El modelo debe inferir por si mismo que terminar no tiene sentido
si no llego. Porque "declara la mision cumplida" implica que la
mision esta cumplida.

### 14.5 Leccion de metodo

REGLA 15 (nueva): antes de cada entrenamiento, revisar el prompt
contra las decisiones del memo 73 y 89 (seccion 12). Verificar que
no incluya reglas de decision.

Esta regla se aplica siempre, sin importar el apuro.

### 14.6 Proximos pasos

1. Regenerar train_cc003.jsonl y eval_cc003_*.jsonl con el prompt limpio.
2. Reentrenar en Kaggle.
3. Evaluar en confirmatorio.
4. Si accuracy < 100% pero > 70%: discriminacion real.
5. Si accuracy = 100%: hay otra regla escondida. Buscar.



---

## 15. HALLAZGO — GAP EN DISTRIBUCION DE DISTANCIAS

### 15.1 El problema

El banco CC003 tenia un gap de 4.24m entre la distancia maxima de
"terminar" (14.40m) y la distancia minima de "ir_a" (18.64m). No habia
NINGUN caso entre 14.40 y 18.64.

Implicancia: el modelo no tenia que aprender el umbral exacto (15m).
Solo tenia que distinguir dos grupos separados. Cualquier umbral entre
14.4 y 18.6 daba 100%.

### 15.2 Como se detecto

Mirada manual del Director a la distribucion de distancias. No hubo
chequeo automatico que lo detectara. Eso es un bache: la lista de
10 chequeos del memo 75 no incluye "distribucion de distancias dentro
de cada clase".

### 15.3 El fix

Se agrego un pool E al generador de CC003: candidatos con dist entre
13 y 17m. Con esto, tanto terminar (abajo de 15) como ir_a (arriba de
15) tienen casos cerca del umbral.

Resultado:
- Gap entre terminar (14.94m) e ir_a (15.60m): 0.66m.
- Zona baja (terminar 13-15m): 56 casos.
- Zona alta (ir_a 15-17m): 13 casos.

### 15.4 Regla nueva

REGLA 16 (nueva): antes de entrenar, verificar la distribucion de
distancias dentro de cada clase. Detectar gaps. Asegurar cobertura
de la zona critica (casos de ambas clases cerca del umbral).

Esta regla esta implementada en pre_entrenamiento.py, CHK 4.

### 15.5 Leccion de metodo

Los chequeos tienen que estar en codigo, no en memos. Un memo que
dice "chequear X" no evita nada si nadie lo ejecuta. Un script que
chequea X y aborta si falla, si.

---

## 16. TAREAS PENDIENTES ESTRUCTURALES (auto-critica)

### 16.1 Contexto

Autocritica del Director (2026-10-12). En dos dias se repitio el mismo
patron de error:

- Dia 1: memo 73 decia "sacar reglas del prompt". Lo escribimos como
  Regla 15. Al dia siguiente, la regla aparecio de nuevo en CC003.
- Dia 2: memo 75 lista 10 chequeos. Faltaba el de distribucion de
  distancias. Descubrimos el gap a ojo.

En ambos casos, la regla existia en un memo pero no se ejecuto.
Dependia de la memoria del Director o de la IA. Eso es un bache
estructural.

### 16.2 El principio violado

El sistema declara (memo 00 y varios): "una IA propone, otra IA
chequea". Y "el sistema NO MIENTE".

Ayer violamos esto sin advertirlo:
- La IA propuso el prompt de CC003.
- La misma IA ejecuto el entrenamiento.
- La misma IA acepto el resultado (100%).
- No hubo verificacion externa entre esos pasos.

El Director lo detecto hoy. Por su memoria, no por el sistema.

### 16.3 Tarea pendiente 1 — Automatizar la verificacion cruzada

**Problema:** la verificacion entre IAs hoy es manual. Depende de que
el Director recuerde pedirla.

**Objetivo:** meter la verificacion en el pipeline, no en la voluntad.

**Aclaracion del Director (2026-10-12):**
El chequeo debe ser un AVISO, no un BLOQUEO.

- El sistema AVISA cuando una propuesta no paso por verificacion
  externa.
- El Director decide si consultar a otra IA o aceptar el riesgo.
- El aviso no impide ejecutar. Es informacion, no impedimento.
- Solo el Director puede saltear el aviso. Si saltea, queda registrado.

**Analogia:** el Gate tiene WARNING y BLOCKED. El aviso de verificacion
cruzada funciona como WARNING.

**Ideas a evaluar:**
- Un script que marque si un commit paso por verificacion externa.
- Un comando tipo logos-verificacion que muestre el estado.
- Un warning antes de ejecutar el paso siguiente, pidiendo
  confirmacion explicita del Director.
- Marca de "verificado por X" opcional en el commit.

**Prioridad:** ALTA.

### 16.4 Tarea pendiente 2 — Auditar la cadena de automatizacion

**Problema:** el sistema tiene muchos eslabones que se ejecutan
automaticamente o se esperan por costumbre. Nunca auditamos la
cadena completa buscando gaps.

**Ejemplos de eslabones a auditar:**
- logos-gate: ¿verifica todo lo que deberia?
- logos-brief / logos-arranque: ¿incluyen toda la info critica?
- Los memos: se escriben, se commitean. ¿Alguien verifica que se
  lean? ¿Que se apliquen?
- Los backups .pre-*: se hacen. ¿Se verifican? ¿Se pueden restaurar?
- Los commits: ¿hay chequeo de que no se mezclan cambios no
  relacionados?
- Los tests: ¿hay chequeo de que pasen antes de commitear?
- Las hipotesis registradas: ¿se cierran?

**Metodologia:**
- Listar eslabones.
- Por cada uno: que se ejecuta, que se espera, que se verifica, que
  NO se verifica.
- Priorizar gaps por impacto.
- Resolver uno por vez.

**Prioridad:** MEDIA-ALTA.

### 16.5 Lo que NO hacer

- No resolver las dos tareas de una sola vez.
- No convertirlo en proyecto paralelo.
- No agregar burocracia sin objetivo.
- No dejar las tareas sin fecha.

### 16.6 Proxima accion

1. Documentar esto en el memo 89 (esta seccion).
2. Continuar con el reentrenamiento de hoy (CC003 + prompt limpio).
3. Elegir momento para Tarea 1 (verificacion cruzada) — la mas urgente.
4. Despues de Tarea 1, encarar Tarea 2 (auditoria de cadena).


---

## 17. RESULTADO FINAL DEL SFT CC003 v4 (aplicacion del criterio)

### 17.1 El resultado

=== RESULTADO VALIDACION CC003 v4 ===
Accuracy: 76/76 = 100.0%
Uso de acciones: {'ir_a': 38, 'terminar': 38}
Por accion: {'ir_a': 38, 'terminar': 38} / {'ir_a': 38, 'terminar': 38}
Errores: 0

### 17.2 Lo que SI demuestra

- El pipeline entero funciona end-to-end.
- El modelo infiere el criterio a partir del proposito (sin que el
  prompt diga "Valida SOLO si dist < 15m").
- El banco con pool E funciono: gap bajo de 4.24m a 0.66m.
- El modelo acierta los 13 casos de la zona alta (15-17m) y los 56
  de la zona baja (13-15m).
- pre_entrenamiento.py no bloqueo nada porque estaba todo bien.

### 17.3 Lo que NO demuestra

Luna GPT (respuesta al informe del 2026-10-12) predijo este resultado
antes de verlo. Su diagnostico:

> "Si obtiene 100%: demostraria que el modelo produce la decision
>  esperada en esos 76 contextos. No demostraria por si solo que
>  posee una capacidad general de razonamiento."

> "Como unicamente existen ir_a y terminar, y una accion declara que
>  la mision esta cumplida, esa definicion practicamente determina la
>  politica esperada."

CC003 mide APLICACION DE UN CRITERIO CONOCIDO. No discriminacion general.

### 17.4 El gap de 0.66m sigue siendo problema

Luna:
> "El caso mas proximo de 'terminar' esta a 14,94 m y el mas proximo
>  de 'ir_a' a 15,60 m. El intervalo de 0,66 m entre ambos deja sin
>  ejemplos la zona mas cercana al limite real de 15 m. Un clasificador
>  podria separar esas muestras usando un umbral distinto de 15 m y
>  aun asi acertar en todos esos casos."

Es decir: el modelo podria estar usando un umbral en cualquier punto
entre 14.94 y 15.60. No prueba que aprendio el 15 exacto.

### 17.5 Nombre correcto del test

A partir de ahora: "Test de aplicacion del criterio de finalizacion".
No "Test de discriminacion".

### 17.6 Propuesta de Luna para medir discriminacion real

- Subconjunto de tension alrededor del umbral con cobertura SIMETRICA.
- Bandas estrechas: 14.5-14.9, 14.9-15.0, 15.0-15.1, 15.1-15.5.
- Casos a 14.99, 15.00, 15.01 cuando la precision lo permita.
- Al menos 30 por lado como objetivo inicial.
- Mantener el banco general separado del banco de tension.

### 17.7 5 chequeos adicionales que Luna propone agregar

1. Consistencia de etiquetas: cada label debe corresponder estricta-
   mente a la condicion de distancia acordada.
2. Baseline determinista: correr "if dist<15: terminar else ir_a"
   sobre el banco. Si no da 100%, algo esta mal antes de entrenar.
3. Cobertura especifica alrededor del umbral (no solo gap > 3m).
4. Auditoria de duplicados y contaminacion train/confirmatorio.
5. Pruebas contrafactuales: variar distancia a traves del limite
   debe cambiar la etiqueta; variar variables irrelevantes no.

### 17.8 Distincion abortar/advertir (coincide con el Director)

- **Errores de integridad** (schema roto, IDs duplicados, fuga,
  etiquetas incompatibles): BLOQUEAN.
- **Advertencias de calidad** (cobertura asimetrica, pocos casos,
  margen insuficiente): AVISAN pero no bloquean.

pre_entrenamiento.py debe distinguir entre los dos niveles.

### 17.9 Proximo paso

1. Conservar el resultado de CC003 v4 como perteneciente a esta
   version del test. No reescribir retrospectivamente.
2. Consultar a Claude con el mismo informe (paralelo a esta seccion).
3. Definir el proximo experimento para medir discriminacion real
   (mas acciones, sin umbral explicito, con contrafactuales).
4. Idea del Director (2026-10-12): achicar el umbral de 15m a
   2-3m para preparar la proxima fase (canales estrechos).
   Pendiente de verificar viabilidad tecnica.

