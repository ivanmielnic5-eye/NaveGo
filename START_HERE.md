# NAVEGO — START HERE

## Antes de actuar

Ejecutar en la terminal:

    cd ~/navego_recuperado
    ./.logos/bin/logos-gate NAVEGO

Si devuelve BLOCKED -> NO actuar. Consultar al Director.
Si devuelve WARNING -> solo lectura. Escritura requiere autorizacion.
Si devuelve READY -> el sistema esta en condiciones de trabajar.

Para arrancar un agente con contexto completo:

    ./.logos/bin/logos-dsh NAVEGO "tarea a ejecutar"

El wrapper hace: Gate -> Capsula -> DSH.

---

## Fuentes de verdad

Este proyecto usa el sistema LOGOS Context Kernel.
Las fuentes autoritativas estan declaradas en:

    .logos/MANIFEST.json

Regla critica:

> Ningun documento es autoridad si no esta declarado en el MANIFEST.

---

## Protocolo de inicio de hilo (para IA)

Al abrir un hilo nuevo con cualquier IA:

1. Pegar el contenido de capsula-de-memoria.md (si existe).
   Si no existe, generarla con:
       ./.logos/bin/logos-mem NAVEGO
2. NO asumir contexto que no este en la capsula.
3. Declarar incertidumbre en lugar de inventar.
4. Respetar las reglas criticas de la capsula.

---

## Reglas criticas

- No modificar main.
- No modificar tests para ocultar fallos.
- No instalar dependencias sin autorizacion.
- Ante conflicto entre spec/test/codigo: STOP.
- Ante incertidumbre arquitectonica: STOP.
- No afirmar exito sin evidencia.
- Contexto incierto = STOP.

---

## Documentacion completa

- Decisiones:      EXPEDIENTE/01_DECISIONES.md
- Arquitectura:    EXPEDIENTE/02_ARQUITECTURA.md
- Workflow:        EXPEDIENTE/03_WORKFLOW.md
- Multi-IA:        EXPEDIENTE/09_PROTOCOLO_MULTI_IA.md
- Incidentes:      EXPEDIENTE/10_INCIDENTES.md
- Capsula Memoria: EXPEDIENTE/17_DECISION_CAPSULA_MEMORIA.md
- Ciclo Sesiones:  EXPEDIENTE/18_ESPEC_CICLO_SESIONES.md
- MANIFEST v3:     EXPEDIENTE/19_DECISION_MANIFEST_V3_CAPSULA.md
- Estados Gate:    EXPEDIENTE/20_ESPEC_GATE_ESTADOS.md
- logos-mem:       EXPEDIENTE/21_ESPEC_LOGOS_MEM.md
- logos-gate:      EXPEDIENTE/22_ESPEC_LOGOS_GATE.md
- logos-dsh:       EXPEDIENTE/23_ESPEC_LOGOS_DSH.md

---

## Autoridad

Director Funcional: Ivan.
La IA propone. GPT-4 critica. Ivan decide.

Frase del sistema:

> "La Capsula de Memoria no recuerda por nosotros; transporta el
> estado verificable del sistema hasta el proximo contexto."
