# CIERRE DE FASE — Prototipo hibrido

**Fecha:** 2026-10-11
**Autor:** Directora de Investigacion
**Estado:** CERRADO. Prototipo hibrido con resultado negativo.
**Complementa:** memos 79, 80.

---

## 0. Proposito

Documentar el cierre de la fase de arquitectura hibrida con el resultado
observado.

---

## 1. LO QUE SE IMPLEMENTO

- admisibilidad.py (capa 1): filtro deterministico de acciones admisibles.
- prompt_hibrido.py: prompt que solo muestra las admisibles.
- hibrido.py: orquesta las 3 capas.
- 16/16 tests unitarios OK.

---

## 2. LO QUE SE ESPERABA

Hipotesis de Luna (memo 80): el filtro de admisibles reduce el espacio de
decision y rompe el colapso de accion. El LLM empezaria a usar al menos
2-3 de las 4 acciones.

---

## 3. LO QUE SE OBSERVO

Caso control (navegando alineado, desvio=0.0 grados, deberia ser ir_a_punto):
- Admisibles: corregir_rumbo, ir_a_punto, frenar.
- Respuesta del LLM: corregir_rumbo 45.0.
- El barco esta mirando exactamente a la meta. El LLM eligio girar 45 grados.

Casos adicionales:
- Navegando desalineado: corregir_rumbo 45.0 (correcto, pero probablemente por colapso).
- Terminal (dist=7m): corregir_rumbo 45.0 (deberia ser terminar).
- Parado lejos (admisibles reducidas a 2): corregir_rumbo 45.0.

En LOS 4 CASOS el LLM devolvio la misma accion y el mismo parametro.

---

## 4. DIAGNOSTICO

El prompt esta bien formado (verificado).
El system prompt esta bien (verificado).
El parser extrae JSON limpio (verificado).
El filtro de admisibles funciona (verificado).

CONCLUSION: Llama 3.1 8b IGNORA el estado. Colapsa a corregir_rumbo
independientemente del prompt, filtro, system o estado.

La hipotesis de Luna NO se cumple para Llama 3.1 8b.

---

## 5. LO QUE ESTO SIGNIFICA

- El filtro simbolico es correcto pero insuficiente.
- El LLM no procesa el estado aunque se lo demos limpio.
- La arquitectura hibrida con Llama 3.1 8b no aporta valor.
- El colapso es independiente del diseno.

---

## 6. ARTEFACTOS

En timonel/:
- admisibilidad.py
- prompt_hibrido.py
- hibrido.py
- cierre_hibrido.json (evidencia)

En EXPEDIENTE/:
- 80_DISENO_HIBRIDO.md
- 81_CIERRE_HIBRIDO.md (este memo)

---

## 7. PROXIMA CONSULTA A LUNA

Preguntas:
1. Si el LLM ignora el estado incluso con filtro simbolico y prompt limpio,
   que opciones quedan?
2. Es momento de ir a fine-tuning con LoRA + SFT?
3. O hay algun otro modelo que valga la pena probar?
4. O aceptamos que en este dominio el LLM no aporta y el sistema debe ser
   puramente simbolico (Python + reglas)?

---

## 8. FIRMA

**Estado:** CERRADO.
**Proximo paso:** consultar a Luna con esta evidencia.
