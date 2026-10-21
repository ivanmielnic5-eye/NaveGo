# Roadmap hacia la Ingeniería de Estándar Industrial

Este documento establece las directrices técnicas para la evolución de NaveGo. El objetivo es dejar de ser un "prototipo académico" para convertirnos en un software de navegación de grado de ingeniería, compitiendo por la vía del software, no del hardware.

## Estrategia de Asimetría Competitiva

Sabemos que no tenemos el hardware de Garmin, u-blox o Trimble (RTK, IMUs de grado militar). Sin embargo, podemos equiparar su lógica de software y superarlos en los frentes donde su modelo de negocio los limita:

1. **Nuestra ventaja (Donde ellos no pueden):**
   * **Soberanía y Offline:** No dependemos de servidores en la nube ni de suscripciones. Procesamiento local.
   * **Honestidad del Track (Track Honesto):** Ellos suavizan el track para que se vea "lindo" en pantalla. Nosotros priorizamos la verdad geométrica: si perdimos señal, el track se corta. "El sistema NO MIENTE".

2. **Lo que tenemos que equiparar (Lo que nosotros no destacamos por falta de hardware):**
   * **Fusión de Sensores:** Usar los sensores del celular (acelerómetro/giroscopio) como respaldo cuando el GNSS falla.
   * **Modelado de Ruido Realista:** Dejar atrás el ruido perfecto (IID) y usar modelos estocásticos que reflejen la realidad (Gauss-Markov / AR(1)).
   * **Control de Calidad (QA) en Tiempo Real:** Descartar fixes basados en HDOP, ruido de velocidad y contexto, no solo en el salto geométrico.

## Directrices de Implementación (Pipeline de Desarrollo)

A partir de hoy, el pipeline de trabajo y los criterios de aceptación para cualquier algoritmo (como C_v2 o sus sucesores) son:

1. **Validación Sim-to-Real:** Ningún algoritmo se declara exitoso solo porque pasa el simulador. Tiene que probarse contra tracks GPX reales (como el Velero Nola) para demostrar invarianza ante ruido real.
2. **Gestión de Incertidumbre:** El algoritmo debe calcular su propio error (varianza/covarianza). No basta con sumar distancias; hay que saber cuánto confiar en ellas.
3. **Costo Computacional y de Batería:** El procesamiento de sensores no puede agotar la batería del TCL T610P en 1 hora. Se priorizan operaciones O(N) en lugar de iteraciones pesadas.
4. **Tolerancia a Fallos de Hardware:** El código debe asumir que el reloj del celular se desincroniza, que el sistema operativo congela la app en segundo plano y que los sensores entregan basura.
5. **Independencia de Datos del Proveedor:** Todo desarrollo debe poder auditarse en local. Nada de cajas negras.

## Brechas Técnicas Actuales (A resolver)

| Brecha Detectada | Impacto | Solución Propuesta |
| :--- | :--- | :--- |
| Ruido del simulador (IID) | Falso positivo en pruebas | **[HECHO]** Modelo AR(1) configurable implementado (ver HALLAZGOS sección 15). Falta calibrar varianza marginal. |
| Falta de filtro de estados | Suma ruido geométrico | Implementar Filtro de Kalman Extendido (EKF) o similar |
| Ausencia de IMU | Track cortado ciegamente | Integrar sensores nativos de Android para heading/speed de respaldo |
| Reloj de software vs GNSS | `dt` distorsionado en gaps | Usar `measuredAt` del GNSS (no `receivedAt` ni `Date.now()`) |
