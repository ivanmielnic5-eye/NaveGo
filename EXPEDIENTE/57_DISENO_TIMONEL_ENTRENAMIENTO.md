# DISEÑO — 2026-10-04

**Proyecto:** Timonel (agente LLM local que pilota Polaris en el simulador)
**Estado:** diseño previo a implementación. Mediciones pendientes antes de escribir código.
**Rama:** experimento-v4-admin
**Referencias externas:** consulta enviada a GPT-4 y a Claude el 2026-10-04. Respuestas recibidas.

---

## 1. Qué es este proyecto

**Timonel** es un agente Python que pilota un velero simulado llamado **Polaris** (Godot 4.7, física Jolt). Consulta a **Qwen 2.5 Coder 7B** vía Ollama local, recibe comandos JSON, y los escribe en un archivo que Godot lee. Existe también un **bridge** (`timonel_bridge.gd`) que escribe telemetría y lee comandos, y un **ground_truth_logger.gd** que graba la verdad física a 60 Hz.

**Lo que YA funciona:**
- Timonel corre, consulta a Qwen, escribe comandos.
- El bridge funciona. Godot responde a los comandos (el barco gira, avanza).
- Física del barco calibrada (masa 3500 kg, flotabilidad Hooke, drag, torque).
- Hay 378 registros de telemetría y 215 comandos de varias sesiones (26 sep). Poco corpus, pero real.

**Lo que NO existe:**
- Memoria entre corridas. Cada corrida empieza como si fuera la primera.
- Criterio de éxito registrado.
- Corpus de éxitos (el agente nunca llegó al objetivo).
- Lecciones extraídas ni reflexión.

**Conclusión del encuadre:** base funcional, aprendizaje escaso. Lo que falta es el mecanismo de acumulación.

---

## 2. El hallazgo arquitectónico (convergencia GPT-4 + Claude)

Las dos respuestas coincidieron en el punto más importante:

**Qwen no debe decidir cada comando. Debe diseñar políticas que se ejecuten sin LLM.**

Hoy Timonel consulta a Qwen cada 15 segundos. Qwen tarda ~3.2s en caliente. Eso significa ~18s por decisión. Si una corrida necesita 15 decisiones, son 48 segundos de inferencia LLM sola, sin contar física ni render.

**La solución:** que el LLM intervenga menos veces, pero en decisiones de más alto nivel.

**Antes:**
telemetria -> Qwen -> comando -> telemetria -> Qwen -> comando -> ...

**Después:**
Qwen -> genera politica -> Python/Godot ejecuta N pasos sin LLM -> telemetria -> evaluacion -> Qwen (fin de corrida)

**Impacto:** bajar de 15-30 llamadas por corrida a 1-5. Sin cambiar el modelo, sin fine-tuning, sin GPU extra.

---

## 3. La pregunta que Claude hizo y que cambió el diseño

Claude cuestionó la premisa: "¿ya midieron cuántas decisiones por corrida necesita Timonel hoy contra Godot? Esa cifra sola dice si el problema es Qwen, es Godot, o es los dos — y hoy nadie lo midió, se asumió."

Asumimos que el cuello de botella era Godot. No medimos. Y la evidencia preliminar del corpus del 26 sep muestra algo raro: 215 comandos en 389s -> un comando cada 1.8s, no cada 15s. Eso contradice el código actual (`time.sleep(15)`) y hay que aclararlo.

**Conclusión:** antes de diseñar nada, medir.

---

## 4. Comparación de las dos respuestas

### Lo que ambas dicen (señal fuerte)

1. Qwen fuera del inner loop. LLM diseña políticas, no comandos individuales.
2. Sin fine-tuning. Memoria externa, no modificación de pesos.
3. Criterio de éxito multicriterio. No solo "llegar", también seguridad, tiempo, suavidad.
4. Aprendizaje por escenarios. Distinguir aprender de tener suerte.
5. Ratchet como referencia real (ver sección 8).

### Lo que solo dice GPT-4

1. Terminología: "inference-time policy improvement", no "training". Qwen no se entrena. Se mejora la política en tiempo de inferencia.
2. Distinguir infrastructure failure de episode failure. Si Qwen devuelve JSON inválido, eso no es que el agente falló — es que la infraestructura falló. No debe contaminar métricas.
3. Promotion gates progresivos (M0-M6) para pasar de Python a Godot sin desaprender.
4. Métrica T_diverge(ε): tiempo hasta que dos simuladores divergen.

### Lo que solo dice Claude

1. Godot `--headless` antes que Python. Si el problema es el render y no el motor, headless resuelve sin reescribir física.
2. 2D directo, no 6DOF. Con viento=0 y olas=0, el roll/pitch no se excita. Modelar 3D es sobre-ingeniería para el ABC.
3. Medir antes de diseñar. Cuántas decisiones por corrida, cuánto tarda el reset, cuánto tarda Qwen real.
4. Interfaz de "proveedor de física" única. El agente no sabe si habla con NumPy, Godot o sensores reales.
5. Verificación honesta de citas. Ratchet verificado (arXiv:2605.22148). CER, ERL y AI-Houkai: no pudo verificarlos, marcados como PROPOSED.
6. Regresiones localizadas. El efecto promedio positivo de las lecciones esconde que algunas ayudan en general y perjudican en casos específicos. Medir por tipo de escenario, no solo promedio.
7. Separar lecciones ABC de lecciones condiciones-reales en el log de evidencia.

---

## 5. Decisiones tomadas

1. No hacemos fine-tuning de Qwen. Memoria externa, no cambio de pesos.
2. No hacemos RL con gradientes.
3. Qwen sale del inner loop. El LLM diseña política; la física corre sin LLM.
4. Terminología adoptada: "inference-time policy improvement" + "external experience memory" + "policy synthesis". No "training".
5. Verificar toda cita antes de apoyarse. CER, ERL y AI-Houkai quedan como PROPOSED.
6. No diseñamos hasta medir. Cuatro mediciones pendientes (sección 6).
7. Ratchet como framework base para curación automática de lecciones. Confirmado real por Claude.

---

## 6. Mediciones pendientes (antes de escribir código)

**M1 — Cuántas decisiones por corrida emite Timonel HOY.**
Del corpus del 26 sep: 215 comandos en 389s -> un comando cada 1.8s. Contradice el código actual (`time.sleep(15)`). Hay que aclarar si:
- El corpus es de una versión vieja del código.
- Los comandos se escriben varias veces por ciclo.
- O hay otro mecanismo que no conocemos.

**M2 — Cuánto tarda Godot en resetear la escena.**
Si es el cuello de botella, mantener un proceso Godot corriendo y resetear estado entre corridas puede ser mucho más rápido que reabrir.

**M3 — Cuánto tarda Qwen en condiciones reales de producción.**
Medimos 3.2s en test aislado. Falta medir en corrida larga, con contexto acumulado.

**M4 — Godot --headless funciona con la escena actual.**
Si sí, es la alternativa más simple antes de reescribir física.

**Con M1-M4 respondidas, decidimos:** Python, Godot headless, o ambos.

---

## 7. Plan de implementación tentativo (a confirmar después de las mediciones)

**Fase 0 — Mediciones.** Las 4 de arriba. Sin escribir código de producción.

**Fase 1 — Conformance (si vamos por Python).** Simulador Python 2D que replique fielmente la física de Godot para el caso ABC. Validación con secuencias de comandos fijas.

**Fase 2 — Policy loop.** Qwen genera política de navegación. Python/Godot ejecuta sin LLM. Reducción de 15-30 llamadas a 1-5 por corrida.

**Fase 3 — Memoria externa.** Ratchet-style: raw -> candidate -> validated -> retired. Evidence Log append-only. Separar lecciones ABC de lecciones condiciones-reales.

**Fase 4 — Evaluación.** Conjuntos train/validation/test congelados. Baseline vs memory-enabled. Mismos escenarios y semillas. Medir por tipo de escenario, no solo promedio.

**Fase 5 — Promotion gates.** M0 (Python nominal) -> M1 (ruido sensor) -> M2 (variación masa/drag) -> M3 (viento) -> M4 (oleaje) -> M5 (Godot) -> M6 (adversos). Solo se promociona si mantiene desempeño previo.

**Fase 6 — Producto.** Cuando funcione, evaluar empaquetado para escuelas / empresas.

---

## 8. Referencias

**Verificadas:**
- Ratchet (AWS, 2026). arXiv:2605.22148. Repo: `amazon-science/Self-Evolving-Agents-Ratchet`. Verificado por Claude.
- Voyager (NVIDIA, 2023). arXiv:2305.16291. Referencia real.
- Generative Agents (Stanford, 2023). Referencia real.
- MuJoCo Python bindings. Documentación oficial.
- Jolt Physics. GitHub oficial.
- Ollama API docs. Documentación oficial.

**PROPOSED (no verificadas):**
- Contextual Experience Replay (CER). Mencionada por GPT-4. No verificada por Claude.
- Experiential Reflective Learning (ERL). Igual.
- AI-Houkai. No verificada.

**Regla:** ninguna referencia PROPOSED se usa para tomar decisiones de diseño hasta que alguien traiga la fuente exacta.

---

## 9. Lo que NO se hace

- Fine-tuning de Qwen.
- RL con gradientes.
- Dependencias pesadas (ROS, Unreal, Unity, MuJoCo si no es necesario).
- Diseñar antes de medir.
- Citar sin verificar.
- Prometer producto comercial antes de tener el ABC aprendido.

---

## 10. Próximo paso inmediato

Antes de cualquier diseño: hacer las 4 mediciones (M1-M4).

Con eso: decidir Python vs Godot headless.

Después: diseñar con datos, no con suposiciones.

---

*Documento de diseño en curso. No es fuente autoritativa de decisión cerrada.*
*Fecha: 2026-10-04*
*Registrado en EXPEDIENTE/57*
