# ADR-010: Kubernetes for production, Docker Compose for development

**Status:** Accepted (reconstructed) · **Scope:** deployment

## Context

- Production needs high availability, self-healing, rolling updates, multi-node scheduling,
  network policy and a service mesh.
- Developers, demos and CI need something that starts on one machine with no cluster overhead.
- Both audiences should see the *same* stack shape and the *same* client API.

## Decision

- **Kubernetes (default)**: Kubespray-provisioned (or bring-your-own via `existing_kubernetes`),
  Helm + Ansible, single-node or multi-node (shared storage required for multi-node).
- **Docker Compose**: `docker/deploy.sh` generates secrets, a per-model compose file and the
  LiteLLM config from `docker/config.cfg`. It runs the same core services (vLLM *or* OpenVINO
  model servers, LiteLLM on `:4000`, PostgreSQL + pgvector, Redis Stack, optional Flowise and
  Langfuse). Applications always talk to LiteLLM, so client code is identical.

## Alternatives considered

| Alternative | Why not |
|---|---|
| Kubernetes only (kind/minikube for dev) | Heavier for laptops/demos; slower iteration |
| Docker only | No HA, no NetworkPolicy/mesh, no multi-node |
| Two unrelated stacks | Behaviour drift; double documentation |

## Consequences

- ✅ Fast local iteration (`--skip-confirmation` for CI), production-grade cluster path.
- ✅ Engine switch (`serving_engine=vllm|openvino`) without client changes.
- ⚠️ Two code paths to maintain (Ansible/Helm vs Bash generators).
- ⚠️ Docker exposes Postgres/Redis on host ports, which suits a development machine, not a shared host; Flowise is loopback-bound until its first owner exists.
- ⚠️ Not every feature exists on both paths (e.g. sandbox, OpenShell, router are Kubernetes features).

## Evidence in the repository

- `README.md` → "Deployment Platform", "Decision Tree".
- `docker/README.md`, `docker/deploy.sh`, `docker/scripts/generate-docker-compose.sh`, `docker/docker-compose.yml`.
