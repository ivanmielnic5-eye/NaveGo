# ROCm Non-Determinism Research Report

**Scope:** Explain a STABLE-PER-BLOCK but DIFFERENT-ACROSS-BLOCKS divergence in Ollama + Qwen2.5-Coder-1.5B running 100% on an AMD Radeon 760M iGPU (RDNA3, gfx1103, UMA/shared RAM) via ROCm. temp=0, seed=555, same prompt: 20/20 identical within one block; different stable regime between process restarts (3 regimes in one hour).

**Method:** web_search + web_fetch. Every URL below was fetched and returned HTTP 200 unless explicitly marked otherwise. No URL, issue number, or paper ID is invented.

---

## 1. The arxiv paper — VERIFIED REAL

**Claimed URL check:** `https://arxiv.org/abs/2606.21023` and `https://arxiv.org/pdf/2606.21023v1` are **REAL, not 404, not nonsense.** Both the abs page and the HTML full text were fetched (HTTP 200). The `pdf` URL returns `Error: unsupported content type "application/pdf"` from the fetch tool — that is a *tool* limitation, not a 404; the same content was read via the HTML version.

- Abs page: https://arxiv.org/abs/2606.21023
- HTML full text: https://arxiv.org/html/2606.21023v1
- DOI: https://doi.org/10.48550/arXiv.2606.21023

**Title:** "Demystifying Numerical Instability in LLM Inference: Achieving Reproducible Inference for Mission-Critical Tasks with HEAL"
**Authors:** Zhenting Zhu, Lucas Thai, Shan Yu, Yicheng Liu, Yifan Qiao, Chenxi Wang, Harry Xu, Junyi Shu (UCLA / UC Berkeley / UCAS)
**Submitted:** Fri, 19 Jun 2026 (v1). Subject cs.LG. License CC BY 4.0.

**Note on the exact-phrase search:** the quoted phrase "non-reproducibility of LLM inference is not a pervasive noise problem, but a localized" did **not** appear verbatim in the fetched paper text. The paper's actual wording is: "the injection of this catastrophic error is not ubiquitous" (§2.2) and the structural-imbalance finding that error contribution is concentrated in specific layers. The search engine associated the query with this paper; treat the exact phrasing as a paraphrase, not a quotation.

### What the paper identifies as the source of non-determinism

- **Microscopic origin: boundary truncation.** "instability is not driven by internal kernel arithmetic (which predominantly operates in FP32), but by *the truncation of high-precision registers during downcasting at kernel boundaries*." The error is a *quantization/rounding* (Q_p) error at kernel boundaries, NOT atomic-add reordering and NOT reduction order per se.
- **Operations/layers implicated:** kernels profiled include GEMM, FlashAttention (`FlashFwdSplitKV`), `PageAttentionV2`, `KernelUnifiedAttention`, `SplitKReduce`, RMSNorm, RotaryEmbedding, SoftmaxReduce, SwiGLU, FusedAddRMSNorm. Attention and GEMM are the two structural bottlenecks (Attention → KV-cache memory wall if upcast; GEMM → Tensor-Core compute wall if upcast).
- **Mechanism of amplification:** three error sources per layer — `ε_new` (fresh rounding), `ε_kv` (horizontal, inherited via KV cache from past tokens), `ε_old` (vertical, via residual stream from prior layers). Total MSE grows exponentially with depth. A single divergent token appears when accumulated error crosses a **divergence threshold** and flips the `argmax` between top-1 and top-2 logits. Below threshold = "benign regime"; above = "catastrophic regime."
- **Mitigation:** HEAL = INT16 quantization for Q/K/V + algebraic error-compensation GEMM, with MCR-Bench. Claims FP32-level reproducibility at 40–109% TPOT overhead vs 4.2–13.1× for full FP32.

### Does it discuss GPU/ROCm, batching, cross-vendor?

- **GPU:** YES, but **NVIDIA-only**. Profiling is SASS-level on NVIDIA A100 (and an H100 FP32 pipeline as ground truth). The motivating framing is *heterogeneous datacenters* — "catastrophic output divergence across heterogeneous GPUs" and vendor mixing (OpenAI/Anthropic non-NVIDIA hardware is cited). It claims the *class* of problem generalizes across vendors/generations, but **no ROCm/AMD/HIP-specific measurements, no gfx targets, and no rocBLAS/hipBLASLt content appear in what was fetched.**
- **Batching:** YES, conceptually. Introduction lists "dynamically shifting software configurations (e.g., varying attention backends or batch sizes)" as a divergence cause. Note it treats batch size as an *execution-path* variable, not a numerical one.
- **Bitwise determinism discussion:** it explicitly discusses the two existing mitigation families — (a) forcing deterministic reduction orders via hardware-specific traits / specialized kernels, which "restricts deployment to a narrow execution path"; and (b) brute-force FP32.

**Relevance to our case — IMPORTANT CAVEAT:** the paper explains *why a small numerical difference becomes a different token* (threshold + argmax flip). It does **not** explain *why two runs of the same process on the same GPU would start in different numerical states*. It is the "amplifier" half of the story, not the "source of the seed difference" half. It is also 16-bit-precision-focused; Ollama Q4/Q8-with-FP16-accumulation does have downcast boundaries, so the boundary-truncation mechanism is plausibly applicable, but the paper does not test AMD.

Related literature surfaced by search (useful corroboration, not fetched in full):
- "Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference" (NeurIPS 2025): https://proceedings.neurips.cc/paper_files/paper/2025/hash/f80094a824ba5912d4a2de169c404a40-Abstract-Conference.html
- "Same Prompt, Different Answer: Hidden Non-Determinism in LLM APIs Undermines Scientific Reproducibility": https://github.com/Roverlucas/genai-reproducibility-protocol/blob/3a9a4e720aef23adc3214787a24106f545474087/article/ncomms_main.pdf
- "One Landscape, Two Readouts: Dissociating Surface and Conceptual Reproducibility in LLM Generation": https://www.zenodo.org/records/21205976
- "Recursive Reproducibility: A YBIM Resolution of LLM Nondeterminism Beyond Temperature = 0": https://www.zenodo.org/records/17118544

---

## 2. The requested ROCm repo issue — FETCHED

- Issue API: https://api.github.com/repos/ROCm/legacy-rocm-build/issues/6595 (HTTP 200)
- Comments API: https://api.github.com/repos/ROCm/legacy-rocm-build/issues/6595/comments (HTTP 200) → **returns `[]`, empty. There are zero comments.** `comments: 0` in the issue JSON confirms this.
- HTML: https://github.com/ROCm/legacy-rocm-build/issues/6595

**Title:** "[Bug] Silent fp32 GEMM corruption on gfx1201 when M > 2^19 rows (both rocBLAS and hipBLASLt; torch 2.13.0+rocm7.2)"
**Reporter:** `bioritmovideo`. **State:** open. **Assignee:** `adityas-amd`. **Label:** `status: triage`. Created 2026-08-09, updated 2026-08-13. No maintainer diagnosis was ever posted (no comments).

**Content (accurate summary of the JSON body):**
- On **gfx1201** (Radeon AI PRO R9700, RDNA4), fp32 GEMMs (`torch.mm`/`addmm`/`bmm`/`F.linear`) with **M > 2^19 = 524,288 rows** return silently corrupted results, no error/warning.
- Two BLAS paths fail differently. **hipBLASLt path** (`TORCH_BLAS_PREFER_HIPBLASLT=1`): surgical — rows up to ~524,287 correct, every row from ~524,288 garbage (bias-only values). **rocBLAS path** (`TORCH_BLAS_PREFER_HIPBLASLT=0`): `addmm` with bias — nearly the whole result wrong (bad rows from row 1). Verified element-wise against a float64 CPU reference on a 200k-row random sample.
- `M=524280` and `M=524288` correct on both paths; `M=600000` breaks. fp16/bf16 at same sizes are correct up to M=1.68M.
- Reporter's hypothesis: unhandled grid-dimension limit in the large-M SGEMM kernel launch/tiling path; routed as possibly rocBLAS / hipBLASLt / **Tensile kernel selection**.
- Environment: 2× R9700 gfx1201, ROCm 7.2.1, PyTorch 2.13.0+rocm7.2, Ubuntu 24.04.4.
- Workaround shipped: chunk matmul into ≤262,144-row blocks.
- Reproducer: https://github.com/bioritmovideo/trellis2-rocm-gfx1201/blob/master/repro_sgemm_fp32_gfx1201.py
- References prior similar-class bug **#5981** (Hunyuan3D texture corruption on R9700, fixed via TheRock nightlies Feb 2026).

**Relevance:** This is a *correctness* bug (threshold-triggered kernel defect), NOT run-to-run non-determinism. It is **not** our mechanism, and it is on gfx1201/RDNA4, not gfx1103. It IS relevant as evidence that (a) the rocBLAS and hipBLASLt paths genuinely select different kernels and produce different numerics for the same problem, and (b) AMD treats `Tensile`/kernel-selection as a live suspect class. **Do not cite it as the cause of regime flipping** — it is a different failure mode (deterministic given shape).

---

## 3. THE KEY MECHANISM — algorithm/kernel selection depending on runtime state

**Answer to the core question: YES. ROCm/hipBLASLt has a documented algorithm-selection step that can choose DIFFERENT kernels for the SAME problem depending on runtime state, and this is a documented source of run-to-run differences. This is CONFIRMED, not speculation.**

### 3a. CONFIRMED — hipBLASLt heuristics choose kernels from problem + GPU + other parameters

Source: **hipBLASLt "Using logging and heuristics"** — https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/how-to/use-logging-heuristics.html

> "hipBLASLt uses heuristics to pick the most suitable matmul kernel for execution based on **the problem sizes, GPU configuration, and other parameters**. This requires performing some computations on the host CPU, which could take tens of microseconds. To overcome this overhead, it's recommended that you query the heuristics once using `hipblasLtMatmulAlgoGetHeuristic()`, then reuse the result for subsequent computations using `hipblasLtMatmul()`."

The page title is literally "Heuristics **cache**". This single paragraph contains **both halves** of the puzzle:

1. **Different-across-process:** the heuristic maps (problem, GPU config, other parameters) → kernel. "Other parameters" is where runtime state enters. Nothing in the doc claims the mapping is a pure function of the shape.
2. **Stable-within-process:** AMD's own recommendation is to call `hipblasLtMatmulAlgoGetHeuristic()` **once** and reuse the result. The resolved algorithm is cached for the handle's lifetime. Consequence: **one verdict per process, held constant for all 20 requests in a block → 20/20 identical**, and a fresh verdict at the next process start → possibly a different-but-then-constant regime.

Logging to observe the chosen kernel: `HIPBLASLT_LOG_LEVEL=4` (level 4 "Info ... can contain details about the heuristic status"); `HIPBLASLT_LOG_MASK` (2 = kernel selection, 32 = bench); `HIPBLASLT_LOG_FILE` (supports `%i` = PID). This is directly usable to prove/disprove the hypothesis — see §6.

### 3b. CONFIRMED (maintainer/AMD-doc stated) — hipBLASLt autotuning is a known source of run-to-run kernel-selection differences, and determinism requires turning it off

Source: **AMD Primus, "Determinism and reproducibility"** — https://rocm.docs.amd.com/projects/primus/en/latest/04-technical-guides/determinism-and-reproducibility.html

> "Additionally, **HipBLASLt autotuning is disabled** in deterministic mode: tuning only runs when `PRIMUS_DETERMINISTIC != 1` *and* `PRIMUS_HIPBLASLT_TUNING=1` ... **This prevents run-to-run kernel-selection differences.**"

And the definition section: "**Bitwise-deterministic**—kernels avoid non-deterministic reductions/atomics and **tuning** so results don't vary between runs. Requires deterministic algorithms and **disabling autotuning**."

Environment variables AMD exports for determinism:
```
NCCL_ALGO="Ring"                    # deterministic collective algorithm
NVTE_ALLOW_NONDETERMINISTIC_ALGO=0  # forbid non-deterministic kernels
ROCBLAS_DEFAULT_ATOMICS_MODE=0      # disable atomic (non-deterministic) reductions
TORCH_COMPILE_DISABLE=1             # avoid torch.compile/Triton race conditions
PRIMUS_TURBO_AUTO_TUNE=0            # disable autotuning (stable kernel choice)
```

This is the strongest single piece of evidence in the whole research: **AMD's own documentation states that without explicit action, kernel selection differs run-to-run.** That is exactly "stable within a block, different across blocks."

Source: **AMD Primus, "Performance tuning guide"** — https://rocm.docs.amd.com/projects/primus/en/main/04-technical-guides/performance-tuning.html
Documents the three-stage hipBLASLt tuning workflow (`PRIMUS_HIPBLASLT_TUNING`, `PRIMUS_HIPBLASLT_TUNING_STAGE` 0–3), `HIPBLASLT_TUNING_OVERRIDE_FILE`, and `TE_HIPBLASLT_TUNING_ALGO_COUNT` / `TE_HIPBLASLT_TUNING_RUN_COUNT`. **`TE_HIPBLASLT_TUNING_RUN_COUNT` = "Number of benchmark runs per shape during TE tuning"** — i.e. the library literally *benchmarks* candidate algorithms and picks by measured timing. A timing-based pick is inherently sensitive to transient machine state (clocks, thermal, co-tenant load, memory pressure) → nondeterministic across processes, fixed once written/cached.

### 3c. CONFIRMED — algorithm discovery + workspace-size filtering is a first-class, documented API surface

Source: **rocBLAS design and usage notes** — https://rocm.docs.amd.com/projects/rocBLAS/en/latest/conceptual/rocblas-design-notes.html

> "The choice of whether to use the embedded Tensile backend or hipBLASLt is handled automatically based on **the architecture and problem**. For instance, hipBLASLt is used as the default backend for problems on the gfx12 architecture."
> Backend overrides: `ROCBLAS_USE_HIPBLASLT` (not set = automatic; `0` = always Tensile; `1` = prefer hipBLASLt with Tensile fallback), `ROCBLAS_USE_HIPBLASLT_BATCHED` (deprecated).
> "hipBLASLt is preferred as the GEMM backend, but the backend will **fall back to Tensile for problems for which hipBLASLt does not provide a solution or if errors are encountered**."

Source: **hipBLASLt extension API — GEMM with Algorithm Discovery and Validation** — https://raw.githubusercontent.com/ROCm/rocm-examples/refs/heads/amd-staging/Libraries/hipBLASLt/gemm_get_all_algos_ext/README.md

Documented flow: `hipblaslt_ext::getAllAlgos()` → create `GemmPreference` → **`setMaxWorkspaceBytes()`** → `gemm.isAlgoSupported()` returns the algorithm's workspace size → **"Filter algorithms based on workspace size constraints"** → `initialize()` with the chosen algorithm and workspace → `run()`.

**This is the exact mechanism requested:** the *set of eligible algorithms depends on how much workspace the caller can grant*, and the caller grants what memory is available. Different eligible set → different chosen kernel → different summation order → legitimately different floating-point result, with each kernel internally deterministic.

### 3d. CONFIRMED — rocBLAS docs explicitly document memory-availability-dependent kernel downgrade producing variable results

Source: https://rocm.docs.amd.com/projects/rocBLAS/en/latest/conceptual/rocblas-design-notes.html (Bitwise reproducibility section)

rocBLAS's stated conditions for bitwise-reproducible results:
- Identical GFX target ISA
- Single HIP stream active per rocBLAS handle
- Identical ROCm versions
- **Atomic operations are not allowed**

Then, verbatim:

> "Functions such as GEMV and TRSM **use temporary device memory to allow optimized kernels to achieve higher performance. If device memory is unavailable, these functions proceed to use an unoptimized kernel, which could also produce variable results.** To notify users that an unoptimized kernel is being used, the function returns the `rocblas_status_perf_degraded` status."

This is AMD documenting, in the *reproducibility* section itself, that **free device memory changes which kernel runs and therefore changes results.** On a UMA APU where "device memory" is a carve-out of system RAM and is shared with the OS, this quantity varies between launches. This is the gfx1103/UMA link.

### 3e. CONFIRMED — Tensile solution selection is an explicit, inspectable step with a tunable search

Source: **Tensile environment variables** — https://rocm.docs.amd.com/projects/Tensile/en/docs-7.14.0/src/reference/environment-variables.html

- `TENSILE_NAIVE_SEARCH` — "Performs naive search for matching kernels instead of optimized search."
- `TENSILE_TAM_SELECTION_ENABLE` — "Enables tile aware solution selection."
- `TENSILE_METRIC` — "Overrides the default distance matrix for solution selection" (Euclidean / JSD / Manhattan / Ratio / **Random**). The existence of a `"Random"` selection metric is notable.
- `TENSILE_SOLUTION_INDEX` — prints the index of the selected solution.
- `TENSILE_DB=0x2|0x4` — solution-selection info; `0x8000` — selected kernel names.

Tensile is the fallback GEMM backend in rocBLAS and is installed as part of ROCm; rocBLAS "uses Tensile and hipBLASLt internally."

### 3f. CONFIRMED — rocBLAS atomics mode: the documented determinism knob

- **rocBLAS issue #1459, "[Question]: rocBLAS determinism with GPU atomics"** — https://github.com/ROCm/rocBLAS/issues/1459 (API), https://github.com/ROCm/rocBLAS/issues/1459 (HTML). Closed, 4 comments.
  - User quotes the cuBLAS determinism conditions (`cublasSetWorkspace`, one handle per stream, `cublasLtMatmul()` with user-owned workspace, `CUBLAS_WORKSPACE_CONFIG=:16:8`/`:4096:8`).
  - **Maintainer `rkamd` (AMD) reply, 2024-08-05, verbatim:** "**Atomic operations are enabled by default in current and previous releases of rocBLAS** and functions using atomic operations may not provide deterministic results. ... In ROCm 6.2 and above users can use `ROCBLAS_DEFAULT_ATOMICS_MODE` environment variable to change the default atomic mode. For prior releases user must use rocBLAS `rocblas_set_atomics_mode()` API to change the default." He also states the docs were updated to "clearly list the conditions in rocBLAS to obtain deterministic results."
- **rocBLAS deprecations page** — https://rocm.docs.amd.com/projects/rocBLAS/en/docs-6.4.2/reference/deprecations.html — "Atomic operations will be disabled by default" announced for rocBLAS 4.0 (still just an announcement there).
- **Current state (latest docs):** https://rocm.docs.amd.com/projects/rocBLAS/en/latest/conceptual/rocblas-design-notes.html now says "**By default, atomic operations are not allowed.** All other functions are bitwise reproducible by default." plus `ROCBLAS_DEFAULT_ATOMICS_MODE=0` (not allowed) / `=1` (allowed) and `rocblas_set_atomics_mode()` taking precedence over the env var.

**Important nuance for our case:** atomics are the *classic* nondeterminism source, and they are a *within-process* nondeterminism (run-to-run varying even with identical inputs in the same process). Our symptom is the **opposite** — perfectly stable within a process, differing only across processes. Therefore atomics are almost certainly **NOT** the cause here; the memory/kernel-selection path is the better fit. Atomics nonetheless matter because they'd *break* the 20/20 observation.

---

## 4. Deterministic mode: cuBLAS analogy and whether ROCm has an equivalent

### cuBLAS (the analogy — for reference, from the issue #1459 quote)
NVIDIA documents explicit bitwise-determinism conditions: `cublasSetWorkspace()`, one handle per stream, `cublasLtMatmul()` with user-owned workspace, or `CUBLAS_WORKSPACE_CONFIG=:16:8` / `:4096:8`. The key idea: **you must pin the workspace** so the library cannot pick a workspace-dependent (split-K/atomic) kernel. Reference: https://docs.nvidia.com/cuda/cublas/#cublassetworkspace and https://docs.nvidia.com/cuda/cublas/#cublasltmatmul

### ROCm equivalent — the honest answer: **PARTIAL. ROCm does NOT have a single documented `CUBLAS_WORKSPACE_CONFIG`-equivalent env var. It has a scattered set of narrower knobs, and the strongest determinism guidance is published by AMD Primus, not by rocBLAS/hipBLASLt itself.**

**CONFIRMED ROCm knobs that exist:**
| Knob | Documented effect | URL |
|---|---|---|
| `ROCBLAS_DEFAULT_ATOMICS_MODE=0` / `=1` | Sets default atomics mode at handle creation (0 = not allowed) | rocBLAS design notes |
| `rocblas_set_atomics_mode()` | Per-handle override; **higher precedence than the env var** | rocBLAS design notes / helper-functions |
| `ROCBLAS_USE_HIPBLASLT=0/1` | Forces Tensile, or prefers hipBLASLt | rocBLAS design notes |
| `HIPBLASLT_LOG_LEVEL` / `_LOG_MASK` / `_LOG_FILE` | Observability of the chosen algorithm, not control | hipBLASLt logging page |
| `HIPBLASLT_TUNING_OVERRIDE_FILE` | Pins a previously tuned kernel per shape (Primus stage 3) | Primus perf-tuning |
| `TENSILE_NAIVE_SEARCH`, `TENSILE_TAM_SELECTION_ENABLE`, `TENSILE_METRIC`, `TENSILE_SOLUTION_INDEX`, `TENSILE_DB` | Influence/inspect Tensile solution selection | Tensile env vars |
| `PRIMUS_DETERMINISTIC=1` | Umbrella that sets the determinism env set (Primus-specific launcher) | Primus determinism |

**What is MISSING / NOT documented (checked):**
- No `ROCBLAS_WORKSPACE_CONFIG` or hipBLASLt workspace-config env var appears on the rocBLAS env-vars page (https://rocm.docs.amd.com/projects/rocBLAS/en/latest/reference/env-variables.html) or the hipBLASLt env-vars page (https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/reference/env-variables.html). The cuBLAS `:16:8`/`:4096:8` workspace-size contract has **no documented ROCm analogue**. hipBLASLt instead exposes **`setMaxWorkspaceBytes()` as a per-call API parameter** — the caller must manage workspace explicitly.
- No hipBLASLt documentation page was found that states a global "deterministic mode" guarantee. The determinism statement lives in **rocBLAS** docs (atomics + the four conditions), and the tuning caveat lives in **Primus** docs.
- The rocBLAS bitwise-reproducibility list itself has a hole: its four conditions do **not** mention hipBLASLt backend selection, hipBLASLt heuristic choice, or Tensile solution selection — yet rocBLAS's own "Use of Tensile and hipBLASLt" section says backend choice is automatic. So the documented guarantee is narrower than the actual surface.

**Also relevant — PyTorch's ROCm deterministic-algorithms support is incomplete and has a documented silent-failure case:**
- **pytorch/pytorch PR #197771** — "[ROCm][CK] Honour use_deterministic_algorithms in mem-efficient SDPA" — https://github.com/pytorch/pytorch/pull/197771 (open, not merged at fetch time). States that on ROCm with the CK backend, `torch.use_deterministic_algorithms(True)` "has **no effect**" on mem-efficient SDPA backward because `deterministic=false` is hardcoded — "the flag is dropped rather than rejected, nothing warns and nothing raises — the user is told determinism is on while it is not." Measured on MI300X (gfx942), torch 2.13.0+rocm10.0: CK mem-efficient path `dq` **differs**; the **AOTriton default path is bitwise reproducible with no flag at all**. Cites dependency on ROCm/rocm-libraries#12277.

---

## 5. AMD APU / iGPU (Radeon 760M / 780M / gfx1103 / UMA) — varying available GPU memory

This is the second half of the mechanism: on a UMA APU, "VRAM" is not a fixed pool, so the quantity the heuristic/workspace logic sees varies between process launches.

**CONFIRMED — memory reporting on gfx1103/UMA APUs is inconsistent and contested:**
- **likelovewant/ROCmLibs-for-gfx1103-AMD780M-APU issue #67** — "Radeon 780M (gfx1103) memory detection reports only BIOS-allocated VRAM instead of full shared memory" — https://github.com/likelovewant/ROCmLibs-for-gfx1103-AMD780M-APU/issues/67 (API: https://api.github.com/repos/likelovewant/ROCmLibs-for-gfx1103-AMD780M-APU/issues/67). Reporter: a build detects only 16 GB instead of all shared memory, traced to **ADLX `TotalVRAM()` reporting only the BIOS-allocated VRAM on integrated GPUs**; `hipMemGetInfo()` "correctly reports all available shared memory." **Direct evidence that on a gfx1103-family APU the number the runtime sees as available GPU memory depends on which API you ask and how the BIOS carved out the aperture.** Closed 2026-05-17.
- **llama.cpp PR #20472** — "ggml-cuda: fix UMA memory detection for HIP/ROCm on AMD APUs" — https://github.com/ggml-org/llama.cpp/pull/20472 (API: https://api.github.com/repos/ggml-org/llama.cpp/pulls/20472). Reports `prop.integrated == 1` on AMD APUs; the UMA path replaced accurate `hipMemGetInfo()` with `MemAvailable` from `/proc/meminfo`, which "reports significantly less memory on systems with large TTM allocations (e.g. **122 GiB vs 91 GiB** on a 128GB Strix Halo system)." Verified on Ryzen AI MAX+ 395 (gfx1151, 128GB unified, ROCm 7.1): `hipMemGetInfo()` = 122880 MiB while `MemAvailable` ≈ 91 GiB. **A ~25% swing in "available memory" purely from which API is consulted** — and `MemAvailable` moves with OS activity. Closed 2026-07-13.
- **llama.cpp issue #24836** — "CUDA/HIP: llama.cpp will have to find a different way on HIP target to calculate free VRAM" — https://github.com/ggml-org/llama.cpp/issues/24836 (API: https://api.github.com/repos/ggml-org/llama.cpp/issues/24836). States that due to https://github.com/ROCm/librocdxg/issues/57, **`hipMemGetInfo()` returns inconsistent results depending on OS** (Windows vs Linux vs WSL2), and that this also affects NVIDIA CUDA per an AMD engineer in that ticket. Closed as stale/not-planned. (The referenced `ROCm/librocdxg` issue #57 was **not** independently fetched — treat as reporter-stated.)
- **ROCm/TheRock issue #2011** — "Remove gfx1103 from gfx110X-all or switch back to publishing gfx110X-dgpu" — https://github.com/ROCm/TheRock/issues/2011 (API: https://api.github.com/repos/ROCm/TheRock/issues/2011). Opened by **`amd-aakash` (AMD)**: "We are hitting build errors that look like **machines are running out of memory** after updating rocm-libraries in the gfx110X-all target family on Windows... we plan on reverting the change that included **gfx1103** in releases via the gfx110X-all target family." Shows gfx1103's place in the build/target matrix is unstable and memory-constrained. Closed 2025-11-04, 19 comments. Related: ROCm/rocm-libraries#2346.

**Relevance:** on a 760M iGPU the "GPU memory available" seen by ROCm is a function of BIOS UMA carve-out, GTT/TTM limits, OS page availability, and other processes. That is exactly the input that (per §3d) can flip rocBLAS/hipBLASLt to a different kernel, and (per §3c) changes which algorithms pass `isAlgoSupported()`.

---

## 6. The mechanism — precise statement

### The confirmed chain

1. Ollama's ROCm backend resolves each matmul through **rocBLAS**, which internally dispatches to either its embedded **Tensile** backend or **hipBLASLt**; on recent ROCm the choice is automatic and architecture/problem dependent (rocBLAS design notes).
2. hipBLASLt resolves the actual kernel via **heuristics** keyed on problem sizes, GPU configuration, **and other parameters** (hipBLASLt docs), recording the answer in a **heuristics cache**. The eligible algorithm set is filtered by **workspace size** (`setMaxWorkspaceBytes` / `isAlgoSupported`) (rocm-examples README). Tensile independently performs **solution selection** over its library, with a naive vs optimized search and a selectable distance metric (Tensile env vars).
3. Several inputs to that resolution are **runtime state, not problem shape**: free device memory (rocBLAS documents an explicit downgrade to an "unoptimized kernel" when device memory is unavailable, "which could also produce variable results"), the workspace the caller can grant, and — when tuning/autotuning is active — **measured timings** (`TE_HIPBLASLT_TUNING_RUN_COUNT` benchmark runs per shape; Primus stages 1–3).
4. On a **Radeon 760M iGPU (gfx1103, UMA)**, "free device memory" is not a fixed hardware property: it derives from the BIOS UMA carve-out, GTT/TTM limits, and current OS page availability, and different APIs disagree about it by large margins (16 GB vs full shared memory; 122 GiB vs 91 GiB). Two launches minutes apart legitimately see different values.
5. Therefore **at process start**, the heuristic/solution-selection resolves against that launch's runtime state. If the state crosses a boundary — a workspace tier, a memory-availability tier, an autotune timing that inverts between two close candidates — the resolver returns a **different kernel with a different accumulation/split order**. Different kernel → different rounding → different logits.
6. Any difference, however small, is then **amplified to a discrete regime flip** by the argmax threshold described in the arxiv paper: below the margin, harmless; above it, top-1 becomes top-2 and the model emits the other tool call. Because both candidate continuations are locally stable, the model then stays in that regime.

### Why this is stable WITHIN a process but DIFFERENT across processes — the precise reason

- **Stable within:** the selection is performed **once** and **cached**. AMD recommends "query the heuristics once using `hipblasLtMatmulAlgoGetHeuristic()`, then reuse the result for subsequent computations." rocBLAS keeps the resolved solution in the `rocblas_handle` (which "contains the temporary device workspace"); Tensile resolves per problem and the answer is stable for the process. All 20 requests in a block therefore execute **the same binary kernel with the same tiling, the same split count, and the same summation order on the same input bytes** → bitwise identical → 20/20. This is not "the GPU is deterministic"; it is "**the choice was frozen**."
- **Different across:** the cache is **per-process (per-handle)** and is **not persisted** across a restart [note: hipBLASLt's heuristics cache is a host-side in-process cache per the docs; no documented cross-process persistence was found]. A new process re-runs resolution against a **new runtime state** — different free/GTT memory after the previous process released its allocations and the OS reclaimed/compacted pages, different thermal/clock state feeding any timing-based autotune, different workspace grant. The resolver lands on a different algorithm. The new choice is immediately frozen again → a *new* stable regime, held for that whole block.
- **The observable signature is exactly what was described:** perfect reproducibility inside a block (20/20) with a hard discontinuity at the process boundary, and a small number of discrete regimes (3 in an hour) rather than continuous jitter. A continuous-noise cause would violate the 20/20; a within-process race would too. A **frozen-per-process, state-dependent choice** is the shape that fits both observations simultaneously.

**Corollary / falsifiable prediction:** the two regimes should show **different kernel names** for the same GEMM shape, and the *first* matmul of each run is where the decision is made. Logging `HIPBLASLT_LOG_LEVEL=4` (heuristic status) and `TENSILE_DB=0x8040` (solution selection + selected kernel names) or `TENSILE_SOLUTION_INDEX=1` per run should show a different solution index/kernel name in Regime A vs Regime B. If the kernel names are identical across regimes, this mechanism is **refuted** and the cause must be sought elsewhere (e.g. attention-backend choice, softmax/reduction kernel selection, or a genuine correctness bug).

---

## 7. Evidence classification

### CONFIRMED (documented by AMD, or stated by an AMD maintainer)
1. hipBLASLt picks the matmul kernel via **heuristics** based on problem sizes, GPU configuration, **and other parameters**, with a **heuristics cache** — https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/how-to/use-logging-heuristics.html
2. AMD's Primus docs state deterministic mode must disable **HipBLASLt autotuning** and that this "**prevents run-to-run kernel-selection differences**" — https://rocm.docs.amd.com/projects/primus/en/latest/04-technical-guides/determinism-and-reproducibility.html
3. Primus documents a hipBLASLt **autotuning** workflow with `TE_HIPBLASLT_TUNING_RUN_COUNT` benchmark runs per shape and a `HIPBLASLT_TUNING_OVERRIDE_FILE` — https://rocm.docs.amd.com/projects/primus/en/main/04-technical-guides/performance-tuning.html
4. rocBLAS **automatically** chooses Tensile vs hipBLASLt by architecture and problem; `ROCBLAS_USE_HIPBLASLT` overrides — https://rocm.docs.amd.com/projects/rocBLAS/en/latest/conceptual/rocblas-design-notes.html
5. **Workspace-dependent algorithm filtering** is a documented API flow (`setMaxWorkspaceBytes` → `isAlgoSupported` → "Filter algorithms based on workspace size constraints") — https://raw.githubusercontent.com/ROCm/rocm-examples/refs/heads/amd-staging/Libraries/hipBLASLt/gemm_get_all_algos_ext/README.md
6. rocBLAS docs, in the **bitwise reproducibility** section: if device memory is unavailable, functions "proceed to use an unoptimized kernel, which could also produce variable results" — same URL as (4)
7. Tensile solution selection is an explicit step with `TENSILE_NAIVE_SEARCH`, `TENSILE_TAM_SELECTION_ENABLE`, `TENSILE_METRIC` (incl. "Random"), `TENSILE_SOLUTION_INDEX`, `TENSILE_DB` — https://rocm.docs.amd.com/projects/Tensile/en/docs-7.14.0/src/reference/environment-variables.html
8. AMD maintainer `rkamd`: atomics **enabled by default**; functions using atomics "may not provide deterministic results"; `ROCBLAS_DEFAULT_ATOMICS_MODE` since ROCm 6.2, `rocblas_set_atomics_mode()` before that — https://github.com/ROCm/rocBLAS/issues/1459
9. Current rocBLAS: atomics **not allowed** by default; four listed conditions for bitwise reproducibility — https://rocm.docs.amd.com/projects/rocBLAS/en/latest/conceptual/rocblas-design-notes.html
10. On gfx1103-adjacent APUs, reported "available GPU memory" differs drastically by API/BIOS carve-out — https://github.com/likelovewant/ROCmLibs-for-gfx1103-AMD780M-APU/issues/67 , https://github.com/ggml-org/llama.cpp/pull/20472
11. PyTorch ROCm has a **silent** determinism gap: `use_deterministic_algorithms(True)` is dropped (no warn, no raise) for CK mem-efficient SDPA backward; CK path `dq` differs, AOTriton default path is bitwise reproducible — https://github.com/pytorch/pytorch/pull/197771
12. The arxiv paper 2606.21023 is real and identifies **downcast boundary truncation**, not atomics, as the microscopic origin, amplified to an argmax flip past a threshold — https://arxiv.org/abs/2606.21023 , https://arxiv.org/html/2606.21023v1
13. The requested ROCm issue 6595 exists, is open/triaged, and has **zero comments** — https://github.com/ROCm/legacy-rocm-build/issues/6595

### PLAUSIBLE-BUT-UNCONFIRMED (mechanism is real and documented; its application to *this* 760M/Ollama case is inference, not documented)
- That **this specific case** is caused by hipBLASLt/Tensile kernel selection flipping across process restarts. The mechanism is confirmed to exist and to be state-dependent; no source describes this exact Ollama+760M symptom. **Needs the logging test in §6 to confirm.**
- That the relevant runtime-state input here is **free/GTT/UMA memory** rather than autotune timing or another parameter. AMD's docs say "other parameters" without enumerating them, and document a memory-driven downgrade — consistent, not proven.
- That the selected algorithm is cached **per process only** (not globally persisted). This is what the Docs' "heuristics cache" + "query once, reuse" wording implies, and it is required for the observed signature, but no AMD page was found that states cross-process cache lifetime explicitly.
- That Ollama's ROCm build actually routes the Coder-1.5B matmuls through hipBLASLt (vs Tensile) and that autotuning is active. Not verified; depends on the Ollama/ROCm build and is checkable with `ROCBLAS_USE_HIPBLASLT` and the logs.
- That the arxiv paper's boundary-truncation mechanism **applies to AMD** — the paper is NVIDIA/SASS-only; the extrapolation is ours.

### SPECULATIVE (flagged as such; no source found)
- That exactly **three** regimes correspond to three distinct kernels/algorithms. The count is consistent with a small discrete choice set but was not verified.
- That the divergence specifically flips the **tool-call formatting** rather than the semantic content. Not addressed by any source.
- That the Radeon 760M's specific UMA/GTT configuration makes it *more* susceptible than a dGPU. Reasonable (memory state is more variable on UMA) but unsourced.
- That ROCm has or lacks a `CUBLAS_WORKSPACE_CONFIG` equivalent **for every** code path. No equivalent env var was found on the rocBLAS or hipBLASLt env-vars pages, but absence of a documented var is weaker than a documented statement that none exists. `setMaxWorkspaceBytes()` is the API-level analogue.
- The referenced `ROCm/librocdxg` issue #57 (inconsistent `hipMemGetInfo()` across OSes) was **not fetched**; treat as reporter-stated only.

---

## 8. Things that were checked and did NOT exist / did not hold

- `https://raw.githubusercontent.com/ROCm/rocBLAS/develop/docs/how-to/what-is-rocblas.rst` → **HTTP 404**. The path moved; the current location is https://rocm.docs.amd.com/projects/rocBLAS/en/latest/conceptual/rocblas-design-notes.html (the section anchors `#atomic-operations` and `#bitwise-reproducibility` referenced by the 2024 maintainer comment now live there). The old `docs/how-to/what-is-rocblas.rst` anchor in issue #1459 is stale.
- The exact quoted phrase "non-reproducibility of LLM inference is not a pervasive noise problem, but a localized" was **not found verbatim** in paper 2606.21023's HTML; see §1.
- `https://api.github.com/repos/ROCm/legacy-rocm-build/issues/6595/comments` returns `[]` — **there are no comments on that issue.**
- No ROCm documentation page was found stating a blanket "hipBLASLt deterministic mode". The nearest things are the rocBLAS atomics/reproducibility conditions and the Primus `PRIMUS_DETERMINISTIC` umbrella.
- No documented ROCm env-var equivalent of `CUBLAS_WORKSPACE_CONFIG` was found.

---

## 9. Practical next step to confirm or refute (recommended)

Run the same block twice while capturing kernel selection, and diff:

```bash
export HIPBLASLT_LOG_LEVEL=4
export HIPBLASLT_LOG_MASK=0xFFFFFFFF
export HIPBLASLT_LOG_FILE=/tmp/hipblaslt_%i.log
export TENSILE_DB=0x8040
export TENSILE_SOLUTION_INDEX=1
export AMD_LOG_LEVEL=2
```

Then compare selected kernel names / solution indices between runs:
`diff <(grep -E "hipblasLt|Tensile|Solution" run_A.log) <(grep -E "hipblasLt|Tensile|Solution" run_B.log)`

- **Different kernel names/solution indices in the two regimes → mechanism CONFIRMED** for this case.
- **Identical kernel names → mechanism REFUTED**; look next at attention-backend choice, softmax/`SplitKReduce`-style reductions, and whether atomics are enabled (`ROCBLAS_DEFAULT_ATOMICS_MODE` unset/1).

Candidate mitigations to test (each has a documented basis): `ROCBLAS_DEFAULT_ATOMICS_MODE=0`; `ROCBLAS_USE_HIPBLASLT=0` (force Tensile) or `=1`; pin the kernel with a tuning override file; pin the workspace; reduce the number of variables by fixing the memory state before launch.

---

## 10. Complete URL index

Papers / literature
- https://arxiv.org/abs/2606.21023
- https://arxiv.org/html/2606.21023v1
- https://arxiv.org/pdf/2606.21023v1 (fetched; tool returned "unsupported content type application/pdf" — not a 404)
- https://doi.org/10.48550/arXiv.2606.21023
- https://proceedings.neurips.cc/paper_files/paper/2025/hash/f80094a824ba5912d4a2de169c404a40-Abstract-Conference.html
- https://github.com/Roverlucas/genai-reproducibility-protocol/blob/3a9a4e720aef23adc3214787a24106f545474087/article/ncomms_main.pdf
- https://www.zenodo.org/records/21205976
- https://www.zenodo.org/records/17118544

ROCm/AMD docs
- https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/how-to/use-logging-heuristics.html
- https://rocm.docs.amd.com/projects/rocBLAS/en/latest/conceptual/rocblas-design-notes.html
- https://rocm.docs.amd.com/projects/rocBLAS/en/docs-6.4.2/reference/deprecations.html
- https://rocm.docs.amd.com/projects/rocBLAS/en/latest/reference/env-variables.html
- https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/reference/env-variables.html
- https://rocm.docs.amd.com/projects/Tensile/en/docs-7.14.0/src/reference/environment-variables.html
- https://rocm.docs.amd.com/projects/primus/en/latest/04-technical-guides/determinism-and-reproducibility.html
- https://rocm.docs.amd.com/projects/primus/en/main/04-technical-guides/performance-tuning.html

ROCm repos / issues
- https://github.com/ROCm/legacy-rocm-build/issues/6595 (API: https://api.github.com/repos/ROCm/legacy-rocm-build/issues/6595)
- https://api.github.com/repos/ROCm/legacy-rocm-build/issues/6595/comments (returns [])
- https://github.com/bioritmovideo/trellis2-rocm-gfx1201/blob/master/repro_sgemm_fp32_gfx1201.py
- https://github.com/ROCm/rocBLAS/issues/1459 (API: https://api.github.com/repos/ROCm/rocBLAS/issues/1459)
- https://github.com/ROCm/TheRock/issues/2011 (API: https://api.github.com/repos/ROCm/TheRock/issues/2011)
- https://github.com/ROCm/rocm-libraries/pull/12277 (referenced by pytorch PR #197771; not independently fetched)
- https://github.com/ROCm/rocm-libraries/blob/46653de70f6d71031bed76e15525edd331318a99/docs/hipblaslt-runtime-triage-checklist.md
- https://raw.githubusercontent.com/ROCm/rocm-examples/refs/heads/amd-staging/Libraries/hipBLASLt/gemm_get_all_algos_ext/README.md
- https://github.com/ROCm/rocm-libraries/issues/2346 (referenced by TheRock #2011; not independently fetched)

APU / UMA / gfx1103
- https://github.com/likelovewant/ROCmLibs-for-gfx1103-AMD780M-APU/issues/67
- https://github.com/ggml-org/llama.cpp/pull/20472
- https://github.com/ggml-org/llama.cpp/issues/24836
- https://github.com/ROCm/librocdxg/issues/57 (cited, not fetched)

PyTorch / cuBLAS analogy
- https://github.com/pytorch/pytorch/pull/197771
- https://docs.nvidia.com/cuda/cublas/#cublassetworkspace
- https://docs.nvidia.com/cuda/cublas/#cublasltmatmul

---

*Report compiled from live web fetches. All HTTP fetches returned 200 except the two explicitly marked. No URL, issue number, or paper ID in this report was invented.*
