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

## 12. Estado de Fase A al cierre del 2026-10-20 (corrida v2_20261020_042653)

NOTA HISTORICA: esta seccion registra el estado al momento del primer
cierre de Fase A. Ver seccion 13 para la actualizacion posterior
(corrida v2_20261020_121820, C7 y C8 PASS).

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

## 13. Actualizacion post-cierre (2026-10-20 12:18)

Continuacion de la sesion del 2026-10-20. Se integraron C7 y C8 en
run_all.py como criterios automatizados. Corrida de referencia:
v2_20261020_121820 (n_rows: 440, n_missing: 0, exit code: 0, 7/7 PASS).

### Criterios C7 y C8 - PASS en la corrida de referencia

- C7 (Recuperacion tras rechazos, N = 1, 2, 3, 5): PASS
  Detail: test_recovery.py exit 0 (corrido como subprocess desde
  run_all.py, cwd=REPO_ROOT).

- C8 (V1 intacto): PASS
  Detail: git status --porcelain vacio sobre V1_DIRS (exp_dist,
  exp_ruido_vs_gap, exp_gaps_avance), corrido como subprocess desde
  run_all.py.

C7 y C8 quedaron integrados en run_all.py como criterios automatizados
que hacen fallar la corrida (exit code != 0) si no pasan. Antes de la
integracion, run_all.py devolvia siempre exit code 0.

### Corridas preservadas (historial completo)

- v2_20261020_040923: corrida inicial, 385 filas. C1 y C5 FAIL por
  criterios originales (C1 umbral 0.5m mas fino que el sesgo geodesico
  de -0.864m; C5 err_m_B absoluto sin descontar ruido geometrico base).
- v2_20261020_042653: 440 filas con C_v2 agregado. C1 y C5 reformulados
  PASS. C7 y C8 SKIP (aun no integrados). Es la corrida historica
  referenciada por la seccion 12.
- v2_20261020_121614: 440 filas. C7 SKIP por bug en path
  (BASE/../tests/ inexistente); C8 FAIL por bug en REPO_ROOT
  (3 niveles en lugar de 4, git status desde docs/). Bug introducido
  durante la integracion C.1, no en el codigo original. Preservada
  como evidencia del fallo intermedio.
- v2_20261020_121820: corrida de referencia, 7/7 PASS.

### Estado local vs estado publicado

El commit 7b17426 en origin/v2-track-honesto (rama publicada el
2026-10-20 antes de esta continuacion) contiene el pipeline V2 hasta
la corrida v2_20261020_042653 y C7/C8 como SKIP. Los cambios
posteriores (integracion C7/C8 en run_all.py, corrida
v2_20261020_121820) estan en el working tree local y todavia NO
fueron commiteados ni pusheados.

No atribuir al commit 7b17426 lo que solo existe localmente. La
publicacion de estos cambios requiere un nuevo commit + push, con
aprobacion explicita separada.

## 14. Interacción entre el watchdog y el umbral adaptativo: barrido de duración de cortes

### 14.1 Contexto y origen de los datos
Este apartado documenta un barrido exploratorio (Fase A) sobre la duración de los cortes de señal, ejecutado con 30 semillas (8100 a 8129), navegación recta a 5 nudos y ruido posicional de 1.0 m. 
**Nota sobre trazabilidad:** Los datos absolutos de distancia para cada método no fueron impresos en la salida de la terminal (solo se reportaron las diferencias y el DiD). Los archivos JSON crudos generados durante esta prueba se almacenaron temporalmente en `/tmp` y fueron eliminados. Para auditar los valores absolutos, será necesario volver a ejecutar el script de barrido con persistencia de datos.

### 14.2 Tabla de resultados observados
Los resultados reportados (en metros) son:

| Duración del corte | % detección visual (watchdog B) | B pierde (S6'-S6) | DiD (B-A) | Observación |
| :--- | :--- | :--- | :--- | :--- |
| 2 s | 0% | +1.09 | +0.03 ± 0.08 | Falla el umbral y el watchdog. |
| 5 s | 0% | +2.12 | +11.57 ± 2.80 | Falla el umbral y el watchdog. |
| 10 s | 0% | +4.35 | +28.32 ± 0.39 | Falla el umbral y el watchdog. |
| 14 s | 0% | +5.72 | +38.59 ± 0.58 | Falla el umbral y el watchdog. |
| 16 s | **100%** | +6.63 | +43.48 ± 0.50 | El watchdog detecta el gap, pero el filtro suma la distancia. |
| 20 s | **100%** | +8.20 | +53.75 ± 0.34 | El watchdog detecta el gap, pero el filtro suma la distancia. |
| 30 s | **100%** | +12.15 | +79.39 ± 0.55 | El watchdog detecta el gap, pero el filtro suma la distancia. |

### 14.3 Hipótesis de desacople: Detección visual vs. Contabilización de distancia
El hallazgo central sugiere una inconsistencia de diseño entre dos mecanismos que operan de forma independiente en el método B:
1. **El watchdog** (basado en `receivedAt`) abre un `gap_event` cuando el intervalo entre recepciones supera los 15 segundos. Esto explica por qué el porcentaje de detección pasa de 0% a 100% en el corte de 16s.
2. **El umbral adaptativo de `processFix`** (basado en `measuredAt`, velocidad y precisión) evalúa el salto geométrico del fix. 

Para una embarcación a velocidad constante, el desplazamiento durante el corte crece como \(v \cdot \Delta t\). Sin embargo, el umbral adaptativo de B se calcula como `max(15, speed * dt * 2.0 + accuracy * 3.0)`. Al tener un factor multiplicador por 2.0 sobre la velocidad y el tiempo, el umbral crece el doble de rápido que el salto real. Por lo tanto, **el salto queda por debajo del umbral y es aceptado**, sumando la distancia no observada, aun cuando visualmente el watchdog haya detectado y dibujado la interrupción.

### 14.4 Comprobaciones necesarias antes de generalizar
No se debe afirmar que C_v2 es robusto frente a entregas irregulares hasta tanto:
- Se verifique que la implementación de C_v2 utilice estrictamente `measuredAt` en su criterio temporal (`dt > 2s`) y no `receivedAt`.
- Se diseñen y prueben escenarios con latencia variable (`latency_jitter_ms`) y entregas agrupadas (`batch_delivery_s`) que pongan a prueba esta distinción.

### 14.5 Limitaciones de este barrido
- Solo se evaluó una trayectoria recta a 5 nudos con ruido posicional gaussiano de 1.0 m.
- No se aplicaron controles emparejados con latencia o pérdida de paquetes.
- Los resultados demuestran un comportamiento en este simulador específico y no se extrapolan automáticamente a todas las condiciones de navegación real.

## 15. Implementación exploratoria del modelo de ruido AR(1)

### 15.1 Contexto y motivación
El análisis de tracks reales (velero y lancha) reveló que la autocorrelación de los errores GNSS tiene memoria temporal (cercana a 0.95 en el track del velero Nola), a diferencia del modelo IID (ruido blanco) que utilizaba el simulador originalmente. Para acercar el laboratorio a la realidad sin romper la retrocompatibilidad, se modificó `tools/gnss_simulator.py` para aceptar un parámetro opcional `noise_model` ("IID" o "AR1") y `noise_rho`.

### 15.2 Resultados de la validación empírica
Se ejecutó una simulación de 300 observaciones (1 Hz) para contrastar ambos modelos con una semilla fija y un σ configurado de 1.0 m.

| Configuración | Autocorrelación observada | Desviación estándar observada |
| :--- | :--- | :--- |
| IID, σ = 1.0 m | -0.011 | 0.983 m |
| AR(1), ρ = 0.95 | 0.924 | 0.821 m |

### 15.3 Precisión estadística y límites del resultado
- **Autocorrelación:** El modelo AR(1) demuestra empíricamente una dependencia temporal fuerte, coherente con la memoria del ruido real. El valor observado (0.924) se encuentra dentro del margen de error estadístico esperado para 300 muestras con un ρ teórico de 0.95.
- **Desviación estándar:** La expectativa teórica indicaba que la desviación estándar (con la innovación escalada por \(\sigma_\eta = \sigma\sqrt{1-\rho^2}\)) debía estabilizarse cerca de 1.0 m. El valor observado fue 0.821 m. Esta discrepancia podría estar asociada al régimen transitorio (inicialización en cero del estado AR-1), pero **esta explicación no ha sido verificada matemáticamente en esta corrida**. Se registra la diferencia como un hallazgo pendiente de calibración y auditoría del generador de ruido.
- **Alcance:** La incorporación de AR(1) dota al laboratorio de una herramienta configurable para pruebas de estrés con ruido temporalmente correlacionado. No se declara que el simulador en su conjunto esté "validado industrialmente" ni que AR(1) sea el único modelo universal del error GNSS.
