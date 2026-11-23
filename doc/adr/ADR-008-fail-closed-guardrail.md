# ADR-008: Fail-closed content-safety guardrail on `pre_call`

**Status:** Accepted (reconstructed) · **Scope:** inference layer (LiteLLM + guard vLLM)

## Context

- Enterprise deployments must screen harmful requests before they reach the main model.
- A safety check that silently stops working while everything looks healthy is worse than none.
- The guard must run on CPU next to the main models, with minimal added latency.
- Guard models change over time; their gateway registration should not be left stranded.

## Decision

- Serve a small guard model, **Qwen3Guard-Gen-0.6B** (`qwen3guard`), as its own vLLM release.
- Register a LiteLLM **`custom_code`** guardrail with a **stable, model-agnostic name**
  (`content_safety`), running on **`pre_call`** for every request.
- **Fail closed**: block when the guard is unreachable, returns non-2xx, the prompt exceeds the
  guard's context, or the verdict cannot be parsed. Each case has its own message.
- `Controversial` is advisory by default (`guard_block_on_controversial: false`).
- Register by **upsert** (`PUT`), after compiling the code in the sandbox
  (`/guardrails/test_custom_code`).
- Guard vLLM uses the **Recreate** strategy; its context window is inherited, not hard-coded.

## Alternatives considered

| Alternative | Why not |
|---|---|
| Fail-open | A guard outage or a model output-format change would silently disable moderation |
| Keyword / regex filters | Poor accuracy; easy to evade |
| A large LLM as judge | High CPU cost and latency on every request |
| `post_call` (screen outputs) only | Harmful input would still reach the main model; output screening remains future work |
| Create-only registration | A renamed or changed guard would leave a stale registration that, being fail-closed, blocks everything |

## Consequences

- ✅ Moderation can never be silently bypassed; causes are visible in the error message.
- ✅ Swapping the guard model never strands a registration; re-runs need no gateway restart.
- ⚠️ The guard is a hard dependency: guard down means all chat requests blocked.
- ⚠️ Blocks surface as **HTTP 500** (fixed LiteLLM behaviour); clients must read `error.message`.
- ⚠️ Adds one guard round-trip to every request; multiple guardrails would add up (the sandbox has no `asyncio`).
- ⚠️ The guard's context window must be ≥ the main model's, or the guard becomes the request-size ceiling.
- ⚠️ 8 GiB memory is not enough (peak ~8.6 GiB, OOM exit 137).

## Evidence in the repository

- `docs/guardrails.md` (architecture, fail-closed behaviour, context window, roadmap).
- `config.yaml` → `guardrails_enabled` (on with LiteLLM).
