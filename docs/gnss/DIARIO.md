## Bloque C — 24 sep 2026
Generador de GNSS simulado. Aplica ruido gaussiano, spikes,
latencia, y genera fixes con measuredAt/receivedAt.

## Etapa 2 cerrada — 24 sep 2026
GNSS Simulator funcionando. 62 fixes generados desde
74s de ground truth. Corte de 12s verificado (gap de
13.198 ms entre fix 30 y 31). Latencia 300ms aplicada.
Seed 20260924 reproducible.

## Estado
- Etapa 0: viento constante ✅
- Etapa 1: ground truth logger ✅
- Etapa 2: GNSS simulator ✅
- Etapa 3: ReplayLocationProvider (siguiente)

## Verificacion por DSH — 24 sep 2026
DSH leyo los archivos y verifico sus 5 hipotesis contra el log.
Resultado: 4 confirmadas, 1 refutada (con hallazgo mejor).
Descubrio que post-corte el heading queda congelado en 171.0,
lo cual es coherente con trayectoria recta, pero revela que
nuestro simulador no modela el comportamiento real de un GPS
durante un corte (deberia estimar heading con ultima velocidad).

## Hallazgo colateral
DSH detecto off-by-one en este diario (decia fix 29-30, era 30-31).
Corregido.

## Estado
Etapa 2 verificada empiricamente por DSH.
Siguiente: Etapa 3 - ReplayLocationProvider en NaveGo.
