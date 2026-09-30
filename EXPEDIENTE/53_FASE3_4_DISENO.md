# DOC 46 FASES 3+4 — DISENO DE ARQUITECTURA

**Fecha:** 2026-09-30
**Estado:** DISENO APROBADO. Pendiente de implementacion.
**Rama:** experimento-v4-admin
**Analisis:** GPT-4 con contexto completo (2026-09-30)

---

## Contexto

Fases 0, 1, 2 y 2.5 completas. Fases 3 y 4 estan acopladas:
la Task no ve los refs de React, hay que mover el estado a SQLite.

---

## Decision P1 — Frontera de la Task

**La Task es productor operacional COMPLETO, no solo volcador.**

- Recibe batch de ubicaciones del OS.
- Persiste cada fix crudo en SQLite.
- Ejecuta processFix() con estado PERSISTENTE (leido de SQLite).
- Persiste resultados derivados (distancia, gaps, estado).

React pasa a ser solo consumidor.

**Razon:** si la Task solo escribe crudos, durante background no
hay procesamiento de gaps/distancia/estado.

---

## Decision P2 — Watchdog de gaps

**No usar setInterval en la Task.** Una Task de ubicacion no
garantiza que JS corra cada 2s si no llegan ubicaciones.

**El gap se detecta por timestamps:** cuando llega el proximo fix,
processFix ve que transcurrio >2s y materializa el gap.

En foreground, el hook puede proyectar "gap activo" con la
antiguedad del ultimo fix de SQLite.

**Regla:** receivedAt y measuredAt siguen separados. El watchdog
usa RECEPCION, no adquisicion GNSS.

---

## Decision P3 — React <-> SQLite

**Polling cada 1-2s como base.** Simple, robusto, predecible.

`addDatabaseChangeListener` queda como optimizacion POSTERIOR,
solo despues de probar. Task y UI pueden usar conexiones
distintas; no asumir que el listener sincroniza ambos runtimes.


---

## Decision P4 — Orden de migracion

1. Congelar replay actual (evidencia BASE).
2. Crear/persistir estado operacional en SQLite:
   - last_fix, last_cog, gap, cursor de sesion.
3. Adaptar processFix():
   - recibe estado persistente, no refs.
   - sigue siendo puro y determinista.
4. Task experimental escribe a tablas de prueba.
   - watchPosition sigue siendo produccion.
   - NO mezclar streams.
5. Comparar Task vs watchPosition:
   - cantidad, timestamps, orden, contenido.
   - 0 duplicados inesperados.
6. Task pasa a produccion:
   - raw + processFix + derivados.
   - unica fuente GPS.
7. Apagar watchPosition en modo REAL.
8. Hook pasa a consumidor de SQLite (polling primero).
9. Probar:
   - background, pantalla apagada, cambio de pantalla,
     Finalizar, reabrir app, reinicio.

**Regla critica:** nunca dejar Task y watchPosition procesando
el mismo stream de produccion. El SO les entrega lo mismo.

---

## Decision adicional — Batches

**La Task debe procesar batches, no fixes individuales.**

`startLocationUpdatesAsync` entrega `data.locations` como array.
processFix se ejecuta secuencialmente:

  batch -> P1 -> state1
        -> P2 -> state2
        -> P3 -> state3

**Todo el batch se persiste transaccionalmente** cuando sea
apropiado. Un batch es una unidad coherente de procesamiento.

---

## Arquitectura congelada

Task recibe batch del OS:
- Escribe raw_fix a SQLite.
- Ejecuta processFix() con estado persistente.
- Persiste gaps y tracker state.
- React lee de SQLite (polling 1-2s).
- HUD se actualiza.

**Frontera:** la Task observa y registra. SQLite conserva.
processFix interpreta. React representa.

Esto preserva la regla "Estimacion != evidencia": la Task
persiste la observacion y deriva el estado por separado.

---

## Lo que NO se toca

- processFix() sigue puro y determinista.
- Track honesto visual (amarillo/negro) intacto.
- Distancia y gaps con misma semantica.
- Replay sigue con watchPosition.
- HUD y mapas sin cambios de diseno.

**La migracion cambia DONDE se ejecuta la captura, no QUE
significa un fix.**

---

## Proximos pasos de implementacion

1. Congelar replay (corrida BASE con la version actual).
2. Crear tablas de estado persistente en SQLite.
3. Adaptar processFix para leer estado de SQLite.
4. Task experimental (tablas de prueba, watchPosition activo).
5. Comparar Task vs watchPosition (0 duplicados).
6. Task a produccion, apagar watchPosition en real.
7. Hook a consumidor (polling).
8. Probar: background, pantalla apagada, Finalizar, reabrir,
   reinicio.

---

*Generado: 2026-09-30*
*Por: agente (chat) bajo direccion del Director Ivan Mielniczuk*
