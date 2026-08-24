# GODOT BUOYANCY PHYSICS — Receta de Flotabilidad Realista

Actualizado: 2026-08-24

## Referencia oficial
Repositorio: Buoyancy in Godot 4 (CBerry22).
URL: https://github.com/CBerry22/Buoyancy-in-Godot-4

## Archivos de referencia en el repo
- Water.gd → sincronizacion CPU/GPU y get_height.
- Cube.gd → flotabilidad por sondas y drag.
- water.gdshader → deformacion de olas en GPU.
- main.tscn → estructura de nodos y posicion de sondas.

## Estructura de nodos
Main (Node3D)
├── Water (MeshInstance3D) → Water.gd y water.gdshader
└── Cube (RigidBody3D) → Cube.gd
    ├── MeshInstance3D
    ├── CollisionShape3D
    └── ProbeContainer (Node3D)
        ├── 9 Marker3D distribuidos

## Flotabilidad basica
- depth = water.get_height(p.global_position) - p.global_position.y.
- Si depth > 0: apply_force(Vector3.UP * float_force * gravity * depth, offset).
- gravity se obtiene de ProjectSettings.

## Drag del agua
- En _integrate_forces:
  state.linear_velocity *= 1 - water_drag.
  state.angular_velocity *= 1 - water_angular_drag.

## Sincronizacion GPU-CPU
- water_time se acumula en CPU y se envia al shader.
- get_height muestrea la textura de ruido con get_pixelv.
- Mapeo de posicion mundial a UV usando wrapf.

## Proximos pasos
- Implementar WaterController basado en Water.gd.
- Implementar boat_controller.gd basado en Cube.gd.
- Crear ProbeContainer con 9 sondas.
- Probar flotabilidad en agua plana y luego con olas.
