# EXPANSION TELEMETRY — NaveGo

Actualizado: 2026-08-21

## Estado
Borrador / Requerimiento futuro. No implementar hasta cerrar auditoria de persistencia.

## Metricas deseadas
1. AWS — Velocidad del Viento Aparente (kn). Origen: simulada o hardware NMEA futuro.
2. AWA — Angulo del Viento Aparente (grados, babor/estribor). Origen: simulada o hardware NMEA futuro.
3. Posicion Geografica de Alta Resolucion. Origen: GPS/GNSS real.
4. Profundidad (m). Origen: simulada o ecosonda NMEA DBT/DPT.
5. Hora del Sistema de Alta Precision (HH:MM:SS). Origen: sistema local.

## Requerimientos de arquitectura
- Actualizar parsers NMEA para MWV, DBT/DPT, RMC/GGA.
- Redisenar layout HUD de forma modular sin saturar pantalla.
- Extender esquema SQLite para muestras de viento y profundidad.

## Prioridad sugerida
Fase 1: Posicion y hora en HUD (ya disponibles).
Fase 2: Viento AWS/AWA con datos simulados.
Fase 3: Profundidad simulada.
Fase 4: Integracion con hardware NMEA real.

## Nota
No implementar hasta cerrar auditoria de persistencia y validar guardado sin errores de unicidad.
