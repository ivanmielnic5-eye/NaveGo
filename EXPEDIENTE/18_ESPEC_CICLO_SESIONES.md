# ESPECIFICACION — Ciclo de Sesiones

**Migrado de:** SESIONES.md (22 ago 2026)
**Fecha migracion:** 2026-09-22
**Estado:** VIGENTE (autoritativo para diseno de sesiones)
**Origen:** original conservado como HISTORICAL en SESIONES.md

---

## Objetivo
Definir el ciclo de vida correcto de una derrota para resolver
acumulacion, unicidad y mutacion de datos historicos.

## Estados de operacion
1. AMARRE: app abierta, tracking inactivo, sin acumular distancia.
2. INICIAR DERROTA: crea nueva sesion en SQLite, comienza a registrar.
3. TRACKING ACTIVO: acumula distancia y registra fixes GPS.
4. PAUSAR: detiene registro, no suma distancia, crea marcador.
5. REANUDAR: inicia segmento nuevo, mantiene sesion actual.
6. FINALIZAR: cierra sesion, guarda distancia final, vuelve a AMARRE.

## Regla de pausa (Opcion C) — DECISION VIGENTE
- Durante la pausa no se suma distancia.
- Al reanudar se inicia un segmento nuevo.
- El mapa debe mostrar una interrupcion visible, NO una linea
  recta falsa.
- Solo se registra lo navegado despues de soltar amarras.

Nota de migracion: esta regla se decidio en agosto 2026 y se perdio
entre hilos hasta septiembre 2026. Es parte de la evidencia del
incidente del 21 sep. NO VOLVER A PERDER.

## Reglas de persistencia
- Cada sesion cerrada es inmutable.
- Una sesion nueva debe tener id unico.
- La secuencia de GPS se reinicia solo al crear sesion nueva.
- No se puede crear mas de una referencia para la misma sesion.
- Si la referencia ya existe, el sistema debe avisar.

## Mapeo con codigo (a la fecha de migracion)
- startTracking: crea sesion y comienza a registrar.
- togglePause: pausa/reanuda registro.
- stopTracking: cierra sesion y guarda distancia.
- resetTracking: limpia contadores en memoria.
- createReferenceRouteFromSession: crea referencia desde sesion.

## Pendientes heredados (referencia, no autoridad)
Los siguientes puntos eran problemas abiertos en ago 2026.
Verificar contra estado actual antes de tratar como vigentes:
- App inicia tracking automaticamente al abrir.
- Boton FINALIZAR no llama a stopTracking.
- Boton RESETEAR no cierra sesion activa.
- Pausa no crea marcador de pausa.
- Referencias duplicadas por doble toque.
- Lista de sesiones se desborda en pantalla.

## Procedencia
- Fuente original: SESIONES.md (22 ago 2026).
- Migrado por: DeepSeek, sesion 2026-09-22.
- Pendiente declarar autoridad formal en MANIFEST.json.
