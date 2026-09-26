# Experimento de distancia GNSS — NaveGo

Fecha: 2026-09-25
GT: `docs/gnss/ground_truth_synthetic_5min.jsonl` (693.22 m, virada 140-170 s)
Script: `docs/gnss/exp_dist/run_experiment.py` | 160 corridas (4 escenarios x 4 sigma x 10 semillas)

Metodologia: Metodo A replica `useNaveGoTracker.ts` (haversine + reset gap >15 m
+ descarte <0.8 m). Metodo B integra `speed x dt`. Referencia = sog del GT
integrado sobre las muestras que el receptor SI reporto (no acredita el tramo
perdido en cortes).

## H1: CONFIRMADA
Evidencia: con sigma=1.5 m, A sobreestima +46.6% en promedio (rango 40.9-52.6%),
y supera el 10% en 40/40 corridas. A sigma=3.0 el error llega a +142.7% y a
sigma=5.0 a +198.7%. La causa es la suma de ruido independiente entre fixes
consecutivos a 1 Hz, que se acumula como camino recorrido falso.

## H2: CONFIRMADA (al limite)
Evidencia: con sigma=0.5 m, A promedia +4.91% (mediana 4.96%, rango 3.08-8.58%).
Cumple el criterio <5% en promedio, pero 19/40 corridas superan el 5%. No es un
"bien" comodo: en el mejor caso de ruido el error ya ronda el umbral.

## H3: CONFIRMADA (92.6% de reduccion)
Evidencia: con sigma=3.0 m, |error| medio A=142.7% vs B=10.6%; B reduce el error
92.6%. Ademas B es insensible al ruido: su error es 10.59% constante en sigma
0.5/1.5/3.0/5.0. B no mide ruido porque usa la velocidad del receptor, no la
geometria de los fixes.

## DECISION PROPUESTA PARA NAVEGO
**Cambia** (parcialmente, no reemplaza): conservar A como medida principal y
agregar B como estimador complementario de validacion/fallback.
Justificacion: A es inutilizable como unica fuente con sigma>=1.5 m (+46.6% a
+142.7%), mientras que B se mantiene en ~10.6% independiente del ruido.
El cambio concreto: registrar `speed x dt` en paralelo a la suma polilinea y
exponer ambos valores en telemetria; si divergen >25%, marcar la distancia de la
sesion como "no confiable" en lugar de persistirla como valida.

## INCERTIDUMBRES
- El error constante de B (10.6%) proviene del sesgo de gap: B integra velocidad
  durante los cortes como si el barco siguiera moviendose. A y B fallan en
  direcciones opuestas; ninguno es exacto por separado.
- El GT es sintetico y sin modelo de corriente/deriva; no hay GT real de campo.
- Solo se probo reporte a 1 Hz. Con 0.2-0.5 Hz el ruido de A cambiaria.
- No se probo el efecto de filtros tipo Kalman/EMA ni de promediado de fixes.
- `spikes` (p=0.01, 50-500 m) se activan, pero el filtro de 15 m de A los
  convierte en resets de gap: su impacto exacto no se aislo en este analisis.
- No se midio costo de bateria/CPU de correr ambos metodos en el TCL T610P.
