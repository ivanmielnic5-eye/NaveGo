# LANDSCAPE V2 — Especificación Técnica

Fecha: 2026-08-25

## 1. Concepto

LandscapeV2 es un banco de pruebas reproducible para auditoría de navegación.
No controla al velero. Observa, genera condiciones y produce telemetría diferencial.

## 2. Principio rector

Ground Truth nunca se degrada.
La degradación afecta únicamente a la percepción/estima.

## 3. Marco cardinal

Norte = -Z
Este = +X
Sur = +Z
Oeste = -X

COG = atan2(Vx, -Vz)

## 4. Capas

- World Frame
- Functional Zones
- Ground Truth
- Sensor Degradation
- Differential Black Box

## 5. Reglas congeladas

1. LandscapeV2 observa y genera condiciones; no gobierna la física del barco.
2. Ground Truth jamás se degrada.
3. COG/SOG de Ground Truth usan el marco cardinal del mundo.
4. La degradación empieza después de validar los 8 puntos cardinales.

## 6. Pruebas de validación

| Rumbo | COG esperado |
|-------|--------------|
| N     | 000°         |
| NE    | 045°         |
| E     | 090°         |
| SE    | 135°         |
| S     | 180°         |
| SO    | 225°         |
| O     | 270°         |
| NO    | 315°         |

## 7. Próximo paso

Implementar LandscapeV2 → Ground Truth → COG/SOG → validación cardinal.
