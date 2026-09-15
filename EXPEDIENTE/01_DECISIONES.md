
## DECISIÓN 2026-09-15 — LOGOS Context Kernel

Se implementa el LOGOS Context Kernel como capa local de contexto,
memoria y trazabilidad para los tres proyectos (LOGOS, NaveGo, Simulador).

Estructura:
- ~/.logos/context/context.json  — snapshot actual
- ~/.logos/core/protocol/protocols.json — reglas R-01 a R-20
- ~/.logos/events/events.jsonl — registro de eventos
- ~/.logos/projects/{LOGOS,NAVEGO,SIMULATOR}/profile.json — perfiles
- ~/.logos/bin/logos-context — script de tarjeta
- ~/.logos/bin/logos-open — script de apertura por modo

Niveles:
- 0: identidad mínima
- 1: tarjeta operacional (por defecto)
- 2: contexto técnico
- 3: expediente completo
- 4: evidencia cruda

Modos (con logos-open):
- trabajo (nivel 1) — uso diario
- observacion (nivel 2) — aprendizaje del uso
- aprendizaje (nivel 3) — decisiones y reglas
- navego / simulador / logos — proyecto específico

Comandos:
- logos-context (nivel 1)
- logos-context --full (nivel 3)
- logos-context --level=N
- logos-context --raw
- logos-open [modo]

Reglas R-16 a R-20 incorporadas:
- R-16: Contexto no es autoridad
- R-17: No autoescritura
- R-18: Source of truth
- R-19: Incertidumbre explícita
- R-20: Contexto inmutable por sesión

Frase oficial:
"LOGOS Context Kernel es una capa local de contexto, memoria y
trazabilidad que informa a humanos e IAs sobre el estado verificable
de un sistema sin convertirse en autoridad sobre sus decisiones."

Estado: IMPLEMENTADO Y VALIDADO.
Validación:
- 3+ aperturas de terminal registradas en events.jsonl.
- Bug de doble tarjeta resuelto.
- Bug de modo heredado resuelto con trap EXIT.
