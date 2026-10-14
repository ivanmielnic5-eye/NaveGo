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



---

## 18. CONSULTAS A LUNA Y CLAUDE — CONSTRUCTO Y PREGUNTAS PENDIENTES (2026-10-12)

### 18.1 Contexto

Tras el resultado de CC003 v4 (100% pero midiendo aplicacion del
criterio, no discriminacion), se consulto a Claude y a Luna con dos
preguntas:

1. Constructo por fase (que capacidad especifica le atribuimos al
   modelo en cada una de las 7 fases).
2. Las preguntas que no nos estamos haciendo.

Las respuestas COMPLETAS estan en los anexos:
- EXPEDIENTE/ANEXOS/89_ANEXO_B_CLAUDE.md
- EXPEDIENTE/ANEXOS/89_ANEXO_B_LUNA.md
- (pendiente) EXPEDIENTE/ANEXOS/89_ANEXO_B_NOTEBOOK_LLM.md

### 18.2 Indice de la respuesta de Claude (anexo B-CLAUDE)

- Correccion de estado: "Fase 1 cerrada" -> "prueba unitaria de
  aplicacion de contrato con umbral fijo".
- Hipotesis central propuesta: "decision condicionada por contrato"
  (cuando cambia la especificacion escrita, la decision cambia sin
  reentrenar). Es lo unico que un LLM aporta sobre un arbol.
- Requisitos comunes a todas las fases: baselines obligatorios,
  contrafacticos de contrato, simetrias, valores no vistos, lazo
  cerrado.
- Tabla de constructo por fase (7 fases).
- Tabla de criterios de falsacion (7 fases).
- Bloqueantes comunes y especificos entre fases.
- Las preguntas que no nos hacemos (8 preguntas).
- Lo que deberia hacernos parar (7 senales).
- Otros puntos: riesgos estructurales de la hoja de ruta.
- Bloqueante X antes de Fase 2: un test de Fase 1 que pueda fallar
  (umbral T variable, valores no vistos, baselines que no lleguen
  al 100% por construccion, hipotesis escrita).

### 18.3 Indice de la respuesta de Luna (anexo B-LUNA)

- Decision estrategica inicial: no avanzar a Fase 2 como si Fase 1
  hubiera demostrado discriminacion.
- Constructo por fase (7 fases, cada una con hipotesis falsable,
  metrica primaria, baseline, condicion de cierre).
- Bloqueos entre fases (tabla de 5 bloqueos comunes: validez del
  entorno, validez de la referencia, capacidad minima, seguridad
  operacional, reproducibilidad).
- Las preguntas que no nos hacemos:
  - Copiloto o piloto automatico.
  - Que aporta el LLM sobre Python.
  - Separacion percepcion/planificacion/control.
  - Que pasa cuando el estado es desconocido o contradictorio.
  - Como se evita medir solo memorizacion.
  - Como se determina si el sistema es seguro.
- Que deberia hacernos parar y repensar (4 senales).
- X antes de Fase 2: 5 entregables (constructo aprobado, referencia
  valida, baseline Python, evaluacion confirmatoria, criterio de
  avance predefinido).
- Cita IMO (Organizacion Maritima Internacional) para buques
  autonomos como referencia metodologica.
- Cierre: la meta no es llegar a Fase 7, es construir evidencia
  acumulativa de que sabe hacer Timonel, en que condiciones, con
  que limites, y que valor aporta al capitan.

### 18.4 Coincidencias entre Luna y Claude

- Fase 1 no esta cerrada. Lo que se cerro es una subprueba de
  aplicacion del criterio de finalizacion.
- No avanzar a Fase 2 fingiendo que Fase 1 demostro discriminacion.
- Cada fase necesita: constructo, hipotesis falsable, baseline,
  criterio de falsacion. Fijados ANTES de correr.
- La pregunta central: que aporta el LLM sobre Python.
- Copiloto vs piloto automatico: hay que decidirlo antes de Fase 2.
- Penrose: sin hipotesis operacionalizable, fuera del roadmap.

### 18.5 Complementariedades

- Claude puso nombre al constructo central ("decision condicionada
  por contrato") y las tecnicas de medicion (logprobs, curva
  psicometrica, AUC de atajos).
- Luna puso la estructura por fase completa (hipotesis, metrica,
  baseline, cierre, bloqueante) y los 5 entregables concretos
  antes de Fase 2.
- Luna agrega: IMO como referencia, el problema del ruido en el
  estado real, la necesidad de "no se" / abtencion como salida.
- Claude agrega: la hipotesis central, los baselines obligatorios
  (incluye modelo base sin SFT), el analisis por logprobs.

### 18.6 Nota

Este anexo preserva las respuestas COMPLETAS. El memo 89 hace de
indice. Cualquier decision que tomemos sobre el proyecto tiene que
citar el anexo correspondiente.



---

## 19. HIPOTESIS CENTRAL DEL PROYECTO — DOS ETAPAS (Director, 2026-10-12)

### 19.1 El marco

Tras las consultas B y C a Claude y Luna (anexos B y C), el Director
fijo el marco del proyecto en dos etapas claramente separadas:

**ETAPA 1 — ¿APORTA O NO APORTA EL LLM?**

Pregunta: comparar el LLM contra Python (regla, arbol, controlador)
en la misma tarea.

Requisitos:
- Baselines que puedan ganarle al LLM (no baselines triviales).
- Metricas que distingan "acierta" de "decide".
- Sin la regla escrita en el prompt.
- Multiples variables relevantes.
- Contrafactuales.
- El LLM tiene que aportar algo, no empatar.

Si el LLM no supera al baseline: la hipotesis se refuta para esa
configuracion. No significa que todo LLM sea incapaz. Significa que
para este modelo (Llama 3.1 8B) y esta tarea, SFT no alcanza.

**ETAPA 2 — SI APORTA, ¿EN QUE DIMENSION Y CUANTO?**

Pregunta: si Etapa 1 pasa, medir:
- Magnitud: cuanto aporta.
- Dimension: en que aporta (interfaz en lenguaje, adaptacion a
  contrato, conocimiento nautico implicito, otra).
- Limites: donde deja de aportar.
- Potenciales: que se puede aprovechar para el copiloto.
- Limitaciones: que no hay que pedirle.

Etapa 2 es la fase de arquitectura del copiloto. No es una fase mas
del ABC. Es la siguiente etapa, la que el Director dejo explicitamente
para despues.

### 19.2 Las 4 dimensiones donde el LLM podria aportar

(Claude, anexo C, seccion A1)

1. Interfaz en lenguaje natural.
2. Adaptacion a cambios de contrato sin reentrenar.
3. Conocimiento nautico implicito.
4. Otras (a determinar por el experimento).

Ninguna de las 4 se asume. Todas se demuestran.

### 19.3 Lo que Luna y Claude aportan a esta hipotesis

**Claude** (anexo C):
- H1 (competencia aprendida) central. H2 (condicionamiento por
  contrato) diferencial.
- 3 escenarios de valor segun H1/H2.
- Distincion aprendizaje vs obediencia: derivacion + variacion
  linguistica.

**Luna** (anexo C):
- H1 con 4 componentes: dependencia estado, correccion,
  generalizacion, valor incremental. Los 4 necesarios.
- H2 como auxiliar, va al copiloto futuro.
- 3 condiciones separadas para test: regla explicita / sin regla /
  cambio de contrato.

**Coincidencias entre los dos:**
- H1 central, H2 auxiliar.
- Fase 1 actual es prueba unitaria, no evidencia de aprendizaje.
- Necesidad de contrafactuales, baselines, criterios predefinidos.

### 19.4 Lo que el Director agrega al marco

Separar las dos etapas. Claude y Luna las mezclaron en la misma fase.
El Director las separa:

- Primero: se demuestra que hay aporte (Etapa 1).
- Despues: se mide el aporte (Etapa 2).

Razon: si Etapa 1 no pasa, Etapa 2 no tiene sentido. Y si Etapa 1
pasa, Etapa 2 tiene una direccion clara: buscar DONDE esta la
ventaja, no asumirla.

### 19.5 Lo que NO se hace todavia

- No se rediseña el test todavia. Eso es trabajo del proximo paso.
- No se decide el orden exacto de las fases. Claude y Luna
  discrepan (velas antes o despues de obstaculos). Decision
  pendiente.
- No se adopta la terminologia de Claude (C0-C4) hasta que el
  Director la revise.
- No se toca el codigo del test.

### 19.6 Proximo paso

Disenar el test de Etapa 1:
- 4 acciones.
- Multiples variables.
- Sin regla en el prompt.
- Baselines: regla, arbol, modelo base sin SFT, Python.
- Contrafactuales.
- Analisis psicometrico (ya validado).
- T variable.

Con criterios de falsacion fijados ANTES.

### 19.7 Referencias

- Anexo B: primera consulta (constructo y preguntas pendientes).
- Anexo C: segunda consulta (hipotesis central y reordenamiento).
- Consultas completas preservadas sin resumir.


---

## 20. CIERRE DEL ANÁLISIS DE BANCO A

**Fecha:** 2026-10-12
**Referencias:** commits 24c53b8 y a8703f0, consulta a Luna 2026-10-12.

### 20.1 Encuadre

Según los documentos (commit 24c53b8 + secciones 1, 2 y 5 de este memo),
Banco A implementa **Fase 1a** ("Contrato"), con hipótesis falsable y
criterio de falsación preregistrado. No es un smoke test de
infraestructura. Esa lectura alternativa no está respaldada por los
documentos.

### 20.2 Qué se verificó

Pipeline end-to-end:
- Carga de dataset JSONL desde Kaggle: OK
- Aplicación de chat template Llama 3.1: OK
- Entrenamiento LoRA r=16 sobre Llama 3.1 8B en 4-bit: OK
- Guardado del adapter (167.8 MB): OK
- Recuperación del adapter: OK
- Generación en formato válido ("1" o "2"): OK

Dataset:
- Train: 600 ejemplos (284 "1", 316 "2"). T en {10, 15, 20, 25}.
- Val: 200 ejemplos (97 "1", 103 "2").
- Confirmatorio: 750 ejemplos. T en {12.5, 17.5, 22.5}.
- Regla: `d < T -> terminar; d >= T -> ir_a`.

Entrenamiento:
- global_step = 150 (2 epochs sobre 600).
- train_loss final = 0.1880.
- log_history: loss 2.00 en step 10 -> 0.05 en step 20 -> meseta
  hasta step 150. eval_loss ≈ train_loss en los tres checkpoints.
- Warning documentado: "num_items_in_batch could not be counted...
  gradient accumulation very slightly less accurate". No es error,
  no causó el colapso.

Evaluación del SFT sobre val:
- SFT: 103/200 = 51.5%.
- Fallos: patrón uniforme real="1" pred="2".
- Colapso a la clase mayoritaria (ir_a).

### 20.3 Qué NO se verificó

- Si el loss se calculó con `train_on_responses_only` (enmascaramiento
  del prompt) o sobre toda la secuencia. No disponible el `.ipynb`
  ejecutado con GPU.
- Evaluación del SFT sobre el confirmatorio (750).
- Comparación emparejada base vs SFT sobre los mismos contextos.
- Causa exacta del colapso, aislada.

### 20.4 Hallazgo: contradicción prompt/etiqueta

Archivos: `prompt_banco_A.py` + `generar_banco_A.py`.

- PROMPT: declara que `terminar` requiere `d < T` **Y** "el barco
  está navegando a baja velocidad".
- ESTADO: solo entrega `d` y `T`. No entrega velocidad.
- ETIQUETA: `d < T -> terminar`, sin velocidad. `sog` y `viento_kn`
  son constantes (0.0).

El modelo lee un contrato que no puede verificar completamente.
Es una explicación plausible del colapso a `ir_a`, pero no la única
posible. La corrección metodológica es inequívoca: el prompt y el
generador deben describir exactamente la misma tarea.

### 20.5 Resolución 51.5% vs 52.3%

Dos mediciones distintas, sobre sets distintos:

| Medición | Modelo | Set | N | Accuracy |
|---|---|---|---|---|
| 52.3% | Base sin SFT | Confirmatorio | 750 | 392/750 |
| 51.5% | SFT (run A) | Val SFT | 200 | 103/200 |

El 52.3% proviene del commit a8703f0. No hay contradicción.

### 20.6 Estado del criterio de falsación de Fase 1a

Criterio 1 (memo sección 2): "el umbral efectivo no sigue a T".
**Se activa.** El modelo colapsó a ir_a en todas las bandas.

Criterio 2: "el modelo base sin SFT ya saca ≈100%".
**No se activa.** El base saca 52.3%.

Señal de parada (memo sección 5): "el modelo base iguala al SFT".
Pendiente de verificar emparejadamente. Los dos números actuales son
de sets distintos.

### 20.7 Conclusión

El pipeline funcionó end-to-end. La capacidad de Fase 1a **no quedó
respaldada** por el checkpoint. La causa exacta del fallo no está
aislada. No se declara refutada la posibilidad de que Llama 3.1 8B
aprenda la comparación con otro diseño.

---

## 21. RESPUESTA DE LUNA — BANCO A (2026-10-12)

Consulta realizada tras el análisis preliminar. Respuesta completa en
`ANEXOS/89_ANEXO_D_LUNA.md`.

### 21.1 Puntos clave

1. No reclasificar retroactivamente Banco A como smoke test.
2. La contradicción prompt/etiqueta es real y plausible causa del
   colapso, pero no demostrada como causa única.
3. El `loss = 0.053` no debe interpretarse como firma inequívoca de
   predecir la clase mayoritaria si el loss incluye el prompt.
4. La señal de parada del memo (base = SFT) no está formalmente
   activada: los números 52.3% y 51.5% son de sets distintos.
5. No reentrenar todavía. Aislar primero el fallo.
6. Verificar: (a) enmascaramiento del loss, (b) reconciliación
   prompt/etiquetas, (c) comparación emparejada base vs SFT,
   (d) generalización por T en T no vistos.

### 21.2 Clasificación propuesta

> "La hipótesis de generalización del umbral no está respaldada por
>  el checkpoint actual y falla en la validación reportada. La
>  conclusión confirmatoria sobre generalización a umbrales no vistos
>  queda pendiente de una evaluación con el checkpoint congelado."

---

## 22. DECISIONES PENDIENTES Y PLAN DE BANCO B

### 22.1 Decisiones del Director pendientes

1. ¿Banco A se cierra como Fase 1a no respaldada, o se rediseña
   y se corre una nueva versión?
2. ¿La condición de "baja velocidad" pertenece al objetivo del
   proyecto? Si sí: agregar velocidad al estado y a las etiquetas.
   Si no: sacarla del prompt y documentar el error.
3. ¿Se consulta a Claude antes del próximo test?
4. ¿Se adopta la propuesta de prompt saneado de Luna (sin mención a
   velocidad, d con 8 decimales)?
5. ¿Se pasa a Luna el `.ipynb` local o los 5 ejemplos reales que pide
   para revisar el enmascaramiento?

### 22.2 Plan de Banco B (borrador)

Orden propuesto, respetando regla de un paso por vez:

1. **Reconciliar prompt y etiquetas.** Decidir si la velocidad
   pertenece al objetivo o no. Ajustar el generador y el prompt para
   que describan la misma tarea.
2. **Verificar enmascaramiento del loss.** Revisar el notebook
   (local o el de Kaggle si aparece la versión con GPU). Si no se
   enmascaró, corregir para el próximo run.
3. **Comparación emparejada base vs SFT.** Evaluar ambos sobre los
   mismos 750 contextos confirmatorios congelados, mismo prompt,
   parser y procedimiento. Esto responde la señal de parada del
   memo.
4. **Medir generalización directamente.** Tasa de `terminar` por T,
   matriz de confusión, umbral efectivo estimado en T no vistos.
5. **Consulta a Claude** antes de generar el próximo banco.

### 22.3 Lo que NO se hace todavía

- NO reentrenar sin aislar el fallo.
- NO crear nuevos bancos sin resolver la contradicción prompt/etiqueta.
- NO usar el confirmatorio de A para decidir el diseño de B.

### 22.4 Firma

**Estado:** Banco A cerrado analíticamente. Fase 1a no respaldada.
**Próximo paso:** decisión del Director sobre secciones 22.1.
**Regla:** calidad primero, performance después.

---

## 25. PROBE F2 — EL ADAPTADOR DE A2 GENERALIZA A UNA CLAUSULA NUEVA

**Fecha:** 2026-10-13
**Referencias:** seccion 24, anexo H (Claude), anexo G (Luna).

### 25.1 Que se probo

Etapa 0 del protocolo A3 (seccion 24.9). Sin reentrenar.

Se evaluo el adaptador de A2 (entrenado solo con F1: d<T -> terminar)
sobre 200 contextos con un contrato nuevo (F2):
terminar si d<T Y v<=v_max. La palabra "velocidad" no aparecio nunca
en el entrenamiento de A2.

Cuadrante clave Q2: d<T Y v>v_max. Etiqueta correcta: ir_a.
Si el modelo dice terminar en Q2, ignora la clausula adicional.

Se comparo contra el mismo modelo con disable_adapter (base sin SFT).

### 25.2 Resultado

Puntaje forzado (lp(terminar) - lp(ir_a)):

  Cuadrante                            SFT      BASE
  Q1 (d<T, v<=vmax, label=terminar)    1.000    0.980
  Q2 (d<T, v>vmax,  label=ir_a)        0.980    0.120
  Q3 (d>=T, v<=vmax, label=ir_a)       1.000    0.260
  Q4 (d>=T, v>vmax,  label=ir_a)       1.000    0.020

  GLOBAL                               0.995    0.345
  Q2 (clave)                           0.980    0.120

Prediccion de terminar en Q2 (deberia ser 0):
  SFT:  1/50
  BASE: 44/50

Prediccion de terminar en TODOS los cuadrantes (base):
  Q1: 49/50  Q2: 44/50  Q3: 37/50  Q4: 49/50
  El base colapsa a "terminar" cuando el prompt menciona velocidad.
  Falla en los cuatro cuadrantes, no solo en Q2.

Veredicto del probe: SFT APORTA. Lee contrato F2 donde el base falla.

### 25.3 Lectura

El adaptador de A2 respeta una clausula que no vio durante el
entrenamiento. El base sin SFT no la respeta (colapsa a "si d<T
entonces terminar" ignorando todo lo demas).

Diferencia en el cuadrante clave: 86 puntos (0.980 vs 0.120).

Lectura tentativa: el SFT no aprendio solo "si d<T -> terminar".
Aprendio algo mas general: "terminar solo cuando TODAS las condiciones
del contrato se cumplen visiblemente". Eso es lectura de contrato, no
memorizacion de una regla fija.

### 25.4 Cautelas

1. Un solo experimento. Una clausula nueva (velocidad), un T fijo
   (15), un formato. A3 mide en serio con multiples familias,
   formulaciones y unidades.

2. No mide LLM vs parser Python. Mide LLM con SFT vs LLM sin SFT.
   La pelea H1b (LLM vs P-text) sigue pendiente.

3. Q2 SFT = 0.98, no 1.0. Un fallo. No se sabe si es ruido o
   sistematico. Se aclara cuando A3 etapa 1 corra con mas variantes.

4. El veredicto "SFT APORTA" es sobre esta tarea y este artefacto.
   No es una conclusion sobre "los LLM" en general.

### 25.5 Implicaciones para A3

El resultado del probe apoya H1a (capacidad de adaptacion) de arranque:

- El SFT de A2 ya generaliza a una familia nueva (F2) sin reentrenar.
- El base no tiene esa capacidad (colapsa a "d<T -> terminar").
- El SFT aporta valor en la tarea acotada de "leer un contrato nuevo".

Si esto se sostiene con F3 (prioridad de seguridad) y F4 (abstencion),
el LLM tiene un rol claro como INTERPRETE de contratos (no como
decisor autonomo).

H1b (LLM vs parser Python) sigue pendiente. La pelea real no es
contra el base, es contra P-text.

### 25.6 Pendientes de A2

Del cierre de A2 (seccion 24.9, etapa 0) quedan:

- Invariancia semantica (orden de acciones invertido). No medida.
  Se mide en A3 etapa 1.
- El fallo unico de Q2 SFT (1/50). Puede ser ruido o sistematico.
  Se aclara en A3 etapa 1 con mas variantes.

### 25.7 Proximo paso

Etapa 1 del protocolo A3 (seccion 24.9):
- Generar F1 + F2 con formulaciones F-train y F-dev.
- Entrenar LLM-A3 (1 semilla).
- Evaluar contra P-struct, P-text, arbol, LLM-A2 congelado, LLM-A3.
- Aplicar compuertas y cribado.

Antes de ejecutar, queda una consulta abierta a Claude (anexo H,
seccion 6): definir la metrica primaria de "ventaja practica" y el
protocolo de esfuerzo humano de forma preregistrada.

### 25.8 Firma

**Estado:** PROBE F2 ejecutado. SFT aporta sobre el base en F2.
**Proximo paso:** etapa 1 de A3, previa consulta a Claude.
**Regla:** calidad primero, performance despues.

---

### 25.9 CORRECCIONES TRAS LA REFORMULACION DE CLAUDE (anexo J)

**Fecha:** 2026-10-13
**Referencias:** anexo I (Claude), anexo J (Claude).

Claude reformulo su lectura del probe al ver el contexto completo. Las
correcciones son metodologicas, no invalidan el probe, pero debilitan
la lectura fuerte.

**Correccion principal: v_max fue constante (0.3 nudos).**
0.3 nudos es casi detenido. Un modelo puede responder `ir_a` por una
prior del mundo ("un barco que se mueve no termino"), no por leer la
clausula de velocidad. El probe no distingue esas dos cosas.

**Control decisivo que falta:** casos que contradicen la prior.
Ejemplo: v=1.5 con v_max=2.0, d<T. Correcto: `terminar` (el barco se
mueve pero esta dentro del limite). Si el modelo dice `ir_a`, usa la
prior, no lee el contrato.

**Correccion secundaria: la base no es control util.**
Colapsa a `terminar` en los 4 cuadrantes (49/44/37/49 de 50). No
resuelve la tarea de F2 en ningun cuadrante. La metrica de titular
deberia ser el **contraste dentro del SFT** (mismo d, T, v; solo
cambia v_max), no SFT vs base.

**Cambio de brazo primario de H1b-interfaz.**
Claude corrige su recomendacion anterior: el primario pasa a ser
**LLM-A3** (entrenado con F-train y F-dev), no el adaptador A2
congelado. Razon: P-text se desarrolla con F-train y F-dev; comparar
al adaptador A2 (que solo vio F-train) contra P-text es asimetrico
en contra del LLM.

El adaptador A2 congelado queda como **brazo de H1a** (la lectura
literal de "sin reentrenamiento", cero exposicion a parafrasis).

**Etapa 0b — controles obligatorios antes de etapa 1.**
Solo puntuar, sin entrenar. Adaptador A2 congelado:

  B1 Placebo: v visible, SIN clausula de velocidad (100 contextos).
     Criterio: exactitud >= 0.95, y en (d<T, v alta) tasa de
     `terminar` >= 0.95.
  B2 v_max variable: v_max en {0.3, 0.6, 1.0, 2.0, 4.0}, con casos
     contra-prior (v moderada con v_max alto -> `terminar`).
     Criterio: exactitud >= 0.95, y >= 0.90 en contra-prior.
  Pares contrafacticos: mismo d, T, v; solo cambia v_max (~50 pares).
     Metrica: fraccion de pares con cambio correcto.
  Re-puntuado con orden invertido sobre probe + 0b. Invariancia.
  Vecindad del fallo Q2 (~30 contextos). Descriptivo.
  Checkpoints 50/100/150/154 sobre el probe. Descriptivo.

**Regla de decision tras 0b:**
- Pasa B1 y B2: A2 congelado es brazo H1a de etapa 1. El probe queda
  como "lee la clausula con umbral variable (para este artefacto)".
- Falla B1 o B2: el resultado del probe se reinterpreta como
  heuristica. Etapa 1 exige entrenar LLM-A3 con v_max variable y
  placebo.

**Principio general para futuras familias:** cada familia nueva trae
su placebo (la variable aparece en el estado, sin clausula en el
contrato) y sus casos contra-prior. Para F3 (seguridad): obstaculo
presente sin clausula de seguridad.

**Correcciones a la redaccion del memo (aplicadas en 25.9):**
- 25.2/25.3: la metrica de titular pasa a ser el contraste dentro
  del SFT, no los 86 puntos vs base.
- 25.5: "ya generaliza a una familia nueva" es demasiado fuerte.
  Correccion: "generaliza a un conjunto adicional con umbral fijo;
  pendiente 0b".
- 25.6: invariancia y fallo Q2 pasan a etapa 0b, no a etapa 1.
- 25.7: reordenar. Primero 0b; despues etapa 1.

---

### 25.10 ETAPA 0b — EL SFT NO LEE v_max (FALLA B2)

**Fecha:** 2026-10-13
**Referencias:** anexo J (Claude), seccion 25.9.

La etapa 0b se ejecuto con el adaptador de A2 congelado. Cuatro bloques,
solo puntuar, sin entrenar:

  B1 placebo: v visible, contrato SIN clausula de velocidad (100).
  B2 v_max variable: contrato CON clausula, v_max en 5 valores (94).
  B3 contrafactual: mismo d/T/v, cambia solo v_max (100).
  B4 vecindad del fallo Q2 (30).

### 25.10.1 Resultado

  Bloque                                        SFT      BASE
  B1 (d<T, v alta, SIN clausula)               1.000    0.080
  B2 contra-prior (v moderada, v_max alto)     0.875    1.000
  B3 pares correctos al cambiar v_max          0.960    ---
  B4 vecindad                                  ---      ---

  VEREDICTO 0b: FALLA B2.

Criterios preregistrados (seccion 25.9):
  - pasa B1 si acc >= 0.95: PASA (1.000).
  - pasa B2 contra-prior si acc >= 0.90: FALLA (0.875).

### 25.10.2 Lectura

**El SFT no lee el v_max del contrato.** Usa la magnitud de `v` como
pista. Cuando ve `v` moderada (por ejemplo 1.5) con `v_max` alto
(por ejemplo 2.0), el correcto es `terminar` (el barco se mueve pero
dentro del limite). El SFT falla en esos casos: dice `ir_a`.

Traduccion: el modelo no compara `v` contra `v_max`. Mira `v` sola y
aplica "si se mueve, no termino". Es una prior del mundo, no una
lectura del contrato.

**B1 pasa limpio.** Cuando el contrato NO menciona velocidad, el SFT
la ignora (acc=1.000). No es ciego: distingue si la velocidad aparece
o no en el contrato. Solo que cuando aparece, la usa mal.

**B3 pasa casi limpio (0.960).** El SFT cambia decision en 48/50
pares al cambiar `v_max`. Hay cierta lectura. Pero no la suficiente:
falla en 3 casos de 24 contra-prior en B2. La lectura es parcial.

**La base no es control util.** Colapsa a `terminar` en B2 y acierta
1.000 por coincidencia con la mayoria. Ya lo dijo Claude en el
anexo J: la metrica de titular debe ser el contraste dentro del SFT,
no SFT vs base.

### 25.10.3 Por que esto es evidencia valiosa

El probe F2 original (seccion 25.2) tenia `v_max = 0.3` fijo, casi
detenido. Con ese corte, dos explicaciones dan el mismo resultado:
- Lectura de contrato: "el contrato dice v <= 0.3, y v = 4.29 > 0.3
  -> ir_a".
- Prior del mundo: "el barco se esta moviendo -> no termino".

La etapa 0b separa esas dos explicaciones. Y el SFT cae del lado de
la prior.

**Sin la etapa 0b, la seccion 25.5 habria pasado a la etapa 1
afirmando que el SFT "generaliza a una familia nueva". Eso era falso.**
La metodologia de control detecto el autoengano antes de propagarlo.

### 25.10.4 Consecuencias

**1. El probe F2 queda reinterpretado.**
La lectura fuerte ("el SFT lee el contrato") no era correcta. El SFT
respeta parte del contrato (B1: ignora v si no se menciona), pero no
compara `v` contra `v_max`.

**2. El brazo H1a de la etapa 1 NO puede ser el adaptador de A2
congelado.** Hay que entrenar LLM-A3 con `v_max` variable y casos
contra-prior. Claude ya lo habia anticipado (anexo J): si 0b falla,
el resultado del probe se reinterpreta como heuristica.

**3. El metodo de control funciona.** La etapa 0b era un control
barato (solo puntuar, sin entrenar). Detecto el problema antes de
invertir en A3. Es el tipo de control que el proyecto necesita.

**4. El B1 sigue siendo buena noticia.** El SFT distingue si la
velocidad aparece en el contrato o no. No es ciego. Solo que cuando
aparece, la usa mal.

### 25.10.5 Regla de decision aplicada

Segun la seccion 25.9:
- "Falla B1 (usa la velocidad como senal de cautela) o B2 (usa la
  magnitud de v e ignora v_max): el resultado del probe se
  reinterpreta como heuristica."

Se aplica el segundo caso: **FALLA B2**. El probe F2 se reinterpreta
como heuristica. La etapa 1 exige entrenar LLM-A3 con `v_max` variable
y placebo.

---

### 25.11 PASO 0c — DIAGNOSTICO DEL SESGO DE B2

**Fecha:** 2026-10-13
**Referencias:** seccion 25.10, anexo L (Claude).

El paso 0c se ejecuto sin datos nuevos: se re-puntuo el banco 0b
con el adaptador de A2 congelado, con orden normal y con orden
invertido, y se desglosaron los errores de B2 por margen |v-v_max|.

### 25.11.1 Resultado

  Invariancia al orden: 321/324 = 0.991 (pasa >0.95).
  B2 SFT (orden normal): acc = 0.883.
  B2 contra-prior: acc = 0.875 (n=24). 21/24 correctos.
  Errores contra-prior: 3.
    margenes |v-v_max|: min=0.56 max=3.26 media=1.50.

  VEREDICTO 0c: SESGO con margen grande.
  El modelo falla lejos del limite, no solo en frontera.

### 25.11.2 Lectura

Los 3 errores de contra-prior tienen margen grande (min 0.56,
max 3.26 nudos). No son ruido de frontera. Son sesgo.

Ejemplo: v=0.74, v_max=4.0 -> correcto `terminar`, el modelo
responde `ir_a`. No esta fallando por estar cerca del limite.
Esta fallando porque ignora `v_max`.

**Esto corrige mi lectura apresurada de la seccion 25.10.** Dije
"el SFT no lee v_max, usa la magnitud de v". Eso era demasiado
fuerte. La correccion de Claude (anexo L) es la correcta:

- B1=1.000 descarta "v alta -> cautela siempre".
- B3=0.960 muestra que la decision SI cambia al cambiar v_max.
- Lo compatible: **lectura parcial con sesgo hacia `ir_a` cuando
  v es moderada**, no ausencia de comparacion.

El problema es el sesgo, no la capacidad. Importante para A3: hay
que entrenar contra el sesgo, no ensenar la capacidad.

### 25.11.3 Invariancia al orden

321/324 = 0.991. Pasa limpio. Los 3 casos que cambian con orden
invertido son ruido de frontera, no un problema sistematico de
posicion. El prompt no tiene sesgo posicional.

### 25.11.4 Implicaciones para A3

El diseno de A3 etapa 1 (anexo L) ya incluia **>=40% de Q1 como
contra-prior** en el train. El 0c confirma que ese diseno es
obligatorio, no opcional:

- Sin contra-prior explicito, el SFT mantiene el sesgo (v moderada
  -> ir_a aunque v_max lo permita).
- El sesgo no se corrige con mas datos generales; se corrige con
  casos especificos donde v es moderada y v_max es alto.

No cambia el plan de A3. Lo justifica mejor.

### 25.11.5 Regla metodologica

El paso 0c costo minutos (solo puntuar, sin entrenar, sin datos
nuevos). Detecto la causa del fallo de B2 y corrigio la lectura
apresurada de 25.10.

**Patron:** antes de disenar un entrenamiento correctivo, agotar el
diagnostico con los datos que ya existen. La mayoria de los errores
se explican sin generar nada nuevo.

---

## 27. F-HELD GENERADO Y EVALUADO CON BASELINES

**Fecha:** 2026-10-13
**Referencias:** seccion 24 (protocolo A3), anexo L, borradores
f0_diseno_v2.md, luna_criterio_contaminacion.md.

### 27.1 Que es F-held

600 items con formulaciones retenidas que ni P-text ni el LLM vieron
durante su desarrollo.

- Autor del bruto: Perplexity, sesion aislada (sin contexto del
  proyecto).
- Consigna sellada antes de generar (SHA256:
  6ca5b526245f0d66e58edaa2bdd6d231e5949adeeb9da2a4e2d7e1574c128ab2).
- Bruto sellado (SHA256:
  5b6d7171d9617de7d4a0dc32ff113dfb3a8bbae2eae06168d24ebe8bf2693471).
- 60 formulaciones de la clausula de velocidad, sin usar las 4
  construcciones existentes.

Estructura:

- fheld_f2: 300 items (60 formulaciones x 5). Balance 150/150.
- fheld_f1: 300 items (6 T nuevos x 50). Balance 150/150.

T_F1_NUEVOS = {9, 13, 19, 21, 25, 27}.
T_F2_INTERP = {11, 17, 23}.
V_MAX_F2_INTERP = {0.4, 1.0, 1.6, 2.5}.

### 27.2 Evaluacion con baselines

  Modelo       F1 (T nuevos)  F2 (Perplexity)  Global
  P-struct     300/300 (100%) 300/300 (100%)   600/600 (100%)
  P-text       300/300 (100%) 150/300  (50%)   450/600  (75%)

P-text: 0 parseos fallidos, pero no reconoce las 60 formulaciones
nuevas. Al no encontrar v_max, cae al caso F1 y dice siempre
`terminar` (porque todos los F2 tienen d < T). Acierta 150
(terminar reales) y falla 150 (ir_a reales).

### 27.3 Lectura

- **El benchmark no esta techo-capped.** P-text no puede anticipar 60
  variantes nuevas con reglas escritas a mano.
- **Hay margen real para el LLM.** Si el SFT generaliza a
  formulaciones nuevas, puede aportar valor medible sobre P-text.
- **La cota superior sigue siendo P-struct (100%).** El LLM no puede
  superarla (spec perfectamente parseada). La pregunta es si se
  acerca.

### 27.4 Proximo paso

Entrenar LLM-A3 con banco A3 (1188 train / 352 val). Evaluar en los
5 splits de bancoA3 y en los 2 splits de F-held. Comparar:

- LLM-A3 vs P-text en F-held F2 (donde P-text falla).
- LLM-A3 vs P-struct en bancoA3 y F-held.
- LLM-A3 vs A2 congelado (transferencia de F1 a F2).

### 27.5 Decisiones pendientes del Director

- Subir banco A3 a Kaggle (dataset).
- Entrenar SFT (1 semilla).
- Guardar version antes de que cierre la sesion.

---

## 28. AUDITORIA DE F-HELD F2

**Fecha:** 2026-10-14
**Referencias:** seccion 27, borradores luna_observacion_a3.md,
claude_observacion_a3.md.

### 28.1 Que se audito

Despues del resultado SFT 0.977 vs P-text 0.500 en fheld_f2, se
verifico si el 0.500 era un bug o el comportamiento esperado.

Se auditaron 300 items de fheld_f2:

- Predicciones de P-text por item.
- Matriz de confusion completa.
- Coherencia entre v_max del prompt y v_max de la etiqueta.
- Parseo de P-text (que extrae y que no).

### 28.2 Resultado de la auditoria

**P-text nunca reconocio las formulaciones de Perplexity:**

  Parseos con v_max: 0 / 300
  Parseos sin v_max: 300 / 300

Las 4 regexes de P-text cubren F_train y F_dev. Ninguna coincide
con las 60 formulaciones de Perplexity.

**P-text cae al modo F1 (solo distancia).** Como todos los items de
fheld_f2 tienen d < T (el generador los hace asi a proposito para
aislar la clausula de velocidad), P-text dice siempre `terminar`.

**Matriz de confusion:**

  real=terminar, pred=terminar: 150
  real=terminar, pred=ir_a    :   0
  real=ir_a,     pred=terminar: 150
  real=ir_a,     pred=ir_a    :   0

  150 aciertos / 150 fallos = 0.500 exacto.

**Coherencia prompt/etiqueta:** 0/300 incoherencias.

### 28.3 Lectura

El 0.500 de P-text es exactamente el comportamiento esperado de un
parser que no reconoce las formulaciones nuevas y cae a un fallback.
No es bug.

La hipotesis de unidades (nudos vs m/s) no aplica. El prompt y la
etiqueta usan la misma unidad en los 300 items.

**Lo que la auditoria confirma:**

- P-text no generaliza a formulaciones que no vio.
- El LLM si generaliza (0.977).
- La diferencia de 47.7 puntos es real, no artefacto.
- El fallback de P-text no es ruido: dice siempre `terminar`, lo
  cual es consistente con "no vi la clausula de velocidad".

### 28.4 Encuadre

**Este resultado es una pieza de la investigacion de roles, no una
competencia entre LLM y Python.**

Lo que se aprendio:

- El LLM puede hacer algo que el parser no: interpretar
  formulaciones no vistas.
- El parser es determinista, rapido, auditable, pero no generaliza.
- Ambos tienen roles distintos. No es "gana uno".

La pregunta que abre: **como se complementan.** No "quien gana".

El LLM no reemplaza al parser. El parser no reemplaza al LLM.
**El circuito completo es lo que importa.**

### 28.5 Lo que no se pudo auditar todavia

- Los 7 errores individuales del SFT en fheld_f2. El eval guardo
  solo agregados. Requiere re-correr con logging individual.
- Los 4 errores en test_balanceado.
- Las compuertas restantes: concordancia generacion vs puntaje
  forzado, invariancia al orden.
- Segunda semilla.

### 28.6 Lo que sigue

Dos pistas en paralelo:

**Pista 1 (roles, offline):**
- Definir el circuito: interprete -> verificador -> decisor.
- Medir cada rol por separado.

**Pista 2 (sistema real, online):**
- El bridge NaveGo <-> Godot.
- Las conducciones que ya llegan a Puerto Esperanza.
- Pregunta: el LLM mejora, empeora o empata la conduccion.

**El punto de union:** si el LLM es buen interprete pero mal decisor,
el circuito correcto es LLM interpreta + Python decide. Si es bueno
en ambos, otra arquitectura. Eso hay que medirlo.
