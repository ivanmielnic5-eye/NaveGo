# PREREGISTRO — Piloto SFT + LoRA

**Fecha:** 2026-10-11
**Autor:** Directora de Investigacion
**Estado:** CONGELADO antes de ejecutar. Condiciones de exito y abandono fijadas.
**Complementa:** memos 79, 80, 81.

---

## 0. Proposito

Determinar si Llama 3.1 8B puede aprender a discriminar acciones del oraculo
mediante fine-tuning supervisado (SFT + LoRA), y si esa mejora generaliza a
estados no vistos durante el entrenamiento.

---

## 1. HIPOTESIS

H-SFT-1: un modelo entrenado con SFT sobre contextos del oraculo aprende a
seleccionar acciones dependientes del estado, reduciendo el colapso de accion
observado en zero-shot.

H-SFT-0 (nula): el modelo no mejora o solo memoriza los ejemplos de entrenamiento.

---

## 2. DISENO

### Modelo base
- llama3.1:8b (Q4_K_M en inferencia, se reentrena desde el modelo completo).
- Se usara el modelo Instruct oficial.

### Dataset
- 240 contextos del split DESARROLLO de CC002 para entrenamiento.
- 60 contextos del split DESARROLLO de CC002 para validacion.
- 300 contextos del split CONFIRMATORIO: INTOCADOS durante todo el piloto.

### Formato
Cada ejemplo es un par (prompt, respuesta_esperada):
- Prompt: el prompt hibrido SIN las acciones admisibles (solo estado + proposito).
- Respuesta: JSON con accion_optima y parametro_oraculo.

### Metodo
- QLoRA (cuantizacion 4-bit + LoRA).
- Configuracion conservadora: rank 16, alpha 32, dropout 0.05.
- Maximo 3 epocas exploratorias.
- Seleccion de checkpoint SOLO con validacion.

### Hardware
- Preferido: Kaggle (T4 16GB, $0, 30h/semana).
- Fallback: Vast.ai (RTX 3090 24GB, ~$0.15/hora).

---

## 3. CRITERIO DE EXITO

Se considera exito si, en el split de VALIDACION:
- Accuracy de accion > accuracy zero-shot del modelo base (25%).
- Uso de las 4 acciones (no colapso a 1-2).
- La mejora supera la variabilidad esperable con n=60.

## 4. CRITERIO DE ABANDONO

Se abandona el piloto si:
- El hardware no es viable (no cabe en T4/RTX 3090).
- SFT no mejora sobre el modelo base tras 3 epocas.
- El modelo solo memoriza (accuracy en train alta, validacion baja).

---

## 5. LO QUE NO SE HACE

- No se consulta el split confirmatorio.
- No se pasa a DPO todavia.
- No se cambia de modelo base.
- No se toca el banco CC002 ni el oraculo.

---

## 6. FIRMA

**Estado:** CONGELADO.
**Proximo paso:** preparar el dataset y ejecutar el piloto en Kaggle.
