# DISENO DE ARQUITECTURA HIBRIDA — Timonel v2

**Fecha:** 2026-10-11
**Autor:** Directora de Investigacion
**Estado:** PROPUESTA. Pendiente de implementar.
**Complementa:** memos 73-79.

---

## 0. Proposito

Disenar un prototipo hibrido (LLM + logica simbolica) que:
1. Aproveche las capacidades del LLM donde aporta valor.
2. Delegue a logica determinista las restricciones que puede resolver exacto.
3. Permita medir la contribucion REAL del LLM (no solo confirmacion).

---

## 1. MOTIVACION

La fase de prompting (memo 79) concluyo que los modelos no discriminan
robustamente entre las 4 acciones en zero-shot. Pero eso no responde:
"puede el LLM aportar valor en un sistema con soporte simbolico?".

Literatura de referencia:
- VL-Nav (DARPA TIAMAT): LLM + grafo simbolico 3D. 83-86% exito real.
- SGIM-STAR (NeurIPS 2025): alterna Q-learning y LLM Navigator.
- DORAEMON: Action Proposer genera candidatas, Policy-VLM elige.

Comun a todos: el LLM no resuelve todo. Aporta donde el simbolico no llega.

---

## 2. ARQUITECTURA PROPUESTA (3 capas)

### Capa 1 — Admisibilidad simbolica
Dado un estado, computa el conjunto de acciones legalmente admisibles:

- corregir_rumbo: SIEMPRE admisible.
- ir_a_punto: SIEMPRE admisible.
- frenar: admisible si sog > 0.5 kn.
- terminar: admisible SOLO si dist < 15m.

Salida: lista de acciones admisibles. Deterministico y auditable.

### Capa 2 — Seleccion del LLM
El LLM recibe:
- El estado.
- El objetivo operativo.
- SOLO las acciones admisibles (no todas).
- Ninguna pista de la respuesta esperada.

El LLM elige entre las admisibles. Si la salida es invalida (no JSON,
accion no admisible, parametro fuera de rango), se rechaza.

### Capa 3 — Control y respaldo determinista
- Valida parametros del LLM.
- Si la salida del LLM es invalida o viola restricciones, se deriva
  a la politica Python (timon_python).
- El sistema hibrido NUNCA queda sin accion.

---

## 3. LO QUE NO SE HACE

- NO se le da al LLM el ranking del oraculo.
- NO se prefiltran las acciones por su calidad (eso mediria confirmacion).
- NO se le pasa el top-k del oraculo como opciones.
- NO se le da el parametro optimo.

El LLM debe elegir entre TODAS las admisibles, no entre las mejores.

---

## 4. COMO MEDIR LA CONTRIBUCION DEL LLM

Tres condiciones sobre los mismos escenarios:

| Condicion | Que mide |
|---|---|
| Piloto Python solo | Control determinista puro |
| Simbolico sin LLM (solo admisibilidad + regla simple) | Cuanto resuelven las restricciones |
| Hibrido (simbolico + LLM) | Cuanto agrega el LLM |

Metrica principal: exito de mision o regret vs oraculo.
Metricas secundarias: validez de salida, uso de las 4 acciones, calidad del parametro.

Criterios de exito:
- **Fuerte:** el hibrido supera al simbolico solo Y al Python solo.
- **Debil:** el hibrido empata con el simbolico (el LLM no aporta ni resta).
- **Negativo:** el hibrido empeora respecto al simbolico.

Todos los resultados son informativos. El negativo es especialmente valioso.

---

## 5. COMPONENTES A IMPLEMENTAR

Archivos nuevos en timonel/:
- admisibilidad.py: capa 1, funciones puras deterministicas.
- hibrido.py: orquesta las 3 capas.
- runner_hibrido.py: corre las 3 condiciones sobre el banco de desarrollo.

Archivos a reusar:
- agente_llm.py (con dispatch por modelo).
- simulador_polaris.py.
- oraculo.py (para calcular regret).
- banco_cc002/.
- variantes_prompt.py (adaptar para el prompt hibrido).

---

## 6. DISENO DEL PROMPT HIBRIDO

Estructura:
1. PROPOSITO: llegar a la meta de forma segura.
2. ESTADO actual.
3. ACCIONES ADMISIBLES EN ESTE ESTADO (dado por capa 1).
4. Pedido de JSON.

Sin reglas estado->accion. Sin ejemplos resueltos (evitar colapso).
Sin lista de las 4 acciones si alguna no es admisible (eso es clave).

El LLM SOLO ve las admisibles. Si dist >= 15m, NO ve "terminar".

---

## 7. LO QUE ESPERAMOS VER

Hipotesis del diseno:
- El colapso de accion se REDUCE al filtrar admisibles.
- El LLM empieza a usar al menos 2-3 de las 4 acciones cuando las ve solas.
- La contribucion medible aparece donde el simbolico solo no alcanza:
  eleccion entre acciones ambas admisibles pero de distinta calidad.

Si el colapso persiste aun con admisibilidad filtrada, entonces el problema
es mas profundo de lo que el diseno puede arreglar.

---

## 8. ORDEN DE IMPLEMENTACION

1. Implementar admisibilidad.py (pura, testeable).
2. Tests unitarios de admisibilidad (todos los bordes: dist=14.9, 15.0, 15.1;
   sog=0.4, 0.5, 0.6).
3. Adaptar el prompt para el modo hibrido.
4. Implementar hibrido.py con las 3 capas.
5. Implementar runner_hibrido.py.
6. Correr sobre 20 contextos de desarrollo (mismos que memo 77 para comparar).
7. Documentar resultados y comparar con la fase de prompting.

---

## 9. LO QUE NO SE IMPLEMENTA TODAVIA

- Fine-tuning. Va despues, condicionado.
- DPO. Idem.
- Cambios al banco CC002.
- Uso del split confirmatorio.

---

## 10. FIRMA

**Estado:** PROPUESTA.
**Proximo paso:** implementar admisibilidad.py.
**Referencia:** respuesta de Luna 2026-10-11 (arquitectura hibrida).
