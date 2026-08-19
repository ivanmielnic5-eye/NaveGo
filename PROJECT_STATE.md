# NaveGo — Project State

Updated: 2026-08-19

## Flujo del Cockpit
ESTADO, TRABAJO, EVIDENCIA, ARCHIVOS, ACCION.

## Current objective
Validar sincronización Course-Up en movimiento real y estabilizar guardado de derrotas.

## Stable
- HUD principal
- SQLite
- Registro GPS
- Sincronización con PC (simulate.js)
- SOG
- COG
- Distancia
- Portrait North-Up
- Línea de derrota viva (verde continua)
- Línea de referencia (cian discontinua)
- Scripts de arranque, guardado y backup
- Documentos vivos: HUMAN_AI_WORKFLOW.md, interfaz_ia.md

## Experimental
- Carga de derrota de referencia desde SQLite
- Sincronización Course-Up con movimiento real
- CockpitScreen con 5 módulos

## Blocked
(Ninguno por ahora)

## Not verified
- Guardado de derrota sin WiFi (observado intermitente, sin patrón confirmado)

## Current hardware
- TCL X1 Pro
- Acelerómetro disponible
- Sin magnetómetro ni giroscopio dedicados

## Active experiments
- Course-Up: observar desfase COG mapa durante giros.

## Next recommended action
Probar guardado de derrota con y sin WiFi para confirmar patrón.

## Critical decisions
- Portrait = North-Up
- Landscape = Course-Up
- Acelerómetro como auxiliar, no como fuente de posición.
- Ninguna IA puede cambiar decisiones arquitectónicas sin propuesta explícita.

## Do not touch
- HUD superior
- Persistencia GPS
- Sincronización estable
- Lógica de cálculo de distancia
