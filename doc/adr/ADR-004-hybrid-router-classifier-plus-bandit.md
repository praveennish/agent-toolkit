# ADR-004: Hybrid Router — rules classifier + per-tier multi-armed bandit, mounted without image rebuild

**Status:** Accepted (reconstructed) · **Scope:** inference layer (LiteLLM)

## Context

- Sending every request to the biggest model is slow and costly, especially on CPU. Sending
  everything to a small model hurts quality on hard prompts.
- Clients should not have to choose a model per request.
- Which model is *fastest* for a tier depends on hardware, load and placement, and it changes
  over time.
- Rebuilding and maintaining a forked LiteLLM image is expensive.

## Decision

Expose one **virtual model**, `hybrid-router`. A pre-routing hook rewrites each request to a
real model in two steps:

1. **Classify** complexity with a cheap, rules-based weighted score (tokens, keyword families,
   multi-step patterns, question density) into `SIMPLE / MEDIUM / COMPLEX / REASONING`
   (boundaries 0.15 / 0.35 / 0.60).
2. **Pick** a model among that tier's candidates with an **online multi-armed bandit**
   (Thompson sampling by default; UCB and ε-greedy available). The reward is
   `target_tpt / (target_tpt + latency/tokens)`, 0 on failure, optionally blended with quality.

Ship it as Python files in a **ConfigMap**, mounted into the stock LiteLLM container and
activated through `litellm_settings.callbacks`. A monkey-patch teaches LiteLLM's router the
`auto_router/hybrid_router` prefix. On by default (`hybrid_router_enabled: true`).

## Alternatives considered

| Alternative | Why not (or why kept as an option) |
|---|---|
| Static model choice per app | No adaptation to prompt difficulty |
| An LLM or embedding classifier for every request | Adds an extra model call of latency and compute per request; the rules classifier is free and explainable. (Embedding-based routing is kept as the optional **vLLM Semantic Router**.) |
| Pure round-robin / least-latency load balancing | Ignores prompt difficulty; does not learn per tier |
| Fixed "fastest model" table | Becomes stale when hardware or placement changes; a bandit re-learns |
| Fork LiteLLM | Maintenance burden; upgrades become hard |

## Consequences

- ✅ Lower average latency and cost with no client changes; other model names untouched.
- ✅ Per-tier bandits learn that a model can be fast on short prompts and slow on long ones.
- ✅ Enable/disable with one setting; config changes without image rebuilds.
- ⚠️ Keyword rules can misclassify; boundaries and keywords are tunable.
- ⚠️ The default reward rewards *speed*; quality only via `quality_weight`.
- ⚠️ With `target_tpt = 1.0` and CPU time-per-token ≪ 1 s, rewards bunch near 1, so the bandit separates models slowly (analysis; tune `target_tpt`).
- ⚠️ Bandit state is in-process memory: it resets on restart and is per replica (inference from the design; verify in code).
- ⚠️ The monkey-patch is coupled to LiteLLM internals, so the LiteLLM version must be pinned.

## Evidence in the repository

- `docs/hybrid-router.md` (how it works, both layers, configuration reference, file layout).
- `config.yaml` → `hybrid_router_enabled: true`.
- `docs/single-node-deployment.md` → Step 1b, verification in Langfuse (`llm.model_name`).
