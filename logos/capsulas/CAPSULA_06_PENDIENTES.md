# 06 — Pendientes, en orden

## Inmediato (verificar / cerrar Paso 3)
[ ] Confirmar salida Paso 3A: esperado 5/5, tsc limpio.
[ ] Confirmar salida Paso 3B: esperado 3/3, tsc limpio.
[ ] Si OK: rebuild + install.
[ ] Test de replay: comparar distancia, puntos, gaps, SOG/COG vs antes.

## Siguiente (verificación cruzada)
[ ] git diff f70a68b..HEAD  → snapshot del cambio completo.
[ ] Preparar commit con message descriptivo.
[ ] Alimentar a DSH con: diff + commit message + archivos nuevos.
[ ] DSH produce análisis: ¿qué cambió? ¿preserva semántica? ¿riesgos?
[ ] Guardar análisis de DSH en LOGOS como evidencia del proceso.

## Después (Fase 0 del plan de background)
[ ] Diseñar cómo processFix se invoca fuera del hilo de UI.
[ ] Definir contrato de serialización de ProcessState/ProcessResult.
[ ] Endurecer tests unitarios de processFix (casos borde de gap/accuracy).

## Riesgos abiertos
- Semántica de cierre de gap depende de refs mutables en el hook.
  Al mover a processFix hay que verificar que el orden de efectos no cambie.
- Logs de filtrado (ACCURACY, gap restart) ahora dependen de rawDistanceDelta:
  confirmar que el número del log coincide con el de antes del refactor.
