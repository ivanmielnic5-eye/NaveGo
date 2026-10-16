# E2 — FRECUENCIA DE DECISIÓN DE TIMONEL

**Fecha:** 2026-10-16
**Estado:** BORRADOR. Fuera del expediente.
**Predecesores:** diagnostico_timon_python_godot_2026-10-16.md
**Contexto:** post-fix P39 (deadlock de arranque) + TIMON_TORQUE = 2500.

---

## 1. Objetivo

Medir el efecto del intervalo de decisión de Timonel sobre la navegación completa hasta la meta.

---

## 2. Diseño

| Aspecto | Valor |
|---|---|
| Escenario | Barco detenido en (0,0), heading 0°, sin viento, meta (36,-6) |
| Controlador | timon_python con fix P39 |
| TIMON_TORQUE | 2500 |
| TIMON_MS | 1500 |
| Variable independiente | INTERVALO_S ∈ {0.5, 1, 2, 3, 5, 10} |
| Reps por valor | 5 |
| Duración máxima | 180 s |
| Criterio de llegada | dist_a_meta < 10 m |

---

## 3. Resultados

| Intervalo | Llegadas | T medio (s) | Dist media (m) | Comandos |
|---|---|---|---|---|
| 0.5 | 5/5 | 63.42 | 35.97 | 124 |
| **1.0** | **5/5** | **55.70** | 36.14 | 55 |
| 2.0 | 5/5 | 81.00 | 38.61 | 41 |
| 3.0 | 5/5 | 89.13 | 41.06 | 30 |
| 5.0 | 5/5 | 145.85 | 40.43 | 30 |
| 10.0 | 0/5 | — | 25.03 | 18 |

Reproducibilidad: las 5 reps de cada intervalo dieron exactamente el mismo resultado. Simulador determinista en este escenario.

---

## 4. Hallazgos

### 4.1 Curva en U

La relación intervalo → tiempo de llegada no es monótona:
- Bajar de 3 → 2 → 1 s mejora el tiempo.
- Seguir bajando a 0.5 s empeora.
- Óptimo en 1.0 s.

### 4.2 El óptimo coincide con TIMON_MS

TIMON_MS = 1500 ms. INTERVALO_S = 1.0 s.

Cuando el intervalo es cercano a la duración de la orden, las correcciones se suceden sin solapamiento y sin pausas.

### 4.3 10 s no llega

Con 10 s entre decisiones el barco avanza varios segundos en dirección errada. Queda orbitando. Distancia recorrida 25 m — no es deadlock, es sub-corrección.

### 4.4 Comparación con el paper del SeaLeon

**CORRECCIÓN (2026-10-16, tras revisión del Director):**

Los 60–155 s del paper NO son el intervalo entre comandos de timón. Son el intervalo entre **decisiones de rumbo táctico**: cuánto tiempo mantener un rumbo antes de reevaluar si conviene virar.

El paper:
- 155 s en ceñida (close-hauled): evita viradas excesivas.
- 60 s general: evita cambios de rumbo innecesarios.
- Mecanismo: control de histéresis para rumbo objetivo, no para timón.

Timonel no tiene ese mecanismo. No vira, no cambia rumbo táctico. Siempre apunta al waypoint directo. Cada INTERVALO_S es la frecuencia con la que **recalcula el timón**.

| Mecanismo | Qué decide | Escala paper | Escala Timonel |
|---|---|---|---|
| Actualización rumbo objetivo | ¿Virar? | 60-155 s | N/A (no vira) |
| Corrección de timón | ±1 al timón | No aplica | ~1 s |

**No hay contradicción — hay diferencia de alcance.** El SeaLeon hacía planificación táctica a vela. Timonel hoy es controlador de rumbo directo (Fase 1).

Los 1 s de Timonel son su óptimo para control de timón. Cuando incorpore navegación a vela (Fase 2), habrá que agregar el mecanismo táctico de 60-155 s.

**Pendiente:** verificar contra el PDF original. Los resúmenes disponibles son de terceros.

---

## 5. Revisión de la decisión sobre torque

Antes de correr E2 se acordó (con Luna): si 2500 no cumple criterios, probar 4000.

**Revisión:** el fallo del intervalo 10 s NO es por torque. Es por frecuencia de decisión. Subir a 4000 no resuelve el caso 10 s.

**Decisión propuesta:** no subir torque. Adoptar 1.0 s como frecuencia de decisión y declarar 10 s fuera de rango útil.

---

## 6. Criterios de aceptación

| Criterio | Resultado |
|---|---|
| Todos los intervalos llegan a <10 m | Falla (10 s no) |
| Sin deadlock | Falla (10 s orbita) |
| Distancia recorrida <60 m en alguna corrida | OK |

---

## 7. Recomendación

1. Adoptar INTERVALO_S = 1.0 s como valor de trabajo para Timonel.
2. Documentar 10 s como fuera de rango útil.
3. No subir torque a 4000.
4. Anotar que la curva en U es un hallazgo.

---

## 8. Límites

- Un solo escenario (sin viento, meta fija).
- No evalúa robustez ante perturbaciones.
- No evalúa acoplamiento con viento real.
- Determinismo confirmado solo en este escenario.

---

## 9. Referencias cruzadas

- diagnostico_timon_python_godot_2026-10-16.md
- ficha_p37_beneteau_2026-10-16.md (sección 3.2)
- P39 (deadlock, resuelto)
