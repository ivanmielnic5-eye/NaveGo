# HOJA DE RUTA — Fases de aprendizaje y auditoria del oraculo

**Fecha:** 2026-10-11
**Autor:** Director + Directora de Investigacion
**Estado:** ABIERTO. Documento de vision y plan.
**Complementa:** memos 73-84.

---

## 0. Proposito

Asentar dos cosas que surgieron en conversacion con el Director:

1. La vision de largo plazo: fases de aprendizaje del copiloto.
2. La auditoria inmediata del oraculo (memo 84) y como testearlo.

Sin este memo, en una semana no nos acordamos de nada.

---

## PARTE 1 — VISION DE LARGO PLAZO: FASES DE APRENDIZAJE

El objetivo final del sistema es un COPILOTO que asista al capitan,
no que lo reemplace. Lee el panorama y sugiere.

El aprendizaje se hace por fases, cada una prerequisito de la siguiente.
Es curriculum learning: se agrega dificultad de a poco.

### FASE 1 — ABC de conduccion (DONDE ESTAMOS)

Objetivo: el agente aprende las 4 acciones basicas.
- corregir_rumbo, ir_a_punto, frenar, terminar.

Estado: el piloto SFT (memo 83) llego a 65% accuracy. Colapso de accion
resuelto. Falta corregir el oraculo (memo 84) antes de seguir.

### FASE 2 — Velas

Objetivo: usar vela mayor y foque.
- Relacion vela-rumbo-viento.
- Ganar velocidad y eficiencia.

Estado: el simulador Godot ya tiene velas rotativas (Q/E mayor, Z/X foque).
Falta integrar al LLM.

### FASE 3 — Deteccion de objetos en superficie

Objetivo: evitar boyas, muelles, otras embarcaciones.
- "No chocar" como restriccion dura.

Estado: el simulador NO tiene obstaculos aun. Hay que modelarlos.

### FASE 4 — Deteccion de objetos en el fondo

Objetivo: evitar bajio, rocas.
- Sensores: solar, sonar, camara.

Estado: hay que agregar sensores al simulador.

### FASE 5 — Olas

Objetivo: encarar olas de frente (menor costo).
- Evitar olas laterales (riesgo de zozobra).

Estado: el simulador YA tiene olas, pero estan PLANCHADAS EN CERO
(por decision del Director, para no complejizar el ABC).
Activar cuando la Fase 1 este consolidada. Solo calibrar, no modelar.

### FASE 6 — Mar picado

Objetivo: multiples olas cruzadas, direcciones complejas.
- Direccion del barco en condiciones adversas.

Estado: muy avanzado. Requiere fisica mas rica.

### FASE 7 — El ojo (tesselaciones de Penrose)

Objetivo: percepcion visual eficiente.
- Codificacion de informacion compleja en patrones locales.
- El Director ya tiene experiencia con tesselaciones de Penrose
  de otra aplicacion.

Estado: idea, para mas adelante. No antes de la Fase 3.

### FASE FINAL — Copiloto del capitan

Objetivo: no reemplazar al humano. Asistirlo.
- Lee el panorama.
- Sugiere.
- El capitan decide.

---

## PARTE 2 — AUDITORIA INMEDIATA DEL ORACULO

### 2.1 Que sabemos

El oraculo es el GROUND TRUTH del proyecto. Etiqueta el banco CC002.
Aparece por primera vez en los memos 60-61.
Codigo en timonel/oraculo.py.

### 2.2 Que NO sabemos (pregunta del Director)

- Quien lo implemento (¿el Director? ¿una IA? ¿otra herramienta?).
- Cuando exactamente.
- Con que criterio se definieron los 4 horizontes (5, 15, 30, 45s).
- Por que el horizonte maximo es 45s y no otro numero.
- Si tuvo validacion propia cuando se creo.

### 2.3 Hallazgo del memo 84 (recordatorio)

En 75 casos con etiqueta corregir_rumbo del split DESARROLLO:
- 45/75 el oraculo tiene razon.
- 30/75 el modelo (ir_a_punto) tiene razon.
- El error crece con el desvio: 0% en 0-30°, 60% en 90-180°.

Esto NO demuestra que el 40% de etiquetas este mal. Demuestra
DISCREPANCIA con una metrica alternativa (distancia final a 60s).
La metrica del oraculo es diferente (progreso trapezoidal 4 horizontes).

---

## PARTE 3 — HIPOTESIS DEL DIRECTOR

### Hipotesis 1 — El horizonte de 45s es muy corto

El oraculo probablemente se limito a 45s por performance (16 simulaciones
por contexto). Pero 45s puede no alcanzar para ver el desastre que pasa
despues. En un caso, corregir_rumbo termino a 107m cuando empezo a 18m.

Test propuesto: subir el horizonte a 60s y 120s. Ver si el oraculo
cambia de opinion en los 30 casos discrepantes.

### Hipotesis 2 — El radio de giro es un "yeso" durante el aprendizaje

Idea del Director (excelente):

> "Es como enseñarle a correr a alguien con muletas y un yeso."

El simulador tiene radio de giro realista. Pero durante el APRENDIZAJE
del ABC, esto complejiza innecesariamente.

Propuesta: crear un MODO SIN RESTRICCIONES DE GIRO donde el barco
puede girar en el lugar. Comparar:
- Modo actual (con restricciones): ver quien falla.
- Modo sin restricciones: ver quien falla.

Si en modo sin restricciones:
- El oraculo cambia sus etiquetas -> la restriccion es la causa.
- El LLM acierta mas -> la restriccion le complica el aprendizaje.
- Ambos siguen fallando -> hay algo mas profundo.

### Hipotesis 3 — Curriculum learning

Ensenar de a poco:
1. Sin restricciones: "¿el agente sabe ELEGIR?"
2. Con radio de giro: "¿puede EJECUTAR?"
3. Con olas, viento, objetos: "¿sobrevive al mundo real?"

Riesgo: el modelo se sobreajusta al modo sin restricciones.
Mitigacion: fine-tunear despues con restricciones reales.

---

## PARTE 4 — PLAN DE AUDITORIA

### Etapa A — Origen del oraculo (30 min, CPU local)

1. git log del archivo oraculo.py.
2. Buscar en memos 57-62 menciones al oraculo y su justificacion.
3. Ver si hay tests del oraculo o hipotesis registradas.

Objetivo: saber si el oraculo fue validado cuando nacio.

### Etapa B — Horizonte extendido (30 min, CPU local)

1. Modificar el test para reconstruir los 4 horizontes originales.
2. Extender a 60s y 90s.
3. Graficar dist_a_meta(t) para las 4 acciones en los 30 casos discrepantes.
4. Ver si corregir_rumbo se "recupera" despues de los 60s.

### Etapa C — Sin restricciones de giro (30 min, CPU local)

1. Modificar el simulador para permitir un modo sin restricciones.
2. Correr el oraculo sobre los 30 casos.
3. Comparar etiquetas con el modo actual.

### Etapa D — Aislar viento (30 min, CPU local)

1. Correr los tests con viento=0.
2. Correr con semilla fija de viento.
3. Ver si el resultado cambia.

### Etapa E — Auditar las otras 3 clases (1 hora, CPU local)

1. Correr el test sobre ir_a_punto, frenar, terminar.
2. Ver si el problema es especifico de corregir_rumbo o es estructural.

### Etapa F — Decision

Con los datos de A-E:
- Si el sesgo se confirma -> reformar oraculo + re-etiquetar + re-entrenar.
- Si el sesgo se desmiente -> nuestro test estaba mal, seguir actual.
- Si es mixto -> distinguir zonas del espacio de estados.

---

## PARTE 5 — REGLA NUEVA DEL PROYECTO

**Adoptada 2026-10-11, a partir del hallazgo del memo 84:**

> Antes de cualquier entrenamiento futuro, auditar el oraculo sobre
> los casos a usar. No se entrena con ground truth sin validar.

Esto aplica a:
- Re-entrenamiento del SFT.
- Entrenamiento de fases 2-7.
- Cualquier futuro modelo.

---

## PARTE 6 — CONSULTAS PENDIENTES

- Luna: ya respondio al informe del oraculo (respuesta archivada).
- Claude: pendiente. Respondera con otro enfoque (falta credito).

La comparacion entre ambas va a informar la decision final.

---

## PARTE 7 — FIRMA

**Estado:** ABIERTO.
**Proximo paso:** prender la compu, correr Etapa A del plan de auditoria.
**Prioridad:** auditar el oraculo antes de seguir entrenando.

**Nota:** este memo es la hoja de ruta a largo plazo del proyecto.
Las fases de aprendizaje (Parte 1) se retoman despues de cerrar
la auditoria (Partes 2-5).
