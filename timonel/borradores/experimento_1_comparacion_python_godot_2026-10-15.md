# EXPERIMENTO 1 — CARACTERIZACIÓN DIRECCIONAL COMPARADA

**Fecha:** 2026-10-15
**Estado:** BORRADOR. Fuera del expediente.
**Predecesores:** experimento_0_godot_headless_2026-10-15.md, flotabilidad_python_2026-10-15.md, divergencia_fisica_python_godot_2026-10-15.md.

---

## 1. Qué es E1

E1 es una **caracterización direccional comparada** entre los dos simuladores de Polaris (Python y Godot). Responde la pregunta: ante entradas equivalentes, ¿en qué aspectos concuerdan y en cuáles divergen los dos modelos?

**E1 NO es:**
- Test de paridad física cuantitativa (eso es Nivel B, requiere unificar parámetros vía P35).
- Veredicto de calidad.
- Selección de modelo canónico.

## 2. Caso ejecutado — A.0 (barco quieto, sin viento)

- **Duración:** 15 s.
- **Estado inicial:** barco en reposo, sin comandos de timón ni avance.
- **Viento:** apagado por override (`NAVEGO_WIND_STRENGTH=0`, `NAVEGO_WIND_DIR_DEG=0`).
- **Comando único:** `timon=0, avance=0` a los 1 s (sin efecto físico).

**Ejecución:**
- Python: `python3 simulador_polaris.py 15`.
- Godot: `./run_headless.sh` con `comandos_in.json`. Run ID `20261015_203108_test`.

## 3. Datos comparados (t=15 s)

| Variable | Godot | Python | Delta |
|---|---|---|---|
| pos_x (delta) | +0.028 m | 0.000 m | 28 mm |
| pos_y (absoluto) | +0.066 m | -0.381 m | 447 mm |
| pos_z (delta) | +0.096 m | 0.000 m | 96 mm |
| pitch_deg | -1.44° | 0.00° | 1.44° |
| roll_deg | +4.41° | 0.00° | 4.41° |
| sog_kn | 0.001 | 0.000 | ~0 |

**Estado inicial de cada simulador:**
- Godot: pos inicial `(5.5, 0, 0)`. Agua a `water_level=0`. El barco flota arriba del origen.
- Python: pos inicial `(0, 0, 0)`. Agua a `NIVEL_AGUA=0`. El barco se hunde a -0.38 m hasta equilibrio.

## 4. Clasificación de divergencias

### 4.1 pos_y — divergencia de convención (no física)
Diferencia de 447 mm en valor absoluto. Pero:
- Godot: el barco flota en pos_y ≈ +0.07 (arriba del origen).
- Python: el barco flota en pos_y ≈ -0.38 (abajo del origen).

**No es divergencia física.** Es que el origen (pos_y=0) significa cosas distintas en cada modelo. Godot tiene el agua coincidente con la línea de flotación; Python tiene el origen por encima. **Ambos se asientan y oscilan de forma similar** (±50 mm).

### 4.2 roll — gap estructural
Godot: +4.41° por gust residual del viento. Python: 0.00°, no lo modela.

**Python no tiene roll.** Es un quinto grado de libertad (rotación alrededor del eje longitudinal) que requiere torque asimétrico en los puntos de flotabilidad. Documentado como limitación explícita.

### 4.3 Deriva en pos_z — divergencia ajustable
Godot: +96 mm en z. Python: 0 mm.

**Causa:** el `gust_amplitude=0.5` de `wind.gd` no se desactivó con el override de `wind_strength`. El gust residual mueve el barco ligeramente. Divergencia menor y ajustable.

### 4.4 pitch — compatible
Godot: -1.44°. Python: 0.00°.

**Diferencia dentro de la tolerancia esperada.** El -1.44° de Godot es efecto del gust lateral residual. Con gust en cero, debería converger a 0.

### 4.5 sog — compatible
Ambos ~0. El barco no se mueve significativamente.

## 5. Lo que E1 NO demuestra

- Equivalencia física cuantitativa.
- Corrección de calibración.
- Determinismo entre corridas sucesivas.
- Que Godot sea más preciso que Python (o al revés).
- Que la dinámica del barco real coincida con alguno de los dos.

## 6. Próximos pasos

1. **Override de `gust_amplitude=0`** en `wind.gd` (mismo patrón que `wind_strength`). Elimina el ruido de viento residual.
2. **Repetir A.0 con gust apagado** para verificar si pitch y pos_z convergen a 0 en ambos.
3. **Caso B — avance:** comando `avance=1, avance_ms=1500` cada 3 s durante 30 s. Comparar dirección y magnitud de la aceleración.
4. **Caso C — timón con velocidad previa:** secuencia común de aceleración seguida de pulsos de timón. Comparar tasa de giro.
5. **Decisión sobre roll en Python:** implementarlo o documentarlo como aproximación 2.5D.

## 7. Referencias cruzadas

- experimento_0_godot_headless_2026-10-15.md — infraestructura headless.
- flotabilidad_python_2026-10-15.md — implementación de flotabilidad en Python.
- divergencia_fisica_python_godot_2026-10-15.md — divergencias conocidas antes de E1.
- P34, P35 en EXPEDIENTE/PENDIENTES.md — paridad activa.

## 8. Estado

**Resultado de E1-A.0:** las respuestas de ambos simuladores son **direccionalmente compatibles** con divergencias clasificables. Ninguna divergencia bloquea la continuación de E1. El siguiente experimento (A.0 con gust apagado) permite cerrar el mapa del caso sin viento antes de avanzar a B y C.
