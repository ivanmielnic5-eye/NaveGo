# SESION STATE MACHINE — NaveGo

Actualizado: 2026-08-22

## Principio fundamental
NaveGo es un instrumento, no solo un grabador de travesías.
Los sensores y el enlace se activan al abrir la app.
La travesía se activa únicamente al tocar "SOLTAR AMARRAS".

## Ciclo de instrumento (siempre encendido)
- GNSS: busca señal y muestra estado real.
- Túnel/Internet: refleja conexión con la PC.
- Reloj: corre desde el arranque.
- Acelerómetro: detecta horizontalidad.
- Estado del sistema: servidor y app vivos.

## Ciclo de travesía (bajo demanda)
EN_ESPERA (amarre)
  → "Soltar amarras" → REGISTRANDO
REGISTRANDO
  → "Amarrar" → EN_PAUSA
EN_PAUSA
  → "Reanudar navegación" → REGISTRANDO
REGISTRANDO o EN_PAUSA
  → "Finalizar travesía" → FINALIZADA
FINALIZADA
  → "Resetear" → EN_ESPERA

## Reglas de transición
1. Al abrir la app, arranca EN_ESPERA con contadores en cero.
2. Solo se registra distancia en REGISTRANDO.
3. Amarrar congela distancia, no suma.
4. Finalizar cierra la sesión y elimina "Reanudar".
5. Resetear limpia y vuelve a EN_ESPERA.
6. Una sesión solo puede generar una referencia.

## Lenguaje de controles
- "Soltar amarras" en lugar de "Iniciar derrota".
- "Amarrar" en lugar de "Pausar".
- "Reanudar navegación" en lugar de "Reanudar".
- "Finalizar travesía" en lugar de "Finalizar".
