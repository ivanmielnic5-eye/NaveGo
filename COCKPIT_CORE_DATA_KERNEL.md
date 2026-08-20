# COCKPIT CORE DATA KERNEL v1.0

Actualizado: 2026-08-19

## Estados universales

### Estado del proyecto
ESTABLE: funciona según lo esperado y existe evidencia suficiente.
EXPERIMENTAL: existe una implementacion o hipotesis en evaluacion.
BLOQUEADO: no puede avanzar hasta resolver una dependencia.
NO_VERIFICADO: existe una afirmacion o implementacion, pero todavia no fue comprobada.
Regla: NO_VERIFICADO no significa incorrecto.

### Estado del conocimiento
IMPLEMENTADO: existe una implementacion concreta.
PROBADO: se ejecuto una prueba.
OBSERVADO: se observo un comportamiento real.
VALIDADO: la evidencia permite considerarlo confirmado dentro del alcance definido.
Importante: IMPLEMENTADO no implica VALIDADO automaticamente.

### Riesgo
BAJO: cambio pequeno, reversible y con bajo impacto.
MEDIO: puede afectar comportamiento existente.
ALTO: puede afectar datos, arquitectura, persistencia, tracking o integridad.

## Entidades universales
PROJECT: que proyecto estamos gestionando?
MISSION: que queremos conseguir?
WORK: que estamos haciendo ahora?
EVIDENCE: que demuestra lo que creemos?
FILE: donde esta materializada la informacion?
ACTION: que podemos hacer a continuacion?
Cada entidad debe tener id, createdAt, updatedAt, status, verificationState, source, relaciones.

## PROJECT
Contiene: identidad, nombre, descripcion, mision activa, estado, fase, adapter utilizado,
salud agregada, trabajo activo, proxima accion recomendada, ultima actualizacion.

## MISSION
Representa la intencion que dirige el trabajo.
Contiene: identidad, objetivo, estado, prioridad, criterios de finalizacion,
proyecto asociado, progreso, fecha de inicio, fecha de finalizacion.
MISION dice para que, TRABAJO dice que estamos haciendo ahora.

## WORK
Contiene: objetivo, descripcion, estado, prioridad, riesgo, responsable,
agente IA, dependencia, evidencia asociada, resultado esperado, resultado obtenido, proxima accion.
Estados: PENDIENTE, EN_CURSO, PAUSADO, COMPLETADO, BLOQUEADO, CANCELADO.

## EVIDENCE
Registra: que se observo, fuente, fecha, origen, conocimiento asociado,
nivel de verificacion, confianza, archivos relacionados, contradicciones, agente o dispositivo.
Fuentes universales: HUMAN, AI, SENSOR, DEVICE, FILE, APPLICATION, API, EXPERIMENT, OBSERVATION.

## FILE
Identifica: ubicacion, nombre, tipo, proyecto, origen, version, estado,
ultima modificacion, relacion con evidencia, relacion con trabajo.
Regla: el Cockpit conoce y opera sobre archivos, pero no es automaticamente su fuente de verdad.

## ACTION
Describe: que quiere conseguir, quien puede ejecutarla, riesgo, requisitos,
resultado esperado, reversibilidad, estado, evidencia que deberia producir.
Estados: DISPONIBLE, PENDIENTE_CONFIRMACION, EN_EJECUCION, COMPLETADA, FALLIDA, CANCELADA, BLOQUEADA.

## Entidades de salud

### HEALTH_CHECK
Campos: id, componente, estado, ultima comprobacion, mensaje, severidad, fuente, proyecto asociado.
Estados: OK, DEGRADED, FAILED, UNAVAILABLE, UNKNOWN.

### SYSTEM_EVENT
Representa algo que ocurrio.
Campos: identidad, timestamp, origen, tipo, severidad, descripcion, contexto, entidades relacionadas.
Distincion: EVENTO es algo que ocurrio, ESTADO es como esta ahora.

## Entidades de orquestacion

### AGENT
Puede ser IA, humano, servicio o proceso automatizado.
Describe: identidad, tipo, capacidades, estado, disponibilidad, permisos, contexto.

### DEVICE
Ejemplos: PC, telefono, tablet, servidor, sensor, dispositivo domestico.
Describe: identidad, tipo, capacidades, estado, conectividad, agente asociado.

### CAPABILITY
Ejemplos: leer archivo, escribir archivo, ejecutar proceso, obtener GNSS, capturar imagen, analizar datos, enviar comando.

### INTEGRATION
Ejemplos: Git, filesystem, terminal, dispositivo movil, Alexa, API, repositorio, servicio local.
Describe: sistema, capacidades, estado, autenticacion, ultima sincronizacion, errores.

## Elementos transversales

### DECISION
Registra decisiones arquitectonicas o de direccion.
Campos: decision, motivo, autor, fecha, alcance, evidencia, estado, reversible o no reversible.

### HISTORY
Registro de cambios significativos.
Permite reconstruir: ANTES, DECISION, ACCION, EVIDENCIA, NUEVO ESTADO.

### SOURCE
Toda informacion importante debe poder responder: de donde salio esto?
Origenes: humano, IA, sensor, archivo, dispositivo, sistema externo, experimento.

## Contrato minimo del Project Adapter
El Adapter es el traductor entre un dominio concreto y el Core.
Debe exponer seis capacidades:
1. IDENTITY: nombre, version, proyecto, descripcion, capacidades.
2. STATE: estado del proyecto, fase, contexto, metricas relevantes, bloqueos.
3. EVIDENCE: fuentes, observaciones, resultados, nivel de verificacion, procedencia.
4. HEALTH: componentes del sistema, health checks, eventos, errores, recuperacion.
5. ACTIONS: acciones disponibles, requisitos, riesgo, capacidades necesarias, resultado esperado.
6. CAPABILITIES: que puede hacer, que recursos necesita, que dispositivos utiliza, que integraciones requiere.

## Preguntas universales al Adapter
Quien sos?
En que proyecto estas?
Cual es el estado?
Que se esta haciendo?
Que evidencia existe?
Que salud tiene el sistema?
Que acciones estan disponibles?
Que capacidades existen?
Que cambio?
Que necesita atencion?

## Regla de frontera
El Core no debe saber que es un barco.
El Core no debe saber que es un iris.
El Core solo debe saber: proyecto, mision, trabajo, evidencia, archivos, accion, estado.

## Minimo congelado para la proxima sesion
Estados: ProjectStatus, KnowledgeState, RiskLevel.
Core: Project, Mission, Work, Evidence, File, Action.
Sistema: HealthCheck, SystemEvent.
Orquestacion: Agent, Device, Capability, Integration.
Memoria: Decision, History, Source.
Contrato Adapter: Identity, State, Evidence, Health, Actions, Capabilities.
