# PLAN DE MIGRACION A BACKGROUND LOCATION

**Fecha:** 2026-09-26
**Estado:** APROBADO — pendiente de ejecucion
**Expediente relacionado:** 44_HITO_GRABACION_PERSISTENTE
**Hipotesis:** H-2026-0021, H-2026-0022

---

## Objetivo

Que la captura de ubicacion siga funcionando cuando:
1. La app pasa a segundo plano.
2. La pantalla se apaga.
3. El celular esta bloqueado.
4. El usuario cambia de pantalla dentro de la app.

NO cubre: reinicio del celular (limitacion de Android).
Durante el reinicio, la sesion sigue viva pero no hay captura.
Ese hueco se registra como DEVICE_RESTART, no como GNSS_LOSS.

---

## Arquitectura objetivo

La Task captura. SQLite conserva. El procesador interpreta.
React muestra.

Un solo productor por modo. Nunca Task + watchPosition a la vez.

---

## Fases

### FASE 0 — Separar dominio de efectos

Objetivo: extraer la logica del callback actual a una funcion
que recibe un fix crudo y devuelve un resultado determinista,
sin tocar SQLite ni React.

NO es "hacer pura la funcion". Los efectos siguen existiendo.
Se separan:
- processFix() — dominio, deterministico.
- persist result — efectos, afuera.

Verificacion: mismo replay -> mismos fixes, gaps, distancia
y estado. Comparar contra una corrida grabada antes.

Riesgo: medio. Esfuerzo: 2-3 horas.

### FASE 1 — Infraestructura

Instalar expo-task-manager. Configurar el plugin de expo-location
con background habilitado. Agregar permisos al manifest:
ACCESS_BACKGROUND_LOCATION, FOREGROUND_SERVICE,
FOREGROUND_SERVICE_LOCATION.

Verificacion: build nativo compila, app sigue funcionando.

Riesgo: bajo. Esfuerzo: 30 minutos.

### FASE 2 — Task aislada

Crear tasks/backgroundLocationTask.ts. La Task recibe ubicaciones
en background pero NO toca SQLite. Escribe a un JSONL de prueba.

Mantener watchPositionAsync activo. La Task es observadora.

Verificacion: abrir app, apagar pantalla 60s, encender 60s, cerrar.
El JSONL debe tener fixes de los 3 periodos.

Riesgo: bajo. Esfuerzo: 30-45 minutos.

### FASE 2.5 — Gate de exclusividad

Demostrar que un fix entra EXACTAMENTE UNA VEZ al pipeline.

Prueba: en 2 minutos, contar fixes de la Task vs watchPosition.
Criterio: total = max(Task, watchPosition). No suma.

Si suma -> duplicados. Parar y arreglar.

Riesgo: bajo. Esfuerzo: 15 minutos.

### FASE 3 — Task = productor real

Activar startLocationUpdatesAsync cuando no sea replay.
Desactivar watchPositionAsync cuando no sea replay.

Replay sigue con watchPosition (no se migra).

Verificacion: sesion completa con pantalla apagada. Todos los
fixes llegan. Ninguno duplicado.

Riesgo: alto. Esfuerzo: 2-3 horas.

### FASE 4 — React = consumidor

El hook deja de ser dueno del estado. Lee last_fix, session y
gap_events de SQLite. El mecanismo de notificacion React <->
SQLite se define en esta fase.

Verificacion: HUD, mapa y gaps reflejan el estado real.

Riesgo: alto. Esfuerzo: 2-3 horas.

### FASE 5 — Finalizar correctamente

1. Marcar sesion CLOSED en SQLite (commit exclusivo).
2. stopLocationUpdatesAsync().
3. La Task verifica que la sesion siga ACTIVE antes de guardar
   cada fix. Un fix tardio no reabre una sesion finalizada.

Riesgo: medio. Esfuerzo: 1 hora.

### FASE 6 — Recuperacion de sesion ACTIVE

Al arrancar: buscar sesion ACTIVE. Si hay, registrar la Task
automaticamente. Si no, flujo normal.

Limitacion: tras un reboot, Android no re-arranca la Task.
El usuario tiene que abrir la app. Ahi se retoma.

Riesgo: medio. Esfuerzo: 2 horas.

---

## Criterios de exito globales

Al final:
1. Captura con pantalla apagada sin interrupcion.
2. Captura en segundo plano sin interrupcion.
3. Sin duplicados (Fase 2.5 lo garantiza).
4. Sesion retomada al reabrir la app.
5. Cierre limpio al apretar Finalizar.
6. Replay sigue funcionando como hoy.
7. Track honesto intacto.
8. Distancia y gaps intactos.

---

## Estimacion total

10-15 horas de trabajo. Orden de magnitud, no compromiso.
La parte dificil no es codigo: es DEMOSTRAR que funciona bajo
todas las condiciones.

---

## Que NO se toca en esta migracion

Distancia, logica de gaps, LIDR, track honesto visual, HUD,
mapas, gobernanza.

La migracion cambia DONDE se ejecuta la captura, no QUE
significa un fix.

---

## Referencias

- EXPEDIENTE/44_HITO_GRABACION_PERSISTENTE.md
- H-2026-0021, H-2026-0022
- GPT-4 (analisis completo, 2026-09-26)
- Hilo paralelo (correcciones al plan de GPT)

---

*Generado: 2026-09-26*
*Por: DeepSeek (chat) bajo direccion del Director*
