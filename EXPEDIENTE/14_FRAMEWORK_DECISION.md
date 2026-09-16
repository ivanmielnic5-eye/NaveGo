# 14 — Framework LOGOS de Decisión Arquitectónica

Fecha: 2026-09-16
Estado: VERSION AUDITADA (integra críticas de Claude).
Fuente de la auditoría: fase CRITIQUE del workflow multi-IA.

## Motivación

El Capitán señaló: "No deberíamos dejar decisiones de diseño
importantes libradas al sentido común. Debe haber un mejor criterio
evaluatorio."

Este framework es la respuesta.

## Principio rector

El framework NO produce "ganadores".
Describe un escenario de preferencias y evidencia.
La decisión final es HUMANA.

## Criterios núcleo (universales)

| Criterio | Definición operativa |
|----------|----------------------|
| Soberanía | Control del dato, sin dependencias externas, offline-first |
| Tolerancia a fallos | El sistema no se cae ante fallos |
| Degradación funcional | El sistema sigue prestando capacidades útiles al perder dependencias |
| Integridad + Proveniencia | Dato íntegro + rastreable a su fuente |
| Mantenibilidad | Complejidad, componentes, diagnóstico, modificación, recuperación |
| Testeabilidad | Cada componente puede probarse aisladamente (R-04) |
| Observabilidad | Se puede diagnosticar en operación real, no solo en lab |
| Recuperabilidad | Fallo → reinstalar → restaurar → reconstruir sin pieza única |
| Interoperabilidad | Convive con MapLibre, SQLite, Godot, LOGOS, Android, iOS |
| Reversibilidad | Se puede volver atrás sin destruir datos |
| Simplicidad operativa | Menos operaciones humanas = menos puntos de fallo |
| Costo de cambio futuro | Costo estimado de reemplazar si la hipótesis falla |

## Criterios contextuales (por dominio)

Cartografía:
- Escalabilidad regional
- Tamaño de dataset
- Rendimiento geográfico

Sensores:
- Precisión
- Frecuencia
- Sincronización temporal

UI:
- Latencia
- Accesibilidad
- Consumo energético

## Reglas de pesos

1. Cada peso debe tener justificación de una frase vinculada a
   una restricción explícita de NaveGo.
2. Los pesos se fijan ANTES de puntuar las alternativas.
3. Cambiar un peso después de ver los resultados está prohibido.
4. El cambio de pesos entre decisiones es válido, pero debe quedar
   registrado ANTES de la nueva evaluación.

## Criterios de veto (antes de puntuar)

Antes de aplicar la matriz, verificar restricciones no negociables:

- ¿Requiere servicios pagos? → INADMISIBLE
- ¿Requiere Google/Mapbox? → INADMISIBLE
- ¿Requiere conexión permanente? → INADMISIBLE
- ¿Impide operar offline? → INADMISIBLE
- ¿Depende de una pieza única irreemplazable? → INADMISIBLE

Si una opción viola un veto → no entra en la puntuación.
No es "peor". Es inadmisible.

## Opciones candidatas (mapas)

- A: MBTiles híbrido (con D1: dump/reload)
- B: Dos archivos sueltos (render.mbtiles + navigation.sqlite)
- C: Dos archivos + manifiesto (con hashes y region_id)
- D: Directorio por región con archivos separados por capa
- E: Servidor local de tiles
- F: BASELINE — solución más simple que satisface requisitos básicos

La opción F obliga a preguntar: ¿realmente necesitamos algo más complejo?

## Tabla epistemológica (separada)

Cada puntuación debe declarar:

| Campo | Valores |
|-------|---------|
| valor | 1-5 |
| evidencia | MEDIDA / ESTIMADA / OPINIÓN |
| confianza | ALTA / MEDIA / BAJA |
| fuente | referencia al experimento o documento |

Así una IA no puede esconder una estimación dentro de un número.

## Tabla evaluatoria (separada)

| opción | criterio | valor 1-5 | peso | subtotal |
|--------|----------|-----------|------|----------|

## Análisis de sensibilidad (obligatorio)

Después de puntuar:
- ¿El orden cambia si uno o dos pesos plausibles se modifican ligeramente?
- Si cambia mucho: resultado SENSIBLE.
- Si permanece estable: resultado ROBUSTO.

## Informe de disenso (obligatorio)

Después de construir la matriz:
1. ¿Cuál es el argumento más fuerte CONTRA la alternativa aparentemente preferida?
2. ¿Qué evidencia podría demostrar que la evaluación está equivocada?

Obliga al sistema a buscar falsación.

## Salida del framework

NO produce "ganador". Produce uno de:

- ROBUSTA: el orden es estable ante cambios plausibles de pesos.
- SENSIBLE: el orden cambia si se modifican pesos.
- INDETERMINADA: falta evidencia para puntuar.

Siempre acompañada de:
- Evidencia fuerte de cada alternativa.
- Incertidumbres.
- Vulnerabilidades.
- Experimento pendiente (si falta evidencia).
- Decisión: HUMANA.

## Flujo

PROBLEMA
  → definir alternativas
  → definir criterios ANTES de examinar resultados
  → fijar pesos con justificación
  → aplicar vetos
  → evaluar evidencia
  → matriz 1-5
  → análisis de sensibilidad
  → informe de disenso
  → experimento mínimo
  → EVIDENCIA
  → actualización de matriz
  → HUMANO DECIDE

## Riesgos a prevenir

1. Manipular pesos.
2. Elegir criterios después de ver opciones.
3. Usar escalas ambiguas.
4. Confundir estimaciones con medidas.
5. Interpretar la suma como decisión.

Frase clave:
"La puntuación describe un escenario de preferencias y evidencia;
nunca constituye una decisión."
