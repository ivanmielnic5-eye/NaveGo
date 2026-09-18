# Ensayo 04 — Multiarchivo
**Fecha:** 18 sep 2026
**Estado:** VERIFICADO

## Hipótesis
DSH puede coordinar cambios en múltiples archivos relacionados
siguiendo dependencias, sin instrucciones explícitas de dónde tocar.

## Tarea dada
Cambiar modo 'desarrollo' → 'produccion' en config.json,
actualizar test_loader.py, NO tocar loader.py.

## Resultado
- config.json modificado correctamente
- test_loader.py actualizado correctamente
- loader.py NO fue tocado (verificado con git diff vacío)
- Test pasa con exit 0

## Verificación independiente
- git diff --name-only: solo config.json y test_loader.py
- git diff -- loader.py: vacío
- python3 test_loader.py: TEST PASA

## Capacidad demostrada
Coordinación multiarchivo con respeto de alcance.

## Próximo
Ensayo 05: descubrimiento dentro del repo.
