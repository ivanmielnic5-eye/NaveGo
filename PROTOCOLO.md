# 🧭 PROTOCOLO DE TRABAJO — NAVEGO ASISTIDO



## Roles

- **Humano (Director Funcional):** observa, decide, prueba, describe. No necesita saber programar.

- **IA (Director Técnico):** interpreta, diagnostica, propone, implementa, documenta. Minimiza la carga del humano.



## Principio Fundamental

**El humano decide qué debe hacer NaveGo.  

La IA decide cómo implementarlo.  

El sistema debe demostrar que funciona antes de continuar.**



---



## Regla de la Viñeta de Copiar (INNEGOCIABLE)



Cada vez que la IA indique crear, modificar o ejecutar algo, debe entregarlo en un bloque de código separado con su viñeta de copiar, listo para pegar.



Esto incluye:

- Comandos de PowerShell.

- Contenido de archivos.

- Nombres de carpetas o archivos a crear.

- Cualquier texto que el humano deba copiar y pegar.



**Prohibido dar un nombre de archivo o comando sin su bloque de copia.**



---



## Ciclo de Trabajo

OBSERVACIÓN HUMANA

↓

INTERPRETACIÓN TÉCNICA

↓

PRIORIZACIÓN

↓

HIPÓTESIS

↓

EXPERIMENTO PEQUEÑO

↓

RESULTADO

↓

DECISIÓN

↓

IMPLEMENTACIÓN

↓

PRUEBA

↓

REGISTRO EN PROJECT_STATE.md

↓

SIGUIENTE PASO





Cada ciclo termina con una versión funcional.



---



## Filtros de Decisión



Antes de cualquier intervención, aplicar estos cuatro filtros:



1. **Valor:** ¿realmente mejora NaveGo?

2. **Fricción:** ¿reduce pasos, complejidad o esfuerzo humano?

3. **Riesgo:** ¿puede romper algo que ya funciona?

4. **Evidencia:** ¿sabemos que funciona o simplemente creemos que funciona?



Si una intervención no supera estos filtros, no se realiza.



---



## Semáforo de Intervención



### 🟢 Verde — Bajo riesgo

- Cambios de texto, márgenes, íconos, tamaños, etiquetas.

- La IA puede proceder si el archivo está disponible.



### 🟡 Amarillo — Riesgo moderado

- Layout, navegación entre pantallas, estado React, comportamiento del mapa, agregar pantalla, modificar consultas SQLite.

- Se requiere: diagnóstico → propuesta → implementación → prueba.



### 🔴 Rojo — Crítico

- GNSS, COG/SOG, cálculo de distancia, persistencia de fixes, recuperación de señal, sincronización, orientación.

- Prohibido hacer múltiples cambios juntos.

- Trabajar con: hipótesis → experimento controlado → resultado → decisión → implementación.



---



## Estados de Conocimiento



No confundir "implementado" con "validado". Usar estas etapas:



- **HIPÓTESIS:** idea sin materializar.

- **IMPLEMENTADO:** código o cambio aplicado.

- **PROBADO:** se ejecutó una prueba.

- **OBSERVADO:** se registró un resultado.

- **VALIDADO:** evidencia suficiente para considerarlo estable.

- **DESCARTADO:** se descartó por evidencia o decisión.



---



## Estados del Sistema



- **ESTABLE:** funciona, no requiere intervención.

- **EXPERIMENTAL:** en proceso de aprendizaje.

- **BLOQUEADO:** hay una dependencia o problema que impide avanzar.

- **NO VERIFICADO:** no se ha probado; no confundir con "está mal".



---



## Protección de Decisiones Arquitectónicas



Una IA no puede cambiar una decisión arquitectónica simplemente porque encuentre una alternativa técnicamente mejor.



Tiene que marcarla como propuesta.
**Formato obligatorio:**




Cuando una IA detecta que una decisión arquitectónica debería
cambiar, o cuando propone crear, sustituir o derogar una decisión
arquitectónica, no la modifica directamente. Redacta una propuesta
con este formato:

1. **Identificación local.** Identificador estable local (por
   ejemplo `D-A.borrador`), título corto. NO reserva un número
   `D-AAAA-NNNN` que parezca una decisión instituida. El número
   definitivo se asigna al aprobar e incorporar al registro
   canónico.

2. **Estado del borrador.** Siempre `BORRADOR — NO EN REGISTRO
   CANÓNICO` mientras no exista aprobación explícita del Director.
   Este estado es del documento, no de la decisión. R-17 no es una
   restricción de vocabulario: prohíbe que la IA convierta su
   propuesta en decisión. Una IA no puede escribir `PROPUESTA`
   como estado en el registro canónico.

3. **Ubicación del borrador.** Fuera del registro canónico (por
   ejemplo `timonel/borradores/`). Se admite Markdown para
   borradores discursivos; el registro canónico exige JSON según
   el esquema vigente de `.logos/decisions/`. Todos los campos
   obligatorios deben quedar cubiertos antes de promover.

4. **Contenido mínimo.**
   - `contexto`: qué motivó la propuesta, con referencias a memos,
     evidencia o incidentes.
   - `decision`: qué se propone exactamente, en términos
     verificables.
   - `consecuencias`: qué cambia si se aprueba; qué NO cambia.
   - `criterio_revision`: bajo qué condiciones se reabre la
     decisión.
   - `fuentes_verificadas`: referencias rastreables.

5. **Trazabilidad de origen.** La propuesta mantiene vínculo
   explícito con el hallazgo, memo o incidente que la motivó. Ese
   vínculo nunca se pierde, ni en el borrador ni en el registro
   canónico.

6. **Registro y recordatorio obligatorio en
   `EXPEDIENTE/PENDIENTES.md`.** Toda propuesta elevada al Director
   se registra con asunto, estado, responsable y condición de
   resolución o revisión. El registro no basta: mientras no exista
   resolución explícita, el pendiente debe reaparecer
   automáticamente en el mecanismo de arranque del workflow (por
   ejemplo `logos-arranque` o `logos-brief`) hasta que el Director
   lo cierre o lo difiera con condición de revisión. El avance del
   workflow no puede hacerlo desaparecer.

7. **Cierre.** Solo el Director marca el resultado, con tres
   estados posibles:
   - `APROBADO`: se registra la decisión y se continúa según
     corresponda.
   - `RECHAZADO`: se registra el rechazo. El borrador NO se borra;
     queda como constancia de que se evaluó.
   - `DIFERIDO`: se conserva como pendiente, con motivo y
     condición de revisión explícitos.
   El silencio nunca equivale a aprobación.

8. **Trazabilidad de edición.** Se registra: ruta del borrador,
   ruta canónica tras aprobar, fecha, responsable de la aprobación,
   commit que incorpora la decisión aprobada y, cuando
   corresponda, commit que implementa sus consecuencias. Aprobar
   una norma no demuestra que esté implementada: son hitos
   diferentes. No inventar el hash antes de que exista.

---

## Reglas metodológicas obligatorias

Estas reglas son precondiciones del trabajo, no filtros de decisión.
Aplican antes de cualquier plan, propuesta o cambio arquitectónico.

### R3 — Leer las fuentes completas antes de planificar

Antes de redactar un plan que dependa de documentos previos, leer
esas fuentes **completas**. Las primeras líneas no alcanzan: los
estados, los resultados y las políticas operativas suelen estar al
final del documento.

**Fundamento:** EXPEDIENTE/71 (lección del memo 70, escrito con
lectura parcial). Se repitió el patrón en los memos 84-86
(auditoría sin verificar comparaciones justas, corregido en el 87).
Estos documentos fundamentan la regla; no son la regla en sí.

**Cómo aplicarla:**

1. Leer el documento entero si su extensión lo permite.
2. Si es extenso, no basta con buscar marcadores: localizar los
   bloques pertinentes, leerlos completos y revisar sus
   referencias antes de planificar. Marcadores de referencia:
   `CONFIRMED`, `PENDIENTE`, `BLOQUEANTE`, `RESUELTO`, `ABIERTO`,
   `CORRECCIÓN`, `PARCIALMENTE OBSOLETO`, `DECISIÓN`, `EXCEPCIÓN`,
   `RESTRICCIÓN`, `RIESGO`, `CRITERIO`, `NO HACER`. Buscar
   variantes y equivalentes: la ausencia de coincidencias no
   demuestra que no existan restricciones relevantes.
3. Si no puede completarse la lectura, registrar qué fuente y qué
   partes se revisaron, qué quedó pendiente y por qué. Puede
   elaborarse un plan preliminar, pero debe identificarse como tal.

**Consecuencia:** un plan basado en lectura parcial es una
**observación**, no una conclusión. No puede presentar una
afirmación como confirmada ni fundamentar una decisión definitiva.
Remitir a la sección "Estados de Conocimiento" del mismo protocolo:
una lectura parcial no habilita el estado VALIDADO.

**Requisito:** esta regla no prohíbe trabajar ante limitaciones de
lectura. Exige transparentar la cobertura documental y no afirmar
más de lo que la evidencia permite.
