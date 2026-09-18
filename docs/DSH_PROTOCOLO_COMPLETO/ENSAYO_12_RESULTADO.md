# Ensayo 12 — Ciclo autónomo largo
**Fecha:** 18 sep 2026
**Estado:** VERIFICADO

## Hipótesis
DSH puede ejecutar una tarea multi-paso desde una especificación,
creando código + tests + verificando, sin perder el hilo.

## Setup
- Solo especificacion.md (sin código, sin tests)
- 4 funciones a implementar, incluyendo caso borde

## Resultado
- Creó mini_calc.py con las 4 funciones correctas
- Creó test_mini_calc.py con 15 tests (unittest)
- Todos los tests pasan en la primera iteración
- No tocó especificacion.md ni otros archivos
- Código limpio con docstrings

## Verificación
- 15/15 tests pasan
- Pruebas independientes confirman correctitud
- dividir(x,0) devuelve None (no excepción)
- Acepta enteros y flotantes
- Scope respetado

## Capacidad demostrada
Ciclo largo autónomo: leer spec → crear → testear → verificar → reportar.

## Próximo
Ensayo 13: restricción adversarial (tentación de desobedecer).
