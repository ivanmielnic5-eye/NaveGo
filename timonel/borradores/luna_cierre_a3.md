# BORRADOR — LUNA: CIERRE A3 Y REFERENTES A4

**Fecha:** 2026-10-14
**Estado:** BORRADOR.
**Origen:** consulta sobre cierre de auditoria A3 y referentes.

---

## 1. A3: la hipotesis estructural es plausible, pero no esta
## demostrada

Los datos respaldan una asociacion entre presencia del conector y
menor tasa de error, pero no alcanzan para concluir que el modelo
aprendio una heuristica estructural especifica.

- conector=True: 0/50 errores.
- conector=False: 7/250 errores, concentrados en cinco formulaciones.

La unidad de analisis importa: los 300 items no son necesariamente
independientes, porque comparten formulaciones. Ademas, con solo
diez formulaciones con conector, observar cero errores no demuestra
que ese recurso garantice el comportamiento.

Correccion a la conclusion: "Los errores residuales se concentran en
formulaciones sin conector; la hipotesis de una heuristica estructural
queda pendiente de una prueba controlada". Tampoco llamaria "ruido" a
los errores sin demostrar que carecen de estructura.

Para verificar la hipotesis: generar pares equivalentes que difieran
unicamente en el conector, con valores numericos y resto de la
redaccion controlados. Comparar por par y por formulacion.

## 2. Referentes para A4

Los referentes son adecuados. Para entorno local, priorizar tres:

- Outlines + Pydantic: buena opcion inicial si la inferencia se
  realiza directamente con Transformers. Outlines admite modelos
  locales y generacion restringida por esquemas; Pydantic valida.
- XGrammar: alternativa para decodificacion restringida,
  especialmente si despues se sirve el modelo con vLLM.
- Restricciones nativas de llama.cpp: opcion si el modelo termina
  desplegandose con ese runtime.

No anadiria DSPy, Instructor o varias capas de orquestacion a A4 por
ahora. Primero resolver extraccion, validacion y medicion.

## 3. Outlines + Pydantic es la recomendacion?

Si, como primera implementacion de referencia, no como decision
irreversible.

Separacion:
- Outlines restringe que estructuras puede generar el modelo.
- Pydantic valida tipos, campos, rangos y coherencia.
- La logica de A4 verifica si esos valores representan correctamente
  el texto original.

La generacion restringida garantiza conformidad estructural, pero no
garantiza que el modelo haya interpretado correctamente el lenguaje
natural.

Usaria un unico modelo Pydantic como fuente del esquema, con campos
desconocidos prohibidos y validadores explicitos. Antes de integrarlo
al entrenamiento LoRA, prueba minima de compatibilidad con la version
concreta de Transformers/Unsloth. Si el despliegue previsto es vLLM,
comparar tambien su generacion estructurada nativa.

## 4. Que documentar antes de cerrar A3

Registrar explicitamente que la hipotesis estructural es una
interpretacion pendiente de prueba; que el criterio preregistrado no
se alcanzo; y que los siete errores estan concentrados en cinco
formulaciones.

Conservar las discrepancias entre puntuacion forzada y generacion
libre como resultados separados. No seleccionar una metrica
retrospectivamente para mejorar la conclusion.

## 5. Antes de arrancar A4

Riesgo principal: trasladar el error de A3 a un campo estructurado.
Un JSON valido puede contener un v_max incorrecto, intercambiar v y
v_max o inventar un limite ausente.

Por eso, A4 debe distinguir restriccion ausente, restriccion presente
y restriccion ambigua. Una mision F1 sin condicion de velocidad no
equivale a una F2 en la que el modelo olvido extraerla. No deben
compartir el mismo null sin informacion adicional.

Evaluar extraccion de campos, unidades, presencia de restricciones,
abtencion y exactitud semantica por separado. La conjuncion de
condiciones seguira a cargo de Python.

Recomendacion final: cerrar A3 con una conclusion descriptiva,
congelar el contrato Intent y disenar A4 para medir extraccion
semantica. La generacion restringida resuelve la forma del objeto; el
experimento debe demostrar que resuelve correctamente su contenido.
