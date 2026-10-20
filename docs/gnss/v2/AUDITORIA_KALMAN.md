# Auditoría Conceptual de Medición y Filtrado (Kalman)

## 1. Magnitud objetivo: ¿Qué queremos medir?
El sistema NaveGo, al depender exclusivamente de datos GNSS (GPS), estima la **Distancia Acumulada sobre el Fondo** (*Distance Run Over Ground*). Es crucial distinguirla de:
- **Distancia a través del agua (STW):** NaveGo no tiene corredera física para medirla. Depende de la corriente.
- **Desplazamiento neto (DMG):** La distancia en línea recta entre el punto de partida y el actual. No refleja el camino recorrido.
- **Distancia observada vs. estimada:** Durante un corte de señal, no sabemos la trayectoria exacta recorrida; cualquier suma durante ese hueco es una estimación, no una medición directa.

## 2. Fuentes y límites de la medición
- **Entradas actuales:** El receptor GNSS provee latitud, longitud, velocidad (SOG) y rumbo (COG).
- **Limitación:** No hay fusión con sensores inerciales (IMU) ni corredera. Toda estimación de movimiento depende de la calidad del GNSS y de su modelo de error.

## 3. El dilema: Movimiento real vs. Deriva del sensor
- **Deriva (Drift):** Cuando el barco está amarrado, el GNSS reporta pequeñas variaciones de posición (1 a 5 m). Esto **no es movimiento real** y no debe sumarse al odómetro.
- **Movimiento lento / Zigzag:** Una lancha que avanza y retrocede 50 metros en un amarre, o que navega a 1 nudo, genera cambios geométricos reales. Un filtro agresivo puede confundir esto con deriva y borrar el recorrido real.
- **Garreo real:** El barco se mueve del ancla (por viento o corriente). El sistema debe detectarlo, no suavizarlo como si fuera ruido.

## 4. Antecedente K0 (exp_dist3)
El filtro de Kalman en `docs/gnss/exp_dist3/run_faseA3.py` es un Kalman Lineal 2D (posición y velocidad por eje) con parámetros `Q=0.0001`, `R=2.25` (calibrado para ruido blanco IID).
- **Falla documentada:** En la trayectoria T4 (garreo), el filtro A+K midió 6.58 m cuando el camino real era de 96.97 m. El filtro interpretó el zigzag real como ruido y lo eliminó.
- **Conclusión:** K0 no es apto para producción sin adaptaciones, ya que prioriza la suavidad sobre la fidelidad del movimiento real.

## 5. Estado del ruido correlacionado (AR1)
Hemos implementado un modelo AR(1) en el simulador. Sin embargo, los resultados de validación (autocorrelación observada de 0.924 vs. teórica de 0.95) son evidencia exploratoria, no una validación universal del comportamiento del GNSS real.

## 6. Propuesta de Benchmark de Filtrado (V2)
Para evaluar cualquier filtro (K0, K1 o futuros), se proponen seis escenarios independientes:
1.  **Recta en movimiento:** Fidelidad en velocidad y dirección.
2.  **Navegación lenta:** Mantener el rumbo sin perder metros reales.
3.  **Zigzag / Virada:** Preservar la geometría del track (ida y vuelta).
4.  **Inmóvil en amarre:** No acumular deriva falsa (Error de deriva en reposo debe ser ~0).
5.  **Garreo real:** Detectar el desplazamiento del ancla (no filtrarlo).
6.  **Cortes de señal:** Cortar el track y no sumar la distancia no observada.

**Métricas exigidas:** Error de distancia acumulada, deriva falsa acumulada, y preservación del track visual.

## 7. Decisiones pendientes del Director
- Confirmar formalmente que el objetivo principal de NaveGo es la *Distancia Acumulada sobre el Fondo*.
- Definir las tolerancias métricas aceptables para el benchmark (ej. máximo de deriva falsa en 1 hora de amarre).
- Decidir si el enfoque del próximo filtro será adaptar el K0 al ruido AR(1) o explorar un modelo de fusión de sensores.
