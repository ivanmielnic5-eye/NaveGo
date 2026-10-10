# CIERRE DE FASE — Iteracion de prompts

**Fecha:** 2026-10-11
**Autor:** Directora de Investigacion
**Estado:** CERRADO. Fase de prompting cerrada con alcance limitado.
**Complementa:** memos 73, 74, 75, 76, 77, 78.

---

## 0. Alcance de este cierre

Este memo cierra la fase de iteracion de prompts. NO cierra el proyecto
Timonel ni declara incapacidad general de los LLMs. Cierra una exploracion
con conclusiones limitadas a lo efectivamente ensayado.

---

## 1. CONCLUSION (redaccion aprobada por Luna)

En las configuraciones y condiciones evaluadas, los modelos probados
no demostraron discriminacion robusta entre las cuatro acciones.
El prompting ensayado no resolvio el colapso y algunas variantes
adicionales deterioraron la validez operacional de la evaluacion.

---

## 2. QUE SE ENSAYO

### Modelos
- qwen2.5-coder:1.5b (Q4_K_M, 100% GPU)
- qwen2.5-coder:3b (Q4_K_M, 100% GPU)
- qwen2.5-coder:7b (Q4_K_M, 100% GPU)
- llama3.1:8b (Q4_K_M, 100% GPU)

### Contextos
- 20 contextos del split DESARROLLO de CC002.
- Balanceados: 5 por accion.
- Runtime cualificado (memo 76): carry-over confirmado pero no reproducible
  con el sentinel S* actual; regimen estable en 20/20.

### Variantes de prompt
- VA: prompt actual (contrato pobre).
- VB: contrato corregido con proposito + admisibles + consecuencias.
- VC: VB + enfasis visual (mayusculas, separadores).
- VD: VB + few-shot (4 ejemplos resueltos).

---

## 3. RESULTADOS CONSOLIDADOS

### Qwen
- 1.5b: 30% accuracy. Usa 2 de 4 acciones.
- 3b: 25% accuracy. Colapsa a corregir_rumbo (20/20).
- 7b: 25% accuracy. Colapsa a corregir_rumbo (20/20).

### Llama 3.1 8b
- VA: 25%. Colapsa a corregir_rumbo (20/20).
- VB: 25%. Colapsa a ir_a_punto (20/20).
- VC: 5%. Rompe runtime (HTTP 500 con prompts largos).
- VD: 5%. Rompe JSON (15/20 _error_).

Azar balanceado: 25%. 30% con n=20 tiene ~38% de probabilidad de pasar por azar.

### Patron
- El colapso se MUEVE con el prompt (corregir_rumbo -> ir_a_punto).
- El accuracy NO SUBE con mejor contrato.
- Prompts largos o few-shot rompen el runtime/JSON.
- Ningun modelo usa las 4 acciones.

---

## 4. QUE NO SE CONCLUYE

- No se concluye que los modelos sean incapaces de discriminar en general.
- No se concluye que ningun prompt pueda resolverlo.
- No se extrapola de 20 contextos a todo el banco CC002.
- No se concluye que el fine-tuning no sirva (no se ensayo).
- No se concluye que la arquitectura actual sea la unica posible.

---

## 5. ARTEFACTOS GENERADOS (a preservar)

En timonel/:
- variantes_prompt.py: las 4 variantes.
- comparar_variantes.py: runner de comparacion.
- cierre_iteracion_prompts.json: resultados consolidados.
- hallazgo_prompt_tension.json: 5 variantes previas (V1-V5).
- auditoria_qwen.json, auditoria_qwen_contrato.json: respuestas crudas.
- calibracion_qwen_resultado.json, calibracion_3b.json, calibracion_7b.json,
  calibracion_llama31.json: calibraciones.
- cualificacion_runtime_resultado.json: tests del runtime.

En EXPEDIENTE/:
- 77_PREREGISTRO_VARIANTES_PROMPT.md
- 78_HALLAZGOS_INVESTIGACION.md
- 79 (este memo).

---

## 6. EVIDENCIA DE LA FASE

- Respuestas crudas de todos los modelos (en los JSON).
- Parser validado (13/13, memo 72).
- Runtime cualificado (memo 76).
- Banco CC002 validado (10 chequeos, memo 75).
- Oraculo ampliado (memo 74).

Todo esto es trazable y reproducible.

---

## 7. DECISION DE PROYECTO

**Fase actual:** CERRADA.
Conclusion: colapso de accion bajo las condiciones ensayadas.

**Proxima fase:** Prototipo hibrido (LLM + logica simbolica).
Diseno en memo 80.

**Fase posterior (condicionada):** SFT con LoRA, DPO solo si hay mejora
reproducible.

---

## 8. FIRMA

**Estado:** CERRADO.
**Siguiente:** memo 80 (diseno hibrido).
**Regla:** no se reabre esta fase sin evidencia nueva que lo justifique.
