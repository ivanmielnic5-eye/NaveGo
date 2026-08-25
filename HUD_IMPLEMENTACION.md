# HUD IMPLEMENTACIÓN — Pasos en Godot

Fecha: 2026-08-25

## 1. Crear HUDManager.gd
- Nodo raíz del HUD.
- Lee la cámara activa.
- Activa/desactiva capas CanvasLayer correspondientes.

## 2. Crear capas de cámara
- CapaLateral (CanvasLayer)
- CapaCenital (CanvasLayer)
- CapaProa (CanvasLayer)

## 3. Conectar fuentes de datos
- HUDManager referencia a LandscapeV2.
- HUDManager referencia a HeadingWindIntegrator.
- Cada capa lee los snapshots y actualiza Labels.

## 4. Prueba de integración
- Ejecutar F6.
- Cambiar cámaras con 1, 2, 3.
- Verificar que cada vista muestre su información.
- Verificar que los datos se actualicen en tiempo real.

## 5. Próximos pasos
- Mejorar estética visual.
- Agregar capa lúdica para escuela.
- Integrar con misiones y feedback.
