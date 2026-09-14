# INCIDENTES

## INC-001 — Deriva por insistencia en BootNext/GRUB
(fecha: 2026-09-12)

## INC-002 — Bloqueo de capa de red WSL/ngrok
(fecha: 2026-09-13)

## INC-003 — Pérdida de partición Windows
(fecha: 2026-09-13)

## INC-004 — Sobrescritura de CockpitScreen original

Fecha del incidente: 2026-09-13
Detección: 2026-09-14
Impacto: Reemplazo del Cockpit original por versión reducida (muleta).

Estado anterior:
- CockpitScreen.tsx con 5 módulos + 4 luces de estado + adapter.
- Última versión completa: commit 2fe520d (2026-08-22).

Estado posterior:
- CockpitScreen.tsx reducido a HUD de telemetría (muleta).

Recuperación:
- Original extraído desde git.
- Guardado en ~/backups/cockpit_original/CockpitScreen_ORIGINAL_2026-08-22.tsx.
- Muleta guardada como CockpitScreen.tsx.muleta_2026-09-13.

Causa raíz:
- Reconstrucción del 13/09 sin revisar git log del archivo.
- Violación del anti-patrón #13: rehacer antes de inspeccionar.

Lección:
- Antes de reescribir cualquier archivo, revisar git log de ese archivo.
- El historial de git es la fuente de verdad, no el working tree.

## Nota sobre nombres

Los incidentes INC-001 a INC-004 estuvieron parcialmente causados por
ambigüedad de nombres ("cockpit" para tres cosas distintas).

Solución adoptada: ver 07_GLOSARIO.md.

Nombres canónicos:
- Cockpit Móvil (CockpitScreen.tsx)
- Cockpit Web (dashboard_command_center_v3.html)
- Cockpit Sim (Cockpit.gd)
- Cockpit Kernel (COCKPIT_CORE_*.md)

Regla: antes de hablar de "el cockpit", especificar cuál de los cuatro.

## Hito 2026-09-14 — Standalone + Autonomía validados

Compilado y probado:
- APK de producción (release) sin dependencia de Metro.
- App arranca sin PC, sin WiFi, sin Metro.

Autonomía verificada (modo avión):
- GNSS OK (±2 m precisión).
- SOG cambia con movimiento real del celular (0.0 → 2.0 nudos).
- COG cambia con la orientación (163° → 206°).
- Distancia acumula correctamente (0.445 km → 0.554 km).
- Chip "SIN INTERNET" visible, pero todo funciona.

R2-D2 confirmado como anexo:
- Chip "Sin conexión con PC" sin afectar la operación.
- El bridge está envuelto en try/catch con timeout 3s.
- La app no depende del bridge para operar.

El Cockpit Móvil original (restaurado hoy) funciona:
- 4 luces de estado (GNSS, PC, Sinc, Metro).
- 5 módulos (Estado, Trabajo, Evidencia, Archivos, Acción).

Pendientes anotados (no bloqueantes):
- Adapter stub con GNSS hardcodeado como NO_VERIFICADO.
- ReferenceDetailScreen usa MapView (crashea sin API key).
- Reset no cierra sesión en SQLite.
- No existe export/borrar de referencias.
