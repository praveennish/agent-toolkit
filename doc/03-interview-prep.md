# Interview Preparation — Intel® Agent Toolkit

> **Goal:** be able to discuss this project confidently at every depth an interviewer may
> probe: a 30-second pitch, component questions, maths deep dives, system design,
> debugging scenarios and trade-off judgement.
>
> **Prerequisites:** read [`01-understanding-the-agent-toolkit.md`](01-understanding-the-agent-toolkit.md),
> then [`02-design.md`](02-design.md) and the [`adr/`](adr/README.md) folder. This document assumes those words.
>
> **Honesty rule (read this first).** Describe your relationship to the project accurately:
> *"I studied / deployed / extended / benchmarked it"*. Never claim to have built parts you did
> not build. Interviewers probe ownership with follow-ups, and a precise, honest account of
> what you understand scores higher than an inflated one. The STAR templates in §8 are
> templates. Fill them only with things you have actually done.

## Contents

1. [Your pitch at three lengths](#1-your-pitch-at-three-lengths)
2. [Whiteboard: draw it in 90 seconds](#2-whiteboard-draw-it-in-90-seconds)
3. [Cheat sheet: names, numbers, ports](#3-cheat-sheet-names-numbers-ports)
4. [Questions and model answers, by level](#4-questions-and-model-answers-by-level)
   - [Level 1 — Fundamentals](#level-1--fundamentals)
   - [Level 2 — Components](#level-2--components)
   - [Level 3 — Deep dives with worked maths](#level-3--deep-dives-with-worked-maths)
   - [Level 4 — Security](#level-4--security)
   - [Level 5 — Performance](#level-5--performance)
5. [System design questions](#5-system-design-questions)
6. [Debugging scenarios](#6-debugging-scenarios)
7. [Trade-off and opinion questions](#7-trade-off-and-opinion-questions)
8. [Behavioural answers (STAR templates)](#8-behavioural-answers-star-templates)
9. [Hands-on rehearsal script](#9-hands-on-rehearsal-script)
10. [Questions to ask the interviewer](#10-questions-to-ask-the-interviewer)
11. [Seven-day study plan and self-check](#11-seven-day-study-plan-and-self-check)

---

## 1. Your pitch at three lengths

### 30 seconds

> "The Intel Agent Toolkit is an open-source, Kubernetes-based platform that gives enterprises
> everything an AI agent needs in production, except the agent itself. That means one
> OpenAI-compatible gateway with keys and budgets, LLM inference on Xeon CPUs with a router that
> picks the cheapest capable model, short- and long-term memory, sandboxed code execution, a
> content-safety guardrail, and full tracing. It installs with one command, and every block can
> be swapped. The business idea is that the agent control plane, and a good share of inference,
> runs efficiently on CPUs, so companies can run private agents on Xeon without depending on
> GPUs."

### 2 minutes (add the structure)

1. **Problem.** Production agents need a dozen systems; integration takes months.
2. **Shape.** Seven provider blocks: gateway, memory, routing, tools, sandbox, observability,
   deployment. Each is a contract with a default provider (Provider Design Pattern).
3. **Request path.** Agent → LiteLLM (virtual key, budget) → fail-closed guardrail
   (Qwen3Guard) → Hybrid Router (rules classifier + bandit) → vLLM on Xeon → trace to Langfuse.
4. **Action path.** Agent → sandbox router (ServiceAccount token, TokenReview) → warm-pool pod →
   `/execute`. Egress is public-only; Kata microVMs and OpenShell credential isolation are opt-in.
5. **Memory.** Redis Stack for sessions; pgvector for long-term memory and RAG.
6. **Operations.** Ansible roles with uniform install/validate/teardown, a report-only
   preflight, Helm charts, and Docker Compose for development.
7. **Scope.** The repository is the *agent-toolkit layer* of Intel's Toolkit Manager; the
   gateway and inference come from the inference layer.

### 5 minutes

Walk the sequence diagram ([`diagrams/sequence.png`](diagrams/sequence.png)). Pause at three
"design moments" and explain the decision behind each:
**fail-closed guardrail** (ADR-008), **router-only Kubernetes access + warm pools** (ADR-006),
**bandit reward on time-per-token** (ADR-004). Close with one limitation and how you would
address it, e.g. single-instance memory stores, or no published inference benchmarks.

---

## 2. Whiteboard: draw it in 90 seconds

Practise until you can draw this from memory:

```
                 [ Agent (LangGraph / CrewAI / …) ]
                    │ OpenAI API + virtual key          │ direct, in-cluster
                    ▼                                    ▼
   [ Envoy Gateway/TLS ] → [ LiteLLM :4000 ]       [ Redis :6379 ] [ pgvector :5432 ]
                            │ guardrail ─► qwen3guard
                            │ hybrid router (tier → bandit)
                            ▼                            [ sandbox-router :8080 ] ─► K8s API
                     [ vLLM on Xeon / cloud LLM ]             │                    ▼
                            │                                 └─► [ warm sandbox pod :8888 ]
                     [ Langfuse · Prometheus · Grafana ]
   ───────────────────────────────────────────────────────────────────────────────
   Kubernetes · Istio ambient mTLS · NetworkPolicy · NRI balloons (NUMA) · Xeon (AMX)
   Ansible roles + Helm · es_auto_installer.sh · preflight · validate
```

---

## 3. Cheat sheet: names, numbers, ports

| Thing | Value |
|---|---|
| Install | `./es_auto_installer.sh configure` → `init agent-toolkit` → `install agent-toolkit` |
| Validate | `./es_auto_installer.sh validate agent-toolkit` → healthy = `failed=0` |
| Config files | `env/<name>/global_config.yaml`, `config.inference.yaml`, `config.agent-toolkit.yaml` (loads last), `models.yaml` |
| Layer contract | `components.yaml`: `agent-toolkit` depends on `[platform, inference]` |
| Components here | redis_stack, pgvector, agent_sandbox (on); openshell, kuberay (off); keycloak_agent_config (JWT mode) |
| LiteLLM | `litellm.litellm.svc:4000`, `https://litellm.<domain>`, Secret `litellm-master-key` |
| Virtual model names | `hybrid-router`, `vllm-sr/auto` |
| Router tiers | SIMPLE < 0.15 ≤ MEDIUM < 0.35 ≤ COMPLEX < 0.60 ≤ REASONING (or 2+ reasoning markers) |
| Router reward | `target_tpt / (target_tpt + latency / max(tokens,1))`, failure = 0; default bandit Thompson |
| Guard model | `Qwen/Qwen3Guard-Gen-0.6B`, guardrail name `content_safety`, mode `pre_call`, fail-closed, block = HTTP 500 |
| Default chat model | `qwen2-5-coder-14b` (Qwen2.5-Coder-14B-Instruct) |
| Redis | `redis-stack-server.redis.svc:6379`, Secret `redis-stack-server-credentials` (`REDIS_URL`), 10 Gi |
| pgvector | `pgvector.pgvector.svc:5432`, db `agentdb`, user `agentuser`, PG 16, ext 0.8.0, 20 Gi |
| Agent Sandbox | v1.0.10; router `sandbox-router-svc.agent-sandbox-system.svc:8080`; pod `:8888 POST /execute`; `python-pool` = 5 |
| Sandbox CRDs | Sandbox, SandboxTemplate, SandboxClaim, SandboxWarmPool (v1beta1) |
| Kata | `kata-fc` (Firecracker, ~125 ms boot, needs devmapper) / `kata-qemu`; `kata-pool` = 1 |
| OpenShell | 0.1.6; gateway `openshell:8080` gRPC/mTLS; provider `genai-gateway`; key `openshell-sandboxes`, budget 50 |
| KubeRay | operator 1.3.0, Ray 2.40.0; `ray://ray-cluster-head-svc.ray-system.svc:10001`; dashboard `:8265`; workers 1–4 |
| Node minimum | 48 cores / 32 GB RAM / 150 GB disk (recommended 96+ / 64 GB / 200 GB) |
| Default install memory | ~131 GiB (96 model + 16 guard + 2 router + 17 stack) |
| Install time | 20–40 min (+10–15 min model pull) |
| Rack-scale results | 83.1 Gbit/s cross-leaf, 0.7 ms RTT, 1.42 GB/s Ceph write, 29k/12.5k IOPS |
| CI | ansible-lint, ShellCheck, Bandit, Checkov, Trivy, Scorecard, dependency-review |

---

## 4. Questions and model answers, by level

### Level 1 — Fundamentals

**Q1. What is an AI agent, and how is it different from a chatbot?**
A chatbot maps one prompt to one answer. An agent runs a loop: ask the LLM what to do, call a
tool, feed back the result, and repeat until the goal is reached. Because it *acts*, it needs
tools, memory, safety and observability: exactly what this toolkit provides.

**Q2. Is this toolkit an agent framework?**
No. Frameworks such as LangGraph and CrewAI implement agent *logic*. The toolkit is the
*production infrastructure underneath* them (README FAQ).

**Q3. Why does a platform need a gateway in front of models?**
For one point of control: authentication, per-agent keys, budgets, rate limits, spend
tracking, routing, safety checks and tracing, without touching any client.

**Q4. What is RAG, and which components support it here?**
Retrieve relevant documents (embedding model `bge-base-en`, vector search in pgvector or
RediSearch, optional `bge-reranker`), add them to the prompt, then generate.

**Q5. What does "Provider Design Pattern" mean here?**
Each block is a contract with an Intel-validated default implementation. Consumers use standard
interfaces (OpenAI API, Redis, PostgreSQL), so any provider can be swapped independently.

**Q6. Why Kubernetes?**
Self-healing, scheduling across nodes, declarative configuration, network policy, and an
ecosystem (Helm, operators, CRDs) that the sandbox and Ray components build on.

**Q7. What exactly is in *this* repository?**
The agent-toolkit layer: Redis Stack, pgvector, Agent Sandbox (+ Kata template), OpenShell,
KubeRay, the Keycloak realm, preflight, the Docker Compose path and the docs. LiteLLM, vLLM,
the router, the guardrail and Langfuse come from the inference layer of `enterprise-ai-solutions`.

### Level 2 — Components

**Q8. Walk me through what happens when an agent calls `model="hybrid-router"`.**
LiteLLM validates the virtual key, budget and rate limit → the `content_safety` guardrail sends
the prompt to Qwen3Guard (block on unsafe or any failure) → the pre-routing hook classifies the
prompt into a tier → the tier's bandit picks a real model → LiteLLM forwards through the AI
gateway to vLLM → on the response, the router computes a reward and updates the bandit, and
Langfuse records the trace, including `llm.model_name`.

**Q9. How is the router added to LiteLLM without rebuilding its image?**
Its Python files are rendered into the ConfigMap `litellm-router-code`, volume-mounted into the
container, and loaded through `litellm_settings.callbacks`. At import time it monkey-patches
`litellm.router.Router` to accept the `auto_router/hybrid_router` prefix, and hooks
`async_pre_routing_hook`.

**Q10. Why are there two memory stores?**
Different access patterns. Redis: very fast, mutable, short-lived session state and semantic
cache. pgvector: durable, queryable long-term memory, with vectors and relational data together.

**Q11. How does an agent get a sandbox?**
It calls the sandbox router over HTTP with a ServiceAccount token. The router verifies the
token (TokenReview), creates a `SandboxClaim`, and the controller binds a pre-warmed pod. The
agent then runs commands through the router to the pod's `POST :8888/execute`.

**Q12. What is a warm pool, and what does it cost?**
A set of pre-created idle sandboxes (`python-pool`, 5 pods). Claims are instant because
scheduling and image pull have already happened. The cost is idle resources (5 × 250m CPU /
256 Mi requested) and refill churn.

**Q13. What does OpenShell add over Agent Sandbox?**
Policy inside the sandbox: egress default-deny with per-host and per-binary rules, L7
method/path rules, Landlock and seccomp. Above all, **credential isolation**: the sandbox sees a
placeholder key, and the supervisor injects the real LiteLLM virtual key only on allowed
requests.

**Q14. What does KubeRay give agents?**
Parallel tool execution on autoscaled Ray workers (`ray.remote` tasks). The head runs with
`num-cpus=0`, so it only schedules. Clients must use exactly the cluster's Ray version (2.40.0).

**Q15. What does preflight check, and why does it not block the install?**
Time sync, kubelet DNS, leftovers from an unfinished install, node connection, swap, disk,
DNS, gateway reachability (FAIL); CPU governor, THP, HF token (WARN); NUMA, kernel, OS (info).
It is report-only so that unusual but valid environments are not blocked. The operator sees a
warning block and a report.

**Q16. How are secrets handled by the installer?**
Passwords are generated (24 characters) only when no Secret exists; otherwise the existing one
is reused, so clients do not break. Connection URLs are published as Secrets. Tasks that touch
secrets run with `no_log`. The LiteLLM master key never leaves its pod: other keys are minted
there.

### Level 3 — Deep dives with worked maths

**Q17. Compute the router reward for two responses, with `target_tpt = 1.0`.**
- A: latency 3 s, 150 tokens → tpt = 0.02 → reward = 1 / 1.02 = **0.980**
- B: latency 12 s, 60 tokens → tpt = 0.2 → reward = 1 / 1.2 = **0.833**
- Failure → **0**

*Follow-up insight:* both CPU responses score near 1, so the signal is compressed. Set
`target_tpt` near the typical observed time-per-token (e.g. 0.05): A → 0.05/0.07 = 0.714,
B → 0.05/0.25 = 0.2. The bandit then separates the models much faster. *(This is my analysis
of the formula, not a statement in the repo.)*

**Q18. Explain Thompson sampling as used for model selection.**
Each model (arm) has a Beta(α, β) belief about its success probability. For each request, draw
one sample from every arm's belief and pick the arm with the highest sample. After the outcome,
update that arm (more α for success, more β for failure). Uncertain arms sometimes produce high
samples and get explored; proven arms win most of the time. A common way to use a continuous
reward r ∈ [0, 1] with a Beta-Bernoulli model is to treat r as a success probability (or as
fractional α/β updates). Optional `tier_priors` let you start with prior beliefs per arm.

**Q19. Compare Thompson sampling, UCB and ε-greedy.**
| | Exploration mechanism | Pros | Cons |
|---|---|---|---|
| ε-greedy | Random arm with probability ε | Simple | Explores blindly forever, even when clearly worse |
| UCB | Optimism bonus that shrinks with more samples | Deterministic, strong guarantees | Needs tuning (`delta`); sensitive to reward scale |
| Thompson | Posterior sampling | Excellent practical balance; natural priors | Randomised; harder to explain to stakeholders |

**Q20. Why per-tier bandits instead of one global bandit?**
A model's efficiency depends on the prompt type: fast on short SIMPLE prompts, slow on long
COMPLEX generations. Separate bandits learn these regimes independently.

**Q21. Size the default model's memory: Qwen2.5-Coder-14B at TP=4.**
Weights: 14 B params × 2 bytes (bf16) ≈ 28 GB ≈ 30.8 GiB in the doc's table. KV cache:
TP × `VLLM_CPU_KVCACHE_SPACE` = 4 × 40 = 160 GiB. Runtime/IPC ≈ 22 GiB. Total ≈ **214 GiB**.
The KV cache is ~75 % of the footprint.

**Q22. How many tokens fit in a 40 GiB KV cache?** *(general LLM knowledge, not in the repo)*
Per-token KV bytes = 2 (K and V) × layers × KV-heads × head-dim × bytes per value. For a
Llama-3.1-8B-like model (32 layers, 8 KV heads with grouped-query attention, head-dim 128, bf16):
2 × 32 × 8 × 128 × 2 = 131,072 B = **128 KiB per token** → 40 GiB / 128 KiB ≈ **327,680 tokens**,
shared by all concurrent sequences. That is why KV size sets the concurrency × context budget.

**Q23. Why does an MoE model like Qwen3-Coder-30B-A3B suit CPUs, and what is the catch?**
Only ~3 B parameters are active per token, so compute and memory bandwidth per token are
small, which suits CPUs. The catch: all 30 B parameters (~64 GiB in bf16) must stay resident.

**Q24. How does speculative decoding preserve quality?**
The draft model proposes N tokens. The target model verifies them in one forward pass and
accepts the longest agreeing prefix (then corrects the next token). The output is what the
target model would have produced, only faster when the draft guesses well.

**Q25. Why is TP=1 capped at 200 GiB memory?**
To keep the pod's memory on the single NUMA node its cores are pinned to (~252 GiB per node).
A larger limit makes NRI widen `cpuset.mems` across nodes, and vLLM then fails to bind cores
(`core ids=[]`).

### Level 4 — Security

**Q26. List the layers that stop malicious generated code.**
(1) Separate disposable pod; (2) non-root, `drop: [ALL]`, no privilege escalation, CPU/memory
limits; (3) NetworkPolicy: ingress from the router only, egress public-only (no RFC 1918, no
link-local, so no node, no Kubernetes API, no cluster services); (4) optional Kata microVM with
its own kernel; (5) optional OpenShell egress default-deny, L7 rules, Landlock, seccomp;
(6) no secrets in the sandbox (OpenShell placeholders).

**Q27. Why does the sandbox router use TokenReview?**
So that only authenticated cluster workloads can create and drive sandboxes, while clients
need no RBAC. The router is the single authenticated choke point.
*Limitation:* any ServiceAccount token in the cluster is accepted (authentication, not
fine-grained authorisation). A natural next step is audience-bound tokens or a per-namespace
allow-list.

**Q28. Why did the role add its own NetworkPolicy when the controller ships one?**
The controller's template policies select a label that warm-pool pods never carry, and a
claimed pod loses its warm-pool label. The toolkit's policy selects
`agents.x-k8s.io/sandbox-name-hash`, which every sandbox pod keeps for its whole life.

**Q29. How does OpenShell keep the API key away from the agent?**
The provider profile declares the credential as `OPENAI_API_KEY`, bearer style, for one
endpoint (LiteLLM) and a list of allowed binaries. Inside the sandbox the variable holds
`openshell:resolve:env:…`. The supervisor rewrites the header with the real virtual key only
for allowed binaries going to the allowed endpoint. Tool output is redacted before it returns to
the LLM (the example agent strips placeholders).

**Q30. Why fail-closed for the guardrail? What is the cost?**
A fail-open guard silently disables moderation when the guard breaks or its output format
changes. Fail-closed makes failures visible. The cost: guard availability becomes chat
availability, and blocks surface as HTTP 500.

**Q31. Redis has a password and is ClusterIP. Why also a NetworkPolicy and the mesh?**
Defence in depth. Each control covers a different failure: a leaked password (NetworkPolicy
still limits who can connect), a policy mistake (mTLS still authenticates the workload), an
accidental Service type change (the docs forbid NodePort/LoadBalancer).

### Level 5 — Performance

**Q32. Where does latency come from on one agent turn?**
TLS/edge → gateway auth → guard model call (pre_call, blocking) → router classification
(cheap) → model TTFT + generation (dominant) → sandbox claim (≈ 0 with a warm pool) → command
execution → memory I/O. Measure each separately (four-path method, `01-…` §4.5).

**Q33. Which Linux settings does preflight warn about, and why do they matter?**
CPU governor not `performance` (cores clock down → slower tokens) and Transparent Huge Pages
`always` (can cause latency spikes and memory bloat). It also reports NUMA topology.

**Q34. What KPIs would you put on a dashboard for this platform?**
TTFT p95, inter-token latency, tokens/s per model, request p95/p99, guardrail block rate by
reason, router tier distribution and bandit arm shares, warm-pool hit rate, sandbox acquisition
latency, Redis/pgvector latency, memory headroom per model pod, OOMKilled count, validate
status. (Full table: `02-design.md` §7.)

**Q35. The repo publishes no tokens/s numbers. How would you produce them credibly?**
Fix and record hardware, model, TP, CPU allocation and KV size. Tune nodes (governor, THP).
Benchmark vLLM direct, via LiteLLM, with the guardrail, and via the router. Sweep concurrency
with fixed and with realistic prompt sets. Report TTFT/ITL percentiles, throughput, errors and
CPU/memory per NUMA node, plus the latency-vs-throughput knee. Automate it per release (e.g.
as a Workload Services Framework test).

---

## 5. System design questions

For each one, use this structure: **clarify → requirements (functional / non-functional) →
high-level design → deep dive → trade-offs → metrics.** Reuse the toolkit's blocks as your
vocabulary.

### SD1. "Design a platform to run AI coding agents for 5,000 developers, on-prem."

- **Clarify.** Concurrency (peak simultaneous agents?), latency SLO, models allowed, data
  residency, existing hardware (Xeon? GPUs?), compliance (audit).
- **Design.** Gateway (LiteLLM) with a key per team and budgets → guardrail → router over
  tiers: small coder model on CPU for SIMPLE/MEDIUM, large MoE or GPU/cloud for
  COMPLEX/REASONING → vLLM fleets per tier, NUMA-pinned → sandboxes from warm pools sized to
  peak tool concurrency, Kata for untrusted repositories → Redis sessions, pgvector code
  memory → Langfuse + Prometheus.
- **Scale numbers to estimate.** Tool calls per task × tasks per developer per hour → peak
  sandbox claims per second → warm-pool size. LLM calls per task × tokens → required
  tokens/s → model replicas per tier.
- **Trade-offs.** CPU vs GPU per tier; Kata cost vs isolation; fail-closed guard vs
  availability (make the guard replicated, with its own SLO).
- **Gaps vs the toolkit.** HA Redis/Postgres, gateway replicas, per-namespace sandbox
  authorisation, router state shared across replicas.

### SD2. "Add a GPU tier without changing any agent."

Register the GPU endpoint in LiteLLM as a new model. Add it to the router's `COMPLEX` and
`REASONING` `tier_candidates` (or use a vLLM-SR decision). Agents keep calling `hybrid-router`.
Watch tier distribution and reward. Use `quality_weight` if the GPU model is also better, not
only faster.

### SD3. "Make the memory layer highly available."

Redis: replication with Sentinel, or Redis Cluster, or an operator; decide what may be lost
(sessions are often reconstructable). Postgres: an operator-managed primary with replicas
(the platform layer already has a PostgreSQL cluster component), PITR backups. Keep the same
Secrets/URLs so clients do not change (Provider Pattern).

### SD4. "Multi-tenant isolation: two business units must not see each other's data."

Separate virtual keys and model allow-lists per tenant; separate namespaces with the mesh
label; per-tenant databases/schemas in pgvector and Redis ACL users (the Docker path already
uses per-service ACL users); per-tenant sandbox namespaces and warm pools; NetworkPolicies
between tenant namespaces; Langfuse projects per tenant.

### SD5. "Scale the router to multiple LiteLLM replicas."

Bandit state is per process, so replicas learn independently. That is fine statistically but
slower to converge. Options: shared state in Redis (atomic α/β increments), periodic
synchronisation, or sticky routing. Weigh consistency against added latency on the hot path.

---

## 6. Debugging scenarios

For each one, say **symptom → hypothesis → check → fix**.

| # | Symptom | Likely cause | Check | Fix |
|---|---|---|---|---|
| D1 | Every chat request returns HTTP 500 "Blocked by the content-safety guardrail: guard unreachable" | Guard vLLM down / still loading / OOM | `kubectl get pods -n llm-inference \| grep qwen3guard`; describe pod | Wait for load; raise memory (8 Gi is too small, peak ~8.6 GiB); redeploy `./model-manager deploy qwen3guard` |
| D2 | Long prompts blocked: "prompt is longer than the guard model's context window" | Guard context < served model context | Compare `max_model_len` of both | Use a longer-context guard or chunked screening; do **not** just raise `--max-model-len` |
| D3 | Model pod `CrashLoopBackOff`, exit code **137** | OOM-killed: footprint > memory limit | `kubectl describe pod` (OOMKilled) | Raise `memory` in `models.yaml`, lower `VLLM_CPU_KVCACHE_SPACE` carefully, or increase TP |
| D4 | Second model deploy fails: `NRI pre-flight failed: not enough physical cores` | First model used `cpu: auto` (a whole NUMA node) | `models.yaml` cpu values | Set explicit `cpu:` per model; undeploy and re-install |
| D5 | `CreateContainerError: no balloon for annotation` | TP doesn't match the balloon topology | Model's TP vs NUMA nodes | Fix `--tensor-parallel-size` |
| D6 | Redis client error `WRONGPASS` | URL `redis://:<pw>@…` without a username | The URL used | Use `redis://default:<pw>@…` from the `REDIS_URL` Secret |
| D7 | SDK call to sandbox router returns `401` | Missing/invalid ServiceAccount token | Request headers | `kubectl create token …`; set `sandbox.connector.session.headers["Authorization"]` |
| D8 | Code in sandbox cannot `pip install` | Egress policy / no proxy / public DNS blocked on this network | NetworkPolicy, OpenShell `DENIED` logs | Pre-bake packages in the image; on proxied networks use the OpenShell path or a custom template |
| D9 | `pip install` in OpenShell sandbox returns `403 Forbidden` | Deny-all policy, by design | `openshell logs <sb> \| grep DENIED` | Add an endpoint to the sandbox `--policy` at create time |
| D10 | OpenShell model call: `binary … not allowed in policy '_provider_genai_gateway'` | The calling executable is not allow-listed | Resolved binary path | Add the path to `genai-gateway-provider.yaml` and re-run, or `provider profile update` |
| D11 | Kata sandbox `FailedCreatePodSandBox … ENOENT` | devmapper snapshotter not active (kata-fc) | `systemctl status containerd-devmapper`; `ctr plugins ls` | Fix the thin-pool or use `kata-qemu` |
| D12 | Kata pod runs but `uname -r` equals the host | It landed on runc | `spec.runtimeClassName` | Use `warmpool="kata-pool"`; check node labels |
| D13 | `kubeadm token create` fails with `secrets is forbidden` on re-install | An earlier install stopped mid-`kubeadm` | Preflight "unfinished Kubernetes install" | `teardown kubernetes`, then install |
| D14 | vLLM-SR loses config hot-reload: "too many open files" | `fs.inotify.max_user_instances` default 128 exhausted | `sysctl fs.inotify` | Raise to 8192 / watches 1048576 (prerequisites) |
| D15 | Hybrid Router always sends to the same model | Only one candidate in that tier, or rewards indistinguishable | Router logs, `router_state()` | Add candidates; tune `target_tpt`; check tier boundaries |
| D16 | Ray client connection errors | Client Ray version ≠ cluster image | `ray.__version__` | Pin `ray[default]==2.40.0` |
| D17 | Node-level steps (Kata, CPU pinning) configured the wrong machine | Missing `ansible_connection` on a node | Preflight node-connection check | Add `ansible_connection: ssh` (or `local` for the installer host) |

---

## 7. Trade-off and opinion questions

Good answers name **both sides** and a **condition** that would change your mind.

- **"Is CPU inference a good idea?"** For agent control planes and small-to-mid models with
  routing, yes: cost, availability and data residency. For large dense models at high
  concurrency, GPUs win on throughput, so keep them as an extra tier behind the same gateway.
  Decide per tier, with measured tokens/s per dollar.
- **"Rules classifier or ML classifier for routing?"** Rules: free, explainable, tunable, but
  brittle. Embedding classifier (vLLM-SR): more robust, but adds a model call. Start with rules
  plus a bandit; move to embeddings if misrouting shows up in task-success metrics.
- **"Fail-closed or fail-open?"** For safety checks, fail-closed, but invest in the guard's
  availability (replicas, capacity), because it is now on the critical path. For non-safety
  checks (e.g. a latency optimiser), fail-open.
- **"Warm pools: how big?"** Size from peak claim rate × claim lifetime (Little's law:
  L = λ × W). Too small means cold starts; too big wastes idle resources.
- **"Why not a dedicated vector DB?"** pgvector keeps relational and vector data together with
  one operational system. Move to a dedicated engine when scale or recall/latency targets
  require it, measured with the recall@k and p95 KPIs.
- **"Ansible vs GitOps?"** Ansible fits bare-metal plus host-level steps and the parent
  installer. GitOps (Argo/Flux) is better for continuous reconciliation of in-cluster state.
  A hybrid is common.
- **"Report-only preflight: risky?"** It avoids false blocks. The risk of ignored warnings is
  mitigated by a loud warning block and a persistent report. A `--strict` flag would be a
  reasonable addition.

---

## 8. Behavioural answers (STAR templates)

Fill these **only with true experiences**. Situation · Task · Action · Result. Quantify where
you can.

1. **"Tell me about learning a complex system quickly."**
   S: new to agent infrastructure. T: understand a multi-layer platform. A: read the code, not
   only the docs. Mapped layers via `components.yaml`, traced one request end to end, drew
   architecture, component and sequence diagrams, wrote ADRs. R: (your outcome, e.g. you can
   explain and deploy it; documents shared with the team).
2. **"A time you found a gap or risk."** Candidate observations from this study: no published
   inference benchmarks; single-instance memory stores; router reward compression with default
   `target_tpt`; any ServiceAccount token accepted by the sandbox router. Describe how you
   would raise and validate it.
3. **"A trade-off you had to make."** Use fail-closed vs availability, or Kata isolation vs cost.
4. **"Working across teams."** This project spans layers owned by different groups (platform,
   inference, agent toolkit). Discuss interface contracts (`components.yaml`, OpenAI API) as a
   way to coordinate.

---

## 9. Hands-on rehearsal script

If you have a lab machine that meets the prerequisites, run these and narrate what each one
proves. (Each command comes from the repository docs.)

```bash
git clone -b release-1.2 https://github.com/intel/enterprise-ai-solutions.git && cd enterprise-ai-solutions
```

```bash
./es_auto_installer.sh configure
```

```bash
./es_auto_installer.sh init agent-toolkit
```

```bash
export HF_TOKEN=hf_xxx && ./es_auto_installer.sh install agent-toolkit
```

```bash
export KUBECONFIG=$PWD/env/local/kubeconfig.yaml && kubectl get pods -A
```

```bash
./es_auto_installer.sh validate agent-toolkit
```

```bash
export LITELLM_MASTER_KEY=$(kubectl get secret litellm-master-key -n litellm -o jsonpath='{.data.master_key}' | base64 -d)
```

```bash
curl -k https://litellm.<base_domain_name>/v1/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer ${LITELLM_MASTER_KEY}" -d '{"model":"hybrid-router","messages":[{"role":"user","content":"What is a Python list?"}],"max_tokens":100}'
```

```bash
kubectl logs -n litellm deploy/litellm -c litellm --tail=50 | grep HybridRouterProxy
```

```bash
kubectl get sandboxwarmpool -n agent-sandbox-system
```

```bash
kubectl exec -n redis redis-stack-server-0 -- sh -c 'redis-cli -a "$REDIS_PASSWORD" --no-auth-warning ping'
```

No cluster? Use the Docker path (`./docker/deploy.sh` from an `enterprise-agent-toolkit`
checkout; 96+ cores, 128 GB RAM) to practise the gateway and memory parts.

---

## 10. Questions to ask the interviewer

- Which blocks do your customers swap most often, and why?
- How do you benchmark CPU inference per Xeon generation, and how do results feed model defaults?
- Is router bandit state shared across LiteLLM replicas today? How do you evaluate routing quality, not only speed?
- What is the plan for output-side guardrails and PII detection, given the `pre_call` latency budget?
- How are rack-scale and Intel® Arc™ paths prioritised for upcoming releases?
- What does on-call look like for a customer deployment: which failures are most common?

---

## 11. Seven-day study plan and self-check

| Day | Focus | Output |
|---|---|---|
| 1 | `01-…` Levels 0–1, Q1–Q3 | 30-second pitch, out loud |
| 2 | Q4 tech stack + performance | Explain KV cache, NUMA, speculative decoding |
| 3 | Q5 agentic AI + ML concepts | Router reward maths by hand; Thompson vs UCB |
| 4 | `02-design.md` §2–4 + diagrams | Draw the whiteboard from memory |
| 5 | ADR-001…012 | One-sentence decision + one trade-off for each |
| 6 | §5 system design + §6 debugging | Two mock design sessions (45 min each) |
| 7 | Full mock interview | Record yourself; fix weak answers |

**Self-check: you are ready when you can, without notes:**

- [ ] Give the 30-second and 2-minute pitches.
- [ ] Draw the architecture and the request sequence.
- [ ] Say which components live in *this* repo and which come from the inference/platform layers.
- [ ] Compute the router reward and explain the bandit choice.
- [ ] Size a model's memory (weights + TP × KV + runtime).
- [ ] List six sandbox security layers.
- [ ] Explain fail-closed, with its cost.
- [ ] Diagnose D1, D3, D4, D6 and D7 from the symptom alone.
- [ ] Name five KPIs and the tool that measures each.
- [ ] State two limitations and how you would fix them.
