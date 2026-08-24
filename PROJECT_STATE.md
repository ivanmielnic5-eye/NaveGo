# NaveGo — Project State

Updated: 2026-08-22

## Fase actual
1. Integridad

## Semáforo
🟡 OBSERVACIÓN

## Flujo del Cockpit
ESTADO, TRABAJO, EVIDENCIA, ARCHIVOS, ACCION.

## Sistema Universal
- COCKPIT_CORE_SPEC.md
- COCKPIT_UNIVERSAL_IMPLEMENTACION.md
- COCKPIT_PC_SPEC.md
- COCKPIT_DATA_CONTRACT.md
- COCKPIT_CORE_DATA_KERNEL.md
- HUMAN_AI_WORKFLOW.md
- NaveGo es adaptador de prueba, no definición del sistema.

## Current objective
Cerrar deuda de persistencia y preparar máquina de estados de sesión.

## Stable
- HUD principal
- SQLite
- Registro GPS
- Sincronización con PC (simulate.js)
- SOG, COG, Distancia
- Portrait North-Up
- Línea de derrota viva y referencia
- Scripts de arranque, guardado y backup
- Token en LOGOS
- Integridad SHA-256
- Panel visual LOGOS
- Indicador de internet corregido
- Scroll en HistoryScreen

## Experimental
- Course-Up en movimiento real
- CockpitScreen con 5 módulos
- Máquina de estados de sesión en diseño

## Blocked
(Ninguno por ahora)

## Not verified
- Guardado de derrota sin WiFi
- Expansión de telemetría futura

## Current hardware
- TCL X1 Pro
- Acelerómetro disponible
- Sin magnetómetro ni giroscopio dedicados
- Canal de voz USB WO Mic operativo

## Active experiments
- Course-Up: observar desfase COG ↔ mapa durante giros.

## Next recommended action
Implementar instrumento siempre encendido en código.

## Critical decisions
- Portrait = North-Up
- Landscape = Course-Up
- Pausa = Opción C: marcador de pausa, sin sumar distancia.
- Acelerómetro como auxiliar, no fuente de posición.
- Ninguna IA puede cambiar decisiones arquitectónicas sin propuesta explícita.
- Cockpit universal separado del contexto náutico.
- NaveGo como instrumento: sensores siempre encendidos, travesía bajo demanda.

## Do not touch
- HUD superior
- Persistencia GPS
- Sincronización estable
- Lógica de cálculo de distancia
- Núcleo arquitectónico del Cockpit

## Simulador Godot
- GODOT_AI_BOOTSTRAP.md como entrada oficial para IAs.
- Estado actual documentado en GODOT_SIMULATOR_SPEC.md y GODOT_TELEMETRY_INTEGRATION.md.
- Referencia externa: Buoyancy in Godot 4 (CBerry22).
- Proxima accion: implementar WaterController con get_water_height sincronizado.
