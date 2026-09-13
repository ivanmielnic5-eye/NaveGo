# GODOT TELEMETRY INTEGRATION — Simulador NaveGo

Actualizado: 2026-08-23

## Objetivo
Conectar la brújula digital y la telemetría del velero al sistema LOGOS.
Que el simulador hable el mismo idioma que NaveGo real.

## Arquitectura por capas
Sailboat / Physics
  ↓
TelemetryProvider
  ├── SOG
  ├── COG
  ├── Heading
  └── Position
  ↓
NavigationModel
  ↓
CompassHUD

## Distinción fundamental
COG ≠ Heading.
COG es hacia dónde se desplaza el barco.
Heading es hacia dónde apunta la proa.
Un barco puede tener COG 037° y Heading 052° por corriente o abatimiento.

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
var velocity_2d = Vector2(linear_velocity.x, linear_velocity.z)
var sog_m_s = velocity_2d.length()
var sog_kn = sog_m_s * 1.94384

## Cálculo de COG
var cog_rad = atan2(-velocity_2d.x, -velocity_2d.y)
var cog_deg = fmod(rad_to_deg(cog_rad) + 360.0, 360.0)

## Umbral de COG
Si SOG < 0.1 m/s, COG no se actualiza para evitar saltos absurdos.

## Heading
Se calcula desde la orientación de proa en el plano XZ.
Debe poder ser independiente de COG.

## Rumbo cardinal
0-22.5 y 337.5-360 → N
22.5-67.5 → NE
67.5-112.5 → E
112.5-157.5 → SE
157.5-202.5 → S
202.5-247.5 → SO
247.5-292.5 → O
292.5-337.5 → NO

## Posición geodésica virtual (EXPERIMENTAL)
No es navegación geodésica real.
Es una escala simulada para visualización.
Usar factor 0.000015 como aproximación local.

## Prueba geométrica mínima
1. Barco detenido → SOG ≈ 0.
2. Velocidad hacia -Z → COG ≈ 000°.
3. Velocidad hacia +X → COG ≈ 090°.
4. Velocidad hacia +Z → COG ≈ 180°.
5. Velocidad hacia -X → COG ≈ 270°.
6. Giro a 45° → COG ≈ 045°.
7. Comprobar que la aguja visual coincide.
8. Comprobar que Heading y COG pueden ser independientes.

## División de tareas sugerida
- DeepSeek: cinemática, vectores, integración de telemetría.
- Claude: estructura de logs, alertas, fatiga.
- Géminis: auditoría, bitácora, sincronización.
- Iván: validación estratégica y escenarios.

## Nota
El informe define la base; no se implementa todavía.
El orden de integración será: proa/norte, SOG, COG, cardinal, lat/lon, viento.
