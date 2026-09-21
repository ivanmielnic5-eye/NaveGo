# AGENTS.md — Instrucciones para agentes IA

## Contexto del proyecto
Proyecto: NaveGoLocal (app de navegacion offline-first, React Native + Expo).
Rama activa: experimento-dsh-01.
Modo de trabajo: desarrollo asistido humano-IA. El humano decide QUE, la IA decide COMO.

## Reglas del proyecto (leer HUMAN_AI_WORKFLOW.md para el detalle)
1. EVIDENCIA ANTES QUE CERTEZA.
2. UNA INTERVENCION POR VEZ.
3. RIESGO ANTES QUE VELOCIDAD.
4. NO VERIFICADO NO ES ERROR.
5. EL HUMANO DECIDE, LA IA EJECUTA.
6. CONVENCION DE COMANDOS EN CHAT: los bloques con boton "copiar" son para pegar en terminal; los fragmentos sin boton son solo para leer.

## PROTOCOLO DE INICIO DE HILO (obligatorio al arrancar)
Antes de cualquier accion, leer en este orden:
1. ESTADO.md        -> estado actual del proyecto.
2. SESIONES.md      -> historial de sesiones y trabajo pendiente.
3. SYNC_BRIEF.md    -> brief corto de la ultima sesion (si esta actualizado).
4. docs/modelos-evaluados.md -> modelos IA ya evaluados (para no re-evaluar).

## Nota sobre Expo
Expo ha cambiado. Leer docs versionadas en https://docs.expo.dev/versions/v57.0.0/ antes de escribir codigo.
