# GODOT TELEMETRY INTEGRATION — Simulador NaveGo

Actualizado: 2026-08-23

## Objetivo
Conectar la brújula digital y la telemetría del velero al sistema LOGOS.
Que el simulador hable el mismo idioma que NaveGo real.

## Nodos de referencia
CompassHUD (Control)
├── OuterRing
├── NorthIndicator
├── CardinalLabels
├── InnerGraduations
├── VectorLine
└── CenterDisplay (COG, SOG)

Sailboat (RigidBody3D)
├── Bow (Node3D) → define la proa física
├── Hull
└── CenterOfBuoyancy

TrueNorth (Node3D) → referencia fija del norte simulado

## Cálculo de SOG
En GDScript, sobre el plano XZ:
var velocity_2d = Vector2(linear_velocity.x, linear_velocity.z)
var sog_m_s = velocity_2d.length()
var sog_kn = sog_m_s * 1.94384  # metros/seg → nudos

## Cálculo de COG
var cog_rad = atan2(-velocity_2d.x, -velocity_2d.y)
var cog_deg = fmod(rad_to_deg(cog_rad) + 360.0, 360.0)

El valor COG se muestra en la brújula como 000.0° a 359.9°.

## Rumbo cardinal
Convertir COG a sector:
0-22.5 y 337.5-360 → N
22.5-67.5 → NE
67.5-112.5 → E
112.5-157.5 → SE
157.5-202.5 → S
202.5-247.5 → SO
247.5-292.5 → O
292.5-337.5 → NO

## Posición geodésica virtual
Definir un punto de referencia inicial:
lat0, lon0 y una escala de metros por grado.

Luego mapear:
lat_sim = lat0 + (global_position.z / 111320.0)
lon_sim = lon0 + (global_position.x / (111320.0 * cos(lat0_rad)))

Eso permite generar trazas compatibles con NaveGo.

## Capas futuras
- Viento aparente y real.
- Escora lateral y abatimiento.
- Corrientes y deriva.
- Alertas tempranas de estrés.

## División de tareas sugerida
- DeepSeek: cinemática, vectores, integración de telemetría.
- Claude: estructura de logs, alertas, fatiga.
- Géminis: auditoría, bitácora, sincronización.
- Iván: validación estratégica y escenarios.

## Nota
El informe define la base; no se implementa todavía.
El orden de integración será: proa/norte, SOG, COG, cardinal, lat/lon, viento.
