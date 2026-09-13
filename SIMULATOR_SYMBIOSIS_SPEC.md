# SIMULATOR SYMBIOSIS SPEC — NaveGo / LOGOS

Actualizado: 2026-08-23

## Proposito
El simulador Godot es un nodo vivo del ecosistema. No reemplaza al instrumento real; lo complementa.
Genera condiciones extremas y evidencia para entrenamiento y validacion.

## Rol en LOGOS
El simulador es un Project Adapter mas. Habla el mismo lenguaje universal:
ESTADO, TRABAJO, EVIDENCIA, ARCHIVOS, ACCION.

## Fuentes de datos
- Real: trajectory_data.json, sensores simulados, eventos de simulate.js.
- Sintetica: motor de fisica propio, olas, viento, colisiones, escenarios.

## Escenarios de simulacion
- Tormenta y oleaje agresivo.
- Huracan y rafagas.
- Colision con objeto flotante.
- Perdida de GNSS en tunel o bajo techo.
- Falla de motor y deriva.
- Hombre al agua simulado.
- Fondeo de emergencia.

## Salida hacia LOGOS
- Eventos de simulacion.
- Evidencia de comportamiento.
- Logs de fatiga y limites.
- Alertas tempranas.
- Registros para TEST_LOG.md y PROJECT_STATE.md.

## Division de IAs propuesta
- DeepSeek: optimizacion matematica, fisica, arrastre, colisiones, 60 FPS.
- Claude: bloques estructurales, telemetria, alertas, logs de fatiga.
- Geminis: auditoria, memoria, bitacora, hashes.
- Ivan: direccion estrategica e hipotesis de conflicto.

## Fases de implementacion
Fase 0: Documentar arquitectura y roles.
Fase 1: Brujula digital visual en Godot (software-list, hardware-wait).
Fase 2: Integracion de datos simulados de simulate.js.
Fase 3: Escuela de navegacion con ejercicios.
Fase 4: Escenarios extremos y alertas tempranas.
Fase 5: Sincronizacion viva con LOGOS.

## Nota
No se implementa fisica completa ahora. Se deja la arquitectura preparada.
Base visual de agua: water.gd con get_height y oscilacion de posicion; no representa fisica completa.
