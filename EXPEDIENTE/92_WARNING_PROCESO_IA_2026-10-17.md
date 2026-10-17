# WARNING PREVENTIVO DE PROCESO MULTI-IA — SESIÓN 2026-10-16/17

**Fecha de registro prevista:** 2026-10-17
**Alcance:** fiabilidad del proceso de asistencia técnica y gobernanza de cambios en NAVEGO/LOGOS.
**Estado:** borrador pendiente de revisión y aprobación del Director.

## 1. Incidente

Durante la sesión técnica del 16 y 17 de octubre de 2026 se acumularon diagnósticos, propuestas y tareas de verificación que no mantuvieron una separación suficientemente rigurosa entre hechos demostrados, hipótesis y acciones realmente ejecutadas.

El Director informó un coste aproximado de catorce horas de trabajo en una jornada especialmente improductiva. Este impacto requiere controles preventivos; no se resuelve mediante una asignación genérica de culpas.

## 2. Riesgos metodológicos identificados

### 2.1. Especulación causal
Se discutieron posibles causas relacionadas con SQLite, la selección de sesiones y `TASK_TEST` sin que quedara establecida una cadena causal concluyente. Los fallos históricos justifican una investigación, pero no identifican por sí solos la causa raíz. Los errores deben mantenerse abiertos hasta que exista evidencia suficiente.

### 2.2. Confusión entre commit, código fuente y aplicación instalada
La inspección de `2de55c8` confirmó que ese commit modifica únicamente `App.tsx` para retirar el botón de testeo. No demuestra una compilación o instalación posterior. En futuras auditorías deben distinguirse expresamente: el código en el repositorio, los cambios locales, la compilación efectivamente ejecutada, el APK instalado y el comportamiento observado.

### 2.3. Secuencias de cambios sin verificación suficientemente trazable
Se discutieron modificaciones relacionadas con la presentación, los tiempos de espera de SQLite y la selección de sesiones. La cronología debe distinguir, para cada una, si fue propuesta, incorporada al árbol de trabajo, probada, compilada e instalada. No se debe asumir que una propuesta fue ejecutada sin verificarlo.

### 2.4. Operaciones y archivos no comprobados previamente
Se propusieron pasos que dependían de rutas y archivos cuya presencia local no se había verificado. También se recomendó eliminar un archivo sin seguimiento antes de inspeccionar su contenido (ej. `eNaveGoTracker.ts`, que contenía ayuda del visor `less`). La lección preventiva es inspeccionar y preservar primero, y decidir después.

### 2.5. Pérdida de contexto y repetición improductiva
Se repitieron comprobaciones y se generaron pasos adicionales sin mantener siempre un registro claro de lo que ya había sido comprobado. El proceso debe preservar el estado conocido.

## 3. Salvaguardas propuestas (Pendientes de aprobación del Director)

*Las siguientes reglas se proponen como mejoras preventivas, pero no entran en vigor hasta que el Director las apruebe explícitamente.*

1. **Clasificar la evidencia:** Distinguir observación directa, hecho confirmado por Git, hecho confirmado por logs, hipótesis y dato no verificado.
2. **Etiquetado en chat (Propuesta):** Prefijar afirmaciones en el chat con `[HECHO]`, `[HIPÓTESIS]` y `[PREGUNTA]`.
3. **No afirmar causas sin correlación:** Establecer relación temporal, versión instalada y evidencia técnica antes de atribuir un fallo.
4. **Trabajo incremental:** Una modificación funcional por vez, con estado previo, evidencia posterior y recuperación definida.
5. **Cortacircuitos de improvisación (Propuesta):** Si una depuración requiere modificar más de un archivo o acumula 3 compilaciones fallidas, la IA debe detenerse y pedir autorización al Director.
6. **Proteger el estado funcional:** No interrumpir grabaciones, reiniciar servicios, manipular bases de datos activas ni compilar durante una prueba sin autorización y un plan verificable.
7. **Inspeccionar antes de borrar:** Todo archivo sin seguimiento debe identificarse antes de decidir su destino.
8. **Verificar rutas:** No afirmar que un archivo fue creado hasta comprobar su existencia real.
9. **Evitar repeticiones:** Mantener un registro de comprobaciones y resultados.
10. **Separar documentación y código:** Los commits documentales deben incluir exclusivamente documentos revisados.
11. **Revisión independiente:** La segunda IA critica afirmaciones. No sustituye la evidencia.

## 4. Regla de gobernanza

Se conserva el principio: **La IA propone; la revisión técnica cuestiona; Iván decide.**

## 5. Estado de cierre

Este warning es un borrador preventivo. No constituye por sí mismo un registro oficial en LOGOS.
