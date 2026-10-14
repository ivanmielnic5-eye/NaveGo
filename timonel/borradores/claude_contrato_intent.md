# BORRADOR — CLAUDE: CONTRATO INTENT

**Fecha:** 2026-10-14
**Estado:** BORRADOR.
**Origen:** consulta sobre contrato Intent para A4.

---

## 1. Las tres capas: correctas, pero falta la regla de fusion

- Intent es lo no confiable, MisionConfig lo aprobado y Effective lo
  derivado. No hay redundancia.
- Falta definir la precedencia. Propongo que limits de MisionConfig
  sean techos: el Intent solo puede estrechar, nunca relajar (una
  interseccion). Un pedido de T=30 m con techo de 20 m se rechaza, no
  se corrige.
- "Omitido != default" necesita precision. Un campo omitido puede
  completarse desde MisionConfig solo si esta aprobado_director. Si
  esta sin_definir o propuesto, el resultado es needs_clarification.
  Distinguir "default" (inventado) de "valor aprobado" (trazable).
- Effective lleva procedencia por campo (origen: intent|config,
  estado) y su hash. La identidad del ensayo suma hash(Intent) +
  hash(MisionConfig) + hash(Effective) + version de la fusion.
- El decisor debe aceptar solo el tipo Effective (clases distintas,
  test que lo verifique), para que sea imposible pasarle un Intent
  crudo.

## 2. Cubre A4? Cuatro criticas

- El LLM no convierte unidades. Extrae valor y unidad tal como estan
  escritos; Python normaliza a SI. Asi la extraccion tiene
  coincidencia exacta bien definida y se evita aritmetica del modelo.
- No coordenadas inventadas. Si el texto nombra un lugar ("Puerto
  Esperanza"), el Intent lleva place_name y el sistema lo resuelve
  contra un registro versionado y con hash. Una posicion solo si el
  texto la da explicita. Un lugar desconocido -> codigo
  UNKNOWN_PLACE.
- El esquema excede los datos. F-held solo tiene criterios de llegada
  (distancia, velocidad). requested_constraints y goal.position no
  tienen verdad de terreno en A4 y quedarian en el target sin
  supervision. Reducir A4 a arrival_criteria + goal + issues, y
  diferir las restricciones.
- Definir unsupported vs needs_clarification por una regla medible:
  clarification es lo que una respuesta del usuario podria resolver;
  unsupported es lo que ninguna respuesta haria expresable (por
  ejemplo, ordenes de varios pasos: codigo MULTI_STEP). Textos
  contradictorios: CONTRADICTORY.

## 3. Entrenable a 8B? Si, simplificando el target

- Un JSON de este tamano es entrenable con LoRA (la salida JSON ya la
  aprendio A3). Dos cambios:
  - Sacar clarification del target. El texto libre introduce varianza
    no evaluable. El sistema genera la pregunta desde una plantilla a
    partir de los codigos.
  - status derivado, no declarado. El LLM emite campos mas
    issues: [codigos]; el lado confiable deriva status. Se elimina la
    inconsistencia posible entre status=complete y missing_fields no
    vacio.
- A diferencia de A3, se pasa a generacion, asi que reaparece la
  confusion del parser: tasa de JSON invalido reportada aparte, o
  decodificacion restringida por esquema (por ejemplo, gramaticas
  GBNF o outlines).
- Cobertura: propongo >=100 ejemplos por codigo de issues y balance
  entre complete y no completos.

## 4. Confianza y status

- Si, aplica. El status autodeclarado es una hipotesis, no una
  autorizacion. El verificador recalcula la completitud desde los
  campos.
- El riesgo mas grave no es la abtencion erronea sino el valor
  fabricado: un campo presente que no estaba en el texto. Python
  solo con el Intent no lo detecta. Defensa: anclaje en el texto.
  Cada campo numerico lleva el fragmento fuente (evidence) y el
  verificador comprueba que el numero exista literalmente en el texto
  original (cifras o palabras). No es parsear el contrato, solo
  validar presencia.
- Calibracion de la abtencion, sin confianza autodeclarada: usar las
  log-probs del token de issues o de la secuencia como puntaje
  externo. Metricas: precision/recall de la abtencion, tasa de
  falso-complete (critica), AUROC del puntaje para detectar errores y
  curva riesgo-cobertura con tau elegido solo en val. Hace falta un
  held-out mixto de >=600 items.

## 5. Que cambia en F0? No se rehace; se agrega

- Semantica de techo en limits.
- Valores de procedencia nuevos: intent_usuario, que no equivale a
  aprobado_director. Un valor pedido por el usuario es valido solo
  dentro del envolvente aprobado.
- Efectivo como artefacto derivado con su esquema y hash.
- Una funcion pura fusionar(intent, mision) -> Effective |
  Rechazo(codigos) con propiedades probadas: nunca mas ancho que el
  techo, nunca default, determinista.
- Registro de lugares versionado, fuera de MisionConfig.
- Mientras el supervisor de seguridad este diferido a F3, la
  verificacion del envolvente vive en esta fusion y no deberia crecer
  mas alla de eso.
