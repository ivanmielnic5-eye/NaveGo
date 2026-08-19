# COCKPIT UNIVERSAL — Data Contract v1.0

Actualizado: 2026-08-19

## Principio rector
El contrato de datos no describe la pantalla.
Describe la realidad que el Cockpit puede conocer.
La pantalla, dock, colores e iconos son una proyeccion de este contrato.

## Preguntas que el Cockpit debe poder responder
1. Donde estamos? -> ESTADO
2. Que estamos haciendo? -> TRABAJO
3. Que evidencia tenemos? -> EVIDENCIA
4. Donde esta lo que sabemos? -> ARCHIVOS
5. Que podemos hacer ahora? -> ACCION
6. Cuanto podemos confiar en lo que vemos? -> Evidencia y verificacion

## Entidades universales del Core
PROJECT, MISSION, STATE, WORK, EVIDENCE, FILE, ACTION

## Entidades de memoria
DECISION, EVENT, HISTORY

## Entidades de confianza
VERIFICATION, SOURCE, CONFIDENCE, CONTRADICTION

## Entidades de orquestacion
AGENT, DEVICE, CAPABILITY, INTEGRATION

## Entidades de salud
HEALTH_CHECK, SYSTEM_EVENT

## Campos globales
project, mission, projectStatus, currentPhase, systemHealth,
recommendedAction, aiPresence, verificationState, lastUpdate,
history, activeAlerts, riskLevel, context, session

## Estados universales
## Estado de proyecto
ESTABLE, EXPERIMENTAL, BLOQUEADO, NO_VERIFICADO

## Verificacion
NO_VERIFICADO, IMPLEMENTADO, PROBADO, OBSERVADO, VALIDADO

## Riesgo de intervencion
BAJO, MEDIO, ALTO

## ESTADO
Responde: Cual es la situacion actual?
Muestra: proyecto, mision, fase, estado, progreso, bloqueos, alertas,
dependencias, ultima actualizacion, nivel de confianza, proximo hito.

## TRABAJO
Responde: Que se esta haciendo ahora?
Muestra: tarea activa, objetivo, responsable, IA participante, progreso,
dependencia, siguiente paso, riesgo, tiempo, estado de ejecucion.
Estados: PENDIENTE, EN_CURSO, PAUSADO, COMPLETADO, BLOQUEADO, CANCELADO.

## EVIDENCIA
Responde: Por que creemos que esto es cierto?
Muestra: observacion, fuente, fecha, origen, evidencia asociada,
nivel de confianza, estado de verificacion, interpretacion de IA, contradicciones.
Fuentes: humano, sensor, archivo, app, agente IA, API, experimento, observacion, dispositivo.
Estados: NO_VERIFICADA, OBSERVADA, CONFIRMADA, CONTRADICTORIA, INVALIDADA.
NO SABEMOS es un estado valido.

## ARCHIVOS
Responde: Donde esta la informacion persistente?
Muestra: archivos, tipo, estado, ultima modificacion, origen,
relacion con tarea, relacion con evidencia, version, importancia.
El Cockpit no es dueno de los archivos. Los observa y actua sobre ellos.
Estados: ACTIVO, ARCHIVADO, MODIFICADO, PENDIENTE, CONFLICTO, NO_VERIFICADO.

## ACCION
Responde: Que puede hacer el humano o la IA ahora?
Cada accion tiene: intencion, descripcion, impacto, riesgo, requisitos,
resultado esperado, reversibilidad, responsable, estado, evidencia generada.
Distinguir abrir archivo de modificar arquitectura.
Estados: DISPONIBLE, PENDIENTE_CONFIRMACION, EN_EJECUCION, COMPLETADA,
FALLIDA, CANCELADA, BLOQUEADA.

## Salud del Sistema
El Core no define indicadores fijos.
Cada proyecto aporta sus health checks.
Ejemplo NaveGo: GNSS, SQLite, Tracking Engine, Sync, sensores, mapa, conectividad.
Ejemplo GAIA: camara, pipeline, almacenamiento, dataset, detector, GPU, exportacion.
La gramatica visual permanece, el contenido cambia.

## Separacion de capas
CORE: conoce proyecto, mision, estado, trabajo, evidencia, archivos,
acciones, historial, verificacion, riesgo, presencia IA.
No conoce GNSS, SOG, COG, camara, SQLite, sensores especificos.
SYSTEM: conoce salud, procesos, servicios, conectividad, eventos, errores, recursos.
PROJECT ADAPTER: traduce el dominio al lenguaje del Core.

## Capabilities
El sistema debe saber que puede hacer cada agente, dispositivo o IA.
Ejemplo: IA-A puede analizar archivos, escribir codigo, no ejecutar dispositivo.
IA-B puede ejecutar scripts, acceder repo.
Telefono puede GNSS, acelerometro, camara.
PC puede filesystem, ejecutar procesos.

## Reglas de consistencia
1. Una sola fuente de verdad para cada dato.
2. Derivacion explicita si un dato se calcula de otro.
3. La evidencia gana a la interpretacion.
4. No verificado no es incorrecto.
5. Los conflictos se muestran.
6. El pasado no se reescribe silenciosamente.

## Proyecto de ejemplo: NaveGo
Proyecto: NaveGo
Mision: Registrar una derrota nautica confiable.
Estado: EXPERIMENTAL
Trabajo: Validar Course-Up.
Evidencia: COG GNSS disponible, acelerometro disponible, giroscopio no disponible.
Salud: GNSS OK, Tracking OK, SQLite OK, Sync NO_VERIFICADO.
Accion: Probar Course-Up en movimiento.

## Proyecto de ejemplo: GAIA
Proyecto: GAIA
Mision: Analizar estructura optica biologica.
Estado: EXPERIMENTAL
Trabajo: Validar pipeline de analisis.
Evidencia: Dataset procesado, metrica obtenida, resultado pendiente de validacion.
Salud: Camara OK, Pipeline OK, Dataset OK, Exportacion NO_VERIFICADO.
Accion: Ejecutar validacion.

## Arquitectura de orquestacion
Humano -> Cockpit -> Core -> System y Project Adapters -> Archivos vivos.
El Cockpit no es una app especifica. Es una gramatica comun para coordinar humanos, IA, software y dispositivos.
