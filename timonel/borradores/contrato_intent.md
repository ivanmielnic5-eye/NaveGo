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
          "x": null,
          "z": null,
          "place_name": null
        },
        "arrival_criteria": {
          "distance": {
            "value": null,
            "unit": null,
            "evidence": null
          },
          "speed": {
            "value": null,
            "unit": null,
            "evidence": null
          }
        }
      },
      "issues": []
    }

Uso indentacion de 4 espacios en lugar de triple backtick para no
romper el heredoc.

**Reglas del schema:**

1. Todos los campos numericos son opcionales. Si no estan en el
   texto, quedan en null. No se inventan.
2. El LLM NO convierte unidades. Extrae value y unit tal como estan
   escritos en el texto. Si el texto dice "3 nudos", value=3.0,
   unit="nudos". Python normaliza a SI despues.
3. Cada campo numerico lleva evidence. Es el fragmento del texto
   original que contiene el valor. Sirve para que el verificador
   compruebe que el numero existe literalmente.
4. Coordenadas solo si el texto las da explicitas. Si el texto
   nombra un lugar ("Puerto Esperanza"), se llena place_name y se
   dejan x y z en null.
5. issues es lista de codigos. No texto libre.


## 5. Codigos de issues

Los codigos que el LLM puede emitir:

- missing_distance: el texto no da distancia de llegada.
- missing_speed: el texto no da velocidad maxima.
- ambiguous_value: el valor es ambiguo ("mas o menos 20").
- unsupported_unit: la unidad no es reconocible.
- unknown_place: el texto nombra un lugar no resoluble.
- multi_step: orden con multiples pasos secuenciales.
- contradictory: dos partes del texto se contradicen.

Un Intent puede tener varios issues a la vez. Puede tener campos
completos y issues simultaneamente (por ejemplo, da distancia pero no
velocidad -> issues: [missing_speed]).

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

- Implementar el schema como JSON Schema formal.
- Definir el banco de A4 (texto -> Intent).
- Congelar el banco antes de entrenar.
- Auditar los 7 errores de A3 antes de entrenar A4.

## 10. Estado

**BORRADOR.** Consolida Luna + Claude. Espera aprobacion del Director
antes de implementar.
