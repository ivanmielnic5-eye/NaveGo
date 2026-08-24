# SIMULATOR KNOWLEDGE CORPUS — NaveGo / LOGOS

Actualizado: 2026-08-24

## Proposito
Compilar el conocimiento tecnico que alimenta el simulador Godot.
Sirve como fuente de consulta para evaluar, estudiar y decidir.

## Conceptos clave
- Ruido procedural: generacion matematica de variaciones naturales.
- NoiseTexture2D: textura procedural basada en FastNoiseLite.
- Mapa de alturas: valores de gris que representan elevacion.
- FastNoiseLite: generador de ruido con frecuencia, seed y octavas.
- Shader de agua: desplaza vertices en la GPU.
- Sincronizacion GPU-CPU: usar el mismo generador y el mismo tiempo.

## Flotabilidad
- Arquimedes: fuerza hacia arriba proporcional al volumen sumergido.
- Profundidad: water_height - body_y_position.
- Sondas: Marker3D distribuidos para cuerpos alargados.
- Drag: amortiguamiento de velocidad lineal y angular en _integrate_forces.
- Fuerza central: se aplica en el centro de masa.

## Funciones clave de Godot
- set_shader_parameter("wave_time", value): sincroniza tiempo con la GPU.
- get_pixel(): muestrea textura de ruido en la CPU.
- _integrate_forces(state): lugar seguro para aplicar fuerzas de fluidos.
- apply_force(force, position): aplica fuerza en un punto relativo.
- linear_velocity, angular_velocity: control directo en _integrate_forces.

## Decisiones adoptadas
- COG ≠ Heading.
- COG se calcula desde linear_velocity, no desde la rotacion.
- SOG se expresa en nudos.
- COG se normaliza a 0-359 grados.
- El simulador es un Project Adapter separado de NaveGo real.
- El agua debe tener una funcion get_height en CPU.

## Proximos experimentos
- Validar la sincronizacion de olas visuales y fisica.
- Probar flotabilidad con sondas en la ballena.
- Ajustar drag y amortiguamiento para comportamiento organico.
- Crear escenarios de tormenta y deriva.

## Notas
La sincronizacion temporal es el punto mas importante.
Si el shader y la CPU no comparten la misma formula, habra error.
La textura de ruido es solo una herramienta; FastNoiseLite es mas flexible.
