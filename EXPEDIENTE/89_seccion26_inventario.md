# SECCION 26 — INVENTARIO DEL SISTEMA TIMONEL (BORRADOR)

**Fecha:** 2026-10-13
**Estado:** BORRADOR. Inventario verificado en codigo, pendiente de validacion
con Claude y Luna antes de incorporar al memo 89.
**Origen:** inspeccion de `timonel/*.py` sin modificar nada.

---

## 26.1 Acciones implementadas

Fuente: `timonel/acciones.py`.

| Intent | Firma | Parametros | Que hace |
|---|---|---|---|
| `rumbo` | `rumbo(theta, horizonte_s)` | `theta` (grados absolutos) | Mantiene rumbo. PID interno. |
| `ir_a` | `ir_a(meta_x, meta_z, horizonte_s)` | `meta_x`, `meta_z` | Navega al punto. Recalcula rumbo cada 0.5s. |
| `frenar` | `frenar(horizonte_s, sog_objetivo_kn=0.3)` | `sog_objetivo_kn` (default 0.3) | Reduce velocidad. Control proporcional. |
| `terminar` | `terminar(meta_x, meta_z, horizonte_s)` | `meta_x`, `meta_z` | Accion logica. Valida solo si `dist < 15.0`. |

Diccionario `ACCIONES` mapea los 4 nombres a sus funciones. **Ese es el
contrato vigente.**

Nota historica: `corregir_rumbo` e `ir_a_punto` fueron reemplazadas por
`rumbo` e `ir_a`. La v1 mezclaba intencion con ejecucion; la v2 separa
setpoint de ejecucion.

## 26.2 Controlador fisico

Fuente: `timonel/controlador_pid.py`.

| Componente | Detalle |
|---|---|
| Clase | `PIDRumbo` |
| Tipo | PID con `Ki=0.0` (en la practica, PD) |
| Frecuencia | 60 Hz (inner loop) |
| Parametros | `Kp=0.10`, `Ki=0.0`, `Kd=0.25` |
| Anti-windup | `integral_limit=20.0` |
| Tolerancia | 1.0 grado |
| Arquitectura | Cascada: el LLM decide setpoint, el PID ejecuta |

El docstring del archivo ya declara la arquitectura:

> "Inner loop (aqui): PID de rumbo a 60 Hz.
>  Outer loop (futuro): el LLM decide el rumbo."

Referencia: `EXPEDIENTE/89 seccion 10.bis y Anexo A`.

## 26.3 Simulador

Fuente: `timonel/simulador_polaris.py`.

**Implementado:**
- Constantes fisicas (MASS, drags, torques, viento).
- Clase `Barco` (estado + integracion).
- Metodo `paso(dt)` (fisica: fuerzas, drag, viento).
- `aplicar_comando(timon, timon_ms, avance, avance_ms)`.
- Telemetria: `heading_deg()`, `sog_kn()`, `cog_deg()`, `dist_a_meta()`.
- Viento variable: `_inicializar_viento_variable()`, `_actualizar_viento_variable()`.
- Clase `Runner` (loop de simulacion con telemetria).

**NO implementado:**
- Deteccion de colisiones.
- Limites del mundo.
- Zonas seguras.
- Profundidad / encallamiento.
- Obstaculos.
- Validacion de comandos (acepta cualquier float en [-1.0, 1.0]).

En el escenario Godot existe un muelle de madera, pero **sin
colisionador**. El simulador matematico replica solo fisica, no
colisiones.

## 26.4 Entrenador v2

Fuente: `timonel/entrenador_v2.py`. Es el vigente.

| Componente | Detalle |
|---|---|
| Horizontes | `[5.0, 15.0, 30.0, 45.0]` segundos |
| Continuacion comun | Todas las acciones corren hasta el horizonte maximo |
| Radio boundary | 500.0 m desde el origen |
| Peligro inminente | Margen < 50 m Y velocidad radial > 0.5 m/s hacia afuera |
| Acciones disponibles | `["rumbo", "ir_a", "frenar", "terminar"]` |
| `mission_complete` | `terminar` valido solo si `dist < 15.0` (hardcodeado) |
| `boundary_violation` | True si el barco sale del radio de 500 m |

**Ranking normal:**


**Ranking normal:**

**Ranking con peligro inminente:**

**Progreso medio:** integracion trapezoidal sobre los horizontes.

## 26.5 Huecos identificados

| Concepto | Estado |
|---|---|
| Umbral T variable en terminar | NO implementado. Hardcodeado en 15.0 |
| Semantica de frenar | Sin definir. Es una accion mas, sin criterio de "cuando gana" |
| Validacion de argumentos | NO implementada |
| Restricciones duras (colisiones, zonas) | NO implementadas |
| Prioridad de seguridad explicita | Parcial (solo boundary de 500 m) |
| abstenerse como output | NO implementado |
| Separacion rumbo vs ir_a | Funcional: apuntan al mismo lugar |

## 26.6 Desalineacion detectada

El banco de A2/A3 usa T variable (10, 15, 20, 25 en A2; 11 valores
en A3). El simulador tiene T fijo en 15.0.

Es un hecho: el contrato del simulador no coincide con el contrato
del banco. Hay que decidir cual manda antes de A3 etapa 1.

## 26.7 Deuda tecnica

El renombrado de oraculo a entrenador esta incompleto. Quedan
referencias en:
- validacion_oraculo.py
- oracle_pure_pilot.py
- context_sampler.py

oraculo.py es un shim que redirige a entrenador. No rompe. Es deuda
tecnica, no bug.
