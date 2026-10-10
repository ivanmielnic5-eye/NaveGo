# TIMONEL DSH — Canal bidireccional Polaris ↔ DSH

**Fecha:** 2026-09-26
**Estado:** diseño aprobado. Fase 1 pendiente de implementar.
**Propósito:** permitir que DSH (Qwen 7B) conduzca el velero
Polaris en el simulador `interfaz/`, mediante un canal
bidireccional de archivos.

---

## Decisiones cerradas

| # | Decisión |
|---|---|
| D1 | Velero se llama **Polaris** |
| D2 | Cuando DSH lo conduce, **DSH es el Timonel** |
| D3 | Comunicación vía **proceso intermediario** `timonel.py` |
| D4 | Godot escribe a **`user://timonel/`** (convención Godot) |
| D5 | **Un escritor por archivo**: Godot escribe telemetría, Python escribe comandos |
| D6 | Timestamps en **epoch ms** |
| D7 | Ritmo **parametrizable** (30 s en Fase 1, 45-60 s en Fase 2) |
| D8 | **Nodo hermano** `timonel_bridge.gd`. No toca scripts existentes |
| D9 | Modelo: **`qwen2.5-coder:7b`** |

---

## Arquitectura

Godot (Polaris)
  - timonel_bridge.gd   (nodo nuevo, hermano)
      escribe -> telemetria.jsonl
      lee    <- comandos.jsonl
  - resto de scripts    (SIN CAMBIOS)

timonel.py (Python, proceso separado)
  - lee   <- telemetria.jsonl
  - POST  -> http://127.0.0.1:11434/api/generate  (DSH)
  - escribe -> comandos.jsonl

---

## Formato telemetria.jsonl

Una linea por muestra. Godot escribe, Python lee.

{"t":1758912345678,"pos_x":12.3,"pos_y":0.1,"pos_z":-45.6,
 "sog_kn":2.6,"cog_deg":171,"hdg_deg":0,
 "aws_kn":2.6,"awa_deg":8,
 "roll_deg":1.2,"pitch_deg":-0.4,"yaw_deg":0.0}

## Formato comandos.jsonl

Una linea por decision. Python escribe, Godot lee.

{"t":1758912345700,"timon":0,"fuente":"dsh","nota":"recto"}

timon en {-1, 0, +1} — babor / recto / estribor.

---

## Protocolo de las dos corridas

### Corrida 1 — Tubo estatico
timonel.py NO consulta a DSH. Escribe timon=0 fijo cada 30 s.
Sirve para validar el flujo completo sin depender de la
latencia del modelo. Si el velero se mueve y el log del bridge
muestra que leyo los comandos, el tubo funciona.

### Corrida 2 — Logica activa
timonel.py si consulta a DSH. Prompt acotado: ultimas N
muestras de telemetria + instruccion de responder solo -1, 0
o +1. Se guarda todo lo que DSH devuelve en
.logos/dsh-output/ para trazabilidad.

---

## Fuera de alcance en Fase 1

- Vela, SOG, AWA, oleaje — solo timon.
- Sin canal tiempo real (Fase B del informe del hilo perdido).
- Sin nombre de IA en el HUD.
- Sin persistencia del plan completo.

---

## Como verificar que funciona

1. Godot corriendo -> telemetria.jsonl crece.
2. timonel.py corriendo -> comandos.jsonl crece con timon=0.
3. En el HUD del Monitor aparece un indicador nuevo de timon.
4. El velero NO se rompe si timonel.py no esta corriendo.

---

## Riesgos

- R1: Qwen tarda >30 s. Mitigacion: timeout + descartar viejas.
- R2: Caracteres no esperados. Mitigacion: parseo estricto,
  fallback a 0.
- R3: Race condition. Mitigacion: un escritor por archivo (D5).

---

# FASE 1 — TUNEL DE INFORMACION (CERRADA)

**Fecha de cierre:** 2026-09-26
**Veredicto:** EXITOSA. Todos los hitos alcanzados.

---

## HITO 1 — Bridge creado

Archivo: `~/interfaz/scripts/timonel_bridge.gd` (112 lineas).

Nodo nuevo `TimonelBridge` agregado como hermano en `main.tscn`.
No toca ningun script existente. Si `timonel.py` no corre, no
rompe nada.

Escribe `telemetria.jsonl` cada 1 s.
Lee `comandos.jsonl` cada 0.5 s.
Aplica torque al velero cuando `timon != 0`.

---

## HITO 2 — Intermediario creado

Archivo: `~/navego_recuperado/timonel/timonel.py` (126 lineas).

Lee telemetria, consulta a DSH (opcional), escribe comandos.
`MODO_FASE1 = True` durante Fase 1 (no consultaba a DSH).

Un escritor por archivo respetado:
- Godot escribe telemetria.jsonl
- timonel.py escribe comandos.jsonl

---

## HITO 3 — Corrida end-to-end

Godot corriendo, timonel.py corriendo, ambos en paralelo.

Evidencia en disco:
- `telemetria.jsonl` crecio hasta ~50 KB (~150 muestras).
- `comandos.jsonl` acumulo 6 comandos con intervalo exacto 30 s.

Sin errores en consola de Godot. Sin romper Monitor, GroundTruth,
FloatCube ni ningun otro script.

---

## HITO 4 — DSH leyo telemetria real

Se le paso una muestra de 3 lineas reales de telemetria, con
4 preguntas:
1. Que ves en esos numeros.
2. Que informacion te falta para decidir.
3. Que comandos querrias emitir ademas de -1/0/+1.
4. Primera decision como Timonel.

Respuesta archivada en:
`logos/dsh/respuesta_fase1_2026-09-26.txt` (2594 chars, 64.5s).

---

## HITO 4a — LO QUE DSH LEYO BIEN

- SOG = 2.60 kn. Correcto.
- Posicion x/z coherente con la telemetria.
- Reconoce explicitamente que le falta informacion.
- Pide viento (aws/awa) — coincide con lo que el bridge
  hoy envia en 0.0 fijo.
- Pide estado de vela.
- Propone comandos de velocidad, vela y estabilizador —
  coincide con la progresion acordada del proyecto
  (timon -> vela -> SOG -> viento -> oleaje).

---

## HITO 4b — LO QUE DSH ALUCINO (registro honesto)

La respuesta contiene errores graves que NO se ocultan:

- Menciona "el Titanic" — se lo invento. El velero se llama
  Polaris.
- Dice "171.00 grados en el eje Z" — 171 es COG, no un eje.
- Dice "pos_y = -2.43 indica movimiento hacia adelante" —
  pos_y es profundidad, no direccion.
- Dice "pos_z = 242, bastante arriba en su trayectoria" —
  pos_z es coordenada horizontal del mundo, no altura.
- Dice "la vela esta parcialmente abierta" — AWA=0 significa
  SIN VIENTO, no vela abierta.
- Inventa tripulacion, otros barcos, emergencias — nada de
  eso existe en el simulador.
- La pregunta 4 pedia UNA decision concreta. Dio cinco.

Diagnostico: DSH no comprende que la telemetria viene de un
RigidBody en un simulador. Trata los numeros como si fueran
de un barco real con tripulacion.

---

## HITO 5 — El tubo esta probado

Godot -> telemetria.jsonl -> timonel.py -> (opcional DSH) ->
comandos.jsonl -> Godot. Funciona en ambos sentidos.

Fase 1 cerrada con exito tecnico.

Fase 2 arrancara con estas correcciones:
1. Prompt con "mundo" explicito (simulador, sin tripulacion).
2. Formato de salida forzado.
3. Arrancar con decisiones simples (-1/0/+1 unicamente).
4. Enviar aws/awa reales desde el bridge.

---

## Lecciones de Fase 1

1. **El aislamiento funciono.** El bridge como nodo hermano no
   rompio nada. Godot arranco sin un solo error nuevo.

2. **El ritmo de 30 s es comodo.** Sin saturacion de I/O, sin
   acumulacion de requests.

3. **Un escritor por archivo es suficiente.** No hubo race
   conditions ni bloqueos.

4. **Qwen 7B alucina fuera de su dominio.** Es un modelo
   "coder". Hay que acotarlo fuerte en el prompt, o aceptar
   que sus respuestas requieren filtro humano.

5. **El bridge no envia todo lo que DSH necesita.** Falta
   aws, awa, y estado del timon. Son los pedidos de DSH en
   la pregunta 2, y son la base de Fase 2.

---

## Estado al cierre

- Codigo Fase 1: `~/interfaz/scripts/timonel_bridge.gd` (112 l).
- Codigo Fase 1: `~/navego_recuperado/timonel/timonel.py` (126 l).
- Diseno completo: este documento.
- Evidencia DSH: `logos/dsh/respuesta_fase1_2026-09-26.txt`.
- Evidencia runtime: telemetria y comandos en
  `~/.local/share/godot/app_userdata/interfaz/timonel/`.

---

## Proximo paso: FASE 2

Cuando el Director lo indique:

1. Modificar `timonel.py`: `MODO_FASE1 = False`.
2. Corregir el prompt a DSH: mundo explicito, formato forzado,
   arrancar con -1/0/+1 unicamente.
3. Agregar log de comandos leidos en `timonel_bridge.gd`.
4. Enviar aws/awa reales desde el bridge (hoy en 0.0).
5. Correr. Ver a Polaris girar bajo decision de DSH.

---

# FIN DE FASE 1
