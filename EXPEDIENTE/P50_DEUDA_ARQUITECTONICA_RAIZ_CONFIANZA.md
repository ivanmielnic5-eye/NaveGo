# P50 — DEUDA ARQUITECTÓNICA: MANTENIMIENTO DE LA RAÍZ DE CONFIANZA Y MANIFEST

**Fecha:** 2026-10-24
**Estado:** HALLAZGO REGISTRADO. REQUIERE DECISIÓN DE DISEÑO.
**Contexto:** Durante la resolución del bloqueo del Gate por la actualización de `EXPEDIENTE/PENDIENTES.md`, se detectó que el flujo actual exige una intervención humana manual excesiva (reconciliar, commitear, re-sellar la raíz).

## El Problema
La raíz de confianza (Root of Trust) está diseñada para detectar cambios no autorizados en el `MANIFEST`. Sin embargo, cada vez que se actualiza el hash de una fuente legítima (por ejemplo, al agregar un pendiente), el `MANIFEST` cambia, lo que invalida la raíz de confianza y obliga a un re-sellado. 
Si se automatiza el re-sellado, la raíz pierde su propósito de seguridad (se convierte en un trámite rutinario). Si no se automatiza, el Director debe hacer de "Sherlock Holmes" manualmente por cada cambio.

## Propuesta de Solución (A auditar)
1. **Separar tipos de cambio:** No es lo mismo un cambio de contenido (ej. P49) que un cambio de metadatos de revisión o un cambio de política de confianza.
2. **Diagnóstico Automático:** Crear un comando que detecte qué cambió, en qué commit, y qué acción exacta se requiere, sin modificar nada.
3. **Re-sellado Condicionado:** La raíz de confianza solo debería re-sellarse cuando cambia el *núcleo* de la política, no cuando se actualiza el hash de un documento de trabajo.
4. **Regla de Oro:** La IA puede automatizar la investigación y la preparación del fix, pero la autorización final (el re-sellado) debe seguir siendo un acto humano explícito.

## Decisión Requerida
Evaluar si el diseño actual del `logos-gate` y `logos-reconcile` es escalable a medida que el proyecto crece, o si requiere un rediseño para separar la integridad del manifiesto de la aprobación de la raíz de confianza.
