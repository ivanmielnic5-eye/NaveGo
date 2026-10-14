# BORRADOR — CLAUDE: AUDITORIA DE ERRORES A3

**Fecha:** 2026-10-14
**Estado:** BORRADOR.
**Origen:** consulta sobre auditoria de errores A3.

---

## 1. Lectura general

- 9 de los 11 errores son falso terminar, la direccion insegura.
- En f2, 5 de 7 no estan en la frontera (v-v_max de 0.95 a 1.94 kn),
  asi que "ruido de borde" no alcanza.
- Los 7 tienen v >= 1.18 kn. Sin denominadores no se sabe la tasa de
  error por banda de v.
- Los dos casos de (T=11, v=1.18, v_max=1.0) y los de (T=17,
  v_max=1.6) repiten combinaciones de parametros con distinta d. Si
  F-held cruza plantillas x combinaciones, el error puede agruparse
  por plantilla o por combinacion. Falta template_id.

## 2. Errores con v = v_max

Cuestiono la observacion 3 ("aprendio la condicion estricta"). Hay
inconsistencia: idx 68 y 286 (v=1.00, v_max=1.0) dicen ir_a, pero idx
50 y 291 (v=1.18, v_max=1.0) dicen terminar. Un umbral monotono en v
no produce ambas cosas. Lo que se ve es frontera difusa con
dependencia de otras variables o de la formulacion, no una regla
estricta.

Dos explicaciones sin descartar:
- Fuera de distribucion: si el generador excluyo |v-v_max| < 0.05, el
  igual nunca se vio y el comportamiento ahi esta indeterminado.
- Etiqueta ambigua: la inclusividad depende de la redaccion ("no
  supere" es <=; "inferior a" es <). Hay que leer los prompts de idx
  68 y 286.

Verificarlo: contar ejemplos de train con |v-v_max| < 0.05, y armar un
estrato de igualdad con ambas redacciones y etiqueta derivada del
operador del texto.

## 3. Puntaje forzado vs generacion

Los desacuerdos estan en los de menor |diff| (1.91; 2.91; 6.28), y los
errores confiados coinciden. El puntaje forzado suma log-probs de toda
la cadena JSON, y la generacion greedy decide en el primer token que
diverge; cerca de 0 pueden diferir.

Con generacion, los conteos serian: f2 = 5 errores (0.983) y
balanceado = 3 (0.995). Las conclusiones no cambian, pero el
comportamiento real es la generacion.

Limitacion del registro: solo se guardan los errores del puntaje
forzado. Los casos con puntaje forzado correcto y generacion
incorrecta son invisibles. Hace falta pred_gen en los 900 items.

Propuesta: reportar ambas metricas, calcular la concordancia sobre
todos los items, y probar un puntaje forzado del primer token
divergente para alinearlo con la generacion. Tratar |diff| < 7 como
estrato inestable.

## 4. Errores lejos del limite

No es "ignora la clausula": 143 de 150 items ir_a de f2 (todos con d<T
y v>v_max) estan bien. Una clausula ignorada daria aprox 0%.

Los lejanos se dividen: idx 1 y 91 (diff 1.9 y 2.9) son inestables;
idx 107, 167 y 293 (diff 17.0; 18.3; 9.4) son malas lecturas
confiadas.

Hipotesis concreta para esos: numeros distractores en el texto (una
clausula irrelevante con un valor mayor que v) usados como v_max. Se
verifica listando los numeros de cada prompt de error: existe otro
numero >= v?

Hipotesis de sobrecorreccion tras 0b: todos los errores tienen v >=
1.0, la banda contra-prior, que A3 sobrerrepresento con terminar
(>=40% de Q1). Si dentro de v >= 1.0 la etiqueta se inclina a terminar
en train, el modelo pudo aprender "v moderada -> terminar". Revisar
P(terminar | v>=1.0, d<T) en train; el AUC global de v puede estar
bien y el condicional no.

## 5. Lo que no estamos viendo

- Denominadores y registro completo de todos los items (con
  template_id, unidad, margenes) para tasas por estrato.
- Tabla cruzada plantilla x combinacion en f2: distingue "plantilla
  mala" de "combinacion mala".
- Los prompts de los 11 errores, que todavia no leimos.
- Una sola semilla: estos 11 errores pueden cambiar con otra.
- Contra el criterio preregistrado (>=0.99 y limite inferior >=0.97
  por familia), f2 en F-held (0.977, Wilson aprox [0.953; 0.989]) no
  lo alcanza, aunque el parametrico si. Conviene declararlo tal cual,
  sin recortar casos despues.
