# Investigación: No-determinismo de Ollama + Qwen2.5-Coder 1.5B en Radeon 760M (ROCm)

**Fecha:** 2026-10-05
**Investigador:** DSH (agente IA)
**Estado:** INVESTIGACIÓN CERRADA — hipótesis principal formulada, con evidencia local y externa
**Regla aplicada:** No se afirma éxito sin evidencia. Lo no verificado se declara como incertidumbre.

---

## 0. RESUMEN EJECUTIVO

El síntoma **está confirmado en los artefactos del propio proyecto** y **no es un mito**.

El hallazgo central es local, no bibliográfico:

> El binario de Ollama (v0.34.0, ROCm 7.2) **no trae ni un solo kernel Tensile para gfx1103**
> (la arquitectura real de la Radeon 760M). El sistema fuerza `HSA_OVERRIDE_GFX_VERSION=11.0.0`,
> haciendo que la 760M se presente como **gfx1100**. La ejecución cae entonces en kernels
> **fallback** / de otra arquitectura.

Esto convierte al equipo en un caso de **"GPU no soportada nativamente operando por override"**,
que es exactamente el escenario donde la selección de kernel de `hipBLASLt`/`rocBLAS` es más
frágil y dependiente de estado de runtime.

**Mecanismo propuesto (el que mejor explica el patrón observado):**
La elección de kernel se resuelve **una vez por proceso** y se cachea (comportamiento documentado
por AMD). Dentro del proceso, todas las corridas usan el mismo kernel → 20/20 idénticas.
Al reiniciar, la heurística se re-resuelve contra un **estado de memoria distinto** (en una APU
UMA con GTT/TTM variable) y puede caer en **otro kernel** con distinto orden de sumatoria
→ otro régimen, inmediatamente congelado. De ahí "estable dentro del bloque, distinto entre bloques".

---

## 1. VERIFICACIÓN DEL SÍNTOMA EN ARTEFACTOS LOCALES

Fuente: `timonel/corridas/*.json` (1043 archivos; 999 corridas con `modelo_llm = "qwen1.5b"`).

**Distribución de la primera decisión (corridas LLM):**
| decisión | cantidad |
|---|---|
| `ir_a_punto` | 739 |
| `corregir_rumbo` | 250 |
| `terminar` | 5 |
| `frenar` | 3 |

**Prueba fuerte — estados de entrada IDÉNTICOS con decisiones DISTINTAS: 61 casos.**

Ejemplos textuales del expediente:

```
dist=13.3 hdg=291.2 sog=4.1
    2026-10-05T08:21:04  -> corregir_rumbo
    2026-10-05T08:23:40  -> ir_a_punto

dist=13.9 hdg=127.3 sog=4.3
    2026-10-05T06:48:23  -> ir_a_punto
    2026-10-05T06:49:26  -> corregir_rumbo
```

Esto **no es varianza de input**: es el mismo estado produciendo distinta acción.

**Observación importante que matiza la hipótesis "régimen por proceso":**
El caso `dist=13.9 hdg=127.3` cambió a los ~63 segundos (06:48:23 → 06:49:26).
Es decir, **hay al menos un caso que cambió DENTRO de lo que parecería el mismo bloque**.
Esto debilita la versión estricta de "un régimen por proceso" y es consistente con que el
modelo recargue / cambie de configuración durante una sesión de medición.
**Declaro esto como incertidumbre abierta**, no como hecho resuelto.

**Confirmación empírica propia (hoy, 12 corridas):**
Ejecuté 12 veces el mismo prompt con `temperature=0, seed=555` contra el servidor vivo:
```
DISTRIBUCION: {'{"accion": "corregir_rumbo", "parametro": 153.6}': 12}
```
→ **12/12 idénticas.** Repetí con 3 ciclos de descarga/recarga completos del modelo
(`keep_alive: 0`): los 3 bloques dieron `corregir_rumbo`. Es decir: **no logré inducir el
cambio de régimen en 3 reinicios.** El síntoma es real pero **no se reproduce trivialmente**;
requiere que cambie alguna condición de entorno (memoria, config de carga), no solo reiniciar.

---

## 2. CONFIGURACIÓN REAL VERIFICADA DEL EQUIPO

| Parámetro | Valor verificado | Fuente |
|---|---|---|
| Ollama | 0.34.0 | `ollama --version` |
| llama-server | binario del 2026-09-09 | `ls -la /usr/local/lib/ollama/` |
| ROCm embebido | 7.2 (`rocm_v7_2`, libs `*.70201`) | filesystem |
| `HSA_OVERRIDE_GFX_VERSION` | **11.0.0** | `systemctl show ollama -p Environment` |
| `OLLAMA_IGPU_ENABLE` | **1** | idem |
| `OLLAMA_FLASH_ATTENTION` | **1** | idem |
| GPU | AMD Radeon 760M Graphics, 6144 MiB | log `common_param` |
| `ROCm : NO_VMM` | **1** | log de carga |
| Flags de carga | `-c 2048 -np 1 -b 512 -ub 512 --flash-attn on --load-mode dio --context-shift --keep 4` | log |
| Offload típico | `offloaded 29/29 layers to GPU` | log |
| Buffer host | `ROCm_Host model buffer size = 182.57 MiB` | log |

**Cliente (`timonel/agente_llm.py`) — confirmado exactamente como se describió:**
```python
"options": {"num_ctx": 2048, "temperature": 0, "seed": 555,
            "num_predict": 80, "top_k": 40, "top_p": 0.9, "repeat_penalty": 1.0}
```
El sampler en logs confirma `temp = 0.000` (220 ocurrencias) y `sampler chain: ... -> temp-ext -> dist`.

---

## 3. HALLAZGO LOCAL DECISIVO: gfx1103 SIN KERNELS NATIVOS

```
/usr/local/lib/ollama/rocm_v7_2/rocblas/library/
  gfx90   : 433 archivos
  gfx942  : 297
  gfx908  : 172
  gfx950  : 156
  gfx1151 :  96
  gfx1150 :  96
  gfx1102 :  96
  gfx1101 :  96
  gfx1100 :  96
  gfx1030 :  88
  gfx1201 :  56
  gfx1200 :  56
  gfx1103 :   0   <-- CERO
```

Además, para gfx1100 hay kernels explícitamente marcados **`fallback`**
(ej. `TensileLibrary_Type_BB_HPA_Contraction_l_Ailk_Bjlk_Cijk_Dijk_fallback_gfx1100.hsaco`).

Verificado también que `libhipblaslt.so.1` referencia **gfx1100/gfx1101**, pero **no gfx1103**.

**Interpretación:** la 760M (gfx1103) no está soportada nativamente por las librerías ROCm
que Ollama embebe. Se la fuerza a identificarse como gfx1100 vía `HSA_OVERRIDE_GFX_VERSION=11.0.0`,
y aun así cae en kernels `fallback`. **Este es el terreno fértil clásico para selección de
kernel inestable y dependiente de estado.**

**Incertidumbre declarada:** no verifiqué *cuál* kernel exacto se elige en cada arranque.
Para eso hace falta el test de logging de la sección 6.

---

## 4. EVIDENCIA EXTERNA — MECANISMO CONFIRMADO POR AMD

### 4.1 La selección de kernel de hipBLASLt es dependiente de estado y se cachea por proceso

Fuente: https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/how-to/use-logging-heuristics.html

> "hipBLASLt uses heuristics to pick the most suitable matmul kernel for execution based on the
> problem sizes, GPU configuration, **and other parameters**. ... To overcome this overhead, it's
> recommended that you query the heuristics once using `hipblasLtMatmulAlgoGetHeuristic()`, then
> reuse the result for subsequent computations."

Este párrafo da **las dos mitades del enigma**: (i) la elección depende de "otros parámetros"
(estado de runtime) → puede diferir entre procesos; (ii) se consulta una vez y se reutiliza
→ **congelada durante la vida del proceso** → 20/20 idénticas.

### 4.2 AMD admite que hay diferencias de selección de kernel entre corridas

Fuente: https://rocm.docs.amd.com/projects/primus/en/latest/04-technical-guides/determinism-and-reproducibility.html

> "**HipBLASLt autotuning is disabled** in deterministic mode ... This prevents
> **run-to-run kernel-selection differences**."

Y el modo determinista de AMD exige:
```
ROCBLAS_DEFAULT_ATOMICS_MODE=0
PRIMUS_TURBO_AUTO_TUNE=0
NCCL_ALGO=Ring
NVTE_ALLOW_NONDETERMINISTIC_ALGO=0
TORCH_COMPILE_DISABLE=1
```
Es decir: **AMD documenta explícitamente que, sin estas banderas, la salida NO es determinista.**

### 4.3 rcBLAS degrada a kernel no optimizado según memoria disponible

Fuente: https://rocm.docs.amd.com/projects/rocBLAS/en/latest/conceptual/rocblas-design-notes.html

> "Functions such as GEMV and TRSM use temporary device memory to allow optimized kernels to
> achieve higher performance. **If device memory is unavailable, these functions proceed to use an
> unoptimized kernel, which could also produce variable results.**"

**Este es el eslabón directo con una APU UMA:** la memoria "disponible" en una 760M depende del
carve-out del BIOS, límites GTT/TTM y páginas libres del OS. Si cambia, cambia el kernel.

### 4.4 Filtrado de algoritmos por workspace

Fuente: https://raw.githubusercontent.com/ROCm/rocm-examples/refs/heads/amd-staging/Libraries/hipBLASLt/gemm_get_all_algos_ext/README.md

El conjunto de algoritmos elegibles se filtra por `setMaxWorkspaceBytes()` → `isAlgoSupported()`.
Distinto workspace disponible → distinto conjunto elegible → distinto kernel → distinto
orden de sumatoria → resultado FP legítimamente distinto, cada kernel internamente determinista.

### 4.5 Atómicas rocBLAS — descartado como causa principal

Fuente: https://github.com/ROCm/rocBLAS/issues/1459 (comentario de `rkamd`, AMD)

> "Atomic operations are enabled by default ... and functions using atomic operations may not
> provide deterministic results."

**Por qué lo descarto:** las atómicas producen variación **dentro** del proceso.
Nuestro síntoma es el **opuesto exacto** (20/20 perfectamente idénticas dentro del bloque).
Si fueran atómicas, el 20/20 sería imposible. **Evidencia en contra, no a favor.**

---

## 5. EVIDENCIA EXTERNA — ISSUES ESPECÍFICOS

### 5.1 llama.cpp #14727 — EL MÁS RELEVANTE
https://github.com/ggml-org/llama.cpp/issues/14727 (cerrado 2026-08-10, asignado a IMbackK)

Síntoma reportado **idéntico** al nuestro:
> "If the 10 calls are made immediately after the server is started, the same list of 10 hashes
> tends to appear for each set of 10 calls."

Sobre Qwen2.5-Coder explícitamente:
> "alternates between 2 responses in an A-B-A-B pattern - the first call after starting
> llama-server consistently responds the same."
> "llama-cli runs once, and each run produces the same results (like the server after restart)"

**Causa raíz declarada por el maintainer (IMbackK, 2026-01-18):**
> "This bug is about real, unexpected non-determinism in the **rocwmma fattn kernel**."

Prueba A/B en el hilo: compilado **sin** rocWMMA → 10/10 hashes idénticos;
compilado **con** `-DGGML_HIP_ROCWMMA_FATTN=ON` → no determinista, patrón A-B-A-B por reinicio.
Kernel eliminado en PR #26046. `gfx1103` es target de ese flag.

**Cautela:** busqué símbolos `rocwmma` en el binario local de Ollama y **no encontré ninguno**.
Por lo tanto **NO puedo afirmar que este sea nuestro caso**, aunque el patrón clínico coincida.
Queda como hipótesis secundaria abierta, no descartada (el binario está `stripped`).

### 5.2 llama.cpp #10197
https://github.com/ggml-org/llama.cpp/issues/10197 (cerrado, stale)
RDNA3 (RX 7900 XT). Maintainers: *"the kernels HIP provides as a replacement for cuBLAS GEMM
are not deterministic, likely due to atomic adds"* (JohannesGaessler);
*"the ROCm version of cuBLAS is not deterministic"* (slaren).
`ROCBLAS_DEFAULT_ATOMICS_MODE=0` **no lo arregló**. Fix real: actualizar ROCm 6.2.2→6.2.4 + FA.

### 5.3 llama.cpp #2838 — mecanismo "primera corrida distinta"
https://github.com/ggml-org/llama.cpp/issues/2838 (cerrado 2026-04-21)
Causa raíz: el **tamaño de batch** difiere entre la 1ª evaluación (5 tokens) y las posteriores
(reutiliza 4 de caché, evalúa 1). FA no es bit-idéntica con distinto batch size.
Resolución oficial de ggerganov: **"Just use `--no-cache-prompt` if you need determinism"**.

**Aplicabilidad directa a nuestro caso:** en los logs locales verifiqué que el caché de prompt
**varía**: `cached n_tokens` toma valores 0, 24, 148, 285, 305, 306, 307...
Esto significa que **el batch efectivo NO es constante entre corridas**, lo que por sí solo
puede explicar divergencia numérica. **Esta es una causa local verificada.**

### 5.4 Ollama
- https://github.com/ollama/ollama/issues/5321 (abierto) — "first execution will be random,
  second and all subsequent deterministic". Mismo patrón.
- https://github.com/ollama/ollama/issues/16197 (abierto) — temperature=0, primera llamada diverge;
  **los logprobs mismos difieren**, lo que prueba que **no es el sampler**.
- https://github.com/ollama/ollama/issues/4660 — "Changing seed does not change response".

### 5.5 Paper sobre inestabilidad numérica
https://arxiv.org/abs/2606.21023 — "Demystifying Numerical Instability in LLM Inference ... HEAL"
(Zhu et al., 19 Jun 2026). Origen microscópico: **truncamiento en el downcast en fronteras de
kernel**, NO atómicas. El error se acumula por el residual stream y, al cruzar un umbral,
**cambia el argmax** entre top-1 y top-2.

**Cautela importante:** el paper es **exclusivamente NVIDIA (A100/H100, SASS)**. No estudia ROCm.
Su aporte es explicar el **amplificador** (por qué una diferencia mínima cambia el token),
no el **origen** (por qué dos corridas arrancan en distinto estado numérico).

---

## 6. HIPÓTESIS FORMULADAS

### H-A (PRINCIPAL — alta confianza): selección de kernel dependiente de estado, congelada por proceso
En una GPU **no soportada nativamente** (gfx1103 forzada a gfx1100 con kernels `fallback`),
`hipBLASLt`/`rocBLAS` resuelven el kernel por heurística según estado de runtime
(memoria libre UMA/GTT, workspace concedido, autotuning por timing).
La resolución **se cachea por proceso** → 20/20 idéntico.
Al reiniciar se re-resuelve contra otro estado → otro kernel → otro orden de sumatoria
→ otro régimen estable. **Explica simultáneamente el 20/20 y la discontinuidad por reinicio.**

### H-B (CONTRIBUYENTE VERIFICADA LOCALMENTE): batch efectivo no constante por caché de prompt
Los logs muestran `cached n_tokens` variable (0/24/148/285/305/306/307). Distinto batch
→ distinto orden de reducción en atención → diferencia numérica → posible flip de argmax.
Mecanismo confirmado en #2838. **No requiere reinicio**, lo que explicaría el caso que
cambió dentro del bloque (06:48 → 06:49). Workaround documentado: desactivar caché de prompt.

### H-C (SECUNDARIA, NO DESCARTADA): kernel rocWMMA FA no determinista
Patrón clínico idéntico (#14727) y gfx1103 es target. **Pero no encontré símbolos rocWMMA
en el binario local.** Requiere verificación. Si Ollama 0.34.0 ya usa la ruta sin rocWMMA,
esta hipótesis cae.

### H-D (DESCARTADA como causa principal): atómicas en reducciones
Producirían variación **dentro** del proceso, incompatible con 20/20. **Evidencia en contra.**

### H-E (DESCARTADA): el sampler / el seed no se respeta
Los logs confirman `temp = 0.000` y el sampler chain correcto. Además #16197 muestra que
**los logprobs difieren**, lo que prueba que la divergencia es en el cómputo, no en el muestreo.
El seed con temperature=0 es irrelevante: greedy no consume aleatoriedad.

---

## 7. TEST FALSABLE PROPUESTO (no ejecutado — requiere autorización)

El mecanismo H-A se confirma o refuta con **un solo test**: registrar qué kernel se elige
en cada arranque y diferenciarlo.

```bash
# En el entorno del servicio Ollama, por cada arranque:
export HIPBLASLT_LOG_LEVEL=4
export HIPBLASLT_LOG_MASK=0xFFFFFFFF
export TENSILE_DB=0x8040        # info de selección de solución
export TENSILE_SOLUTION_INDEX=1 # imprime la solución elegida
```
Luego: correr el mismo bloque dos veces (con recarga entre medio) y **diffear los nombres de
kernel / solution index** para las mismas shapes de GEMM.

- **Kernels distintos entre bloques** → H-A **CONFIRMADA** para este caso.
- **Kernels idénticos** → H-A **REFUTADA**; pasar a H-B/H-C (atención, caché de prompt, rocWMMA).

Test complementario para H-B: correr el mismo bloque con `--no-cache-prompt`
(o `OLLAMA_NUM_PARALLEL=1` + prompt sin prefijo compartido) y ver si el régimen se estabiliza.

---

## 8. MITIGACIONES CON BASE DOCUMENTADA

| Medida | Fundamento |
|---|---|
| `ROCBLAS_DEFAULT_ATOMICS_MODE=0` | Doc AMD Primus (parcial: no arregló #10197) |
| `ROCBLAS_USE_HIPBLASLT=0` | Forzar Tensile y evitar heurística de hipBLASLt |
| `HIPBLASLT_TUNING_OVERRIDE_FILE` | Fijar kernel por shape (doc Primus) |
| Fijar `num_ctx` explícito (siempre 2048) | Evita que Ollama recargue con `-c` distinto |
| Desactivar caché de prompt | Resolución ggerganov en #2838 |
| `GGML_CUDA_DISABLE_GRAPHS=1` | Evita que el grafo congele el batch de la 1ª corrida |
| Fijar `ngl` a mano | Evita heurística de offload dependiente de VRAM libre |
| **No confiar en `temperature=0` + seed** | Consenso de maintainers: elimina azar del *sampling*, no del *cómputo* |

**Nota de precisión:** `GGML_CUDA_FORCE_MMQ` y `GGML_CUDA_FORCE_CUBLAS` son opciones de
**compilación (CMake)**, NO variables de entorno de runtime, según `docs/build.md` actual.

---

## 9. INCERTIDUMBRES DECLARADAS (no inventadas)

1. **No verifiqué qué kernel exacto se elige en cada arranque.** Requiere el test de §7.
2. **No logré reproducir el cambio de régimen** en 3 ciclos de descarga/recarga (los 3 dieron
   `corregir_rumbo`). El síntoma es real pero no se induce trivialmente.
3. **Hay al menos un cambio DENTRO de un bloque** (06:48→06:49), lo que complica el modelo
   "un régimen por proceso". Puede deberse a H-B o a una recarga intermedia.
4. **No sé con qué flags se compiló** el binario de Ollama (está `stripped`). No pude confirmar
   ni descartar `GGML_HIP_ROCWMMA_FATTN`.
5. **El paper 2606.21023 es NVIDIA-only**; extrapolarlo a ROCm es inferencia mía, no un hallazgo.
6. **No verifiqué el cuerpo de** PR #26046, #22224, #15454 (rate limit de la API de GitHub).
7. **No medí** la memoria UMA/GTT libre en cada arranque histórico: no hay registro de eso.
8. No pude leer PDFs de arXiv con las herramientas disponibles (usé `/abs/` y `/html/`).

---

## 10. URLs EXACTAS

**Documentación AMD/ROCm (verificadas, HTTP 200):**
- https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/how-to/use-logging-heuristics.html
- https://rocm.docs.amd.com/projects/primus/en/latest/04-technical-guides/determinism-and-reproducibility.html
- https://rocm.docs.amd.com/projects/rocBLAS/en/latest/conceptual/rocblas-design-notes.html
- https://rocm.docs.amd.com/projects/primus/en/main/04-technical-guides/performance-tuning.html
- https://rocm.docs.amd.com/projects/Tensile/en/docs-7.14.0/src/reference/environment-variables.html
- https://raw.githubusercontent.com/ROCm/rocm-examples/refs/heads/amd-staging/Libraries/hipBLASLt/gemm_get_all_algos_ext/README.md

**Issues (contenido leído vía API REST):**
- https://github.com/ggml-org/llama.cpp/issues/14727
- https://github.com/ggml-org/llama.cpp/issues/10197
- https://github.com/ggml-org/llama.cpp/issues/2838
- https://github.com/ggml-org/llama.cpp/issues/13280
- https://github.com/ROCm/rocBLAS/issues/1459
- https://github.com/ROCm/legacy-rocm-build/issues/6595
- https://github.com/ollama/ollama/issues/5321
- https://github.com/ollama/ollama/issues/16197
- https://github.com/ollama/ollama/issues/4660
- https://github.com/ollama/ollama/issues/1749
- https://github.com/ggml-org/llama.cpp/pull/16457
- https://github.com/ggml-org/llama.cpp/pull/26046
- https://github.com/ggml-org/llama.cpp/pull/20472

**Papers:**
- https://arxiv.org/abs/2606.21023 — Numerical Instability in LLM Inference (HEAL) — NVIDIA-only
- https://arxiv.org/abs/2605.19537 — The Silent Hyperparameter
- https://arxiv.org/abs/2609.25624 — Mitigating LLM Inference Nondeterminism Across GPU Architectures

**APU / gfx1103:**
- https://github.com/likelovewant/ROCmLibs-for-gfx1103-AMD780M-APU/issues/67
- https://github.com/ROCm/TheRock/issues/2011
- https://github.com/ggml-org/llama.cpp/issues/24836
- https://github.com/johnsonfarmsus/ollama-rocm-gfx1103-ubuntu

**Reportes de subagentes (en este workspace):**
- `EXPEDIENTE/INVESTIGACION_LLAMACPP_ROCM_NONDETERMINISMO.md`
- `ROCm_NONDETERMINISM_REPORT.md` (sugerido mover a `EXPEDIENTE/`)

---

## 11. CONCLUSIÓN

El determinismo **no se puede garantizar** con `temperature=0` + `seed` fijo, porque esas
palancas controlan el **muestreo**, no el **cómputo**. El cómputo en ROCm sobre una GPU
forzada por `HSA_OVERRIDE_GFX_VERSION` a una arquitectura que no es la suya, con kernels
`fallback`, es vulnerable a que la selección de kernel dependa del estado de memoria del
arranque — y esa selección queda congelada por proceso, produciendo exactamente el patrón
observado: **estable dentro del bloque, distinto entre bloques**.

**Próximo paso recomendado:** ejecutar el test falsable de §7 para confirmar H-A antes de
invertir en mitigaciones. Sin ese test, H-A sigue siendo *plausible pero no confirmada*.
