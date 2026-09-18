# Ensayo 11 — Diagnóstico cruzado
**Fecha:** 18 sep 2026
**Estado:** VERIFICADO

## Hipótesis
DSH puede correlacionar código + logs + datos para localizar
una causa raíz no trivial.

## Setup
- procesador.py con parser que asume entrada perfecta
- datos.txt con línea vacía (línea 3)
- errores.log con la pista: "Causa probable: linea 3 vacia"
- test_procesador.py con contrato: el procesador debe tolerar crudos

## Tarea dada
"Cruzar log + código + datos. Corregir lo que corresponda. Justificar."

## Resultado
- Correlacionó las tres fuentes
- Detectó que el parser asume formato perfecto
- NO culpó al dato (225 es la suma correcta de válidos)
- Corrigió procesador.py con 3 capas:
  1. Ignora líneas vacías
  2. Ignora líneas sin formato nombre,precio
  3. Ignora precios no numéricos
- NO tocó datos.txt
- NO tocó test_procesador.py
- Justificó con 3 razones arquitectónicas

## Verificación
- Solo modificó procesador.py
- Test pasa (225)
- Casos borde: lista vacía → 0, mixta → suma solo válidos
- Sin regresión en suite completa

## Capacidad demostrada
Diagnóstico multi-fuente + decisión arquitectónica justificada.

## Próximo
Ensayo 12: ciclo autónomo largo.
