# Constructo por fase y preguntas pendientes

## Antes de las tablas: una corrección de estado y una hipótesis central

**"Fase 1 cerrada" hay que reformularlo.** Lo que está cerrado es una **prueba unitaria de aplicación de contrato con umbral fijo** (T=15). El constructo de discriminación de la Fase 1 sigue abierto. Además, un 100% con T fijo todavía no separa "leyó el contrato" de "memorizó el 15".

**Propuesta mía (no viene del informe):** el constructo central del proyecto podría ser **decisión condicionada por contrato**: *cuando cambia la especificación escrita en el prompt, la decisión cambia de forma apropiada, sin reentrenar*. Es lo único que un LLM aporta de forma clara frente a un árbol de decisión o un planificador clásico: un árbol no se adapta a un contrato nuevo en texto. Si la hipótesis central es otra, escribila, pero tiene que existir.

**Requisitos comunes a todas las fases:**
- **Baselines obligatorios:** una regla de 2-3 líneas, un árbol de decisión entrenado con los mismos datos, el **modelo base sin SFT** (zero-shot y few-shot) y un planificador clásico donde exista.
- **Contrafácticos de contrato:** mismo estado, contrato modificado.
- **Simetrías:** reflejar babor/estribor o rotar viento y meta debe transformar la respuesta de forma predecible.
- **Valores no vistos** en entrenamiento.
- **Lazo cerrado** donde la decisión tenga consecuencias dinámicas.

## 1. Constructo de cada fase

| Fase | Capacidad atribuida (falsable) | Éxito, distinto de imitar una regla |
|---|---|---|
| **1a. Contrato** (lo que hay hoy) | Aplica el criterio de éxito declarado (umbral T) a la distancia mostrada, **para T no vistos** | El umbral efectivo del modelo sigue a T (pendiente ≈1) en umbrales no vistos y cerca del umbral |
| **1b. 4 acciones** | Elige acción usando ≥2 variables cuando la óptima depende de su interacción, no de un umbral único | Menor arrepentimiento en lazo cerrado que la heurística y el árbol, con etiquetas de utilidad (esperanza sobre parámetros plausibles) |
| **2. Obstáculos** | Mantiene un margen de seguridad **declarado en el contrato** (S) sin perder la meta, y cambia la decisión cuando cambia S | Distancia mínima y tasa de colisión en lazo cerrado vs. una regla geométrica; para otras embarcaciones, clasificación de la situación (cruce, alcance, frente a frente) según el reglamento documentado (COLREG) |
| **3. Maniobras finas** | Elige el plan de aproximación (rumbo, velocidad objetivo, abortar/rodear) con éxito bajo perturbación de parámetros | Tasa de éxito bajo perturbación comparable a un baseline PID/MPC |
| **4. Velas** | Elige ángulo y bordada coherentes con la polar de velocidad del barco | Cercanía al óptimo de VMG calculado desde la polar, vs. fórmula cerrada |
| **5. Fondo** | Decide con margen bajo-quilla = profundidad − calado − incertidumbre del sensor | Respeta el margen aun con ruido de sensor y cambia con el calado declarado |
| **6. Olas** | Elige rumbo/velocidad que reduce exposición lateral, compensando con avance a la meta | Mejor trade-off riesgo/progreso que la regla "proa a la ola", en un modelo con procedencia |
| **7. Mar picado** | La cadena **wavelet → features numéricas → LLM** estima el estado de mar y esas features mejoran decisiones | Error acotado de las features vs. el generador, y mejora sobre el mismo pipeline con FFT/RMS simple |

## 2. Criterios de falsación

| Fase | Resultado que diría "NO aprendió esto" |
|---|---|
| **1a** | El umbral efectivo se queda en 15 cuando T cambia (memoriza); o el modelo base sin SFT ya saca ≈100% (el SFT no aporta) |
| **1b** | Un árbol entrenado con los mismos ejemplos iguala o supera al LLM, y el LLM no se adapta a un contrato nuevo en texto |
| **2** | La decisión no se mueve al cambiar S; falla en configuraciones reflejadas; más colisiones que la regla geométrica |
| **3** | El éxito colapsa con ±X% en parámetros donde el baseline no colapsa (X a fijar de antemano) |
| **4** | No hay equivarianza al rotar viento y meta juntos; errores concentrados en la zona de no-navegación; asimetría entre amuras |
| **5** | Decide sobre la lectura ruidosa sin margen; no responde al calado declarado |
| **6** | Sin equivarianza al rotar la dirección de ola y meta; indiferente a la altura de ola |
| **7** | Reemplazar wavelets por FFT/RMS da lo mismo (las wavelets no aportan) |

## 3. Bloqueantes entre fases

**Comunes a todas:**
1. Constructo escrito en ≤3 frases y criterio de falsación fijado **antes** de correr.
2. Un test donde los baselines **no** lleguen al 100% (el test puede perder).
3. Fuente de las etiquetas con procedencia o sensibilidad medida.
4. Reporte con baselines, estratos e IC, desde manifiesto.

**Específicos:**
- **Pasar a la 2:** que la 1a pase con T no vistos, que esté medido el modelo base sin SFT y que la 1b esté rediseñada en cascada (ver sección 6).
- **Pasar a la 3:** infraestructura de **lazo cerrado** con métrica de colisión; definir la división de roles entre LLM y controlador.
- **Pasar a la 4:** una **polar con procedencia documentada**. Con la física inventada actual, esta fase multiplicaría el problema 2.
- **Pasar a la 5 y 6:** un modelo de sensor (ruido) y un modelo de estabilidad/oleaje con procedencia, no reglas inventadas.
- **Pasar a la 7:** una hipótesis operacionalizable para cualquier componente nuevo (ver sección 5).

## 4. Las preguntas que no nos hacemos

1. **¿Qué aporta el LLM sobre un planificador clásico?** Sin respuesta, cada fase puede terminar mostrando que el LLM imita una regla que el código ejecuta gratis.
2. **¿Copiloto o piloto?** El objetivo declarado es asistir al capitán, pero las fases evalúan pilotaje autónomo. Un copiloto se evalúa por calidad de recomendación, **abstención** ("no sé / consulten"), costo de falsas alarmas, explicación y latencia, no por exactitud contra un oráculo.
3. **¿Qué mide la exactitud offline?** Un modelo con buena exactitud puede fallar en lazo cerrado: sus errores lo llevan a estados que no están en el dataset (cambio de distribución). Falta evaluación en rollouts.
4. **¿Cuánto rinde el modelo base sin SFT en el Run 3?** El informe no lo menciona. Si saca ≈100% sin entrenar, el SFT no explica nada.
5. **¿Qué ve realmente el copiloto real?** El prompt actual entrega distancia y desvío exactos a 0,1. Un barco real tiene estimaciones ruidosas, y el error típico de un GPS civil es del orden de metros, comparable a los umbrales de 2-3 m de la Fase 3.
6. **¿Cómo se genera la verdad en cada fase?** Si es una regla o un oráculo, el techo es esa regla u oráculo. Una justificación técnica sólida para el LLM sería **destilar un planificador por simulación lento** (cómputo y latencia vs. arrepentimiento), pero entonces la validez de las etiquetas depende del simulador, con sus parámetros inventados.
7. **¿Qué pasa con el entrenamiento secuencial?** Si cada fase reentrena el LoRA, se puede olvidar lo anterior. Hace falta una **suite de regresión** entre fases.
8. **¿Hay varianza entre semillas y curva de aprendizaje?** Sigue pendiente de las respuestas anteriores.

**Supuestos sin chequear:** (a) que la exactitud sintética se traslada a lazo cerrado; (b) que los números con un decimal en el prompt son la entrada realista; (c) que la tokenización numérica del 8B alcanza para las comparaciones finas de la Fase 3; (d) que el simulador es adecuado más allá de la Fase 1.

## 5. Lo que debería hacernos parar

- **El modelo base sin SFT iguala al SFT** en una fase: la pregunta del proyecto cambia.
- **Un árbol o regla simple iguala al LLM** en dos fases consecutivas: sin ventaja demostrable.
- **El umbral efectivo no sigue a T**: memorización.
- **Accuracy alta offline y fallo en lazo cerrado.**
- **Las etiquetas cambian con perturbaciones moderadas de parámetros**: miden supuestos, no situaciones.
- **No poder escribir el constructo de una fase en 3 frases**: no abrirla.
- **Reordenar la hoja de ruta o redefinir criterios después de ver resultados.** Está bien reordenar, pero con el criterio de salida preregistrado de antemano.
- **Penrose en la Fase 7.** Los wavelets sí tienen uso técnico establecido (análisis tiempo-frecuencia de señales de movimiento u oleaje para estimar estado de mar). No identifico en cambio un rol establecido para "Penrose". Pediría una hipótesis operacionalizable: qué señal, qué transformación, qué predicción comparable con FFT o wavelet estándar. Sin eso, la sacaría de la hoja de ruta. Y el LLM no debería leer señales crudas: las features numéricas las calcula un front-end.

## 6. Otros puntos

**Riesgos estructurales de la hoja de ruta:**
- **El orden sigue la complejidad del entorno, no la del problema de decisión.** Conviene ordenar por clase de problema: determinado por un umbral → multivariable → trade-offs → incertidumbre.
- **Cada fase tiende a repetir el patrón de la Fase 1.** "Encarar de frente", "umbral 2-3 m" y "calado" son reglas. Sin etiquetas de utilidad o contrafácticos, cada fase termina midiendo aplicación.
- **Física acumulada sobre un simulador sin validar.** Cada fase agrega parámetros inventados.
- **Las Fases 3, 6 y 7 piden tiempo real que el LLM no puede dar.** 1 nudo ≈ 0,514 m/s: a 4 nudos el barco avanza unos 2 m por segundo. Con un LLM decidiendo a ~1 Hz, un tick ya equivale a la tolerancia de 2-3 m. En esas fases el LLM no puede estar en el lazo del frenado final: elige el plan y delega a un controlador.
- **La hoja de ruta lista las 4 acciones antiguas.** ¿Incorpora el rediseño en cascada (el LLM emite consignas y un PID las ejecuta) que se discutió antes? Si no, las fases 2+ se construirían sobre recetas que ya se cuestionaron.

## Antes de avanzar a la Fase 2, el equipo tiene que resolver

**X = contar con al menos un test de Fase 1 que pueda fallar:** umbral T variable con valores no vistos, con baselines (regla, árbol, modelo base sin SFT) que **no** lleguen al 100% por construcción, y con la hipótesis central escrita. Todo lo demás depende de eso. La celda de la respuesta anterior ya genera ese banco.
