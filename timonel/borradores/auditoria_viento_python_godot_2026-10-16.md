# AUDITORÍA VIENTO — PYTHON vs GODOT

**Fecha:** 2026-10-16
**Estado:** BORRADOR. Solo lectura, sin cambios de código.
**Origen:** bloqueante del Bloque 1 (paridad de viento).

---

## 1. Convención de Python

**Ubicación:** simulador_polaris.py:142-143
Comentario del código: "Direccion: hacia donde sopla. 0=norte (sopla de sur a norte)"

**Cálculo:** simulador_polaris.py:231-234
  rad = radians(viento_direccion_deg)
  viento_x = sin(rad) * fuerza_n
  viento_z = -cos(rad) * fuerza_n

**Interpretación:** ángulo = dirección hacia donde SOPLA el aire. 0° = sopla hacia el norte.

## 2. Convención de Godot

**Ubicación:** wind.gd:13. Sin comentario explicativo.

**Cálculo:** wind.gd:68-69
  angle_rad = deg_to_rad(wind_direction_deg + dir_offset)
  wind_direction = Vector3(sin(angle_rad), 0.0, cos(angle_rad)).normalized()

**Nota:** get_wind_direction() devuelve wind_direction_deg + 90.0. Sugiere convención interna distinta.

## 3. Tabla cardinal

Mapeo verificado: X = este, −Z = norte (atan2(vel_x, -vel_z), línea 176).

| Ángulo | Python | Dirección | Godot | Dirección | Coinciden |
|---|---|---|---|---|---|
| 0° | (0, −1) | Norte | (0, +1) | Sur | NO |
| 90° | (+1, 0) | Este | (+1, 0) | Este | Sí |
| 180° | (0, +1) | Sur | (0, −1) | Norte | NO |
| 270° | (−1, 0) | Oeste | (−1, 0) | Oeste | Sí |

**Conclusión:** reflexión sobre eje E-O. Componentes N/S invertidos, E/W coinciden.
**No concluyente:** Godot no declara semántica de wind_direction_deg.

## 4. Fuerza y torque

**Python:** fuerza acumulada en fx/fz (aplicada al CoM). Torque explícito en torque_viento (líneas 235-250). VIENTO_TORQUE_POR_NUDO = 20.0.

**Godot:** solo apply_central_force al CoM. Sin torque explícito.

**Diferencia estructural:** Python tiene torque de viento; Godot no.

## 5. Telemetría aws/awa

**Python:** hardcodeado en 0.0 (líneas 418-419). Bloqueante para Bloque 2.

**Godot:** calculado en HeadingWindIntegrator.gd:67-75. Monitor.gd los lee y convierte.

## 6. Opciones

1. Alinear Python con Godot (invertir Z, activar aws/awa). Requiere revalidar E1 y E2.
2. Mantener Python, agregar velas (riesgo: semántica distinta).
3. Modelo experimental separado (dos vientos conviven).
4. Solo prueba de componente de velas. **← AUTORIZADA por Luna 2026-10-16.**

## 7. Decisión 2026-10-16 (Luna)

**Opción 4 aprobada.** Solo prueba aislada de la función de efectividad de velas.
**Pendientes:** convención de viento, activación aws/awa Python, justificación torque de viento.

## 8. Referencias

- plan_fase_2_2026-10-16.md (secciones 2.2, 2.3)
- contraste_cobertura_python_godot_2026-10-15.md
