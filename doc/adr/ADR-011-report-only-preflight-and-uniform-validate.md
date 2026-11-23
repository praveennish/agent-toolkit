# ADR-011: Ansible roles with uniform install/validate/teardown; report-only preflight

**Status:** Accepted (reconstructed) · **Scope:** deployment automation (this repository)

## Context

- A full install takes 20–40 minutes. Failing at minute 30 because of swap, NTP or DNS wastes
  time and trust.
- Installs are re-run often (config changes, partial failures, upgrades), so every step must
  be safe to repeat.
- The toolkit is one layer among several, so it must plug into a common installer.
- Operators need the same mental model for every component.

## Decision

1. **One Ansible role per component**, each with `defaults/main.yaml` and
   `tasks/{main,install,validate,teardown}.yaml`. `main.yaml` dispatches on
   `component_action` (default `install`), and skips install when the component's
   `*_enabled` switch is false.
2. **Register components** in `components.yaml` (layer + `depends_on`) so Toolkit Manager can
   order and toggle them.
3. **Idempotency patterns**: `state: present`; read the existing Secret before generating a
   password; detect and remove a *failed* Helm release before `upgrade --install`; upserts for
   registrations; readiness polling with retries; secret-handling tasks run with `no_log`.
4. **Preflight is report-only**: it runs at the start of `install` (skippable), checks every
   node, writes a cumulative JSON/HTML/TXT report, prints a warning block, never stops the
   install, and is capped at 5 minutes. Its single change to a system is the kubelet DNS
   setting.
5. **Validate** runs each enabled component's `validate.yaml` and fails with a reason.
   Healthy means `failed=0`.

## Alternatives considered

| Alternative | Why not |
|---|---|
| One big shell script | Hard to re-run safely, hard to toggle components, hard to validate |
| Helm umbrella chart only | Cannot do host-level steps (Kata, DNS, CPU pinning) or cross-system steps (minting LiteLLM keys) |
| Preflight that blocks | False positives would block valid but unusual environments; a report lets the operator decide |
| GitOps operator (Argo/Flux) | Possible later; Ansible fits the bare-metal plus Kubernetes scope and the parent installer |

## Consequences

- ✅ Uniform operations: `install`, `validate`, `teardown` for every component; easy to add a new one.
- ✅ "Re-run install" is a safe, standard repair path.
- ✅ Early, readable environment diagnostics (e.g. CPU governor, THP, swap).
- ⚠️ Report-only means an operator can ignore a real problem; the warning block exists to prevent that.
- ⚠️ Correct inventory matters: a node without `ansible_connection` would have node-level steps run on the installer machine. Preflight detects this by comparing machine IDs.
- ⚠️ Ansible + YAML + Jinja logic can become complex (string-replacing upstream manifests, for example).

## Evidence in the repository

- `roles/*/tasks/main.yaml` (identical dispatch pattern), `components.yaml`.
- `roles/redis_stack/tasks/install.yaml`, `roles/pgvector/tasks/install.yaml` (failed-release cleanup, password reuse).
- `playbooks/preflight-check.yml`, `playbooks/preflight/*`, `docs/validate-stack.md`.
- `.github/workflows/ansible-lint.yml`.
