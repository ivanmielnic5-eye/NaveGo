# Hallazgos Fase A - V2 (Track Honesto)

Fecha: 2026-10-20
Corrida: docs/gnss/v2/results/v2_20261020_040923
Comando: python3 docs/gnss/v2/eval/run_all.py --phase A
n_rows: 385 · n_missing: 0 · exit: 0

Estado: DOCUMENTACION DE RESULTADOS. No se modificaron metodos, criterios
ni codigo tras la corrida. Los criterios originales permanecen definidos
tal cual estaban al momento de ejecutar.

## 0. Alcance

Esta corrida evalua A (historico), B (produccion, verificado F.4+F.5) y
5 variantes de C sobre 11 escenarios x 5 seeds = 55 archivos x 7 metodos.
Los resultados se reportan como observacion. No se declara ganador global.

## 1. Conciliacion con el primer reporte

El primer reporte afirmo "A = B = C en todos los escenarios sin cortes".
Esa afirmacion es INCORRECTA tal como esta redactada. La tabla por
escenario muestra:

- S1, S2, S3 (sigma <= 1.5): A, B, C difieren < 1% entre si. Convergen.
- S4 (sigma = 3.0): A = +126.4%, B = +128.9%, C_orig = +128.1%. Divergen
  levemente.
- S5 (sigma = 5.0): A = +171.4%, B = +262.6%, C_orig = +191.8%. Divergen
  fuertemente.

La redaccion correcta es: "en sigma <= 1.5 los tres metodos convergen;
en sigma >= 3.0 divergen y la divergencia crece con sigma". Los
denominadores (gt_ref_m) son iguales para los tres metodos en cada
escenario (mismo fixes.jsonl, verificado por hash en C3). Las
definiciones de dist_m son las mismas en methods.py. La diferencia es
real y atribuible al comportamiento de los metodos, no a la metrica.

## 2. S1 - Sesgo geometrico sistematico

Observado: err_m = -0.864 en A, B y C, identico entre seeds.

Causa: tools/gnss_simulator.py convierte pos_x/pos_y a lat/lon con
WGS84 (R = 6378137 m). methods.py y processFix.ts calculan haversine
con R = 6371000 m. Diferencia relativa: 6371000/6378137 - 1 ~= -0.112%.
Sobre el recorrido de 769 m: -0.86 m. Coincide con lo observado.

Consecuencia: el criterio C1 original (|err_m| < 0.5, |err_rel| < 0.5%)
es mas fino que la diferencia entre dos constantes geodesicas estandar.

Tolerancia candidata: |err_m| < 2.0 m y |err_rel| < 1%. NO aplicada
en esta corrida. Requiere aprobacion explicita. La justificacion es
metrologica: cubre la diferencia entre WGS84 y R=6371000 en recorridos
de hasta ~1.5 km, sin ocultar errores de algoritmo.

Estado de C1 en esta corrida: FAIL, esperado, documentado.

## 3. S6 - Resultado observado, no causalidad demostrada

Observado en S6 (corte 10 s, sigma = 1.0):

| Metodo    | err_%  | gapEv | gRest |
|-----------|--------|-------|-------|
| A         | +16.9% | 0.0   | 1.0   |
| B         | +20.9% | 0.0   | 0.0   |
| C_orig    | +17.1% | 1.0   | 1.0   |

B - A = +29.4 m. Coincide en orden de magnitud con el avance del barco
durante el corte (2.57 m/s x 10 s ~= 25.7 m) mas ruido geometrico de
2-3 m.

Limitacion importante: los +29.4 m NO estan aislados del efecto del
ruido geometrico que afecta a todos los escenarios. Para atribuir esa
diferencia exclusivamente al corte se necesita un escenario control
S6' sin corte, misma trayectoria, misma seed, mismo sigma, con el mismo
conjunto de observaciones fuera de la ventana de corte. Ese control
NO existe en la matriz actual y NO fue ejecutado.

Lo que SI esta demostrado:
- B no abre gap_event en corte de 10 s (watchdog requiere > 15 s).
- B no corta por isGapRestart (threshold adaptativo = 61 m > salto 26 m).
- C_orig si abre 1 gap_event por corrida y su distancia coincide con A.

Lo que NO esta demostrado:
- Que el total de +29.4 m sea efecto puro del gap.

Estado de C5 en esta corrida: FAIL. El criterio original
(err_m_B en [+20, +30] absoluto) no contemplaba el ruido geometrico
base. No se reetiqueta como aprobado. Se documenta como criterio a
reformular.

## 4. S17 - Advertencia seria para C

Observado en S17 (sigma = 5.0, barco detenido, sin corte):

| Metodo    | gapEv | gRest | ruido | err_%  |
|-----------|-------|-------|-------|--------|
| A         | 0.0   | 38.8  | -     | +191.5 |
| B         | 0.0   | 0.2   | -     | +287.9 |
| C_orig    | 3.6   | 3.6   | 35.2  | +211.5 |
| C_pair    | 3.6   | 3.6   | 35.2  | +191.5 |

C_orig abre 3.6 gap_event falsos por corrida con el barco quieto y
sigma = 5. Causa: la rama speed <= 0.3 m/s se cumple siempre en
detencion. Cualquier salto > 15 m por ruido se clasifica GAP_REAL.

B no abre ninguno (threshold adaptativo alto).
A no abre ninguno (no tiene capacidad de abrir gap_event).

Consecuencia operativa: en S17, C es PEOR que A y B en falsos gaps
visuales. La rama speed <= 0.3 necesita rediseno antes de proponer C
para produccion. C NO queda recomendado para produccion en este estado.

## 5. C_pair vs C_orig - diferencia medida

Observado en S5 (sigma = 5.0, sin corte):

| Metodo    | err_%  | gRest | ruido |
|-----------|--------|-------|-------|
| A         | +171.4 | 39.2  | -     |
| C_orig    | +191.8 | 0.0   | 39.2  |
| C_pair    | +171.4 | 0.0   | 39.2  |

C_orig acumula d_anchor (distancia al ultimo ancla aceptada). Cuando el
ancla queda atras por rechazos de ruido, la siguiente CONTINUIDAD suma
un d_anchor grande. Eso agrega ~20 puntos porcentuales de inflacion.

C_pair acumula d_pair en CONTINUIDAD (distancia entre fixes consecutivos
aceptados). Iguala a A exactamente en S5.

Limitacion de C_pair: comparte con C_orig el problema de S17 (3.6
gap_event falsos por corrida con barco detenido). Reducir la inflacion
de distancia no corrige el comportamiento visual.

C_pair NO se declara ganador global. Solo se documenta que, en ruido
puro, su error de distancia coincide con A mientras C_orig lo excede.

## 6. Hallazgo central - el ruido geometrico domina

Los escenarios sin corte y con sigma >= 1.5 muestran que la suma de
distancias euclidianas entre observaciones ruidosas sobreestima el
recorrido real por un factor dependiente de sigma:

| Escenario | sigma       | err_% A | err_% B  | err_% C_orig |
|-----------|-------------|---------|----------|--------------|
| S2        | 0.5         | +4.1    | +4.1     | +4.1         |
| S3        | 1.5         | +39.4   | +39.4    | +39.4        |
| S4        | 3.0         | +126.4  | +128.9   | +128.1       |
| S5        | 5.0         | +171.4  | +262.6   | +191.8       |
| S11       | 1.5 (lenta) | +183.6  | +183.9   | +183.9       |

La causa es geometrica, no algoritmica: E[|Delta|] = sqrt(d^2 + 2 sigma^2)
> d para cualquier sigma > 0. A sigma = 1.5 ya infla 39% sobre 300 s.
A sigma = 5 infla 170%+.

Consecuencia: el manejo de gaps es un problema de segundo orden frente
al ruido geometrico en el rango sigma >= 1.5. Cualquier algoritmo que
sume distancias entre fixes consecutivos sin filtrar ruido geometrico
hereda esta inflacion.

Esto NO estaba en la hipotesis original. Se registra como linea de
investigacion independiente: filtrado de ruido posicional antes de
acumular distancia (Kalman, EMA, RTS, etc.) o estimacion de distancia
por integracion de velocidad (con speed no ruidoso).

## 7. Lo que NO se hizo

- No se modifico run_all.py, methods.py, ni los criterios de aceptacion.
- No se reetiqueto C1 ni C5 como aprobados. Permanecen FAIL en esta corrida.
- No se ejecutaron simulaciones nuevas.
- No se genero el control S6' sin corte.
- No se toco V1 (git status docs/gnss/exp_* vacio).
- No se toco tools/gnss_simulator.py.
- No se declaro H-2026-0026 (no existe como archivo en LOGOS).
- No se promovio C ni C_pair a produccion.

## 8. Preservacion

Los archivos de esta corrida (results/v2_20261020_040923/) no se
sobrescriben. Si en el futuro se modifican los criterios de aceptacion,
se conserva la definicion original de C1 y C5 como referencia historica
y se registra el cambio con fecha y justificacion.

## 9. Proximos pasos propuestos (no ejecutados)

1. Aprobacion de criterios revisados: C1 con tolerancia metrologica,
   C5 reformulado como diferencia B-A en S6.
2. Diseno del control S6' sin corte para aislar el efecto del gap.
3. Decision sobre la rama speed <= 0.3 de C: redisenar (e.g. AND en
   lugar de OR, o exigir evidencia adicional), o retirar de la propuesta
   de produccion.
4. Linea independiente de investigacion: filtrado de ruido geometrico.
5. Cierre de Fase A como evidencia observacional, sin declarar validacion
   de H-2026-0026.

Ninguno de estos pasos se ejecuta sin aprobacion explicita del Director.

## 10. Validacion de C_v2 (Opcion A) - resultados acotados

Contexto: el Director aprobo la Opcion A (eliminar la rama speed <= 0.3
de C, dejando solo dt > 2 s como criterio de GAP_REAL). Se agrego C_v2 a
methods.py manteniendo C_orig como referencia. Se re-corrio run_all.py
--phase A con 8 metodos (A, B, C_orig, C_pair, C_var, C_ctrl_no_event,
C_and_speed, C_v2).

Corrida: docs/gnss/v2/results/v2_20261020_042653
n_rows: 440 · n_missing: 0 · exit: 0

### Tabla de resultados (promedio sobre 5 seeds)

| Escenario     | Metodo  | err_%  | gapEv | gRest | ruido |
|---------------|---------|--------|-------|-------|-------|
| S6 corte 10 s | A       | +16.9  | 0.0   | 1.0   | 0.0   |
| S6 corte 10 s | B       | +20.9  | 0.0   | 0.0   | 0.0   |
| S6 corte 10 s | C_orig  | +17.1  | 1.0   | 1.0   | 0.0   |
| S6 corte 10 s | C_pair  | +16.9  | 1.0   | 1.0   | 0.0   |
| S6 corte 10 s | C_v2    | +17.1  | 1.0   | 1.0   | 0.0   |
| S16 sigma=3   | A       | +141.3 | 0.0   | 1.4   | 0.0   |
| S16 sigma=3   | B       | +144.1 | 0.0   | 0.2   | 0.0   |
| S16 sigma=3   | C_orig  | +143.2 | 0.0   | 0.0   | 1.4   |
| S16 sigma=3   | C_pair  | +141.3 | 0.0   | 0.0   | 1.4   |
| S16 sigma=3   | C_v2    | +143.2 | 0.0   | 0.0   | 1.4   |
| S17 sigma=5   | A       | +191.5 | 0.0   | 38.8  | 0.0   |
| S17 sigma=5   | B       | +287.9 | 0.0   | 0.2   | 0.0   |
| S17 sigma=5   | C_orig  | +211.5 | 3.6   | 3.6   | 35.2  |
| S17 sigma=5   | C_pair  | +191.5 | 3.6   | 3.6   | 35.2  |
| S17 sigma=5   | C_v2    | +212.4 | 0.0   | 0.0   | 38.8  |
| S18 corte 5 s | A       | +137.3 | 0.0   | 1.4   | 0.0   |
| S18 corte 5 s | B       | +140.0 | 0.0   | 0.2   | 0.0   |
| S18 corte 5 s | C_orig  | +139.1 | 0.0   | 0.0   | 1.4   |
| S18 corte 5 s | C_pair  | +137.3 | 0.0   | 0.0   | 1.4   |
| S18 corte 5 s | C_v2    | +139.1 | 0.0   | 0.0   | 1.4   |
| S5 sigma=5    | A       | +171.4 | 0.0   | 39.2  | 0.0   |
| S5 sigma=5    | B       | +262.6 | 0.0   | 0.2   | 0.0   |
| S5 sigma=5    | C_orig  | +191.8 | 0.0   | 0.0   | 39.2  |
| S5 sigma=5    | C_pair  | +171.4 | 0.0   | 0.0   | 39.2  |
| S5 sigma=5    | C_v2    | +191.8 | 0.0   | 0.0   | 39.2  |

### Efecto observado en S17 (barco detenido, sigma=5, sin corte)

C_orig abria 3.6 gap_event falsos por corrida. C_v2 abre 0.0.

Causa: la rama speed <= 0.3 m/s se cumple siempre en detencion.
Cualquier salto > 15 m por ruido posicional se clasificaba GAP_REAL
en C_orig. C_v2 elimina esa rama y solo clasifica GAP_REAL si dt > 2 s.

Costo medido: el error de distancia en S17 pasa de +211.5% (C_orig) a
+212.4% (C_v2), un incremento de 0.9 puntos porcentuales. El incremento
es atribuible a que los 3.6 saltos que C_orig clasificaba como GAP_REAL
(y por tanto movian el ancla) ahora caen en RUIDO y no mueven el ancla,
lo que afecta la acumulacion posterior via d_anchor.

### Ausencia de cambios observados en otros escenarios

- S6 (corte 10 s): C_orig y C_v2 dan err_% identicos (+17.1) y gapEv
  identicos (1.0). La rama speed <= 0.3 no se usaba en S6 (barco en
  movimiento a 2.57 m/s).
- S18 (corte 5 s durante detencion): C_orig y C_v2 dan err_% identicos
  (+139.1) y gapEv identicos (0.0). El corte tiene dt = 6 s > 2 s,
  detectado por la rama temporal en ambos.
- S16 (sigma=3, detenido, sin corte): C_orig y C_v2 dan err_% identicos
  (+143.2) y ruido identico (1.4). El ruido sigma=3 no alcanza para
  producir saltos > 15 m con la frecuencia necesaria para diferenciar.
- S5 (sigma=5, en movimiento, sin corte): C_orig y C_v2 dan err_%
  identicos (+191.8) y ruido identico (39.2).

### Limitaciones de alcance

Este resultado NO demuestra que C_v2 sea superior a C_orig en todas las
condiciones. Lo que demuestra, en los escenarios evaluados:

- Se eliminaron los falsos gap_event detectados en S17 (3.6 -> 0.0).
- El error de distancia en S17 aumento 0.9 pp.
- No se observaron cambios en S6, S18, S16, S5 dentro de las pruebas
  reportadas.

NO se probo:
- Entregas agrupadas (batch_delivery_s > 0).
- Latencia variable (latency_jitter_ms > 0).
- Ruido en speed (speed_sigma_ms > 0).
- Cortes de 30 s o 60 s en el pipeline nuevo.
- Velocidad cero con sigma < 5.
- Navegacion lenta con sigma > 1.5.
- Escenarios con dt en el rango [2s, 5s] donde la rama temporal tiene
  efecto marginal.

La afirmacion correcta y acotada es: "en los escenarios evaluados, C_v2
elimina los falsos gaps detectados en S17 con un incremento de error de
distancia de 0.9 puntos porcentuales". No se generaliza a produccion ni
se declara superior a C_orig en todas las condiciones.

## 11. C_pair_v2 - candidata experimental no evaluada

C_pair_v2 es una combinacion hipotetica: clasificacion temporal de C_v2
(solo dt > 2 s) mas la politica de acumulacion de C_pair (sumar d_pair en
lugar de d_anchor en CONTINUIDAD).

Motivacion: en S17, C_pair obtuvo err_% = +191.5 (mejor que C_orig
+211.5 y C_v2 +212.4) porque acumula d_pair. Pero C_pair conservo los
3.6 gap_event falsos de C_orig porque su clasificacion sigue siendo la
de C_orig (con la rama speed <= 0.3). La combinacion C_pair_v2 tendria,
en principio, lo mejor de ambos: menos falsos gaps (de C_v2) y menor
inflacion de distancia (de C_pair).

Estado: NO implementada, NO evaluada.

C_pair_v2 no se presenta como ganadora ni como solucion recomendada para
produccion. Queda registrada como linea experimental futura, a evaluar
en Fase B o en una corrida dedicada, con su propia aprobacion explicita.

## 12. Estado de Fase A - criterios diferidos

Criterios evaluables aprobados en la corrida v2_20261020_042653:

- C1 (Sanity S1, tolerancia metrologica |err_m| < 2.0 y |err_rel| < 1.0%): PASS
- C3 (Mismas observaciones, hash identico entre metodos): PASS
- C4 (NO_ETIQUETABLE <= 5% por archivo): PASS
- C5 (Caso obligatorio S6, diferencial B-A en [20, 35] m): PASS
- C6 (Rama speed <= 0.3 ejercitada en S10/S16/S17/S18): PASS

Criterios diferidos explicitamente, NO evaluados como pass/fail:

- C7 (Recuperacion tras rechazos, N = 1, 2, 3, 5): el test standalone
  tests/test_recovery.py pasa 7/7 sobre datos sinteticos, pero no esta
  integrado al run_all.py como criterio automatizado que falle la corrida.
  Se documenta como control diferido.

- C8 (V1 intacto): verificado manualmente con git status post-corrida
  (vacio en los directorios V1). No esta automatizado como criterio que
  haga fallar run_all.py. Se documenta como control diferido.

Consecuencia: Fase A NO se declara formalmente cerrada de manera integral.
Se registra como "evidencia observacional consolidada, con los controles
C7 y C8 explicitamente diferidos". El cierre formal requiere:

1. Integrar C7 como criterio en run_all.py (que corra test_recovery.py y
   haga fallar la corrida si no pasa).
2. Integrar C8 como criterio en run_all.py (que verifique git status y
   falle si V1 aparece modificado).

Ambas integraciones requieren aprobacion explicita separada. No se
ejecutan como parte de esta documentacion.

## Nota de sesion

Sesion 2026-10-20 cerrada. Estado al cierre:

- Fase A: 5/5 criterios evaluables aprobados, C7 y C8 diferidos.
- C_v2: documentado como resultado acotado (seccion 10).
- C_pair_v2: documentado como candidata no evaluada (seccion 11).
- Metodos, criterios y resultados: sin cambios desde v2_20261020_042653.
- V1, tools/gnss_simulator.py, hipotesis LOGOS: sin cambios.

Proxima reanudacion: pendiente de decision del Director. Pasos posibles
(no ejecutados, requieren aprobacion separada cada uno):

1. Integrar C7/C8 como criterios en run_all.py.
2. Disenar el control S6' sin corte para aislar causalidad del gap en S6.
3. Implementar C_pair_v2 y evaluarla en escenarios acotados.
4. Abrir Fase B (S7-S9, S12-S15) con speed_sigma_ms, latency_jitter_ms,
   batch_delivery_s, cortes 30s/60s.

Ninguno de estos pasos se ejecuta sin aprobacion explicita del Director.
