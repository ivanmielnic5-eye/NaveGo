# HITO: GRABACION PERSISTENTE DE NAVEGO

**Fecha:** 2026-09-25
**Estado:** PROPUESTO — pendiente de diseño
**Prioridad:** MAXIMA de la etapa actual
**Responsable:** Director + IAs (DeepSeek, DSH, GPT, Claude)

---

## 1. El objetivo

Que NaveGo NO CORTE la grabacion de una travesia cuando:

- La app pasa a segundo plano (usuario abre otra app).
- La pantalla del celular se apaga.
- El usuario cierra la app por error.
- El celular se reinicia (caso extremo).

**La travesia debe continuar. La grabacion debe continuar.
Los gaps se registran. Los fixes se guardan. El track se
construye sin importar el estado de la app.**

---

## 2. Por que es un hito

Hoy la app depende de `watchPositionAsync` de expo-location. Ese
metodo **solo funciona en primer plano**. Si la app se pausa, la
grabacion se detiene silenciosamente.

Consecuencia: cualquier interrupcion en la navegacion real (mensaje
de WhatsApp, llamada, cambio de app) **corrompe la travesia**.

Para una app de navegacion, eso es inaceptable. Es el equivalente
a que un chartplotter se apague cuando el usuario toca otra cosa
en el panel.

**Resolver esto cambia la app de "util en pantalla activa" a
"confiable para navegacion real".**

---

## 3. Los tres niveles de persistencia

### Nivel 1 — Doble confirmacion en "Finalizar"

**Dificultad:** baja.
**Tiempo:** 10-20 minutos.
**Riesgo:** bajo.

Boton "Finalizar" abre un modal de confirmacion. Evita cierres
accidentales.

**Implementacion:** `<Modal>` de React Native. Estado en `App.tsx`.

### Nivel 2 — Seguir grabando en segundo plano

**Dificultad:** media.
**Tiempo:** 1-2 dias.
**Riesgo:** medio.

Migrar de `watchPositionAsync` a
`startLocationUpdatesAsync` + `TaskManager`. Requiere definir
una task de background.

**Recursos:**
- expo-location.startLocationUpdatesAsync
- expo-task-manager

**Permisos nuevos:** `ACCESS_BACKGROUND_LOCATION` (Android 10+).

**Efecto esperado:** el celular bloqueado o con otra app abierta
sigue actualizando posiciones cada 1 segundo (o el intervalo
configurado).

### Nivel 3 — Seguir grabando con app cerrada

**Dificultad:** alta.
**Tiempo:** 3-5 dias.
**Riesgo:** alto.

Requiere **Foreground Service** de Android:
- Servicio nativo corriendo en primer plano.
- Notificacion permanente "NaveGo esta grabando".
- Pelear con Doze mode, restricciones de bateria, etc.
- Manejo de reinicio del dispositivo.

**Recursos:**
- `expo-notifications` (para la notificacion).
- Servicio propio en Android (Kotlin/Java).
- O librerias como `react-native-background-actions`.

**Efecto esperado:** incluso si el usuario cierra la app, el
servicio sigue grabando. Al reabrir, la sesion se recupera.

---

## 3.5. NIVEL 4 — RETOMAR SESION AL REINICIAR EL CELULAR

**Dificultad:** media.
**Tiempo:** 1-2 dias.
**Riesgo:** medio.

Ademas de los 3 niveles anteriores, hay un caso critico:

- El celular se apaga por inactividad (configuracion de ahorro de
  bateria del usuario).
- El usuario no apreto "Finalizar".
- El celular se reinicia (se prendio de nuevo).
- **La sesion NO debe perderse.**

**Regla sagrada:**

> **Mientras no haya "Finalizar", la sesion sigue abierta.**
> **El celular se apague o se reinicie, la app retoma la sesion
> al volver.**

**Como se implementa:**
- Android permite que una app se despierte al reiniciar el celular
  con el permiso `RECEIVE_BOOT_COMPLETED`.
- Al despertar, la app lee `sessions` en SQLite y busca sesiones
  con `status = 'ACTIVE'` (sin `end_time`).
- Si encuentra una, la retoma automaticamente.
- El usuario ve la sesion como si nunca se hubiera interrumpido.

**Limitacion fisica:** si el hardware esta apagado (bateria 0%),
ningun software corre. Eso no se puede cubrir. Pero el caso real
es que el celular se reinicia, no que se apaga de verdad.

**Escenario del viaje (real):**

- Viaje de ida: Santa Fe -> Buenos Aires. Sesion 1.
  Carpeta `navego_track/2026-09-XX_ida/`.
- Llegada: "Finalizar". Sesion 1 cerrada.
- Viaje de vuelta: Buenos Aires -> Santa Fe. Sesion 2.
  Carpeta `navego_track/2026-09-YY_vuelta/`.
- Llegada a Santa Fe: "Finalizar". Sesion 2 cerrada.

Cada viaje es una sesion. Cada sesion tiene su propia carpeta.
Cada sesion sobrevive a las interrupciones del celular.

---

## 4. Hipotesis a validar

**H-2026-0021** — Grabacion en background y con app cerrada.
**H-2026-0022** — Retomar sesion al reiniciar el celular.

---

## 5. Orden de implementacion

1. **Doble confirmacion** (Nivel 1). Hoy mismo, 10 min.
2. **Background** (Nivel 2). Semana siguiente.
3. **Foreground Service** (Nivel 3). Despues, si hace falta.

No saltar al Nivel 3 sin pasar por el 2. El 2 valida el patron.
El 3 es refinamiento. El 4 es la frutilla del postre.

---

## 6. Que NO se rompe

Al implementar la grabacion persistente, el resto del sistema
debe seguir funcionando igual:

- Los gaps se abren y cierran correctamente.
- La distancia confirmada sigue excluyendo los tramos no observados.
- El track honesto (Estados 1-4) sigue funcionando.
- La base SQLite se mantiene consistente.
- El HUD muestra los dos numeros.

Si algo de esto se rompe, la implementacion esta mal.

---

## 7. Que se anota en el sistema

Este hito va registrado en:

- Este expediente (contexto).
- `~/.logos/PENDIENTES_NAVEGO.md` (tareas concretas).
- `~/.logos/hypotheses/H-2026-0021.json` (hipotesis falsable).
- `context.json` del proyecto (proximo paso).

---

## 8. Criterio de exito

**Exito:** una sesion de navegacion de 30 minutos con 3
interrupciones (app en background, pantalla apagada, otra app
abierta) registra correctamente:
- Todos los fixes.
- Todos los gaps (abiertos y cerrados).
- La distancia confirmada correcta.
- Ningun corte en la travesia.

**Fracaso:** cualquier interrupcion produce un gap artificial en
la travesia, o pierde fixes, o cierra la sesion sin que el
usuario lo pidio.

---

*Generado: 2026-09-25*
*Por: DeepSeek (chat) bajo direccion del Director*
