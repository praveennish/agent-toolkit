# ADR-009: Defence in depth — ambient mTLS, NetworkPolicy, ClusterIP-only backends

**Status:** Accepted (reconstructed) · **Scope:** platform + agent-toolkit layers

## Context

- The cluster hosts sensitive state (agent sessions, embeddings, keys) and untrusted code
  (sandboxes) side by side.
- Any single control can be misconfigured. Security must not rest on one layer.
- Agents in customer namespaces must still reach shared backends easily.

## Decision

Stack several independent controls:

1. **Istio ambient mesh with strict mTLS** for the toolkit namespaces (labelled
   `istio.io/dataplane-mode: ambient` when `istio_enabled`). Workload namespaces join by
   label. LiteLLM admits only listed namespaces (`litellm_allowed_namespaces`).
2. **NetworkPolicies** on every sensitive workload: Redis (its port + HBONE 15008), sandbox
   pods (router-only ingress, public-only egress), OpenShell sandbox pods (DNS, gateway,
   LiteLLM, proxy, public only).
3. **ClusterIP-only** services for Redis, pgvector, sandbox router and OpenShell. Admin access
   goes through `kubectl port-forward` (gated by Kubernetes RBAC). The docs explicitly say
   *not* to switch to NodePort/LoadBalancer.
4. **Narrow, documented exceptions**: OpenShell sandboxes sit outside the mesh. They are
   admitted to LiteLLM in plaintext *on the LiteLLM pods only*, still need the virtual key,
   and are allowed from the pod network (`litellm_allow_pod_network`).

## Alternatives considered

| Alternative | Why not |
|---|---|
| Perimeter-only security (TLS at the edge) | Flat internal network; one compromised pod sees everything |
| Sidecar-based Istio | Ambient mode avoids a sidecar per pod: lower overhead and simpler sandbox pods |
| NetworkPolicy only, no mesh | No workload identity or encryption between services |

## Consequences

- ✅ A failure of one control (e.g. a missing NetworkPolicy) does not expose everything.
- ✅ Backends are unreachable from outside the cluster by construction.
- ⚠️ Requires a CNI that enforces NetworkPolicy (e.g. Calico).
- ⚠️ Sandbox templates must opt *out* of the mesh (`istio.io/dataplane-mode: none`), or their NetworkPolicy is not enforced: a subtle interaction that is documented for custom templates.
- ⚠️ New agent namespaces need two steps (mesh label + LiteLLM allow-list).

## Evidence in the repository

- `config.yaml` → `litellm_allowed_namespaces`, `litellm_allow_pod_network`.
- Roles: "Enrol namespace in the ambient mesh" tasks; `charts/redis-stack/.../networkpolicy.yaml`.
- `roles/agent_sandbox/tasks/install.yaml` → `eat-sandbox-pool-egress`.
- `roles/openshell/tasks/install.yaml` → `eat-openshell-sandbox-pods`, "Let sandboxes reach LiteLLM under STRICT mTLS".
- `docs/backend-connection-reference.md`, `docs/single-node-deployment.md` → "Redis security notes".
