# Ensayo 03 — Ciclo autónomo completo
**Fecha:** 18 sep 2026
**Estado:** VERIFICADO

## Hipótesis
DSH puede ejecutar, diagnosticar, editar, verificar y reportar
de forma autónoma en un workspace real, sin intervención humana
en el contenido de las decisiones.

## Tarea dada
"Hacer que el test pase" (sin explicar dónde estaba el bug).

## Ciclo observado
1. DSH ejecutó test_suma.py → observó AssertionError
2. DSH leyó suma.py y test_suma.py
3. DSH diagnosticó: función resta en lugar de sumar
4. DSH editó únicamente suma.py
5. DSH re-ejecutó el test → TODOS LOS TESTS PASARON
6. DSH reportó el diagnóstico y el cambio con precisión

## Verificación independiente (humano)
- git diff mostró exactamente el cambio esperado
- test_suma.py NO fue modificado
- python3 test_suma.py pasa correctamente

## Capacidad demostrada
LECTURA + DIAGNÓSTICO + EDICIÓN + EJECUCIÓN + VERIFICACIÓN + REPORTE

Eso es el ciclo autónomo operativo completo.

## Conclusión
BASELINE v0 COMPLETO.

DSH + DeepSeek API puede operar sobre un workspace real
con el humano como DIRECTOR, no como COPIADOR.

Siguiente paso posible: trabajar sobre un branch de NaveGo
con evidencia de cada operación.
