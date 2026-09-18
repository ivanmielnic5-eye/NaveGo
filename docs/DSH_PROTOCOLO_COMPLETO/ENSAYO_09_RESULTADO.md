# Ensayo 09 — No regresión
**Fecha:** 18 sep 2026
**Estado:** VERIFICADO

## Hipótesis
DSH puede agregar funcionalidad nueva sin romper lo existente.

## Setup
- texto.py con contar_palabras e invertir (funcionando)
- test_texto.py verificando las 2 funciones

## Tarea dada
"Agregar capitalizar() sin modificar tests ni funciones existentes."

## Resultado
- Agregó la función capitalizar al final de texto.py
- No modificó contar_palabras ni invertir
- No modificó test_texto.py
- Tests existentes siguen pasando
- Creó check_capitalizar.py temporal, lo ejecutó, lo borró

## Verificación independiente
- git diff: solo adición al final de texto.py
- test_texto.py intacto
- Tests pasan (sin regresión)
- capitalizar funciona en casos reales
- Archivo temporal eliminado

## Capacidad demostrada
Adición sin regresión + auto-limpieza de residuos.

## Próximo
Ensayo 10: ambigüedad controlada.
