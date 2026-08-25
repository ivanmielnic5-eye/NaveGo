# HUD CORE SPEC — Simulador NaveGo

Fecha: 2026-08-25

## 1. Propósito

Definir la estructura general del HUD del simulador y su conexión con los datos.

## 2. Principios

- El HUD es solo lectura. No modifica la física.
- La verdad física nunca se degrada.
- Cada cámara muestra información relevante para su propósito.
- La capa lúdica (escuela) se agrega encima sin romper las capas técnicas.

## 3. Fuentes de datos

- LandscapeV2 → Ground Truth (SOG, COG, posición, error diferencial)
- HeadingWindIntegrator → HDG, COG, SOG, viento aparente y real
- SailboatBody → posición y velocidad real
- WindController → viento ambiental aplicado

## 4. Estructura modular

HUD Core
├── HUDManager (activa/desactiva capas según cámara)
├── Capa Lateral
│   ├── Panel de viento
│   ├── Panel de movimiento
│   └── Barra de estado
├── Capa Cenital
│   ├── Panel de posición
│   ├── Panel de error diferencial
│   └── Mapa de zonas
└── Capa Proa
    ├── Brújula grande
    ├── Indicador de viento aparente
    └── Panel de rumbo deseado

## 5. Reglas de visualización

- No mostrar datos redundantes.
- Usar colores de estado: verde, amarillo, naranja, rojo.
- Textos legibles con tipografía clara.
- Paneles oscuros con acento cian.

## 6. Próximos pasos

- Implementar HUDManager.
- Crear capas de cámara.
- Conectar snapshots.
- Probar en tiempo real.
