# AUDITORIA DEL ORACULO — Ground truth parcialmente incorrecto

**Fecha:** 2026-10-11
**Autor:** Directora de Investigacion + Director
**Estado:** HALLAZGO GRAVE. Requiere decision antes de seguir.
**Complementa:** memos 79, 80, 81, 82, 83.

---

## 0. Proposito

Documentar el hallazgo de que el oraculo tiene ~40% de etiquetas
incorrectas en la clase corregir_rumbo.

---

## 1. COMO SE DESCUBRIO

Tras el piloto SFT (memo 83, 65% accuracy), el Director noto que:

> "puede ser porque el radio de giro es grande y se le complica si no
>  llega justo"

Es decir: en distancias cortas con desvio moderado, corregir_rumbo puede
ALEJAR al barco por el radio de giro. La accion fisicamente mejor podria
ser ir_a_punto aunque el oraculo diga corregir_rumbo.

---

## 2. TEST EMPIRICO

Se simulo el barco 60 segundos completos con cada accion, sobre los 75
contextos del split DESARROLLO que el oraculo etiqueto como corregir_rumbo.

Para cada contexto:
- Simular 60s con corregir_rumbo (hacia la meta).
- Simular 60s con ir_a_punto (hacia la meta).
- Comparar distancia final a la meta.

Ganador = accion que llega mas cerca.

---

## 3. RESULTADO

Total: 75 contextos.

- Ganador corregir_rumbo (oraculo OK): 45 (60%)
- Ganador ir_a_punto (MODELO OK):      30 (40%)
- Empates: 0

### Por rango de desvio

| Rango | corregir_rumbo gana | ir_a_punto gana | Tasa error oraculo |
|-------|--------------------|-----------------|--------------------|
| 0-30  | 12                 | 0               | 0%                 |
| 30-45 | 7                  | 1               | 12%                |
| 45-60 | 6                  | 2               | 25%                |
| 60-90 | 8                  | 9               | 53%                |
| 90-180| 12                 | 18              | 60%                |

Conclusion: el error del oraculo CRECE con el desvio.

---

## 4. ANALISIS

### Causa probable
El oraculo simula con horizonte maximo de 45s. En acciones que requieren
giros grandes, 45s no alcanza para ver que el barco termina alejandose.
Ejemplo: en un caso, corregir_rumbo termino a 107m de la meta cuando
empezo a 18m. El oraculo no ve ese desastre.

### Implicancias
1. El banco CC002 tiene ~40% de etiquetas incorrectas en la clase
   corregir_rumbo.
2. El piloto SFT (memo 83) fue entrenado con datos parcialmente erroneos.
3. La accuracy de 65% puede estar SUBESTIMADA: el modelo podria haber
   aprendido mejor la clase, pero las etiquetas incorrectas lo penalizan.

---

## 5. PREGUNTAS ABIERTAS

1. Corregir el oraculo (horizonte 60s, o comparacion especifica
   corregir_rumbo vs ir_a_punto en zona gris).
2. Re-etiquetar el banco con el oraculo corregido.
3. Re-entrenar el modelo con etiquetas correctas.
4. O cambiar la semantica: corregir_rumbo como precondicion de ir_a_punto.

---

## 6. ARTEFACTOS

- test_radio_giro.py: test sobre 9 casos.
- test_oraculo_300.py: test sobre 75 casos.
- test_oraculo_300.json: resultados completos.

---

## 7. FIRMA

**Estado:** HALLAZGO GRAVE.
**Proximo paso:** consultar a Luna y Claude con estos datos.
**Regla nueva:** antes de cualquier entrenamiento futuro, auditar el
oraculo sobre los casos a usar.
