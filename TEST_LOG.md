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
