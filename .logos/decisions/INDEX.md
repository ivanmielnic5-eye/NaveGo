# INDICE DE DECISIONES CONGELADAS

Ultima actualizacion: 2026-10-08

---

## TRACKING GNSS

- D-2026-0001 - Estimacion != evidencia observada (CONGELADA)
- D-2026-0002 - Gap como entidad persistente (CONGELADA)
- D-2026-0003 - Track observado != track estimado (CONGELADA)

## PERSISTENCIA SQLITE

- D-2026-0004 - Migraciones SQLite versionadas y exclusivas (CONGELADA)
- D-2026-0005 - Verificacion post-migracion (CONGELADA)
- D-2026-0006 - Version efectiva de expo-sqlite: 16.0.10 (CONGELADA)
- D-2026-0007 - Un solo escritor por worktree (CONGELADA)
- D-2026-0008 - Objetivo de salida de la investigacion GNSS (CONGELADA)

## KERNEL LOGOS / GATE

- D-2026-0009 - Semantica de reviewed_against_commit y estados del Gate (CONGELADA)
- D-2026-0010 - Freshness de fuentes por hash de contenido (CONGELADA)

---

## ESTADOS

- CONGELADA: no se discute mas, requiere decision explicita nueva para cambiar
- REVISABLE: podria cambiar segun nueva evidencia
- REVISADA: cambio al menos una vez
- DESCARTADA: ya no aplica

---

## NOTA DE INTEGRACION

Estas decisiones todavia NO estan declaradas en el MANIFEST del proyecto.
Pendiente para proxima sesion:
1. Agregar tipo 'decision_records' al MANIFEST como collection.
2. Correr validate-manifest.
3. Actualizar logos-dsh y logos-mem para leer el nuevo tipo.
