# RESULTADO DEL PILOTO SFT — Exito en validacion

**Fecha:** 2026-10-11
**Autor:** Directora de Investigacion
**Estado:** PILOTO EXITOSO. Cumple criterio de exito del memo 82.
**Complementa:** memos 79, 80, 81, 82.

---

## 0. Proposito

Documentar el resultado del piloto SFT+LoRA sobre Llama 3.1 8B.

---

## 1. SETUP DEL PILOTO

- Modelo base: Meta-Llama-3.1-8B-Instruct (4-bit).
- Metodo: QLoRA con LoRA rank 16, alpha 32, dropout 0.05.
- Dataset: 240 train + 60 val desde banco CC002 desarrollo.
- Entrenamiento: 6 epochs, 180 steps, batch 8 efectivo.
- Hardware: Kaggle GPU T4 (gratis).
- Duracion: ~35 minutos.

---

## 2. RESULTADO EN VALIDACION (n=60)

=== RESULTADO VALIDACION ===
Accuracy: 39/60 = 65.0%
Uso de acciones: {frenar: 16, terminar: 15, ir_a_punto: 22, corregir_rumbo: 7}

Por accion (aciertos/total):
- frenar:         11/15 = 73.3%
- terminar:       15/15 = 100.0%
- ir_a_punto:     11/15 = 73.3%
- corregir_rumbo:  2/15 = 13.3%

---

## 3. COMPARACION CON BASELINE ZERO-SHOT

| Metrica | Zero-shot (memo 79) | SFT+LoRA (ahora) | Mejora |
|---|---|---|---|
| Accuracy | 25% | 65% | +40 pp |
| Acciones usadas | 1 | 4 | +3 |
| Colapso | SI | NO | resuelto |

---

## 4. CRITERIO DE EXITO (memo 82)

- Accuracy > 25% (baseline): CUMPLIDO (65%).
- Uso de las 4 acciones: CUMPLIDO.
- Mejora supera variabilidad: 40 pp sobre 25% es enorme.

CONCLUSION: el piloto SFT es EXITOSO.

---

## 5. OBSERVACIONES

- terminar: 100%. El modelo aprendio perfectamente la senal "dist<15m".
- frenar e ir_a_punto: 73% cada uno. Solidos.
- corregir_rumbo: 13%. Debil.

Hipotesis sobre corregir_rumbo:
- Es la unica accion que requiere un parametro (angulo).
- El modelo puede estar eligiendo bien el momento pero errando el angulo.
- Falta analisis detallado de los 13 casos fallidos.

---

## 6. ARTEFACTOS

- Notebook: timonel_sft_kaggle.ipynb (en Kaggle).
- Adaptador LoRA: timonel_lora/ (~170 MB).
- Dataset: sft_dataset/ (train.jsonl, val.jsonl).

---

## 7. PROXIMOS PASOS

1. Analizar los 13 casos fallidos de corregir_rumbo.
2. Correr el modelo sobre el split CONFIRMATORIO (300 contextos intactos).
3. Comparar contra baseline Python y oraculo.
4. Documentar.

---

## 8. FIRMA

**Estado:** PILOTO EXITOSO.
**Proximo paso:** evaluacion confirmatoria.
