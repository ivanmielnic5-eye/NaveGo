# HITO FUNCIONAL OBSERVADO — NAVEGO (2026-10-17)

**Fecha de observación:** 2026-10-17
**Fuente principal:** observaciones funcionales informadas por el Director
**Estado:** hito funcional observado; no implica cierre de la auditoría técnica.

## 1. Comportamiento observado

Durante las pruebas realizadas el 17 de octubre de 2026, el Director informó los siguientes resultados:

- La ubicación GNSS volvió a enganchar correctamente.
- El track rojo volvió a mostrarse en el mapa.
- La distancia acumulada funcionó.
- Los valores COG y SOG se actualizaron.
- Funcionaron el guardado de referencias y su selección y reutilización.
- La operación con trayectos y referencias guardadas funcionó.
- La interfaz en portrait quedó limpia, sin el botón de testeo.
- La interfaz en landscape funcionó, aunque falta recuperar el seguimiento de curva disponible anteriormente.

La aplicación continuó funcionando al pasar a segundo plano sin perder el track ni la distancia acumulada, según la prueba informada por el Director.

## 2. Límites y asuntos pendientes

El comportamiento observado no demuestra que la captura de waypoints continúe correctamente con la pantalla apagada. También permanece pendiente investigar la pérdida de referencia que puede impedir integrar correctamente un tramo de la trayectoria.

Quedan pendientes, además:
- Incorporar el tratamiento visual del GNSS degradado mediante los colores negro y amarillo del track.
- Recuperar el seguimiento de curva en landscape.
- Investigar los fallos históricos de SQLite y el ciclo de vida de sus conexiones.
- Revisar otros defectos menores que todavía no fueron inventariados.

## 3. Evidencia y causalidad

El commit `2de55c8f998417d97f6330fa57e67811a3466771`, fechado el 16 de octubre de 2026, elimina seis líneas de `App.tsx` relacionadas con el botón `EXPORT DB (TEST)`.

El historial inspeccionado no demuestra que se haya compilado e instalado una aplicación a partir de ese commit. Por tanto, no se atribuye a ese cambio, ni a una limpieza de base de datos, la recuperación funcional observada.

El código fuente actualmente inspeccionado contiene cambios locales en `tasks/backgroundLocationTask.ts` y declara `BACKGROUND_TEST_ENABLED = false` en `devConfig.ts`. Estos datos describen el árbol de trabajo, pero no identifican por sí solos el código exacto de la aplicación instalada durante la prueba.

Los registros históricos de fallos nativos y los problemas de SQLite siguen pendientes de investigación forense. Este hito no demuestra que el pipeline completo esté libre de defectos.

## 4. Conclusión

Se registra un avance funcional significativo: GNSS, track, distancia, COG/SOG y operaciones con referencias guardadas funcionaron durante las pruebas informadas.

Este resultado debe preservarse como una línea base funcional positiva. No constituye una declaración de cierre de los problemas de segundo plano, continuidad de trayectoria, SQLite ni ciclo de vida de las conexiones.
