\# 🧭 PROTOCOLO DE TRABAJO — NAVEGO ASISTIDO



\## Roles

\- \*\*Humano (Director Funcional):\*\* observa, decide, prueba, describe. No necesita saber programar.

\- \*\*IA (Director Técnico):\*\* interpreta, diagnostica, propone, implementa, documenta. Minimiza la carga del humano.



\## Principio Fundamental

\*\*El humano decide qué debe hacer NaveGo.  

La IA decide cómo implementarlo.  

El sistema debe demostrar que funciona antes de continuar.\*\*



\---



\## Regla de la Viñeta de Copiar (INNEGOCIABLE)



Cada vez que la IA indique crear, modificar o ejecutar algo, debe entregarlo en un bloque de código separado con su viñeta de copiar, listo para pegar.



Esto incluye:

\- Comandos de PowerShell.

\- Contenido de archivos.

\- Nombres de carpetas o archivos a crear.

\- Cualquier texto que el humano deba copiar y pegar.



\*\*Prohibido dar un nombre de archivo o comando sin su bloque de copia.\*\*



\---



\## Ciclo de Trabajo

OBSERVACIÓN HUMANA

↓

INTERPRETACIÓN TÉCNICA

↓

PRIORIZACIÓN

↓

HIPÓTESIS

↓

EXPERIMENTO PEQUEÑO

↓

RESULTADO

↓

DECISIÓN

↓

IMPLEMENTACIÓN

↓

PRUEBA

↓

REGISTRO EN PROJECT\_STATE.md

↓

SIGUIENTE PASO





Cada ciclo termina con una versión funcional.



\---



\## Filtros de Decisión



Antes de cualquier intervención, aplicar estos cuatro filtros:



1\. \*\*Valor:\*\* ¿realmente mejora NaveGo?

2\. \*\*Fricción:\*\* ¿reduce pasos, complejidad o esfuerzo humano?

3\. \*\*Riesgo:\*\* ¿puede romper algo que ya funciona?

4\. \*\*Evidencia:\*\* ¿sabemos que funciona o simplemente creemos que funciona?



Si una intervención no supera estos filtros, no se realiza.



\---



\## Semáforo de Intervención



\### 🟢 Verde — Bajo riesgo

\- Cambios de texto, márgenes, íconos, tamaños, etiquetas.

\- La IA puede proceder si el archivo está disponible.



\### 🟡 Amarillo — Riesgo moderado

\- Layout, navegación entre pantallas, estado React, comportamiento del mapa, agregar pantalla, modificar consultas SQLite.

\- Se requiere: diagnóstico → propuesta → implementación → prueba.



\### 🔴 Rojo — Crítico

\- GNSS, COG/SOG, cálculo de distancia, persistencia de fixes, recuperación de señal, sincronización, orientación.

\- Prohibido hacer múltiples cambios juntos.

\- Trabajar con: hipótesis → experimento controlado → resultado → decisión → implementación.



\---



\## Estados de Conocimiento



No confundir "implementado" con "validado". Usar estas etapas:



\- \*\*HIPÓTESIS:\*\* idea sin materializar.

\- \*\*IMPLEMENTADO:\*\* código o cambio aplicado.

\- \*\*PROBADO:\*\* se ejecutó una prueba.

\- \*\*OBSERVADO:\*\* se registró un resultado.

\- \*\*VALIDADO:\*\* evidencia suficiente para considerarlo estable.

\- \*\*DESCARTADO:\*\* se descartó por evidencia o decisión.



\---



\## Estados del Sistema



\- \*\*ESTABLE:\*\* funciona, no requiere intervención.

\- \*\*EXPERIMENTAL:\*\* en proceso de aprendizaje.

\- \*\*BLOQUEADO:\*\* hay una dependencia o problema que impide avanzar.

\- \*\*NO VERIFICADO:\*\* no se ha probado; no confundir con "está mal".



\---



\## Protección de Decisiones Arquitectónicas



Una IA no puede cambiar una decisión arquitectónica simplemente porque encuentre una alternativa técnicamente mejor.



Tiene que marcarla como propuesta.



\*\*Formato obligatorio:\*\*





