# Investigación: no-determinismo en llama.cpp sobre ROCm/AMD

Objetivo: explicar por qué un modelo (Qwen2.5-Coder 1.5B) en un iGPU AMD Radeon 760M
(gfx1103, RDNA3) vía ROCm produce "regímenes estables" que cambian entre reinicios de
proceso, aun con `temperature=0`, `seed=555`, mismo prompt y mismo modelo.

Todo lo marcado **VERIFICADO** fue leído directamente (API REST de GitHub o fetch del
contenido). Lo marcado **SOLO TÍTULO** proviene únicamente de resultados de búsqueda.

---

## 1. Issues de llama.cpp (contenido real leído)

### Issue #10197 — "Bug: Nondeterministic results on AMD RDNA3 (ROCm) despite zero temperature and fixed seed"
- URL: https://github.com/ggml-org/llama.cpp/issues/10197
- API: https://api.github.com/repos/ggml-org/llama.cpp/issues/10197
- **Estado: CERRADO** (cerrado por `github-actions[bot]` el 2024-12-29 por inactividad; etiquetas `bug-unconfirmed`, `stale`, `medium severity`). Autor: Googulator.
- **VERIFICADO**. Reporta RX 7900 XT (RDNA3), llama-server, `-ngl 50`, mistral-nemo q8_0.
  Workarounds que DAN determinismo (según el autor):
  - Deshabilitar el offload del KV cache.
  - Compilar con `GGML_CUDA_FORCE_MMQ=1` **y** activar Flash Attention (ninguno solo basta).
  - Parchear el chequeo de compute capability (en `ggml-cuda.cu`) para devolver `false` en AMD, **y** activar FA.
- **Causa raíz declarada por maintainers:**
  - `slaren` (MEMBER): "my conclusion would be that the ROCm version of cuBLAS is not deterministic."
  - `JohannesGaessler` (CONTRIBUTOR): "the kernels HIP provides as a replacement for cuBLAS GEMM are not deterministic, **likely due to atomic adds**. Unless it's possible to configure that library differently there is nothing on our end that we could do."
  - El chequeo de CC pretendía decidir si la GPU tiene F16 matmul suficientemente rápida para convertir operandos a F16; "fue escrito para GPUs NVIDIA, y no creo que se haya probado en hardware AMD" (slaren).
- **Actualización del autor (2024-11-13)**: al actualizar ROCm 6.2.2 → 6.2.4, `--flash-attn` pasó a ser suficiente para determinismo. Concluye que eran **dos bugs distintos**:
  1. Un bug de ROCm (regresión en 6.2.x) que hacía no deterministas los kernels `GemmEx` aun con atomics desactivados → arreglado en 6.2.4.
  2. Otro problema (en GGML/llama.cpp o ROCm) que introduce no-determinismo **específicamente con FA deshabilitada**; persiste en 6.2.4 incluso con `top_k=1`, MMQ forzado y `ROCBLAS_DEFAULT_ATOMICS_MODE=0`.
- Nota del autor: `ROCBLAS_DEFAULT_ATOMICS_MODE=0` (recomendado por docs de AMD) **no** lo arregló.

### Issue #14727 — "Eval bug: Nondeterministic output with ROCm backend despite zero temperature"
- URL: https://github.com/ggml-org/llama.cpp/issues/14727
- API: https://api.github.com/repos/ggml-org/llama.cpp/issues/14727
- **Estado: CERRADO** (2026-08-10, asignado a `IMbackK`; etiqueta `bug`). Autor: Googulator.
- **VERIFICADO**. RX 7800 XT (gfx1100) y RX 7900 XT, `-fa`, Q8_0, `-t 0` (greedy).
  Observaciones clave **que coinciden exactamente con el problema del iGPU 760M**:
  - "If the 10 calls are made immediately after the server is started, **the same list of 10 hashes tends to appear** for each set of 10 calls."
  - "Qwen-2.5-Coder alternates between 2 responses in an **A-B-A-B pattern - the first call after starting llama-server consistently responds the same**."
  - "Disabling Flash-Attention changes the pattern, but doesn't fix the issue."
  - También en `llama-cli`: "llama-cli runs once, and each run produces the same results (**like the server after restart**)". Es decir: **un proceso nuevo = un régimen estable nuevo**. Esto es exactamente el síntoma reportado.
- **Reproducción de régimen por reinicio (broadbit-hu, VERIFICADO)**: lista de 10 hashes idéntica antes y después de parar/arrancar llama-server, pero distinta entre bloques → "Just see the pattern of the output after server restart."
- **Diagnóstico de los maintainers / hallazgos:**
  - `ggerganov` (MEMBER): pedir `cache_prompt:false`, probar build CPU-only, revisar `--verbose`.
  - `JohannesGaessler`: probar `GGML_CUDA_FORCE_MMQ=ON` → **no** arregla (broadbit-hu lo confirmó con log `FORCE_MMQ = 1`).
  - **Confirmado**: CPU-only y CUDA (NVIDIA) son deterministas; **solo ROCm** falla.
  - `IMbackK` (CONTRIBUTOR, asignado): "rocBLAS is not deterministic by default. you can fiddle with `ROCBLAS_DEFAULT_ATOMICS_MODE` to make it deterministic."
  - `IMbackK` preguntó si el bug ocurre con `GGML_HIP_ROCWMMA_FATTN=On`, `Off`, o ambos.
  - **Respuesta clave (broadbit-hu, VERIFICADO, 2025-07-30):**
    - **Sin rocWMMA** (`-DGGML_HIP=ON -DAMDGPU_TARGETS=gfx1100,gfx1101`): **determinista** (10/10 hashes iguales), pero pp baja de ~1700 a ~800 t/s en 7900 XTX.
    - **Con rocWMMA** (`-DGGML_HIP_ROCWMMA_FATTN=ON`): **NO determinista**, mismo patrón A-B-A-B en cada reinicio.
    - Con `-ngl 0` (CPU): determinista en ambos casos.
  - **Conclusión explícita del maintainer asignado (IMbackK, 2026-01-18, VERIFICADO):**
    > "This bug is about **real, unexpected non-determinism in the rocwmma fattn kernel**, i dont think theres mutch point in spending time investigateing why the kernel is not deterministic, **since this kernel is going to be removed soon**"
  - Nota de `tommasocerruti` (community): `temperature=0/top_k=1/seed fijo` quita aleatoriedad del *sampling* pero **no garantiza cómputo determinista**, especialmente en backends GPU. Sugiere `--threads 1 --threads-batch 1`, `--batch-size 1 --ubatch-size 1`, y `n_probs>0` para capturar el primer token divergente.
- **Contexto del PR que cambió el patrón**: broadbit-hu reporta que en el release b6218 (que incluye PR #15454 "CUDA: refactor FA support/selection code") el patrón cambió. **PR #15454 URL**: https://github.com/ggml-org/llama.cpp/pull/15454 (solo título/atribución verificados por búsqueda; el fetch directo de la API falló por rate limit).

### Issue #2838 — "CUDA non-determinism on identical requests"
- URL: https://github.com/ggml-org/llama.cpp/issues/2838
- API: https://api.github.com/repos/ggml-org/llama.cpp/issues/2838
- **Estado: CERRADO** (2026-04-21). Etiquetas `bug`, `good first issue`.
- **VERIFICADO**. Es el caso NVIDIA/CUDA, pero **crítico** porque identifica el mecanismo exacto
  de "primer request distinto, luego estable" y de "un régimen por reinicio":
  - **Causa raíz (comentario de `ivich123`, 2026-03-20, VERIFICADO):**
    - El servidor reutiliza KV cache; el **tamaño de batch** de la primera evaluación difiere del de las posteriores. Ej.: primer request evalúa 5 tokens de prompt en un batch (`batch.n_tokens = 5`); el segundo reutiliza 4 tokens y evalúa 1 (`batch.n_tokens = 1`).
    - "**CUDA Flash Attention is not bit-identical when computing attention with different batch sizes** (5 tokens at once vs 1 token reading K/V from cache). The floating point operation order differs due to parallelism, producing small numerical differences (~0.01-0.07) that accumulate across 32 transformer layers and are enough to change which token wins during sampling."
    - Bisect de `ngl`: `ngl 0/1/2` → no reproduce; `ngl 3+` → sí. Es decir, **basta offload parcial** para introducir la divergencia.
  - `ggerganov` (MEMBER): "We seem to be ignoring the provided seed" (regresión tras soporte de decodificación paralela) — pero luego se aclaró que con `temperature=0` el RNG no importa.
  - **Resolución / workaround oficial**: PR #22224 (https://github.com/ggml-org/llama.cpp/pull/22224) propuso forzar `n_past = 0` cuando el seed está fijado; **NO fusionado**. `ggerganov` respondió (2026-04-21, VERIFICADO): **"Just use `--no-cache-prompt` if you need determinism"** y el PR se cerró. El issue se cerró al día siguiente.
  - Comentario adicional (d-kleine, 2024-10-03): "When disabling the KV cache, the output is deterministic. When keeping it enabled, the first output is different from the following ones... It seems like the cache is not updated with the same state as has been initialized."

### Issue #13280 — "Eval bug: Heavy nondeterminism in Qwen3 MoE (CUDA)"
- URL: https://github.com/ggml-org/llama.cpp/issues/13280
- **Estado: CERRADO** (2025-05-04).
- **VERIFICADO**. Relevante porque demuestra un **race condition real en el kernel MMQ** que
  causaba no-determinismo variable, y muestra la metodología de diagnóstico:
  - Con `-ub 1` → resultados **correctos y deterministas**. Con `-ngl 99` → incorrectos y no deterministas. Con `-ngl 0` → incorrectos pero deterministas. Con `-ngl 2+` y creciente → "worse and worse".
  - `JohannesGaessler` publicó un parche de prueba eliminando el fast-path `mul_mat_id`, luego un fix por **race condition en el nuevo código MMQ** (PR #13294 y PR #13299). El usuario confirmó el fix en el commit `93c4e23905987949b714b21ae918ff6bfb55fe36`: "fixed the nondeterminism issue."
  - Frase clave del maintainer: "prior to my changes the results were already non-deterministic" y "Generally speaking it is expected that results will not be bit-for-bit identical if you vary some of the parameters. If different code is being run, then the floating point rounding error will be different".

### PR #26046 — "HIP: remove rocWMMA FlashAttention"
- URL: https://github.com/ggml-org/llama.cpp/pull/26046
- **SOLO TÍTULO / diff indirecto** (verificado vía SemanticDiff y el commit espejo https://github.com/RunanywhereAI/llama.cpp/commit/fa72aeccb23947074c12b5fec25f5b6ced28cbfe). Confirma que el kernel rocWMMA FA (el señalado como no determinista en #14727) **fue eliminado**.

### Issue #26220 — "Bug: Native MMA FA kernel regresses prompt processing up to 2x at depth on RDNA4 (gfx1201) after rocWMMA removal"
- URL: https://github.com/ggml-org/llama.cpp/issues/26220
- **SOLO TÍTULO**. Muestra que la eliminación de rocWMMA tuvo consecuencias de rendimiento en RDNA.

### PR #16457 — "Add hipblasLt implementation for batched gemm to improve performance for CDNA3 only"
- URL: https://github.com/ggml-org/llama.cpp/pull/16457
- **Estado: ABIERTO, NO fusionado** (`merged: false`, `mergeable_state: clean`). Autor: peizhang56 (AMD-Ecosystem).
- **VERIFICADO**. Relevante para hipBLASLt vs rocBLAS:
  - "This acts an alternative way to fix the **coredump when export `ROCBLAS_USE_HIPBLASLT=1`**".
  - "The feature is **disabled by default**, and only applies to CDNA3".
  - Variables: `USE_HIPBLASLT_GROUPED_GEMM=1` (enable), `=2` (offline-bench), `=3` (best algo).
  - Implica que en RDNA (gfx11xx) hipBLASLt **no** se usa por defecto en esta ruta, y que seleccionar algoritmo "best algo" introduce una **heurística de autotuning**.

### Otras issues ROCm/MMQ relevantes (VERIFICADO, solo cuerpo/título del listado)
- #29910 (PR abierto): "ggml-cuda: fix a mountain of VGPR spills on Q2_K" — en gfx1100 (RDNA3) MMQ tenía **1387 spills**, en gfx1200 **2041**; el autor los lleva a 0 con otro unroll. Demuestra que la selección de kernel MMQ por arquitectura es sensible y divergente por arch.
  URL: https://github.com/ggml-org/llama.cpp/pull/29910
- #29536 (PR abierto): "hip : fix build with stock LLVM 23 and avoid MMQ spills on RDNA4" — menciona RDNA y el 780M (gfx1103).
  URL: https://github.com/ggml-org/llama.cpp/pull/29536
- #28404: "Eval bug: two co-resident llama-server processes ... CUDA graph reuse; `GGML_CUDA_DISABLE_GRAPHS=1` fixes it" — **SOLO TÍTULO**. Indica que la captura de CUDA graphs puede causar fallos reproducibles; el env var `GGML_CUDA_DISABLE_GRAPHS=1` lo evita.
- #28495: `-np 2` + `--kv-unified` degrada prompt processing en HIP; workaround `--no-kv-unified`. Menciona `GGML_CUDA_DISABLE_GRAPHS=1` usado en todas las ramas del test. **VERIFICADO** parcialmente (cuerpo).
  URL: https://github.com/ggml-org/llama.cpp/issues/28495
- #26964 / #26996: paquetes Windows ROCm sin `hipblas.dll`/`rocblas.dll` → GPU no detectada. **VERIFICADO**. Contexto sobre lo frágil de la cadena hipBLAS/rocBLAS.

---

## 2. Variables de entorno y flags: lo que build.md realmente dice

Fuente verificada: https://raw.githubusercontent.com/ggml-org/llama.cpp/master/docs/build.md

**CORRECCIÓN IMPORTANTE:** En la documentación actual de llama.cpp, `GGML_CUDA_FORCE_MMQ` y
`GGML_CUDA_FORCE_CUBLAS` aparecen en la tabla de **opciones de compilación** (CMake), no como
variables de entorno de runtime. El log `ggml_cuda_init: GGML_CUDA_FORCE_MMQ: no` que ven los
usuarios proviene de que el binario fue compilado con esa opción. Muchos reportes (incluido
#10197) las tratan como env vars; **conviene tratarlas como flags de build**.

| Flag / env var | Tipo | Efecto documentado | Relevancia para determinismo |
|---|---|---|---|
| `GGML_CUDA_FORCE_MMQ` | Compilación | Fuerza kernels MMQ propios en vez de cuBLAS FP16 (afecta V100, CDNA, **RDNA3+**). Peor speed a batch grande, menos VRAM. | Usar el código propio (determinista por diseño) en vez de la BLAS externa (no determinista). No siempre suficiente (#10197, #14727). |
| `GGML_CUDA_FORCE_CUBLAS` | Compilación | Fuerza cuBLAS FP16 en vez de MMQ. | Fuerza la ruta externa → riesgo de no-determinismo por atomics. |
| `GGML_CUDA_FA_QUANTS` | Compilación | Selecciona combinaciones K/V para kernels FA. | Determina qué kernel FA corre → distinta aritmética. |
| `GGML_HIP_ROCWMMA_FATTN` | Compilación | Habilita FA vía rocWMMA en CDNA/RDNA3+. | **Kernel señalado como no determinista** en #14727; **eliminado en PR #26046**. |
| `GGML_CUDA_DISABLE_GRAPHS` | Runtime (env) | Deshabilita captura/repetición de CUDA graphs. | Evita fallos por reutilización de grafo (#28404); un grafo captura el tamaño de batch → puede fijar/alterar el orden de reducción. |
| `GGML_CUDA_ENABLE_UNIFIED_MEMORY` | Runtime | UMA para iGPU (relevante para el 760M). | Cambia dónde viven los buffers; puede alterar rutas de kernel. |
| `ROCBLAS_DEFAULT_ATOMICS_MODE=0` | Runtime (ROCm) | Recomendado por docs AMD para kernels deterministas. | Reportado **ineficaz** en #10197. |
| `ROCBLAS_USE_HIPBLASLT=1` / `ROCBLAS_USE_HIPBLASLT_BATCHED=1` | Runtime (ROCm) | Enruta GEMM a hipBLASLt (autotuning de algoritmo). | Candidato fuerte a selección de kernel no determinista entre procesos (caché de autotuning). |
| `HIP_VISIBLE_DEVICES` | Runtime | Selección de GPU. | No afecta determinismo, pero sí reproduciblemente el entorno. |
| `HSA_OVERRIDE_GFX_VERSION` | Runtime | Fuerza gfx target (ej. 11.0.0). | Cambiar el target cambia el set de kernels → puede cambiar régimen. |

---

## 3. Papers sobre no-reproducibilidad / localización

### "The Silent Hyperparameter: Quantifying the Impact of Inference Backends on LLM Reproducibility"
- arXiv: **https://arxiv.org/abs/2605.19537** (v2, 20 May 2026). HTML: https://arxiv.org/html/2605.19537v2
- Autores: David Pape, Jonathan Evertz, Lea Schönherr (CISPA). **VERIFICADO (abstract + secciones 1–6)**.
- Hallazgos clave:
  - La elección de backend puede mover el score de benchmark hasta **16.6 puntos porcentuales** con pesos, decoding params y hardware constantes. Ollama es un outlier notable (Llama 3.1 8B en GSM8K cae ~10 pts; DeepSeek R1 Distill Qwen 7B con Ollama: tasa de desacuerdo **27.37%**).
  - **Causa raíz**: "this divergence is driven by **system-level optimizations like prefix caching and CUDA graphs, custom kernels, and engine-specific defaults in logit processing**."
  - Evalúan en **un solo GPU NVIDIA H100**, batch size 1, greedy decoding, FP16. No cubren ROCm.
  - **Aplicación al caso**: prefix caching y CUDA/HIP graphs son exactamente los dos mecanismos que cambian entre procesos/reinicios y entre primera y siguientes peticiones.

### "Accelerating the Mitigation of LLM Inference Nondeterminism Across GPU Architectures"
- arXiv: **https://arxiv.org/abs/2609.25624** (22 Sep 2026). Autores: Cooper, Jeong, Jeon, Young, Kim (Georgia Tech). **VERIFICADO (abstract)**.
- Tesis: "The root cause is **floating-point non-associativity combined with hardware-dependent kernel selection**. Inference frameworks select different matrix-multiplication kernels on each architecture, with **different parallel reduction orders** and unspecified tensor-core arithmetic, and the resulting rounding differences can flip output tokens."
- Propone kernels con **reduction order que es función pura de la forma del problema**, independiente del número de SMs y del scheduling. Reproducibilidad bit a bit entre Ampere/Ada/Hopper.
- **Aplicación**: valida que "mismo modelo, distinta selección de kernel → distinto resultado" es el mecanismo de primer orden, y que la clave es fijar el orden de reducción.

### Paper con la frase "not a pervasive noise problem, but a localized..."
- **BÚSQUEDA PARCIALMENTE FALLIDA.** La frase aparece citada en un snippet: "the non-reproducibility of LLM inference is not a pervasive noise problem, but a localized se..." asociada a `arxiv.org/pdf/2606.21023v1`. Sin embargo, al recuperar **https://arxiv.org/abs/2606.21023** el contenido real es **otro paper**: "Demystifying Numerical Instability in LLM Inference: Achieving Reproducible Inference for Mission-Critical Tasks with HEAL" (Zhu et al., 19 Jun 2026), cuyo abstract NO contiene esa frase y trata de errores de truncamiento al hacer downcast en fronteras de kernel y una técnica llamada HEAL.
- **No pude identificar con certeza el paper exacto de la frase.** El snippet parece provenir del cuerpo (no del abstract) de algún PDF indexado. Lo reporto explícitamente como **NO VERIFICADO**.
- Candidato relacionado y **verificado**: el paper HEAL sí localiza la causa en "truncation errors introduced during downcasting at kernel boundaries" — es decir, **no es ruido difuso, está localizado en operaciones concretas**.

### "Same Prompt, Different Answer: Hidden Non-Determinism in LLM APIs Undermines Scientific Reproducibility"
- URL: https://github.com/Roverlucas/genai-reproducibility-protocol (PDF `article/ncomms_main.pdf`) — **SOLO TÍTULO**. Trata de no-determinismo en APIs de LLM.

### Localización empírica ROCm vs CPU (spec de vllm.cpp, muy relevante)
- URL: https://raw.githubusercontent.com/mudler/vllm.cpp/refs/heads/main/.agents/specs/rocm-tier-hidden-state-bisect.md
- **VERIFICADO (documento completo)**. Aunque es otro proyecto, es el mejor ejemplo metodológico de localización de divergencia ROCm↔CPU:
  - Resultado: divergencia **rampante y suave** (no un salto), `rel_l2` final ≈ 2.6–2.8e-02, consistente con una caminata aleatoria bf16 (~1.03–1.11× lo inevitable).
  - **Las 16 capas de atención completa cargan 84%/74%/79% de la varianza** frente a las 48 capas GDN; dentro de la capa, "the full-attention mixer **amplifies the incoming relative error by 2.160** where the GDN mixer returns 1.500".
  - "The right reading is that the attention block is the one with the most bf16 stores and **two reduction orders over a paged KV cache**, not that it is wrong."
  - Piso de run-to-run = **exactamente cero** por tier, pero la divergencia cross-tier es real.
  - Lección: token-exactness entre tiers **no está disponible** en bf16; solo cambia el token cuando el margen del modelo es menor que el delta.
  - Menciona un caso previo `gfx1100` 0.8B con divergencia **localizada** (P1) donde `fa0_q` tenía `rms-rel 1.196` y la causa era "a kernel dispatched on the source dtype instead of the output dtype" — precedente de bug localizado real.

---

## 4. Vía Ollama

### ollama#5321 — "Llama3: Generated outputs inconsistent despite seed and temperature"
- URL: https://github.com/ollama/ollama/issues/5321 — **Estado: ABIERTO**, 22 comentarios.
- **VERIFICADO**. Síntoma idéntico al problema reportado:
  - "the output from the **first execution will be random**, whereas the output of the second execution and all subsequent executions will be generated consistently deterministic."
  - "the generated outputs differ **across those different OS**... on Windows, this code produced a different consistent deterministic output than Ubuntu did."
  - Requiere fijar `num_ctx` "otherwise slightly random output".
- **Causa raíz no declarada en el cuerpo**; sigue abierto.

### ollama#16197 — "Bug? temperature=0 produces different output on first run vs subsequent runs"
- URL: https://github.com/ollama/ollama/issues/16197 — **Estado: ABIERTO** (creado 2026-05-17), etiqueta `bug`. 2 comentarios.
- **VERIFICADO**. Con `temperature=0`, qwen2.5:7b, GPU NVIDIA:
  - Epoch 1 diverge; epochs 2/3 byte-idénticos.
  - **Los propios logprobs difieren** entre la primera llamada y las siguientes (ej. `top_1=" in" [-0.200212]` vs `top_1=" log" [-0.118924]`), lo que el autor interpreta como "a different internal model state on the first call, not just different sampling behaviour."
  - El autor señala que `greedy()` es argmax puro, así que la causa no es el sampler.

### ollama#1812 — "Proper calculation of the KV cache size inside of `gpu::NumGPU()` instead of the 3/4 magic number"
- URL: https://github.com/ollama/ollama/issues/1812 — **SOLO TÍTULO**. Evidencia de que la estimación de capas a offloadear usa heurísticas (número mágico 3/4), lo que puede hacer que **`ngl` varíe entre arranques** según VRAM libre. Esto es directamente relevante: en #2838 y #13280, cambiar `ngl` cambia el régimen.

### Guía de determinismo de Ollama
- https://makandracards.com/makandra/626358-ollama-generate-deterministic-results — **VERIFICADO**. Solo recomienda `temperature: 0` + `seed` fijo. No aborda el problema de multi-proceso/multi-régimen. La doc oficial referenciada: https://github.com/ollama/ollama/blob/main/docs/api.md#chat-request-reproducible-outputs

### Setup gfx1103 (mismo iGPU que el usuario)
- https://github.com/johnsonfarmsus/ollama-rocm-gfx1103-ubuntu — **VERIFICADO (descripción)**. "Native ROCm acceleration for Ollama on the AMD Radeon 780M iGPU (gfx1103)... builds ollama-for-amd from source, applies **three small ml/device.go patches**, and installs Fedora 43's prebuilt gfx1103 Tensile kernels into the system rocBLAS."
- **Muy relevante**: (a) existen parches específicos de `ml/device.go` para gfx1103 — la heurística de asignación de capas/VRAM se modifica a mano; (b) se instalan kernels **Tensile** específicos de gfx1103 en rocBLAS — la biblioteca de kernels cambia según el sistema.

---

## 5. Lista rankeada de mecanismos candidatos para "saltos entre regímenes estables por reinicio"

Ordenada por (a) evidencia directa en las fuentes y (b) capacidad de explicar un **régimen estable por proceso** (no ruido dentro del proceso).

**1. Selección de kernel dependiente del entorno en la BLAS externa (rocBLAS/hipBLASLt), con autotuning/caché por proceso.**
- Evidencia: #10197 ("the kernels HIP provides as a replacement for cuBLAS GEMM are not deterministic, likely due to atomic adds"); #14727 ("rocBLAS is not deterministic by default", `ROCBLAS_DEFAULT_ATOMICS_MODE`); PR #16457 ("best algo solution", hipBLASLt deshabilitado por defecto en no-CDNA3).
- Por qué explica regímenes estables: la heurística de selección de algoritmo depende de VRAM libre, orden de asignación y caché de autotuning **al inicio del proceso**. Un proceso que elige el kernel A produce siempre el resultado A; otro que elige B produce B. Determinista dentro del proceso, distinto entre procesos.
- Determinismo observado en CPU confirma que no es el grafo de llama.cpp.

**2. El kernel FlashAttention rocWMMA (RDNA3) — no determinista, ya eliminado.**
- Evidencia directa y explícita: #14727, comentario de IMbackK: "real, unexpected non-determinism in the **rocwmma fattn kernel**". Y la prueba A/B de broadbit-hu: sin rocWMMA → determinista; con rocWMMA → A-B-A-B por reinicio. Eliminado en PR #26046.
- **Acción inmediata para el usuario**: comprobar si su build de Ollama usa `GGML_HIP_ROCWMMA_FATTN=ON`. Si sí → **causa confirmada y con fix conocido** (rebuild sin rocWMMA, o actualizar a un llama.cpp con #26046).
- Nota: gfx1103 (RDNA3) es exactamente el target de rocWMMA FATTN (`GGML_HIP_ROCWMMA_FATTN` cubre CDNA y RDNA3+).

**3. Tamaño de batch/ubatch distinto → distinto orden de reducción en FA.**
- Evidencia directa: #2838 (comentario de ivich123), con logits medidos: la primera petición evalúa N tokens, las siguientes reutilizan caché y evalúan 1. "CUDA Flash Attention is not bit-identical when computing attention with different batch sizes."
- Por qué explica regímenes: el tamaño efectivo de batch depende de si el prefijo está cacheado y de la heurística `num_batch`/`num_ctx` de Ollama, que a su vez depende de VRAM libre al arrancar (ver candidato 6). Un arranque con más VRAM libre → otro `n_batch` → otro orden de reducción.
- Workaround oficial: `--no-cache-prompt` (ggerganov, PR #22224); en Ollama, `num_ctx` fijo y evitar reutilización de caché.

**4. MMQ vs BLAS: selección por arquitectura + spills de VGPR dependientes del compilador.**
- Evidencia: #13280 (race condition real en MMQ → fix #13294/#13299); #29910 y #29536 (spills masivos en gfx1100/gfx1200, 1387 y 2041 VGPRs, dependientes del unroll y del compilador LLVM); build.md: `GGML_CUDA_FORCE_MMQ` afecta explícitamente a RDNA3+.
- Por qué explica regímenes: el binario compilado fija un unroll y una ruta; pero en runtime la elección MMQ-vs-BLAS depende de la CC y del tamaño de batch (`ggml_cuda_should_use_mmq`). Distintos `n_batch` → distinta ruta → distinta aritmética.
- Nota: en #14727 y #10197 forzar MMQ **no** bastó, así que probablemente es co-causa, no causa única.

**5. Captura/reutilización de CUDA/HIP graphs.**
- Evidencia: build.md (env `GGML_CUDA_DISABLE_GRAPHS`); #28404 (fallos por reutilización de grafo, arreglado por `GGML_CUDA_DISABLE_GRAPHS=1`); paper Silent Hyperparameter identifica "CUDA graphs" como causa de divergencia; #28495 usa `GGML_CUDA_DISABLE_GRAPHS=1` en todos los brazos.
- Por qué explica regímenes: un grafo capturado congela el tamaño de batch y el orden de kernels de la primera ejecución. Qué se captura depende de la primera petición tras el arranque → régimen por proceso. El usuario de #14727 describe literalmente "the first call after starting llama-server consistently responds the same" y luego A-B-A-B.
- Acción: `GGML_CUDA_DISABLE_GRAPHS=1` como experimento de diagnóstico.

**6. Heurísticas de offload de capas (`ngl`) de Ollama dependientes de VRAM libre al arrancar.**
- Evidencia: ollama#1812 (cálculo de KV cache con "3/4 magic number"); johnsonfarmsus/ollama-rocm-gfx1103-ubuntu ("three small ml/device.go patches"); #2838 y #13280 muestran que **`ngl` cambia el régimen** (ngl 0/1/2 determinista o distinto; ngl 3+ divergente).
- Por qué explica regímenes: la VRAM libre al arrancar (que varía con lo que esté corriendo en el sistema, el WM, otro proceso usando el iGPU) determina cuántas capas van a GPU. Distinto reparto → distinta ruta por capa → distinto orden de reducción acumulado. **Muy plausible en un iGPU 760M con memoria compartida.**

**7. Split mode / tensor parallelism y orden de reducción.**
- Evidencia: **DÉBIL para este caso**. La mayoría de evidencia es multi-GPU (#29868 usa `--split-mode tensor` en 2×RX 9060 XT). El usuario tiene **una sola GPU** (iGPU), así que `--split-mode` no aplica directamente. El paper Silent Hyperparameter y #2609.25624 sí respaldan la no-asociatividad de reducción en general. Lo dejo bajo en el ranking.

**8. Condición de carrera / bug real localizado (precedente).**
- Evidencia: #13280 (race en MMQ, arreglado); la spec de vllm.cpp menciona un caso gfx1100 donde `fa0_q` divergía por "kernel dispatched on the source dtype instead of the output dtype".
- Por qué explica regímenes: una carrera puede resolverse de forma distinta según el *timing* de arranque (carga del modelo, compilación JIT de kernels, contención de memoria). Menos probable que los anteriores pero no descartable, y sería el escenario "arreglable".

**9. Inestabilidad de hardware / throttling del iGPU.**
- Evidencia: #13280, JohannesGaessler sugiere `nvidia-smi --lock-gpu-clocks` por bit flips. En el caso reportado **no cambió nada**, pero es un control a descartar.
- Para un iGPU 760M con memoria compartida y posible throttling térmico/power, es un control barato de hacer.

---

## 6. Resumen accionable (lo que el padre debería hacer a continuación)

1. **Primero descartar/inculpar rocWMMA FA**: identificar con qué `GGML_HIP_ROCWMMA_FATTN` fue compilado el binario de Ollama. Es la única causa con declaración explícita de maintainer ("real, unexpected non-determinism in the rocwmma fattn kernel") y ya fue eliminada upstream (PR #26046). gfx1103 es RDNA3, target exacto de ese kernel.
2. **Fijar el entorno de ejecución**: `num_ctx` explícito, `num_batch`/`num_predict` explícitos, `--no-cache-prompt` equivalente, `GGML_CUDA_DISABLE_GRAPHS=1`, y fijar `ngl` manualmente en vez de dejar que Ollama lo estime. Cualquier variación de VRAM libre al arrancar cambia el reparto de capas.
3. **Protocolo de evidencia**: por cada arranque, registrar (a) hash del binario de llama.cpp/ggml-hip embebido en Ollama, (b) `n_gpu_layers` efectivo y VRAM libre reportada, (c) `n_batch`/`n_ubatch`, (d) si rocWMMA está activo, (e) `n_probs>0` para capturar el primer token divergente. La spec de vllm.cpp es el modelo metodológico a seguir: comparar por capa, buscar discontinuidad vs rampa, y medir el piso run-to-run.
4. **No esperar** que `temperature=0` + seed resuelva el problema: hay consenso explícito (ggerganov, JohannesGaessler, IMbackK, tommasocerruti) de que eso solo elimina la aleatoriedad del *sampling*, no la del *cómputo*.

## 7. Limitaciones de esta investigación

- **GitHub REST API alcanzó el rate limit** al final. No pude recuperar el cuerpo de PR #15454, #26046 ni #22224 vía API; para esos me apoyo en títulos/diffs vía búsqueda (marcados como SOLO TÍTULO donde corresponde).
- **No pude recuperar el paper exacto de la frase "not a pervasive noise problem, but a localized..."**. El id `2606.21023` apunta a un paper distinto (HEAL). Lo dejo explícitamente como no verificado en lugar de adivinar.
- Los PDFs en `arxiv.org/pdf/...` **no son recuperables** con la herramienta `web_fetch` (error: unsupported content type "application/pdf"); usé las páginas `/abs/` y `/html/`.
- No verifiqué el código fuente de Ollama (`ml/device.go`, `memory.go`) directamente: la búsqueda de código de GitHub requiere autenticación (HTTP 401). Todo lo relativo a heurísticas de Ollama está marcado como inferencia a partir de issues/títulos.
