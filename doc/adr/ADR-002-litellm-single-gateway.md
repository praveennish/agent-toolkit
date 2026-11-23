# ADR-002: LiteLLM as the single OpenAI-compatible gateway, with virtual keys

**Status:** Accepted (reconstructed) · **Scope:** inference layer (consumed by every agent and sandbox)

## Context

- Many agents, many models (local vLLM, cloud APIs). Without a single entry point, every
  agent needs every model's URL and credential, and nobody can see or cap spend.
- Agent frameworks almost universally speak the **OpenAI API**.
- Policy (auth, budgets, rate limits, content safety, routing, tracing) must be enforced in
  one place.

## Decision

Route **every** model call through **LiteLLM** (the "GenAI Gateway", service `litellm:4000`,
external `https://litellm.<domain>`). Use **virtual keys** (one per agent or sandbox
population, each with its own allowed models and budget) as the default access mode
(`auth_provider: "litellm"`, `auth_type: litellm_vkey`), with Keycloak JWT as an alternative.
Attach guardrails, the Hybrid Router and Langfuse tracing as LiteLLM hooks and callbacks.

## Alternatives considered

| Alternative | Why not |
|---|---|
| Agents call vLLM directly | No auth, budgets, tracing or routing; secrets everywhere |
| A generic API gateway (Envoy only) | Handles HTTP, not LLM semantics (tokens, spend, model aliases, fallbacks) |
| Build a custom proxy | Re-implements what LiteLLM already provides for 100+ providers |
| JWT-only (Keycloak) | Supported, but virtual keys are simpler for machine clients and carry budgets |

## Consequences

- ✅ One URL and one key per agent; frameworks work unchanged.
- ✅ Central spend tracking and budgets (e.g. OpenShell sandboxes share one key, budget 50).
- ✅ Natural place for cross-cutting features (guardrail, router, tracing) without client changes.
- ⚠️ The gateway is on the critical path for every call: its availability and latency matter (KPI: gateway overhead).
- ⚠️ Custom behaviour (router) depends on LiteLLM internals; version pinning is required.
- ⚠️ The master key is powerful: it is kept in Secret `litellm-master-key`, and other components mint keys *inside* the pod rather than copying it.

## Evidence in the repository

- `config.yaml` → `auth_type: "litellm_vkey"`, `litellm_allowed_namespaces`, `litellm_public_paths`.
- `docs/single-node-deployment.md` → verify via `/v1/models`, `/v1/chat/completions`.
- `docs/openshell.md` → interface #7 (key minted via `kubectl exec` + `/key/generate`).
- `docker/docker-compose.yml` → LiteLLM `v1.83.14-stable.patch.2`, Langfuse callbacks.
