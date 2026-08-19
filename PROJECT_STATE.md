# NaveGo — Project State

Updated: 2026-08-19

## Flujo del Cockpit
ESTADO, TRABAJO, EVIDENCIA, ARCHIVOS, ACCION.

## Sistema Universal
- COCKPIT_CORE_SPEC.md: nucleo arquitectonico universal.
- COCKPIT_UNIVERSAL_IMPLEMENTACION.md: plan de implementacion por fases.
- COCKPIT_PC_SPEC.md: especificacion visual y funcional para pantalla grande.
- HUMAN_AI_WORKFLOW.md: flujo conceptual de trabajo humano-IA.
- NaveGo es adaptador de prueba, no definicion del sistema.

## Current objective
Validar sincronizacion Course-Up en movimiento real y estabilizar guardado de derrotas.

## Stable
- HUD principal
- SQLite
- Registro GPS
- Sincronizacion con PC (simulate.js)
- SOG
- COG
- Distancia
- Portrait North-Up
- Línea de derrota viva (verde continua)
- Línea de referencia (cian discontinua)
- Scripts de arranque, guardado y backup
- Documentos vivos del Cockpit universal

## Experimental
- Carga de derrota de referencia desde SQLite
- Sincronizacion Course-Up con movimiento real
- CockpitScreen con 5 modulos

## Blocked
(Ninguno por ahora)

## Not verified
- Guardado de derrota sin WiFi (observado intermitente, sin patron confirmado)

## Current hardware
- TCL X1 Pro
- Acelerometro disponible
- Sin magnetometro ni giroscopio dedicados

## Active experiments
- Course-Up: observar desfase COG mapa durante giros.

## Next recommended action
Probar guardado de derrota con y sin WiFi para confirmar patron.

## Critical decisions
- Portrait = North-Up
- Landscape = Course-Up
- Acelerometro como auxiliar, no como fuente de posicion.
- Ninguna IA puede cambiar decisiones arquitectonicas sin propuesta explicita.
- Cockpit universal separado del contexto nautico.

## Do not touch
- HUD superior
- Persistencia GPS
- Sincronizacion estable
- Logica de calculo de distancia
- Nucleo arquitectonico del Cockpit
