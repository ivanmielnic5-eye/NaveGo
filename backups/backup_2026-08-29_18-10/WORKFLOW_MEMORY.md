# WORKFLOW MEMORY — NaveGo

**Versión:** 1.0
**Fecha de creación:** 2026-08-29
**Última actualización:** 2026-08-29
**Ubicación:** C:\Users\ivan\Downloads\_Proyectos\NaveGoLocal\governance\WORKFLOW_MEMORY.md

---

## 📍 POSICIÓN ACTUAL

- **Proyecto:** Ambos (NaveGoLocal + Simulador Godot)
- **Última tarea:** Auditoría de dependencias en Simulador (scripts huérfanos, duplicación de HUD).
- **Estado:** En pausa — preparando gobernanza y contexto compartido.
- **Próxima acción:** Implementar WORKFLOW_MEMORY.md y definir ritual diario.

---

## 🗺️ MAPA DE RUTA

### Objetivos generales
1. **NaveGoLocal (App móvil):** Pipeline de navegación offline-first funcionando con Kalman + ZUPT + GPS State Machine. Pendiente: prueba de campo y ajuste de parámetros.
2. **Simulador Godot:** Limpiar duplicación de HUD (Monitor.gd vs hud.gd), consolidar scripts activos, preparar flujo de exportación de logs para pruebas de la app.

### Próximos hitos
1. **Hoy/Tarde:** Crear WORKFLOW_MEMORY.md y establecer ritual de apertura/cierre.
2. **Mañana:** Primera apertura de jornada con el archivo. Evaluar si necesitamos ajustes.
3. **Esta semana:**
   - App: Conectar acelerómetro real al orquestador processGpsFix (reemplazar placeholder).
   - Simulador: Aplicar plan de intervención (reasignar Monitor.gd, eliminar huérfanos).
   - Unificación: Crear documento NAVEGO_UNIFICATION_v1.md (alcances, flujo de datos, vocabulario común).

### Decisiones pendientes
- [ ] ¿Mantenemos eact-native-maps o migramos a MapLibre en la app? (Decisión: mantener por ahora, posponer migración).
- [ ] ¿Cuándo hacemos la primera prueba de campo con el pipeline completo? (Propuesta: después de conectar acelerómetro real).

---

## 📋 REGISTRO DE INCIDENTES

| Fecha | Incidente | Causa | Solución | Estado |
|-------|-----------|-------|----------|--------|
| 2026-08-29 | Duplicación de HUD en Simulador Godot (hud.gd vs Monitor.gd) | Ambos scripts asignados al nodo HUD en la escena principal, compitiendo por recursos visuales. | Reasignar Monitor.gd al nodo HUD, verificar funcionamiento, eliminar scripts huérfanos. | 🔴 EN CURSO (pendiente de ejecución) |
| 2026-08-28 | Error en kinematics.ts (extracto incompleto al compartir con IA) | Recorte de código para mensaje, omitiendo funciones críticas (predictKalman, updateKalman, helpers de matrices). | Confirmar que el código real está completo y funcional. El orquestador processGpsFix ya usa los helpers correctos. | 🟢 RESUELTO (documentado en el chat) |
| 2026-08-27 | Confusión entre proyectos: pérdida de contexto al alternar entre App y Simulador | Falta de un archivo central que unifique el estado de ambos proyectos. | Creación de WORKFLOW_MEMORY.md como punto de verdad único. | 🟡 REPETIDO (se implementa hoy) |

---

## 🧠 LECCIONES APRENDIDAS (Reglas del proyecto)

### Regla 1: El contexto es sagrado
> **"Antes de empezar a trabajar, consulta el WORKFLOW_MEMORY.md. Antes de cerrar la jornada, actualízalo."**

### Regla 2: No añadir complejidad innecesaria
> **"El sistema destinado a reducir la complejidad no puede introducir complejidad significativa."**
> (Frase extraída de conversación con ChatGPT, 2026-08-29)

### Regla 3: Evidencia antes que certeza
> **"No asumir. Verificar. Siempre."**
> Aplica a: scripts huérfanos, datos GPS, dependencias, soluciones propuestas.

### Regla 4: Separar pero unificar
> **"Los proyectos pueden ser independientes, pero su gobernanza es común."**
> El WORKFLOW_MEMORY.md vive en la raíz y sirve a ambos.

### Regla 5: La IA es herramienta, no autoridad
> **"La IA propone, el humano decide."**
> El sistema de auditoría es solo lectura; la decisión final siempre es nuestra.

### Regla 6: Sistema inmunológico del proyecto (NaveGo Development Guard)
> **"Detectar patrones recurrentes y aumentar la respuesta cuando vuelven a aparecer."**

#### Niveles de respuesta:
- **Primera aparición** → 🟡 Advertencia (documentar en incidentes).
- **Segunda aparición** → 🟠 Revisión obligatoria (auditar dependencias).
- **Tercera aparición** → 🔴 Bloqueo preventivo + auditoría profunda.

#### Semáforo de estados:
- 🟢 NORMAL
- 🟡 REPETIDO
- 🟠 ESCALADO
- 🔴 MONITOREO / BLOQUEADO
- 🔵 RECUPERACIÓN (después de resolver, antes de volver a NORMAL)

---

## 🔄 ÚLTIMA INTERACCIÓN (con IA)

- **Fecha:** 2026-08-29
- **Resumen:** Se revisó el estado de ambos proyectos (App y Simulador). Se identificó la necesidad de un mecanismo de gobernanza compartido. Se propuso el WORKFLOW_MEMORY.md como tablero de contexto. Se definieron rituales de apertura/cierre de jornada. Se establecieron los cimientos del NaveGo Development Guard (sistema inmunológico del proyecto).
- **Archivos tocados:** Ninguno (fase de diseño).
- **Decisiones tomadas:**
  1. No empezar con la Fase A de NaveGoLocal (conexión de acelerómetro) hasta implementar el WORKFLOW_MEMORY.md.
  2. Priorizar la gobernanza mínima antes de cualquier intervención técnica.
  3. No construir un agente autónomo; construir primero un auditor de solo lectura.
  4. Incorporar el concepto de "memoria inmunológica" con niveles de respuesta ante patrones recurrentes.
- **Pendientes:** Crear el archivo, definir estructura, llenarlo con estado actual.

---

## 🔵 RECUPERACIÓN (Incidente abierto)

**Incidente:** HUD_DUPLICATION en Simulador Godot.

**Estado actual:** 🔴 MONITOREO (pendiente de intervención).

**Plan de acción:**
1. Reasignar Monitor.gd al nodo HUD en main.tscn.
2. Verificar que el simulador funcione correctamente (F6).
3. Si funciona, eliminar scripts huérfanos (hud.gd, Diagnostico.gd, DiagnosticoTecla.gd, estela.gd).
4. Documentar el cambio en este archivo.
5. Ejecutar test de regresión: simular 5 minutos y verificar que no haya errores.
6. Si todo ok, pasar a 🟢 NORMAL.

**Regla aprendida:**
*"Antes de crear un nuevo HUD, auditar los existentes y verificar si ya cumplen la función."*

---

## 📋 CHECKLIST DIARIO (Ritual de apertura)

### ⏰ Mañana (antes de empezar)
- [ ] Abrir WORKFLOW_MEMORY.md y leer "POSICIÓN ACTUAL" y "MAPA DE RUTA".
- [ ] Copiar "ÚLTIMA INTERACCIÓN" al inicio del chat con la IA (si la usas).
- [ ] Preguntar: *"¿Qué debo saber antes de empezar hoy?"*
- [ ] Elegir la tarea más prioritaria del día (marcarla como "en progreso").

### 🌙 Tarde (al finalizar)
- [ ] Actualizar "POSICIÓN ACTUAL" con lo que se hizo.
- [ ] Si hubo incidentes, agregarlos al "REGISTRO DE INCIDENTES".
- [ ] Si se aprendió algo, agregarlo a "LECCIONES APRENDIDAS".
- [ ] Actualizar "ÚLTIMA INTERACCIÓN" con un resumen del día.
- [ ] Guardar y cerrar el archivo.

---

## 🧘 RECORDATORIO (Sticker mental)

> **"Antes de empezar, ¿miraste el tablero?"**

---

## 📌 NOTAS ADICIONALES

- Este archivo es la **fuente de verdad** del proyecto. Si algo no está aquí, no existe.
- Puede crecer con el tiempo, pero debe mantenerse **legible y accionable**.
- Si un día no hay tiempo para actualizarlo, escribir al menos 3 líneas de resumen.
- Revisar semanalmente para archivar incidentes viejos y mantenerlo liviano.

---

**Próxima actualización programada:** 2026-08-30 (apertura de jornada).
