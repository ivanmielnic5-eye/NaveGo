# GODOT AI BOOTSTRAP — Entrada oficial para IAs (Simulador NaveGo)

Actualizado: 2026-08-24

## Proposito
Este archivo es el punto de entrada para cualquier IA que vaya a trabajar en el simulador Godot de NaveGo.
Evita repetir contexto. Cualquier IA debe leerlo antes de proponer o ejecutar cambios.

## Que es el simulador
- Un clon de entrenamiento y validacion de NaveGo, separado de la app movil.
- Es un Project Adapter del ecosistema LOGOS.
- Permite simular oleaje, viento, flotabilidad y escenarios de navegacion sin hardware real.
- No reemplaza a NaveGo real; lo complementa.

## Estado actual (segun informe tecnico reciente)
- Escena principal: MainSimulator (Node3D) con main_simulator.gd.
- Agua: Water (MeshInstance3D) con shader ocean.gdshader.
- Velero: Sailboat (RigidBody3D) con flotabilidad y controles.
- Camara: CameraPivot > Camera3D.
- Instrumento: CompassHUD (Control) con COG, SOG, HDG y aguja.
- Sondas: Probes (Node) con Marker3D distribuidos en el casco.
- Referencia norte: TrueNorth (Node3D).
- Controlador de agua: WaterController (Node3D) con get_water_height().

## Documentos vivos relacionados
- GODOT_SIMULATOR_SPEC.md → especificacion de la brujula y escenas.
- GODOT_TELEMETRY_INTEGRATION.md → formulas de SOG, COG, HDG, lat/lon virtual.
- GODOT_BUOYANCY_PHYSICS.md → receta de flotabilidad y sincronizacion GPU-CPU.
- SIMULATOR_SYMBIOSIS_SPEC.md → roles de IAs y fases del simulador.
- SIMULATOR_KNOWLEDGE_CORPUS.md → conceptos y resumenes tecnicos.
- SIMULATION_REFERENCES.md → repositorios y enlaces de referencia.
- PROJECT_STATE.md → estado general del proyecto.

## Reglas no negociables
1. No tocar la app movil NaveGo (App.tsx, useNaveGoTracker, SQLite, servidor).
2. No tocar el servidor simulate.js ni los scripts de arranque de NaveGo.
3. No inventar nombres de nodos: si no se sabe, pedir el arbol actual.
4. Una intervencion a la vez.
5. Evidencia antes que certeza: distingue IMPLEMENTADO, PROBADO, OBSERVADO, VALIDADO.
6. COG ≠ Heading: COG viene de la velocidad, Heading de la proa.
7. Todo cambio debe poder revertirse.
8. Entregar scripts completos con viñeta de copiar, no fragmentos sueltos.

## Flujo de trabajo de cualquier IA
1. Leer este archivo.
2. Leer GODOT_BUOYANCY_PHYSICS.md y SIMULATOR_KNOWLEDGE_CORPUS.md.
3. Pedir el arbol de nodos actual si no esta claro.
4. Proponer el cambio de mayor valor y menor riesgo.
5. Implementar solo con confirmacion del Director.
6. Probar y documentar en TEST_LOG.md.

## Referencias externas
- Repositorio Buoyancy in Godot 4 de CBerry22.
- URL: https://github.com/CBerry22/Buoyancy-in-Godot-4
- Commit de referencia: e4108e585b9552ed0aeefb6ecac07540670c9bd2

## Meta
Que cualquier IA (DeepSeek, ChatGPT, Claude, Gemini) entre al simulador con el mismo contexto, sin que el Director tenga que repetir informacion.

## 2026-08-24 — Referencia oficial confirmada

### Repositorio
- Buoyancy in Godot 4 (CBerry22).
- Contiene Water.gd, Cube.gd, water.gdshader y main.tscn.

### Aplicacion en NaveGo
- WaterController debe implementar get_height como Water.gd.
- boat_controller.gd debe aplicar flotabilidad como Cube.gd.
- Se debe crear ProbeContainer con 9 sondas.

### Estado
Documentado y listo para implementar en Godot.
