# Evidencia — Sesion 2026-09-21

## Tipo
Sesion de analisis arquitectonico. Descubrimiento de vulnerabilidad.

## Contexto del incidente
El hilo arranco SIN seguir el protocolo de arranque oficial
(~/.logos/bin/logos-context --level=4). Resultado: la IA confundio
DSH (DeepSeek Harness) con Harness.io (herramienta DevOps de una
empresa llamada Harness). Se descubrio, en vivo, una vulnerabilidad
arquitectonica del sistema LOGOS.

## Hallazgos
1. LOGOS kernel ya existe y esta validado (15 sep 2026).
2. El protocolo de arranque esta escrito pero no se aplica.
3. Cinco fuentes de contexto desincronizadas.
4. SESIONES.md (22 ago) contiene diseno vivo NO duplicado:
   - Maquina de estados: AMARRE -> INICIAR DERROTA -> TRACKING ACTIVO
     -> PAUSAR -> REANUDAR -> FINALIZAR.
   - Regla de pausa Opcion C ("interrupcion visible, no linea
     recta falsa") — decidida en agosto, perdida entre hilos.
5. Caso real y reproducible del problema de continuidad de contexto.

## Correcciones incorporadas (auditoria GPT-4, 21 sep)
- MANIFEST DECLARA, GATE CALCULA.
- Roles singleton vs collection para tipos de fuente.
- Root of trust del propio MANIFEST: pendiente de diseno.

## Propuesta arquitectonica
- MANIFEST.json — declara autoridad por tipo de dato.
- Context Gate — preflight READY/WARNING/BLOCKED.
- FAIL-CLOSED — sin contexto valido, no arranca agente.
- TEST-CONTEXT-01 — test de regresion del incidente.

## Estado actual
Evidencia congelada. Diseno de MANIFEST en revision.
No se ha tocado el kernel LOGOS ni el codigo de NaveGo.

## Precision sobre archivos antiguos
ESTADO.md, SESIONES.md y SYNC_BRIEF.md NO estan declarados
HISTORICAL todavia. Estan en proceso de clasificacion/migracion.
