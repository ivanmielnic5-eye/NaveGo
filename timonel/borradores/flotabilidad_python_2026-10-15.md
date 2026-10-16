# FLOTABILIDAD EN SIMULADOR PYTHON — IMPLEMENTACIÓN

**Fecha:** 2026-10-15
**Estado:** BORRADOR. Fuera del expediente.
**Origen:** hallazgo de divergencia Python↔Godot + pregunta del Director
("¿cómo fingir la tridimensionalidad?").

---

## 1. Giro conceptual

El simulador Python (`simulador_polaris.py`) era **2D plano**:
- `pos_y` y `vel_y` declarados pero nunca modificados.
- `FLOAT_FORCE = 120.0` declarado pero nunca aplicado.
- `PROBES_LOCAL` (12 puntos) declarados pero decorativos.
- Física solo en el plano XZ (avance, timón, viento).

Tras este cambio, es **2.5D con flotabilidad por resorte**:
- Dos puntos de flotabilidad (proa y popa).
- Empuje calculado por resorte vertical: F = K_FLOT * profundidad - C_VERT * vel_y.
- Cabeceo (pitch) real, amortiguado.
- Integración de `pos_y`, `vel_y`, `pitch`, `pitch_rate`.

## 2. Logro medido

Test de humo, sin viento ni comandos, 15 s:

| Variable | Comportamiento |
|---|---|
| pos_y | Se estabiliza en -0.381 m (Godot: -0.36 m — diferencia 21 mm) |
| pitch | Arranca en 0 (simétrico) o 15° (forzado), amortigua a 0 con ζ≈0.1 |
| Período de oscilación de pitch | ~1 s |
| Tiempo de estabilización vertical | ~3 s |

## 3. Constantes usadas

- K_FLOT = 45000.0 N/m
- C_VERT = 8000.0 N*s/m
- Z_PROA = 3.0 m
- Z_POPA = -3.0 m
- INERCIA_PITCH = 19000.0 kg*m^2
- C_PITCH = 30000.0 N*m*s/rad
- NIVEL_AGUA = 0.0 m

Calibración: hundimiento base esperado = 2 * K_FLOT * prof = MASS * GRAVITY.
Resolución: prof = (3500 * 9.8) / (2 * 45000) = 0.381 m. Coincide con lo medido.

## 4. Aislamiento por NAVEGO_RUN_DIR

El simulador Python ahora lee NAVEGO_RUN_DIR (mismo patrón que Godot).
Sin la variable: comportamiento normal.
Con la variable: escribe en la carpeta indicada.

Verificado:
- Sin variable: TELEMETRIA = /home/ivan/.local/share/.../telemetria.jsonl
- Con variable: TELEMETRIA = /tmp/test_isolation/telemetria.jsonl

Backups: simulador_polaris.py.pre-flotab, simulador_polaris.py.pre-aislamiento.

## 5. Corrección a P34

El documento divergencia_fisica_python_godot_2026-10-15.md decía:

> "Python: 12 puntos de flotabilidad"

Estaba mal. La realidad verificada era:

> "Python: 0 puntos. Constante declarada pero nunca aplicada."

Después de este cambio, la divergencia es de modelo, no de presencia:

| Aspecto | Python | Godot |
|---|---|---|
| Modelo | Resorte de 2 puntos | Malla de 168 puntos, Arquímedes real por punto |
| Puntos efectivos | 2 | 168 |
| Constante | K_FLOT, C_VERT globales | rho, g, area por punto |
| Cabeceo | Sí, por diferencia de fuerzas | Sí, por distribución de empujes |
| Roll | No implementado | Sí, natural por la malla 3D |

P34 debe actualizarse con esta corrección. La divergencia sigue existiendo
pero es de naturaleza distinta: no "uno tiene y otro no", sino "dos métodos
distintos de resolver el mismo problema físico".

## 6. Propuesta de regla R-23

Ninguna capacidad se declara imposible sin antes explorar caminos.

- Antes de escribir "no se puede", "no viable", "no existe forma":
  agotar tres alternativas concretas.
- Si las tres fallan: declarar "no encontrado con los métodos probados",
  no "imposible".
- Ejemplo fundacional (2026-10-15): se declaró Python sin flotabilidad.
  El Director preguntó "¿cómo fingirla?". Se resolvió con resorte de
  2 puntos en 30 min.

Esta regla es propuesta, no aprobada. Requiere decisión del Director para
incorporarse a PROTOCOLO.md.

## 7. Lo que este cambio habilita

- E1 es viable completo. Sin separar en "E1a (plano) + E1b (vertical)".
  Flotabilidad, cabeceo y hundimiento se pueden comparar.
- P35 cambia de enfoque. Ya no es "implementar flotabilidad en Python"
  (hecho). Es "calibrar el modelo Python para que sea compatible con Godot"
  y declarar tolerancias.
- El test de paridad activa (P35) puede evaluar 5 variables ahora:
  pos_x, pos_y, pos_z, hdg, pitch.
