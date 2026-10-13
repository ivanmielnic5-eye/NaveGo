<!-- ingesta: 2026-10-13 20:17 -->
No hay problema. La revisión más rigurosa sería esta:

## 1. Alcance: migrar por semántica, no por coincidencia numérica

No reemplazaría automáticamente todos los `15.0`. Primero clasificaría cada aparición según lo que representa: umbral de llegada, horizonte temporal, parámetro de diagnóstico, texto de prompt u otra cosa. Que coincidan numéricamente no significa que compartan semántica.

- Flujo activo: migrar cada consumidor que calcula etiquetas o aplica el criterio de llegada para que use el contrato común.
- Herramientas de generación y diagnóstico: migrarlas si producen etiquetas o resultados que alimentan el flujo vigente.
- Código histórico: preservar una ruta reproducible y explícita. No cambiar silenciosamente su significado para satisfacer el test guardian.

La clasificación de «activo» debe basarse en puntos de entrada, imports, llamadas y artefactos consumidos; no solamente en el nombre del archivo.

## 2. `T` variable: opción B

Una configuración resuelta por contexto en `evaluar_todas`. Es la que corresponde a un banco donde cada contexto puede tener `T=10, 15, 20 o 25`.

Cada contexto debe traer o referenciar su `T` original. No debe inferirse de la etiqueta resultante ni sustituirse silenciosamente por 15 si falta.

Para evitar costos innecesarios, se puede reutilizar una `MisionConfig` inmutable por hash. Entrenador, simulador y evaluación deben usar la misma configuración efectiva para cada contexto.

## 3. Migración: incremental y reversible

Orden recomendado:

1. Inventariar cada aparición del literal y su significado.
2. Confirmar que `etiquetar()` conserva los resultados históricos de referencia.
3. Migrar `acciones.py` y sus dos llamadores; verificar las fronteras de llegada.
4. Migrar `entrenador_v2.py` y resolver `T` por contexto.
5. Migrar `timonel_python.py` y `recetas_navegacion_v2.py`.
6. Migrar generadores, diagnósticos y prompts activos; documentar los históricos excluidos.
7. Añadir el test guardian y excepciones explícitas, justificadas y revisables.

No combinar esta migración con cambios en la física, el ranking o la definición de éxito.

## 4. Criterios de éxito

Los 2316 contextos idénticos prueban la equivalencia de `etiquetar()` en ese conjunto, no la equivalencia de todos sus consumidores.

También comprobaría:

- Mismo resultado del entrenador y mismas acciones seleccionadas con configuraciones equivalentes.
- Mismas decisiones de `timonel_python` para estados idénticos.
- Casos de frontera `T−ε`, `T` y `T+ε`, respetando exactamente `<` o `<=`.
- Contextos con diferentes valores de `T`, incluyendo orden de evaluación alterado.
- Hash y procedencia de la configuración registrados en los resultados.

Si aparece una diferencia intencional, documentarla como cambio funcional por separado.

## 5. Búsquedas adicionales y una distinción importante

Además del grep, buscaría variantes (`15`, `15.00`), argumentos por defecto, constantes renombradas, expresiones derivadas, comparaciones duplicadas, plantillas, prompts y artefactos generados previamente.

Distinción arquitectónica: `etiquetar()` debe ser la autoridad para producir etiquetas. Pero si también se usa para decidir en tiempo de ejecución si `terminar` es válido, hay que verificar que su contrato realmente sirve para esa función. No conviene acoplar una función de etiquetado offline al controlador solo porque comparten un criterio; sí deben compartir la misma definición formal y configuración de misión.

Bloqueante real antes de migrar: comprobar que cada contexto conserva su `T` de origen y que cada literal se ha clasificado semánticamente. Sin esas dos garantías, una migración mecánica podría producir resultados aparentemente consistentes pero incorrectos.
