# BITACORA MAESTRA — LOGOS / NaveGo

Actualizado: 2026-08-21

## Fase actual
1. Integridad

## Semáforo de desarrollo
🟡 OBSERVACIÓN

## Objetivo de fase
Garantizar inmutabilidad de datos y persistencia sin errores.

## Deuda técnica
- SQLite UNIQUE constraint
- Acumulador de distancia
- Mojibake
- Visualización de trazas

## Evidencia de fase
- TEST_LOG.md
- SECURITY_BASELINE.md

## Próximo paso
Corregir guardado de sesiones con reset estricto.

## Regla de avance
No pasar a Fase 2 sin cerrar deuda crítica.

## Fases
0. Fundamentos: COMPLETADO
1. Integridad: EN OBSERVACIÓN
2. Consolidación: PENDIENTE
3. Expansión: PENDIENTE
4. Interfaz Lúdica: PENDIENTE

## 2026-08-25 — Visión: Gemelo Digital Activo

### Idea central
El simulador no es solo visual. Es un gemelo digital que se alimenta de datos reales
y predice el comportamiento de una embarcación antes de zarpar.

### Aplicaciones futuras
- Entrenador de maniobras para novatos.
- Cálculo de ángulos óptimos de ceñida (VMG).
- Alerta de límites estructurales.
- Ensayo de emergencias y condiciones hostiles.
- Asistente de regatas.
- Caja negra inteligente con evidencia.

### Puente de comunicación
- TELEMETRY_CONTRACT.md define cómo NaveGo y simulador comparten datos.
- simulate.js ya es el primer eslabón.
- Falta unificar el formato de telemetría.

### Próximo paso
Definir y validar el contrato de telemetría antes de continuar el simulador.

## 2026-08-25 — Landscape V2: laboratorio de percepción

### Documento
- LANDSCAPE_V2_SPEC.md

### Idea central
Ground Truth nunca se degrada. Solo se degrada la estima/sensores.
El simulador se convierte en un banco de pruebas reproducible.

### Próximo paso
Implementar LandscapeV2 → Ground Truth → COG/SOG → validación cardinal.
