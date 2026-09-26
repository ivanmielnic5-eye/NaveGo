# INFORME DE SESION — 2026-09-25

**Duracion:** ~4 horas (aprox. 22:00 a 02:45)
**Foco principal:** Replay GNSS, persistencia de gaps, hipotesis de conflicto
**Resultado:** Replay funcionando + 1 bug encontrado y arreglado + 11 hipotesis guardadas

---

## 1. LO QUE SE HIZO

### 1.1 Replay GNSS completo

Se construyo un sistema que permite a NaveGo leer un archivo con
posiciones grabadas (`docs/gnss/gnss_simulado.jsonl`) y servirlo como
si fuera GPS real. Permite probar la app sin salir al rio.

Archivos nuevos:
- `LocationProvider.ts` — contrato comun entre GPS real y replay
- `ReplayLocationProvider.ts` — lee el .jsonl y lo sirve como GPS
- `devConfig.ts` — flag REPLAY_ENABLED (solo activo con env var)

Archivos modificados:
- `useNaveGoTracker.ts` — 5 patches para usar el provider
- `metro.config.js` — acepta extension .jsonl
- `assets/gnss/gnss_simulado.jsonl` — copia del escenario

**Verificado:** los 5 tests pasaron (carga, 1Hz, gap de 13s, maquina
de estados, outlier rechazado).

### 1.2 Punto azul unificado con el track

El mapa dibujaba el punto azul con `<UserLocation>` nativo (GPS del
telefono) y el track con el tracker (provider). Bajo techo se veian
en lugares distintos.

**Fix:** se reemplazo `<UserLocation>` por `<Marker>` usando `userPos`
que ya venia del tracker.

Archivo: `components/MapaOffline.tsx` (2 cambios quirurgicos).

### 1.3 Migracion SQLite v2

Se agrego a la base:
- Columna `received_at_ms` a `gps_fixes`
- Columna `source` a `gps_fixes` (GNSS o REPLAY)
- Tabla nueva `gap_events` con 15 columnas

**Verificado:** los 4 logs de schema confirman que la migracion
corrio bien y todo quedo en su lugar.

### 1.4 Deteccion automatica de gaps

Se agrego al tracker la logica para:
- Abrir un gap cuando pasan >2s sin fix
- Cerrar el gap cuando vuelve un fix
- Abandonar el gap si se cierra sesion mientras esta abierto

Funciones nuevas en `db/journal.ts`:
- `openGap(db, sessionId, startFixId, ...)` — abre
- `closeGap(db, gapId, endFixId, endAtMs)` — cierra
- `getOpenGap(db, sessionId)` — consulta
- `abandonGap(db, gapId, abandonedAtMs)` — abandona al cerrar sesion

### 1.5 Seis decisiones congeladas

Guardadas en `.logos/decisions/`:
- D-2026-0001: Estimacion != evidencia observada
- D-2026-0002: Gap como entidad persistente
- D-2026-0003: Track observado != track estimado
- D-2026-0004: Migraciones SQLite versionadas y exclusivas
- D-2026-0005: Verificacion post-migracion
- D-2026-0006: Version efectiva de expo-sqlite = 16.0.10

### 1.6 Once hipotesis guardadas

`~/.logos/hypotheses/` ahora tiene:

- H-0001 EN_CURSO — Arquitectura de mapas A vs B
- H-0002 PROPUESTA — Replay determinista
- H-0003 CONFIRMADA — DSH deriva hipotesis
- H-0004 CONFIRMADA+VERIFICADA — Gap fantasma (bug encontrado y arreglado)
- H-0005 PROPUESTA — Gap duplicado (race condition)
- H-0006 PROPUESTA — Duracion de gap por reloj de pared
- H-0007 PROPUESTA — Perfiles de tarea para brief
- H-0008 PROPUESTA — Frontera de contexto explicita
- H-0009 PROPUESTA — Brief como JSON canonico
- H-0010 PROPUESTA — Deteccion de fuentes desactualizadas
- H-0011 PROPUESTA — Registro de traspaso entre IAs

---

## 2. BUG ENCONTRADO Y ARREGLADO (H-2026-0004)

### 2.1 Que era

Si el usuario apretaba "Finalizar" mientras habia un gap abierto
(corte de senal activo), el gap quedaba `OPEN` para siempre en la
base. Nadie lo cerraba. Se acumulaban fantasmas.

### 2.2 Como se encontro

DSH (agente local) formulo 3 hipotesis de conflicto GNSS cuando se
le pidio. La primera fue esta. DSH no lo invento: leyo el codigo
y detecto que `getOpenGap` estaba exportada pero nunca se invocaba.

### 2.3 Como se probo

Test con el replay:
- Umbral temporal bajado de 10s a 2s (para ampliar ventana de test)
- Apretar "Finalizar" durante el gap
- Logs agregados al tracker

Resultado: `[TEST-H0004] ANTES: gaps OPEN = 1` /
`[TEST-H0004] DESPUES: gaps OPEN = 1`. Confirmado el bug.

### 2.4 Como se arreglo

Se agrego `abandonGap` a `journal.ts`, y el tracker la llama antes
de `endSession` en `stopTracking`.

### 2.5 Como se verifico

Test repetido 2 veces:
- `[FIX-H0004] gap abandonado: gap_...`
- `[TEST-H0004] DESPUES: gaps OPEN = 0`

Ambas corridas dieron 0. Bug arreglado.

### 2.6 Evidencia

`h0004-test2.log` — bug confirmado
`h0004-test3.log` — fix verificado

---

## 3. PENDIENTES

### 3.1 Urgentes (proxima sesion)

- **Rebuild del APK limpio.** El del TCL tiene el umbral de 2s y
  los logs [TEST-H0004] todavia. El codigo en el repo ya esta limpio.
  Falta recompilar e instalar.
- **Capsula de memoria desactualizada.** No refleja las 6 decisiones
  ni las 11 hipotesis nuevas. DSH lo detecto al principio de la sesion.
- **Rama de git desincronizada.** `AGENTS.md` dice `experimento-dsh-01`,
  la realidad es `experimento-v4-admin`. Hay cambios sin commitear.

### 3.2 Hipotesis sin probar

- H-2026-0005 — Gap duplicado (race condition)
- H-2026-0006 — Duracion de gap por reloj de pared
- H-2026-0007 a H-2026-0011 — Gobernanza de contexto (diseño)

### 3.3 Proyecto grande

- Dead reckoning (DR) para posicion estimada durante gaps
- Escenarios largos con curvas desde el simulador Godot
- Tiempo 2 de LOGOS: integrar decision_records al MANIFEST

### 3.4 Hallazgos de DSH sin resolver

- `EXPEDIENTE/09` declarado como multi_ia_protocol pero su contenido
  es sobre Modo Soberano. Inconsistencia entre MANIFEST y contenido.

---

## 4. DSH — EVALUACION DE DESEMPEÑO

DSH participo en 2 tareas grandes. Ambas superadas con nota:

### Tarea 1: Hipotesis de conflicto GNSS

- Formulo 3 hipotesis solidas (no 5 de relleno)
- Cito lineas exactas del codigo
- Marco 4 incertidumbres explicitas
- Descarto 2 escenarios con justificacion (no aplican)

### Tarea 2: Diseño del rol de portero de contexto

- Detecto que la capsula se pasa entera en cada tarea (no hay seleccion)
- Propuso 5 hipotesis de diseño, no empiricas
- Encontro que EXPEDIENTE/09 esta mal etiquetado
- Listo 8 incertidumbres para el Director

### Conclusion

DSH es util como portero de contexto y como formulador de hipotesis.
Encontro un bug real (H-0004) leyendo el codigo. Eso demuestra que
trabaja con evidencia, no con alucinaciones.

---

## 5. ARCHIVOS CLAVE DE HOY

### Codigo del proyecto
- `LocationProvider.ts`
- `ReplayLocationProvider.ts`
- `devConfig.ts`
- `useNaveGoTracker.ts` (modificado)
- `db/journal.ts` (modificado)
- `db/schema.ts` (modificado)
- `components/MapaOffline.tsx` (modificado)
- `metro.config.js` (modificado)

### Sistema LOGOS
- `.logos/decisions/D-2026-0001..0006.json`
- `~/.logos/hypotheses/H-2026-0004.json` (actualizada)
- `~/.logos/hypotheses/H-2026-0007..0011.json` (nuevas)
- `~/.logos/hypotheses/INDEX.md` (actualizado)

### Logs de test
- `h0004-test.log` — primer intento (no alcanzo)
- `h0004-test2.log` — bug confirmado
- `h0004-test3.log` — fix verificado

### Backups internos
- `useNaveGoTracker.ts.pre-*` (varios)
- `db/journal.ts.pre-*`
- `db/schema.ts.pre-*`

---

## 6. PROXIMA SESION — SUGERENCIA

Orden sugerido:

1. **Rebuild limpio + install** (5 min). Dejar el TCL con codigo limpio.
2. **Actualizar capsula de memoria** (30 min). Incorporar hipotesis
   nuevas y decisiones. Que refleje el estado real del sistema.
3. **Implementar H-2026-0007** (perfiles de tarea). Este es el que
   resuelve el problema del Director: no explicar todo a cada IA nueva.
4. **Cuando haya tiempo:** probar H-0005 y H-0006, seguir con DR,
   armar escenarios largos del simulador.

---

*Generado: 2026-09-25 ~02:50*
*Por: DeepSeek (chat) + DSH (agente local) bajo direccion del Director*
