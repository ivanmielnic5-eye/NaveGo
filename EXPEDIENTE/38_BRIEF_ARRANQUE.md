# BRIEF DE ARRANQUE — NAVEGO

**Uso:** Pegar al inicio de cualquier chat nuevo (con IA web o con IA local).

---

## VERSION PARA IA WEB (GPT, Claude, Gemini, DeepSeek web)

Copiar y pegar:

CONTEXTO PARA IA WEB — PROYECTO NAVEGO

Soy el Director del proyecto NaveGo. Trabajo con agentes locales
(DSH) y con vos. No tenes acceso a mi computadora, asi que te voy
a pasar el contexto cuando haga falta.

Lo que necesito que sepas de entrada:

- NaveGo es una app Android de navegacion fluvial
  (React Native + Expo 54 + MapLibre GL Native).
- Dispositivo objetivo: TCL T610P (gama media).
- Es offline-first: mapas MBTiles, sin backend, todo local.
- Subsistemas: NaveGo (app), Simulador Godot, LOGOS (gobernanza),
  Cockpit (HUD).

Estado actual (2026-09-25):
- 20 hipotesis en ~/.logos/hypotheses/
- 8 decisiones congeladas en ~/navego_recuperado/.logos/decisions/
- Investigaciones activas: GNSS (cortes), distancia (A vs B vs
  A+Kalman), track honesto (mostrar gaps).

Como trabajo:
- DSH (agente local) investiga y ejecuta.
- Vos validas, cuestionas, contrastas.
- Las decisiones las tomo yo.

Reglas minimas:
- No inventes datos. Si algo no lo sabes, decilo.
- Cuando dudes, pregunta antes de avanzar.
- Espanol simple, no tecnico.
- Si algo no cuadra, decilo sin diplomacia.

Cuando empiece una tarea concreta te paso los archivos relevantes.

---

## VERSION PARA IA CON ACCESO AL FILESYSTEM

Leer en orden:
1. ~/navego_recuperado/capsula-de-memoria.md
2. ~/.logos/hypotheses/INDEX.md
3. ~/navego_recuperado/.logos/decisions/INDEX.md
4. ~/navego_recuperado/EXPEDIENTE/ (ultimos 5)

Contexto: soy el Director de NaveGo. Cada chat arranca en cero.
Reglas: no tocar codigo sin backup, no tocar GNSS ni persistencia
sin autorizacion, preguntar antes de avanzar, espanol simple.

Contame en 20 lineas que ves y que esta desactualizado.

---

## ARCHIVOS CLAVE DEL PROYECTO

- Capsula: ~/navego_recuperado/capsula-de-memoria.md
- Hipotesis: ~/.logos/hypotheses/
- Decisiones: ~/navego_recuperado/.logos/decisions/
- Expediente: ~/navego_recuperado/EXPEDIENTE/
- Gobernanza: ~/navego_recuperado/AGENTS.md y .logos/MANIFEST.json

---

*Generado: 2026-09-25*
*Por: DeepSeek (chat) bajo direccion del Director*
