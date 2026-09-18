# Ensayo 07 — Error inducido + recuperación
**Fecha:** 18 sep 2026
**Estado:** VERIFICADO

## Hipótesis
DSH puede identificar la causa raíz de un error cuya fuente
no es el código sino los datos, y corregir el lugar correcto.

## Setup
- servidor.py: código correcto (pass-through del config)
- servidor_config.json: "timeout": "30" (string en lugar de int)
- test_servidor.py: valida que timeout sea int

## Tarea dada
"Hacer que los tests pasen. Investigá la causa raíz."

## Resultado
- Ejecutó el test, observó AssertionError de tipo
- Leyó servidor.py Y servidor_config.json
- Detectó que era problema de DATOS, no de código
- Notó la inconsistencia interna (puerto int, timeout str)
- Corrigió SOLO el dato: "30" → 30
- NO tocó código ni test
- Argumentó por qué: coercionar ocultaría config inválido

## Verificación
- git diff: solo 1 carácter en servidor_config.json
- git diff -- servidor.py: vacío
- git diff -- test_servidor.py: vacío
- Todos los tests anteriores siguen pasando (no regresión)

## Capacidad demostrada
Diagnóstico de causa raíz + criterio de diseño + no regresión.

## Próximo
Ensayo 08: control de alcance adversarial.
