# ADR-003: CPU-first inference with vLLM on Intel® Xeon®; GPU/cloud optional

**Status:** Accepted (reconstructed) · **Scope:** inference layer

## Context

- Agents spend most of their wall-clock time on orchestration, tools, state and policy (the
  "control plane"), not only on LLM reasoning.
- GPUs are expensive and scarce, and many enterprise data centres are CPU-only.
- Modern Xeon CPUs have **AMX** (matrix units for bf16/int8). Combined with MoE models,
  smaller coding models and speculative decoding, they can serve useful models.
- Product goal: show agentic AI running on Xeon (see `01-…` Q2).

## Decision

Serve all default models (chat, embedding, rerank, guard) with **vLLM on CPU** under
**KServe**, tuned per model (`models.yaml`: `cpu`, `memory`, `--dtype bfloat16`, KV cache,
TP, tool-call parser). Offer speculative-decoding (`-specdec`) variants and MoE models.
Keep the gateway **OpenAI-compatible**, so GPU or cloud endpoints (OpenAI, Anthropic, Gemini,
SambaNova) can be added for heavy reasoning without changing agents. Docker path: vLLM CPU or
OpenVINO Model Server (int4/int8).

## Alternatives considered

| Alternative | Why not |
|---|---|
| GPU-first (vLLM on GPUs) | Contradicts the cost/availability argument and the product goal; GPUs remain optional |
| Cloud LLM APIs only | Breaks data residency and air-gap requirements |
| llama.cpp / other CPU runtimes | vLLM gives an OpenAI server, continuous batching, prefix caching, speculative decoding, tool parsers and KServe integration |
| OpenVINO everywhere | Offered on the Docker path; Kubernetes default stays vLLM |

## Consequences

- ✅ Runs on existing Xeon fleets; no GPU required; private and air-gappable.
- ✅ Same API whether a model runs on CPU, GPU or cloud.
- ⚠️ Large memory per model (KV cache dominates): the default install needs ~131 GiB, more than a 128 GB node.
- ⚠️ Lower peak throughput than GPUs for large dense models, so routing (ADR-004) and model choice matter.
- ⚠️ Careful CPU/NUMA placement required (ADR-012).
- Follow-up: publish per-SKU inference benchmarks (missing today, see `02-design.md` §7).

## Evidence in the repository

- `README.md` → "core insight", FAQ "Does it require a GPU? No … AMX".
- `docs/single-node-deployment.md` → CPU model catalog, speculative decoding, memory note.
- `docs/xeon-model-configuration.md` → sizing, footprint table, flags.
- `docker/model-configs.yaml`, `docker/ovms-model-configs.yaml`.
