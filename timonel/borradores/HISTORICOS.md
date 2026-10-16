# Borradores históricos (pre-canónicos)

Estos archivos son versiones preliminares de decisiones hoy **congeladas** en el
registro canónico de LOGOS. Se preservan para trazabilidad del proceso decisorio,
**NO** como fuente autoritativa.

| Borrador | Decisión canónica | Ubicación autoritativa |
|---|---|---|
| `D-A.borrador.json` | D-2026-0012 | `.logos/decisions/D-2026-0012.json` |
| `D-B.borrador.json` | D-2026-0013 | `.logos/decisions/D-2026-0013.json` |
| `D-C.borrador.json` | D-2026-0014 | `.logos/decisions/D-2026-0014.json` |

## Regla de precedencia

Ante cualquier discrepancia entre el borrador y la versión canónica, **prevalece
siempre la canónica**. Los JSON de esta carpeta permanecen sin editar, tal como
estaban al momento de la congelación.

## Contenido

Los tres borradores tienen contenido textual idéntico a las decisiones canónicas,
salvo los campos de metadata:

- `id`: `D-A (numero a asignar)` / `D-B (a confirmar)` / `D-C` en lugar de `D-2026-00XX`.
- `estado`: `BORRADOR — NO EN REGISTRO CANONICO` en lugar de `CONGELADA`.

Verificado el 2026-10-16 por inspección cruzada borrador vs canónico: no se perdió
contenido en la síntesis.

## Origen

Estos archivos se redactaron el 2026-10-14 durante el hilo FOCO contrato_intent.
Fueron la base sobre la que el Director aprobó las decisiones canónicas. Se
preservan aquí porque su lugar original (`timonel/borradores/`) es un directorio
de trabajo activo, y mantenerlos sin marca de estatus podía inducir a error.
