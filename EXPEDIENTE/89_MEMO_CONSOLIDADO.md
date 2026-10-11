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

