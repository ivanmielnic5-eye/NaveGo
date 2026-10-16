# FICHA P37 — Beneteau First Class 8 HIL Simulator

**Fecha:** 2026-10-16
**Estado:** BORRADOR. Fuera del expediente.
**Fuente:** resumen de tercero sobre el paper MDPI 2023, más análisis de Luna y otra IA. SIN verificar contra el PDF original.
**Advertencia:** los datos citados provienen de resúmenes, no del PDF. Antes de citar formalmente, verificar.

---

## 1. Referencia

**Título probable:** A Hardware-in-the-Loop Simulator to Optimize Autonomous Sailboat Performance in Real Ocean Conditions.
**Revista:** Journal of Marine Science and Engineering (MDPI), 2023.
**URL:** https://www.mdpi.com/2077-1312/11/6/1104

---

## 2. Qué modela

Simulador HIL para velero autónomo. El algoritmo corre en el microcontrolador real, la PC simula el entorno.

**Dos embarcaciones distintas** (aclaración importante):
- **Beneteau First Class 8 (~8 m):** el modelo dinámico de 6 grados de libertad.
- **SeaLeon (2.4 m):** el velero autónomo donde corre el piloto embebido.
- **No son la misma embarcación.** El modelo es del Beneteau; el piloto es del SeaLeon.

**Arquitectura:**
- Microcontrolador SAMD20-J a bordo, corre el piloto.
- PC con Simulink procesa dinámica y ambiente.
- Sensores emulados por NMEA-0183 (GPS RMC, anemo MWV, compás I2C).

**Física — 6 grados de libertad:**
- Casco y quilla: matriz de fuerzas de canal de remolque (5 variables: velocidad, escora, cabeceo, deriva, desplazamiento).
- Olas: solver Nemoh, fuerzas de Froude-Krylov y masa añadida.
- Velas: curvas ORC + método Masuyama.
- Timón: teoría de perfiles alares.

---

## 3. Hallazgos de control (aplicables a Timonel)

### 3.1 Viento real vs aparente
- Con viento aparente: no validó el 2do waypoint en 1823 s.
- Con viento real: validó con amplio margen.
- **NO es regla universal.** Es un hallazgo del paper para su controlador y condiciones.
- Pregunta NAVEGO: ¿qué viento usa Timonel? ¿real, aparente, o estimado?

### 3.2 Frecuencia de actualización de rumbo
- Demasiado frecuente → viradas continuas → pérdida de velocidad.
- Óptimo del paper: 155 s en ceñida / 60 s general.
- **NO copiar esos valores.** Medir los propios.
- Pregunta NAVEGO: ¿cada cuánto recalcula rumbo Timonel?

### 3.3 Zona muerta
- Definida como ±45° respecto a la dirección del viento.
- Si el rumbo directo cae ahí, desfasa para navegar al borde y hacer tacking.
- Pregunta NAVEGO: ¿Timonel gestiona dead zone?

### 3.4 Validación de waypoint
- Radio 25 m, 5 lecturas GPS consecutivas.
- **NO copiar parámetros.** Sí la idea: llegada como evento medible.
- Pregunta NAVEGO: ¿validación por persistencia o por instante?

### 3.5 Frecuencia del compás
- Óptimo del paper: 1.0 s. A 4-5 s: oscilaciones.
- Pregunta NAVEGO: ¿cómo obtiene heading Timonel?

### 3.6 Viento de popa
- Desfase a 140° del viento para navegar a largo con trasluchadas.

### 3.7 VMG (Velocity Made Good)
- Mide velocidad útil en dirección de navegación.
- Pregunta NAVEGO: ¿medimos VMG o solo SOG?

---

## 4. Las cuatro variables que no hay que confundir

Del análisis de los resúmenes. Separan mecanismos hoy mezclados:

| Variable | Qué se investiga |
|---|---|
| **Frecuencia de sensores** | ¿Cada cuánto se actualizan rumbo, viento, posición? |
| **Frecuencia de decisión** | ¿Cada cuánto Timonel recalcula estrategia? |
| **Duración de la orden** | ¿Cuánto tiempo se mantiene una acción antes de reevaluar? |
| **Frecuencia de GNSS** | ¿Qué precisión se pierde al reducir actualizaciones? |

**Son mecanismos distintos.** No se pueden tratar como una sola "frecuencia".

---

## 5. Separación mundo físico / mundo observado

El paper mantiene dos mundos distintos:
- **Mundo físico:** estado real del barco (ground truth).
- **Mundo observado:** lo que el controlador recibe vía sensores.

**Aplicación NAVEGO:** preservar esa separación. El ground truth evalúa, no alimenta al controlador. Habilita probar fallos GNSS, ruido de brújula, errores de viento.

---

## 6. Lo que NO está en los resúmenes

- Coeficientes numéricos del casco.
- Curvas ORC concretas.
- Dataset de Nemoh.
- Ecuaciones explícitas.
- Métricas de error contra la embarcación real.

**Sin esto, el paper es referencia de metodología, no de física.**

---

## 7. Aplicabilidad a NAVEGO

| Elemento | Aplicable | Cómo |
|---|---|---|
| Decisiones de control (viento, dead zone, frecuencias) | Sí | Revisar Timonel |
| Validación de waypoint por persistencia | Sí | Revisar Timonel |
| VMG como métrica | Sí | Agregar al benchmark |
| Separación ground truth / observado | Sí | Ya está en el contrato de datos |
| Arquitectura HIL (microcontrolador) | No aplica | NAVEGO usa Python+Godot |
| Coeficientes del Beneteau | No disponible | Requeriría el PDF |
| Modelo 6-DOF con Nemoh | No a corto plazo | Proyecto de ingeniería naval |

---

## 8. Próximos pasos

1. Inspeccionar código de Timonel contra las preguntas de la sección 3.
2. Verificar cómo se coordinan hoy: ciclo de decisión, bridge, duración de órdenes.
3. Diseñar E2: efecto de la frecuencia de decisión sobre trayectoria.
4. Si el PDF completo aparece, extraer coeficientes.

**Principio rector:** no copiar resultados del SeaLeon. Reproducir su rigor experimental.


---

## 10. Estado actual de Timonel frente al paper

Inspección del código activo (2026-10-16). Responde las preguntas de la sección 3.

| Pregunta del paper | Estado en Timonel | Evidencia |
|---|---|---|
| ¿Usa viento real, aparente o estimado? | **No usa viento en control activo** | timonel.py:107-108 lee aws/awa solo en consultar_dsh(), que no se invoca |
| ¿Cada cuánto recalcula rumbo? | **3 s fijo, hardcodeado** | timonel.py:24 INTERVALO_S=3.0 |
| ¿Cuánto dura una orden? | **1500 ms fijo, hardcodeado** | timonel.py:185-186 |
| ¿Tiene zona muerta? | **No** | timonel.py:88 solo tiene umbral de 45° para avanzar/no avanzar |
| ¿Tiene tacking? | **No** | Sin referencias en el código activo |
| ¿Validación de waypoint? | **Instántanea** | timonel.py:75 dist<10 → return, sin persistencia |
| ¿Usa VMG? | **No** | Métrica no calculada |

### Lo que esto significa

Timonel hoy navega como embarcación a motor: rumbo directo a la meta, avance si alineado, freno en zona de llegada. No usa viento, no hace bordos, no gestiona zona muerta.

Es exactamente el alcance de la Fase 1 del curriculum (ABC de conducción). El paper describe un piloto de Fase 2+ (navegación a vela).

### Lecciones del paper que aplican hoy

- **Frecuencia de decisión.** Hoy fija en 3 s. Vale la pena experimentar con otros valores.
- **Validación de llegada.** Hoy instántanea. Persistencia (5 lecturas consecutivas) es un cambio de una línea.

### Lecciones que requieren Fase 2

- Viento real vs aparente.
- Zona muerta y tacking.
- VMG.

Esas quedan registradas para cuando Timonel navegue a vela.

---

## 9. Referencias cruzadas

- P37 en EXPEDIENTE/PENDIENTES.md.
- contraste_cobertura_python_godot_2026-10-15.md.
- R-23 (pendiente de formalizar).

---

## 11. Material recibido 2026-10-16 (tercero, sin verificar)

### 11.1 Aplicable hoy (control)

**Event-driven turning (principio de control).**
Un temporizador rígido de decisión de rumbo puede costar hasta 300 m extra si el barco sale de la dead zone entre ciclos. Solución: doble gatillo — timer (evita viradas excesivas) + evento (corrige al cruzar límite).

**Viento real vs aparente — causa de la diferencia.**
El viento aparente causa oscilaciones porque el movimiento del barco contamina la lectura. El real no. Refuerza la sección 3.1 con el porqué.

**Sistemas de coordenadas.**
El paper usa NED (North-East-Down). NAVEGO usa Y-up + Z-forward. No es error, pero debe declararse en el contrato de datos para comparaciones futuras.

### 11.2 Aplicable en el mediano plazo (corrientes y vientos)

**Modelado de olas no estacionarias.**
Coeficientes de masa añadida y amortiguamiento obtenidos con Nemoh (solver de teoría de potencial open source). Fuerza de excitación de Froude-Krylov por integración de presión sobre el casco. Para tiempo real se omite el efecto de memoria.
- **Aplicación futura a NAVEGO:** cuando incorporemos oleaje realista más allá de las 4 olas de Gerstner.

**Perfil de ola Airy simplificado.**
Altura pico a cresta 0.3 m, período 3.5 s. Alternativa a Gerstner.
- **Aplicación futura:** cuando queramos comparar modelos de ola.

**Corrientes marinas por interpolación espacial.**
Promedio ponderado de los dos puntos de la base oceanográfica más cercanos al barco. Modifica la SOG (velocidad sobre el fondo).
- **Aplicación futura:** cuando NAVEGO tenga escenarios con corrientes.

**Viento real desde malla geográfica.**
Interpolación espacial y temporal en cada paso de simulación. Genera campo de viento real en la posición del barco.
- **Aplicación futura:** cuando queramos escenarios de viento con variación espacial (hoy NAVEGO tiene viento constante o variable por tiempo, no por posición).

**Timestep 0.1 s.**
NAVEGO corre a 60 Hz (0.0167 s), resolución mejor. No copiamos, pero el paper valida que 0.1 s es suficiente para dinámica de olas.

### 11.3 No aplicable a NAVEGO (arquitectura HIL del paper)

- **NMEA-0183 (RMC, MWV), SAMD20-J, USB-to-TTL.** No usamos microcontrolador embebido ni emulación NMEA.
- **Simulink.** NAVEGO usa Python + Godot.

### 11.4 Referencia

**Zona muerta ±45° y navegación al largo a 140°.**
Sector de no-navegación respecto a la dirección del viento. Si la derrota directa cae dentro, se aplica offset a la orilla de la zona y se navega en ceñida con bordos. Si la derrota pide viento de popa, offset a 140° para navegar al largo con trasluchadas.

**Temporizador de rumbo en ceñida: 155 s óptimo.**
Balance entre pérdida de velocidad por virada y beneficio de aprovechar borneos.
- **No copiar el valor.** Medirlo para Polaris cuando llegue Fase 2.

### 11.5 Advertencia

Material de resumen de tercero (mismo canal que antes citó navego_gym_env.py, que no existe). Tratar como ideas sugeridas, no como fuente verificada. **No citar hasta ver el PDF original.**
