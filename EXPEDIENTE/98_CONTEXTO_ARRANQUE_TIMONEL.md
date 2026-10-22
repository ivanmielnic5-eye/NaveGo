# 98 — Contexto de arranque para Timonel

**Fecha de corte:** 2026-10-22
**Naturaleza:** documento de orientación y continuidad. No sustituye expedientes, decisiones ni fuentes de código.

## 0. Propósito

Este documento es la puerta de entrada para un hilo nuevo que vaya a investigar o trabajar sobre Timonel.

Debe leerse primero. Después se consultan los expedientes y las fuentes que referencia. Su función es reducir la pérdida de contexto y evitar repetir investigaciones ya documentadas.

No autoriza cambios, experimentos ni commits. Las propuestas requieren aprobación expresa del Director.

## 1. Identidad y estado al corte

- Rama de trabajo informada: `v2-track-honesto`.
- HEAD informado al corte: `b9cc6fc`.
- Gate informado: READY.
- Discrepancia del Gate: se informó una diferencia entre seis checks mostrados en texto y siete en JSON; falta corregir la etiqueta `Trust` en la salida textual.
- Expediente 95: corregido y verificado, 119 líneas, hash informado `a12844355bd4a044`. Backup: `.pre-correccion-95`.
- Expediente 96: escrito, hash informado `f66b44148258290d`.
- Los expedientes 95 y 96 no estaban incorporados al seguimiento de Git en la última comprobación.
- No se había hecho commit ni push de esas correcciones.
- No existe aún el expediente 98 al momento de preparar este documento.

Estos son datos del corte informado, no una garantía del estado futuro del repositorio.

## 2. Responsabilidades de Timonel

- `timonel.py`: ciclo principal; `INTERVALO_S = 3.0`.
- `timon_python()` dentro de `timonel.py`: control determinista.
- `timonel_python.py`: agente de alto nivel basado en LLM, según el inventario existente.
- `controlador_pid.py`: controlador `PIDRumbo`.
- `acciones.py`: cuatro acciones de alto nivel; las acciones de rumbo y navegación emplean el PID.
- `recetas_navegacion.py`: cuatro recetas con lógica discreta propia.
- `entrenador_v2.py`: evalúa acciones sobre horizontes temporales comunes.
- `acciones.py` y `recetas_navegacion.py` son capas distintas. El entrenador v2 consume las acciones de `acciones.py`, no las recetas.
- DSH es infraestructura transversal para agentes aislados; no debe confundirse con el decisor de navegación.

## 3. Simuladores y límites de transferencia

**Python — `simulador_polaris.py`**

- Se documentaron 168 puntos de flotación derivados de `hull_mesh.json` en el commit `31e0e1a`.
- Se informó una masa de 8000 y centro de masa `(0, -1.2, 0)` para ese modelo.
- El arrastre es lineal.
- La efectividad del timón depende de factores dinámicos del modelo.

**Godot — Polaris**

- `timonel_bridge.gd` aplica el torque nominal 2500 mientras la orden está activa, con inversión de signo.
- El modelo de arrastre es cuadrático.
- Se informó una frecuencia efectiva de 48,54 Hz en una ejecución headless concreta; no debe tratarse como frecuencia universal.
- La cantidad de puntos de flotación de Godot no se afirma aquí hasta verificar una fuente específica.

**Regla de transferencia:** Python y Godot son modelos diferentes. Ningún resultado debe trasladarse automáticamente de uno al otro ni a una embarcación real.

En los modelos examinados, `timon=0` deja de aplicar torque, aunque el mecanismo interno difiere entre Python y Godot.

## 4. E2 — Alcance de los resultados

E2 estudió intervalos de decisión de 0,5; 1; 2; 3; 5 y 10 segundos, con cinco repeticiones por condición y un horizonte máximo de 180 segundos.

| Intervalo | Resultado informado |
| --- | --- |
| 0,5 s | Llegada en 63,42 s; 124 comandos |
| 1 s | Llegada en 55,70 s; 55 comandos |
| 2 s | Llegada en 81,00 s; 41 comandos |
| 3 s | Llegada en 89,13 s; 30 comandos |
| 5 s | Llegada en 145,85 s; 30 comandos |
| 10 s | Sin llegada dentro de 180 s; 18 comandos; distancia final 23,87 m |

La recomendación experimental documentada fue 1 segundo. El código mantiene `INTERVALO_S = 3.0`. La discrepancia sigue abierta y no autoriza cambiar el código.

Las repeticiones idénticas implican un tamaño efectivo de variabilidad de una condición por intervalo: permiten comprobar determinismo en esas condiciones, pero no estimar variabilidad frente a escenarios distintos.

La salida disponible no conserva la trayectoria temporal ni registra `timon_activo` real o `yaw_rate`. Los campos finales informados son `pos_final_x/z`, `dist_final`, `dist_recorrida`, `comandos` y `t_llegada`.

Por ello, E2 no permite afirmar ni descartar una órbita. La falta de llegada a los 10 segundos es un resultado censurado por el horizonte de 180 segundos, no una prueba de órbita ni de fallo permanente.

## 5. Hallazgos que no deben reconstruirse desde cero

Según la revisión de código y los informes del 22/10:

- Commit `31e0e1a`: migración de la flotabilidad Python a 168 puntos y parámetros físicos asociados documentados.
- Commit `c544da9`: cambio de `TIMON_TORQUE` de 886 a 2500.
- En `acciones.py`, `accion_rumbo` ejecuta el PID durante cada paso físico; `accion_ir_a` actualiza el rumbo objetivo cada 0,5 s, pero ejecuta el PID en cada paso físico.
- `entrenador_v2.py` usa `acciones.py`; no instancia `PIDRumbo` directamente. Las acciones de rumbo sí instancian y utilizan el PID.
- `accion_terminar` es una acción terminal lógica y no consume el horizonte.
- Las recetas tienen reglas y criterios de terminación propios, distintos de las acciones.
- E2 no demuestra un intervalo óptimo universal ni una equivalencia con Godot o con navegación real.

Estos puntos se apoyan en las lecturas comunicadas del código. Si una futura modificación cambia la fuente o la versión, corresponde revisar solo el alcance afectado.

## 6. Pendientes conocidos

- Bug 2: `logos-arranque` fija una rama antigua en la línea 131.
- Bug 3: falta la etiqueta `Trust` en la salida textual de `logos-gate`.
- `INTERVALO_S = 3.0` frente a la recomendación experimental de 1,0 s.
- Los expedientes 95 y 96 están pendientes de incorporación al repositorio.
- La inclusión de Timonel en el mecanismo de arranque aún no está implementada.
- La hipótesis H-E2 no está registrada en LOGOS.
- X0' no está autorizado.
- Los archivos no rastreados de GNSS no deben tocarse como parte de esta tarea.

## 7. Orden de lectura para un hilo nuevo

1. Este documento: 98.
2. `EXPEDIENTE/95_INFORME_CONSOLIDADO_TIMONEL_COPILOTO.md`.
3. `EXPEDIENTE/96_MEMO_EXPERIMENTOS_OCTUBRE_2026-10-15_16.md`.
4. Las fuentes de código solo cuando la pregunta concreta lo requiera: `timonel.py`, `timonel_python.py`, `simulador_polaris.py`, `controlador_pid.py`, `acciones.py`, `recetas_navegacion.py` y `entrenador_v2.py`.
5. Para las diferencias de simuladores, consultar el informe de divergencia física y el diagnóstico de timón correspondientes a sus respectivas versiones.

No repetir una lectura completa sin una pregunta nueva o una discrepancia documentada.

## 8. Reglas de actuación

- La IA propone; el Director decide.
- Separar hechos, inferencias e hipótesis.
- No ejecutar E2, X0' ni Godot sin autorización expresa.
- No modificar `INTERVALO_S` por inferencia.
- No alterar ni eliminar archivos no rastreados sin autorización.
- No incluir cambios GNSS ajenos en un commit de continuidad de Timonel.
- No actualizar hashes sin revisar el contenido.
- Antes del commit, revisar los archivos seleccionados y el diff completo.
- El commit no implica autorización de push.

**Estado del documento:** borrador para revisión. No incorporado a LOGOS ni al MANIFEST.
