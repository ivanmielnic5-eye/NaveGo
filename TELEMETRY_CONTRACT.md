# TELEMETRY CONTRACT — NaveGo ↔ Simulador

Actualizado: 2026-08-25

## Propósito
Definir el formato de comunicación entre NaveGo (móvil/sensores) y el simulador Godot.
Es la base del Gemelo Digital Activo.

## Fuentes de datos actuales
NaveGo ya captura:
- SOG (Speed Over Ground)
- COG (Course Over Ground)
- Heading (cuando esté disponible)
- Accuracy (precisión GNSS)
- Timestamp
- Latitud / Longitud

## Datos que el simulador espera
El simulador Godot consume:
- Posición X/Z (metros locales)
- Altura de agua (para flotabilidad)
- Viento (dirección y fuerza)
- Estado del velero (escora, rumbo)

## Propuesta de contrato
Un objeto JSON por actualización:
{
  "timestamp": 0,
  "lat": 0.0,
  "lon": 0.0,
  "sog_ms": 0.0,
  "cog_deg": 0.0,
  "heading_deg": 0.0,
  "accuracy_m": 0.0,
  "pitch_deg": 0.0,
  "roll_deg": 0.0,
  "yaw_deg": 0.0
}

## Transporte
Por ahora:
- NaveGo → simulate.js → trajectory_data.json → Godot.
Futuro:
- WebSocket local o archivo de stream en tiempo real.

## Reglas
- NaveGo es fuente de evidencia real.
- El simulador es fuente de escenarios sintéticos.
- LOGOS registra y compara.
- Ningún dato se inventa: se marca como NO_VERIFICADO si falta.
