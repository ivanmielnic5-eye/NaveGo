# LANDSCAPE DE PRUEBAS — Simulador NaveGo

Fecha: 2026-08-25
Propósito: Diseñar un entorno físico simulado para probar sensores, robustez y autoconciencia del sistema.

## 1. Concepto

El landscape no es decorativo. Es un banco de pruebas hidrodinámico y sensorial.
Debe permitir someter al velero a condiciones límite y registrar cómo responde.

## 2. Zonas funcionales

| Zona | Nombre | Medidas aprox. | Función de prueba |
|---|---|---|---|
| A | Bahía de Calibración | 100 x 100 m | Agua calma, viento suave constante. Punto de partida. |
| B | Paso de los Morros | 20 m ancho, 300 m largo | Paredes rocosas altas, pérdida de WiFi, viento arrachado. |
| C | Canal de la Corriente | 15 m ancho, 400 m largo | Corriente fuerte que arrastra al velero. |
| D | Rompeolas de Proximidad | 60 m ancho | Obstáculos fijos y flotantes para sensores. |
| E | Estrecho de Sonda | 25 m ancho | Fondo variable: piedras, bancos de arena, profundidad mínima. |
| F | Zona de Pérdida Total | 50 x 50 m | Sin GPS, sin WiFi, sin viento, agua en calma. |

## 3. Variables por zona

| Zona | WiFi | GPS | Viento | Corriente | Profundidad | Obstáculos |
|---|---|---|---|---|---|---|
| A | Alta | Alta | Suave | Nula | 10 m | Ninguno |
| B | Nula | Media | Ráfagas laterales | Leve | 8 m | Paredes laterales |
| C | Alta | Alta | Leve | Fuerte | 12 m | Ninguno |
| D | Alta | Alta | Suave | Nula | 6 m | Muchos |
| E | Media | Media | Suave | Leve | Variable 1-5 m | Lecho rocoso |
| F | Nula | Nula | Nula | Nula | 15 m | Ninguno |

## 4. Autoconciencia del sistema

El simulador debe transmitir en todo momento:

- Dato directo: viene de sensor simulado confiable.
- Dato estimado: calculado por dead reckoning o filtro.
- Dato perdido: sin señal, sin actualización.
- Margen de error: porcentaje o rango estimado.

Ejemplo en Paso de los Morros:

GNSS: PERDIDO
WiFi: SIN SEÑAL
Posición: ESTIMADA (± 5 m)
Rumbo: ESTIMADO por IMU (± 2°)
Velocidad: ESTIMADA por corredera (± 0.5 kn)
Alerta: NO CONFIABLE — navegación por estima

Regla: Evidencia antes que certeza.

## 5. Implementación futura en Godot

1. Crear malla de terreno con desniveles (CSG o heightmap simple).
2. Agregar el mar actual como plano de agua.
3. Generar paredes rocosas con StaticBody3D.
4. Crear áreas de señal con Area3D para WiFi/GPS.
5. Crear corrientes como campos de fuerza locales.
6. Crear obstáculos con etiquetas para sensores de proximidad.
7. Registrar en HUD de diagnóstico qué sensores están activos y qué incertidumbre hay.

## 6. Lo que NO se hará hoy

No tocar main.tscn ni scripts.
Solo definir croquis y requerimientos.
