# 02 — ARQUITECTURA CONSOLIDADA

Fecha: 2026-09-14
Estado: CONGELADO — Extraído de documentos existentes.

## Regla de este documento

Este documento NO diseña. Extrae.
Todo lo que está acá ya existía escrito antes del 2026-09-14.
Fuente principal: COCKPIT_CORE_DATA_KERNEL.md v1.0 (2026-08-19).

## Documentos fuente

- COCKPIT_CORE_DATA_KERNEL.md v1.0 (2026-08-19)
- COCKPIT_DATA_CONTRACT.md v1.0 (2026-08-19)
- COCKPIT_CORE_SPEC.md (2026-08-19)
- TELEMETRY_CONTRACT.md (2026-08-25)
- PROTOCOLO.md (protocolo de trabajo)

## Frase raíz

"El Core no debe saber que es un barco.
El Core no debe saber que es un iris.
El Core solo debe saber: proyecto, misión, trabajo, evidencia,
archivos, acción, estado."

Esto define LOGOS. No hay que inventarlo.

## Arquitectura de capas

CORE (agnóstico al dominio)
  ├── Estado, Trabajo, Evidencia, Archivos, Acción
  ├── Salud (dinámica, cada proyecto la define)
  ├── Agentes, Dispositivos, Capacidades, Integraciones
  ├── Decisiones, Historia, Fuentes
  └── Verificación: NO_VERIFICADO / IMPLEMENTADO / PROBADO /
                    OBSERVADO / VALIDADO

SYSTEM (contexto técnico)
  ├── Salud del sistema
  ├── Eventos
  ├── Riesgo
  └── Integraciones

PROJECT ADAPTER (traductor)
  ├── NaveGo
  ├── Ojo de Gaia
  ├── Cockpit
  └── Futuros

## Los cinco módulos universales

1. ESTADO   — ¿Qué está pasando?
2. TRABAJO  — ¿Qué estamos intentando hacer?
3. EVIDENCIA— ¿Qué demuestra el resultado?
4. ARCHIVOS — ¿Dónde vive el conocimiento persistente?
5. ACCIÓN   — ¿Qué puede hacer el humano o la IA?

La INTENCIÓN no es un sexto módulo.
Atraviesa los cinco.

## Contrato del Project Adapter

Un adapter por proyecto debe exponer:

1. IDENTITY   — nombre, versión, capacidades
2. STATE      — estado, fase, contexto, métricas, bloqueos
3. EVIDENCE   — fuentes, observaciones, verificación, procedencia
4. HEALTH     — componentes, health checks, eventos, errores
5. ACTIONS    — disponibles, requisitos, riesgo, resultado esperado
6. CAPABILITIES — qué puede hacer, qué recursos necesita

## Estados universales

Proyecto:      ESTABLE / EXPERIMENTAL / BLOQUEADO / NO_VERIFICADO
Conocimiento:  NO_VERIFICADO / IMPLEMENTADO / PROBADO / OBSERVADO / VALIDADO
Riesgo:        BAJO / MEDIO / ALTO
Salud:         OK / DEGRADED / FAILED / UNAVAILABLE / UNKNOWN
Evidencia:     NO_VERIFICADA / OBSERVADA / CONFIRMADA / CONTRADICTORIA / INVALIDADA
Trabajo:       PENDIENTE / EN_CURSO / PAUSADO / COMPLETADO / BLOQUEADO / CANCELADO
Acción:        DISPONIBLE / PENDIENTE_CONFIRMACION / EN_EJECUCION /
               COMPLETADA / FALLIDA / CANCELADA / BLOQUEADA

## Reglas de consistencia

1. Una sola fuente de verdad por dato.
2. Derivación explícita si un dato se calcula de otro.
3. La evidencia gana a la interpretación.
4. NO VERIFICADO no es incorrecto.
5. Los conflictos se muestran.
6. El pasado no se reescribe silenciosamente.

## Reglas congeladas (COCKPIT_CORE_SPEC)

1. Los cinco módulos son universales.
2. Salud es un contenedor dinámico, no fijo.
3. Los proyectos se conectan mediante adaptadores.
4. Estado global y contexto de proyecto están separados.
5. NO_VERIFICADO es un estado legítimo.
6. La intención humana atraviesa sin convertirse en módulo.
7. Ningún proyecto introduce una categoría visual al Core sin
   demostrar que existe en más de un dominio.

## La regla de silencio

Cuando todo está bien, la pantalla puede estar casi vacía.
Cuando algo importante aparece, el instrumento despierta.

Metáfora: instrumento de orquestación, no dashboard.

## Contrato de telemetría (NaveGo ↔ Godot)

JSON de intercambio:
{
  "timestamp": 0,
  "lat": 0.0,
  "lon": 0.0,
  "sog_ms": 0.0,
  "cog_deg": 0.0,
  "heading_deg": 0.0,
  "accuracy_m": 0.0,
  "pitch_deg": 0.0,
  "roll_deg": 0.0,
  "yaw_deg": 0.0
}

Reglas:
- NaveGo es fuente de evidencia real.
- Godot es fuente de escenarios sintéticos.
- LOGOS registra y compara.
- Ningún dato se inventa: si falta, se marca NO_VERIFICADO.

Deuda técnica detectada:
- El bridge actual devuelve formato NMEA parseado.
- El contrato define formato estructurado con unidades explícitas.
- Pendiente: unificar el bridge con el contrato.

## División de roles (PROTOCOLO.md)

Humano: Director Funcional.
  - Observa, decide, prueba, describe.
  - No necesita programar.

IA: Director Técnico.
  - Interpreta, diagnostica, propone, implementa, documenta.
  - Minimiza la carga del humano.

Ciclo:
  OBSERVACIÓN → INTERPRETACIÓN → PRIORIZACIÓN → HIPÓTESIS →
  EXPERIMENTO → RESULTADO → DECISIÓN → IMPLEMENTACIÓN →
  PRUEBA → REGISTRO → SIGUIENTE PASO

Semáforo:
  🟢 Verde:   cambios de texto, márgenes, íconos.
  🟡 Amarillo: layout, navegación, estado React, SQLite.
  🔴 Rojo:    GNSS, COG/SOG, distancia, persistencia, sync.

## Aporte de GPT-4 (2026-09-14)

Coincide con el kernel en:
- Contrato universal de observación
- Separación Navigation Data ≠ Render Data
- Capability Degradation
- ReplayProvider obligatorio
- Preservar RAW sin destruirlo

Aporte nuevo válido:
- Concepto formal de "Map Region Package" (regiones navegables
  en vez de "mapa del mundo").
- Modelo de degradación por capacidades:
  100% → 80% → 50% → 30% → 0%

## Aporte de Claude (2026-09-14)

Advertencia de secuencia:
- No diseñar portabilidad antes de tener una app funcionando.
- Recuperar los documentos existentes antes de diseñar nuevos.
- No dejar que dos IAs toquen el mismo core en paralelo sin
  síntesis única.

Esta advertencia es VÁLIDA y se incorpora como regla:
- Ninguna IA modifica el Core sin pasar por este expediente.
- Toda propuesta nueva se marca como PROPUESTA hasta ser
  validada contra el kernel existente.

## Lo que NO se toca hasta nueva orden

- No se rediseña el kernel. Ya está congelado.
- No se elige formato de mapa (MBTiles/PMTiles/GeoPackage)
  sin medirlo en un caso de uso real.
- No se migra Google Maps → MapLibre hasta que NaveGo
  tenga una pantalla funcionando estable.
- No se implementa LOGOS Core hasta cerrar NaveGo.

## Próximo paso concreto

Cerrar el diagnóstico del HUD y del Cockpit en el celular.
Cuando NaveGo funcione de punta a punta, extraer de él los
componentes reutilizables y recién ahí empezar a construir
LOGOS Core sobre lo que ya sirvió dos veces sin cambios.

## Frase única

"NaveGo es un núcleo de navegación local, observable y recuperable,
independiente de la interfaz, de la red y de la fuente de datos,
capaz de degradar sus capacidades sin perder su estado ni la
soberanía de sus datos."

Para LOGOS:
"LOGOS no comparte aplicaciones: comparte las estructuras que
permiten que las aplicaciones aprendan, persistan, se observen
y sobrevivan."
