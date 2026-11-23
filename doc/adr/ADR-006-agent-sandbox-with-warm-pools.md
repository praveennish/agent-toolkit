# ADR-006: kubernetes-sigs Agent Sandbox; router is the only Kubernetes API caller; TokenReview; warm pools

**Status:** Accepted (reconstructed) · **Scope:** agent-toolkit layer (`roles/agent_sandbox`)

## Context

- Agents execute code that an LLM wrote. That code may be wrong, destructive or adversarial.
- Isolation must be per task, disposable, and limited in network reach.
- Creating a pod on demand costs scheduling and image-pull time: seconds per tool call.
- Agent pods should not need Kubernetes permissions (RBAC). Giving every agent "create pods"
  rights would be dangerous.

## Decision

Adopt upstream **kubernetes-sigs/agent-sandbox v1.0.10** (CRDs + controller from the official
release manifest) and harden it:

1. **sandbox-router** (×2, PDB) is the only component that talks to the Kubernetes API.
   Clients call it over HTTP `:8080`. The role injects
   `--authz-mode=tokenreview --authz-tokenreview-require-token=true`, so every call needs a
   valid ServiceAccount token.
2. **Default template** `python-sandbox-template`: non-root, `drop: [ALL]`, no privilege
   escalation, 1 CPU / 1 Gi limit, `POST /execute` API on `:8888`.
3. **Warm pool** `python-pool` of 5 pre-created sandboxes for instant hand-out.
4. **Extra NetworkPolicy** `eat-sandbox-pool-egress`, keyed on the label every sandbox pod
   keeps for life: ingress from the router only; egress to public addresses only.

## Alternatives considered

| Alternative | Why not |
|---|---|
| Run code inside the agent pod | No isolation; a bad command hits the agent and its secrets |
| Give agents RBAC to create pods | Large blast radius; every agent becomes a cluster admin risk |
| Build a custom sandbox operator | Upstream SIG project exists, with CRDs, SDK and warm pools |
| Cold pods only (no pool) | Seconds of latency per sandbox; poor agent UX |
| Rely on the controller's own template NetworkPolicies | They select a label that warm-pool pods never carry, which leaves a gap; hence the extra policy |

## Consequences

- ✅ Agents need no RBAC; the router is a narrow, authenticated choke point.
- ✅ Near-instant sandboxes from the warm pool.
- ✅ Sandboxed code cannot reach the node, the Kubernetes API or cluster services.
- ⚠️ Pods share the host kernel (runc): mitigated by the opt-in Kata path (ADR-007).
- ⚠️ "Any ServiceAccount token in the cluster is accepted": authentication, not fine-grained authorisation.
- ⚠️ Sandboxes use public DNS and get no proxy settings, so they have no outbound access on networks that require a proxy.
- ⚠️ Warm pools consume resources while idle (5 × 250m/256 Mi requests).

## Evidence in the repository

- `roles/agent_sandbox/defaults/main.yaml`, `roles/agent_sandbox/tasks/install.yaml`.
- `charts/agent-sandbox/default-templates.yaml`.
- `docs/agent-sandbox.md` (architecture, router token, network access, SDK patterns).
