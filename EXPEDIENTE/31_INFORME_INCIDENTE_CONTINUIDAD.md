# EXPEDIENTE 31 — Informe de Incidente de Continuidad y Deriva de Workspace

**Fecha:** 2026-09-23
**Proyecto:** NaveGo / LOGOS
**Tipo:** Incidente de gobernanza multi-IA
**Severidad:** Alta para integridad del proceso de desarrollo
**Impacto:** ~3 horas de recuperación y reconstrucción
**Estado:** Recuperado; causas arquitectónicas identificadas

## 1. Resumen

Durante una sesión de trabajo paralela con un agente se produjo una
pérdida de continuidad entre hilos de conversación. El hilo anterior
había alcanzado el límite práctico de contexto y fue necesario iniciar
uno nuevo.

El Director comenzó a reconstruir manualmente el contexto, pero por la
hora y la carga cognitiva de la sesión no identificó que el agente
estaba trabajando sobre ~/workspace en lugar del repositorio real
~/navego_recuperado.

El nuevo hilo recibió una instrucción relacionada con el test U-08 sin
disponer de la totalidad del contexto arquitectónico y operativo
acumulado.

Como consecuencia, el agente:
- reemplazó App.tsx por un escenario de prueba;
- movió los assets del mapa (~122 MB);
- realizó cinco commits sin verificación previa;
- generó cambios incompatibles con el estado real de NaveGo;
- llevó al Director a ejecutar comandos bajo una premisa incorrecta.

El resultado visible fue que la aplicación dejó de mostrar NaveGo y
pasó a mostrar el entorno de TEST.

## 2. Cadena causal

No hubo una única causa.

acumulación de contexto
  -> nuevo hilo
  -> reconstrucción manual incompleta
  -> contexto operativo insuficiente
  -> workspace equivocado
  -> agente interpreta la tarea localmente
  -> ausencia de gate previo
  -> cambios destructivos / commits
  -> ejecución humana
  -> incidente

## 3. Factores contribuyentes

### Factor humano
El Director reconoce que:
- inició el nuevo hilo de madrugada;
- no verificó explícitamente el workspace activo;
- no proporcionó todo el contexto acumulado;
- ejecutó acciones suponiendo que el entorno era el correcto.

Esto se registra como factor contribuyente, no como causa exclusiva.

### Factor de continuidad
El conocimiento relevante estaba distribuido entre varios hilos y
documentos. La reconstrucción manual requería recordar: qué pasó, qué
se decidió, qué está vigente, qué está descartado, qué repo está
activo, qué branch está activa, qué workspace está activo, qué
acciones están autorizadas. Ese procedimiento no era suficientemente
robusto para depender de memoria humana.

### Factor de identificación de workspace
Existían simultáneamente ~/navego_recuperado, ~/workspace,
~/navego_dsh_test, ~/sandbox_agente. El agente pudo operar sin
demostrar inequívocamente sobre cuál estaba trabajando.

## 4. Causa raíz arquitectónica

La causa raíz se define como:

Ausencia, en el momento del incidente, de un mecanismo obligatorio que
vinculara identidad de proyecto + contexto válido + workspace + branch
+ autorización de escritura antes de permitir operaciones del agente.

El protocolo existía documentalmente. La ejecución del protocolo no era
obligatoria. Por tanto: documentación ≠ control.

## 5. Qué demostró el incidente

El incidente demostró cuatro límites del modelo de trabajo anterior:

1. La memoria conversacional no puede ser la fuente de verdad.
2. La reconstrucción manual de contexto no es fiable a escala.
3. Un agente no debe inferir el workspace por proximidad o nombre.
4. Un agente no debe poder comenzar a escribir sin preflight.

## 6. Medidas arquitectónicas adoptadas

Como respuesta se desarrolló LOGOS v1:

MANIFEST -> Context Gate -> Cápsula de Memoria -> Agent Session ->
Workspace / Git -> Diff / Test / Trace

Con tres propiedades obligatorias:

- Cápsula = DERIVADA
- Context Gate = FAIL-CLOSED
- Estado = CON PROCEDENCIA

Además: logos-mem, logos-gate, logos-dsh, validate-manifest,
test-context-01, AGENTS.md, START_HERE.md.

## 7. Nueva interpretación del problema

El problema no es simplemente "hay que pasar más contexto al nuevo
chat". Eso nos volvería a meter en el mismo ciclo.

El problema correcto es: la cantidad de contexto operativo necesaria
para trabajar correctamente está creciendo y no debe ser reconstruida
manualmente.

Por eso la solución no consiste en hacer mensajes cada vez más grandes.
Consiste en hacer que:

- contexto -> persistente
- estado -> estructurado
- decisiones -> versionadas
- hipótesis -> identificables
- procedencia -> explícita
- workspace -> inequívoco
- autorización -> verificable

## 8. Requisito nuevo derivado del incidente

Se agrega una propiedad indispensable: IDENTIDAD DE EJECUCIÓN.

Antes de permitir cualquier escritura, el sistema debe mostrar
inequívocamente:

- PROJECT
- REPOSITORY
- WORKSPACE
- BRANCH
- HEAD
- WRITER
- CONTEXT_REVISION
- MANIFEST_VERSION
- GATE_STATUS

Si alguno de esos elementos es ambiguo: BLOCKED.

Eso habría atacado directamente el incidente.

## 9. Conclusión sobre la responsabilidad humana

El error humano fue real y contribuyó al incidente. Precisamente por eso
constituye un requisito de diseño: un sistema robusto debe tolerar
olvidos, fatiga, trabajo nocturno, cambio de hilo y reconstrucción
incompleta de contexto sin permitir que una equivocación humana se
transforme automáticamente en una modificación destructiva del sistema.

Esto es ingeniería de seguridad. Un buen sistema no parte de "el
operador nunca se equivoca". Parte de "el operador puede equivocarse;
el sistema debe detectar las condiciones peligrosas antes de que
produzcan daño".

## 10. Diagrama del flujo objetivo

Hilo lleno
  -> nuevo hilo
  -> Cápsula de Memoria
  -> Context Gate
  -> Identidad de ejecución
  -> READY / BLOCKED

Con esto, un hilo nuevo puede ser perfectamente "tonto" respecto del
anterior. El sistema ya sabe dónde está.

## 11. Por qué este informe queda como documento de arquitectura

Este incidente no se conserva solamente como un error de sesión. Es el
caso de prueba que permitió descubrir que la continuidad cognitiva y la
identidad operacional son problemas distintos, y que ambos necesitan
mecanismos persistentes fuera del chat.

## 12. Acciones tomadas

- LOGOS v1 desarrollado como respuesta arquitectónica.
- Cápsula de Memoria implementada (logos-mem).
- Context Gate implementado (logos-gate, FAIL-CLOSED).
- Identidad de ejecución definida como requisito.
- Este informe queda como referencia permanente del incidente.

---

Fin del informe.
