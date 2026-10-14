# BORRADOR — CLAUDE: OBSERVACION DE RESULTADOS A3

**Fecha:** 2026-10-14
**Estado:** BORRADOR.
**Origen:** consulta sobre resultados A3.

---

## 1. Que observo

- El SFT sale perfecto en todo lo parametrico: 1.000 en train, val,
  interp (600) y extrap (400). La unica imperfeccion en bancoA3 es
  test_balanceado: 0.993 (596/600, 4 errores, prediccion 300/300).
- En F-held, F1 se sostiene (1.000) y F2 baja a 0.977 (293/300). Su
  Wilson 95% es [0.953; 0.989]; queda por debajo de 0.99 y de un
  limite inferior de 0.97.
- Inferencia aritmetica: con acc_term 1.000, acc_ir 0.953 y prediccion
  157 T / 143 I, F2 tiene 150 items terminar y 150 ir_a, y los 7
  errores son todos falso terminar, el tipo que habiamos definido como
  error critico.
- P-text: 1.000 en bancoA3 y en fheld_f1, pero 0.500 exacto en
  fheld_f2. P-struct: 1.000 en todo.
- La base saca 0.17-0.25 en bancoA3 y 0.033 en fheld_f1.

## 2. Lo que destaco

- La direccion del error del SFT se invirtio. En 0b el sesgo era hacia
  ir_a (fallar en contra-prior); ahora los 7 errores son hacia
  terminar. Los errores aparecen solo en F2 con formulaciones
  retenidas, no en F1.
- P-text rinde 0.500 exacto, que coincide con un predictor constante
  en un set balanceado 150/150. Un parser que ignorara la velocidad
  sacaria mas (aprox 0.75-0.83, segun los cuadrantes del set). Un
  valor tan limpio sugiere fallo de parseo con valor por defecto, o un
  error sistematico de conversion de unidades, no una limitacion
  gradual de regex.
- La base esta por debajo del azar de forma sistematica. Con 0.033 en
  F1, no es "no sabe": esta anticorrelacionada (invertir daria aprox
  0.97). En A2 habia dado 0.310. Su comportamiento cambia entre
  experimentos, no es referencia estable.
- P-struct no parsea el prompt: usa v_max interno. Es un techo de
  etiquetas por construccion.

## 3. Lo que falta o no esta claro

- Contra-prior, placebo, pares y extrap de v_max: no aparecen en el
  reporte. Es justamente lo que 0b detecto como fallo; sin esos
  estratos no se sabe si el sesgo se corrigio. No se si
  test_balanceado los cubre.
- Como se etiqueto F-held. Si los parametros se inyectaron por
  programa en plantillas, la etiqueta es correcta por construccion. Si
  Perplexity genero textos libres con la etiqueta derivada de su spec,
  hace falta la anotacion ciega de acuerdo texto-spec. Los 7 errores
  del SFT podrian ser items ambiguos.
- Distribucion de unidades y plantillas en F-held, y en cuales caen
  los 7 errores del SFT y los fallos de P-text.
- P-text: no se sabe si se congelo tras llegar a >=99% en F-dev, ni si
  F-dev incluia las variantes de velocidad que F-held usa.
- Tasa de fallos de parseo y valor por defecto de P-text.
- Compuertas restantes: concordancia de generacion con puntaje forzado
  e invariancia al orden de acciones. Tampoco se ve errores.jsonl, el
  arbol, A2 congelado, el hibrido ni McNemar.
- Una sola semilla. Los 7 errores podrian variar entre semillas.
- Los 4 errores de test_balanceado: no se sabe si estan cerca de los
  umbrales.

## 4. Diferencia SFT vs P-text en fheld_f2

- El hecho: 0.977 contra 0.500, es decir 47.7 puntos, con P-text sin
  diferencia en F1. La brecha aparece solo en F2, lo que localiza el
  problema en como se expresa la velocidad en el texto retenido.
- Hipotesis, sin verificar: los dos sistemas podrian estar fallando
  por el mismo motivo, las unidades de velocidad (nudos vs m/s). Un
  valor en m/s tiene numero mas chico que en nudos; leerlo sin
  convertir daria "v baja", es decir falso terminar, justo la
  direccion de los 7 errores del SFT. P-text, si no convierte,
  quedaria cerca del azar.
- Antes de leerlo como ventaja de interfaz: hace falta saber si el
  0.500 es un bug o un limite de regex, y si el protocolo de congelado
  se cumplio. El criterio Delta >= 10 puntos se cumple en bruto, pero
  su alcance es "relativo a esta distribucion de formulaciones y a
  este P-text".
- El SFT no es inmune: su 2.3% de errores esta concentrado y en la
  direccion insegura.
