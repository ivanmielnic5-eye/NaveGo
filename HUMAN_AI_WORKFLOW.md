# 🧠 HUMAN AI WORKFLOW — Cockpit de Trabajo Humano-IA

## Principio fundamental
La IA maneja la complejidad. El humano conserva el control de la intención.

## Ciclo de trabajo
El flujo es: ESTADO, luego TRABAJO, luego EVIDENCIA, luego ARCHIVOS, luego ACCION, y vuelve a ESTADO.

## Reglas del método
1. EVIDENCIA ANTES QUE CERTEZA. No avanzar sobre supuestos cuando una prueba puede resolver la incertidumbre.
2. UNA INTERVENCIÓN POR VEZ. No mezclar múltiples cambios simultáneos cuando sea posible aislarlos.
3. RIESGO ANTES QUE VELOCIDAD. Antes de modificar algo, determinar el riesgo.
4. NO VERIFICADO NO ES ERROR. Es información pendiente.
5. EL HUMANO DECIDE, LA IA EJECUTA. La IA puede analizar, diagnosticar, proponer, escribir, implementar, documentar. Las decisiones importantes permanecen bajo control humano.

## Estados del sistema
- ESTABLE
- EXPERIMENTAL
- BLOQUEADO
- NO VERIFICADO

## Estados de conocimiento
- HIPOTESIS
- IMPLEMENTADO
- PROBADO
- OBSERVADO
- VALIDADO
- DESCARTADO

## Módulos universales

### 1. ESTADO
Pregunta: "¿Cómo está el sistema?"
Muestra: salud general, tarea activa, bloqueos, alertas, cambios recientes, próximos pasos.

### 2. TRABAJO
Pregunta: "¿En qué estamos trabajando ahora?"
Muestra: tarea actual, objetivo, riesgo, próximo paso recomendado.

### 3. EVIDENCIA
Pregunta: "¿Qué sabemos realmente?"
Muestra: implementado, probado, observado, validado, logs, capturas, resultados.

### 4. ARCHIVOS
Pregunta: "¿Dónde está el conocimiento del proyecto?"
Muestra: documentos vivos (PROJECT_STATE.md, DECISIONS.md, TEST_LOG.md, CHANGE_LOG.md, ARCHITECTURE.md, UX_PRINCIPLES.md, NAUTICAL_THEORY.md).

### 5. ACCION
Pregunta: "¿Qué hacemos?"
Muestra: campo de intención, ejecutar prueba, crear tarea, guardar evidencia, pedir análisis, solicitar código, confirmar intervención, comandos de voz posteriores.

## Jerarquía visual
- Nivel 1: Ahora, lo que necesita atención, ocupa la mayor superficie.
- Nivel 2: Contexto, información para comprender el problema, menos luminosa.
- Nivel 3: Archivo, todo lo demás, no compite por atención.

## Semáforo con explicación textual
Nunca mostrar solo color. Siempre acompañar con texto.
Ejemplo: BLOQUEADO, Pantalla no responde, CAUSA DESCONOCIDA, Próxima acción: obtener consola.

## Preparación para voz
La voz alimenta el campo de intención. No ejecuta directamente.
Flujo: Humano, luego IA interpreta, luego presenta propuesta, luego confirmación explícita, luego ejecuta.

## Objetivo general
Reducir carga cognitiva, memoria necesaria, escritura innecesaria, navegación entre herramientas, errores por olvidar contexto, intervenciones innecesarias, desgaste físico y mental.
Aumentar evidencia, trazabilidad, claridad, velocidad de decisión, seguridad, continuidad del proyecto, autonomía del humano.

## Alcance actual
NaveGo es el primer caso de uso.
La arquitectura conceptual puede convertirse en sistema general para dirigir distintos proyectos con IA.

## Implementación mínima viable (MVP)
1. Crear HUMAN_AI_WORKFLOW.md (este documento).
2. Actualizar PROJECT_STATE.md con el flujo del Cockpit.
3. Crear script estado.ps1 para ver el estado en terminal.
4. Adaptar CockpitScreen.tsx con los 5 módulos y contenido mínimo.
5. Probar en una sesión real de trabajo.
6. Registrar en TEST_LOG.md si el flujo ayudó o no.

## Segunda etapa
- Comandos de voz reales.
- Integración con múltiples IAs en paralelo.
- Panel web para PC.
- Automatización de propuestas de IA.
- Métricas de uso del Cockpit.
