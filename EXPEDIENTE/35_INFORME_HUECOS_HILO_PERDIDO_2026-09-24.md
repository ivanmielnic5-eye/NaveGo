# HUECOS DEL HILO PERDIDO — 24 sep 2026

**Motivo:** El hilo del 24/09 se llenó y no se hizo informe de cierre.
**Verificación:** Se revisó el sistema actual. Lo guardado está intacto.
**Resultado:** Faltan 5 piezas específicas que estaban en la conversación
pero nunca se volcaron a archivos.

---

## Contexto

El 24 de septiembre se trabajó intensamente en el pipeline GNSS:
Etapa 0 (viento), Etapa 1 (ground truth logger), Etapa 2 (GNSS simulator).
Todo eso quedó guardado en `docs/gnss/` y se verificó intacto.

Lo que NO se guardó son 5 piezas conversacionales que aparecieron
sobre el final del hilo y en el hilo siguiente. Esta lista las documenta
para que no se pierdan.

---

## Hueco 1 — Las 5 hipótesis GNSS que derivó DSH

DSH leyó `DIARIO.md`, `02_Contrato.md`, `03_scenario.json` y las primeras
líneas del `gnss_simulado.jsonl`. Derivó 5 hipótesis falsables:

### H1 — Accuracy constante en 4.5
Observación: todos los 62 fixes tienen `accuracy = 4.5`.
Es un valor fijo (`sigma_m * 1.5 = 3.0 * 1.5`), no derivado del ruido.
Predicción: si calculamos la desviación real del ruido aplicado, no coincide
con 4.5 en cada fix.
Criterio de refutación: si la accuracy varía fix a fix, la hipótesis se refuta.

### H2 — Heading ruidoso post-corte
Observación: el heading en los fixes después del corte (fix 31 en adelante)
muestra valores como 171.000046245753, siempre iguales.
Predicción: el heading post-corte se congela en un valor único.
Criterio de refutación: si el heading varía entre fixes post-corte, se refuta.
**Nota:** esta hipótesis fue marcada por el hilo como "refutada con hallazgo
mejor" — el heading congelado es coherente con trayectoria recta, pero revela
que el simulador no modela el comportamiento real de un GPS durante un corte
(debería estimar heading con la última velocidad conocida).

### H3 — Latencia pura (receivedAt - measuredAt = 300 ms)
Observación: cada fix tiene `receivedAt = measuredAt + 300`.
Predicción: la diferencia es exactamente 300 ms en los 62 fixes.
Criterio de refutación: si algún fix tiene una diferencia distinta, se refuta.

### H4 — Distancia perpendicular ≈ sigma
Observación: la trayectoria del ground truth es casi recta
(`pos_y ≈ -2.43` constante, sd 0.19).
Predicción: la distancia perpendicular de los fixes a la recta inicial
debería ser aproximadamente sigma = 3.0 metros.
Criterio de refutación: si la distancia perpendicular media es muy distinta
de 3.0 m, el ruido no está bien calibrado.

### H5 — 0 o 1 spike en 62 fixes
Observación: la configuración tiene `probability: 0.01`.
Predicción: en 62 fixes, se espera 0 o 1 spike (62 × 0.01 = 0.62).
Criterio de refutación: si hay 2 o más spikes, la probabilidad no coincide.
**Nota:** el fix 25 es el spike detectado (lat=-31.646815, salto de ~150 m).

---

## Hueco 2 — La verificación de esas 5 hipótesis

El último mensaje del hilo perdido le pedía a DSH que verificara las 5
hipótesis contra `gnss_simulado.jsonl`, reportando CONFIRMADA / REFUTADA /
INCIERTA con el dato exacto de cada una.

**No sabemos si DSH llegó a ejecutar la verificación.**

Estado actual del sistema: solo se sabe que H-2026-0003 está marcada como
CONFIRMADA con la evidencia:
- DSH leyó 4 archivos y generó 5 hipótesis falsables no triviales.
- Detectó que CONTRATO_GNSS.md no existía y usó 02_Contrato.md.
- Las hipótesis H1 y H3 identifican decisiones de diseño reales.
- Las hipótesis H2, H4 y H5 son verificables con el log actual.

**Acción recomendada:** volver a correr la verificación con DSH y guardar
el resultado. Este es un experimento pendiente de H-2026-0003.

---

## Hueco 3 — Regla "un solo escritor por worktree"

En la conversación con GPT-4 se acordó esta regla:

> Un solo escritor por worktree. Múltiples agentes pueden existir en
> paralelo, pero nunca sobre el mismo checkout.

Origen: el incidente del 20/09, donde dos chats tocaron el mismo `App.tsx`
sin coordinación y produjeron commits destructivos.

**Estado actual:** no está escrita en ningún archivo de gobernanza.
Ni en `AGENTS.md`, ni en `.logos/MANIFEST.json`, ni en `START_HERE.md`.

**Acción recomendada:** guardarla como decisión congelada (D-2026-0007).

---

## Hueco 4 — Test de regresión del incidente 20/09

Se propuso convertir el incidente del 20/09 en una prueba automática:
que el sistema detecte solo si dos agentes intentan pisarse en el mismo
worktree.

**Estado actual:** no implementado. Ni como script ni como regla mecánica.

**Acción recomendada:** escribir como hipótesis de diseño (H-2026-0014),
con criterio de falsación concreto.

---

## Hueco 5 — DSH operando el velero: offline vs tiempo real

Discusión del 25/09 sobre cómo aprovechar a DSH para operar el velero
en Godot (ponerle nombre al velero, que DSH decida cómo gobernarlo).

Dos formas posibles identificadas:

**Forma A (offline):** DSH genera un plan de navegación completo ANTES
de la corrida (secuencia de comandos de timón para todo el recorrido).
Godot lee ese plan y lo ejecuta. DSH no está presente durante la corrida.

**Forma B (tiempo real):** DSH recibe telemetría del velero y emite
comandos segundo a segundo. Requiere canal bidireccional que hoy no existe.

**Estado actual:** Forma A es viable. Forma B queda como hipótesis futura.
No hay decisión tomada ni hipótesis escrita.

**Acción recomendada:** escribir como hipótesis de diseño (H-2026-0015)
y proponer nombre al velero comandado por IA.

---

## Recomendación de cierre

| Hueco | Acción |
|---|---|
| 1 — 5 hipótesis GNSS de DSH | Guardar como H-2026-0014 a H-2026-0018 |
| 2 — Verificación de esas hipótesis | Correr DSH con el prompt de verificación |
| 3 — Regla "un solo escritor" | Guardar como D-2026-0007 |
| 4 — Test de regresión del incidente | Guardar como H-2026-0019 |
| 5 — DSH operando el velero | Guardar como H-2026-0020 |

**Prioridad:** huecos 1 y 2 son verificables en 10 minutos. Huecos 3 y 4
son decisiones. Hueco 5 es planificación.

---

*Generado: 2026-09-25*
*Por: DeepSeek (chat) bajo dirección del Director*
