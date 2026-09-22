# Sandbox — Misión "Corredor Santa Fe → CABA"

**TASK_ID:** CORREDOR-SF-CABA-2026-09-22
**Fecha:** 2026-09-22
**Commit base:** e88d2d4
**Ejecutado por:** DSH (perfil headless, DeepSeek API)
**Orquestado por:** logos-dsh v1.1.0
**Autoridad final:** Iván (Director Funcional)

## PBF objetivo

- Path: ~/cockpit/argentina-latest.osm.pbf
- SHA256: 0a979a3da11d64ab871b177ca322e200fe9785c8741bbff8c09a985e689686e4
- Tamaño: 257.252.921 bytes
- **Estado: TRUNCADO.** Faltan 9.409 bytes. Contiene 49.912.000 nodos
  pero 0 ways y 0 relations. NO sirve para cartografía vial.

## PBF alternativo encontrado

- Path: ~/cockpit/backup_mapa/argentina-260901.osm.pbf
- SHA256: d43f9af1a293f822fb23da570d7cb44d022b1943e73c79fcd6b87b190b5c504f
- Tamaño: 428.645.479 bytes
- Estado: aparentemente íntegro. 59,3M nodos, 5,9M ways, 88.563 relations.
- Mismo snapshot que el objetivo (2026-09-01T20:20:50Z).
- **NO VERIFICADO**: no se confirmó que cubra toda la extensión necesaria
  para SF→CABA.

## Restricciones de la misión

- Solo lectura sobre el PBF.
- Escritura SOLO en este sandbox.
- No ejecutar osmium extract, tippecanoe, ni generación de MBTiles.
- No git commit.
- No modificar el sistema.

## Qué se ejecutó

- osmium fileinfo / fileinfo -e / cat
- stat, ls, du, sha256sum, grep, find
- 7 scripts Python propios de análisis (solo lectura)

## Qué NO se ejecutó

- osmium extract
- osmium tags-filter
- tippecanoe
- Generación de MBTiles
- Instalación de paquetes
- Modificación del PBF original
- Servicios, firewall, systemd
- git commit

## Verificado por el wrapper

- Hash y mtime del PBF objetivo: intactos.
- HEAD del repo: sigue en e88d2d4 (sin cambios en código del proyecto).
- Único cambio en el repo: sandbox_corredor/ (untracked en el momento de la misión).

## Artefactos producidos

- CORRIDOR_PROPOSAL.md — propuesta con análisis e hipótesis de trabajo.
- corridor_candidates.json — 3 candidatos con bbox.
- work_hypothesis.md — razonamiento expandido.
- commands.sh — comandos propuestos (NO ejecutados).
- size_estimates.csv — todos UNABLE_TO_ESTIMATE_RELIABLY.
- EVIDENCE.md — comandos ejecutados y hallazgos.
- 7 scripts de análisis (bbox_calc, diag, find_boundary, geo_analysis,
  probe_content, probe_corridor_nodes, probe_truncation).
- .pbf_sha256.txt — hash registrado durante la misión.

## Hallazgo principal

El PBF objetivo está TRUNCADO. Sin ways no hay rutas. Sin rutas no hay
corredor. DSH detectó el bloqueo, buscó evidencia alternativa, encontró
el backup local, y se detuvo sin inventar.

## Puntos que requieren decisión humana

1. ¿Usar backup argentina-260901.osm.pbf o redescargar?
2. Semiancho: 20 / 50 / 90 km.
3. Eje: RN9 vs RN11. Prioridad: tiempo vs previsibilidad.
4. Los 3 tamaños quedaron como UNABLE_TO_ESTIMATE_RELIABLY.
