# BRIDGE BLENDER-MCP — MANUAL OPERATIVO

Manual para cualquier hilo nuevo que necesite usar el puente entre el
chat de IA (DeepSeek, ChatGPT, Claude, Gemini) y Blender. Permite
ejecutar codigo Python en Blender desde el chat, sin abrir el editor
de codigo.

## Arquitectura (3 piezas)

    [Chat IA en el navegador]
            ↓ Extension MCP SuperAssistant (Firefox)
    [http://localhost:3000/sse]  ← bridge Node.js
            ↓ socket TCP
    [Blender puerto 9876]        ← addon BlenderMCP

El bridge corre en una terminal separada. Blender corre normal.
La extension vive en el navegador y conecta el chat con el bridge.

## Componentes instalados

| Componente | Donde | Que hace |
|---|---|---|
| Node.js | /usr/bin/node (v26.10.0) | Corre el bridge |
| Bridge | ~/Descargas/Nexus-Blender-Bridge/nexus-server.js | Puente HTTP<->TCP |
| Addon BlenderMCP | ~/.config/blender/5.2/scripts/addons/addon.py | Socket dentro de Blender |
| Extension SuperAssistant | Firefox (instalada) | Conecta chat<->bridge |

## Arranque (cada vez que quieras usar el puente)

### Paso 1 — Bridge (en una terminal)

    cd ~/Descargas/Nexus-Blender-Bridge
    node nexus-server.js

Debe decir:

    🚀 Nexus Blender Bridge is LIVE!
    📍 SSE Endpoint: http://localhost:3000/sse

Dejar la terminal abierta. El bridge debe estar corriendo siempre que
uses el puente.

Para dejarlo corriendo sin ocupar la terminal:

    nohup node nexus-server.js > /tmp/nexus-bridge.log 2>&1 &

### Paso 2 — Blender

    ~/Descargas/blender-5.2.2-linux-x64/blender-5.2.2-linux-x64/blender &

Cuando abra Blender:

1. Apretar `N` para abrir el panel lateral derecho.
2. Hacer clic en la pestana **BlenderMCP**.
3. Apretar el boton **"Connect to Claude"** (aunque diga Claude,
   sirve para cualquier IA).
4. El boton debe ponerse **azul** y decir **"Running on port 9876"**.

### Paso 3 — Extension en Firefox

1. Abrir el chat de IA (DeepSeek, ChatGPT, etc.) en Firefox.
2. La extension MCP SuperAssistant debe estar conectada a
   `http://localhost:3000/sse`.
3. Los botones **MCP / Auto insert / Auto Submit / Auto Execute**
   deben estar activados.

Con esas 3 piezas activas, los bloques `jsonl` que el chat genere se
ejecutan automaticamente en Blender.

## Como se usa

El chat (la IA) genera bloques de codigo en formato `jsonl` asi:

    ```jsonl
    {"type": "function_call_start", "name": "execute_python", "call_id": N}
    {"type": "description", "text": "que hace"}
    {"type": "parameter", "key": "code", "value": "codigo Python"}
    {"type": "function_call_end", "call_id": N}
cd ~/navego_recuperado

# 1. Backup del .blend antes de que lo guardes con Ctrl+S
cp ~/Descargas/sailboat_normalizado.blend ~/Descargas/sailboat_normalizado.pre-renombres.blend
echo "[OK] backup: sailboat_normalizado.pre-renombres.blend"

# 2. Crear el memo del estado del trabajo en Blender
cat > EXPEDIENTE/67_TRABAJO_BLENDER_ESTADO.md << 'MDEOF'
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

