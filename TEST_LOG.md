# TEST LOG — NaveGo

Actualizado: 2026-08-19

## 2026-08-19 — Course-Up a velocidad peatonal

### Condiciones
- Exterior
- Caminando
- Dando vuelta a la manzana
- Dispositivo TCL X1 Pro
- Mapa en landscape

### Resultado
- El mapa giro y se alineo con el rumbo real.
- La sincronizacion visual coincidio con lo observado.
- El acelerometro funciono correctamente.

### Evidencia
- Derrota guardada: 422 m.
- El mapa se ajusto con fluidez a velocidad peatonal.

### Estado de verificacion
- Course-Up: OBSERVADO, NO VALIDADO en velocidad de auto.
- Acelerometro como indicador de horizontalidad: OBSERVADO, funciona.

## Problemas detectados
- Segunda derrota no se visualiza en el mapa aunque dice guardada con exito.
- Acumulado de aproximadamente 3500 m sin explicacion clara.
- Guardado intermitente de derrotas, con y sin WiFi.

## Observaciones adicionales
- En casa, guardo sin internet (modo avion). OK.
- En casa de la madre, a veces guardo y a veces no.
- El indicador de internet de la PC no se conecto nunca en casa de la madre.
- Posible acumulacion de metros entre sesiones.

## Hipotesis separadas
1. El guardado local es independiente del internet.
2. El indicador de internet se confunde con el guardado.
3. La red WiFi de la casa de la madre interfiere.
4. El guardado intermitente es un problema de sesion, no de red.

## Experimento propuesto
En casa con WiFi normal: registrar y finalizar derrota.
En casa en modo avion: registrar y finalizar derrota.
En casa de la madre con WiFi: registrar y finalizar derrota.
En cada caso registrar:
- Dice guardada con exito?
- Aparece en Historial?
- Aparece en el mapa?
- Indicador de internet en verde, ambar o rojo?

## Siguiente experimento
- Probar Course-Up en auto a mayor velocidad.
- Observar fluidez y posible retraso.
- Registrar COG, SOG y sensacion visual.

## Pendiente futuro
- Evaluar boton para eliminar sesiones con confirmacion.
- Revisar acumulacion de metros entre derrotas.
- Separar correctamente las sesiones en el almacenamiento.

## 2026-08-20 — Prueba piloto de control remoto sin teclado

### Resultado
- Se creo voice_bridge.js en el proyecto.
- Se levanto en el puerto 4000.
- Se probo desde el celular en la misma red Wi-Fi.
- URL utilizada: http://192.168.1.19:4000/guardar
- La PC ejecuto save.ps1 correctamente.
- Se obtuvo mensaje "Version guardada de NaveGo".

### Validacion
- Funciona el control remoto por red local sin teclado.
- No se toco NaveGo, tracking, SQLite ni HUD.
- Queda como apendice piloto para futura integracion con voz.

### Proximos pasos
- Incorporar mas comandos: arrancar, estado, backup.
- Integrar con Geminis o asistente de voz.
- Evaluar seguridad y confirmacion para acciones criticas.

## 2026-08-21 — Blindaje de LOGOS

### Resultado
- Se implemento token de acceso en voice_bridge.js.
- Se separo panel.html de voice_bridge.js.
- Se actualizo save.ps1 para calcular y guardar hash SHA-256.
- Se genero integrity.json con hashes de scripts criticos.
- Se probo el panel LOGOS desde el celular con exito.
- Se confirmo que una peticion sin token es rechazada.

### Validacion
- El token protege los comandos remotos.
- La integridad SHA-256 queda registrada en cada guardado.
- NaveGo no fue tocado.

### Proximos pasos
- Blindar simulate.js con token.
- Reducir superficie de red de los servicios locales.
- Evaluar deshabilitar SMB/NetBIOS en red hostil.
- Actualizar SECURITY_BASELINE.md con estado implementado.

## 2026-08-22 — Cierre de sesión: avances y pendientes

### Logros
- Indicador de internet corregido (IP 192.168.1.19).
- Mojibake corregido en useNaveGoTracker.ts, journal.ts y HistoryScreen.tsx.
- Token de acceso en LOGOS operativo.
- Panel visual LOGOS con botones Guardar, Estado, Arrancar y Backup.
- Integridad SHA-256 en save.ps1, con integrity.json.
- SECURITY_BASELINE.md actualizado.
- EXPANSION_TELEMETRY.md creado como requerimiento futuro.
- Máquina de estados de sesión definida conceptualmente.

### Pendientes para próxima sesión
- Implementar máquina de estados en código (amarre, registrando, pausa, finalizada).
- Botón resetear visible después de finalizar.
- Evitar duplicar referencia si ya existe.
- Arreglar scroll en HistoryScreen.
- Revisar acumulación de distancia y reset estricto.
- Actualizar Cockpit con estado real.

## 2026-08-22 — Cierre ampliado: tareas para próxima sesión

### Nuevas tareas
- Auditar App.tsx.bak y decidir conservar, renombrar o eliminar.
- Diseñar interfaz de PC para control del Cockpit (misma base que panel LOGOS, 4-5 botones, pantalla grande).
- Implementar lectura automática del estado real de documentos vivos en el Cockpit.
- Hacer que el Cockpit se actualice automáticamente con cada guardado.
- Reflejar en Cockpit: fase, semáforo, última actualización, tareas pendientes, estado de servicios.

### Tareas pendientes previas
- Implementar máquina de estados de sesión en código.
- Botón resetear visible después de finalizar.
- Evitar duplicar referencia si ya existe.
- Arreglar scroll en HistoryScreen.
- Revisar acumulación de distancia y reset estricto.
- Actualizar Cockpit con estado real.

## 2026-08-22 — Decisión de lenguaje náutico

### Cambio adoptado
- "Soltar amarras" reemplaza a "Iniciar derrota".
- "Amarrar" o "Volver a amarrar" reemplaza a "Pausar".
- "Reanudar navegación" reemplaza a "Reanudar".
- "Finalizar travesía" o "Concluir registro" reemplaza a "Finalizar".

### Motivo
- Evitar connotación negativa de "derrota".
- Reflejar mejor la pausa física y el reinicio de navegación.

### Aplicación
- Se implementará en la máquina de estados de sesión.
