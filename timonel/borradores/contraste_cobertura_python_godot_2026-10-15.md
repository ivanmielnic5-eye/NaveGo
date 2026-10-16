# CONTRASTE DE COBERTURA — PYTHON vs GODOT

**Fecha:** 2026-10-15
**Estado:** BORRADOR. Fuera del expediente.
**Origen:** inspección de código solicitada por Luna tras el rediseño de E1.
**Predecesores:** experimento_0, flotabilidad_python, experimento_1.

---

## 1. Objetivo

Mapear qué fenómenos físicos representa cada simulador, con evidencia de línea
de código. Distinguir "cobertura" (el modelo lo contempla) de "validación"
(el modelo representa la realidad). Este documento cubre lo primero.

---

## 2. Tabla de cobertura

| Fenómeno | Python | Godot | Evidencia |
|---|---|---|---|
| Gravedad vertical | Sí | Sí | Py:339 · Jolt automático |
| Flotabilidad | Sí, 168 pts | Sí, 168 pts | Py:319-337 · G float_cube:241 |
| Olas de Gerstner | Sí | Sí | Py:altura_agua() · G water.gd |
| Drag forward | Sí, lineal | Sí, cuadrático | Py:245-260 · G float_cube:262 |
| Drag lateral | Sí, lineal | Sí, cuadrático | Py:245-260 · G float_cube:262 |
| Drag vertical | Sí, lineal (C_VERT) | Sí, cuadrático | Py:337 · G float_cube:271 |
| Drag angular | Sí, lineal | Sí, cuadrático | Py:303,342,346 · G float_cube:266 |
| Viento sobre casco | Sí (fuerza + torque) | Sí (solo fuerza central) | Py:230-250 · G wind.gd:96 |
| **Viento sobre velas** | **No** | **Sí (factor por ángulo)** | — · G wind.gd:69-74 |
| Torque de timón | Sí (con efectividad + prop_wash) | Parcial (rudder sí, bridge no) | Py:263 · G rudder:63 · bridge:157 |
| Fuerza de avance | Sí | Sí | Py:220 · G bridge:160 |
| **Prop walk (reversa)** | **Sí** | **No** | Py:280 · — |
| CoM aplicado en torque | No | Sí (motor Jolt) | Py:342 · G float_cube:206 |
| Colisiones | No | No (sin obstáculos) | — |
| Roll por viento | Parcial (malla asimétrica) | Sí (malla + velas) | Py:346 · G |

---

## 3. Hallazgos estructurales

### 3.1 Modelos conceptualmente distintos, no solo parámetros

- **Python:** el viento sobre el casco aplica **fuerza + torque explícito de yaw**.
- **Godot:** el viento sobre el casco aplica **solo fuerza central**. El torque
  de yaw emerge del empuje lateral sobre las velas, que están fuera del CoM.

**No es un parámetro distinto. Es cómo se genera el yaw.**

### 3.2 Godot modula el viento por velas; Python no

`wind.gd:69-74`:
- Calcula `eff_mayor` y `eff_foque` según ángulo entre vela y viento.
- La fuerza total del viento depende de la posición de las velas.

Python aplica viento pleno sin importar velas. Esto hace que la comparación
"con velas izadas" no sea válida entre ambos modelos.

### 3.3 Python sub-representa el roll

Python tiene `roll` y `roll_rate`, pero solo la malla de 168 puntos genera
roll por asimetría. Falta confirmar si el viento contribuye al roll en Python
como lo hace en Godot.

### 3.4 Prop walk solo en Python

Python modela `PROP_WALK_TORQUE = 1800` para reversa a baja velocidad.
Godot no lo tiene implementado.

---

## 4. Implicación para el benchmark

Dos modelos con coberturas distintas:

| Pregunta experimental | Modelo viable |
|---|---|
| ¿El controlador llega a la meta en plano XZ? | Ambos |
| ¿Respeta márgenes con olas? | Ambos (con tolerancia) |
| ¿Cómo responde al viento sobre velas? | Solo Godot (hoy) |
| ¿Cómo responde a prop_walk en reversa? | Solo Python |
| ¿Cómo se comporta con roll inducido por viento? | Solo Godot (hoy) |
| ¿Cómo se comporta con la geometría exacta del casco? | Solo Godot (hoy) |

La decisión sobre qué modelo usar en cada comparación es del Director.
La recomendación técnica es: **no declarar ninguno canónico hasta que
la cobertura de ambos sea comparable** o hasta que una referencia externa
indique cuál representa mejor la realidad.

---

## 5. Pendientes derivados

### P36 — Velas en simulador Python
Python puede tener velas. No hay impedimento técnico. Es una decisión de
alcance que se postergó. Implementar `vela_mayor_deg` y `vela_foque_deg`
en `Barco`, análogo a Godot. Habilita Fase 2 del curriculum en Python.

### P37 — Referencia externa: Beneteau First Class 8
Paper: "A Hardware-in-the-Loop Simulator to Optimize Autonomous Sailboat
Performance in Real Ocean Conditions" (MDPI, 2023).
URL: https://www.mdpi.com/2077-1312/11/6/1104
Objetivo: verificar si publica ecuaciones, coeficientes, ensayos de tanque
y registros de navegación recuperables. Si sí, anclar parte de la física
en evidencia externa. Si no, no convertirlo en proyecto interminable.

### P38 — Contraste de cobertura como base para E1 extendido
Este documento es la base. Cuando se decida qué modelo usar para cada
pregunta experimental, actualizar esta tabla con la decisión tomada.

---

## 6. Referencias cruzadas

- experimento_0_godot_headless_2026-10-15.md
- experimento_1_comparacion_python_godot_2026-10-15.md
- flotabilidad_python_2026-10-15.md
- divergencia_fisica_python_godot_2026-10-15.md
- P34, P35 en EXPEDIENTE/PENDIENTES.md
