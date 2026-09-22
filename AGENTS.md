# AGENTS.md — Instrucciones para agentes IA

## Contexto del proyecto

Proyecto: NaveGoLocal (app de navegacion offline-first, React Native + Expo).
Rama activa: experimento-dsh-01.
Modo de trabajo: desarrollo asistido humano-IA.
Directorio raiz: ~/navego_recuperado

Regla de autoridad:
- IA propone. GPT-4 critica. Ivan (Director Funcional) decide.
- Ninguna IA cierra una rama que ella misma propuso. (R-09)

---

## Reglas del proyecto

Del HUMAN_AI_WORKFLOW.md:
1. EVIDENCIA ANTES QUE CERTEZA.
2. UNA INTERVENCION POR VEZ.
3. RIESGO ANTES QUE VELOCIDAD.
4. NO VERIFICADO NO ES ERROR.
5. EL HUMANO DECIDE, LA IA EJECUTA.
6. CONVENCION DE COMANDOS EN CHAT: los bloques con boton "copiar"
   son para pegar en terminal; los fragmentos sin boton son solo
   para leer.

Reglas adicionales del sistema LOGOS:
7. NO MODIFICAR MAIN.
8. NO MODIFICAR TESTS PARA OCULTAR FALLOS.
9. NO INSTALAR DEPENDENCIAS SIN AUTORIZACION.
10. ANTE CONFLICTO ENTRE SPEC/TEST/CODIGO: STOP.
11. ANTE INCERTIDUMBRE ARQUITECTONICA: STOP.
12. NO AFIRMAR EXITO SIN EVIDENCIA.
13. CONTEXTO INCIERTO = STOP.

---

## PROTOCOLO DE INICIO DE HILO (obligatorio)

Al abrir un hilo nuevo, leer en este orden:

1. START_HERE.md          -> puerta de entrada al sistema.
2. .logos/MANIFEST.json   -> fuentes autoritativas declaradas.
3. EXPEDIENTE/01_DECISIONES.md -> decisiones arquitectonicas.
4. EXPEDIENTE/09_PROTOCOLO_MULTI_IA.md -> reglas de colaboracion.
5. capsula-de-memoria.md  -> capsula de contexto (si existe).

Si la capsula no existe, generarla con:
    ./.logos/bin/logos-mem NAVEGO

Regla critica: no asumir contexto que no este en las fuentes
declaradas en el MANIFEST.

---

## Flujo LOGOS (wrapper de arranque)

Para ejecutar una tarea con contexto completo:

    ./.logos/bin/logos-dsh NAVEGO "tarea a ejecutar"

El wrapper hace, en orden:
1. Gate (preflight): verifica estado del sistema.
2. Capsula: genera capsula-de-memoria.md.
3. DSH: arranca el agente con la capsula como contexto.
4. Reporte: status, context_revision, exit code, git status.

Para solo verificar el estado (sin ejecutar agente):

    ./.logos/bin/logos-gate NAVEGO

Resultado:
- READY: autorizado a trabajar.
- WARNING: solo lectura. Escritura requiere autorizacion humana.
- BLOCKED: STOP. No actuar. Consultar al Director.

---

## Archivos historicos (NO autoritativos)

Estos archivos fueron declarados HISTORICAL y NO deben usarse
como fuente de verdad:

- ESTADO.md       (migrado parcialmente, pendiente rescate).
- SESIONES.md     (migrado a EXPEDIENTE/18).
- SYNC_BRIEF.md   (pendiente rescate).

Si necesitas info de ellos, verificar primero si ya esta en las
fuentes autoritativas del MANIFEST.

---

## Nota sobre Expo

Expo ha cambiado. Leer docs versionadas en
https://docs.expo.dev/versions/v57.0.0/ antes de escribir codigo.

---

## Frase del sistema

"La Capsula de Memoria no recuerda por nosotros; transporta el
estado verificable del sistema hasta el proximo contexto."
