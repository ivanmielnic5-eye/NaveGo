# 03 — WORKFLOW CONSOLIDADO Y AUTO-OBSERVACIÓN

Fecha: 2026-09-14
Estado: PROPUESTA — A validar antes de implementar.
Relación: Complementa PROTOCOLO.md y COCKPIT_CORE_DATA_KERNEL.md v1.0.

## Regla de este documento

No modifica el kernel congelado.
Lo extiende con capacidades nuevas.
Toda extensión queda marcada como PROPUESTA hasta ser validada.

## 1. Workflow consolidado

### 1.1 Ciclo cognitivo (del PROTOCOLO.md)

OBSERVACIÓN HUMANA
     ↓
INTERPRETACIÓN TÉCNICA (IA)
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
REGISTRO EN EXPEDIENTE
     ↓
SIGUIENTE PASO

Cada ciclo termina con una versión funcional.

### 1.2 Semáforo de riesgo

VERDE   — texto, márgenes, íconos, etiquetas.
AMARILLO— layout, navegación, estado React, SQLite.
ROJO    — GNSS, COG/SOG, distancia, persistencia, sync.

### 1.3 Estados de conocimiento

HIPÓTESIS → IMPLEMENTADO → PROBADO → OBSERVADO → VALIDADO
                                            ↘ DESCARTADO

### 1.4 Reglas de hierro

R-01 Una hipótesis principal por iteración.
R-02 Una decisión por consulta.
R-03 Roles funcionales, no jerárquicos.
R-04 Ninguna acción exitosa sin evidencia.
R-05 exit code 0 ≠ éxito funcional.
R-06 UNKNOWN ≠ FAILED.
R-07 No modificar sin autorización explícita.
R-08 Separar hipótesis de decisión.
R-09 Ninguna IA cierra una rama que ella misma propuso.
R-10 NO REGRESIÓN: hipótesis descartada no vuelve sin evidencia nueva.
R-11 STOP CONDITION: 3 fallos equivalentes bloquean la estrategia.
R-12 EVIDENCIA NUEVA: repetir un comando no cuenta como evidencia nueva.
R-13 CONSTRAINT LOCK: las restricciones del usuario son parte del estado.
R-14 OBJECTIVE CHECK: si el estado no cambia materialmente, parar.
R-15 Ninguna IA modifica el kernel sin pasar por el expediente.

## 2. Integridad de evidencia — SHA-256

### 2.1 Propósito

Cada pieza de evidencia importante debe poder demostrar:
- Que no fue alterada después de ser registrada.
- Que puede compararse con otra versión sin ambigüedad.
- Que su origen es trazable.

### 2.2 Propuesta

Extender la entidad EVIDENCE con:

hash_sha256: string
hash_algo: "sha256"
hash_created_at: timestamp
previous_hash: string (opcional, para cadena de evidencia)
content_ref: ruta al archivo o snapshot

### 2.3 Aplicación

- Los archivos de evidencia (capturas, logs, JSON) se hashean al momento de registrarlos.
- El hash se guarda en el kernel.
- Si un archivo cambia, el hash cambia → se detecta contradicción.
- Se puede construir una cadena de hashes para auditar historia.

### 2.4 Anti-patrón

No hashear sin registrar:
- qué se hasheó
- cuándo
- con qué algoritmo
- quién lo generó

## 3. Auto-observación del sistema

### 3.1 Propósito

El núcleo debe poder responder en todo momento:

"¿Cuánta capacidad tengo disponible AHORA?"

Y en base a eso, decidir qué nivel de agente usar.

### 3.2 Nuevo concepto: RESOURCE_PROFILE

Extiende HEALTH_CHECK con un perfil de recursos.

RESOURCE_PROFILE
├── cpu_load_avg_1m
├── cpu_load_avg_5m
├── cpu_load_avg_15m
├── memory_total_mb
├── memory_used_mb
├── memory_available_mb
├── swap_used_mb
├── disk_free_gb
├── battery_percent
├── battery_charging
├── network_status
├── latency_ms
├── thermal_state
└── timestamp

### 3.3 Estados de capacidad

SOBRECARGADO  — la máquina está al límite. Reducir carga.
ÓPTIMO        — recursos balanceados. Modo normal.
SUBUTILIZADO  — sobra capacidad. ¿Subir a un nivel de agente superior?
DESCONOCIDO   — no hay medición confiable.

### 3.4 Decisión sobre el nivel de agente

El núcleo NO decide por sí solo.
Propone, el humano o una IA autorizada decide.

Ejemplo de propuesta automática:

SUBUTILIZADO + proyecto activo
  → "Capacidad disponible para subir modelo de IA local"
  → Propuesta: cambiar de qwen2.5-coder:7b a un modelo mayor
  → Requiere confirmación humana

SOBRECARGADO + tarea no crítica
  → "Recursos al límite"
  → Propuesta: posponer tarea no crítica, mantener las críticas

ÓPTIMO
  → Sin cambios.

### 3.5 Sobre el "sobre-girado" y "sub-girado"

Términos en discusión. Propongo estos equivalentes técnicos:

SOBRE-GIRADO (overclocked):
  El sistema opera por encima de su capacidad confortable.
  Síntomas: alta temperatura, throttling, latencia creciente, swap.
  Riesgo: degradación silenciosa de la calidad de decisión.

SUB-GIRADO (underclocked):
  El sistema opera muy por debajo de su capacidad.
  Síntomas: CPU < 20%, RAM libre > 70%, sin swap.
  Oportunidad: subir capa de agente, precomputar, aprender.

GIRO ÓPTIMO:
  El sistema opera en su curva de mejor eficiencia.
  Ni forzado ni desaprovechado.

La decisión de ajustar el giro NO es del kernel.
El kernel mide, reporta, y propone.
El humano (o un agente autorizado) decide.

## 4. Capas de procesamiento

Propongo formalizar tres capas, para que el sistema sepa cuál usar según recursos:

CAPA 1 — MÍNIMA
  Cuando: batería baja, calor alto, CPU saturada.
  Qué corre: GPS + persistencia + HUD básico.
  Qué NO corre: IA local, precomputo, sincronización.
  IA: ninguna o modelo mínimo.

CAPA 2 — ÓPTIMA
  Cuando: recursos normales.
  Qué corre: todo lo anterior + IA local estándar (7b) + sync.
  Qué NO corre: análisis pesado, replays largos.
  IA: qwen2.5-coder:7b (referencia actual).

CAPA 3 — EXPANDIDA
  Cuando: recursos sobrantes, sin presión.
  Qué corre: todo lo anterior + IA mayor + análisis + precomputo.
  IA: modelo mayor (14b, 32b) o colaboración multi-agente.

La transición entre capas requiere:
1. Medición real.
2. Propuesta del núcleo.
3. Confirmación humana.
4. Registro en EVIDENCE.

## 5. El "auto-leerse"

El sistema, cada N segundos, se pregunta:

1. ¿Cuánta capacidad tengo?
2. ¿Cuánta estoy usando?
3. ¿Cuánta me sobra?
4. ¿Qué capa estoy usando?
5. ¿Estoy en la capa correcta?
6. ¿Debería proponer cambio?

Esta auto-lectura se registra como SYSTEM_EVENT.
Si la propuesta es aceptada, se registra como DECISION.
Si cambia la capa, se registra como HISTORY.

## 6. Reglas R-16 a R-20 — Referencia normativa

**Fuente autoritativa:** `~/.logos/core/protocol/protocols.json`.

Este archivo no duplica el texto normativo vigente. Las definiciones
historicas que siguen se conservan exclusivamente para trazabilidad y
no tienen autoridad normativa.

**HISTORICO — DEFINICIONES NO VIGENTES; NO UTILIZAR COMO PROTOCOLO ACTIVO**

- R-16 Todo cambio de capa debe tener evidencia de la medición previa.
- R-17 El núcleo propone, el humano decide. Nunca auto-cambio silencioso.
- R-18 La auto-observación no interfiere con la operación normal.
- R-19 Un cambio de capa es reversible.
- R-20 Un cambio de capa es REVERSIBLE + REGISTRADO.

Las definiciones autoritativas de estos identificadores son las registradas
en `protocols.json`. Ante cualquier discrepancia, consultar esa fuente y no
este bloque historico.

## 7. Frase para el expediente

"El sistema no solo ejecuta: se observa. Mide su capacidad,
reporta su estado, propone ajustes. El humano decide.
El núcleo no auto-ajusta: auto-informa."

## 8. Lo que NO se hace todavía

- No se implementa SHA-256 hasta que haya evidencia que hashear.
- No se implementa RESOURCE_PROFILE hasta que haya un consumidor.
- No se implementan CAPAS hasta que NaveGo funcione standalone.
- No se auto-ajusta nada hasta que exista el mecanismo de confirmación.

## 9. Próximos pasos concretos

1. Validar este documento contra el kernel v1.0.
2. Si hay conflicto, marcar como PROPUESTA y no modificar el kernel.
3. Incorporar solo lo que sea compatible sin romper.
4. Dejar el resto como roadmap.

## Anexo operativo P48 — ciclo de vida de pendientes LOGOS

**Estado:** procedimiento operativo específico de P48. Este anexo no declara validado el workflow consolidado completo ni modifica el kernel institucional.

### Principios obligatorios

1. La IA inspecciona, propone y aporta evidencia; el Director decide.
2. Aceptar la implementación no equivale a aceptar el cierre.
3. No hay aprobación por silencio, cierre automático ni commit automático.
4. Las pruebas y los mensajes de consola son evidencia; no reemplazan la revisión del diff ni la decisión humana.
5. No se mezclan cambios ajenos. Si Gate no está READY o una prueba falla, se detiene el flujo.
6. La raíz de confianza ausente debe permanecer como advertencia visible. No se crea ni se declara verificada por inferencia.

### Secuencia operativa

**1. Inspeccionar sin modificar**

    python3 .logos/bin/logos-pendiente inspeccionar P48

Revisar la sección completa, Gate y estado de Git. Resolver primero cualquier conflicto o cambio ajeno que pudiera quedar incluido en la operación.

**2. Registrar una decisión explícita**

    python3 .logos/bin/logos-pendiente decision P48 --fase implementacion --decision ACEPTO --nota "Justificación"

Las fases admitidas son `implementacion` y `cierre`; las decisiones son `ACEPTO` y `RECHAZO`. Este comando escribe en `EXPEDIENTE/PENDIENTES.md`, pero no actualiza el MANIFEST. Revisar inmediatamente el diff y preservar el historial. No repetir una decisión si ya está registrada.

**3. Ejecutar las verificaciones**

    python3 .logos/bin/logos-pendiente verificar P48 --test .logos/tests/test_logos_pendiente.py --test .logos/tests/test_logos_p48_guards.py

Cada prueba debe terminar correctamente. La verificación también debe confirmar el estado del Gate. No avanzar si hay errores o si la salida no permite confirmar el resultado.

**4. Revisar la reconciliación antes de ejecutarla**

Para el registro de pendientes:

    python3 .logos/bin/logos-pendiente reconciliar-pendientes --dry-run

Para documentar este workflow, si su fuente está registrada en el MANIFEST:

    ./.logos/bin/logos-reconcile mark-reviewed workflow --dry-run

Examinar el diff propuesto. La reconciliación real es una operación separada y solo se realiza con autorización explícita, después de revisar su alcance.

La advertencia `trust: ABSENT` significa que la raíz de confianza no existe y no está verificada. Solo puede reconocerse como advertencia conocida cuando la herramienta confirma explícitamente que aplicó `mark-reviewed`. Cualquier otro error, resultado ambiguo o Gate distinto de READY obliga a detenerse e investigar.

**5. Preparar únicamente los archivos autorizados**

    python3 .logos/bin/logos-pendiente preparar P48 --test .logos/tests/test_logos_pendiente.py --test .logos/tests/test_logos_p48_guards.py --path .logos/bin/logos-pendiente --path .logos/bin/logos-ingesta --path .logos/bin/logos-arranque --path .logos/tests/test_logos_pendiente.py --path .logos/tests/test_logos_p48_guards.py --path EXPEDIENTE/03_WORKFLOW.md --path EXPEDIENTE/PENDIENTES.md

`preparar` no crea commits. Antes de ejecutar, confirmar que el Gate esté READY y que los archivos preparados previamente estén dentro de la lista permitida. Después, revisar `git diff --cached --name-only`, `git diff --cached --check` y el diff preparado completo. No confirmar cambios que no fueron revisados.

**6. Cerrar solo con una segunda decisión humana**

El cierre requiere una decisión de fase `cierre` con `ACEPTO`, registrada por separado, además de las pruebas, el Gate READY y la confirmación textual exacta:

    python3 .logos/bin/logos-pendiente cerrar P48 --confirm "CERRAR P48" --test .logos/tests/test_logos_pendiente.py --test .logos/tests/test_logos_p48_guards.py

Este comando no crea commits. Si falla la reconciliación o el Gate, se debe comprobar el contenido actual antes de cualquier restauración. Si hay cambios concurrentes, no se sobrescriben: se informa el conflicto y se preserva la evidencia para resolución humana.

### Resultado y evidencia

Registrar los comandos ejecutados, sus códigos de salida, los resultados de las pruebas, el Gate final, el diff reconciliado y las advertencias no resueltas. La raíz de confianza ausente permanece explícita hasta que el Director decida cómo resolverla.

Este anexo describe el procedimiento de P48; no constituye una decisión de cierre de P48 ni una aprobación global del documento de workflow.
