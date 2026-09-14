# 07 — GLOSARIO CANÓNICO

Fecha: 2026-09-14
Propósito: Eliminar ambigüedades de nombres. Un solo término por cosa.

## Regla

Cada concepto tiene UN nombre canónico.
Los nombres antiguos quedan como "alias" solo para búsqueda en código legacy.

## Nombres canónicos

### Cockpits (tres cosas distintas)

- **Cockpit Móvil**
  Pantalla React Native del celular con 5 módulos universales.
  Archivo: CockpitScreen.tsx
  Contenido: Estado, Trabajo, Evidencia, Archivos, Acción + 4 luces.
  NO usar: "HUD", "Panel móvil", "Dashboard".

- **Cockpit Web**
  Dashboard HTML con monitoreo (navegador en PC).
  Archivo: dashboard/dashboard_command_center_v3.html
  Servidor: navego_dashboard_server.py
  NO usar: "Cockpit PC", "Dashboard", "Panel web".

- **Cockpit Sim**
  Panel de instrumentos dentro del simulador Godot.
  Archivo: Cockpit.gd
  NO usar: "HUD de Godot", "Panel de simulación".

- **Cockpit Kernel**
  Contratos y estados universales (conceptual, no UI).
  Archivos: COCKPIT_CORE_DATA_KERNEL.md, COCKPIT_DATA_CONTRACT.md,
            COCKPIT_CORE_SPEC.md
  NO usar: "Core" (ambiguo), "Kernel" solo (ambiguo).

### Instrumentos y pantallas

- **HUD**
  Instrumentos de navegación en tiempo real: SOG, COG, LAT, LON, FIX, UTC.
  NO usar: "Cockpit" (es otra cosa).

- **Port Trail**
  Pantalla principal con el mapa interactivo (se abre en landscape).
  NO usar: "Mapa", "Pantalla principal".

### Sistemas y meta-sistemas

- **NaveGo**
  App de navegación (móvil + backend R2-D2).
  NO usar: "NaveGo Local" (ese era el nombre del build anterior).

- **Logos**
  Meta-sistema. Constelación. Fábrica de apps.
  NO usar: "GAIA" (es Ojo de Gaia, otra cosa).

- **Ojo de Gaia**
  App de lectura oftalmológica (iris, cristalino).
  NO usar: "GAIA" solo.

- **NaveGo Core**
  Núcleo de navegación (una vez extraído).
  Aún no existe como código. Está en diseño.

- **Logos Core**
  Núcleo compartido de la constelación.
  Aún no existe. Es el destino de la extracción futura.

### Agentes y automatización

- **Agente de Escritorio**
  El sistema de automatización local (FSM + ydotool + Ollama).
  Alias en código: agent_fsm.py
  NO usar: "GAIA" (era el nombre de otra cosa).

- **Ollama**
  El runtime de modelos locales. No es una app, es infraestructura.

- **R2-D2**
  La Mini PC. Nodo cognitivo local.
  NO usar: "la PC", "el servidor" (ambiguo).

## Aliases (para búsqueda en código legacy)

Si encontrás estos términos en el código viejo, mapean así:

- "cockpit" en CockpitScreen.tsx → Cockpit Móvil
- "cockpit" en dashboard/*.html → Cockpit Web
- "cockpit" en Cockpit.gd → Cockpit Sim
- "cockpit" en COCKPIT_*.md → Cockpit Kernel
- "HUD" en la muleta → verificar si es HUD o Cockpit Móvil
- "Panel" en panel.html → verificar (probablemente dashboard antiguo)
- "NaveGoLocal" en package.json → es el slug técnico, no el nombre del producto

## Frase para recordar

"Si dos cosas comparten el mismo nombre, ninguna de las dos
existe todavía."

Nombrar bien es parte de construir bien.
