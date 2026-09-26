# Contrato GNSS — NaveGo / Simulador

Fecha: 24 sep 2026
Estado: CONGELADO

## Por que dos timestamps
- measuredAt: comparar contra ground truth
- receivedAt: watchdog (GNSS_DEGRADED_AFTER_MS, etc)

## Semantica de accuracy
Radio de incertidumbre en metros (Expo). No es sigma.

## Regla fundamental
La app NaveGo NO tiene dos caminos (real vs simulado).
El pipeline es el mismo. Solo cambia la fuente.
El replay esta detras de un flag, invisible en produccion.

## Scenario con seed
Misma seed = misma corrida. Reproducible criptograficamente.
