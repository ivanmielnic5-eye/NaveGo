# TRABAJO BLENDER — ESTADO AL 2026-10-09

## Archivo de trabajo

    /home/ivan/Descargas/sailboat_normalizado.blend

Backup previo (antes de renombrar objetos):

    /home/ivan/Descargas/sailboat_normalizado.pre-renombres.blend

## Que hay en la escena

Tres objetos MESH separados, en castellano:

1. **Velero**       — casco + mastil + timon + jarcias. 2522 caras.
2. **Vela_Mayor**   — la vela grande, va detras del mastil. 2 caras
                      (frente y dorso, es un triangulo plano).
3. **Foque**        — la vela chica, va adelante del mastil. 8 caras
                      (triangulo con subdivision).

Escala: eslora 10 m, manga 3 m, alto total 14.45 m. Coincide con la
escala que usa Godot (`scale 0.00592` aplicado al mesh original).

## Que falta hacer

### 1. Botavara (barra horizontal en la base de la vela mayor)

La vela mayor necesita una botavara real, igual que cualquier velero.
Va del mastil a la escota (borde trasero bajo de la vela mayor).

Origen aproximado:
- Extremo en el mastil: (0.04, -0.31, 1.78)
- Extremo en la escota: (0.44, -4.26, 1.78)
- Largo: ~3.97 m
- Grosor recomendado: 8 cm de radio

El objeto se puede llamar `Botavara` y queda como objeto aparte.
No es hijo de la vela — ambos giran juntos.

### 2. Mover origen de Vela_Mayor al puno de amura

Actualmente el origen de Vela_Mayor esta en (0,0,0). Para que la vela
rote alrededor del mastil hay que moverlo al **puno de amura**:

    (0.04, -0.31, 2.24)   <- version world, revisar

Este punto es donde el gratil de la vela (borde delantero) se une
al mastil por abajo. Al rotar la vela sobre ese punto, gira como un
velero real, no sobre su centro.

### 3. Mover origen de Foque al puno de amura

Mismo caso. El foque gira sobre su amura (el punto de abajo-adelante).

### 4. Cloth Simulation en ambas velas

Despues de que la rotacion este verificada, aplicar:
- Modificador Cloth en Vela_Mayor y Foque.
- Vertex Group que fija el gratil (borde delantero) al mastil.
- Vertex Group que fija el pujamen (borde inferior) a la botavara
  (solo Vela_Mayor).
- Campo de viento (Wind force field) para que las velas se inflen.

IMPORTANTE: las velas actuales tienen muy pocos vertices (2 y 8 caras).
Antes de Cloth hay que **subdividirlas** (100-500 vertices) para que la
tela pueda deformarse.

### 5. Exportar a Godot

Cuando las velas rotan bien y el Cloth este aplicado:
- Exportar el `.blend` a `.glb` con las animaciones horneadas.
- Importar en Godot reemplazando el `sailboat.glb`.
- Ajustar el `scale` del mesh en `main.tscn` (pasa de 0.00592 a 1.0
  si exportamos en escala real).
- Re-verificar la orientacion (Y-up en Blender = Y-up en Godot).

## Estado actual del trabajo

- Separacion de vela mayor y foque: HECHA.
- Nombres en castellano: HECHO.
- Botavara: PENDIENTE.
- Origenes de rotacion: PENDIENTE.
- Cloth Simulation: PENDIENTE.
- Exportacion a Godot: PENDIENTE.

## Reglas aprendidas hoy

- **NO guardar automaticamente** desde scripts Python via MCP.
  El guardado lo hace el Director con Ctrl+S en Blender cuando se
  verifica que todo se ve bien.
- Backup del `.blend` antes de cada serie de cambios importantes.
- Un cambio por vez, con verificacion.
- Los scripts del bridge (jsonl) van en el CHAT, no en bash.
- Cuando algo se rompe, usar `File -> Revert` para volver al ultimo
  guardado sin perder el archivo.

