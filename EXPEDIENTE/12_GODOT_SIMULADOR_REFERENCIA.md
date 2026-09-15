# 12 — REFERENCIA DEL SIMULADOR GODOT (Recuperada)

Fecha: 2026-09-15
Estado: REFERENCIA COMPLETA — Permite reconstruir el simulador.
Fuente original: Video "How to make things float in Godot 4" + repo CBerry22/Buoyancy-in-Godot-4 (ya no disponible en GitHub).

## Estructura de la escena
- Water (MeshInstance3D): PlaneMesh 500×500m, 500 subdivisiones.
  - Script: Water.gd
  - Material: ShaderMaterial con water.gdshader + FastNoiseLite
- Cube (RigidBody3D): masa 10 kg.
  - BoxMesh 5×1×10m + CollisionShape3D
  - Script: Cube.gd
  - ProbeContainer en y=-0.59
    - 9 Marker3D en cuadrícula

## Sondas
Esquinas: (2.5,0,5), (2.5,0,-5), (-2.5,0,5), (-2.5,0,-5)
Bordes/Centro: (2.5,0,0), (0,0,5), (0,0,0), (0,0,-5), (-2.5,0,0)

## Water.gd (get_height)
- Sincroniza tiempo: time += delta; set_shader_parameter("wave_time", time)
- Extrae imagen del ruido: get_seamless_image(512,512)
- get_height(world_position):
  - wrapf() para UV
  - Lee píxel del ruido
  - Retorna global_position.y + pixel.r * height_scale

## Cube.gd (flotabilidad)
- float_force: 1.3-1.4
- water_drag: 0.05
- water_angular_drag: 0.05
- _physics_process: para cada sonda, si depth > 0, apply_force(UP * float_force * gravity * depth)
- _integrate_forces: si submerged, amortigua linear_velocity y angular_velocity

## Para reconstruir
1. Crear proyecto Godot 4.
2. Crear Main.tscn con Water + Cube.
3. Copiar Water.gd y Cube.gd del documento original.
4. Crear water.gdshader con el vertex shader.
5. Configurar 9 sondas en ProbeContainer.
6. Ajustar float_force y water_drag según el tipo de embarcación.

## Prioridad
MEDIA. El simulador se puede reconstruir cuando haya tiempo.
No bloquea NaveGo.

## Scripts recuperados (2026-09-15)

### HeadingWindIntegrator.gd
- Calcula: heading, cog, sog, viento aparente
- Método: get_navigation_snapshot() → Dictionary
- Campos: heading_deg, cog_deg, sog_knots, apparent_wind_speed_ms, apparent_wind_angle_deg

### wind.gd
- Genera viento con ráfagas sinusoidales
- wind_strength base: 8.0, gust: sin(time*0.7)*3.0
- Aplica fuerza proporcional a masa

### simulador_config.json
- water: wave_frequency, wave_height, height
- boat: buoyancy_center_y (-0.3), mass (200 kg), angular_damping (0.9)

## Documentos de referencia
- GODOT_WATER_SIM_REFERENCE.md (agua)
- GODOT_BUOYANCY_PHYSICS.md (flotabilidad)
- GODOT_TELEMETRY_INTEGRATION.md (conexión)
- Cockpit.gd (script del panel)

## Lo que falta para reconstruir
- project.godot, main.tscn
- water.gd, water.gdshader
- Sailboat.tscn + script
- Capitania.gd
- sailboat.glb

## Ubicación de los originales
backups/backup_estructural_2026-09-02_03-56-56/ (y _57-02, _57-38)

## Prioridad
MEDIA. Reconstruible. No bloquea NaveGo.

## Arquitectura completa del simulador (2026-09-15)

### Puente de buceo físico (Buoyancy + LandscapeV2)
- Muestreo multipunto en el casco (proa, popa, babor, estribor).
- Fuerzas hidrodinámicas: empuje (buoyancy), resistencia (drag), escora (heel).
- Altura y normal del agua desde shader de LandscapeV2.

### Contrato de datos CapitaniaSnapshot
- Timestamp / Frame ID
- Cinemática del casco: posición (x,y,z), velocidad lineal/angular,
  orientación (Quaternion o Euler: Roll, Pitch, Heading)
- Vectores ambientales: viento real/aparente, oleaje
- Actuadores: rudder angle, sheet/trim

### Scenario Pipeline (FSM)
1. IDLE / ACQUIRE — línea base sin interferencias
2. TRIGGER — marca ventana crítica (ej. t0 a t0+30s)
3. PERTURBATION — inyecta variable (ráfaga, cambio de oleaje)
4. EVALUACIÓN — mide recuperación homeostática (inercia náutica)

### Nombres de archivos a buscar
- Capitania.gd / CapitaniaManager.cs
- HeadingWindIntegrator.gd (ya recuperado)
- LandscapeV2.gd / WaveSpectrum.gd
- SailboatController.gd / ShipPhysics.gd
- ScenarioRunner.gd

### Principio fundamental
Determinismo: mismo Scenario → misma salida bit a bit.
Permite validar algoritmos de navegación antes del hardware real.

### Relación con NaveGo real
- CapitaniaSnapshot usa el mismo contrato de datos que el bridge.
- Simulación y real comparables campo por campo.
