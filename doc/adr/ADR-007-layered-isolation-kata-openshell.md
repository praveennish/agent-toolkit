# ADR-007: Opt-in stronger isolation — Kata microVMs and NVIDIA OpenShell

**Status:** Accepted (reconstructed) · **Scope:** agent-toolkit layer (`roles/agent_sandbox` Kata block, `roles/openshell`)

## Context

- Namespaces and cgroups (runc) share the host kernel. A kernel exploit escapes the sandbox.
- Network policy at L3/L4 cannot say "GET is allowed on api.github.com but POST is not".
- An agent that can read its own API key can leak it through any allowed channel.
- Stronger isolation costs more (microVM boot, memory, KVM requirement, operational complexity),
  and not every deployment needs it.

## Decision

Offer two **opt-in** layers on top of ADR-006, both **off by default**:

1. **Kata Containers** (`kata_containers_enabled: true`, `kata_runtime: kata-fc | kata-qemu | both`):
   a `kata-sandbox-template` with the same image but a Kata `runtimeClassName` (Firecracker
   preferred), plus a `kata-pool` of size 1. Each sandbox gets its own guest kernel. Nodes must
   pass a KVM check and are labelled `ei-kata-eligible`. Firecracker needs a devmapper
   snapshotter, which the infrastructure layer provisions automatically.
2. **NVIDIA OpenShell** (`openshell_enabled: true`, requires Agent Sandbox): a supervisor in
   every sandbox enforces egress default-deny, per-host/per-binary rules, **L7 method/path
   rules**, Landlock and seccomp, plus **credential isolation**. The sandbox sees a placeholder
   key, and the supervisor injects a dedicated, budgeted LiteLLM virtual key only toward
   LiteLLM.

## Alternatives considered

| Alternative | Why not |
|---|---|
| Kata/OpenShell always on | Requires KVM / extra components; higher cost; blocks simple deployments |
| gVisor | Not chosen in the repo; Kata/Firecracker follows the upstream agent-sandbox example and keeps the same SDK |
| Build L7 egress filtering in-house | OpenShell already integrates with Agent Sandbox CRs |
| Pass real API keys into sandboxes | Leak risk; violates least privilege |

## Consequences

- ✅ Security can be raised per deployment without changing agent code (same SDK; only the warm pool name changes).
- ✅ Credential isolation means a compromised agent cannot steal the LiteLLM key.
- ✅ Missing prerequisites stop or warn with the fix in the message, rather than failing obscurely; the Kata pool has no readiness gate, so one bad node cannot hang the install.
- ⚠️ More moving parts: KVM, devmapper, OpenShell gateway, mTLS client certificate (which grants full gateway control, so `pods/exec` must be restricted).
- ⚠️ OpenShell single-admin mode only; OIDC not yet validated; breaking changes between OpenShell 0.0.x and 0.1.x.

## Evidence in the repository

- `docs/agent-sandbox.md` → "microVM Isolation with Kata Containers".
- `charts/agent-sandbox/kata-templates.yaml`; `roles/agent_sandbox/tasks/install.yaml` (Kata block).
- `docs/openshell.md`; `roles/openshell/*`; `charts/openshell/genai-gateway-provider.yaml`.
