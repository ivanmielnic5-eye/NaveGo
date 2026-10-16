# REGISTRO DE CIERRE — EXPERIMENTO 0: GODOT HEADLESS

**Director:** Iván
**Fecha:** 2026-10-15
**Estado:** COMPLETADO según los siete criterios reportados.
**Modo:** Registro de evidencia existente. No ejecutar nuevas pruebas.

---

## 1. Objetivo

Habilitar ejecuciones automatizadas de Godot en modo headless con comandos programados y registros aislados por corrida, como base de un laboratorio reproducible.

---

## 2. Resultado

Los siete criterios de aceptación definidos en el diseño v2 fueron superados.

| # | Criterio | Estado |
|---|---|---|
| 1 | Inicialización correcta | OK |
| 2 | Comandos escritos con spacing ≥ 600 ms | OK |
| 3 | Cierre por `duracion_total_ms` | OK |
| 4 | `ground_truth.jsonl` dentro del rango esperado | OK (412 líneas) |
| 5 | `telemetria.jsonl` con ~1 muestra/segundo | OK (8 líneas) |
| 6 | Aislamiento de registros persistentes | OK |
| 7 | Carpeta de corrida nueva y verificable | OK |

---

## 3. Evidencia de la corrida

Directorio: `~/.logos/runs/20261015_195114_test/`

Contenido:
- `comandos_in.json` (input)
- `comandos.jsonl` (3 líneas escritas por el runner)
- `ground_truth.jsonl` (412 líneas)
- `telemetria.jsonl` (8 líneas)
- `runner.log` (diagnóstico del runner)
- `resultado.json` (resumen de cierre)

---

## 4. Timing

Errores de escritura respecto de los tiempos programados:
- Comando 1 (`t_rel=1000`): escrito a +3 ms.
- Comando 2 (`t_rel=3000`): escrito a +3 ms.
- Comando 3 (`t_rel=5000`): escrito a +5 ms.

**Precisión:** errores de 3–5 ms respecto del instante programado.

**Límite:** esto mide el momento en que el runner escribió el comando al archivo. No demuestra por sí solo que el bridge lo haya aplicado físicamente al barco con ese mismo error. Esa medición requiere instrumentación adicional y se reserva para experimentos posteriores.

---

## 5. Registro físico

- `ground_truth.jsonl`: 412 líneas.
- `telemetria.jsonl`: 8 líneas.
- Frecuencia medida del ground truth: **48,54 Hz**.
- Duración real de la corrida: **8,49 s** (programada: 8,00 s + gracia 2,00 s = 10,00 s, cerró antes por cumplimiento de `min_cierre`).

---

## 6. Aislamiento

Verificación concreta, antes vs después de la corrida:

| Archivo persistente | Antes | Después |
|---|---|---|
| `~/.local/share/godot/app_userdata/interfaz/timonel/telemetria.jsonl` | 0 líneas | 0 líneas |
| `~/.local/share/godot/app_userdata/interfaz/timonel/comandos.jsonl` | 1792 líneas | 1792 líneas |
| ground_truth más reciente | `1792102909376` | `1792102909376` (sin cambio) |

Conclusión: el runner no escribió en las rutas del sistema normal. La regla de aislamiento de P35 se cumple en la corrida reportada.

---

## 7. Respuesta observada

Datos del log y la telemetría:
- SOG pasó de 0,0 a 3,9 kn durante la corrida.
- El heading varió ±1–2° con cada comando.
- AWA (ángulo de viento aparente) cambió con el rumbo.

**Interpretación:** la respuesta es compatible con una aplicación física de los comandos. No se atribuye causalidad detallada (qué comando produjo qué cambio exacto) sin una correlación fina entre comandos escritos y respuesta tick a tick, que no se realizó en esta corrida.

---

## 8. Archivos modificados

Todos con respaldo `.pre-headless` en el mismo directorio:

1. `~/interfaz/project.godot`
2. `~/interfaz/scripts/main.gd`
3. `~/interfaz/rudder_controller.gd`
4. `~/interfaz/sail_controller.gd`
5. `~/interfaz/scripts/ground_truth_logger.gd`
6. `~/interfaz/scripts/timonel_bridge.gd`

Archivos nuevos (sin respaldo, no existían antes):

7. `~/interfaz/test_input.gd` (autoload, no utilizado en esta corrida)
8. `~/interfaz/runner_headless.gd` (orquestador)
9. `~/interfaz/run_headless.sh` (wrapper)

---

## 9. Límites

Lo que **NO** demuestra este experimento:

- **Paridad Python–Godot.** No se corrió el mismo caso en ambos simuladores.
- **Reproducibilidad entre ejecuciones.** Solo se corrió una vez.
- **Determinismo físico estricto.** Godot no garantiza física determinista, y no se midió dispersión.
- **Aplicación física exacta de cada comando.** El timing de escritura no es lo mismo que el timing de aplicación.
- **Aislamiento con otros escritores.** Solo se verificaron los dos conocidos (`ground_truth_logger`, `timonel_bridge`).

---

## 10. Siguiente experimento propuesto

**Experimento 1 — Paridad de dinámica Python–Godot.**

Objetivo: correr el mismo caso (estado inicial, viento, secuencia de comandos) en ambos simuladores y comparar trayectorias tick a tick.

Requisitos previos:
- Definir tolerancia (diferencia máxima aceptable en `pos_x`, `pos_z`, `hdg_deg`).
- Definir condiciones iniciales y de viento idénticas.
- Definir criterio de cierre común.

**No se ejecuta en este documento.**

---

## Restricciones cumplidas

- Sin commits.
- Sin modificar `EXPEDIENTE/PENDIENTES.md` ni decisiones institucionales.
- Sin alterar archivos del simulador ni registros de la corrida.
- Sin ejecutar Godot, Ollama ni nuevos experimentos durante la redacción.
- Respaldos `.pre-headless` conservados.
