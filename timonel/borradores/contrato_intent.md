# BORRADOR — CONTRATO INTENT (A4)

**Fecha:** 2026-10-14
**Estado:** BORRADOR. Consolida propuestas de Luna y Claude.
**Referencias:** borradores luna_contrato_intent.md,
claude_contrato_intent.md.

---

## 1. Los tres objetos

Hay tres objetos distintos. No se mezclan.

**Intent.** Lo que el usuario pidio. Lo produce el LLM. NO es
confiable. Puede tener campos faltantes, valores fabricados o
ambiguedades. Es una hipotesis, no una orden.

**MisionConfig.** Parametros de mision aprobados y trazables. Los
produce el Director o el sistema. Confiable. Con procedencia y estado
por campo. Hash canonico (F0).

**EffectiveMissionConfig (Effective).** Configuracion concreta,
validada e inmutable que consume el decisor. Se deriva de fusionar
Intent con MisionConfig. Con procedencia por campo y hash.

## 2. Quien produce cada cosa

| Objeto | Produce | Consume |
| --- | --- | --- |
| Intent | LLM interprete | Verificador |
| MisionConfig | Director / sistema | Fusion |
| Effective | Fusion (verificador) | Decisor |

**Regla clave:** el decisor acepta SOLO Effective. No acepta Intent
crudo. Clases distintas, con test que lo verifique.

## 3. Separacion de A4

A4 entrena al LLM para producir Intent a partir de texto. NO entrena
la fusion. La fusion es Python puro.

A4 mide el INTERPRETE, no el decisor. Esa es la diferencia con A3.

**Alcance reducido de A4:** solo los campos que tienen verdad de
terreno en el banco:
- goal.position (aunque sea place_name)
- goal.arrival_criteria (distance, speed)

**Fuera de A4 (diferido):**
- requested_constraints: no hay verdad de terreno.
- Verificacion de seguridad.
- Fusion con MisionConfig.



## 4. Schema JSON del Intent

El LLM produce exactamente este objeto. Sin texto adicional.

    {
      "goal": {
        "position": {
          "x":          { "estado": "ausente", "value": null, "unit": "m",
                          "evidence": null },
          "z":          { "estado": "ausente", "value": null, "unit": "m",
                          "evidence": null },
          "place_name": { "estado": "ausente", "value": null,
                          "evidence": null }
        },
        "arrival_criteria": {
          "distance": {
            "estado": "presente",
            "value": 15.0,
            "operator": "<",
            "unit": "metros",
            "evidence": "menor que 15.0 metros"
          },
          "speed": {
            "estado": "ausente",
            "value": null,
            "operator": null,
            "unit": null,
            "evidence": null
          }
        }
      },
      "issues": []
    }

Uso indentacion de 4 espacios en lugar de triple backtick para no
romper el heredoc. El ejemplo del campo distance es ilustrativo, no
un valor predeterminado de mision.

**Reglas del schema:**

1. Cada campo lleva `estado` obligatorio. El enum es
   `ausente | presente | ambigua | conflictivo`:
   - ausente: campo examinado, la informacion no esta en el texto.
   - presente: valor extraido con evidencia.
   - ambigua: el texto admite varias interpretaciones. value = null.
   - conflictivo: el texto contiene valores o instrucciones
     incompatibles para el mismo campo. value = null.

   Si el campo es ausente, ambigua o conflictivo: value = null. No
   se inventan valores.

2. El LLM NO convierte unidades. Extrae value y unit tal como estan
   escritos en el texto. Si el texto dice "3 nudos", value=3.0,
   unit="nudos". Python normaliza a SI despues.

3. Cada campo numerico lleva evidence. Es el fragmento del texto
   original que contiene el valor. Sirve para que el verificador
   compruebe que el numero existe literalmente. Evidence reproduce
   el fragmento, no una parafrasis del modelo.

4. goal.position se descompone en tres subcampos atomicos (x, z,
   place_name), cada uno con su propio estado. Si el texto dice
   "navegar a Puerto Esperanza", place_name=presente aunque x y z
   esten ausentes. La resolucion de place_name a coordenadas es
   posterior y no altera lo que decia el texto original.

5. Coordenadas x, z solo si el texto las da explicitas.

6. Clave emitida != estado semantico. El esquema exige las claves.
   Una clave no emitida por el LLM es salida invalida respecto al
   esquema, no equivale a estado=ausente. La fusion nunca debe
   confundir una omision del modelo con permiso para usar defaults.

7. issues es lista de codigos. No texto libre.

## 5. Codigos de issues

Los codigos que el LLM puede emitir:

- missing_distance: el texto no da distancia de llegada.
- missing_speed: el texto no da velocidad maxima.
- ambiguous_value: el texto admite varias interpretaciones.
- conflicting_values: dos valores del texto se contradicen para el
  mismo campo.
- constraint_conflict: contradiccion transversal entre campos.
- unsupported_unit: la unidad no es reconocible.
- unknown_place: el texto nombra un lugar no resoluble.
- multi_step: orden con multiples pasos secuenciales (fuera de A4 v1).
- contradictory: dos partes del texto se contradicen.

Un Intent puede tener varios issues a la vez. Los estados y los
issues conviven: no se reemplazan entre si.

Mapeo contractual estado -> issue:

| Estado del campo | Tratamiento                                                   |
| ---------------- | ------------------------------------------------------------- |
| ausente          | Issue de campo faltante solo si es requerido en ese contexto. |
| presente         | Sin issue por estado; el valor aun debe validarse.            |
| ambigua          | ambiguous_value.                                              |
| conflictivo      | conflicting_values.                                           |

Las contradicciones entre campos se registran ademas como problemas
transversales (constraint_conflict).
## 6. Lo que NO va en el Intent

Segun las criticas de Claude:

- status: derivado por el verificador, no declarado por el LLM.
- clarification: el texto de la pregunta lo genera Python desde una
  plantilla a partir de los codigos.
- confidence: no confiable como autorizacion. Se mide con log-probs
  externamente.
- schema_version: la impone el sistema, no el LLM.
- mision_id, fecha, texto original: metadatos del sistema, fuera de
  la salida del LLM.
- requested_constraints: no hay verdad de terreno en A4.
- coordinate_system: deferido.


## 7. Fusion (conceptual, no implementada todavia)

La fusion toma un Intent y una MisionConfig, y devuelve una
EffectiveMissionConfig o un rechazo con codigos.

**Reglas (propuestas por Claude):**

1. **Techos.** Los limits de MisionConfig son techos. El Intent solo
   puede estrechar, nunca relajar. Un pedido de T=30m con techo de
   20m se RECHAZA, no se corrige.

2. **Omitido != default.** Un campo omitido en el Intent se completa
   desde MisionConfig SOLO si su estado es aprobado_director. Si esta
   sin_definir o propuesto, el resultado es needs_clarification.

3. **Procedencia por campo.** Effective lleva origen (intent|config) y
   estado por cada campo. Hash canonico.

4. **Evidence anchor.** Cada campo numerico lleva el fragmento fuente.
   El verificador comprueba que el numero exista literalmente en el
   texto original.

5. **Funcion pura.** fusionar(intent, mision) -> Effective | Rechazo.
   Nunca mas ancho que el techo. Nunca default. Determinista.

6. **Decisor solo acepta Effective.** Clases distintas, con test que
   lo verifique.

**Lo que NO hace la fusion en A4:**
- No verifica seguridad (diferido a F3).
- No convierte unidades (lo hace Python, no el LLM).
- No inventa valores. Si falta y no esta aprobado, rechaza.

## 8. Relacion con F0

F0 NO se rehace. Se agrega:

- Semantica de techo en limits.
- Procedencia nueva: intent_usuario. No equivale a
  aprobado_director. Un valor pedido por el usuario es valido solo
  dentro del envolvente aprobado.
- Effective como artefacto derivado con esquema y hash.
- Funcion pura fusionar (a implementar en A4 o despues).
- Registro de lugares versionado, fuera de MisionConfig.


## 9. Lo que sigue (fuera de este documento)

1. Implementar el schema como JSON Schema formal.
2. Verificar que el schema JSON formal, los ejemplos etiquetados del
   banco A4 y la regla de fusion preserven las distinciones
   ausente / presente / ambigua / conflictivo.
3. Definir y generar el banco A4 (texto -> Intent).
4. Auditar las etiquetas y los casos limite del banco.
5. Congelar el banco y su manifiesto.

Concluido: la auditoria de los 7 errores de A3 (referencia a
evidencia en EXPEDIENTE/89).

Diferido a v2: candidates[] (alternativas estructuradas para
ambigua). Fuera del alcance de A4 v1.

Fuera de A4 v1: misiones multi_step (bloquean ejecucion).

## 10. Estado

APROBADO. Registrado como D-2026-0011 (2026-10-14). Implementacion,
schema JSON formal, banco A4 y tests quedan como cambios tematicos
posteriores.
