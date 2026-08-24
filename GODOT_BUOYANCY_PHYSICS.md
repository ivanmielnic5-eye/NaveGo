# GODOT BUOYANCY PHYSICS — Receta de Flotabilidad Realista

Actualizado: 2026-08-24

## Proposito
Documentar la logica exacta para que barcos y objetos floten y reaccionen al oleaje.
Conectar la fisica de la CPU con el movimiento visual de la GPU.

## Estructura de nodos
RigidBody3D (Barco)
├── MeshInstance3D (Modelo visual)
├── CollisionShape3D (Colision)
└── ProbeContainer (Node)
    ├── Marker3D (Proa)
    ├── Marker3D (Centro)
    ├── Marker3D (Popa)
    └── ... más sondas según tamaño

## Flotabilidad basica
- Variable float_force para calibrar.
- gravity se obtiene de ProjectSettings.
- water_height es la altura de la superficie.
- depth = water_height - global_position.y.
- Si depth > 0, aplicar apply_central_force(Vector3.UP * float_force * gravity * depth).

## Resistencia del agua (Drag)
- No modificar linear_velocity en _physics_process.
- Usar _integrate_forces(state).
- Si submerged: state.linear_velocity *= (1.0 - linear_drag).
- Si submerged: state.angular_velocity *= (1.0 - angular_drag).

## Sincronizacion GPU-CPU para olas
- No usar TIME nativo del shader.
- Acumular wave_time en GDScript.
- Enviar wave_time al shader con set_shader_parameter.
- Crear funcion get_height(world_pos) en la CPU.
- Mapear world_pos a UV y muestrear la misma textura de ruido.
- Compensar la posicion global del nodo de agua.

## Flotabilidad avanzada con sondas multiples
- Colocar varios Marker3D distribuidos en el casco.
- Para cada sonda:
  water_height = get_height(probe.global_position).
  depth = water_height - probe.global_position.y.
  force = Vector3.UP * float_force * gravity * depth.
  apply_force(force, probe.global_position - global_position).
- Con muchas sondas, float_force debe ser baja (ej. 1.4).

## Calibracion recomendada
1. Ajustar float_force hasta que flote estable.
2. Ajustar linear_drag y angular_drag para evitar rebotes.
3. Probar con agua plana primero.
4. Despues probar con olas sincronizadas.

## Metricas para Project Adapter (LOGOS)
- Pitch (cabeceo) y Roll (balanceo).
- Yaw (guiñada).
- Fuerzas por sonda.
- Velocidad angular.
- Evidencia de estabilidad por escenario.

## Nota
Sistema preparado para el simulador Godot, no para NaveGo real.
Esta receta resuelve el desacople entre shader y fisica.
