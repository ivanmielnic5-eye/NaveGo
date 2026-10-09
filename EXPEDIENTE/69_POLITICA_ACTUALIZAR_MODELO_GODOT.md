# POLITICA: ACTUALIZAR EL MODELO 3D EN GODOT DESDE BLENDER

Fecha: 2026-10-09
Aplica a: cualquier hilo que toque el modelo del velero Polaris

## Regla central

**Godot NUNCA importa `.blend`.**
El `.blend` es fuente de trabajo en Blender. Lo que viaja a Godot
es el `.glb` exportado a mano.

El auto-import de `.blend` en Godot esta **desactivado a proposito**
en `Proyecto -> Ajustes del Proyecto -> filesystem/import/blender/enabled`.
No reactivar.

## Por que

Godot intenta convertir el `.blend` a glTF internamente. Como las
texturas estan embebidas en el `.blend`, no las encuentra afuera y
falla con errores. Ademas deja basura (`.import`, carpeta `textures/`).

El `.glb` ya tiene todo embebido y se importa sin problemas.

## Procedimiento completo

### PASO 1 — En Blender: exportar el `.glb`

Cuando el modelo este listo:

1. `Archivo -> Exportar -> glTF 2.0 (.glb/.gltf)`.
2. Configurar:
   - Formato: `glTF Binario (.glb)`
   - Nombre: `sailboat_v2.glb` (o el numero que corresponda)
   - Ubicacion: `~/interfaz/`
   - Aplicar modificadores: tildado
   - Y-up: tildado
3. Exportar.

Se genera `~/interfaz/sailboat_v2.glb`.

### PASO 2 — Backup del `.glb` actual

    cd ~/interfaz
    cp sailboat.glb sailboat.glb.pre-v2

### PASO 3 — Reemplazar el `.glb` viejo

    cd ~/interfaz
    mv sailboat_v2.glb sailboat.glb

Godot detecta el cambio solo y reimporta.

### PASO 4 — Verificar en Godot

1. En Godot: mirar el viewport.
2. Play (F5): probar que se vea bien.
3. Si la escala quedo distinta por el export, ajustar en el nodo
   `Perimetro_Velero` el campo `Scale` del Inspector.

### PASO 5 — Si algo se rompe

    cd ~/interfaz
    cp sailboat.glb.pre-v2 sailboat.glb

Vuelve al modelo anterior.

## Reglas aprendidas

- **NO** intentar importar `.blend` en Godot.
- **NO** reactivar el auto-import de `.blend`.
- **SIEMPRE** backup del `.glb` antes de pisarlo.
- **SIEMPRE** verificar visualmente antes de commitear.
- **SIEMPRE** revertir si algo se ve mal.

## Por que este metodo es seguro

- El `.glb` viejo no se borra, se renombra.
- Godot no toca Blender (cero dependencia).
- El cambio es un solo archivo.
- Reversible con un comando.

## Como detectar que algo salio mal

Si al abrir Godot aparecen errores tipo:

    Can't find file 'res://assets/blender/textures/Image_N.png'
    glTF: Image index 'N' ... couldn't be imported

Es senal de que el auto-import de `.blend` esta activado. Hay que
volver a desactivarlo en Ajustes del Proyecto.

## Historial

- 2026-10-09: primera version. Motivada por auto-import fallido al
  agregar `sailboat_work.blend` al repo del simulador.
