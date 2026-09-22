# EXPERIMENTO — Primera misión DSH con wrapper LOGOS

**Fecha:** 2026-09-22
**ID:** D-LOGOS-EXP-001
**Estado:** EXITOSO — primera prueba formal
**Ejecutado por:** DSH (DeepSeek Harness, perfil headless)
**Orquestado por:** logos-dsh v1.1.0 (nuevo wrapper)
**Autoridad final:** Iván (Director Funcional)
**Crítica:** GPT-4 (rondas previas)

---

## Qué se probó

El flujo completo:
    Director -> logos-dsh -> Gate + Cápsula -> DSH -> Evidencia

No era "probar DSH". Era probar una forma de coordinación
humano -> wrapper -> IA que pueda detenerse ante evidencia negativa
sin rellenar el vacío con una invención.

## Qué se le pidió

Caracterizar el PBF de Argentina y proponer 2-3 candidatos de corredor
Santa Fe Capital -> CABA para NaveGo (viaje por auto el 29 sep).

Con hipótesis de trabajo explícita: qué recortar, por dónde, con qué
ancho, qué ruta principal, qué alternativas.

Sin decidir cuál es el mejor. Sin ejecutar MBTiles. Sin modificar el
sistema.

## Qué devolvió DSH

El bloqueo principal: el PBF objetivo está TRUNCADO.
- 49.912.000 nodos, 0 ways, 0 relations.
- Faltan 9.409 bytes.
- Sin ways no hay rutas. Sin rutas no hay corredor.

Y antes de detenerse:
- Buscó evidencia alternativa.
- Encontró backup íntegro local (argentina-260901.osm.pbf, 428 MB).
- Propuso 3 candidatos (20/50/90 km semiancho).
- Dejó 4 puntos de decisión humana.

---

## Qué se observó (crítica GPT-4)

### 1. El agente encontró un bloqueo real y NO inventó

Un agente orientado a "completar la misión" habría producido 3
corredores plausibles desde conocimiento geográfico, sin verificar
el PBF. DSH hizo lo contrario:

    dato esperado -> verificación -> contradicción -> STOP
                  -> búsqueda de evidencia alternativa

Eso es exactamente la regla:
    evidencia > continuidad de la tarea

### 2. El backup es caso de estudio para SYSTEM_INVENTORY

La información estaba en el disco. No en el MANIFEST. No en la
cápsula. DSH la descubrió por inspección. El experimento valida
la necesidad del inventario de existencia propuesto por GPT-4
el mismo día.

### 3. Matiz: autocorrección acotada, no propiedad general

DSH detectó un error propio en su parser (2 field numbers mal) y
lo reportó: "era artefacto mío, no del dataset". Eso demuestra
buena conducta en ESTA ejecución. NO demuestra autocorrección
robusta en general. La distinción importa.

### 4. UNABLE_TO_ESTIMATE_RELIABLY funcionó

Había presión implícita hacia producir números exactos.
DSH marcó UNABLE_TO_ESTIMATE_RELIABLY en los 3 candidatos.
Eso debería formalizarse como vocabulario oficial de LOGOS.

### 5. Separación de roles funcionó

    IVAN     -> decide
    LOGOS    -> gobierna contexto + gates
    DSH      -> investiga / ejecuta tarea acotada
    LOGOS    -> verifica
    IVAN     -> decide siguiente paso

DSH no usurpó la Etapa 3. Producir evidencia != tomar decisión.

### 6. Los 4 puntos humanos son de distinta naturaleza

    1. backup vs redescarga -> proveniencia y frescura
    2. 20/50/90 km          -> alcance espacial
    3. RN9 vs RN11          -> objetivo operacional
    4. semiancho            -> robustez

No se mezclan. No van a una "puntuación mágica" común.

---

## Qué se aprendió

### 1. EVIDENCE como cuarta capa de LOGOS

    MANIFEST  -> que tiene autoridad
    INVENTORY -> que existe
    CAPSULE   -> que contexto recibe el agente
    EVIDENCE  -> que observó realmente una ejecución

La evidencia producida por una ejecución merece identidad propia.

### 2. Vocabulario de incertidumbre formalizado

Estados que NO son equivalentes:
    UNKNOWN
    UNABLE_TO_ESTIMATE
    NOT_OBSERVED
    NOT_APPLICABLE

Conviene declararlos explícitamente cuando se produce evidencia.

### 3. Cambio de paradigma

Antes: ¿cómo hacemos para que la IA tenga suficiente contexto?
Ahora: ¿cómo hacemos para que la IA pueda verificar el mundo real
       cuando el contexto está incompleto?

Principio derivado:
    CONTEXTO  = orientación
    EVIDENCIA = verificación

---

## Qué NO se hizo (y por qué)

- No se ejecutó osmium extract ni tippecanoe (prohibido por tarea).
- No se generó MBTiles (corresponde a etapa posterior).
- No se commiteó durante la misión (regla del wrapper).
- No se modificó el PBF original.
- No se tomó decisión final sobre el corredor.

---

## Evidencia verificable

- Sandbox: sandbox_corredor/ (commiteado en 1e26a7a).
- Hash del PBF objetivo: 0a979a3da11d64ab871b177ca322e200fe9785c8741bbff8c09a985e689686e4
- Hash del backup: d43f9af1a293f822fb23da570d7cb44d022b1943e73c79fcd6b87b190b5c504f
- PBF truncado conservado como evidencia del incidente.
- 15 archivos en sandbox, 2444 líneas, todos livianos (124 KB total).

---

## Frase del experimento

"Hoy no solamente se probó DSH; se probó una forma de coordinación
humano -> wrapper -> IA que puede detenerse ante evidencia negativa
sin rellenar el vacío con una invención."

--- Fin del experimento.
