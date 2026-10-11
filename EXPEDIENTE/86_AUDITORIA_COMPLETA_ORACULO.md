# AUDITORIA DEL ORACULO — Hallazgo completo con verificacion

**Fecha:** 2026-10-11
**Autor:** Directora de Investigacion + Director
**Estado:** CONFIRMADO. 3 chequeos de verificacion pasados.
**Complementa:** memos 83, 84, 85.

---

## NOTA DE NOMENCLATURA (2026-10-11)

El sistema que este memo llama "oráculo" fue renombrado a **"Entrenador"**
el 2026-10-11 (commit 6e2f6eb).

Razón: "oráculo" no refleja la función real. El sistema da el ejemplo
correcto para que el modelo aprenda, como un entrenador que prepara al
agente en cada fase del aprendizaje.

- Archivo: `oraculo.py` -> `entrenador.py`
- Clase: `Oracle` -> `Entrenador`
- Compatibilidad: shim `oraculo.py` que reexporta todo.

**A partir de este memo, se usa "Entrenador". Los memos anteriores
mantienen "oráculo" como registro histórico.**

---


---

## 0. Proposito

Documentar el hallazgo completo de la auditoria del Entrenador, con los
3 chequeos de verificacion que confirman que los cambios son reales,
estables y no dependen del viento.

---

## 1. HALLAZGO PRINCIPAL

El Entrenador con horizonte de 45s (diseño original del memo 61) produce
etiquetas INCORRECTAS para el banco CC002, especificamente en:

- corregir_rumbo: 67% mal etiquetado (50/75).
- frenar: 100% mal etiquetado (75/75).

Las otras dos clases (ir_a_punto, terminar) estan OK.

---

## 2. COMO SE DESCUBRIO

1. El SFT (memo 83) mostro 65% accuracy, con corregir_rumbo al 13%.
2. El Director noto que el radio de giro puede alejar al barco.
3. Se simulo el barco 60s con cada accion (test_radio_giro.py).
4. 4 de 9 casos favorables a ir_a_punto.
5. Se extendio el horizonte y se confirmo el patron.

---

## 3. TEST DE CONVERGENCIA (240s)

Horizontes crecientes sobre los 75 casos corregir_rumbo:

| Horizonte | ir_a_punto gana | corregir_rumbo gana |
|-----------|----------------|---------------------|
| 45s       | 0              | 75                  |
| 60s       | 6              | 69                  |
| 90s       | 29             | 46                  |
| 120s      | 39             | 36                  |
| 180s      | 48             | 27                  |
| 240s      | 50             | 25                  |
| 360s      | 50             | 25                  |

Cambios entre configs:
- 180s -> 240s: 2
- 240s -> 360s: 0 (CONVERGENCIA)

El Entrenador se estabiliza a los 240s.

---

## 4. AUDITORIA COMPLETA DEL BANCO

Corrida sobre los 300 contextos del split desarrollo:

| Clase original | Cambios a 240s | % error |
|---------------|---------------|---------|
| corregir_rumbo | 50/75        | 67%     |
| ir_a_punto     | 0/75         | 0%      |
| frenar         | 75/75        | 100%    |
| terminar       | 0/75         | 0%      |

Distribucion final con 240s:
- Etiqueta original: corregir_rumbo=75, ir_a_punto=75, frenar=75, terminar=75
- Ganadora 240s: ir_a_punto=200, corregir_rumbo=25, terminar=75, frenar=0

Frenar DESAPARECE como accion optima.

---

## 5. ANALISIS DEL PATRON

Comparacion de los 50 casos que cambian vs los 25 que no:

| Variable | Cambian (oraculo mal) | No cambian (oraculo OK) |
|----------|----------------------|------------------------|
| Distancia media | 143.47m | 25.19m |
| Desvio medio | 100.06 grados | 33.99 grados |

Tabla cruzada (distancia x desvio):

CASOS QUE CAMBIAN:
| DIST \ DESV | 0-30 | 30-45 | 45-60 | 60-90 | 90-180 |
|-------------|------|-------|-------|-------|--------|
| 0-20        | 0    | 1     | 0     | 0     | 0      |
| 20-50       | 0    | 0     | 1     | 0     | 0      |
| 50-100      | 0    | 0     | 1     | 2     | 9      |
| 100-150     | 0    | 0     | 0     | 4     | 8      |
| 150-300     | 0    | 0     | 2     | 10    | 12     |

CASOS QUE NO CAMBIAN:
| DIST \ DESV | 0-30 | 30-45 | 45-60 | 60-90 | 90-180 |
|-------------|------|-------|-------|-------|--------|
| 0-20        | 11   | 3     | 4     | 1     | 0      |
| 20-50       | 1    | 4     | 0     | 0     | 0      |
| 50-100      | 0    | 0     | 0     | 0     | 0      |
| 100-150     | 0    | 0     | 0     | 0     | 0      |
| 150-300     | 0    | 0     | 0     | 0     | 1      |

PATRON: el Entrenador se equivoca cuando el barco esta LEJOS y MUY DESVIADO.

---

## 6. INTERPRETACION FISICA

Hipotesis del Director (confirmada):

> El velero tiene radio de giro. Cuando esta lejos de la meta y muy
> desviado, corregir_rumbo implica girar "en el lugar" (sin avanzar)
> mientras ir_a_punto gira Y avanza al mismo tiempo.

A 45s, el Entrenador ve que corregir_rumbo esta orientando el barco hacia
la meta y cree que es mejor. A 240s, se ve que el barco no avanzo
(distancia recorrida), mientras ir_a_punto si llego mas cerca.

En resumen: el Entrenador miope NO VE el costo del "giro en el lugar"
porque no espera suficiente tiempo.

---

## 7. VERIFICACION — 3 CHEQUEOS

### Chequeo 1 — Margenes reales o empates?
Corrida sobre los 50 casos que cambian. Mide margen entre 1ra y 2da.

Resultado:
- Empate tecnico (< 1m): 1/50 (2%)
- Cambio debil (1-5m): 2/50 (4%)
- Cambio real (>= 5m): 47/50 (94%)
- Margen mediano: 45.24m
- Margen maximo: 127.47m

Conclusion: los cambios son REALES, no empates tecnicos.

### Chequeo 2 — 240s es estable?
Corrida con horizontes 180s, 200s, 220s, 240s, 260s, 280s, 300s, 360s.

Resultado:
- Cambios entre 240s y 360s: 0
- Casos con mismo ganador en TODOS los horizontes >= 180s: 48/50
- Los 2 casos que varian: CC002-002124, CC002-000806

Conclusion: 240s es ESTABLE. Podemos usarlo.

### Chequeo 3 — El viento afecta?
Corrida de los 50 casos con viento=0 vs viento original del contexto.

Resultado:
- Cambios por viento: 0/50
- Casos borderline evaluados: sin cambio con/sin viento

Conclusion: el viento NO afecta la decision en estos casos.

---

## 8. CONSECUENCIAS

### Sobre el banco CC002
- 50/300 (17%) de las etiquetas estan mal SOLO contando corregir_rumbo.
- 75/300 (25%) estan mal SUMANDO frenar.
- El banco necesita re-etiquetarse con horizonte 240s.

### Sobre el LLM
- El modelo SFT fue entrenado con etiquetas parcialmente incorrectas.
- Su accuracy real (contra etiquetas correctas) probablemente sea mayor al 65%.
- Los "fallos" en corregir_rumbo eran en realidad aciertos.

### Sobre el frenar
- La accion frenar nunca es optima a 240s.
- El problema no es de horizonte sino de funcion de utilidad.
- Hay que decidir: eliminar frenar, o cambiar la metrica del Entrenador.

### Sobre el proyecto
- La regla nueva (auditar antes de entrenar) queda confirmada.
- El Entrenador necesita reforma: horizonte 240s + funcion de utilidad revisada.

---

## 9. PROXIMOS PASOS

1. Consultar a Luna y Claude con estos datos.
2. Decidir que hacer con frenar (eliminar o reformular).
3. Reformar el Entrenador con horizonte 240s.
4. Re-etiquetar el banco CC002 completo (600 contextos).
5. Re-entrenar el SFT con etiquetas correctas.
6. Re-evaluar.

---

## 10. ARTEFACTOS

Tests en timonel/:
- test_radio_giro.py
- test_oraculo_300.py
- test_horizonte_extendido.py
- test_horizonte_sensibilidad.py
- test_convergencia.py
- auditoria_completa_banco.py
- analisis_radio_giro.py
- chequeo1_margenes.py
- chequeo2_estabilidad.py
- chequeo3_viento.py

Resultados JSON:
- test_oraculo_300.json
- test_horizonte_extendido.json
- test_horizonte_sensibilidad.json
- test_convergencia.json
- auditoria_completa_banco.json
- analisis_radio_giro.json
- chequeo1_margenes.json
- chequeo2_estabilidad.json
- chequeo3_viento.json

---

## 11. FIRMA

**Estado:** CONFIRMADO.
**Proximo paso:** consultar a Luna + Claude con este memo.
**Regla nueva:** auditar el Entrenador antes de cualquier entrenamiento.
