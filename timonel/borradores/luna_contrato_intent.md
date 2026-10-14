# BORRADOR — LUNA: CONTRATO INTENT

**Fecha:** 2026-10-14
**Estado:** BORRADOR.
**Origen:** consulta sobre contrato Intent para A4.

---

## 1. Decision: B, con una tercera capa

Recomiendo Intent -> verificacion y resolucion -> MisionConfig
efectiva.

No es una conversion directa: el verificador combina la intencion
validada con la configuracion aprobada de la mision, comprueba
consistencia y resuelve que informacion falta. Nunca debe inventar
valores nauticos ausentes.

Separo tres objetos:

- Intent: lo que el usuario pidio.
- MisionConfig: parametros de mision aprobados y trazables.
- EffectiveMissionConfig: configuracion concreta, validada e
  inmutable que consume el decisor.

## 2. Campos de Intent

Contrato minimo para A4:


- status: enum cerrado (complete, needs_clarification, unsupported).
- requested_constraints: restricciones tipadas, no texto libre.
- missing_fields: campos que faltan para ejecutar la mision.
- clarification: pregunta concreta cuando no pueda resolverse una
  ambiguedad.
- mision_id, texto original y fecha: metadatos del sistema, fuera de
  la salida generada por el LLM.
- La version del esquema la impone el sistema; no confiar en la
  declarada por el modelo.

Los null son marcadores de diseno. No todos los campos tienen que ser
obligatorios si una configuracion aprobada ya proporciona el valor.

## 3. Relacion con MisionConfig

El verificador no debe convertir automaticamente lo omitido en
defaults. Para cada campo, debe distinguir entre peticion explicita,
valor aprobado heredado, valor pendiente y conflicto.

La procedencia y el estado se asignan en el lado confiable, no los
decide el LLM. Si la intencion contradice una restriccion obligatoria
o deja un dato critico sin resolver, el sistema solicita aclaracion o
rechaza la ejecucion.

## 4. no_entendi: mejor un estado estructurado

Evitaria no_entendi como campo libre aislado. El enum status y
clarification cubren la salida del interprete; el verificador
registra codigos propios, como missing_required_field,
ambiguous_value, invalid_unit o constraint_conflict.

Asi se pueden medir categorias de fallo sin depender de interpretar
explicaciones en lenguaje natural.

## 5. Confianza: no usarla como autorizacion

No confiaria en un confidence: 0.93 autodeclarado por el LLM para
habilitar una maniobra. La confianza verbal no equivale necesariamente
a probabilidad de correccion; su utilidad debe medirse empiricamente.

Para A4, mediria exactitud semantica, calibracion y abstencion por
separado. El verificador calcula hechos objetivos (campos ausentes,
unidades invalidas, restricciones incompatibles); una estimacion
probabilistica de confianza solo se incorpora si se calibra en datos
independientes.

Decision para A4: congelar primero el esquema de Intent y su conjunto
de referencia. Entrenar al LLM para producir ese contrato, sin
permitirle generar directamente la configuracion ejecutable.
