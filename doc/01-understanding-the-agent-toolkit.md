# Understanding the Intel® Agent Toolkit — from zero, one level at a time

> **Who this is for.** Any engineer: backend, frontend, QA, DevOps, data, or a manager who
> reads code. No prior knowledge of AI, Kubernetes or Intel hardware is assumed.
>
> **How to read it.** The document climbs a ladder. Each **Level** builds on the one before.
> Every level ends with a short **"Check yourself"** box: if you can answer those questions
> in your own words, go up a level; if not, re-read that level. Do not skip levels.
>
> **Where the facts come from.** Everything here is taken from the repository itself
> (`README.md`, `docs/`, `roles/`, `charts/`, `docker/`, `components.yaml`, `config.yaml`),
> fork `praveennish/agent-toolkit`, upstream `intel/enterprise-agent-toolkit`. When this
> document gives an **interpretation** rather than a fact from the repo, it says so with the
> label **🔎 Interpretation**.

---

## Contents

- [Level 0 — The words you need first](#level-0--the-words-you-need-first)
- [Level 1 — What is this project, in one breath?](#level-1--what-is-this-project-in-one-breath)
- [Q1 — What is the purpose of this project?](#q1--what-is-the-purpose-of-this-project)
- [Q2 — Which business goal of Intel does it serve?](#q2--which-business-goal-of-intel-does-it-serve)
- [Q3 — What is the nature of the project?](#q3--what-is-the-nature-of-the-project)
- [Q4 — Tech stack, performance tools, performance analysis report](#q4--tech-stack-performance-tools-performance-analysis-report)
- [Q5 — Which parts of Agentic AI and Machine Learning does it touch, and which problems does it solve?](#q5--which-parts-of-agentic-ai-and-machine-learning-does-it-touch-and-which-problems-does-it-solve)
- [Level 6 — Putting it all together](#level-6--putting-it-all-together)
- [Glossary](#glossary)

---

## Level 0 — The words you need first

Before any question can be answered, we need a shared vocabulary. Read these slowly.
Each one has an everyday picture next to it.

| Word | Plain meaning | Everyday picture |
|---|---|---|
| **Model** (AI model) | A big file of numbers, learned from data, that turns an input into an output. | A recipe that has been tuned by tasting thousands of dishes. |
| **LLM** (Large Language Model) | A model that reads text and writes text. Examples: Llama, Qwen, Gemma, GPT, Claude. | A very well-read assistant who answers in writing. |
| **Token** | The small piece of text an LLM reads or writes (roughly ¾ of a word). Speed and cost are measured in tokens. | Syllables. |
| **Inference** | *Using* a trained model to get an answer. (Training is *making* the model; this project does not train.) | Cooking with a finished recipe. |
| **Serving / inference server** | A program that keeps a model loaded in memory and answers requests over HTTP. Here: **vLLM**. | The kitchen that is always open. |
| **Prompt** | The text you send to the LLM. | The order you give the kitchen. |
| **Agent** | A program that uses an LLM to *decide what to do next*, then *does it* using **tools**, looks at the result, and repeats until the job is done. | An intern who plans, acts, checks, and tries again. |
| **Tool** | A function the agent is allowed to call: run code, search a database, call an API. | The intern's keyboard, phone and filing cabinet. |
| **Memory** | What the agent remembers: what happened earlier in this conversation (short-term) and what it learned in past conversations (long-term). | A notepad (short-term) and an archive (long-term). |
| **Embedding** | A list of numbers that represents the *meaning* of a piece of text. Similar meanings → similar numbers. | GPS coordinates for ideas. |
| **Vector database** | A database that can find "the stored texts whose embeddings are closest to this one". Here: **pgvector**, **RediSearch**. | "Find books similar to this one" in a library. |
| **RAG** (Retrieval-Augmented Generation) | Look up relevant documents first, paste them into the prompt, then ask the LLM. | Opening the textbook before answering the exam question. |
| **Sandbox** | An isolated box where untrusted code can run without harming anything outside it. | A sandpit: dig as much as you like, the garden is safe. |
| **Container** | A packaged program plus everything it needs, run in isolation (Docker). | A shipping container: same box everywhere. |
| **Kubernetes (K8s)** | Software that runs many containers across many machines and keeps them healthy. | An airport control tower for containers. |
| **Pod / Namespace** | A pod is one running unit (one or more containers). A namespace is a folder that groups pods. | A pod = one flat; a namespace = one building. |
| **Helm chart** | A packaged, parameterised set of Kubernetes files. | A flat-pack furniture kit with options. |
| **Ansible** | A tool that runs scripted steps (tasks) on machines, written in YAML. | A checklist a robot follows. |
| **CPU / GPU** | CPU = general-purpose processor (Intel® **Xeon®** is Intel's server CPU). GPU = processor built for massive parallel maths. | CPU = a team of skilled chefs. GPU = a factory line. |
| **Gateway** | One front door that every request passes through, so security and accounting happen in one place. | Reception desk of an office. |
| **Observability** | Being able to see what the system did: logs, metrics, traces. | CCTV and a flight recorder. |

> **Check yourself (Level 0)**
> 1. What is the difference between *training* and *inference*? Which one does this project do?
> 2. What makes an *agent* different from a plain chatbot?
> 3. Why would you want code written by an AI to run in a *sandbox*?

---

## Level 1 — What is this project, in one breath?

> **The Intel® Agent Toolkit is a ready-made, open-source "back office" for AI agents.
> You bring the agent (the brain). The toolkit installs everything the agent needs around
> it — a secure front door to the models, the models themselves running on Intel® Xeon®
> CPUs, memory, a safe place to run code, and cameras that record everything — on a
> Kubernetes cluster, with one command.**

The README's own one-line summary:

> *"Deploy a production-grade, open source agentic AI stack on Intel® Xeon® in hours — not months."*

An analogy that will carry us through the whole document:

| Restaurant | Agent Toolkit |
|---|---|
| The chef's skill and recipes | **Your agent** (written with LangGraph, CrewAI, …) — *not* part of the toolkit |
| Front desk that checks reservations and bills each table | **API Gateway** (LiteLLM) |
| The ovens (big and small) | **LLM inference** (vLLM on Xeon, optional GPUs/cloud) |
| A head waiter who sends simple orders to the fast oven and hard ones to the big oven | **Hybrid Router** |
| Food-safety inspector at the door | **Guardrails** (content-safety model) |
| Order pad + recipe archive | **Memory** (Redis + pgvector) |
| A fire-proof test kitchen for risky experiments | **Sandbox** (Agent Sandbox, Kata, OpenShell) |
| CCTV and the accounts book | **Observability** (Langfuse, Prometheus, Grafana) |
| The building contractor who builds all of the above in a day | **Deployment automation** (Ansible + Helm + installer) |

The toolkit is the **restaurant building and staff**, not the chef.

> **Check yourself (Level 1)**
> 1. If someone says "the toolkit is an agent framework like LangGraph", what would you correct?
> 2. Name four things the toolkit provides *around* an agent.

---

## Q1 — What is the purpose of this project?

### Level 1 answer (the simple version)

Building one AI agent demo is easy. Running agents **safely and reliably for a whole
company** is hard, because you suddenly need a dozen other systems. The purpose of this
project is to **give companies those dozen systems pre-built, pre-connected and tested on
Intel® Xeon®**, so they can start running agents in hours instead of spending months
gluing open-source pieces together.

### Level 2 answer (the problems it removes)

The README's "Why This Matters" and "Business Value at a Glance" sections list the problems
directly. Here they are, each paired with the part of the toolkit that solves it:

| Problem a company hits | What the toolkit provides | Default component |
|---|---|---|
| Months spent integrating pieces | Everything pre-integrated, installed by one command | `es_auto_installer.sh install agent-toolkit` |
| Who may call which model, how much may they spend? | One secure entry point with keys, budgets, rate limits | LiteLLM "GenAI Gateway" |
| Big models are slow and expensive for easy questions | Send each request to the smallest model that can handle it | Hybrid Router |
| Agents forget everything between steps and sessions | Short-term and long-term memory | Redis Stack, PostgreSQL + pgvector |
| An agent may run dangerous code | Disposable, isolated execution boxes | Agent Sandbox (+ Kata microVMs, OpenShell) |
| Harmful prompts reach the model | A safety model screens every request first | Guardrail with Qwen3Guard |
| "Why did the agent do that?" | Every token, latency and step recorded | Langfuse, Prometheus, Grafana, Loki |
| Dependence on expensive GPUs | Run inference on CPUs by default, add GPU/cloud only where needed | vLLM on Xeon |
| Fear of lock-in | Every block can be swapped (the **Provider Design Pattern**) | — |

### Level 3 answer (the precise scope)

Be careful with one detail that confuses many readers: **this repository is one layer of a
larger installer.**

- The installer is **Toolkit Manager** in the separate `intel/enterprise-ai-solutions`
  repository (`es_auto_installer.sh`).
- That installer is organised in **layers**: infrastructure → platform → inference →
  **agent-toolkit**.
- `components.yaml` in this repository declares:
  `layer: agent-toolkit, depends_on: [platform, inference]`.

So, strictly, **this repository's code installs**:

| Component | Role | Default |
|---|---|---|
| `redis_stack` | Short-term memory, session state, semantic cache | on |
| `pgvector` | Long-term memory, RAG vector store | on |
| `agent_sandbox` | Isolated code execution (+ Kata template when enabled) | on |
| `openshell` | Policy-enforced sandboxes, credential isolation | off |
| `kuberay` | Ray cluster for parallel tool execution | off |
| `keycloak_agent_config` | Keycloak realm `agent-toolkit` (only when auth is Keycloak/JWT) | off with LiteLLM auth |

…plus a **preflight** playbook (node readiness), a **Docker Compose** path for
developers, and the **documentation** for the whole stack. The gateway (LiteLLM), the
model servers (vLLM/KServe), the Hybrid Router code, guardrails, Langfuse, Kubernetes,
Istio and the observability stack are installed by the *other* layers. The docs here
explain them because together they form the product.

> 🔎 **Interpretation.** Read the project as a *product* made of many repositories, with this
> one owning the **agent-specific services** and the **story** (docs) of the whole stack.

> **Check yourself (Q1)**
> 1. Which file tells you this repository is a *layer* and what it depends on?
> 2. Is the Hybrid Router's code in this repository? Where is it installed from?
> 3. Which agent-toolkit components are *on* by default?

---

## Q2 — Which business goal of Intel does it serve?

### Level 1 answer

Intel sells processors. Most AI conversations focus on GPUs. This project argues, and shows
in working code, that **a large part of an AI-agent system runs very well on Intel® Xeon®
CPUs**, so companies can build agent platforms on servers they already know (and buy).

### Level 2 answer — what the repository itself says

The README states the reasoning plainly:

> *"**The core insight:** GPUs accelerate reasoning. But the value of agentic AI comes from
> end-to-end task execution — and that control plane (state, tools, policy, coordination)
> runs efficiently on CPUs."*

and:

> *"Does it require a GPU? No. The toolkit is designed to run AI agent workloads efficiently
> on Intel® Xeon® CPUs using AMX acceleration."*

Other direct signals in the repository:

- Every LLM in the default catalog is a **CPU model** served by vLLM on Xeon, with
  per-model CPU sizing (`docs/xeon-model-configuration.md`).
- The **Hybrid Router** sends easy requests to small models: that is what makes CPU
  inference practical.
- The docs point to the **Intel AI Performance Advisor** to size Xeon servers
  (`docs/single-node-deployment.md`).
- Badges and FAQ stress: *on-premise*, *air-gapped*, *data residency*, *regulated
  industries*, *Apache 2.0*, *no lock-in*.
- "Build vs. Build-from-Scratch" table: time to production *3–6 months → hours to days*;
  total cost of ownership *High → Low (open source + Xeon)*.

### Level 3 answer — the business goals, stated clearly

> 🔎 **Interpretation** (built only from the evidence above):

| Business goal | How the project serves it |
|---|---|
| **1. Grow Xeon demand in the AI era** | Prove that agent control planes *and* a useful share of LLM inference run on Xeon (bf16, AMX, NUMA-aware vLLM). Every deployment is a Xeon deployment. |
| **2. Win the enterprise / on-prem / private-AI segment** | Companies that cannot send data to a public cloud (banks, healthcare, government) need a private, air-gappable stack. The toolkit targets exactly that. |
| **3. Lower the barrier to adoption** | Time-to-value is the main obstacle to selling platforms. A one-command install removes months of integration work and puts the evaluation on Intel hardware. |
| **4. Reduce total cost of ownership versus GPU-only designs** | CPU first, GPU/cloud only for the hardest reasoning, steered automatically by the router: a cost argument customers can act on. |
| **5. Build an open ecosystem around Intel platforms** | Apache 2.0, standard components (Kubernetes, LiteLLM, vLLM, Ray), works with every agent framework. Partners and customers can extend it without asking Intel. |

> **Check yourself (Q2)**
> 1. Quote the README's "core insight" in your own words.
> 2. Why does a *router* help a CPU-first business argument?
> 3. Which customer segment benefits most from "air-gapped, on-prem"?

---

## Q3 — What is the nature of the project?

### Level 1 answer

It is **not** an app, **not** an AI model and **not** an agent framework. It is a
**platform blueprint plus the automation that builds it**, a kind of project often called
*infrastructure-as-code* or *platform engineering*.

### Level 2 answer — classify it on several axes

| Axis | This project |
|---|---|
| **Type** | Reference platform / solution blueprint for running AI agents in production |
| **Main artefacts** | Ansible roles, Helm charts, Kubernetes manifests, Docker Compose files, Bash scripts, documentation |
| **Languages in the repo** | YAML (Ansible + Helm + K8s), Jinja2 templates, Go templates (Helm), Bash. README: *Shell 88 %, Jinja 10 %, Go Template 2 %* |
| **Users** | Platform / DevOps / MLOps engineers who install and run it; agent developers who build on it |
| **Licence** | Apache 2.0 (open source) |
| **Delivery** | Versioned releases (docs reference `release-1.2`; several features are marked *"not available in this release"*) |
| **Deployment targets** | Kubernetes single-node, multi-node, (rack-scale, not in this release); Docker Compose for development |
| **Quality gates (CI)** | ansible-lint, ShellCheck, Bandit, Checkov, Trivy, OpenSSF Scorecard, dependency review (`.github/workflows/`) |

### Level 3 answer — how the code is organised

```
agent-toolkit/
├── README.md, docs/          ← the product story + one guide per feature
├── components.yaml           ← registers this layer + its components with Toolkit Manager
├── config.yaml               ← default switches (seeded into env/<name>/config.agent-toolkit.yaml)
├── roles/<component>/        ← one Ansible role per component
│   ├── defaults/main.yaml    ←   tunable settings (namespace, versions, sizes)
│   └── tasks/{main,install,validate,teardown}.yaml   ← lifecycle actions
├── charts/                   ← Helm charts (redis-stack, pgvector, kuberay) + sandbox/OpenShell YAML
├── playbooks/preflight*      ← node-readiness checks and HTML/TXT/JSON report
└── docker/                   ← Docker Compose path for developers (deploy.sh + generators)
```

The pattern to remember: **every component has the same four verbs**, chosen by
`component_action`:

```yaml
# roles/<component>/tasks/main.yaml (same shape for all six roles)
- include_tasks: "{{ component_action | default('install') }}.yaml"
  when: component_action != 'install' or <component>_enabled
```

So `install`, `validate` and `teardown` are uniform across the stack. This uniformity is the
"nature" of the codebase: **declarative, idempotent, switch-driven automation**.

> **Check yourself (Q3)**
> 1. What are the four task files every role has, and what does each do?
> 2. Name three CI security tools the project runs.
> 3. Why is "idempotent" (safe to re-run) important for an installer?

---

## Q4 — Tech stack, performance tools, performance analysis report

### 4.1 Tech stack — Level 1 (the shape)

Think of the stack as floors of a building, bottom to top:

```
 Floor 7   Your agent (LangGraph · CrewAI · Microsoft Agent Framework · OpenClaw)
 Floor 6   Observability: Langfuse · Prometheus · Grafana · Loki
 Floor 5   Agent services: Redis · pgvector · Agent Sandbox · OpenShell · KubeRay
 Floor 4   Gateway & routing: LiteLLM · Hybrid Router · Guardrail · vLLM Semantic Router
 Floor 3   Inference: vLLM on KServe (CPU) · OpenVINO Model Server (Docker path)
 Floor 2   Platform: Kubernetes · Helm · Istio · Envoy Gateway · cert-manager · MetalLB
 Floor 1   Hardware: Intel® Xeon® (AMX, NUMA) · optional GPUs / cloud LLMs
```

See the picture: [`diagrams/architecture.png`](diagrams/architecture.png).

### 4.2 Tech stack — Level 2 (the full table)

| Layer | Technology | Version pinned in repo | Why it is there |
|---|---|---|---|
| Hardware | Intel® Xeon® | — | Runs everything; AMX speeds up bf16 maths for CPU inference |
| OS | Ubuntu 22.04 / 24.04, RHEL | — | Host operating system |
| Cluster | Kubernetes via **Kubespray** | — | Runs and heals all services |
| Packaging | **Helm**, raw manifests | — | Install charts with parameters |
| Automation | **Ansible** (≥ 2.15) + `kubernetes.core` collection | — | Install / validate / teardown each component |
| Service mesh | **Istio ambient** (strict mTLS) | — | Encrypts and authenticates traffic between namespaces |
| Network policy | Kubernetes **NetworkPolicy** (Calico CNI) | — | Firewall rules between pods |
| Edge | **Envoy Gateway**, cert-manager, MetalLB | — | HTTPS entry, certificates, load-balancer IPs |
| CPU pinning | **NRI balloons** policy, **NFD** | — | Pin each model to the cores of one NUMA node |
| Storage | local-path / NFS / Ceph (Rook) | — | Persistent volumes |
| Gateway | **LiteLLM** | `v1.83.14-stable.patch.2` (Docker) | OpenAI-compatible proxy: keys, budgets, routing, callbacks |
| Routing | **Hybrid Router** (custom LiteLLM callback); **vLLM Semantic Router** (optional) | — | Pick the right model per request |
| Safety | LiteLLM `custom_code` guardrail + **Qwen3Guard-Gen-0.6B** | — | Content-safety screening |
| Inference | **vLLM** (CPU) on **KServe**; **OpenVINO Model Server** (Docker option) | vLLM CPU `v0.24.0`, OVMS `2025.4.1` (Docker) | Serve LLMs, embeddings, rerankers |
| Models | Qwen2.5-Coder-14B (default), Qwen3-Coder-30B-A3B, Llama-3.1-8B, Gemma-4-26B-A4B, Qwen3-30B-A3B, Qwen3.6-35B-A3B, bge-base-en, bge-reranker, Qwen3Guard | — | Chat, coding, embeddings, reranking, safety |
| Short-term memory | **Redis Stack** (RediSearch) | `redis-stack-server:7.4.0-v8` (Docker) | Session state, cache, vector search |
| Long-term memory | **PostgreSQL 16 + pgvector** | image `pgvector/pgvector:pg16`, ext `0.8.0` | Persistent vectors, RAG, structured state |
| Sandbox | **kubernetes-sigs/agent-sandbox** + `k8s-agent-sandbox` SDK | `v1.0.10` | Ephemeral isolated pods for code execution |
| Strong isolation | **Kata Containers** (Firecracker `kata-fc` / QEMU `kata-qemu`) | `3.32.0` | microVM per sandbox (own guest kernel) |
| Policy sandbox | **NVIDIA OpenShell** | `0.1.6` | Egress default-deny, L7 rules, Landlock, credential isolation |
| Parallel compute | **KubeRay** operator + Ray | operator `1.3.0`, Ray `2.40.0` | Parallel tool calls, autoscaled workers |
| Identity | **Keycloak** realm (optional) | — | JWT auth alternative to LiteLLM keys |
| Observability | **Langfuse**, Prometheus, Grafana, Loki, Tempo, OTel Collector, Node Exporter | — | Traces, metrics, logs, dashboards |
| Dev path | **Docker Compose** (+ Flowise low-code builder) | Flowise `3.1.2` | Single-machine development and demos |
| CI | GitHub Actions: ansible-lint, ShellCheck, Bandit, Checkov, Trivy, Scorecard, dependency-review | pinned by commit SHA | Code quality and supply-chain security |

### 4.3 Performance tools — Level 2

"Performance tools" here means two kinds of thing: **features that make it fast** and
**instruments that measure speed**.

**A. Features that make it fast (built into the configuration)**

| Feature | Where | What it does, simply |
|---|---|---|
| **bf16 + Intel® AMX** | vLLM CPU args `--dtype bfloat16` | Half-size numbers that Xeon's AMX units multiply very fast |
| **NUMA-aware pinning (NRI balloons)** | `cpu: auto`, `docs/xeon-model-configuration.md` | Keeps a model's threads and memory on one socket's memory node, avoiding slow cross-socket memory access |
| **Tensor parallelism (TP)** | `--tensor-parallel-size` 1/2/4 | Splits one model across several NUMA nodes so more cores work at once |
| **KV cache sizing** | `VLLM_CPU_KVCACHE_SPACE` (GB) | Memory reserved for the attention cache: more = longer contexts / more parallel requests |
| **Prefix caching, chunked prefill** | vLLM args `--enable-prefix-caching`, `--enable_chunked_prefill` | Reuse work for repeated prompt beginnings; interleave long prompts with generation |
| **Speculative decoding** | `-specdec` model variants | A tiny "draft" model guesses tokens, the big model verifies them in parallel → lower latency |
| **MoE models** | Qwen3-Coder-30B-**A3B** (3 B active of 30 B) | Only a fraction of the weights is used per token → faster on CPU |
| **Quantisation (Docker/OpenVINO)** | `weight_format: int4/int8` | Smaller numbers → less memory, faster |
| **Hybrid Router** | LiteLLM callback | Easy prompts go to small fast models; bandit learns the fastest model per tier |
| **Warm pools** | `SandboxWarmPool` (python-pool = 5) | Sandboxes are created *before* they are needed: no cold start |
| **Ray autoscaling** | `kuberay_worker_min/max_replicas` | Adds workers when tool calls pile up |
| **Node tuning checks** | preflight: CPU governor `performance`, THP not `always` | Flags common Linux settings that slow inference |
| **Native-BGP fabric networking** (rack-scale, not in this release) | Calico BGP, MTU 9000 | No encapsulation overhead between pods |

**B. Instruments that measure performance**

| Tool | Measures | How you use it |
|---|---|---|
| **Langfuse** | Per-request latency, tokens, cost, model chosen | UI → project `inference` → Tracing → `litellm_request` |
| **Prometheus + Grafana** | CPU, memory, request metrics, dashboards | Observability layer (`observability_enabled: true`) |
| **Loki / Tempo / OTel** | Logs and distributed traces | Same stack |
| **Hybrid Router logs + `router_state()`** | Tier chosen, model chosen, bandit arm statistics | `kubectl logs -n litellm deploy/litellm -c litellm -f` |
| **Ray Dashboard** | Task throughput, worker utilisation | `https://ray.<domain>/` |
| **Preflight report** | Node readiness: governor, THP, NUMA, swap, disk, DNS | `env/<name>/logs/health-report-latest.{html,json,txt}` |
| **`validate`** | Functional health of each component | `./es_auto_installer.sh validate agent-toolkit` → `failed=0` |
| **iperf3** | Network throughput between pods | Rack-scale guide (Step 6) |
| **fio** | Storage throughput / IOPS on Ceph | Rack-scale guide (Step 7) |
| **Intel AI Performance Advisor** | Sizing estimates for Xeon (cloud and on-prem) | Linked from the deployment guides |

> 🔎 **Related but separate.** Intel's **Workload Services Framework** (a separate Intel
> repository) is a benchmarking framework for Xeon workloads (`ctest.sh`,
> `list-kpi.sh`). It is *not* part of the Agent Toolkit, but it is the kind of harness you
> would use to produce repeatable inference benchmarks for a report like the one below.

### 4.4 Performance analysis report — Level 3

**Read this first, honestly:** the repository publishes **no measured LLM throughput or
latency numbers** (no tokens/second, no time-to-first-token). What it does publish:
(a) measured **network and storage** results for the rack-scale design, (b) **memory sizing**
estimates per model, and (c) a number of **operational timings and limits**. Those are
collected below. Section 4.5 then shows how to produce the missing inference report
yourself.

**(a) Measured — rack-scale fabric** (Intel Lab201, Arista Clos, Intel® E810-C NICs at
100G; 3 control-plane, 3 NVMe storage, 6 GNR-AP compute nodes; `docs/rack-scale-deployment.md`,
feature not in this release):

| Metric | Result | What it tells you |
|---|---|---|
| Cross-leaf iperf3 (4 streams, 100G links) | **83.1 Gbit/s** | ~83 % of line rate pod-to-pod |
| Cross-leaf pod round-trip time | **0.7 ms** | Sub-millisecond east-west latency |
| Encapsulation overhead | **None** (native BGP) | No VXLAN/IPIP cost |
| Ceph sequential write (fio, 4 jobs) | **1.42 GB/s** | |
| Ceph random 4K read (concurrent burn) | **29,000 IOPS** | |
| Ceph random 4K write (concurrent burn) | **12,500 IOPS** | |
| Fabric NIC use under storage burn | ~18–20 Gbit/s | **Bottleneck = NVMe drives, not the network** |
| BGP sessions / stability | 11/11 established; no errors under burn | |

**(b) Estimated — memory footprint per model** (BF16 weights; `docs/xeon-model-configuration.md`).
Formula: *total ≈ weights (params × 2 bytes) + draft model + KV cache (TP × `VLLM_CPU_KVCACHE_SPACE`) + runtime buffer*.

| Model | TP | Weights | KV cache | Runtime | ≈ Total |
|---|---|---|---|---|---|
| Llama-3.1-8B-Instruct | 1 | 16.8 GiB | 40 GiB | 12 GiB | **~69 GiB** |
| Llama-3.1-8B-Instruct (specdec) | 2 | 16.8 + 2.6 draft | 80 GiB | 16 GiB | **~116 GiB** |
| Qwen2.5-Coder-14B-Instruct | 4 | 30.8 GiB | 160 GiB | 22 GiB | **~214 GiB** |
| Qwen3-Coder-30B-A3B-Instruct | 4 | 64.0 GiB | 240 GiB | 24 GiB | **~328 GiB** |
| google/gemma-4-26B-A4B-it | 4 | 55.0 GiB | 160 GiB | 22 GiB | **~238 GiB** |
| Qwen3.6-35B-A3B | 4 | 73.5 GiB | 200 GiB | 26 GiB | **~300 GiB** |

Lesson visible in the table: **on CPU, the KV cache, not the weights, usually dominates
memory.** Memory limits by TP: TP=1 → limit 200 GiB (kept on one NUMA node); TP ≥ 2 →
limit 400 GiB.

**(c) Operational timings, sizes and limits stated in the docs**

| Item | Value | Source |
|---|---|---|
| Fresh single-node install | **20–40 min** (+10–15 min for model weights) | single-node guide |
| Default install memory request | **~131 GiB** (model 96 + Qwen3Guard 16 + router 2 + rest 17) → does *not* fit a 128 GB node | single-node guide |
| Minimum / recommended node | 48 / 96+ cores, 32 / 64 GB RAM, 150 / 200 GB disk | prerequisites |
| Guard model real peak | ~8.6 GiB (8 GiB limit is OOM-killed, exit 137) | guardrails |
| Guard KV cache | 4 GiB → 37,376 tokens vs 32,768 context (both guard and default model at 32,768) | guardrails |
| Guard call timeout | 60 s (clamped by LiteLLM); verdict capped at 32 tokens | guardrails |
| Firecracker microVM boot | ~125 ms | agent-sandbox |
| Sandbox default limits | request 250m CPU / 256 Mi, limit 1 CPU / 1 Gi | default template |
| Warm pool sizes | python-pool 5, kata-pool 1 | role defaults |
| OpenShell workspace seeding on NFS | ~16 min → hence local-path for workspaces | openshell |
| pgvector first `initdb` on NFS | ~5 min (Helm timeout 15 min) | pgvector role |
| Preflight time cap | 5 min | validate-stack |
| Docker path resources | 96+ cores, 128 GB (1 model) / 256 GB (2+ models) | docker README |
| OpenVINO first start with conversion | 30+ min (pre-converted `OpenVINO/*` IDs start in minutes) | docker README |

### 4.5 How to produce the inference performance report (the missing part)

A complete report for this stack should answer: *for model M on Xeon server S, at
concurrency C, what latency and throughput do users get, and how much do the gateway,
guardrail and router add?* A practical method:

1. **Fix the setup.** Record CPU model, sockets, NUMA nodes, memory, model, TP, `cpu`,
   `VLLM_CPU_KVCACHE_SPACE`, vLLM version. Run preflight; make sure the governor is
   `performance` and THP is not `always`.
2. **Measure four paths separately**, because each layer adds latency:
   1. vLLM directly (in-cluster `:8000`): the raw engine.
   2. Through LiteLLM with the guardrail **off**: the gateway cost.
   3. Through LiteLLM with the guardrail **on**: the guardrail cost (an extra guard-model call per request).
   4. Through `hybrid-router`: router effect (should *lower* average latency on mixed traffic).
3. **Sweep concurrency** (1, 2, 4, 8, 16, 32 …) with fixed input/output lengths
   (e.g. 512 in / 256 out) and with a realistic mixed prompt set.
4. **Record** for each point: TTFT p50/p95, inter-token latency, output tokens/s per user
   and in total, request p95/p99, error rate, CPU utilisation per NUMA node, memory vs limit.
5. **Repeat** for `-specdec` variants and for MoE vs dense models.
6. **Report** as tables plus a latency-vs-throughput curve; mark the "knee" where p95
   latency rises sharply. That knee is the server's useful capacity.

A ready-to-fill KPI table is in [`02-design.md` → KPIs](02-design.md#7-kpis--what-to-measure-and-why).

> **Check yourself (Q4)**
> 1. Why does the KV cache often need more memory than the model weights?
> 2. What does "NUMA-aware pinning" protect against?
> 3. The rack-scale storage test was NVMe-bound, not network-bound. How do the numbers show that?
> 4. Which four request paths would you benchmark separately, and why?

---

## Q5 — Which parts of Agentic AI and Machine Learning does it touch, and which problems does it solve?

### Level 1 — what an agent actually does

Every agent, whatever the framework, runs this loop:

```
            ┌───────────────────────────────────────────────┐
            ▼                                               │
  1. THINK   ask the LLM: "given the goal and what I know,  │
             what should I do next?"                        │
  2. ACT     if the LLM asks for a tool → run the tool      │
  3. OBSERVE put the tool's result back into the context ───┘
  4. STOP    when the LLM answers without asking for a tool
  (+ REMEMBER important things for next time)
```

That loop needs five capabilities: **thinking** (LLM inference), **acting** (tools and code
execution), **remembering** (memory), **being safe** (guardrails, isolation, permissions)
and **being watched** (observability). The toolkit provides all five as infrastructure.
The sequence diagram walks through one full loop:
[`diagrams/sequence.png`](diagrams/sequence.png).

### Level 2 — map of the Agentic AI problems it solves

| Agentic AI problem | Why it is hard | How the toolkit solves it |
|---|---|---|
| **1. Model access and governance** | Every agent needs models; companies need to control who uses what, and at what cost | One OpenAI-compatible gateway (LiteLLM) with virtual keys per agent/sandbox, budgets (e.g. OpenShell key budget 50), rate limits, spend tracking |
| **2. Cost and latency of reasoning** | Agents make *many* LLM calls per task; sending all of them to a large model is slow and costly | **Hybrid Router**: complexity tier + bandit learns the most efficient model; optional **vLLM Semantic Router** (embedding signals) |
| **3. Unsafe input** | Prompts can contain harmful requests | **Guardrail** on every request (`pre_call`), **fail-closed** |
| **4. Running AI-written code** | The model may generate destructive or malicious commands | **Agent Sandbox**: one disposable pod per task, non-root, all capabilities dropped, NetworkPolicy (no private network, no cluster services); **Kata** microVM for kernel-level isolation; **OpenShell** egress default-deny, L7 rules, Landlock |
| **5. Secret leakage by agents** | An agent that can read its API key can leak it through a tool call | **OpenShell credential isolation**: the sandbox only sees a placeholder; the supervisor injects the real LiteLLM key on the way out |
| **6. Memory** | LLMs are stateless; agents must remember within and across sessions | **Redis Stack** (fast session state, semantic cache, RediSearch) + **pgvector** (persistent vectors, RAG) |
| **7. Slow tool starts** | Creating a pod per tool call adds seconds | **Warm pools**: pre-created sandboxes handed over instantly |
| **8. Parallel tool calls** | Agents often fan out (search 10 sources at once) | **KubeRay**: distributed workers, autoscaled |
| **9. Debugging agent behaviour** | Multi-step reasoning is opaque | **Langfuse** traces each LLM call (input, output, tokens, cost, chosen model); OpenShell logs every `DENIED` decision |
| **10. Framework lock-in** | Teams use different frameworks | OpenAI-compatible API → LangGraph, CrewAI, Microsoft Agent Framework, OpenClaw, Flowise all work |
| **11. Tools integration** | Each tool is custom work | **MCP** (Model Context Protocol) servers are the named pattern in the README. The templates themselves are *not* in this repository. |

### Level 3 — the Machine Learning concepts inside the stack

The project does **no model training**. It is an **ML-systems / MLOps** project. Still, it
uses several real ML ideas, and an engineer should be able to explain each one:

**1. LLM inference serving (vLLM).**
An LLM generates one token at a time. For every new token it must look back at all previous
tokens, and to avoid recomputing them it stores intermediate results in the **KV cache**
(keys and values of the attention layers). This is why memory, not just compute, limits CPU
serving. vLLM manages that cache in blocks (`--block-size 128`) so many requests share
memory efficiently.

**2. Tensor parallelism.** One model is split across TP workers (here, NUMA nodes), each
holding a slice of every layer. More cores work in parallel. The cost is communication
between workers, which is why TP must stay inside the memory topology.

**3. Speculative decoding.** A small *draft* model (e.g. 1 B for Llama-8B, 0.6 B for
Qwen3-Coder-30B) proposes `N` tokens. The big *target* model checks them all in a single
pass and keeps the ones it agrees with. Quality is unchanged and latency drops.

**4. Mixture-of-Experts (MoE).** Models like Qwen3-Coder-30B-**A3B** have 30 B parameters
but only ~3 B are *active* per token (a gating network picks a few "experts"). Compute per
token is small, but **all** weights must still sit in memory. The sizing table uses total
parameters for that reason.

**5. Quantisation.** Storing weights as int8/int4 instead of bf16 (OpenVINO path) cuts
memory and speeds up maths, at a small accuracy cost.

**6. Embeddings, vector search and reranking (RAG).**
`bge-base-en` turns text into vectors. pgvector / RediSearch find the nearest vectors
(semantic search). `bge-reranker` re-orders the candidates more accurately. Together they
form RAG and long-term memory.

**7. Safety classification.** **Qwen3Guard-Gen-0.6B** is a small generative classifier: it
reads the prompt and writes `Safety: Safe | Unsafe | Controversial` plus categories. The
gateway parses the verdict and blocks or allows.

**8. Rule-based complexity classification.** The Hybrid Router's first layer is *not* a
neural network. It is a weighted score over hand-designed features: estimated tokens,
code / reasoning / technical / simple keyword hits, multi-step patterns ("first … then",
numbered lists), question density. The score maps to a tier:
`SIMPLE < 0.15 ≤ MEDIUM < 0.35 ≤ COMPLEX < 0.60 ≤ REASONING` (or 2+ reasoning markers).
It is cheap (no extra model call) and explainable.

**9. Online learning with multi-armed bandits (reinforcement-learning family).** The router's
second layer treats each candidate model of a tier as a slot-machine *arm*. After each
response it computes a reward:

```
time_per_token = latency_seconds / max(completion_tokens, 1)
reward         = target_tpt / (target_tpt + time_per_token)        # in (0, 1]; failure = 0
(optional)     = (1 − quality_weight)·efficiency + quality_weight·quality_score
```

It then updates that arm's statistics. Three algorithms are offered:

| Algorithm | Idea in one sentence |
|---|---|
| **Thompson sampling** (default) | Keep a Beta(α, β) belief per model; sample from each belief and pick the highest sample, so uncertain models still get tried sometimes. |
| **UCB** (Upper Confidence Bound) | Pick the model with the best *optimistic* estimate (average + uncertainty bonus); `delta` controls the bonus. |
| **ε-greedy** | Usually pick the best-so-far; with probability ε (default 0.1) pick a random one to keep exploring. |

This is the **exploration vs exploitation** trade-off: keep using what works, but keep
checking whether something else has become better (for example, after a model is moved to
a bigger node).

**10. Semantic routing (vLLM Semantic Router, optional).** Compares the prompt's embedding
with example phrases per category (`coding_tasks` threshold 0.72 …) and applies prioritised
rules (`coding-route` 10, `reasoning-route` 50, `default-route` 100).

### Level 4 — what it deliberately does *not* solve

Knowing the edges is part of understanding:

- It does **not** provide agent logic, planning strategies or prompts: that is your framework.
- It does **not** train or fine-tune models.
- It does **not** ship MCP tool templates or ready-made business agents ("Example use cases —
  not pre-bundled").
- The guardrail screens **input only** (`pre_call`), with **one** guard; multiple concurrent
  guardrails (e.g. PII) are on the roadmap.
- Several advertised features are marked **"not available in this release"**: rack-scale
  fabric, Intel® Arc™ XPU, Flowise plugin, parts of vLLM-SR (semantic cache, jailbreak/PII
  detection, Langfuse export), resume mode, burn tests.

> **Check yourself (Q5)**
> 1. Draw the agent loop from memory and mark which toolkit component serves each step.
> 2. Explain the KV cache to a non-engineer in two sentences.
> 3. Why does an MoE model run fast on CPU but still need a lot of memory?
> 4. Compute the router reward for latency 4 s and 200 completion tokens with `target_tpt = 1.0`.
>    *(Answer: tpt = 0.02 → reward = 1 / 1.02 ≈ 0.980.)*
> 5. Why does the guardrail *block* when the guard model is unreachable, instead of letting the request through?

---

## Level 6 — Putting it all together

Follow one request through the whole system. Keep [`diagrams/sequence.png`](diagrams/sequence.png)
open beside this text.

1. A user asks an agent: *"Fix the failing unit test."*
2. The agent loads the session from **Redis** and searches **pgvector** for similar past fixes.
3. The agent calls `POST /v1/chat/completions` with `model = "hybrid-router"` and its
   **virtual key**. The request enters through **Envoy Gateway** (TLS) into **LiteLLM**.
4. LiteLLM checks the key's validity, budget and rate limit.
5. The **guardrail** sends the prompt to **Qwen3Guard**. *Safe* → continue. *Unsafe* or
   any failure → HTTP 500 "Blocked by the content-safety guardrail" (fail-closed).
6. The **Hybrid Router** classifies the prompt (say *COMPLEX*) and its Thompson-sampling
   bandit picks `qwen3-coder-30b`.
7. LiteLLM forwards the call through the AI gateway to **vLLM on Xeon**.
8. The model replies with a tool call: `run_shell("pytest -x")`.
9. LiteLLM computes the reward and updates the bandit, and sends a trace to **Langfuse**.
10. The agent asks the **sandbox router** (with its Kubernetes ServiceAccount token) for a
    sandbox. The router checks the token (TokenReview) and claims a pod from the **warm pool**
    straight away.
11. The command runs at `POST :8888/execute` inside the isolated pod. `stdout`, `stderr` and
    `exit_code` come back.
12. The agent appends the result and loops to step 3 until the model stops asking for tools.
13. The agent saves the outcome to memory, terminates the sandbox (the pool refills) and
    answers the user.

Three design ideas explain most of the system:

- **One front door** for every model call (security, cost, routing, tracing in one place).
- **Isolation by default** for everything an agent *does* (sandboxes, NetworkPolicy, mTLS,
  ClusterIP-only backends, fail-closed safety).
- **Swap anything** (Provider Design Pattern, OpenAI-compatible interfaces, per-component
  switches).

### Where to go next

| You want to… | Read |
|---|---|
| See the big picture | [`diagrams/architecture.png`](diagrams/architecture.png) |
| See every component, namespace and port | [`diagrams/component.png`](diagrams/component.png) |
| Understand the design in depth, with KPIs | [`02-design.md`](02-design.md) |
| Understand *why* each choice was made | [`adr/`](adr/README.md) |
| Prepare for an interview about this project | [`03-interview-prep.md`](03-interview-prep.md) |

---

## Glossary

| Term | Meaning |
|---|---|
| **AMX** | Advanced Matrix Extensions: matrix-multiply units in recent Xeon CPUs, used for bf16/int8 AI maths |
| **bf16** | 16-bit floating-point format; half the memory of fp32 with similar range |
| **ClusterIP** | A Kubernetes service reachable only inside the cluster |
| **CRD** | Custom Resource Definition: a new object type added to Kubernetes (e.g. `Sandbox`, `RayCluster`) |
| **Controller / operator** | A program that watches custom resources and makes reality match them |
| **Fail-closed** | When a check cannot decide, deny (safe default) |
| **Idempotent** | Running it twice gives the same result as running it once |
| **Kata Containers** | Runs each pod inside a lightweight VM with its own kernel |
| **KServe** | Kubernetes framework for serving ML models |
| **KV cache** | Stored attention keys and values for previous tokens during generation |
| **Landlock** | Linux kernel feature that restricts which files a process may access |
| **LiteLLM** | Open-source OpenAI-compatible proxy for many LLM providers |
| **MCP** | Model Context Protocol: a standard for exposing tools to LLM agents |
| **mTLS** | Mutual TLS: both sides prove their identity with certificates |
| **NetworkPolicy** | Kubernetes firewall rules between pods |
| **NUMA** | Non-Uniform Memory Access: each CPU socket/node has "near" memory; remote memory is slower |
| **NRI balloons** | A Kubernetes node-resource plugin policy that pins containers to sets of CPU cores |
| **Provider Design Pattern** | Each block defines *what* it does (contract); the *how* (provider) can be swapped |
| **TokenReview** | Kubernetes API that verifies a ServiceAccount token |
| **TP** | Tensor parallelism: one model split across several workers |
| **TTFT** | Time To First Token: how long until the first word of the answer appears |
| **Virtual key** | A LiteLLM API key with its own model list, budget and spend tracking |
| **Warm pool** | Pre-created idle sandboxes, ready to hand out instantly |
