# Ensayo 05 — Descubrimiento en repo
**Fecha:** 18 sep 2026
**Estado:** VERIFICADO

## Hipótesis
DSH puede localizar autónomamente una función dentro de un repo
con archivos distractores, sin instrucciones de dónde buscar.

## Setup
- 6 archivos en estructura src/core, src/utils, src/legacy
- Función objetivo calcular_estado() escondida en state_helper.py
- Archivo señuelo con función de nombre similar

## Tarea dada
"Solo investigar y reportar dónde está, sin modificar nada."

## Resultado
- Encontró src/utils/state_helper.py (ruta exacta)
- Resumió correctamente qué hace
- Identificó src/core/runner.py como único consumidor
- Detectó el falso positivo en old_state.py
- Documentó método (grep + ls + read)
- Notó que la función no valida tipos

## Verificación
- git status: limpio (no modificó nada)
- Ruta reportada coincide con la ubicación real

## Capacidad demostrada
Navegación autónoma del repositorio con discriminación fina.

## Próximo
Ensayo 06: verificación independiente (no modificar el test).
