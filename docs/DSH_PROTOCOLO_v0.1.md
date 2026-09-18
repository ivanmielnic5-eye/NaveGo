# DSH — Protocolo de Autonomía v0.1

**Fecha:** 18 sep 2026
**Estado:** 6/15 ensayos verificados

## Ensayos completados

| # | Ensayo | Capacidad | Estado |
|---|---|---|---|
| 01 | Lectura autónoma | leer repo | ✅ |
| 02 | Edición controlada | escribir archivo | ✅ |
| 03 | Ciclo completo | ejecutar→diagnosticar→editar | ✅ |
| 04 | Multiarchivo | coordinar dependencias | ✅ |
| 05 | Descubrimiento | navegar repo sin guía | ✅ |
| 06 | Verificación independiente | no modificar test | ✅ |

## Capacidades por nivel

### Nivel 1 — Demostrado
Leer, comprender, editar, ejecutar, verificar, reportar.

### Nivel 2 — Esperable (parcialmente demostrado)
Multiarchivo ✅, búsqueda en repo ✅, tests existentes ✅.

### Nivel 3 — Pendiente
Iteraciones largas, regresiones, ambigüedad, cambios amplios.

### Nivel 4 — Fuera de alcance
Operación autónoma sin límites, producción, credenciales.

## Reglas de oro

- Sandbox antes que proyecto real.
- Git como red de seguridad.
- Humano como director, no como copiador.
- Evidencia (diff, log, test) antes de cada commit.
- Sin auto-approve. Sin tocar main.

## Próximos ensayos sugeridos
07 — Error inducido + recuperación
08 — Control de alcance adversarial
09 — No regresión
10 — Ambigüedad controlada
