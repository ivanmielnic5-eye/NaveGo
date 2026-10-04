# INVESTIGACION EXTRA — Material de LLM Notebook — 2026-10-04

**Proyecto:** Timonel / NaveGo (agente y simulador)
**Fuente:** LLM Notebook (investigacion con busqueda en internet)
**Estado:** material de referencia. **NO adoptado en su totalidad.**

## Aviso importante

Este documento reune el material adicional que trajo LLM Notebook y que NO entra en EXPEDIENTE/58. Incluye:

- Sistema de evaluacion y rubricas de maniobras (PNA).
- Metricas cuantitativas de gobierno (SI, DER, KSM).
- Analizador de telemetria en tiempo real.
- Funcion de recompensa multicriterio.
- Integracion Godot <-> Python por WebSocket/UDP.
- Entrenamiento por Reinforcement Learning (PPO + Stable-Baselines3 + Gymnasium).

**NO TODO SE ADOPTA.** La arquitectura decidida con GPT-4 y Claude descarta explicitamente:

- Fine-tuning de Qwen.
- Reinforcement Learning con gradientes.
- Interfaz Gymnasium y servidores UDP.

El enfoque actual es: **memoria externa + LLM local (Qwen via Ollama) + Python puro sin servidor.**

**Sin embargo, el material se guarda por tres razones:**

1. Las rubricas y criterios PNA son utiles para el sistema de evaluacion (aplica a entrenamiento y a producto para escuelas).
2. El analizador de telemetria aporta ideas conceptuales utiles (deteccion de perdida de gobierno, prediccion de overshoot).
3. Si en el futuro se necesita RL o integracion WebSocket con Godot, el trabajo ya esta pensado.

**Como leer este documento:** identificar que se puede adoptar ahora, que se anota para fase futura, y que se descarta definitivamente.

---

## 1. Sistema de Evaluacion y Rubricas de Maniobras (PNA)

**Origen:** LLM Notebook propuso un sistema de evaluacion con puntaje de 0 a 100 para auditar maniobras. Combina metricas de control fisico, eficiencia espacial y seguridad operativa.

### 1.1 Metricas Cuantitativas de Gobierno

1. **Indice de Suavidad de Timon (Smoothness Index - SI):**
   SI = (1/T) * integral de |delta_punto(t)| dt
   - Penaliza las sacudidas continuas o bruscas de la cana (jittering).
   - Un timonel experimentado aplica correcciones breves y anticipadas.

2. **Diametro de Deriva (DER):**
   DER = max_t || p(t) - p_origen ||
   - En maniobras de espacio reducido (ciaboga), mide el desplazamiento total del centro de pivote.
   - Valor > 1.2 esloras (~10 metros) indica perdida de control.

3. **Margen de Seguridad Cinetica (KSM):**
   - Evalua SOG en funcion de proximidad a obstaculos.
   - Exige SOG <= 1.0 nudo cuando la distancia a un muelle o embarcacion sea < 5 metros.

### 1.2 Rubricas por Maniobra

#### A. Atraque de Costado a Muelle

| Criterio | Condicion tecnica / Tolerancia | Puntaje |
|---|---|---|
| Angulo de Insercion | Aproximacion entre 20 y 30 grados respecto a la amarra | 20 pts |
| Velocidad de Aproximacion | SOG <= 1.5 kts a 5m; SOG <= 0.8 kts al contacto | 30 pts |
| Alineacion Final | Parallelismo de la crujia con el muelle (delta_theta <= 5 grados) | 25 pts |
| Uso del Prop Walk | Toque breve de reversa para apoyar la popa sin dar arrancada atras | 25 pts |
| **Falta Eliminatoria** | Contacto a SOG > 1.5 kts (colision estructural) | **0 pts / Reprobado** |

#### B. Ciaboga (360 grados en Espacio Reducido)

| Criterio | Condicion tecnica / Tolerancia | Puntaje |
|---|---|---|
| Encierro Geometrico | Mantener el pivote dentro del radio de 10m (1.2 esloras) | 40 pts |
| Tecnica de Impulsos | Mantenimiento del timon a la banda + toques alternados de acelerador | 30 pts |
| Tiempo Eficiente | Completar el giro completo de 360 grados entre 20 y 30 segundos | 30 pts |

#### C. Hombre al Agua (MOB - Estandar PNA)

| Criterio | Condicion tecnica / Tolerancia | Puntaje |
|---|---|---|
| Reaccion Inmediata | Caida inicial de la cana hacia la misma banda del naufrago | 20 pts |
| Linea de Sotavento | Aproximacion final proa al viento/corriente desde sotavento | 40 pts |
| Llegada en Calma | Detencion completa (SOG = 0.0 kts) a menos de 2m de la persona | 40 pts |
| **Falta Eliminatoria** | Helice acoplada (throttle > 0) a menos de 3m de la persona | **0 pts / Reprobado** |

---

## 2. Analizador de Telemetria en Tiempo Real (conceptos)

**Origen:** LLM Notebook propuso un modulo (`telemetry_analyzer.py`) que procesa el stream de telemetria a 10 Hz y emite diagnosticos instantaneos.

**Estado:** conceptos adoptables. Codigo completo no aplica (usa WebSocket/UDP).

### 2.1 Estructura del Stream de Telemetria

10 variables por ciclo (a 10 Hz):

- SOG (velocidad sobre el fondo, nudos).
- STW (velocidad sobre el agua, nudos).
- HDG (heading, direccion de la proa).
- COG (course over ground, direccion real del movimiento).
- Deriva (diferencia COG - HDG por corriente/viento).
- Angulo de timon.
- Delta X, Delta Y (distancia a la meta).
- Viento: velocidad y direccion.

### 2.2 Diagnosticos Cinematicos Utiles

1. **Deteccion de Perdida de Gobierno (STW < 1.0 kts):**
   - Por debajo de 1 nudo de velocidad sobre el agua, el timon pierde flujo laminar y deja de responder.
   - Alerta: "Timon ineficaz por falta de arrancada".
   **UTIL PARA ADOPTAR:** nuestro simulador deberia modelar esta perdida de gobierno.

2. **Magnitud del Prop Walk en Reversa:**
   - Cuando throttle < -0.3 y SOG < 0.5 kts, la helice genera fuerza lateral no axial antes de mover el barco atras.
   - Se monitorea la aceleracion angular rapida de la proa.
   **UTIL PARA ADOPTAR:** nuestro simulador deberia modelar el prop walk.

3. **Prediccion de Overshoot Inercial:**
   - Calculando la velocidad rotacional (psi_punto = DeltaHDG / Deltat), el sistema predice el angulo final donde se detendra el giro.
   - Formula: HDG_estimado = HDG_t + psi_punto * tau_inercia
   **UTIL PARA ADOPTAR:** ya lo tenemos validado (~10 grados), se puede usar para anticipar.

4. **Alerta de Invasión de Zona de Seguridad:**
   - Si la distancia al muelle o victima es < 5m y SOG > 1.5 kts, alerta de riesgo inminente de impacto.
   **UTIL PARA ADOPTAR:** util para el sistema de evaluacion.

---

## 3. Funcion de Recompensa Multicriterio (conceptos)

**Origen:** LLM Notebook propuso una funcion de recompensa matematica para RL.

**Estado:** NO aplica a nuestro enfoque (no hacemos RL). Pero los CONCEPTOS son utiles para el sistema de evaluacion.

### 3.1 Estructura General

Recompensa total = R_Progreso + R_Seguridad - P_Inercia_y_Control

### 3.2 Componentes por Maniobra (conceptos)

**Atraque de Muelle:**
- Velocidad segura: si esta a menos de 5m del muelle y SOG entre 0.5 y 1.0 kts -> bonificacion.
- Si SOG > 1.5 kts -> penalizacion por exceso de velocidad.
- Exito: distancia < 1.5m y SOG <= 1.0 nudo.
- Falta grave: impacto contra el muelle a SOG > 1.2 kts.

**Ciaboga (360 grados en espacio reducido):**
- Suma puntos por cada radian de rotacion de la proa.
- Penaliza si el barco deriva lateralmente fuera de un radio de 1.2 esloras (~10m).

**Hombre al Agua (MOB):**
- Llegada en calma: detenerse a SOG < 0.5 nudos junto a la victima.
- Seguridad de helice: penalizar si el motor permanece acoplado a menos de 3m del naufrago.

**Penalizacion por Suavidad de Gobierno:**
- Restar una fraccion proporcional a la variacion de los comandos entre pasos consecutivos.
- Evita que el agente sacuda el timon o el acelerador de forma erratica.

### 3.3 Como se conecta con nuestro enfoque

**NO vamos a usar la formula matematica como recompensa de RL.**

**SI vamos a usar los criterios como rúbrica de evaluacion** de las maniobras ejecutadas por el agente. Porque:

- Evaluan si la maniobra es "buena" segun criterios nauticos.
- Aplican a entrenamiento (saber si el agente mejora) y a producto (evaluar alumnos de escuela).
- Son verificables con telemetria.

---

## 4. Integracion Godot <-> Python por WebSocket / UDP

**Origen:** LLM Notebook propuso conectar Godot 4.7 (servidor `Capitania.gd`) con Python (cliente `navego_gym_env.py`) por UDP en el puerto 4242.

**Estado:** DESCARTADO para entrenamiento. Anotado para fase futura (demos, presentacion visual).

### 4.1 Que proponia

- Canal UDP 127.0.0.1:4242.
- Frecuencia: comandos a 10 Hz, fisicas a 60 Hz con sub-stepping.
- Serializacion JSON bidireccional.
- Godot retorna telemetria de 10 variables.
- Python envia comandos [throttle, rudder].

### 4.2 Por que se descarta

1. **No es necesario.** El simulador Python es equivalente a Godot en el canal bridge. No necesitamos Godot para entrenar.
2. **Satura la maquina.** Godot + Qwen + Python juntos cuelgan la mini PC (probado).
3. **Agrega complejidad.** Servidor UDP, GDScript del lado de Godot, sincronizacion de paquetes.
4. **No aporta al ABC.** El agente aprende lo mismo en Python puro.

### 4.3 Cuando podria ser util

- **Demos a escuelas.** Mostrar visualmente al agente navegando en Godot.
- **Presentaciones.** Video de marketing.
- **Validacion visual.** Cuando el agente este entrenado, correr una corrida en Godot para ver que se ve bien.

**No descartado para siempre. Solo fuera de la fase de entrenamiento.**

---

## 5. Entrenamiento por Reinforcement Learning (PPO + Gymnasium)

**Origen:** LLM Notebook propuso un pipeline completo de RL:

1. **Clonacion de Comportamiento (Behavioral Cloning)** para pre-entrenar la red.
2. **PPO (Proximal Policy Optimization)** con Stable-Baselines3.
3. **Domain Randomization** para robustez.
4. **Metricas de convergencia** en TensorBoard.

**Estado:** DESCARTADO en esta fase.

### 5.1 Por que se descarta

1. **Ya decidimos con GPT-4 y Claude:** no RL, no fine-tuning, no gradientes.
2. **No tenemos GPU.** Entrenar PPO requiere hardware dedicado.
3. **No hay dataset.** Empezariamos con 0 episodios.
4. **La arquitectura es otra.** Memoria externa + LLM local, no red neuronal entrenada.
5. **Riesgo de sobre-ingenieria.** Meter RL agrega meses al proyecto.

### 5.2 El enfoque que SI usamos

- **LLM local (Qwen via Ollama)** que decide los comandos.
- **Memoria externa** que acumula experiencia entre corridas.
- **Recetas de maniobras** disenadas a mano, ejecutadas por el agente.
- **Sin gradientes, sin RL, sin PyTorch.**

Si en el futuro el LLM local no alcanza, RL queda como alternativa a evaluar. Pero no ahora.

---

## 6. Que se Adopta y Que No — Resumen Ejecutivo

### Adoptar

- **Rubricas PNA de evaluacion** (seccion 1.2): criterios de atraque, ciaboga y MOB. Aplicables a entrenamiento y a producto.
- **Metricas cuantitativas** (seccion 1.1): Indice de Suavidad, Diametro de Deriva, Margen de Seguridad Cinetica.
- **Conceptos del analizador** (seccion 2.2): perdida de gobierno bajo 1 kt, prop walk en reversa, prediccion de overshoot, alerta de zona de seguridad.
- **Criterios de la funcion de recompensa** (seccion 3.2) como rubrica de evaluacion (no como recompensa de RL).

### Anotar para fase futura

- **Integracion Godot <-> Python por WebSocket/UDP** (seccion 4). Para demos y presentacion visual.
- **Entrenamiento por RL** (seccion 5). Si el LLM local no alcanza en alguna fase.

### Descartar (definitivo)

- **Codigo completo de PPO con Stable-Baselines3.** No va con nuestra arquitectura.
- **Interfaz Gymnasium.** No aplica.
- **Serializacion HDF5 / Parquet para datasets.** No aplica.
- **Scripts `Capitania.gd` como servidor UDP.** No aplica al entrenamiento.

---

## 7. Proximo paso con este material

1. **Modelar en `simulador_polaris.py`:**
   - Perdida de gobierno bajo 1.0 kt.
   - Prop walk en reversa.
   - Radio de giro (verificar 12-20m).

2. **Escribir recetas de maniobras** (`recetas_navegacion.py` en `timonel/`):
   - Basadas en las rubricas PNA y los datos de EXPEDIENTE/58.
   - Formato simple: lista de `(timon, avance, duracion_ms)`.
   - Sin dependencias de Gymnasium ni Stable-Baselines3.

3. **Sistema de evaluacion automatica:**
   - Basado en las rubricas PNA.
   - Se corre al final de cada corrida del agente.
   - Reporta puntaje y penalizaciones.
   - Guarda en JSON.

---

*Documento de referencia. Material extra de LLM Notebook. NO adoptado en su totalidad.*
*Fuente: LLM Notebook (investigacion con busqueda en internet).*
*Fecha: 2026-10-04.*
*Registrado en EXPEDIENTE/59.*
