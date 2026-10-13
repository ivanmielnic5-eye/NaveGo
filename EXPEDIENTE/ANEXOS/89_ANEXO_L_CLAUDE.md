# ANEXO L — CLAUDE / DISENO DE A3 ETAPA 1

**Fecha:** 2026-10-13
**Origen:** respuesta a la consulta del 2026-10-13 (diseno de A3 etapa 1).
**Contenido:** respuesta completa de Claude, sin resumir.

---

# Diseño de A3 etapa 1

## 0. Mi lectura de 0b (difiero en parte)

**Acepto el veredicto formal.** B2 era compuerta preregistrada y falla, así que se activa la regla: la etapa 1 entrena con `v_max` variable y placebo.

**Difiero en la interpretación.** "No compara v contra v_max, usa la magnitud de v" no encaja con tus propios datos:
- **B1 = 1,000:** sin cláusula, ignora v. Descarta "v alta → cautela siempre".
- **B3 = 0,96:** mismo d, T y v, cambia solo `v_max`, y la decisión cambia. Si solo usara la magnitud de v, no habría cambios.

Lo compatible es **lectura parcial con sesgo hacia `ir_a` cuando v es moderada**, no ausencia de comparación. Para el diseño de A3 importa porque el problema es el sesgo, no la capacidad.

**Cautela estadística:** si B2 tuvo n=40, 35/40 tiene Wilson [0,74; 0,95], que solapa la compuerta de 0,90. Formalmente falla; la magnitud del fallo es incierta.

**Datos que me faltan:** n de B2; si el 48/50 de B3 son pares o contextos; si B3 incluye casos contra-prior.

**Paso 0c, antes de generar nada (sin datos nuevos):**
- Desglosar los errores de B2 por v, v_max y margen |v−v_max|. Errores en margen chico son frontera; errores con margen grande son el sesgo.
- Re-puntuar 0b con el orden de acciones invertido.
- Re-puntuar con los checkpoints 50/100/150/154 (descriptivo).

Esto decide qué cobertura necesita el entrenamiento de A3.

## 1. LLM-A3 (entrenamiento y banco)

**Qué va:**

| Split | Contenido | Tamaño |
|---|---|---|
| train | F1 (T como en A2: 11 valores): 340 sin v + **60 placebo** (v visible, sin cláusula). F2: 4 cuadrantes × 200, con v_max ∈ {0,3; 0,5; 0,8; 1,2; 2,0; 3,0}, y ≥40% de Q1 como **contra-prior** (d<T, v≥1,0 kn, v≤v_max). Formulaciones F-train y F-dev | 1200 |
| val | Misma composición, solo para ajustar | 300 |
| test paramétrico | F1 (T interp/extrap como en A2) 300; F2 con combinaciones (T, v_max) retenidas, v_max ∈ {0,4; 1,0; 1,6; 2,5}, 300 | 600 |
| test contra-prior | Combinaciones retenidas | 150 |
| test placebo | v visible sin cláusula | 100 |
| test pares | Mismo d, T, v; cambia solo v_max | 100 pares |
| test extrap v_max | v_max ∈ {0,15; 5,0} | 100 |

**Auditoría de atajos en el banco:** dentro de d<T, el AUC de `v` solo y de `v_max` solo debe estar en [0,45; 0,55], y el AUC de (v−v_max) debe ser alto. Así, la magnitud de v no predice la etiqueta.

**Criterios preregistrados:**
- **Compuertas:** las de A2 (masking verificado, ajuste en train, señal en val, generación coincide).
- **F1 y F2 paramétricos:** ≥0,99 con límite inferior Wilson ≥0,97 (n=300).
- **Contra-prior:** ≥0,97 (≥146/150; LB ≈0,933).
- **Placebo:** ≥0,99.
- **Pares:** ≥0,97 con cambio de decisión correcto.
- **Invarianza al orden:** ≥99% de decisiones idénticas.
- **Falso `terminar`:** reportar la cota (0 en 300 acota a ≈1%).
- **Extrap v_max:** se reporta, no condiciona.

**Costo:** entrenamiento ≈2× el de A2 si mantienen épocas y batch (A2 = 616 ejemplos × 2 épocas = 154 steps, consistente con batch 8; inferencia mía). Evaluación: ~25-40 min por modelo y por orden de acciones, extrapolando tu cifra de 25 min (no sé el n de esa evaluación).

## 2. F-held

**Qué va (`heldout/`):** `brief_autor.md`, `contratos_heldout.jsonl`, `gold_spec.jsonl`, `seal.txt`, `anotacion_ciega.csv`.

**Construcción:** 300 contextos por familia (600). Un autor independiente (una instancia de LLM bajo consigna, no el Director) escribe **60 plantillas por familia** con marcadores ({T}, {unidad}, {v_max}). Los parámetros se inyectan por programa (combinaciones retenidas, conversiones kn↔m/s y m↔mn con margen mayor al redondeo), así que **la etiqueta es correcta por construcción**. Más **60 textos libres por familia**, con anotación ciega doble (una persona y un modelo grande vía API); los desacuerdos se excluyen por regla preregistrada, antes de sellar.

**Criterios de validez:** acuerdo de anotación ≥98% en los textos libres; distancia de edición mínima respecto de F-train y F-dev (verificación automática); sello con SHA256 y tag de git **antes** de que empiece P-text.

**Costo:** humano 2-3 h de revisión (estimación mía); datos 600; GPU solo puntuar.

## 3. P-text, P-struct y árbol

**Archivos:** `engine/policy_engine.py` (P-struct, esquema declarativo) + tests; `ptext/` con `ptext_A.py`, `ptext_B.py`, `dev_log.md`, `ptext_frozen.py` + hash; `tree/tree.py` (features = parámetros del contrato + estado, CPU).

**Procedimiento:** el de mi respuesta anterior (autor asistente de código, dos implementaciones, mejor en F-dev, una ronda de red team, parada al llegar a ≥99% en F-dev o al agotar K=5 rondas / tope de horas preregistrado). **Equidad de exposición:** P-text ve F-train y F-dev; LLM-A3 entrena con F-train y F-dev.

**Criterios:**
- **H1b-interfaz:** Δ = exactitud(LLM-A3) − exactitud(P-text) en F-held ≥ 10 puntos, McNemar exacto p<0,01. Con 600 pares, la potencia para 10 puntos alcanza si la proporción de discordantes q ≤ ~0,5; para 5 puntos, solo si q ≤ ~0,13.
- **No inferioridad vs. P-struct** en formulación estándar: error ≤2 puntos (n=600, suficiente).
- **Versión sin bugs de P-text:** se reporta, no es primaria.

**Costo:** 2-4 h de supervisión humana (estimación mía), GPU cero.

## 4. Preregistro

**Archivos:** `prereg/prereg_A3_e1.md` y `prereg_A3_e1.json` (constantes que el script de veredicto lee), commiteados **antes de entrenar**, con hashes de bancos y plantillas.

**Contenido:** hipótesis, brazos, criterios de las secciones 1-3, y tabla de decisión:
- **Falla H1a (cualquier estrato):** diagnóstico; se permite **una** iteración de datos (A3.1) antes de abrir F-held, con **semillas de test nuevas**.
- **Pasa H1a:** se abre F-held y se evalúa H1b.
- **H1b:** Δ ≥10 con p<0,01 → "ventaja de interfaz, relativa a esta distribución de formulaciones". Si no, no apoyada, con IC.

Más un registro de desvíos.

## 5. Ejecución

1. Prereg + bancos + sellado de F-held.
2. Paso 0c.
3. En paralelo: P-text (CPU/humano) y entrenamiento de LLM-A3 (1 semilla).
4. Compuertas y cribado en val y test paramétrico. **No se abre F-held** hasta que P-text y LLM-A3 estén congelados con hash.
5. Se abre F-held y se evalúan P-struct, P-text, árbol, A2 congelado y LLM-A3.
6. Veredicto por familia. Si pasa: 2 semillas más.
7. Protocolo de esfuerzo, con P-text ya congelado.

## 6. Las cuatro decisiones

**a) Desde Llama base, no desde el adaptador de A2.** El adaptador arrastra el sesgo prior que 0b detectó; el banco de A3 incluye F1, así que no se pierde nada; y una receta desde base es replicable con semillas, mientras que desde A2 queda atada a una semilla ajena. Es decidible sin más datos.

**b) 1 semilla de cribado, +2 si pasa.** La repetición de inferencia no sirve: el puntaje forzado es determinista y la varianza que importa es la del **entrenamiento** (inicialización del LoRA y orden de datos), con el mismo banco. Con 3 semillas no se estima una tasa de fallo: se puede decir "ninguna semilla falló". Si la semilla 1 falla, **diagnóstico antes de nuevas semillas**; una falla aislada no es evidencia sobre la receta.

**c) Diferir como brazo; adelantar un uso barato.** Un modelo grande vía API como **segundo anotador ciego de F-held** (auditoría de validez de las etiquetas), que de paso responde si los contratos son inequívocos. Un 70B local en 4-bit necesita del orden de 35-40 GB de VRAM; no sé tu GPU, pero con 2×T4 de Kaggle probablemente no entra. Como brazo más adelante: generación más parser no es comparable con puntaje forzado, así que sería referencia, fuera del McNemar.

**d) K = 8 contratos nuevos, fijados por tipo de novedad** (4 tipos × 2): unidad nueva, variante de cláusula de la misma familia ("no supere"), variable nueva, estructura nueva (disyunción o negación). Suite de aceptación de 20 contextos por contrato, 5 de ellos cerca del límite; contratos disjuntos de F-held; orden contrabalanceado entre caminos. Es **descriptivo** (mediana y rango, sin inferencia), así que el n no necesita potencia. La cobertura con cero ediciones sobre F-held es la métrica confirmatoria del artefacto.

## 7. Lo que no puedo decidir

- Tiempo real de entrenamiento y evaluación (uso A2 como unidad; no tengo sus tiempos).
- Si 1200 ejemplos con ~2 épocas bastan en A3 desde base: es empírico.
- Los umbrales numéricos de las secciones 1-3 son propuestas que el Director confirma antes de preregistrar.
