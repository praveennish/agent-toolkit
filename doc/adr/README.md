# Architecture Decision Records (ADRs)

An **ADR** is a short document that records *one* important design decision: the situation
(context), what was decided, which alternatives were weighed, and what follows from it
(consequences). ADRs explain the **why** behind a system, which code alone rarely does.

## Important note on provenance

The Intel® Agent Toolkit repository does not ship ADRs. The records below are
**reconstructed** from evidence in the repository (README, `docs/`, `roles/`, `charts/`,
`components.yaml`, `config.yaml`, `docker/`). Each ADR lists that evidence.
**"Alternatives considered"** are reasoned reconstructions. They describe what a team would
realistically have weighed, not quotes from the authors. Treat them as a study aid and as
interview talking points.

## Template used

```
# ADR-NNN: Title
Status · Scope (which layer/component)
## Context        — the forces and constraints
## Decision       — what was chosen
## Alternatives considered
## Consequences   — positive / negative / follow-ups
## Evidence in the repository
```

## Index

| ADR | Decision | Layer |
|---|---|---|
| [ADR-001](ADR-001-provider-design-pattern.md) | Provider Design Pattern: pluggable blocks behind standard interfaces | Whole product |
| [ADR-002](ADR-002-litellm-single-gateway.md) | LiteLLM as the single OpenAI-compatible gateway, with virtual keys | Inference |
| [ADR-003](ADR-003-cpu-first-inference-on-xeon.md) | CPU-first inference with vLLM on Xeon; GPU/cloud optional | Inference |
| [ADR-004](ADR-004-hybrid-router-classifier-plus-bandit.md) | Hybrid Router: rules classifier + per-tier multi-armed bandit, mounted without image rebuild | Inference |
| [ADR-005](ADR-005-two-tier-memory-redis-pgvector.md) | Two-tier memory: Redis Stack (short-term) + pgvector (long-term) | Agent toolkit |
| [ADR-006](ADR-006-agent-sandbox-with-warm-pools.md) | kubernetes-sigs Agent Sandbox; router is the only K8s API caller; TokenReview; warm pools | Agent toolkit |
| [ADR-007](ADR-007-layered-isolation-kata-openshell.md) | Opt-in stronger isolation: Kata microVMs and NVIDIA OpenShell | Agent toolkit |
| [ADR-008](ADR-008-fail-closed-guardrail.md) | Fail-closed content-safety guardrail on `pre_call` | Inference |
| [ADR-009](ADR-009-defense-in-depth-network-and-mesh.md) | Defence in depth: ambient mTLS, NetworkPolicy, ClusterIP-only backends | Platform + toolkit |
| [ADR-010](ADR-010-kubernetes-for-production-docker-for-development.md) | Kubernetes for production, Docker Compose for development | Deployment |
| [ADR-011](ADR-011-report-only-preflight-and-uniform-validate.md) | Ansible roles with uniform install/validate/teardown; report-only preflight | Deployment |
| [ADR-012](ADR-012-numa-aware-cpu-pinning.md) | NUMA-aware CPU pinning and TP-based memory limits for CPU inference | Inference / platform |

## How to use these for learning

1. Read the **Context** and stop. Decide what *you* would choose.
2. Read the **Decision** and compare.
3. Read the **Consequences**: these make the best interview answers ("the trade-off was…").
