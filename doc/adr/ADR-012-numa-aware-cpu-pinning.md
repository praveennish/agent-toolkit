# ADR-012: NUMA-aware CPU pinning and TP-based memory limits for CPU inference

**Status:** Accepted (reconstructed) · **Scope:** inference layer / platform (NRI balloons, model-manager)

## Context

- Multi-socket Xeon servers are **NUMA** machines: each node has fast local memory and slower
  remote memory. LLM inference is memory-bandwidth-bound, so remote memory access hurts speed.
- vLLM CPU shards a model across **tensor-parallel** ranks; each rank should own the cores and
  memory of one NUMA node.
- Kubernetes' default CPU management does not understand this topology.
- Over-large memory limits make the placement widen across NUMA nodes and break core binding.

## Decision

- Use the **NRI balloons** policy to pin model containers to physical cores.
- `cpu: auto` → take the free physical cores of **one NUMA node per TP rank** (on the smallest
  schedulable node). TP is auto-selected among 1/2/4 from the detected topology. Explicit
  `cpu:` values must be a multiple of TP and fit in a socket.
- Memory limits by TP: **TP=1 → 200 GiB** (keeps memory on the pinned NUMA node; a larger
  limit makes NRI widen `cpuset.mems` and vLLM fails to bind cores). **TP ≥ 2 → 400 GiB**
  (requests 128–256 GiB).
- Preflight checks the CPU governor (`performance`), THP and NUMA topology.

## Alternatives considered

| Alternative | Why not |
|---|---|
| Plain Kubernetes CPU requests (no pinning) | Threads float across sockets; remote memory traffic; noisy neighbours |
| Kubelet static CPU manager only | Less control over NUMA-node granularity and balloon sizing |
| Always TP=1 | Leaves other NUMA nodes idle for one model |
| Span NUMA nodes at TP=1 | Documented crash (`shm.cpp thread_num mismatch`) |

## Consequences

- ✅ Better memory locality and predictable performance per model.
- ✅ Small models (e.g. Llama-8B, TP=1) can use a full NUMA node's cores.
- ⚠️ `cpu: auto` on a single-NUMA node leaves no cores for a second model (`NRI pre-flight failed: not enough physical cores`), so set explicit `cpu:` values to co-locate models.
- ⚠️ A TP mismatch fails with `CreateContainerError: no balloon for annotation`.
- ⚠️ Models above ~60 B parameters in bf16 do not fit at TP=1 (200 GiB limit) and need TP ≥ 2.
- ⚠️ Several large MoE models already exceed the 256 GiB request at TP=4; they rely on the 400 GiB limit and Burstable QoS.

## Evidence in the repository

- `docs/xeon-model-configuration.md` (CPU cores and memory limits; footprint table).
- `docs/single-node-deployment.md` (NRI pre-flight note; Intel AI Performance Advisor).
- `playbooks/preflight/layer-platform-health.yml` (governor, THP, NUMA checks).
