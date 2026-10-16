# DIAGNÓSTICO TIMÓN — PYTHON vs GODOT

**Fecha:** 2026-10-16
**Estado:** BORRADOR. Fuera del expediente.
**Origen:** detección de giro lento (0.5°/s) durante E2.

---

## 1. Cadenas de timón — dónde se aplica el torque

### Python (`simulador_polaris.py:250-263`)
- `efectividad = max(speed_factor, prop_wash_factor)`
- `speed_factor = min(1, (speed_ms / 1.286)**2)` — cuadrática
- `prop_wash_factor = 0.35` si avance activo, sino 0
- `torque = TIMON_TORQUE(886) * timon * efectividad`
- Duty cycle: `timon_ms=1500`, gap de 1.5 s (si INTERVALO_S=3)

### Godot `rudder_controller.gd:53-63` (teclado)
- `fraccion = _angulo_actual / angulo_maximo` (0..1 por ángulo)
- `eficiencia = clamp(speed / 0.5, 0, 1)` — lineal, satura a 0.5 m/s
- `torque = fraccion * torque_max(5500) * eficiencia`
- Duty cycle: continuo mientras tecla apretada

### Godot `timonel_bridge.gd:155-157` (headless / archivo)
- `torque = timon_torque * torque_dir`
- Sin eficiencia por velocidad
- Duty cycle: `timon_ms=1500`, mismo gap que Python

**En headless corre el bridge, NO el rudder_controller.** El teclado no funciona en headless (`TestInput.pressed` devuelve false).

---

## 2. Diferencias reales entre Python y Godot headless

| Aspecto | Python | Godot headless |
|---|---|---|
| Torque base | 886 | **2500 (presunto)** |
| Eficiencia por velocidad | Cuadrática hasta 1.286 m/s | **Ninguna** |
| Prop wash | 0.35 | No aplica |
| Duty cycle | 1.5s on / 1.5s off | 1.5s on / 1.5s off |
| Inercia | 53333 kg·m² (caja 4x1x8) | **Calculada por Jolt (desconocida)** |

---

## 3. Verificación del giro observado en Python

Test de humo (60 s, sin viento, meta en (36,-6)):
- Velocidad: ~0.21 m/s
- `speed_factor = (0.21/1.286)² = 0.027`
- `prop_wash = 0.35` (avance activo)
- `efectividad = 0.35`
- `torque_on = 886 × 0.35 = 310 N·m`
- `I_y = 8000 × (4²+8²) / 12 = 53333 kg·m²`
- `α = 310 / 53333 = 0.0058 rad/s² = 0.33°/s²`
- En 1.5 s de comando: Δω ≈ 0.5°/s
- Con duty 50%: ω_promedio ≈ 0.25°/s
- **Observado: 0.53°/s.** Cuadra en orden de magnitud.

**Conclusión:** el giro lento NO es un bug. Es consecuencia directa de las constantes actuales (886 y prop_wash=0.35 en un barco con I_y=53333).

---

## 4. Preguntas abiertas

1. **¿Cuánto vale realmente `timon_torque` en `timonel_bridge.gd`?** El commit del 15/10 lo menciona como 2500, pero hay que confirmarlo en el archivo.
2. **¿Cuál es la inercia real del barco en Godot?** Jolt la calcula del `BoxShape_sailboat`. Sin ver las dimensiones del shape, no se puede comparar.
3. **¿El duty cycle es igual en ambos?** Confirmado: sí (1.5 s on, 1.5 s off).

---

## 5. Protocolo de sensibilidad propuesto

**Objetivo:** medir cómo responde la tasa de giro al cambio de `TIMON_TORQUE` en Python, manteniendo todo lo demás constante.

| Aspecto | Valor |
|---|---|
| Escenario | Barco detenido en (0,0), heading 0°, sin viento, sin meta |
| Comando | `timon=1, timon_ms=1500` cada 3 s, 30 s total |
| Variable independiente | `TIMON_TORQUE` ∈ {886, 1500, 2500, 4000, 5500} |
| Otras variables | Fijas: eficiencia cuadrática, prop_wash=0.35, I_y=53333 |
| Métricas | Δhdg_total, ω_promedio, α_inicial, sobrecorrección |
| Reps | 3 por valor (15 corridas) |

**Resultado esperado:** tabla que muestre si la relación torque → giro es lineal en el rango probado. De ahí sale el valor justificable.

---

## 6. Restricciones

- No modificar código hasta aprobar el protocolo.
- No asumir que 5500 es correcto.
- No cambiar fórmulas de eficiencia sin medir el efecto.
- Un solo factor variable por corrida.

---

## 7. Referencias cruzadas

- ficha_p37_beneteau_2026-10-16.md
- P39 (deadlock de arranque, ya resuelto)
- experimento_e2_frecuencia.py

---

## 8. Datos verificados (2026-10-16, tras auditoría)

### 8.1 Valor real del bridge

- `timonel_bridge.gd:10`: `@export var timon_torque: float = 2500.0`
- **Confirmado: 2500 N·m en headless.**
- Sin eficiencia por velocidad ni prop_wash.

### 8.2 Dimensiones del casco (Godot)

- `main.tscn`: `BoxShape3D size = Vector3(3, 1.5, 10)`.
- Inercia Jolt (aproximada como caja): `I_y = MASS·(3²+10²)/12 = 8000·109/12 = 72667 kg·m²`.
- Python usa `SIZE_X=4, SIZE_Z=8` → `I_y = 53333 kg·m²`.
- **Divergencia: 1.36×.**

### 8.3 Velocidad angular teórica

| Simulador | Torque efectivo | Damping angular | ω terminal (con duty 50%) |
|---|---|---|---|
| Python (0.21 m/s) | 310 N·m | 0.005/tick · 60 = 0.3/s | ~0.55°/s |
| Godot headless | 2500 N·m | 0.8/s | ~1.23°/s |

**Godot headless gira ~2.3× más rápido que Python.**

### 8.4 Conclusión del diagnóstico

El giro lento de Python **no es bug**. Es resultado de:
- Torque efectivo bajo (310 N·m por prop_wash=0.35).
- Damping angular bajo (0.005/tick).
- `I_y` grande (53333 kg·m²).

Si subimos `TIMON_TORQUE` a 2500 (igualando el bridge):
- Torque efectivo = 2500 × 0.35 = 875 N·m
- α = 875/53333 = 0.0164 rad/s² = 0.94°/s²
- ω terminal ≈ 1.55°/s (con duty)
- **≈ 3× la velocidad actual.**

Si además subimos el piso de efectividad (por ejemplo, prop_wash=0.5):
- Efectividad = 0.5
- α = 2500 × 0.5 / 53333 = 0.0234 = 1.34°/s²
- ω terminal ≈ 2.2°/s
- **≈ 4× la velocidad actual.**

### 8.5 Recomendación para el experimento de sensibilidad

En lugar de asumir 2500 como correcto, correr una curva completa:

`TIMON_TORQUE ∈ {886, 1500, 2500, 4000, 5500}` × 3 reps = 15 corridas.

Métricas: `Δhdg_total`, `ω_promedio`, `α_inicial`, distancia, sobrecorrección.

**La elección final se hace mirando la curva, no por semejanza con Godot.**

---

## 9. Curva de sensibilidad — resultado medido (2026-10-16)

Experimento: `experimento_e2b_sensibilidad.py`. Escenario: barco detenido en (0,0), heading 0°, sin viento, meta en (36,-6). Comando: timon=+1, timon_ms=1500, avance=1, cada 3 s, 30 s.

| TIMON_TORQUE | Δhdg total | ω medio | α inicial |
|---|---|---|---|
| 886 (base) | 15.22° | 0.533°/s | 0.00151 rad/s² |
| 1500 | 25.77° | 0.903°/s | 0.00255 rad/s² |
| 2500 | 42.94° | 1.505°/s | 0.00425 rad/s² |
| 4000 | 68.71° | 2.407°/s | 0.00680 rad/s² |
| 5500 | 94.47° | 3.310°/s | 0.00936 rad/s² |

### 9.1 Linealidad

La relación torque → velocidad angular es **lineal** en el rango medido. Los ratios entre pasos consecutivos coinciden con los ratios de torque con precisión de 3 cifras.

**Consecuencia:** la elección de TIMON_TORQUE es una decisión de comportamiento deseado, no de saturación del modelo. Cualquier valor entre 886 y 5500 produce un resultado predecible.

### 9.2 Repeticiones idénticas

Las 3 repeticiones por valor dieron **exactamente el mismo resultado** (al milésimo). El simulador es determinista en este escenario.

**Alcance:** la reproducibilidad está confirmada **para este escenario**. No demuestra determinismo universal bajo otras condiciones (viento, olas, semillas).

### 9.3 Límites del experimento

- No evalúa la navegación completa (el barco gira pero no llega a la meta).
- No evalúa oscilaciones de timón de largo plazo.
- No evalúa el acoplamiento con el controlador `timon_python`.
- Las repeticiones idénticas no cubren introducción de perturbaciones.

### 9.4 Aprobación del Director (vía Luna)

**Decisión:** avanzar con `TIMON_TORQUE = 2500` como primer candidato **experimental** (no calibración física validada).

**Condiciones:**
- Cambiar **solo** `TIMON_TORQUE`. Mantener eficiencia y `PROP_WASH_FACTOR`.
- Correr test de humo aislado y después E2, con criterios de aceptación definidos.
- Si 2500 no alcanza, informar antes de probar 4000.

### 9.5 Nota de precisión

**Paridad nominal ≠ paridad física.** Que Python y el bridge Godot usen ambos 2500 no significa que las fórmulas sean equivalentes. Las eficiencias y dampings siguen siendo distintos.
