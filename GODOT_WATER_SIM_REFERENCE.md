# GODOT WATER SIM REFERENCE — Simulación de agua en Godot 4

Fuente: Video "WATER SIMULATION in Godot 4" de Crigz Vs Game Dev
Fecha de guardado: 2026-08-25

## Resumen técnico

### 1. Doble búfer con Viewport Textures
- La simulación de ondas usa un Viewport que renderiza a una textura.
- Se alimenta la textura de vuelta al shader como uniform.
- El canal R almacena el estado actual; el canal G el anterior.
- En Godot 4.0 beta, configurar el Viewport en 514x514 evita un bug.

### 2. Colisiones con la cámara invertida
- Una cámara ortográfica mira desde abajo hacia la superficie.
- Renderiza solo objetos en la capa 20.
- El canal B guarda la colisión para el siguiente pase.
- Si hay colisión nueva, el agua se eleva; si desaparece, baja.

### 3. Desplazamiento de vértices
- El shader de vértices muestrea la textura de simulación.
- `Amplitude` controla la altura máxima de las olas.
- Se suma al vértice: `VERTEX.y += height * Amplitude`.

### 4. Profundidad y ley de Beer
- Se lee el depth buffer y se decodifica con la matriz de proyección.
- La ley de Beer (transmitancia exponencial) define opacidad según profundidad.
- Mezcla `shallow_color` y `deep_color` para el albedo.
- Aguas poco profundas transparentes; profundas opacas.

### 5. Normales y refracción
- Se calcula un normal map a partir del canal R de simulación.
- Se distorsiona la screen texture con las normales.
- Genera refracción realista de objetos sumergidos.

### 6. Integración
- Todo se combina en un único shader visual para la malla del agua.
- El script de flotabilidad usa el mismo `get_height()` que el shader.
- Las olas interactúan con objetos y paredes mediante la cámara de colisión.

## Aplicación futura en NaveGo
- Base para el agua realista del simulador limpio.
- Posible gemelo digital con interacción física y visual coherente.
- Referencia para implementar el shader de agua avanzado sin romper el rendimiento.
