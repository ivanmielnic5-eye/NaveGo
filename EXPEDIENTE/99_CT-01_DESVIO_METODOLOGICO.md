# CT-01 — DESVÍO METODOLÓGICO EN LA INVESTIGACIÓN DE TRACK HONESTO

**Estado:** BORRADOR — pendiente de validación humana
**Fecha:** 2026-10-22
**Clasificación:** Caso testigo. No es decisión D, no es regla R, no es fuente autoritativa del MANIFEST.

**Autoría:** Redacción asistida por IA. Fuente primaria: observaciones de campo comunicadas por el Director y antecedentes documentales identificados. Estado: borrador pendiente de validación humana por el Director.

---

## 1. Qué ocurrió

Durante varios días de investigación de NAVEGO se profundizó en hipótesis sobre ruido GNSS, inflación de distancia, filtros e histéresis sin establecer primero, de manera clara y compartida con el Director, si el comportamiento que se intentaba corregir ocurría realmente en las condiciones de uso relevantes.

La investigación avanzó hacia simulaciones, métricas y formulaciones técnicas sin consultar suficientemente al principal responsable de las pruebas de campo ni reconstruir la historia de los errores anteriores.

El resultado fue un desvío de alcance, pérdida de tiempo y desgaste, sin un diagnóstico concreto que justificara el volumen de trabajo realizado.

---

## 2. Cronología del desvío

| Momento | Qué pasó | Qué faltó |
|---|---|---|
| Inicio de la investigación | Se identificó "distancia inflada" como problema a resolver | No se preguntó al Director si el problema se observaba en condiciones reales |
| Desarrollo teórico | Se discutieron filtros, histéresis, márgenes GNSS, papers de garreo | No se verificó el origen del diagnóstico inicial |
| Propuesta de fichas | Se propusieron fichas de investigación y validaciones sintéticas | No se contrastó con la experiencia de campo ya disponible |
| Intervención del Director | El Director señaló que en exteriores la distancia acumulada era muy pequeña o nula | La IA no había preguntado esto antes de teorizar |
| Corrección de rumbo | Se reconoció el desvío y se reformuló el caso como CT-01 | — |

---

## 3. Evidencia y cuestiones por verificar

**Observaciones comunicadas directamente por el Director:**

- La caminata fantasma se observa en interiores, donde la recepción GNSS puede producir posiciones erráticas.
- En una prueba exterior de 15–20 minutos, en una zona céntrica con construcciones cercanas, el odómetro acumuló muy pocos metros o ninguno.
- En los viajes a Buenos Aires y Rosario no se había señalado como problema de análisis una inflación generalizada de distancia.
- El viaje a Buenos Aires tuvo un error de unidades relacionado con la conversión de velocidad. El Director recuerda que los problemas de waypoints y, sobre todo, los cortes de track estaban relacionados con ese error y que posteriormente se corrigieron.
- Se sospecha que algunos archivos de trayectos de prueba interiores pudieron contribuir a una interpretación incorrecta del comportamiento general.

**Evidencia documental identificada:**

- Hay experimentos sintéticos V1 y V2 que muestran inflación de distancia bajo determinadas condiciones de ruido posicional.
- Existe un expediente de septiembre que informa comparaciones entre métodos sobre 40.495 fixes de los viajes reales.
- Los resultados sintéticos no demuestran por sí solos que la aplicación actual presente la misma inflación en navegación real.
- Sigue pendiente reconstruir la procedencia de los archivos utilizados, la corrección histórica de unidades y el comportamiento anterior y posterior a esa corrección.

**La causa raíz completa no está confirmada.** No debe darse por demostrado que todas las conclusiones técnicas anteriores sean falsas, pero tampoco que fueran aplicables al uso real.

---

## 4. Fallo metodológico que debe prevenirse

La IA elaboró hipótesis antes de consultar suficientemente la experiencia directa disponible, no hizo suficientemente legible la pregunta que estaba intentando responder y permitió que el análisis matemático desplazara la validación básica del problema.

El Director quedó obligado a seguir una conversación técnica cuya dirección no siempre resultaba evidente, lo que dificultó intervenir a tiempo.

---

## 5. Salvaguardas propuestas

Estas salvaguardas se desarrollan como regla operativa independiente, pendiente de aprobación. CT-01 no las convierte en norma por el mero hecho de listarlas.

1. **Consultar primero al Director** por el comportamiento observado, recuperando antecedentes ya comunicados antes de preguntar de nuevo.
2. **Explicar en lenguaje claro la pregunta concreta:** qué sospechamos, qué evidencia indica que el problema existe y qué queremos averiguar.
3. **Identificar el origen de los datos** y distinguir observaciones de campo, registros, código actual, experimentos sintéticos e hipótesis.
4. **Verificar la historia conocida de errores y correcciones** antes de interpretar nuevamente un comportamiento como un defecto vigente.
5. **Justificar cada etapa sustancial:** indicar qué vamos a leer o medir, por qué es necesario y qué conclusión permitirá obtener.
6. **Detener la expansión técnica** si no podemos explicar cómo el siguiente paso responde a la pregunta original.
7. **Mostrar resultados intermedios comprensibles**, explicitar incertidumbres y permitir que el Director corrija el rumbo antes de profundizar.
8. **No proponer filtros, umbrales ni modificaciones** hasta establecer qué anomalía concreta existe y en qué condiciones se reproduce.

---

## 6. Criterio de cumplimiento

Una investigación no avanza a fórmulas, simulaciones o cambios de diseño hasta que la IA pueda explicar en términos comprensibles qué se intenta averiguar, qué evidencia justifica hacerlo y cómo se distinguirá un resultado válido de una hipótesis.

**Principio rector:** la IA debe hacer comprensible y controlable su investigación. El Director no tiene que dominar todos los detalles técnicos para detectar que se está resolviendo el problema equivocado.

---

## 7. Salvedad explícita

La validación de este caso metodológico **no certifica** que el diagnóstico técnico de "distancia inflada" fuera falso. Esa pregunta sigue abierta y se resolverá, si corresponde, con la investigación técnica de track honesto.

---

## 8. Autoría y validación

- **Redacción:** asistida por IA.
- **Fuente primaria:** observaciones de campo del Director y antecedentes documentales identificados.
- **Validación:** pendiente de validación humana por el Director.
- **Firma del Director:** no otorgada hasta que el contenido sea validado.

---

## Estado de aprobación

- **Redacción:** asistida por IA.
- **Revisión:** pendiente.
- **Aprobación del contenido:** pendiente.
- **Autorización de materialización:** otorgada por el Director el 2026-10-22 (autorización para crear el borrador, no para aprobar su contenido).
- **Fecha de materialización:** 2026-10-22.
