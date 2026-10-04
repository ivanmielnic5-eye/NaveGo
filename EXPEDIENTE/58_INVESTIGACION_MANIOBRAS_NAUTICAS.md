# INVESTIGACION — Maniobras Nauticas y Fisica de Simulacion — 2026-10-04

**Proyecto:** Timonel (agente LLM local que pilota Polaris)
**Fuente:** LLM Notebook (investigacion con busqueda en internet)
**Estado:** informe bruto, sin procesar. Material de referencia para el manual de maniobras.
**Uso:** datos de calibracion del simulador Python y disenio de recetas.

---

## 1. Respuestas a las Preguntas Especificas de Calibracion

### A) Radio de giro real de un velero de 8m a 4 nudos

- **Radio de giro fisico:** 12 a 20 metros (diametro tactico de 24 a 40 metros, 3 a 5 veces la eslora).
- **Fundamento hidrodinamico:** un velero de 3500 kg posee orza/quilla fija profunda y timon de pala suspendida. A 4 nudos, con el timon metido a fondo (30 a 35 grados de angulo de pala), la fuerza centripeta generada por la pala hace que el barco pivote sobre su centro de lateralidad (ubicado cerca del palo/quilla), barriendo una huella circular cerrada de aproximadamente 2.5 a 3 esloras de diametro interior.

### B) Velocidad de entrada a puerto / darsena

- **En canal de acceso o antepuerto:** 2.0 a 3.0 nudos.
- **En darsena / calle de amarre:** 1.0 a 1.5 nudos.
- **Aproximacion final al muelle (ultimos 10 metros):** 0.5 a 1.0 nudo (velocidad de gobierno o gobierno con arrancada minima).
- **Regla de oro nautica:** "Nunca te acerques a un muelle a una velocidad mayor a la que estas dispuesto a chocar contra el". A 4 nudos la inercia de 3500 kg destruye guardamancebos, proa o cornamusas.

### C) Secuencia exacta de la maniobra de Ciaboga

La ciaboga permite girar el barco 360 grados dentro de su propia eslora aprovechando el choque de agua del helicoptero en el timon (prop wash) y la fuerza lateral del helicoptero en reversa (prop walk).

- **Presupuesto:** helicoptero dextrogiro (caida de la popa a babor en reversa -> giro de proa a estribor).
- **Secuencia paso a paso:**
  1. **Inicio:** barco totalmente detenido (SOG < 0.5 kts).
  2. **Timon:** meter y mantener todo el timon a Estribor (30-35 grados) durante TODA la maniobra.
  3. **Toque 1 (Avante firme):** enganchar marcha avante a 2000 RPM durante 2 a 3 segundos. El chorro del helicoptero empuja el timon y hace girar la proa a estribor sin dar tiempo a ganar velocidad lineal.
  4. **Transicion:** Neutro (punto muerto) por 1 segundo.
  5. **Toque 2 (Reversa firme):** enganchar marcha atras a 1800-2000 RPM durante 3 a 5 segundos. El prop walk tira de la popa hacia babor (ayudando a que la proa continue pivotando a estribor) y frena cualquier avance hacia adelante.
  6. **Repeticion:** alternar Avante (2-3s) -> Neutro (1s) -> Reversa (3-5s).
- **Tiempo total de giro 360:** 20 a 30 segundos. Espacio requerido: 1.2 veces la eslora (~10 metros).

### D) Magnitud del Prop Walk (Efecto de la Helice) en un barco de 3500 kg

- **Magnitud de la fuerza:** la fuerza lateral no axial producida por las palas del helicoptero representa entre el 10% y el 15% del empuje total de traccion en los primeros segundos de engranar reversa.
- **Desplazamiento real:** en un velero de 3500 kg con motor auxiliar inboard de 12-20 HP y helicoptero dextrogiro de 2 o 3 palas, al engranar reversa con el barco parado, la popa se desplaza lateralmente entre 0.3 y 0.8 metros hacia babor en los primeros 3 a 5 segundos antes de que el barco gane arrancada atras.
- **Dominancia:** con el barco parado o navegando a menos de 1 nudo marcha atras, la fuerza del prop walk supera completamente la accion del timon.

---

## 2. Detalle de los 5 Bloques del Manual de Maniobras

### Bloque 1: Maniobras Basicas a Motor (El "ABC" del Timonel)

1. **Atraque de costado (de Amarra / Muelle):**
   - Aproximacion a un angulo de 20 a 30 grados respecto al muelle, a 1.5 nudos, apuntando a la parte delantera del amarradero.
   - Al estar a media eslora del muelle, meter timon afuera para alinear la embarcacion paralela al muelle.
   - Dar un toque firme de reversa para frenar la arrancada y apoyar la popa mediante el prop walk.

2. **Desatraque de Muelle con Viento o Corriente de Costa:**
   - Usar una espia de proa/popa como pivote. Meter marcha avante contra la espia con timon acantonado hacia el muelle para abrir la popa, retirar la espia y salir marcha atras libre de obstaculos.

3. **Frenado de Emergencia (Atras Todo):**
   - Reducir acelerador a neutro e inmediatamente meter marcha atras a 2500 RPM. La distancia de parada completa a 4 nudos es de 1 a 1.5 esloras (~8 a 12 metros).

4. **Navegacion en Canal Estrecho y Deriva:**
   - Compensacion de la deriva por viento o corriente corrigiendo el rumbo de proa (heading) hacia el barlovento/correntada para mantener la trayectoria lineal real (COG) centrada en el canal.

### Bloque 2: Comportamiento Real vs. Simulado

1. **Perdida de Gobierno a Baja Velocidad:**
   - Por debajo de 1.0 a 1.2 nudos, la velocidad del agua sobre la pala del timon es insuficiente para generar fuerza sustentadora hidrodinamica. El timon "se ablanda" y deja de responder.

2. **Gobierno en Marcha Atras:**
   - El flujo de agua en marcha atras viene desde la popa. El timon tiende a sufrir un golpe violento de cana/rueda (rudder force) si no se sujeta con firmeza, debido a que el centro de presion hidrodinamica se desplaza por detras del eje del timon.

3. **Inercia en el Giro (Overshoot):**
   - Al llevar la cana a la via a 4 nudos, la masa de 3500 kg mantiene un momento angular de inercia que hace que la proa continue rotando entre 8 y 12 grados adicionales antes de estabilizar la tasa de giro a cero.

### Bloque 3: Maniobras a Vela (Para Fase Futura)

1. **Angulo Muerto (No-Go Zone):**
   - Arco de 80 a 90 grados totales centrado hacia la direccion del viento real (40 a 45 grados a cada banda de la linea del viento). El velero no puede generar sustentacion en las velas dentro de este sector.

2. **Virada por Avante (Tacking):**
   - Hacer pasar la proa a traves del viento. Se pierde velocidad de 4.5 kts a ~1.5 kts durante el cruce del angulo muerto. Si el barco no lleva suficiente velocidad previa, se queda "en facha" (atrapado en el centro del viento).

3. **Virada por Redondo (Jibing / Traslucida):**
   - Hacer pasar la popa a traves del viento. Es una maniobra de alta fuerza dinamica donde la botavara cruza de una banda a otra con gran aceleracion. Requiere cazar la vela mayor al centro antes de virar para evitar danos estructurales o zozobra.

---

### Bloque 4: Examen PNA (Prefectura Naval Argentina) y Escuelas Nauticas

1. **Maniobra Obligatoria: Hombre al Agua (MOB / Man Overboard):**
   - Inmediatamente caer a la banda donde cayo la persona (para alejar el helicoptero).
   - Ejecutar la curva de Boutakow o navegacion en "8" para aproximarse siempre por el sotavento de la victima, llegando con arrancada muerta (0 nudos) y el motor en neutro al momento del rescate.

2. **Ponerse al Pairo (Quedar en Facha):**
   - Mantener el foque/genova cazado a la banda contraria (acuartelado) y el timon a la via/arriba. El velero se estabiliza de costado al viento a 0.5 a 1 nudo de deriva, permitiendo descansar o capear una tormenta.

3. **Fondeo de Emergencia:**
   - Aproximacion proa al viento/corriente. Al perder la arrancada adelante, soltar el ancla y filar cabo/cadena a una relacion de 3:1 en calma o 5:1 / 7:1 con mal tiempo respecto a la profundidad.

### Bloque 5: "Lo Que No Sabias Que No Sabias" (Fisica Fluvial Avanzada)

1. **Diferencia entre Compas, Heading, COG, STW y SOG:**
   - **Heading (HDG):** direccion a la que apunta la proa del barco.
   - **STW (Speed Through Water):** velocidad del barco respecto al agua (medida por corredera).
   - **COG (Course Over Ground):** rumbo real del barco respecto al fondo terrestre (vector resultante de sumarle el viento y la corriente al Heading).
   - **SOG (Speed Over Ground):** velocidad real sobre el fondo (medida por GPS).

2. **Abatimiento vs. Deriva:**
   - **Abatimiento:** desplazamiento lateral provocado por el viento sobre la obra muerta (casco y mastil).
   - **Deriva:** desplazamiento vectorial producido por la corriente del rio sobre la obra viva (quilla y casco sumergido). En el rio Parana, la corriente (2 a 4 nudos) puede ser igual o mayor a la velocidad del motor del velero.

---

## Notas sobre material descartado

LLM Notebook propuso, ademas del informe, un conjunto de herramientas tecnicas que NO se adoptan por ahora:

- Reinforcement Learning (PPO, DPO) con PyTorch y Stable-Baselines3.
- Interfaz Gymnasium / Farama con WebSocket o UDP hacia Godot.
- Script `Capitania.gd` como servidor UDP.
- Reward functions matematicas multicriterio.

**Razon:** la arquitectura ya decidida con GPT-4 y Claude descarta RL con gradientes y fine-tuning. El enfoque es memoria externa + LLM local (Qwen via Ollama) + Python puro sin servidor. Si en el futuro se necesita RL, se evalua aparte.

---

*Documento de referencia. Material bruto de investigacion. Sin procesar ni sintetizar.*
*Fuente: LLM Notebook (investigacion con busqueda en internet).*
*Fecha: 2026-10-04.*
*Registrado en EXPEDIENTE/58.*
