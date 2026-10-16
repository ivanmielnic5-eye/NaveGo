# DIVERGENCIA DE FÍSICA — Python vs Godot

**Fecha:** 2026-10-15
**Estado:** BORRADOR. Fuera del expediente.
**Origen:** hilo 2026-10-15, investigación de capacidades del simulador.
**Investigación de campo:** Deep. **Auditoría:** GPT. **Decisión:** Director.

---

## 1. Hallazgo

Existen dos implementaciones independientes de la física del velero Polaris:

- **Python:** `timonel/simulador_polaris.py` — usado para entrenamiento de Timonel.
- **Godot:** `~/interfaz/scripts/float_cube.gd` — usado para operación y visualización.

**No representan el mismo modelo físico.** Divergen en parámetros fundamentales, no solo en detalles.

---

## 2. Tabla de diferencias

| Parámetro | Python | Godot | Ratio |
|---|---|---|---|
| Puntos de flotabilidad | 12 (grilla regular) | 168 (malla .glb Blender) | ×14 |
| Modelo de flotabilidad | Constante `FLOAT_FORCE=120.0` | Arquímedes real por punto | Distinto |
| Densidad agua | No declara | 1025 kg/m³ | — |
| Centro de masa | (0, -1.5, 0) | (0, -1.2, 0) | 0.3 m |
| Drag frontal | 0.0134 | 0.05 | ×3.7 |
| Drag lateral | 0.05 | 1.20 | **×24** |
| Drag angular | 0.005 | 0.35 | **×70** |
| Drag vertical | **No existe** | 45.0 | Falta en Python |
| Masa | 3500 kg | (gestionado por RigidBody3D) | — |

El **drag lateral ×24 y angular ×70** son las divergencias más severas. Implican que:

- En Python el barco **deriva más** y **gira más fácil**.
- En Godot el barco **deriva menos** y **gira con más dificultad**.

---

## 3. Implicación operativa

Timonel (LLM o Python puro) **entrena contra el modelo Python** pero **opera contra el modelo Godot**.

Consecuencia concreta: un controlador que aprendió a maniobrar en un barco resbaladizo (Python) va a sobrecorregir cuando maneje un barco que agarra (Godot). Los comandos van a ser agresivos para un timón que responde más de lo esperado.

No es un bug. Es un patrón: **cuando la misma cosa se implementa dos veces, se desincroniza.** Le pasó al hashing (P29/P31/P32, resuelto por D-2026-0015/16). Le pasó a la física ahora.

---

## 4. Estado de cada modelo

- **Godot (`float_cube.gd`):** modelo vigente. Extrae la malla del `.glb` de Blender. Flotabilidad real por Arquímedes punto a punto. Es el barco que se ve y se opera.
- **Python (`simulador_polaris.py`):** modelo histórico. 12 probes. No fue actualizado tras la mejora en Blender/Godot.

---

## 5. Recomendación

**Principio:** los simuladores Python y Godot deben ser **siameses**. No dos modelos distintos — dos implementaciones del mismo modelo, con parámetros compartidos y verificación activa.

**Pero la divergencia no siempre es un error.** A veces se querrá probar diferencias deliberadamente (ej: comparar un controlador en dos físicas distintas). Por eso el mecanismo **advierte**, no bloquea — salvo cuando la divergencia invalida específicamente lo que la corrida quiere medir.

### 5.1. Fuente única de parámetros

Todos los parámetros físicos (masa, drags, torque, puntos de flotabilidad, densidad del agua, centro de masa) viven en **un único archivo JSON** leído por ambos simuladores.

- Godot: lo lee al arrancar.
- Python: lo lee al importar.
- Si un parámetro cambia, cambia en un solo lugar.

### 5.2. Verificación activa de paridad

Script que corre el mismo input en ambos simuladores y compara trayectorias:

1. Estado inicial idéntico (posición, rumbo, viento, semilla).
2. Mismos comandos inyectados a ambos.
3. Comparar `pos_x/y/z` y `hdg_deg` tick por tick.
4. Reportar divergencia con nivel:
   - `OK` — divergencia dentro de tolerancia.
   - `WARNING` — divergencia supera tolerancia, pero la corrida sigue.
   - `INCOMPATIBLE` — la divergencia invalida específicamente la variable que la corrida quiere medir.

### 5.3. Check de integridad en el arranque

Antes de cada corrida, el sistema verifica:

- Que ambos simuladores declaran la misma versión del archivo de parámetros.
- Si difieren, se emite `WARNING` con el detalle.
- Si la corrida declara medir una variable que está entre las divergentes, se emite `INCOMPATIBLE` (y ahí sí se bloquea esa corrida puntual).

### 5.4. Estado actual

Hoy no hay ninguna de las tres piezas. La divergencia entre Python y Godot es estructural. Se documenta como **deuda a resolver**, no como estado aceptable.

## 6. Archivo histórico

- El modelo Python actual (12 probes) queda **histórico**. No se borra. No se modifica sin decisión.
- Las corridas previas al 2026-10-15 se registran como **"modelo_fisico: python-histórico"** en cualquier análisis retrospectivo.
- La migración de Python al modelo de Godot es **decisión pendiente**, no auto-ejecutable.

---

## 7. Referencias

- `timonel/simulador_polaris.py:55-59` (12 probes)
- `~/interfaz/scripts/float_cube.gd:24-30` (constantes drag)
- `~/interfaz/scripts/float_cube.gd:168` (malla, comentario)
- D-2026-0015, D-2026-0016 (patrón de unificación previo, sobre hashing)
- EXPEDIENTE/PENDIENTES.md — P34 (este hallazgo)
