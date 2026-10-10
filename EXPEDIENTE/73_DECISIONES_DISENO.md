# DECISIONES DE DISENO — Timonel

**Fecha:** 2026-10-10
**Autor:** Director + consulta a Luna GPT
**Estado:** CONGELADO. Ninguna linea de codigo se toca hasta que este memo este commiteado.
**Reemplaza:** no reemplaza nada. Complementa memo 71 (estado real) y memo 72 (fix format:json).

---

## 0. Proposito

Tras una auditoria completa del sistema (15 fallas identificadas), el Director consulto a Luna GPT y tomo 5 decisiones de diseno + 2 decisiones adicionales. Este memo las congela.

Sin este memo, en 3 dias no sabemos que se decidio ni por que.

---

## 1. LAS 5 DECISIONES PRINCIPALES

### Decision 1 — Accion + parametro (Opcion C)

El LLM produce accion Y parametro. La metrica principal es la concordancia de la accion. Los parametros se evaluan por separado (error angular circular).

Razon: no confundir "elegir bien la maniobra" con "ejecutarla con precision".

### Decision 2 — terminar evaluable (Opcion A)

Se incorpora terminar al oraculo con semantica explicita:
- Si dist < 15m -> accion terminal exitosa.
- Si dist >= 15m -> accion invalida.

Se resuelve en el criterio del oraculo, NO silenciosamente en el runner.

### Decision 3 — El LLM ve el viento (Opcion A)

Se agrega viento al prompt. Los 3 modelos y el piloto Python reciben las mismas variables observables.

Razon: el oraculo simula con viento. Si el LLM decide sin viento, comparamos decisiones tomadas con informacion distinta.

### Decision 4 — Se elimina la regla de decision del prompt (Opcion B)

El prompt explica mision, acciones, parametros y restricciones. NO dice que maniobra corresponde a cada condicion del estado.

Razon: medir discriminacion, no obediencia.

### Decision 5 — Ampliar el oraculo (Si)

El oraculo debe devolver:
- Accion optima.
- Parametros que utilizo.
- Puntuaciones por accion y horizonte.
- Margen respecto de la segunda mejor alternativa.

NO optimizar el oraculo en la misma pasada. Primero ampliar, despues optimizar con tests de regresion.

---

## 2. LAS 2 DECISIONES ADICIONALES

### Adicional 1 — Congelar que significa "ganar" en el oraculo

Antes del benchmark hay que fijar:
- Funcion de utilidad (progreso, seguridad, alineacion).
- Como se combinan los horizontes (5s, 15s, 30s, 45s).
- Que es un empate.
- Margen minimo para considerar unica una accion.

Sin esto, el ground truth puede cambiar aunque el estado sea identico.

### Adicional 2 — El prompt primario no lleva experiencias ni historial

Primero se mide el LLM con estado + instrucciones generales. La memoria se evalua DESPUES, como condicion experimental separada.

Razon: evitar el defecto del memo 63 (misaligned experience replay) de raiz.

---

## 3. LOS 2 RIESGOS ADICIONALES

### Riesgo 1 — Circularidad del benchmark

Si el piloto Python comparte codigo o logica con el oraculo, la comparacion "LLM vs Python" mide cuanto se parecen, no cuanto navega cada uno.

Accion: auditar independencia Python vs oraculo ANTES del benchmark.

### Riesgo 2 — Runtime bloqueante

Carry-over confirmado (memo 65) y cambio de regimen no resuelto (memo 64) siguen bloqueando el benchmark confirmatorio.

Accion: cualificar el protocolo de ejecucion ANTES del benchmark.

---

## 4. ORDEN DE EJECUCION (6 pasos)

1. Congelar semantica de las 4 acciones + funcion de utilidad.
2. Ampliar el oraculo (sin optimizarlo).
3. Corregir prompt y parser.
4. Validar el banco con etiquetas independientes.
5. Cualificar el runtime.
6. Recien entonces: benchmark contra los 3 modelos y Python.

---

## 5. LO QUE NO SE HACE

- No se toca codigo hasta que este memo este commiteado.
- No se corre ningun benchmark con Qwen todavia.
- No se mezcla ampliacion del oraculo con optimizacion.
- No se corre el benchmark confirmatorio antes de cualificar el runtime.

---

## 6. FALLA 15 DEL INFORME — El oraculo es costoso

El oraculo corre ~15 simulaciones por decision (4 horizontes x 3 recetas + 3 extra del horizonte maximo).

400 contextos = ~6000 simulaciones solo para el oraculo. Tener en cuenta para el diseno.

Se optimiza DESPUES de ampliar, con tests de regresion.

---

## 7. REFERENCIAS

- Memo 71: estado real del Timonel (H-CARRY-1 confirmado, bloqueantes reales).
- Memo 72: fix del bug format:json.
- Informe enviado a Luna GPT (2026-10-10): las 15 fallas + las 5 decisiones.
- Respuesta de Luna GPT (2026-10-10): las decisiones tomadas.

---

## 8. FIRMA

**Estado:** CONGELADO.
**Proximo paso:** commit de este memo, despues empezar por el paso 1 del orden de ejecucion.
**Regla:** sin este memo commiteado, no se toca codigo.
