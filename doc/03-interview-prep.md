# Interview Preparation — Intel® Agent Toolkit (Complete Edition)

> **What this is.** One self-contained document you can read end to end and then answer any
> interview question about this repository, from "what is it?" to code-level, maths-level,
> security-level and system-design-level questions.
>
> **Scope.** Repository: fork `praveennish/agent-toolkit` of `intel/enterprise-agent-toolkit`,
> documentation for release 1.2. Every fact below comes from the repository's files. Each answer
> cites the file it comes from. When something is **my analysis** rather than a fact in the repo,
> it is labelled **🔎 Analysis**. When it is **general industry knowledge** not stated in the repo,
> it is labelled **📚 General**.
>
> **Honesty rule.** In an interview, describe your relationship to the project precisely:
> *"I studied / deployed / extended / benchmarked it"*. Never claim authorship of parts you did
> not build. Interviewers test ownership with follow-up questions, and precise understanding beats
> inflated claims.

---

## How to use this document

| Part | What it gives you | When to read |
|---|---|---|
| **A. Orientation** | One-page fact card, pitches, whiteboard drawing | Day 1, then re-read before the interview |
| **B. Knowledge base** | Deep explanation of every subsystem, with code | Days 1–3, the core study material |
| **C. Question bank** | 164 questions with model answers, by topic and difficulty | Days 3–5, practise out loud |
| **D. System design** | Five fully worked design answers | Day 5 |
| **E. Debugging scenarios** | 22 symptom → cause → fix cases | Day 6 |
| **F. Critique** | Weaknesses of the repo and how you would fix them | Day 6 ("what would you improve?") |
| **G. Trade-offs** | Opinion questions with balanced answers | Day 6 |
| **H. Behavioural** | STAR templates | Day 7 |
| **I. Rapid fire** | 60 one-line flashcards | Last hour before the interview |
| **J. Mock rounds and checklist** | Three mock interview scripts, questions to ask, readiness checklist | Day 7 |

Difficulty markers in the question bank: **🟢 basic · 🟡 intermediate · 🔴 advanced**.

---

## Contents

- [Part A — Orientation](#part-a--orientation)
- [Part B — Knowledge base](#part-b--knowledge-base)
  - [B1 Repository anatomy](#b1-repository-anatomy)
  - [B2 Layer model and the installer](#b2-layer-model-and-the-installer)
  - [B3 The gateway: LiteLLM (real use, not a dummy)](#b3-the-gateway-litellm-real-use-not-a-dummy)
  - [B4 The Hybrid Router](#b4-the-hybrid-router)
  - [B5 The content-safety guardrail](#b5-the-content-safety-guardrail)
  - [B6 vLLM Semantic Router](#b6-vllm-semantic-router)
  - [B7 Inference on Xeon](#b7-inference-on-xeon)
  - [B8 Memory: Redis Stack and pgvector](#b8-memory-redis-stack-and-pgvector)
  - [B9 Agent Sandbox](#b9-agent-sandbox)
  - [B10 Kata Containers](#b10-kata-containers)
  - [B11 NVIDIA OpenShell](#b11-nvidia-openshell)
  - [B12 KubeRay](#b12-kuberay)
  - [B13 Keycloak realm](#b13-keycloak-realm)
  - [B14 Observability](#b14-observability)
  - [B15 Security model, consolidated](#b15-security-model-consolidated)
  - [B16 Deployment automation patterns](#b16-deployment-automation-patterns)
  - [B17 Preflight and validate](#b17-preflight-and-validate)
  - [B18 Docker Compose path](#b18-docker-compose-path)
  - [B19 CI and supply-chain security](#b19-ci-and-supply-chain-security)
  - [B20 Numbers to memorise](#b20-numbers-to-memorise)
- [Part C — Question bank (164 Q&A)](#part-c--question-bank-164-qa)
- [Part D — System design, fully worked](#part-d--system-design-fully-worked)
- [Part E — Debugging scenarios](#part-e--debugging-scenarios)
- [Part F — Critique: weaknesses and improvements](#part-f--critique-weaknesses-and-improvements)
- [Part G — Trade-off and opinion questions](#part-g--trade-off-and-opinion-questions)
- [Part H — Behavioural answers (STAR)](#part-h--behavioural-answers-star)
- [Part I — Rapid-fire flashcards](#part-i--rapid-fire-flashcards)
- [Part J — Mock rounds, questions to ask, checklist](#part-j--mock-rounds-questions-to-ask-checklist)

---

# Part A — Orientation

## A1. The one-page fact card

| Question | Answer |
|---|---|
| **What is it?** | An open-source, Kubernetes-based platform that provides everything an AI agent needs in production *except the agent itself*: gateway, inference routing, memory, sandboxed code execution, guardrails, observability, deployment automation |
| **Tag line (README)** | "Deploy a production-grade, open source agentic AI stack on Intel® Xeon® in hours — not months." |
| **Core insight (README)** | "GPUs accelerate reasoning. But the value of agentic AI comes from end-to-end task execution — and that control plane (state, tools, policy, coordination) runs efficiently on CPUs." |
| **Architecture idea** | Seven pluggable **provider blocks** (Provider Design Pattern): each block is a contract with an Intel-validated default |
| **Default providers** | LiteLLM (gateway) · Hybrid Router + vLLM on Xeon (routing/inference) · Redis Stack + pgvector (memory) · kubernetes-sigs Agent Sandbox (+ Kata, OpenShell) · Langfuse, Prometheus, Grafana, Loki (observability) · Kubernetes, Helm, Ansible, Docker Compose (deployment) · MCP (tools, pattern only) |
| **What this repo installs** | The **agent-toolkit layer**: `redis_stack`, `pgvector`, `agent_sandbox` (on by default), `openshell`, `kuberay` (off), `keycloak_agent_config` (JWT mode only), plus preflight, a Docker Compose path, and the docs |
| **What it does not install (Kubernetes path)** | LiteLLM, Hybrid Router, guardrail, vLLM/KServe, Langfuse, Kubernetes, Istio, storage: all from the other layers of `intel/enterprise-ai-solutions` ("Toolkit Manager") |
| **Installer** | `./es_auto_installer.sh configure` → `init agent-toolkit` → `install agent-toolkit`; `validate agent-toolkit`; `teardown agent-toolkit` |
| **Languages** | YAML (Ansible, Helm, Kubernetes), Jinja2, Go templates, Bash. README: Shell 88 %, Jinja 10 %, Go Template 2 % |
| **Licence** | Apache 2.0 |
| **Frameworks supported** | LangGraph, CrewAI, Microsoft Agent Framework, OpenClaw, Flowise, any OpenAI-compatible client |
| **Default chat model** | `qwen2-5-coder-14b` (Qwen2.5-Coder-14B-Instruct), served by vLLM on CPU |
| **Hardware minimum** | 48 cores, 32 GB RAM, 150 GB disk; recommended 96+ cores, 64 GB; default install actually requests ~131 GiB of memory |
| **Business purpose** | Show that agentic AI runs on Xeon; cut time-to-production from months to hours; enable private, on-prem, air-gapped AI; avoid lock-in |

## A2. Pitches

### 30-second pitch

> "The Intel Agent Toolkit is an open-source platform that installs, on Kubernetes, everything an
> AI agent needs in production except the agent itself. Every model call goes through one
> OpenAI-compatible gateway, LiteLLM, with per-agent keys and budgets, a fail-closed safety check,
> and a router that sends each request to the cheapest model able to handle it. Models run on Xeon
> CPUs with vLLM. Agents get Redis and pgvector for memory, and disposable sandboxes for running
> code. Everything is traced in Langfuse. One command installs it, and every block can be swapped.
> The business idea is that the agent control plane, and a useful share of inference, runs well on
> CPUs."

### 2-minute pitch (seven beats)

1. **Problem.** Production agents need a dozen systems; integration takes months.
2. **Shape.** Seven provider blocks, each a contract with a default (Provider Design Pattern).
3. **Model path.** Agent → Envoy Gateway (TLS) → LiteLLM (virtual key, budget, rate limit) →
   `content_safety` guardrail with Qwen3Guard (fail-closed) → Hybrid Router (rules classifier +
   per-tier multi-armed bandit) → vLLM on Xeon → Langfuse trace.
4. **Action path.** Agent → sandbox router (ServiceAccount token, TokenReview) → pod from a warm
   pool → `POST :8888/execute`. Egress is public internet only. Opt-in Kata microVMs and NVIDIA
   OpenShell for credential isolation.
5. **Memory.** Redis Stack for session state; PostgreSQL 16 + pgvector for long-term memory, with
   ready-made agent tables.
6. **Operations.** One Ansible role per component, each with install/validate/teardown;
   report-only preflight; Helm charts; Docker Compose for development; CI security scanners.
7. **Scope.** This repo is the agent-toolkit layer; the gateway and inference come from the
   inference layer of `enterprise-ai-solutions`.

### 5-minute version

Walk the request sequence (B3 → B4 → B5 → B7 → B9 → B8) and stop at three "design moments", giving
the decision and its trade-off for each:

1. **Fail-closed guardrail.** Safety can never be silently bypassed, at the cost of the guard
   becoming a hard dependency.
2. **Router-only Kubernetes access plus warm pools.** Agents need no RBAC and get sandboxes
   instantly, at the cost of idle resources.
3. **Bandit reward on time-per-token.** The router adapts to real hardware, at the cost of
   rewarding speed rather than quality by default.

Finish with one honest limitation and its fix (for example, no published inference benchmarks;
single-instance memory stores).

## A3. Whiteboard: draw it in 90 seconds

```
                     [ Agent (LangGraph / CrewAI / …) ]
                       │ OpenAI API + virtual key          │ direct, in-cluster
                       ▼                                    ▼
 [ Envoy Gateway/TLS ] → [ LiteLLM :4000 ]          [ Redis :6379 ]  [ pgvector :5432 ]
                          │ 1 key/budget/rate
                          │ 2 guardrail ─► qwen3guard  (fail-closed)
                          │ 3 hybrid router: tier → bandit
                          ▼                          [ sandbox-router :8080 ] ─► K8s API
                   [ vLLM on Xeon / cloud LLM ]            │ TokenReview          ▼
                          │                                └─► [ warm sandbox pod :8888 ]
                   [ Langfuse · Prometheus · Grafana ]           (Kata / OpenShell opt-in)
 ─────────────────────────────────────────────────────────────────────────────────────────
 Kubernetes · Istio ambient mTLS · NetworkPolicy · NRI balloons (NUMA) · Xeon (AMX)
 Ansible roles + Helm · es_auto_installer.sh · preflight · validate · teardown
```

Practise until you can draw it from memory and narrate each arrow.

---

# Part B — Knowledge base

## B1. Repository anatomy

| Path | Contents | Why it matters in an interview |
|---|---|---|
| `README.md` | Product story, seven blocks, Provider Design Pattern, FAQ, "Build vs Build-from-Scratch" | Source of the business argument and the scope |
| `components.yaml` | Registers the `agent-toolkit` layer (`depends_on: [platform, inference]`) and six components with `enabled` expressions and `depends_on` | Shows the layer contract |
| `config.yaml` | Default switches, seeded into `env/<name>/config.agent-toolkit.yaml` | Shows defaults (`auth_type: litellm_vkey`, `hybrid_router_enabled: true`, `openshell_enabled: false` …) |
| `roles/<component>/` | One Ansible role per component: `defaults/main.yaml`, `meta/main.yaml`, `tasks/{main,install,validate,teardown}.yaml` | The real automation code |
| `charts/redis-stack/` | Vendored Helm chart (subchart `redis-stack-server`): StatefulSet, Service, Secret, NetworkPolicy | Hardened Redis |
| `charts/pgvector/` | Helm chart: StatefulSet, Service, Secret, init ConfigMap with SQL schema | Long-term memory and its schema |
| `charts/kuberay/` | `RayCluster` template | Ray head/worker design |
| `charts/agent-sandbox/` | `default-templates.yaml` (python template), `kata-templates.yaml` | Sandbox pod spec and hardening |
| `charts/openshell/` | `values.yaml` (overlay on NVIDIA's chart), `genai-gateway-provider.yaml` | OpenShell provider profile |
| `playbooks/preflight-check.yml` + `playbooks/preflight/` | Node readiness checks; HTML/TXT templates for the report | Report-only preflight |
| `docker/` | `deploy.sh`, `docker-compose.yml`, generators, model config libraries, chat templates, LiteLLM config | Single-machine path |
| `docs/` | One guide per feature (≈ 6,000 lines) | Detailed behaviour, numbers, limitations |
| `.github/workflows/` | ansible-lint, ShellCheck, Bandit, Checkov, Trivy, Scorecard, dependency-review | Supply-chain and code quality |
| `.github/CODEOWNERS` | Default owners for review | Governance |

## B2. Layer model and the installer

**Toolkit Manager** (`intel/enterprise-ai-solutions`, script `es_auto_installer.sh`) installs the
product as ordered layers:

```
infrastructure  →  platform  →  inference  →  agent-toolkit (this repo)
(K8s, storage,     (Envoy Gateway, cert-manager,  (KServe, vLLM, LiteLLM,   (Redis, pgvector, Agent
 Kata classes)      MetalLB, Istio, PostgreSQL,    Hybrid Router, guardrail, Sandbox, OpenShell,
                    observability, NRI, NFD,       Langfuse, vLLM-SR)        KubeRay, Keycloak realm)
                    Keycloak)
```

**`components.yaml`** (this repo):

```yaml
layers:
  - name: agent-toolkit
    enabled: "{{ agent_toolkit_enabled | default(true) | bool }}"
    depends_on: [platform, inference]
components:
  - { name: redis_stack,  layer: agent-toolkit, enabled: "{{ redis_stack_enabled | default(true) | bool }}",  depends_on: [] }
  - { name: pgvector,     layer: agent-toolkit, enabled: "{{ pgvector_enabled | default(true) | bool }}",     depends_on: [] }
  - name: keycloak_agent_config
    enabled: "{{ keycloak_agent_config_enabled | default(keycloak_enabled | default((auth_provider | default('keycloak')) != 'litellm')) | bool }}"
  - { name: agent_sandbox, layer: agent-toolkit, enabled: "{{ agent_sandbox_enabled | default(true) | bool }}", depends_on: [] }
  - { name: openshell,    layer: agent-toolkit, enabled: "{{ openshell_enabled | default(false) | bool }}",   depends_on: [agent_sandbox] }
  - { name: kuberay,      layer: agent-toolkit, enabled: "{{ kuberay_enabled | default(false) | bool }}",     depends_on: [] }
```

Key points:
- Cross-layer ordering comes from **layer order**; only same-layer dependencies are declared
  (`openshell → agent_sandbox`).
- The Keycloak realm is enabled only when authentication is **not** LiteLLM. The default for this
  toolkit is LiteLLM virtual keys, so the realm is normally off.

**Configuration files** (`env/<name>/`, created by `init agent-toolkit`):

| File | Holds | Precedence |
|---|---|---|
| `global_config.yaml` | Domain, TLS mode, `auth_provider`, observability, storage backend, Istio, Kata, proxy, existing cluster | Base |
| `config.inference.yaml` | Inference layer settings (e.g. `vllm_sr_enabled`) | Loaded before toolkit config |
| `config.agent-toolkit.yaml` | This layer's switches and sizes (seeded from `config.yaml`) | **Loaded last**: overrides `guardrails_enabled`, `hybrid_router_enabled`, `litellm_*` |
| `models.yaml` | Model catalog: `cpu`, `memory`, vLLM `args`, `env`, `draft_model_id` | Read by model-manager |
| `inventory/hosts.yaml` | Nodes in Kubespray groups; `ansible_connection` per node | — |

Role defaults (`roles/*/defaults/main.yaml`) are the lowest layer; `config.yaml` overrides them.

**Uniform dispatch:** every role's `tasks/main.yaml` is the same shape:

```yaml
- name: "<component> | Dispatch action: {{ component_action | default('install') }}"
  ansible.builtin.include_tasks: "{{ component_action | default('install') }}.yaml"
  when: >-
    (component_action | default('install')) != 'install' or
    (<component>_enabled | default(<default>) | bool)
```

So `install` is skipped when a component is disabled, while `validate` and `teardown` always run
when asked. That lets you tear down something you have since disabled.

## B3. The gateway: LiteLLM (real use, not a dummy)

**What LiteLLM is.** An open-source, OpenAI-compatible proxy in front of 100+ model providers,
with keys, budgets, rate limits, model aliases, callbacks and an admin UI.

**How the repository uses it: an audit of every reference**

| Location | Kind | What it really does |
|---|---|---|
| `docker/docker-compose.yml` | **Deployment** | Runs `berriai/litellm:v1.83.14-stable.patch.2` on `:4000` with its own PostgreSQL DB, Redis (routing cache), master key, salt key, `STORE_MODEL_IN_DB=True`, Langfuse keys, and a health check on `/health/liveliness` |
| `docker/scripts/generate-vault-secrets.sh` | **Secrets** | Generates `LITELLM_MASTER_KEY="sk-<hex>"`, salt key, DB password, Redis password into `vault.yml` |
| `docker/deploy.sh` | **Provisioning** | Creates a dedicated `litellm` Postgres user and DB, revokes `CONNECT` from `PUBLIC`, adds a Redis ACL user `litellm`, writes `.env`, restarts or recreates LiteLLM when its config hash or `NO_PROXY` changes |
| `docker/scripts/generate-docker-compose.sh` → `generate_litellm_config()` | **Routing config** | Writes `docker/litellm/config.yaml`: Langfuse callbacks plus one `model_list` entry per model (`openai/<model_id>`, `api_base http://agentic-vllm-<name>:8000/v1` or `…ovms…/v3`). Sets `mode: embedding / rerank / audio_transcription`, and `encoding_format: float` for embeddings (works around a vLLM 400 on LiteLLM's health check) |
| `roles/openshell/tasks/install.yaml` | **Admin API use** | Runs Python *inside* the LiteLLM pod: `POST /key/delete` (alias cleanup) then `POST /key/generate` with `key_alias`, `models`, `max_budget`. Stores the virtual key in Secret `openshell-genai-key`. The master key (`PROXY_MASTER_KEY` env in the pod) never leaves the pod |
| `roles/openshell/tasks/install.yaml` | **Mesh access** | PeerAuthentication `openshell-sandbox-ingress` so non-mesh sandboxes reach LiteLLM under STRICT mTLS; LiteLLM still requires the key |
| `charts/openshell/genai-gateway-provider.yaml` | **Provider registration** | Declares LiteLLM as OpenShell's inference provider: credential `OPENAI_API_KEY` (bearer), endpoint `GENAI_HOST:GENAI_PORT`, allowed binaries |
| `config.yaml` | **Settings for the inference layer** | `auth_type: litellm_vkey`, `guardrails_enabled`, `hybrid_router_enabled: true`, `litellm_public_paths: []`, `litellm_allowed_namespaces`, `litellm_allow_pod_network` |
| `components.yaml`, `roles/keycloak_agent_config` | **Logic** | Skip the Keycloak realm when `auth_provider == 'litellm'` |
| `playbooks/preflight/templates/health-report.html.j2` | **Report** | Shows LiteLLM's internal URL and an example call |
| `docs/*` (≈ ⅔ of mentions) | **Documentation** | Verification, Hybrid Router, guardrails, vLLM-SR, OpenShell |

**About `api_key: dummy`.** It appears in the generated LiteLLM config (`api_key: dummy`; the docs
example uses `api_key: unused`). It is the key LiteLLM sends **to the backend model server**. vLLM
and OVMS run without authentication, but LiteLLM's OpenAI client requires a non-empty key, so any
placeholder works. Real authentication is client → LiteLLM (master key / virtual keys).

**Kubernetes path.** The LiteLLM Helm chart (`genai-gateway`), the router code and the guardrail
template live in `enterprise-ai-solutions`. This repo configures and consumes LiteLLM there but
does not install it.

**Concepts you must be able to explain:**

| Concept | Meaning |
|---|---|
| **Master key** | Admin credential (Secret `litellm-master-key`, key `master_key`); also the UI password for user `admin` |
| **Virtual key** | A LiteLLM-issued key with its own allowed models, budget, alias and spend tracking; one per agent or sandbox population |
| **`store_model_in_db`** | Models can be added at runtime via `POST /model/new` without restarting |
| **Callbacks** | `success_callback` / `failure_callback` (Langfuse); custom callbacks such as the Hybrid Router |
| **Guardrails API** | `/guardrails`, `/v2/guardrails/list`, `/guardrails/test_custom_code` |
| **Endpoints used** | `/v1/models`, `/v1/chat/completions`, `/key/generate`, `/key/delete`, `/model/new`, `/ui`, `/health/liveliness` |

## B4. The Hybrid Router

**Purpose.** Clients call one virtual model, `hybrid-router`. The router rewrites each request to
the most efficient real model for that request's complexity.

**Integration without an image rebuild** (`docs/hybrid-router.md`):
1. The router's Python files are rendered into ConfigMap `litellm-router-code`.
2. They are volume-mounted into the LiteLLM container (`/etc/litellm/…`).
3. Registered as a callback: `litellm_settings.callbacks: ["custom_hybrid_router.proxy_handler_instance"]`.
4. On import, the module **monkey-patches** `litellm.router.Router` to recognise the
   `auto_router/hybrid_router` deployment prefix and hooks `async_pre_routing_hook`. This mirrors
   LiteLLM's own built-in `ComplexityRouter`.
5. Requests for any other model name are untouched.

**Flow:**

```
model="hybrid-router" → Router.async_pre_routing_hook (patched)
   1 extract user + system text
   2 HybridRouter.classify()   → SIMPLE / MEDIUM / COMPLEX / REASONING
   3 HybridRouter.pick_model() → best real model for that tier (bandit)
   4 return PreRoutingHookResponse(model=<chosen>)
→ LiteLLM routes normally
→ async_log_success_event / async_log_failure_event → reward → bandit.update()
```

**Layer 1: rules-based complexity classifier (no model call).** It scores the prompt on estimated
token count; code, reasoning, technical and simple keyword hits; multi-step patterns ("first …
then", "step 2", numbered lists); and question density. The weighted score maps to a tier:

| Tier | Score | Typical prompt |
|---|---|---|
| SIMPLE | < 0.15 | Greetings, facts, yes/no |
| MEDIUM | 0.15 – 0.35 | Explanations, summaries, basic coding |
| COMPLEX | 0.35 – 0.60 | Architecture, multi-step code, technical analysis |
| REASONING | ≥ 0.60 **or** 2+ reasoning markers | Chain-of-thought, deduction, proofs |

Everything is overridable via `complexity_router_config` (`tier_boundaries`, `token_thresholds`
such as `simple: 15`, `complex: 400`, keyword lists, weights).

**Layer 2: per-tier multi-armed bandit.** Each tier has its own bandit; its arms are that tier's
candidate models (`tier_candidates`). A tier with one candidate skips the bandit.

```
time_per_token = latency_seconds / max(completion_tokens, 1)
reward         = target_tpt / (target_tpt + time_per_token)        # (0, 1];  failure → 0
if quality_weight > 0:
reward         = (1 − quality_weight) · efficiency + quality_weight · quality_score
```

| `bandit` | Algorithm | Parameter |
|---|---|---|
| `thompson` (default) | Beta-Bernoulli Thompson sampling | `tier_priors` (α, β) per arm, optional |
| `ucb` | Upper Confidence Bound | `delta` ∈ (0, 1), default 0.1; smaller = more exploration |
| `epsilon_greedy` | ε-greedy | `epsilon` ∈ [0, 1], default 0.1 |

**Configuration** (on the virtual model's `litellm_params`): `hybrid_router_default_model`
(required if `tier_candidates` is omitted), `hybrid_router_config` {`bandit`, `delta`, `epsilon`,
`target_tpt` (1.0), `quality_weight` (0.0), `tier_candidates`, `tier_priors`,
`complexity_router_config`}. Toggle with `hybrid_router_enabled`. Apply changes with
`./es_auto_installer.sh install agent-toolkit -- -e litellm_reconcile=true`. Onboard at runtime with
`POST /model/new` (needs `store_model_in_db`).

**Observability:** startup log `[HybridRouterProxy] litellm.router.Router patched…`; one line per
request (`tier=SIMPLE -> llama-3-1-8b`); state via `HybridRouterProxy.router_state()` (arm counts,
running means, Thompson α/β); Langfuse attribute `llm.model_name`.

**🔎 Analysis you can offer in interviews:**
- With `target_tpt = 1.0` s/token and CPU time-per-token well under 0.2 s, rewards cluster near 1
  (0.02 s → 0.980; 0.2 s → 0.833). The bandit then separates models slowly. Setting `target_tpt`
  near the observed time-per-token spreads the curve (e.g. 0.05: 0.02 s → 0.714; 0.2 s → 0.2).
- Bandit state appears to live in process memory, so it is per replica and lost on restart
  (inferred from the design; confirm in the code).
- The default reward measures **speed**, not answer quality; `quality_weight` exists for that.
- The monkey-patch couples the router to LiteLLM internals, so the LiteLLM version must be pinned.

## B5. The content-safety guardrail

(`docs/guardrails.md`; code lives in the inference layer's `roles/litellm`.)

- **Guard model:** `qwen3guard` = `Qwen/Qwen3Guard-Gen-0.6B`, its own vLLM release (`vllm-guard`)
  in namespace `llm-inference`, reached through the AI gateway.
- **Guardrail:** a LiteLLM `custom_code` guardrail named **`content_safety`** (model-agnostic
  name), mode **`pre_call`**, i.e. before the main LLM.
- **Sandboxed code:** compiled by LiteLLM with RestrictedPython. Rules: no `import`, no `class`, no
  leading-underscore names, no f-strings. Only injected primitives: `allow`, `block`, `trim`,
  `lower`, `contains`, `json_parse`, `json_stringify`, `regex_find_all`, `http_post`.
- **Verdict format:** `Safety: Safe | Unsafe | Controversial` + `Categories: …`. `Controversial` is
  advisory unless `guard_block_on_controversial: true` (off, because it rejects much legitimate
  traffic).
- **Fail-closed:** block when the guard is unreachable, returns non-2xx, the prompt is longer than
  the guard's context window, or the verdict cannot be parsed. Each case has its own message.
- **Blocked request = HTTP 500** with the reason in `error.message` (fixed LiteLLM behaviour for
  `custom_code` guardrails), e.g. `Custom code guardrail execution failed: Blocked by the
  content-safety guardrail: unsafe content (categories: …)`.
- **Registration is an upsert:** `PUT /guardrails/{id}` re-initialises the in-memory guardrail
  without a gateway restart (`PATCH` cannot change `litellm_params`). Before registering, the
  playbook compiles the code with `POST /guardrails/test_custom_code`, so a sandbox mistake cannot
  take the guardrail down.
- **Settings:** `guardrails_enabled` (default on with LiteLLM), `guardrail_model` (default
  `qwen3guard`), `guardrail_service_url` (derived), `guard_block_on_controversial` (false),
  `guard_max_tokens` (32), `guard_timeout` (60 s, clamped by LiteLLM).
- **Sizing facts:** the guard peaks at ~8.6 GiB (6.8 GiB worker + 0.9 GiB API server + 0.7 GiB
  EngineCore), so an 8 GiB limit is OOM-killed (exit 137). A 4 GiB KV cache gives 37,376 tokens ≥ the
  32,768 context; halving it would make long prompts fail closed. The guard uses the **Recreate**
  strategy (RollingUpdate would need its CPU twice over during a rollout).
- **Context-window rule:** `--max-model-len` is not set for the guard or served models, so each
  inherits its model's own value. If the guard's window were smaller, it would silently become the
  request-size ceiling of the whole stack.
- **Roadmap:** more guard models (one template per verdict format); multiple concurrent guardrails
  (e.g. PII via Presidio). Blockers: CPU capacity, latency (blocking `pre_call`, no `asyncio` in the
  sandbox, so checks add up), per-check failure policy, aggregate false-positive rate.

## B6. vLLM Semantic Router

(`docs/vllm-semantic-router.md`; `vllm_sr_enabled` in `config.inference.yaml`; parts marked not
available in this release.)

- Clients call `vllm-sr/auto` through LiteLLM; vLLM-SR extracts **semantic signals** (embedding
  similarity to example phrases, e.g. `coding_tasks` threshold 0.72) and evaluates **decisions** in
  priority order (lower number wins): `coding-route` 10, `reasoning-route` 50, `default-route` 100.
- Models are discovered automatically at deploy time. A model joins the coding route if `coder` is
  in its name; reasoning and default routes consider every model.
- No infinite loop: LiteLLM treats `vllm-sr/auto` and the real model names as separate entries.
- Dashboard at `vllm-sr.<domain>` (own host because it serves root paths); credentials in Secret
  `vllm-sr-dashboard`.
- Not wired in this release: semantic cache, jailbreak and PII detection, Langfuse export.

**Hybrid Router vs vLLM-SR:** rules + bandit (cheap, adaptive, explainable) vs embedding signals +
priority rules (more semantic, extra model, more configuration). Both are virtual models behind
LiteLLM, so clients choose by model name.

## B7. Inference on Xeon

**Serving:** KServe + vLLM (CPU) per model in `llm-inference`, reached via the AI gateway
(`/llm-inference/<model>/v1`). Docker path: vLLM CPU `v0.24.0` or OpenVINO Model Server `2025.4.1`.

**Model catalog (CPU):**

| Value | Model | Notes |
|---|---|---|
| `qwen2-5-coder-14b` | Qwen/Qwen2.5-Coder-14B-Instruct | **Default**; used by the Coding Agent |
| `qwen3-coder-30b` | Qwen/Qwen3-Coder-30B-A3B-Instruct | MoE, 3 B active |
| `bge-base-en` | BAAI/bge-base-en-v1.5 | Embeddings |
| `bge-reranker` | BAAI/bge-reranker-base | Reranking |
| `qwen3-30b-a3b` | Qwen/Qwen3-30B-A3B-Instruct-2507 | MoE |
| `gemma-4-26b` | google/gemma-4-26B-A4B-it | MoE |
| `llama-3-1-8b` | meta-llama/Llama-3.1-8B-Instruct | Sequential tool calls only |
| `*-specdec` | Llama-3.1-8B, Qwen3-Coder-30B, Qwen2.5-Coder-14B | Speculative decoding variants |
| `qwen3-6-35b-a3b` | Qwen/Qwen3.6-35B-A3B | MoE; weights on PVC via `HF_HOME` |

**Per-model configuration** (`models.yaml`): `cpu` (number or `auto`), `memory`, `args`
(`--dtype bfloat16`, `--block-size 128`, `--tensor-parallel-size`, `--tool-call-parser`,
`--chat-template`, `--trust-remote-code`, `--enable-prefix-caching`, `--enable_chunked_prefill`,
`--max-model-len`), `env` (`VLLM_CPU_KVCACHE_SPACE`, `VLLM_CPU_NUM_OF_RESERVED_CPU`,
`VLLM_RPC_TIMEOUT`, `VLLM_ENGINE_ITERATION_TIMEOUT_S`, `VLLM_ALLOW_LONG_MAX_MODEL_LEN`, `HF_HOME`),
`draft_model_id`. If a model has no entry in the Helm `modelConfigs`, it silently falls back to
`defaultModelConfigs` (generic, maybe wrong parser or template).

**Tool-call parsers:** `llama3_json` (Llama-3.x), `hermes` (Qwen3 non-coder), `qwen3_xml`
(Qwen3-Coder / Qwen2.5-Coder), `gemma4`. Docker docs also list `qwen3_coder`.

**CPU placement (NRI balloons):**
- `cpu: auto` → the free physical cores of **one NUMA node per TP rank**, on the smallest
  schedulable node.
- TP auto-selected among 1, 2 and 4 from topology (8 not auto-selected).
- `cpu` must be a multiple of TP and fit within a socket. Spanning NUMA nodes at TP=1 crashes
  (`shm.cpp thread_num mismatch`).
- Errors: `NRI pre-flight failed: not enough physical cores`;
  `CreateContainerError: no balloon for annotation` (TP mismatch).

**Memory rules:**

| TP | Request | Limit | Why |
|---|---|---|---|
| 1 | 128–200 GiB | 200 GiB | Keep memory on the pinned NUMA node (~252 GiB/node); bigger widens `cpuset.mems` → vLLM `core ids=[]` |
| 2–3 | 128–256 GiB | 400 GiB | — |
| ≥ 4 | 256 GiB | 400 GiB | Several MoE models exceed 256 GiB and rely on the 400 GiB limit + Burstable QoS |

**Footprint ≈ weights (params × 2 B) + draft + TP × `VLLM_CPU_KVCACHE_SPACE` + runtime/IPC:**

| Model | TP | Weights | Draft | KV | Runtime | ≈ Total |
|---|---|---|---|---|---|---|
| Llama-3.1-8B | 1 | 16.8 GiB | — | 40 | 12 | ~69 GiB |
| Llama-3.1-8B specdec | 2 | 16.8 | 2.6 (1 B) | 80 | 16 | ~116 GiB |
| Qwen2.5-Coder-14B | 4 | 30.8 | — | 160 | 22 | ~214 GiB |
| Qwen3-Coder-30B-A3B | 4 | 64.0 | — | 240 | 24 | ~328 GiB |
| Qwen3-Coder-30B specdec | 4 | 64.0 | 1.3 (0.6 B) | 240 | 26 | ~332 GiB |
| Gemma-4-26B-A4B | 4 | 55.0 | — | 160 | 22 | ~238 GiB |
| Qwen3.6-35B-A3B | 4 | 73.5 | — | 200 | 26 | ~300 GiB |

**Default install memory:** ~131 GiB = model 96 + Qwen3Guard 16 + router 2 + rest 17, which does
not fit a 128 GB node. Use a 64 GiB model there (`qwen2-5-coder-7b`, `llama-3-1-8b`).

**Speculative decoding:** a small draft model proposes N tokens; the target verifies them in one
pass, giving lower latency with the same output. Configured with `--speculative-config.method
draft_model`, `--speculative-config.model /mnt/models/draft`,
`--speculative-config.num_speculative_tokens N`. Separate catalog entries (`-specdec`).

**📚 General ML concepts you should be able to explain:**
- **KV cache:** stored attention keys and values for previous tokens. Per-token bytes =
  2 × layers × KV-heads × head-dim × bytes. For a Llama-3.1-8B-like model (32 layers, 8 KV heads,
  head-dim 128, bf16) that is 128 KiB/token, so 40 GiB ≈ 327,680 tokens shared by all concurrent
  sequences.
- **MoE:** a gate picks a few experts per token, so compute is small but all weights stay resident.
- **Tensor parallelism:** each rank holds a slice of every layer; ranks must communicate, so keep
  them inside the memory topology.
- **bf16 + AMX:** Xeon's Advanced Matrix Extensions accelerate bf16/int8 matrix maths.
- **Prefix caching / chunked prefill:** reuse computation for shared prompt prefixes; interleave
  long prefills with decoding.
- **Quantisation (OpenVINO path):** int4/int8 weights mean less memory and faster maths, with a
  small accuracy cost.

## B8. Memory: Redis Stack and pgvector

### Redis Stack (`roles/redis_stack`, `charts/redis-stack`)

| Aspect | Detail |
|---|---|
| Image | `redis/redis-stack-server:7.4.0-v8` (includes RediSearch), `imagePullPolicy: Always` |
| Kind | StatefulSet `redis-stack-server`, 1 replica, PVC (chart default 1 Gi; role sets **10 Gi**) |
| Namespace / service | `redis` / `redis-stack-server.redis.svc.cluster.local:6379`, **ClusterIP** |
| Auth | Mandatory: the Secret template **fails to render** if no password is given. Password passed via `REDIS_ARGS="--requirepass $(REDIS_PASSWORD)"` |
| Secret | `redis-stack-server-credentials`: `REDIS_PASSWORD`, `REDIS_URL = redis://default:<pw>@…:6379` (the `default:` user is required, since Redis 6+ rejects `redis://:<pw>@` with `WRONGPASS`) |
| Hardening | Pod `seccompProfile: RuntimeDefault`; container `allowPrivilegeEscalation: false`, `drop: [ALL]` |
| NetworkPolicy | Ingress on 6379 (+ Istio HBONE **15008** via `meshPort`); `allowedNamespaces` allow-list, or any pod if empty; always allows its own namespace |
| Resources (role) | 250m / 512 Mi → 2 CPU / 2 Gi |
| Installer behaviour | Reuses the existing password from the Secret; removes a **failed** Helm release first; `helm` errors captured then turned into an `assert` with the message; `no_log` everywhere secrets appear; waits for `app=redis-stack-server` Running |
| Validate | Pod Running; `redis-cli PING` → `PONG`; `MODULE LIST` contains `search` |
| Uses | Session state, short-term memory, semantic cache, RediSearch vector index |
| Limits | Single instance (no HA); no automated password rotation |

### PostgreSQL + pgvector (`roles/pgvector`, `charts/pgvector`)

| Aspect | Detail |
|---|---|
| Image | `pgvector/pgvector:pg16`; extension `vector` 0.8.0 |
| Kind | StatefulSet, 1 replica, PVC (chart 10 Gi; role sets **20 Gi**); `fsGroup: 999` |
| Service | `pgvector.pgvector.svc.cluster.local:5432` (ClusterIP); db `agentdb`, user `agentuser` |
| Probes | `pg_isready`; **startupProbe 10 s × 90 = 15 min** (first `initdb` on NFS takes ~5 min); Helm timeout 15 min |
| Resources (role) | 250m / 512 Mi → 2 CPU / 2 Gi (chart default limit 1 CPU / 1 Gi); `pgvector_parameters` → `-c key=value` server args (e.g. `max_connections`) |
| Secrets | Chart secret (`POSTGRES_PASSWORD` …) + role-created `pgvector-credentials` with `DATABASE_URL`, host, port, database, username, password |
| Installer behaviour | Reuses the password, including after a failed first install where only the chart's Secret exists; failed-release cleanup; verifies `pg_extension` has `vector` |

**Init schema (ConfigMap `…-init`, runs once at first start):**

```sql
CREATE EXTENSION IF NOT EXISTS vector;
-- privileges for agentuser on DB, schema public, default privileges on tables/sequences

CREATE TABLE agent_memory (            -- long-term memory
  id BIGSERIAL PRIMARY KEY, agent_id TEXT NOT NULL, user_id TEXT NOT NULL DEFAULT 'default',
  session_id TEXT, content TEXT NOT NULL, embedding VECTOR(1536),
  metadata JSONB NOT NULL DEFAULT '{}', created_at/updated_at TIMESTAMPTZ DEFAULT NOW());
CREATE INDEX agent_memory_embedding_idx ON agent_memory
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX agent_memory_agent_user_idx ON agent_memory (agent_id, user_id);

CREATE TABLE agent_events (            -- audit log of every action / tool call / LLM response
  …, event_type TEXT NOT NULL, payload JSONB, duration_ms INTEGER, created_at TIMESTAMPTZ);
CREATE INDEX agent_events_agent_session_idx ON agent_events (agent_id, session_id, created_at DESC);

CREATE TABLE agent_cache (             -- persistent cache of tool results / LLM responses
  cache_key TEXT UNIQUE, embedding VECTOR(1536), value JSONB, hit_count INT,
  expires_at TIMESTAMPTZ, …);
CREATE INDEX agent_cache_embedding_idx ON agent_cache
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

**Concepts:**
- **HNSW** (Hierarchical Navigable Small World): a graph index for approximate nearest-neighbour
  search. `m` = links per node (recall vs memory); `ef_construction` = build-time candidate list
  (recall vs build time). Query-time recall is tuned with `hnsw.ef_search` (📚 General).
- **`vector_cosine_ops`:** cosine distance (`<=>` operator in queries) (📚 General).
- **Semantic cache:** `agent_cache` stores results keyed by text and embedding, so a similar
  request can reuse an earlier answer.

**🔎 Analysis: the dimension mismatch to raise in interviews.** The schema fixes
`VECTOR(1536)`. 1536 is the size of OpenAI's popular embeddings. The toolkit's bundled embedding
model, `bge-base-en-v1.5`, outputs **768-dimensional** vectors (📚 model card). Inserting 768-d
vectors into a 1536-d column fails. So an agent using the local embedding model must either
create its own 768-d table, or the schema should be parameterised (e.g. a `pgvector_embedding_dim`
value). Spotting this shows you read the code, not only the docs.

## B9. Agent Sandbox

(`roles/agent_sandbox`, `charts/agent-sandbox`, `docs/agent-sandbox.md`.)

**Upstream:** `kubernetes-sigs/agent-sandbox` **v1.0.10**, applied from the official manifest
`sandbox-with-extensions.yaml`: CRDs `Sandbox`, `SandboxTemplate`, `SandboxClaim`,
`SandboxWarmPool` (API `v1beta1`; groups `agents.x-k8s.io` and `extensions.agents.x-k8s.io`) +
controller `agent-sandbox-controller`.

**Architecture:**

```
Agent ──HTTP :8080 + Bearer <SA token>──► sandbox-router-svc (Go, ×2 replicas, PDB)
   router ── TokenReview + create SandboxClaim ──► Kubernetes API
   controller ── binds a warm-pool pod (or creates from SandboxTemplate)
   router ── POST :8888/execute {"command": "..."} ──► sandbox pod (python-runtime-sandbox, uvicorn)
   ◄── {"stdout": ..., "stderr": ..., "exit_code": 0}
```

**Install steps** (`roles/agent_sandbox/tasks/install.yaml`):
1. Namespace `agent-sandbox-system` (fixed: the upstream manifests use it) + ambient label if Istio.
2. Apply the upstream manifest; wait for the controller (`readyReplicas == replicas`, 60 × 10 s).
3. Download router manifests (`serviceaccount, rbac, rbac-tokenreview, deployment, service, pdb,
   networkpolicy`) with retries (raw.githubusercontent throttles with HTTP 429).
4. **Rewrite them on the fly:** replace image `…sandbox-router-go:latest` with the pinned version,
   and inject `--authz-mode=tokenreview` and `--authz-tokenreview-require-token=true` after
   `--cache-enabled=true`. Apply; wait for the router.
5. Apply `python-sandbox-template` (placeholders `AGENT_SANDBOX_VERSION`, `imagePullPolicy`).
6. Apply **NetworkPolicy `eat-sandbox-pool-egress`**.
7. Create **SandboxWarmPool `python-pool`** with `agent_sandbox_python_warm_pool_size` (5).
8. If `kata_containers_enabled`, add the Kata template and pool (B10).
9. Wait for all pods Running and containers ready.

**The default template** (`charts/agent-sandbox/default-templates.yaml`):

```yaml
kind: SandboxTemplate
metadata: { name: python-sandbox-template, namespace: agent-sandbox-system }
spec:
  service: true                      # headless Service per pod (SDK DNS / tunnel mode)
  podTemplate:
    spec:
      containers:
      - name: runtime
        image: registry.k8s.io/agent-sandbox/python-runtime-sandbox:v1.0.10
        ports: [{ name: api, containerPort: 8888 }]
        resources: { requests: {cpu: 250m, memory: 256Mi}, limits: {cpu: 1000m, memory: 1Gi} }
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1000
          capabilities: { drop: [ALL] }
```

**The extra NetworkPolicy, and why it exists:**

```yaml
kind: NetworkPolicy
metadata: { name: eat-sandbox-pool-egress, namespace: agent-sandbox-system }
spec:
  podSelector: { matchExpressions: [{ key: agents.x-k8s.io/sandbox-name-hash, operator: Exists }] }
  policyTypes: [Ingress, Egress]
  ingress: [{ from: [{ namespaceSelector: {…agent-sandbox-system}, podSelector: { matchLabels: {app: sandbox-router} } }] }]
  egress:
    - to:
      - ipBlock: { cidr: 0.0.0.0/0, except: [10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16] }
      - ipBlock: { cidr: "::/0",   except: ["fc00::/7", "fe80::/10"] }
```

The controller's template policies select a label that **warm-pool sandboxes never carry**, and a
**claimed** sandbox loses its warm-pool label. `agents.x-k8s.io/sandbox-name-hash` stays on every
sandbox pod for life, so this policy covers pooled and claimed pods alike. Effect: only the router
can reach a sandbox, and sandbox code reaches **public addresses only**, never the node, the
Kubernetes API, cluster services or cloud metadata (169.254.169.254).

**SDK usage** (`pip install k8s-agent-sandbox==1.0.10`, version must match the server):

```python
import os
from k8s_agent_sandbox import SandboxClient
from k8s_agent_sandbox.models import SandboxDirectConnectionConfig

client = SandboxClient(connection_config=SandboxDirectConnectionConfig(
    api_url="http://sandbox-router-svc.agent-sandbox-system.svc.cluster.local:8080"))
sandbox = client.create_sandbox(warmpool="python-pool", namespace="agent-sandbox-system")
sandbox.connector.session.headers["Authorization"] = f"Bearer {os.environ['ROUTER_AUTH_TOKEN']}"
try:
    print(sandbox.commands.run("python3 --version").stdout)
    print(sandbox.commands.run('sh -c "echo a && echo b | tr a-z A-Z"').stdout)  # no shell by default
finally:
    sandbox.terminate()
```

- Token: `kubectl create token default -n agent-sandbox-system`. **Any** ServiceAccount token in
  the cluster is accepted; otherwise `401`.
- Modes: **Direct** (URL; in-cluster or manual port-forward) and **Tunnel**
  (`SandboxLocalTunnelConnectionConfig`, the SDK runs `kubectl port-forward`).
- **Session pattern:** keep one sandbox per agent session so installed packages and files persist;
  re-create it if `not sandbox.is_active`.
- Custom runtimes: any image exposing `POST /execute` on 8888; new `SandboxTemplate` +
  `SandboxWarmPool` (the v1.0.10 SDK starts sandboxes from warm pools). Custom templates should set
  `istio.io/dataplane-mode: none`, or their NetworkPolicy is not enforced.
- Sandboxes use **public DNS** (8.8.8.8, 1.1.1.1) and get **no proxy settings**, so on networks
  that require a proxy they have no outbound access.

**Validate:** controller and router deployments, CRDs, template, warm-pool readiness (warn if 0
ready), Kata template if enabled. **Teardown:** router deployment, router cluster RBAC
(`sandbox-router`, `sandbox-router-auth-delegator`), the manifest (CRDs + controller), the namespace.

## B10. Kata Containers

- **Why:** runc pods share the host kernel, so a kernel exploit escapes. Kata boots each pod in a
  lightweight VM with its **own guest kernel**.
- **Runtimes:** `kata-fc` (Firecracker: minimal device model, ~125 ms boot, needs the containerd
  **devmapper** snapshotter) and `kata-qemu` (QEMU: broader devices such as VFIO, heavier boot, works
  with the default snapshotter). `kata_runtime: kata-fc | kata-qemu | both`.
- **Enable:** `agent_sandbox_enabled: true` + `kata_containers_enabled: true` (global_config),
  `kata_version: "3.32.0"` (kata-deploy Helm chart from
  `oci://ghcr.io/kata-containers/kata-deploy-charts/kata-deploy`).
- **Infrastructure side** (enterprise-ai-solutions `roles/kata_containers`): checks `/dev/kvm`,
  loads `kvm` / `kvm_intel` if the CPU has `vmx`; for Firecracker, auto-provisions a loopback
  thin-pool at `/var/lib/containerd/devmapper` (100 GB sparse file) via a
  `containerd-devmapper.service` unit, registers the snapshotter, and restarts containerd. Because
  Kubespray regenerates `config.toml`, this is re-applied on every deploy. Labels eligible nodes
  `ei-kata-eligible=true`.
- **This repo's side:** picks `kata-fc` if that RuntimeClass exists, else `kata-qemu`; applies
  `kata-sandbox-template` (same image; `runtimeClassName`; `nodeSelector ei-kata-eligible: "true"`;
  label `sandbox: kata`; `istio.io/dataplane-mode: none`, since microVMs can't join the ambient
  mesh) and `kata-pool` (size **1**, because microVMs cost more). There is **no readiness gate** on
  the Kata pool, so one bad node can't hang the install.
- **Failure handling:** no `/dev/kvm` anywhere → stop with a fix; Firecracker without devmapper
  anywhere → stop; on some nodes → those nodes are unlabelled and named in a warning; invalid
  `kata_runtime` → stop; Agent Sandbox off → runtime classes only.
- **Use:** `client.create_sandbox(warmpool="kata-pool", …)`. Prove it with `uname -r` (guest
  kernel ≠ host kernel).

## B11. NVIDIA OpenShell

(`roles/openshell`, `charts/openshell`, `docs/openshell.md`; off by default.)

**What it adds on top of Agent Sandbox:** a **supervisor** in each sandbox pod enforces:
- **Egress default-deny**, with per-host and **per-binary** allow rules.
- **L7 rules** (HTTP method/path): e.g. `access: read-only` on `api.github.com`.
- **Filesystem restrictions**: Landlock (best effort) + seccomp.
- **Credential isolation**: the sandbox sees a placeholder (`openshell:resolve:env:…`); the
  supervisor injects the real credential only on allowed requests.

**Two "gateways":** the **OpenShell gateway** (control plane, StatefulSet `openshell-0`,
`openshell:8080` gRPC over mTLS; creates and deletes sandboxes, stores policies and credentials;
does not proxy LLM traffic) vs the **GenAI Gateway** (LiteLLM, which sandboxes use for models).

**Versions:** chart/images `0.1.6`, CLI `v0.1.6`, Agent Sandbox `v1.0.10`. Upgrading from 0.0.x
is a breaking migration (back up the database and keys, re-create sandboxes).

**Interfaces** (from the docs):

| # | From → To | How |
|---|---|---|
| 1 | Admin/CI → OpenShell gateway | gRPC over mTLS via `kubectl port-forward` (Secret `openshell-client-tls`) |
| 2 | OpenShell gateway → K8s API | Creates `agents.x-k8s.io/v1beta1` `Sandbox` CRs in `openshell-sandboxes` |
| 3 | Agent Sandbox controller → K8s API | Reconciles the CR into a pod (unchanged) |
| 4 | Supervisor → OpenShell gateway | gRPC/mTLS: policy, credentials, events (client TLS copied into the sandbox namespace) |
| 5 | Agent → supervisor | All pod egress passes through the supervisor |
| 6 | Supervisor → LiteLLM :4000 | Placeholder bearer rewritten to the virtual key (`providers_v2_enabled=true`) |
| 7 | Playbook → LiteLLM admin API | `kubectl exec` → `/key/generate` → Secret `openshell-genai-key` |
| 8 | LiteLLM → model backends | Unchanged; the key's models and budget apply |
| 9 | Supervisor → external hosts | Only hosts in the sandbox policy, through the corporate proxy |

**Install task groups:**
1. **Prerequisites:** `kubectl get nodes`; the `sandboxes.agents.x-k8s.io` CRD must serve
   `v1beta1`.
2. **Gateway:** namespaces `openshell-system`, `openshell-sandboxes`; choose the workspace
   StorageClass (`local-path` if present, because seeding a workspace on NFS takes ~16 min); Helm
   install of `oci://ghcr.io/nvidia/openshell/helm-chart` with values = repo overlay
   (`telemetryEnabled: false`, `agentSandbox.preflight.enabled: true`) combined with role overrides
   (image tag, `sandboxNamespace`, `workspaceStorageClass`, OIDC **or**
   `auth.allowUnauthenticatedUsers: true` for single-admin mode, `upstreamProxy`). Values go in as
   one dict, so an unchanged release compares equal and is not upgraded again. Then replicate
   `openshell-client-tls` into the sandbox namespace (a chart gap), detect NodeLocal DNSCache, apply
   NetworkPolicy `eat-openshell-sandbox-pods`, and wait for the gateway.
3. **GenAI provider:** check LiteLLM exists; PeerAuthentication `openshell-sandbox-ingress`
   (PERMISSIVE on the LiteLLM pods only); mint the virtual key once (alias `openshell-sandboxes`,
   `max_budget` 50, `models` from `openshell_genai_key_models`); fetch the CLI into a private,
   versioned directory (`~/.cache/eat/openshell-cli-v0.1.6`, mode 0700); write the mTLS bundle;
   render the provider profile (substitute `GENAI_HOST`/`GENAI_PORT`); register profile
   `eat-genai-gateway` and provider `genai-gateway` via a temporary port-forward (optimistic
   concurrency on update; tolerant of a transient `get` failure); **remove the CLI credentials**.
4. **Summary.**

**Provider profile** (`charts/openshell/genai-gateway-provider.yaml`): `id: eat-genai-gateway`,
`category: inference`, credential `api_key` → `OPENAI_API_KEY`, `auth_style: bearer`, endpoint
`GENAI_HOST:GENAI_PORT` `protocol: rest`, `access: read-write`, `enforcement: enforce`; binaries
`/usr/bin/curl`, `python3` variants, `/sandbox/.uv/python/**`,
`/usr/lib/node_modules/opencode-ai/bin/.opencode`. Binary identity is the **resolved executable
path**: symlinks are resolved, globs are not.

**NetworkPolicy `eat-openshell-sandbox-pods`:** selects sandbox pods *without*
`openshell.ai/boundary-role` (newer split pods keep the chart's stricter policies). Ingress only
from `openshell-system`. Egress: kube-dns and NodeLocal DNSCache (or `openshell_sandbox_dns_cidrs`)
on 53, `openshell-system`, LiteLLM on 4000, proxy port on `openshell_upstream_proxy_cidrs`
(defaults to RFC 1918 because proxy hostnames behind GSLB resolve to varying IPs), and public
addresses.

**Worked example from the docs ("restricted agent"):**

| Agent action | Result | Enforced by |
|---|---|---|
| Chat completion to LiteLLM | Allowed; spend on key `openshell-sandboxes` | Provider + credential injection |
| `GET api.github.com/repos/…` | Allowed | Policy `github_api`, `read-only` |
| `POST httpbin.org/post` | Blocked (curl exit 56) | Egress default-deny |
| `POST api.github.com/gists` | **403** | L7: POST not allowed by `read-only` |
| `echo $OPENAI_API_KEY` | Placeholder only | Credential isolation |

Logs: `openshell logs <sandbox> --source sandbox | grep DENIED` shows `NET:OPEN … DENIED …
[reason: endpoint httpbin.org:443 is not allowed by any policy]` and `HTTP:POST … DENIED … [engine:l7]`.

**Security caveat:** the client certificate `openshell-client-tls` grants **full gateway control**.
It is mounted for supervisors in the sandbox namespace, so restrict `pods/exec` there. OIDC is
supported but not validated with the toolkit. Policies on filesystem and Landlock apply at
**create** time and can't be changed later with `policy set`.

## B12. KubeRay

- **Purpose:** parallel tool execution and distributed Python for agents (`ray.remote`). Off by
  default.
- **Install:** namespace `ray-system` (ambient label if Istio); failed-release cleanup for both
  releases; Helm repo `ray-project.github.io/kuberay-helm`; operator `1.3.0`; `RayCluster` from
  `charts/kuberay`; wait for the head pod and `status.state == ready` with ready workers.
- **RayCluster spec:** `enableInTreeAutoscaling: true`; head `num-cpus: "0"` (schedules only),
  ports 6379 (GCS), 8265 (dashboard), 10001 (client); liveness TCP 6379; readiness HTTP
  `/api/version` on 8265; workers `replicas 2, min 1, max 4`, 500m–2 CPU / 2–4 Gi; containers
  non-root, `drop: [ALL]`, no privilege escalation; affinity prefers `workload-class=platform`;
  tolerates control-plane taints.
- **Dashboard:** `https://ray.<domain>/` via the platform gateway, **basic auth** (user `ray`,
  password generated once, SHA htpasswd, Secret `ray-dashboard-auth`).
- **Client:** `ray.init("ray://ray-cluster-head-svc.ray-system.svc.cluster.local:10001")`;
  `pip install "ray[default]==2.40.0"`, which must match the cluster image
  `rayproject/ray:2.40.0-py312` exactly.

## B13. Keycloak realm

`roles/keycloak_agent_config` creates realm **`agent-toolkit`** on the platform's existing Keycloak
(it does not deploy Keycloak). It waits for the `keycloak` StatefulSet, applies a
`KeycloakRealmImport` (`k8s.keycloak.org/v2beta1`), waits for condition `Done` or `HasErrors`, and
fails with the import's error message. It is used only when authentication is Keycloak JWT
(`auth_provider != litellm`).

## B14. Observability

| Level | Tool | What you see |
|---|---|---|
| LLM | **Langfuse** (callback from LiteLLM; project `inference`) | Each request: input, output, tokens, cost, latency, `llm.model_name` (routing decision) |
| System | Prometheus Operator, Grafana, Node Exporter | CPU, memory, request metrics |
| Logs/traces | Loki, Tempo, OTel Collector | Logs and distributed traces |
| Decisions | Hybrid Router logs + `router_state()`; OpenShell `DENIED` logs | Why a model or request was chosen or blocked |
| Install health | Preflight report; `validate` recap | Readiness and functional health |
| Ray | Ray dashboard | Tasks, workers |

Langfuse UI login: Secret `langfuse-secrets` (`admin_email`, `admin_password`). To check routing,
open Tracing → `litellm_request` → Metadata → attributes → `llm.model_name`.

## B15. Security model, consolidated

| Threat | Control | Where |
|---|---|---|
| Unauthenticated model use | Virtual keys / JWT; master key only in Secret | LiteLLM |
| Runaway spend | Per-key budgets, rate limits | LiteLLM |
| Harmful prompts | Fail-closed `pre_call` guardrail | LiteLLM + Qwen3Guard |
| Generated code harms host | Separate pod; non-root uid 1000; `drop: [ALL]`; no privilege escalation; 1 CPU / 1 Gi limit | Sandbox template |
| Kernel escape | Kata microVM | Opt-in |
| Lateral movement / exfiltration | Egress public-only NetworkPolicy; OpenShell default-deny + L7 | Sandbox / OpenShell |
| Cloud metadata theft | 169.254.0.0/16 blocked | NetworkPolicy |
| API-key leakage by agent | OpenShell placeholders; key minted inside the LiteLLM pod; CLI credentials deleted | OpenShell role |
| Unauthorised sandbox use | Router TokenReview with required token; agents need no RBAC | Sandbox router |
| Eavesdropping / spoofing in cluster | Istio ambient, strict mTLS; LiteLLM namespace allow-list | Platform |
| Exposed databases | ClusterIP only; NetworkPolicy; password required | Redis / pgvector |
| Weak or lost secrets | Generated 24-char passwords; reused, not regenerated; `no_log` | Roles |
| Unauthenticated Redis | Chart refuses to render without a password | Redis chart |
| Flowise owner takeover (Docker) | Loopback-only port until first owner; then `DENYLIST_URLS=/api/v1/account/register` | Docker path |
| Supply chain | Pinned actions (SHA), harden-runner, Trivy, Checkov, Bandit, Scorecard, dependency review | CI |
| Telemetry leakage | OpenShell `telemetryEnabled: false`; vLLM `VLLM_NO_USAGE_STATS`, `DO_NOT_TRACK` (Docker) | Config |

**Documented exceptions (know these, interviewers like edge cases):**
- OpenShell sandboxes are **outside** the mesh, so LiteLLM accepts plaintext from them on its pods
  only (PeerAuthentication), still with the virtual key, and admits the pod network
  (`litellm_allow_pod_network`).
- Custom sandbox templates must set `istio.io/dataplane-mode: none`, or NetworkPolicy isn't
  enforced.
- Any ServiceAccount token is accepted by the sandbox router (authentication, not per-namespace
  authorisation).
- The OpenShell client certificate equals full admin, so `pods/exec` must be restricted.
- No password rotation; single-instance Redis and pgvector.

## B16. Deployment automation patterns

These patterns repeat across roles. Name them in interviews; they show engineering maturity.

| Pattern | Example | Why |
|---|---|---|
| **Uniform action dispatch** | `include_tasks: "{{ component_action }}.yaml"` | Same verbs for every component |
| **Idempotent resources** | `kubernetes.core.k8s: state: present` | Safe re-runs |
| **Secret reuse** | Read Secret → reuse password, else generate | Re-install doesn't break clients |
| **Failed-release recovery** | `helm_info` → remove if `status == failed` → install | `helm upgrade --install` can't recover a failed first release |
| **Errors as clear asserts** | `ignore_errors` on Helm + `assert … fail_msg` | Readable failures without leaking secrets |
| **`no_log` on secrets** | Every task touching passwords/keys | No secrets in logs |
| **Readiness polling** | `k8s_info … until … retries/delay` | Deterministic completion |
| **Manifest patching** | Router manifests: pin image + inject authz flags | Harden upstream without forking |
| **Retry downloads** | `get_url` retries 5, delay 30 | Survive GitHub 429 throttling |
| **Upsert registrations** | Guardrail `PUT`; OpenShell profile update | No stale state |
| **Mint secrets where they live** | `kubectl exec` into LiteLLM for `/key/generate` | Master key never leaves the pod |
| **Clean up credentials** | Remove OpenShell CLI credentials after use | Least privilege on the admin host |
| **Graceful optionality** | Kata warns/skips; OpenShell provider skipped without LiteLLM | Partial environments still install |
| **Stable Helm values** | OpenShell values combined into one dict | No spurious upgrades |

**Teardown and decommission:** `./es_auto_installer.sh teardown agent-toolkit` (this layer) or
`teardown infrastructure` (whole cluster via Kubespray `reset.yml`; `env/` config files are kept).

## B17. Preflight and validate

**Preflight** (`playbooks/preflight-check.yml`):
- Runs at the start of `install` (before Kubespray on a new cluster, otherwise before the
  components). Skipped with `--only`. Disable with `node_preflight_enabled: false`. Capped at
  5 minutes. **Report-only**: never stops the install.
- Play 1 (per host): network layer (`ping` the default gateway; `getent hosts huggingface.co` for
  external DNS) and platform-health layer (NTP via `chronyc tracking` or `timedatectl`; root and
  containerd disk; kernel and OS; kubelet; kubelet DNS file; unfinished-install leftovers; swap; CPU
  governor from `/sys/.../scaling_governor`; NUMA via `lscpu`; THP from
  `/sys/kernel/mm/transparent_hugepage/enabled`).
- Play 2 (aggregate): compare each node's machine ID **directly** and **through delegation** (to
  detect missing `ansible_connection`), merge into a cumulative report, write
  `health-report-latest.{json,html,txt}` + archive under `env/<name>/logs/`, print the summary and
  a `PREFLIGHT WARNING` block.
- Statuses: **FAIL** (time sync, kubelet DNS file, unfinished install, node connection, swap, disk
  < 10 % free, external DNS, gateway), **WARN** (governor ≠ performance, THP = always, invalid HF
  token), **PENDING** (cluster checks before the cluster exists; HF token unset), **OK**
  (informational).
- Its only change to a system: if no node runs `systemd-resolved`, it writes
  `kube_resolv_conf: "/etc/resolv.conf"` and `resolvconf_mode: "none"` to `kubespray_extra.yml`.
  Mixed nodes → FAIL.

**Validate** (`./es_auto_installer.sh validate <layer|component> [--only]`), healthy = `failed=0`:

| Layer | Checks |
|---|---|
| Infrastructure | kubectl/kubeconfig, API, node readiness; storage CSI + one default class (+ Ceph health); kata-deploy + RuntimeClasses |
| Platform | cert-manager, MetalLB, Envoy Gateway (GatewayClass/Gateway accepted, TLS secret); Istio (istiod, ztunnel per node, mesh mTLS); PostgreSQL, SeaweedFS; observability stack; NRI balloons, NFD labels; Keycloak |
| Inference | KServe CRDs/controllers, serving runtimes, models, CPU policy; LiteLLM (deployment, readiness, master key, a request through the guardrail and a chat request); Langfuse; vLLM-SR |
| Agent toolkit | Redis (PING, RediSearch); pgvector (extension, credentials); Agent Sandbox (controller, router, CRDs, templates, warm pools, Kata template); OpenShell gateway; KubeRay operator + head |

Not in this release: burn tests, proxy checks, post-deploy report file.

## B18. Docker Compose path

- **Run:** `./docker/deploy.sh` (from an enterprise-agent-toolkit checkout). Flags:
  `--observability`, `--full`, `--skip-build`, `--down`, `--skip-confirmation`.
- **Config:** `docker/config.cfg`: `hugging_face_token`, `serving_engine=vllm|openvino`,
  `models=<comma-separated HF IDs>`, `tool_call_parser`, `deploy_docker_fresh`,
  `deploy_agenticai_plugin` (Flowise), `deploy_observability` (Langfuse), proxies.
- **Generated files:** `vault.yml` → `.env`; `docker-compose.vllm.yml` or
  `docker-compose.ovms.yml` (one container per model, ports 2080+); `litellm/config.yaml`;
  `postgres/init.sql`; `redis/acl.conf`. Don't edit generated files by hand.
- **Services:** model servers; LiteLLM `:4000`; PostgreSQL 16 + pgvector `:5432` (DBs `litellm`,
  `flowisedb`, `langfuse`, `agentdb`, each with its own least-privilege user); Redis Stack `:6379`
  (ACL users: `admin`, `litellm`, `flowise`, `langfuse`); Flowise `:3000` (profile); Langfuse
  `:3002` + ClickHouse + MinIO (profile). Containers `cap_drop: ALL`.
- **Engines:** vLLM (`vllm/vllm-openai-cpu:v0.24.0`, `/v1`, `/health`) or OpenVINO Model Server
  (`openvino/model_server:2025.4.1`, `/v3`, `/v2/health/ready`; `OpenVINO/*` IR repos start fast;
  others convert with `optimum-cli` on first start, 30+ min; `--rest_workers 32` and `nofile 65536`
  to avoid "too many open files"; no Whisper task). Switching engines removes the other compose
  file and its containers; model volumes are kept.
- **Resources:** 96+ cores; 128 GB for one model, 256 GB for two or more; unlisted models default
  to 80 GB, 40 GB KV, 16 GB shm.
- **Flowise security:** first owner is created by an **unauthenticated** `POST
  /api/v1/account/register`, so port 3000 binds to `127.0.0.1` until setup; afterwards `deploy.sh`
  sets `DENYLIST_URLS`. `NODE_ENV` is deliberately unset (no stack traces; cookies work over HTTP).

## B19. CI and supply-chain security

| Workflow | Tool | Purpose |
|---|---|---|
| `ansible-lint.yml` | ansible-lint 26.8.0 | Role/playbook quality |
| `shellcheck.yml` | ShellCheck | Bash quality (deploy scripts) |
| `bandit.yml` | Bandit (weekly + SARIF upload) | Python security lint |
| `checkov.yml` | Checkov 3.3.16 (weekly + SARIF) | IaC misconfiguration (K8s, Helm) |
| `trivy.yml` | Trivy v0.74.0 (weekly + SARIF) | Vulnerabilities and misconfiguration |
| `scorecard.yml` | OpenSSF Scorecard (weekly) | Supply-chain posture |
| `dependency-review.yml` | GitHub dependency review | New vulnerable dependencies in PRs |

All jobs use `step-security/harden-runner`, and every action is **pinned by commit SHA**. In the
code you will see `checkov:skip=CKV_SECRET_6` comments where a *Secret name* (not a value) looks
like a secret.

## B20. Numbers to memorise

| Item | Value |
|---|---|
| LiteLLM port / Docker image | 4000 / `v1.83.14-stable.patch.2` |
| Router tier boundaries | 0.15 · 0.35 · 0.60 |
| Router defaults | Thompson; `delta` 0.1; `epsilon` 0.1; `target_tpt` 1.0; `quality_weight` 0.0 |
| Guard | Qwen3Guard-Gen-0.6B; max 32 tokens; timeout 60 s; peak ~8.6 GiB; KV 4 GiB = 37,376 tokens; context 32,768 |
| Default install memory | ~131 GiB (96 + 16 + 2 + 17) |
| Install time | 20–40 min (+10–15 min model pull) |
| Node minimum / recommended | 48 cores · 32 GB · 150 GB / 96+ · 64 GB · 200 GB |
| TP memory limits | TP1 200 GiB; TP ≥ 2 400 GiB |
| Redis | 7.4.0-v8; 6379; 10 Gi; HBONE 15008 |
| pgvector | pg16; ext 0.8.0; 5432; agentdb/agentuser; 20 Gi; startup 15 min; `VECTOR(1536)`; HNSW m 16 / ef_construction 64 |
| Agent Sandbox | v1.0.10; router :8080 ×2; pod :8888 `/execute`; python-pool 5; 250m/256 Mi → 1 CPU/1 Gi; uid 1000 |
| Kata | 3.32.0; Firecracker ~125 ms; kata-pool 1; devmapper 100 GB sparse |
| OpenShell | 0.1.6; :8080 gRPC mTLS; key budget 50; NFS workspace seeding ~16 min |
| KubeRay | operator 1.3.0; Ray 2.40.0; head num-cpus 0; 10001/8265/6379; workers 1–4 |
| Preflight | cap 5 min; disk < 10 % free = FAIL |
| inotify | `max_user_instances 8192`, `max_user_watches 1048576` |
| Rack-scale (not in this release) | 83.1 Gbit/s; 0.7 ms RTT; 1.42 GB/s; 29 k / 12.5 k IOPS; 11/11 BGP |

---

# Part C — Question bank (164 Q&A)

Answer out loud, then compare. 🟢 basic · 🟡 intermediate · 🔴 advanced. Section references
(B3, B9 …) point back to Part B.

## C1. Project and business

**1. 🟢 What is the Intel Agent Toolkit in one sentence?**
An open-source Kubernetes platform that installs, on Xeon, everything a production AI agent needs
except the agent: gateway, routing, inference, memory, sandboxes, guardrails, observability and
deployment automation.

**2. 🟢 Who are its users?**
Platform/DevOps/MLOps engineers who install and run it; agent developers who build on its
endpoints; security and compliance teams who need isolation and audit; product owners who care
about cost and time to value.

**3. 🟢 What problem does it solve?**
Time and risk of integration. A production agent needs a dozen systems (gateway, keys, budgets,
routing, memory, sandboxes, safety, tracing, deployment). The README estimates 3–6 months from
scratch, versus hours to days with the toolkit.

**4. 🟡 Which Intel business goal does it serve?**
The README states the insight: the agent control plane runs efficiently on CPUs, and the toolkit
"does not require a GPU". 🔎 The business goals that follow: grow Xeon demand in AI; win private,
on-prem and air-gapped enterprise AI; lower adoption barriers; lower TCO versus GPU-only designs;
build an open ecosystem (Apache 2.0, standard components) on Intel platforms.

**5. 🟢 Is it an agent framework like LangGraph?**
No. Frameworks provide agent logic; the toolkit is the infrastructure underneath them (README FAQ).

**6. 🟢 Does it need a GPU?**
No. Models run on Xeon via vLLM (bf16/AMX). GPU or cloud endpoints can be added behind the same
gateway for heavy reasoning.

**7. 🟡 What does "Provider Design Pattern" mean?**
Each of the seven blocks defines a capability contract with an Intel-validated default provider.
Consumers depend on standard interfaces (OpenAI API, Redis, PostgreSQL, HTTP sandbox API), so any
provider can be swapped independently, with no big-bang replacement and no lock-in.

**8. 🟢 Name the seven blocks and their defaults.**
Gateway (LiteLLM); Memory (Redis Stack, pgvector); Inference routing (Hybrid Router, vLLM-SR,
vLLM/SGLang); Actions & tools (MCP, ETL); Sandbox (Agent Sandbox, OpenShell); Observability
(Langfuse, Prometheus, Grafana, Loki); Deployment (Kubernetes, Helm, Docker Compose).

**9. 🟡 Which use cases does it target?**
README examples, not pre-bundled: coding agent, deep research agent, Flowise agents, customer
support, enterprise data analyst (NL to SQL), IT operations agent.

**10. 🟡 Why is on-prem / air-gapped support a selling point?**
Regulated industries need data residency. The stack runs on bare metal or private cloud with no
mandatory external runtime dependency. Inference, memory and tracing all stay inside.

**11. 🟡 What is not in this release, even though the docs describe it?**
Rack-scale AI fabric mode, Intel Arc (XPU) deployment, the Flowise plugin (Kubernetes),
vLLM-SR semantic cache / jailbreak / PII / Langfuse export, resume mode, burn tests, OpenShell
deploy-state fingerprint, some guardrail sizing paths.

**12. 🟡 How would you summarise its "build vs buy" argument?**
Same flexibility and data control as building yourself (Apache 2.0, Provider Pattern), but with
governance built in, Xeon optimisation, a lower TCO and hours instead of months to production.

## C2. Architecture and scope

**13. 🟢 Draw the architecture.** See A3. Explain the two paths: model path (gateway) and action
path (sandbox), plus direct memory access.

**14. 🟡 Which components does *this* repository install?**
`redis_stack`, `pgvector`, `agent_sandbox` (default on), `openshell`, `kuberay` (default off),
`keycloak_agent_config` (only with Keycloak/JWT auth). Plus preflight, the Docker path, docs.

**15. 🟡 Where do LiteLLM, the router and vLLM come from?**
The inference layer of `intel/enterprise-ai-solutions` (Toolkit Manager). This repo declares
`depends_on: [platform, inference]`.

**16. 🟡 Why split the product into layers?**
Separation of ownership and lifecycle: infrastructure, platform, inference and agent services
change at different rates and are owned by different teams. Layers allow partial installs
(`install inference`), independent validation, and reuse of lower layers by other products.

**17. 🟡 How does the installer know what to install and in which order?**
Layer order handles cross-layer dependencies. Within a layer, `components.yaml` gives each
component an `enabled` expression and `depends_on` (e.g. `openshell → agent_sandbox`).

**18. 🟡 How do agents reach the backends?**
Model calls go to `https://litellm.<domain>/v1`, or in-cluster to `litellm.litellm.svc:4000`.
Memory is reached directly at `redis-stack-server.redis.svc:6379` and
`pgvector.pgvector.svc:5432`. Sandboxes via `sandbox-router-svc.agent-sandbox-system.svc:8080`;
Ray via `ray://ray-cluster-head-svc.ray-system.svc:10001`. Agent namespaces must be labelled
`istio.io/dataplane-mode=ambient`.

**19. 🟡 Why don't agents call vLLM directly?**
They would bypass auth, budgets, the guardrail, routing and tracing. One gateway enforces policy
in one place.

**20. 🟡 Why don't agents call the Kubernetes API to create sandboxes?**
That would need RBAC to create pods in every agent, which is a large blast radius. The router is
the only Kubernetes API caller; agents just present a ServiceAccount token.

**21. 🔴 Where are the single points of failure?**
LiteLLM is on every model call. The guard model is on every chat call (fail-closed). Redis and
pgvector are single instances. The OpenShell gateway is a StatefulSet of one. The sandbox router
has two replicas and a PDB, so it is the most resilient piece.

**22. 🟡 What does the platform layer provide that the toolkit relies on?**
Envoy Gateway + TLS (cert-manager) + LoadBalancer IPs (MetalLB); Istio ambient mTLS; storage
classes; observability; NRI balloons and NFD for CPU placement; PostgreSQL for LiteLLM/Langfuse;
Keycloak (optional).

**23. 🟡 Which hosts are published externally?**
`litellm.<domain>`, `langfuse.<domain>`, `vllm-sr.<domain>`, `ray.<domain>` (basic auth), and the
Coding Agent host (not in this release). The certificate must cover all of them (SAN or wildcard).

**24. 🔴 How would you replace pgvector with another vector DB without touching agents?**
You can't fully, if agents speak SQL to pgvector. The Provider Pattern only holds at the interface
the agent uses. The practical path: put an abstraction in the agent framework (most frameworks have
vector-store adapters), or keep the PostgreSQL protocol (e.g. another Postgres-compatible vector
engine). Be honest that "swappable" depends on client coupling.

## C3. LiteLLM and the gateway

**25. 🟢 Is LiteLLM real or a dummy in this repo?**
Real. It's the gateway for every model call. The Docker path deploys and configures it fully. On
Kubernetes it comes from the inference layer, and this repo uses its admin API to mint a virtual
key for OpenShell. `api_key: dummy` is only the placeholder LiteLLM sends to unauthenticated vLLM
backends (B3).

**26. 🟢 What is a virtual key?**
A LiteLLM-issued key with its own allowed models, budget, alias and spend tracking. You give one per
agent or sandbox population instead of sharing the master key.

**27. 🟡 How does the OpenShell role create its virtual key?**
`kubectl exec` into the `litellm` container and run Python that calls
`http://127.0.0.1:4000/key/delete` (removes an old key with the same alias) then `/key/generate`
with `key_alias`, `models`, `max_budget`, authorised by the pod's `PROXY_MASTER_KEY`. It prints the
key, which is stored in Secret `openshell-genai-key`. It runs only if that Secret doesn't exist yet,
with `no_log: true`.

**28. 🔴 Why delete by alias before generating?**
Aliases are unique, and a key with this alias can outlive the Secret (e.g. after `teardown
agent-toolkit`). Generating again would fail on the duplicate alias, so the role deletes it first
and tolerates 400/404 when none exists.

**29. 🟡 Where is the master key, and who can use it?**
Secret `litellm-master-key` (key `master_key`) in namespace `litellm`. It's the admin credential and
UI password for user `admin`. Best practice in the repo: mint other keys *inside* the pod so the
master key never leaves it.

**30. 🟡 How do you verify the gateway after install?**
`GET /v1/models` with the master key, then `POST /v1/chat/completions` with a model from that list.
Use `curl -k` because TLS is self-signed by default; add the gateway IP to `/etc/hosts` or use
`kubectl port-forward -n litellm svc/litellm 4000:4000`.

**31. 🟡 What does the Docker path configure for LiteLLM?**
Its own Postgres DB and user (`litellm`, `CONNECT` revoked from `PUBLIC`), a Redis ACL user, master
and salt keys, `STORE_MODEL_IN_DB`, Langfuse callbacks, one `model_list` entry per model with
`openai/<id>` and the container `api_base`, modes for embedding/rerank/transcription, and
`encoding_format: float` for embeddings.

**32. 🔴 Why `encoding_format: float` for embedding models?**
LiteLLM's health check sends `encoding_format=null`, which vLLM rejects with a 400 validation
error. Setting it explicitly keeps the embedding model healthy (comment in
`generate-docker-compose.sh`).

**33. 🟡 When does `deploy.sh` restart LiteLLM?**
If `NO_PROXY` changed, it **recreates** the container (environment variables need a new container).
If only `litellm/config.yaml` changed (hash comparison), it **restarts** it. Otherwise it leaves it
running.

**34. 🟡 What does `litellm_allowed_namespaces` do?**
Lists the mesh namespaces whose workloads LiteLLM admits: the gateway namespace, `litellm`,
`agent-sandbox-system`, `ray-system`. You add your own ambient-labelled agent namespace here.

**35. 🔴 What is `litellm_allow_pod_network` for?**
OpenShell sandboxes are outside the mesh, so LiteLLM must admit them from the pod network on its
API port. It's set to `openshell_enabled`. They still need the virtual key. On a bring-your-own
cluster you must also set `kubernetes_cluster_cidr`.

**36. 🟡 What does `litellm_public_paths: []` mean?**
Empty = all paths are published on LiteLLM's route (admin UI and key API reachable), relying on
LiteLLM's own auth. You could restrict it to `/v1/*` for a tighter edge.

**37. 🔴 What happens on the gateway when a guardrail blocks?**
HTTP 500 with the reason in `error.message`. Clients that treat 5xx as "retry" might retry blocked
prompts, so they should inspect the message. That's a client-design point to raise.

**38. 🟡 How can you add a model to LiteLLM without a restart?**
`POST /model/new` with the master key when `store_model_in_db` is on. The Hybrid Router docs show
onboarding a second virtual router (`hybrid_router2`) this way.

## C4. Hybrid Router and the ML inside it

**39. 🟢 What does the Hybrid Router do?**
Exposes a virtual model `hybrid-router`, classifies each prompt's complexity, and sends it to the
most efficient real model for that tier, learning online which model that is.

**40. 🟡 How is it plugged into LiteLLM?**
ConfigMap-mounted Python plus a callback; a monkey-patch adds the `auto_router/hybrid_router`
prefix and a pre-routing hook. No image rebuild (B4).

**41. 🟡 Describe the classifier.**
Rules-based weighted score: tokens, keyword families (code, reasoning, technical, simple),
multi-step patterns, question density. Thresholds 0.15 / 0.35 / 0.60 give SIMPLE / MEDIUM /
COMPLEX / REASONING; 2+ reasoning markers force REASONING.

**42. 🟡 Why rules rather than an ML classifier?**
Zero extra latency or compute (no model call), deterministic, explainable and tunable. An embedding
classifier exists as an option (vLLM-SR). The bandit corrects model choice *within* a tier.

**43. 🟡 Write the reward formula.**
`reward = target_tpt / (target_tpt + latency/max(tokens,1))`; 0 on failure; optional blend
`(1−q)·efficiency + q·quality_score`.

**44. 🔴 Compute the reward: latency 3 s / 150 tokens and 12 s / 60 tokens, `target_tpt = 1`.**
tpt 0.02 → 1/1.02 = **0.980**; tpt 0.2 → 1/1.2 = **0.833**.

**45. 🔴 What is the weakness of that default, and how would you tune it?**
Rewards cluster near 1, so the separation between models is small and learning is slow. Set
`target_tpt` near the observed time-per-token, e.g. 0.05 → 0.714 vs 0.2. (🔎 Analysis.)

**46. 🟡 Explain Thompson sampling.**
Each arm has a Beta(α, β) belief. Sample once per arm, pick the highest sample, then update α/β
with the outcome. Uncertain arms get explored naturally; good arms are exploited. `tier_priors` let
you start with prior beliefs.

**47. 🟡 Compare Thompson, UCB and ε-greedy.**
ε-greedy: random exploration with probability ε. Simple, but wastes traffic on clearly bad arms.
UCB: picks the arm with the best optimistic estimate (mean + bonus); deterministic; `delta` tunes
the bonus. Thompson: posterior sampling; strong in practice; supports priors.

**48. 🟡 Why per-tier bandits?**
Efficiency depends on prompt type: a model can be fast on short SIMPLE prompts and slow on long
COMPLEX generations. Separate bandits learn each regime.

**49. 🟡 What happens if a tier has only one candidate?**
The bandit is skipped; the request goes straight to that model.

**50. 🔴 What is "exploration vs exploitation", and why does it matter here?**
Exploit the model that is best so far, while still exploring others in case conditions change (a
model moved to a bigger node, load shifted). Without exploration, the router would lock onto an
early, possibly wrong, winner.

**51. 🔴 What risks does the monkey-patch create?**
It's coupled to LiteLLM internals, so an upgrade can break routing silently. Mitigation: pin the
LiteLLM version, run a router smoke test in `validate`, and watch the startup log line confirming
the patch.

**52. 🔴 Is the bandit state shared across LiteLLM replicas?**
🔎 It appears to be in-process memory: per replica, lost on restart. Each replica learns
independently, which is statistically fine but converges slower. Shared state in Redis (atomic α/β
increments) would fix it, at the cost of a network hop.

**53. 🟡 How do you see which model the router picked?**
LiteLLM log line `[HybridRouterProxy] … tier=… -> <model>`; Langfuse attribute `llm.model_name`;
the `model` field in the response.

**54. 🔴 The router speeds things up, but could it hurt quality? How would you detect that?**
Yes: the default reward is speed only. Detect it with task-success metrics per tier (tests passed,
user acceptance, LLM-as-judge on samples). Then raise `quality_weight`, adjust `tier_candidates`,
or move thresholds.

## C5. Guardrails

**55. 🟢 What does the guardrail do?**
Screens every chat request with Qwen3Guard before the main model; blocks unsafe content.

**56. 🟡 Why `pre_call`?**
Harmful input never reaches the main model, and you save its compute. Output screening
(`post_call`) is not implemented.

**57. 🟡 What does fail-closed mean here, and which cases trigger it?**
When the check can't decide, block. Triggers: guard unreachable, non-2xx, prompt longer than the
guard's context, unparseable verdict.

**58. 🔴 Why is an unparseable verdict treated as a block?**
If the guard model's output format changed, a fail-open parser would silently mark everything safe
while dashboards looked healthy. Fail-closed makes the problem visible immediately.

**59. 🟡 Why is the guardrail called `content_safety` rather than after the model?**
A stable, model-agnostic identity: swapping `guardrail_model` never leaves a stale registration
(which, being fail-closed, would block everything).

**60. 🔴 Why upsert with `PUT` and not create-if-absent?**
The name is stable across model changes, so create-only would keep outdated code. `PUT` also
re-initialises the in-memory guardrail, so there's no restart. `PATCH` can't change
`litellm_params`.

**61. 🔴 What are RestrictedPython's rules for the guard code?**
No `import`, no `class`, no leading-underscore names, no f-strings. Use only the injected
primitives (`allow`, `block`, `trim`, `lower`, `contains`, `json_parse`, `json_stringify`,
`regex_find_all`, `http_post`). The code is compiled first via `/guardrails/test_custom_code`.

**62. 🔴 Why must the guard's context window be ≥ the main model's?**
The guard sees the same prompt. If its window were smaller, long prompts would be blocked
(fail-closed), and the guard would silently become the stack's request-size limit. That's why
neither sets `--max-model-len`; both inherit their model's value (32,768 each today).

**63. 🔴 Why does the guard deployment use the Recreate strategy?**
RollingUpdate keeps the old pod while starting the new one, needing the guard's CPU twice. On a busy
single node, the new pod would stay Pending forever.

**64. 🔴 Why not add PII detection as a second guardrail today?**
Every check is on the blocking `pre_call` path, and the sandbox has no `asyncio`, so latencies add
up. Each guard model needs its own CPU, failure policies differ (fail-closed suits safety, not
necessarily PII), and blocking is a union of checks, so false positives compound.

## C6. Inference and performance

**65. 🟢 Which inference server is used?** vLLM (CPU build) on KServe; OpenVINO Model Server is an
option on the Docker path.

**66. 🟢 What is the default model, and why a coder model?**
`qwen2-5-coder-14b`. It's used by the Coding Agent, a flagship use case, and it supports tool
calling with the `qwen3_xml` parser.

**67. 🟡 What is the KV cache, and why does it dominate CPU memory here?**
Stored attention keys and values for past tokens, reserved per replica by `VLLM_CPU_KVCACHE_SPACE`
and multiplied by TP. For Qwen2.5-Coder-14B at TP=4: 160 GiB of KV vs 30.8 GiB of weights.

**68. 🔴 Size Qwen2.5-Coder-14B at TP=4.**
30.8 (weights) + 4 × 40 (KV) + 22 (runtime) ≈ **214 GiB**.

**69. 🔴 How many tokens fit in 40 GiB of KV for a Llama-3.1-8B-like model?** (📚)
2 × 32 × 8 × 128 × 2 B = 128 KiB/token → ≈ 327,680 tokens, shared across concurrent sequences.

**70. 🟡 What is tensor parallelism, and how is TP chosen?**
The model is split across ranks, each holding a slice of every layer. The playbook auto-selects 1,
2 or 4 by NUMA topology; `tensor_parallel_size` is a ceiling.

**71. 🔴 Why is TP=1 limited to 200 GiB?**
To keep memory on the NUMA node whose cores are pinned. A larger limit makes NRI widen
`cpuset.mems`, and vLLM then fails to bind cores (`core ids=[]`).

**72. 🟡 What does `cpu: auto` do?**
Takes the free physical cores of one NUMA node per TP rank on the smallest schedulable node.

**73. 🟡 Why can't a second model deploy on a single-NUMA node?**
`cpu: auto` gave the first model all of that node's cores, so the balloon has none left. Fix: set
explicit `cpu:` values in `models.yaml`, undeploy, re-install.

**74. 🟡 What is speculative decoding?**
A small draft model proposes tokens; the large model verifies them in one pass. Lower latency,
identical output. `-specdec` variants (e.g. Llama-8B with a 1 B draft; Qwen3-Coder-30B with a 0.6 B
draft).

**75. 🟡 Why are MoE models attractive on CPU?**
Few active parameters per token (e.g. 3 B of 30 B), so compute and bandwidth per token are low.
But total weights must stay in memory (64 GiB for Qwen3-Coder-30B-A3B).

**76. 🟡 Which vLLM flags matter most for tool calling?**
`--enable-auto-tool-choice`, `--tool-call-parser` (model-family-specific) and, if needed,
`--chat-template`. A wrong parser means tool calls aren't extracted.

**77. 🟡 What does the preflight check for performance?**
CPU governor (`performance` recommended), THP (`always` causes latency spikes; use `madvise`), NUMA
topology.

**78. 🔴 The repo has no tokens/s numbers. How would you produce a credible report?**
Record hardware, model, TP, `cpu`, KV size and versions. Tune nodes. Benchmark four paths: vLLM
direct, via LiteLLM, plus guardrail, plus router. Sweep concurrency with fixed and realistic prompt
sets. Report TTFT p50/p95, inter-token latency, tokens/s (per user and aggregate), p95/p99, errors,
CPU and memory per NUMA node. Find the knee of the latency-throughput curve.

**79. 🔴 Where does latency come from in one agent turn?**
TLS/edge → gateway auth → guard model call (blocking) → classification (≈ 0) → TTFT + generation
(dominant) → sandbox claim (≈ 0 with a warm pool) → command execution → memory I/O.

**80. 🟡 What measured performance results does the repo publish?**
Rack-scale only (not in this release): 83.1 Gbit/s cross-leaf iperf3 on 100G, 0.7 ms pod RTT, zero
encapsulation, Ceph 1.42 GB/s sequential write, 29 k/12.5 k 4K IOPS, NVMe-limited not network-limited.

**81. 🔴 Why is the rack-scale storage result "NVMe-bound, not network-bound"?**
Fabric NIC use under the storage burn was ~18–20 Gbit/s on 100G links, far below capacity. The
drives saturated first.

**82. 🟡 What is the default install's memory request, and why does it matter?**
~131 GiB (96 model + 16 guard + 2 router + 17 stack), so it doesn't fit a 128 GB node; pick a
64 GiB model there.

**83. 🔴 What happens if a model has no `modelConfigs` entry in the Helm values?**
It silently falls back to `defaultModelConfigs`: generic KV, CPU and args, possibly the wrong
tool-call parser or chat template. It works, but it's untuned.

## C7. Memory

**84. 🟢 Why two memory stores?**
Redis for fast, mutable, short-lived session state and cache; pgvector for durable, searchable
long-term memory joined with relational data.

**85. 🟡 How does an agent connect to Redis?**
Read `REDIS_URL` from Secret `redis-stack-server-credentials`:
`redis://default:<pw>@redis-stack-server.redis.svc.cluster.local:6379`.

**86. 🟡 Why `default:` in the Redis URL?**
Redis 6+ rejects an empty username, so `redis://:<pw>@…` fails with `WRONGPASS`.

**87. 🟡 How does the chart enforce Redis authentication?**
The Secret template calls Helm `fail` if auth is enabled and the password is empty, so it can't
render an unauthenticated Redis. The password is passed via `REDIS_ARGS="--requirepass …"`.

**88. 🔴 Why does the Redis NetworkPolicy open port 15008?**
That's Istio ambient's HBONE tunnel port. Meshed clients arrive through it.

**89. 🟡 What tables does pgvector create?**
`agent_memory` (long-term memory with `VECTOR(1536)` + HNSW cosine index + `(agent_id, user_id)`
index), `agent_events` (audit log of actions, tool calls, LLM responses with `duration_ms`),
`agent_cache` (semantic cache with a unique `cache_key`, embedding, `hit_count`, `expires_at`).

**90. 🔴 What is HNSW, and what do `m` and `ef_construction` control?**
A multi-layer proximity graph for approximate nearest-neighbour search. `m` = neighbours per node
(more = better recall, more memory); `ef_construction` = candidate list size at build time (more =
better graph, slower build). The values used, 16 and 64, are pgvector's defaults (📚).

**91. 🔴 What problem do you see in that schema?**
`VECTOR(1536)` doesn't match the bundled `bge-base-en` embedding model, which produces 768-d vectors
(📚). Inserts from the local model would fail. Fix: parameterise the dimension, or create per-model
tables. (🔎 Analysis.)

**92. 🟡 Why does pgvector have a 15-minute startup probe?**
First-start `initdb` on NFS takes ~5 minutes; 10 s × 90 failures gives enough time without
killing the pod.

**93. 🟡 How are passwords kept stable across re-installs?**
The role reads the existing Secret and reuses the password, falling back to the chart's
`POSTGRES_PASSWORD` after a failed first install. It generates a new one only if none exists.

**94. 🔴 How would you make memory highly available?**
Redis: Sentinel/replication or Redis Cluster via an operator; decide what may be lost (sessions are
often rebuildable). Postgres: operator-managed primary plus replicas, PITR backups. Keep the same
Secrets and URLs so clients don't change.

**95. 🟡 What is a semantic cache?**
Store prompt/tool results with embeddings; when a new request is semantically close (cosine above a
threshold), reuse the stored answer and skip the LLM or tool call. Redis (RediSearch) and
`agent_cache` both support it.

## C8. Agent Sandbox

**96. 🟢 What is a sandbox here?**
A disposable, isolated pod (`python-runtime-sandbox`) where agent-generated code runs via
`POST :8888/execute`, returning stdout, stderr and exit code.

**97. 🟡 Name the CRDs.** `Sandbox`, `SandboxTemplate`, `SandboxClaim`, `SandboxWarmPool`
(v1beta1).

**98. 🟡 What is a warm pool, and what does it buy you?**
Pre-created idle sandbox pods (`python-pool`, 5). A claim gets a running pod instantly: no
scheduling and no image pull. The pool refills in the background.

**99. 🟡 How is the router authenticated?**
The role injects `--authz-mode=tokenreview --authz-tokenreview-require-token=true`. Every request
needs a ServiceAccount bearer token, verified with the Kubernetes TokenReview API; otherwise 401.

**100. 🔴 What is the limitation of that authentication?**
Any ServiceAccount token in the cluster is accepted. It's authentication, not authorisation. An
improvement: audience-bound tokens or a per-namespace allow-list.

**101. 🔴 Why did the role add `eat-sandbox-pool-egress`?**
The controller's template policies select a label that warm-pool pods never carry, and a claimed
pod loses its pool label. The toolkit's policy selects `agents.x-k8s.io/sandbox-name-hash`, which
stays for the pod's life.

**102. 🟡 What can sandbox code reach on the network?**
Public addresses only. Private ranges, link-local (cloud metadata), the node, the Kubernetes API and
cluster services are blocked. Ingress comes only from the router.

**103. 🟡 List the pod-level hardening.**
Non-root uid 1000, `allowPrivilegeEscalation: false`, `drop: [ALL]`, requests 250m/256 Mi, limits
1 CPU/1 Gi.

**104. 🟡 How does the role harden upstream manifests without forking?**
It downloads them, string-replaces the image tag `:latest` with the pinned version, injects the authz
flags after `--cache-enabled=true`, parses the YAML and applies it.

**105. 🟡 Why are downloads retried?**
raw.githubusercontent.com throttles with HTTP 429; `get_url` retries 5 times with a 30 s delay.

**106. 🟡 Why does `commands.run("a && b")` fail?**
It runs without a shell. Wrap it: `sh -c "a && b"`.

**107. 🟡 How do you keep state across tool calls?**
The session pattern: reuse one sandbox per agent session (packages and files persist); re-create it
if it's no longer active; terminate at the end.

**108. 🟡 How do you add a Node.js runtime?**
Build an image exposing `POST /execute` on 8888; create a `SandboxTemplate` (set
`istio.io/dataplane-mode: none`) and a `SandboxWarmPool`; call `create_sandbox(warmpool="node-pool")`.

**109. 🔴 Why must custom templates opt out of the mesh?**
With the ambient mesh, NetworkPolicy enforcement for those pods doesn't work as intended (the docs:
"Keep sandboxes outside the ambient mesh, or their NetworkPolicy is not enforced").

**110. 🔴 Why can't sandboxes reach the internet on some corporate networks?**
They resolve through public DNS (8.8.8.8, 1.1.1.1) and get no proxy settings. Where direct DNS or
egress is blocked, they have no outbound access. The OpenShell path chains through the corporate
proxy instead.

**111. 🟡 How do you verify the sandbox install?**
`kubectl get pods -n agent-sandbox-system`; CRD versions show `v1beta1`; `kubectl get
sandboxtemplate`; `kubectl get sandboxwarmpool python-pool` (5/5); router `/healthz` →
`{"status":"ok"}`.

## C9. Kata and OpenShell

**112. 🟡 What does Kata add?**
A microVM per sandbox with its own guest kernel, so kernel exploits don't reach the host.

**113. 🟡 `kata-fc` vs `kata-qemu`?**
Firecracker: minimal, ~125 ms boot, needs the devmapper snapshotter. QEMU: broader device support,
heavier, default snapshotter.

**114. 🔴 Why does Firecracker need devmapper, and how is it provided?**
Firecracker can't use overlayfs for the container rootfs. The infrastructure role creates a
loopback thin-pool (100 GB sparse) with a systemd unit and registers the snapshotter, re-applying
it every deploy because Kubespray rewrites `config.toml`.

**115. 🟡 Why is the Kata warm pool size 1 and not readiness-gated?**
microVMs cost more resources, and a virtualisation problem on one node must not hang the whole
stack deployment.

**116. 🟡 How do you prove a sandbox runs in Kata?**
`uname -r` inside differs from the host's; `spec.runtimeClassName` on the pod is `kata-fc`.

**117. 🟢 What does OpenShell add over Agent Sandbox?**
Egress default-deny with per-host/per-binary rules, L7 method/path rules, Landlock/seccomp, and
credential isolation.

**118. 🔴 Explain credential isolation end to end.**
The provider profile maps `OPENAI_API_KEY` to the LiteLLM key for one endpoint and a list of
binaries. Inside the sandbox the variable holds `openshell:resolve:env:…`. The supervisor rewrites
the `Authorization` header with the real virtual key only when an allowed binary calls the allowed
endpoint. The key lives in Secret `openshell-genai-key` and the OpenShell gateway, never in the
sandbox.

**119. 🔴 Why does the provider list binaries, and what's subtle about it?**
So only known programs can use the credential. Identity is the **resolved executable path**:
symlinks are resolved, globs aren't, so a venv's python resolves to its base interpreter, and the
uv interpreter is matched by its real path.

**120. 🟡 What do the two "gateways" in OpenShell docs refer to?**
The OpenShell gateway (control plane: sandbox lifecycle, policies, credentials) and the GenAI
Gateway (LiteLLM: model traffic).

**121. 🔴 What is the security risk of single-admin mode?**
The client certificate `openshell-client-tls` grants full gateway control and is present in the
sandbox namespace for supervisors, so you must restrict `pods/exec` there. Access is otherwise gated
by Kubernetes RBAC (port-forward).

**122. 🔴 Why was a PeerAuthentication added for LiteLLM?**
The mesh is STRICT mTLS and sandboxes are outside it. The exception applies only to LiteLLM's pods,
and the key is still required.

**123. 🟡 Why `local-path` for OpenShell workspaces?**
Seeding a workspace on NFS (thousands of small files) takes ~16 minutes; node-local storage keeps
sandbox start fast.

## C10. KubeRay

**124. 🟢 Why KubeRay in an agent stack?** Parallel tool execution and distributed Python for
fan-out agent workloads, with autoscaling.

**125. 🟡 Why does the head run with `num-cpus: 0`?**
So no user tasks are scheduled on the coordinator; all work goes to workers.

**126. 🟡 What do min and max replicas do?** They bound the Ray in-tree autoscaler (1–4 by
default; 2 initially).

**127. 🟡 Common Ray client error?** A version mismatch: the client `ray[default]` must equal the
cluster image version (2.40.0).

**128. 🟡 How is the Ray dashboard protected?**
Published at `ray.<domain>` through the platform gateway with basic auth (user `ray`, generated
password hashed as SHA htpasswd in `ray-dashboard-auth`, created once).

## C11. Deployment automation, Kubernetes, Ansible, Helm

**129. 🟢 How do you install the toolkit?** `configure` → `init agent-toolkit` → edit
`env/<name>/*.yaml` → `export HF_TOKEN=…` → `install agent-toolkit`.

**130. 🟡 Explain the role structure.** `defaults/` (tunables), `meta/` (galaxy info, Ansible ≥
2.15), `tasks/main.yaml` (dispatch), `install.yaml`, `validate.yaml`, `teardown.yaml`.

**131. 🟡 What does "idempotent" mean here, and how is it achieved?**
Re-running gives the same state: `state: present`, secret reuse, failed-release cleanup, upserts,
and readiness waits instead of blind sleeps.

**132. 🔴 Why can't `helm upgrade --install` recover a failed first release?**
Helm considers a release with only a failed revision un-upgradable. The roles detect `status ==
failed` with `helm_info` and uninstall it before installing.

**133. 🟡 Why `no_log: true` so often?** Tasks that handle passwords and keys would otherwise print
them in Ansible output and logs.

**134. 🟡 Why are Helm errors captured with `ignore_errors` and then asserted?**
To give a readable failure message without letting the raw module output (which may include
secret values) reach the log.

**135. 🟡 What does preflight check, and why isn't it blocking?**
See B17. Report-only so unusual-but-valid environments aren't blocked; the warning block and the
report keep it visible.

**136. 🔴 How does preflight detect a wrong `ansible_connection`?**
It reads each node's machine ID directly and through delegation (as the installer would) and
compares them. A mismatch means node-level steps would run on the wrong machine.

**137. 🔴 What is the kubelet DNS problem preflight fixes?**
Kubespray points kubelet at `/run/systemd/resolve/resolv.conf`, which exists only with
`systemd-resolved`. If no node runs it, preflight writes `kube_resolv_conf: /etc/resolv.conf` and
`resolvconf_mode: none`. Mixed nodes fail.

**138. 🟡 How do you validate?** `./es_auto_installer.sh validate agent-toolkit` (healthy =
`failed=0`); `--only` for one layer or component.

**139. 🟡 Single-node vs multi-node requirements?**
Multi-node needs shared storage (`storage_backend: nfs | ceph | netapp-trident`; `local-path` is
single-node only), an inventory with Kubespray groups, and `ansible_connection` per node.

**140. 🟡 How do you run behind a corporate proxy?**
Set `http_proxy`, `https_proxy` and `no_proxy` in `global_config.yaml`, including service CIDRs
(`10.96.0.0/12`, `10.233.0.0/16`, `.svc`, `.svc.cluster.local`) and the stack's host names.

**141. 🟡 What kernel setting do the prerequisites require, and why?**
`fs.inotify.max_user_instances = 8192`, `max_user_watches = 1048576`. The default of 128 is a per-UID
limit shared by containers; when exhausted, file watchers fail (e.g. vLLM-SR config hot reload).

**142. 🔴 How does the OpenShell role avoid needless Helm upgrades?**
It combines the repo's values file and the role overrides into one values dict, so an unchanged
release compares equal and isn't upgraded again.

## C12. Observability and KPIs

**143. 🟢 Where do you see each LLM call?** Langfuse, project `inference`, trace `litellm_request`.

**144. 🟡 Name ten KPIs for this platform.**
TTFT p95; inter-token latency; tokens/s per model; request p95/p99; guardrail block rate by reason;
router tier distribution and arm shares; warm-pool hit rate; sandbox acquisition latency;
Redis/pgvector latency; memory headroom per model pod / OOM count; validate status.

**145. 🟡 How would you measure guardrail overhead?**
A/B test: identical load through LiteLLM with `guardrails_enabled` on and off; compare TTFT and
end-to-end latency.

**146. 🟡 How would you show the router helps?**
Run mixed traffic through `hybrid-router` vs always-largest-model; compare average latency and
cost at equal task success.

**147. 🟡 What does OpenShell log for denials?** `DENIED` lines with layer (NET or HTTP), binary,
destination, policy and engine (`opa`, `l7`) and a reason.

**148. 🟡 What files does preflight produce?**
`env/<name>/logs/health-report-latest.{json,html,txt}` plus archives, and `preflight-check.log`.

**149. 🔴 Which KPI would you put on the front page, and why?**
Output tokens/s at the p95 TTFT target per model and server. It combines capacity and user
experience and directly supports Xeon sizing.

**150. 🔴 How would you catch performance regressions between releases?**
A short gated benchmark in release CI (fixed model, prompt set and concurrency) with thresholds on
tokens/s and TTFT, plus svrinfo-style hardware capture for comparability.

## C13. Docker path and CI

**151. 🟢 When would you use Docker instead of Kubernetes?** Development, demos, CI and learning:
a single machine with no cluster overhead.

**152. 🟡 vLLM vs OpenVINO on the Docker path?**
vLLM: `/v1`, bf16, configs in `model-configs.yaml`. OVMS: `/v3`, int4/int8, configs in
`ovms-model-configs.yaml`; pre-converted `OpenVINO/*` IR repos start fast, while others convert on
first start (30+ min). No Whisper. Clients always use LiteLLM on 4000, so code doesn't change.

**153. 🔴 Why is Flowise bound to loopback at first?**
Its first owner is created through an unauthenticated register endpoint; whoever calls it first
becomes the only owner. After setup, `deploy.sh` sets `DENYLIST_URLS` to close it.

**154. 🟡 How are secrets created in Docker mode?**
`generate-vault-secrets.sh` → `vault.yml` → `deploy.sh` writes `.env`; per-service Postgres users
and Redis ACL users with their own passwords.

**155. 🟡 Name the CI security tools.** ansible-lint, ShellCheck, Bandit, Checkov, Trivy, OpenSSF
Scorecard, dependency review; all actions pinned by SHA, with harden-runner.

**156. 🔴 Why pin GitHub Actions by commit SHA?**
Tags can be moved, and a compromised action tag could inject code into CI. SHAs are immutable.

## C14. Code-reading questions ("what does this snippet do?")

**157. 🔴 What does this do?**
```yaml
when: >-
  (component_action | default('install')) != 'install' or
  (pgvector_enabled | default(true) | bool)
```
It runs the selected action file. `install` is skipped if pgvector is disabled, but `validate` and
`teardown` always run when requested.

**158. 🔴 What does this do?**
```yaml
| map('replace', '- --cache-enabled=true', _authz_args)
```
It injects `--authz-mode=tokenreview` and `--authz-tokenreview-require-token=true` into the
upstream router deployment by replacing the `--cache-enabled` line with itself plus the new flags.

**159. 🔴 What does this do, and why?**
```yaml
_redis_pw: >-
  {{ (_redis_secret.resources[0].data.REDIS_PASSWORD | b64decode)
     if (_redis_secret.resources | default([]) | length > 0 and …REDIS_PASSWORD is defined)
     else redis_stack_password }}
```
It reuses the stored password if the Secret exists, else uses the freshly generated default, so
re-installs never rotate the password underneath connected clients.

**160. 🔴 What does this do?**
```yaml
podSelector: { matchExpressions: [{ key: agents.x-k8s.io/sandbox-name-hash, operator: Exists }] }
```
It selects every sandbox pod, pooled or claimed, because this label persists for the pod's life,
unlike the warm-pool label.

**161. 🔴 What does this do?**
```sql
CREATE INDEX … ON agent_memory USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```
It builds an approximate nearest-neighbour index for cosine-distance search over memory embeddings.

**162. 🔴 What does this do?**
```yaml
REDIS_ARGS: "--requirepass $(REDIS_PASSWORD)"
```
Kubernetes expands `$(REDIS_PASSWORD)` from the earlier env var; redis-stack-server appends
`REDIS_ARGS` to the server command line, which enables password authentication.

**163. 🔴 What does this do?**
```yaml
headGroupSpec: { rayStartParams: { num-cpus: "0", dashboard-host: "0.0.0.0" } }
```
The Ray head advertises zero CPUs (no tasks scheduled on it) and serves the dashboard on all
interfaces so the Service can reach it.

**164. 🔴 What does this do?**
```yaml
values: >-
  {{ lookup('file', helm_charts_base_openshell ~ '/values.yaml') | from_yaml
     | combine(helm_overrides | from_yaml, recursive=True) }}
```
It deep-merges the repo's OpenShell values overlay with role-computed overrides into one dict for
Helm, giving deterministic values and no spurious upgrades.

---

# Part D — System design, fully worked

Use the same frame every time: **clarify → requirements → estimates → high-level design → deep
dive → trade-offs → metrics → rollout**. Reuse the toolkit's blocks as your vocabulary; it shows you
know the repo.

## D1. "Design an on-prem platform for AI coding agents for 5,000 developers."

**Clarify.** Peak concurrent agents? Latency target (interactive or batch)? Allowed models? Which
repos may agents touch? Data residency? Hardware available (Xeon only, or some GPUs)? Audit needs?

**Requirements.**
- Functional: chat and tool use, code execution, repo access, memory of past fixes, per-team budgets.
- Non-functional: p95 TTFT under a few seconds for interactive use, isolation of untrusted code,
  audit trail, 99.9 % availability, no data leaving the site.

**Estimates (state your assumptions out loud).** Say 10 % of developers are active at peak (500
agents), each turn makes 3 LLM calls and 2 tool calls, with one turn every 20 s per agent. That
gives ~75 LLM calls/s and ~50 sandbox commands/s. If a sandbox session lasts 10 minutes and sessions
start at 1/s, Little's law gives ~600 concurrent sandboxes. Size the warm pool for the start rate
times the claim time, not for the concurrent total.

**Design.**
1. **Edge:** Envoy Gateway + TLS; per-team virtual keys in LiteLLM with budgets and rate limits;
   LiteLLM with several replicas behind a Service.
2. **Safety:** `content_safety` guardrail; scale the guard model to its own SLO (replicas), because
   it's fail-closed and on the critical path.
3. **Routing:** Hybrid Router; SIMPLE/MEDIUM → `qwen2-5-coder-14b` (or the 7 B) on CPU; COMPLEX/
   REASONING → `qwen3-coder-30b-specdec` on CPU, or a GPU tier if available; tune `target_tpt`.
4. **Inference:** vLLM fleets per tier, NUMA-pinned (explicit `cpu:` to pack nodes), prefix
   caching on (shared system prompts).
5. **Execution:** Agent Sandbox warm pools sized from the start rate; **Kata** for untrusted repos;
   **OpenShell** policy allowing only the internal Git host and package mirror, so the agent never
   sees credentials.
6. **Memory:** Redis for sessions; pgvector for code-fix memory (parameterised embedding dimension;
   HNSW).
7. **Observability:** Langfuse per team project; Prometheus/Grafana dashboards for the KPIs in C12;
   `agent_events` as the audit log.

**Trade-offs.** CPU vs GPU per tier (measure tokens/s per currency unit); Kata cost vs isolation;
fail-closed guard vs availability; one shared Redis vs per-team.

**Gaps to close in the toolkit.** HA Redis/Postgres; shared router state across LiteLLM replicas;
per-namespace authorisation on the sandbox router; output-side guardrails.

**Rollout.** Pilot one team on a single node → multi-node → enable Kata/OpenShell → add a GPU tier
only if measurements demand it.

## D2. "Add a GPU tier without changing any agent."

Register the GPU endpoint in LiteLLM (`/model/new` or config). Add it to `tier_candidates` for
COMPLEX and REASONING. Agents keep calling `hybrid-router`. Watch tier distribution and arm shares in
`router_state()` and Langfuse. If the GPU model is also *better*, raise `quality_weight` so the
reward reflects quality. Cap GPU spend with virtual-key budgets.

## D3. "Make the platform highly available."

| Component | Today | HA design |
|---|---|---|
| LiteLLM | Deployment (inference layer) | ≥ 2 replicas, PDB, shared DB/Redis; shared router state |
| Guard model | Recreate strategy | ≥ 2 replicas on different nodes (capacity planned) |
| vLLM models | One per model | Replicas per model; LiteLLM load-balances deployments with the same name |
| Sandbox router | 2 replicas + PDB | Already HA |
| Sandbox controller | Upstream deployment | Leader election (upstream) |
| Redis | Single StatefulSet | Sentinel/replication or cluster via an operator |
| pgvector | Single StatefulSet | Postgres operator with replicas + PITR |
| OpenShell gateway | `openshell-0` | Depends on upstream support; back up its database |
| Storage | local-path/NFS | Ceph or enterprise CSI |

Keep connection Secrets and URLs identical so clients don't change.

## D4. "Multi-tenant: two business units must not see each other's data."

Separate virtual keys and model allow-lists per tenant. Separate agent namespaces (ambient label;
add to `litellm_allowed_namespaces`). Per-tenant Postgres databases/roles and Redis ACL users (the
Docker path already uses ACL users per service). Per-tenant sandbox namespaces and warm pools.
NetworkPolicies between tenants. Langfuse projects per tenant. Tighten the sandbox router to accept
tokens only from that tenant's namespaces.

## D5. "Design the benchmark that proves Xeon sizing for this stack."

Fixed hardware record (svrinfo-style), tuned nodes, pinned versions. Four request paths (direct,
gateway, +guardrail, +router). Concurrency sweep with fixed and realistic prompts. Metrics: TTFT,
inter-token latency, tokens/s, p95/p99, CPU/memory per NUMA node, OOMs. Repeat per model, TP and
`-specdec`. Publish the latency-throughput curves and the knee per SKU. Run a short gated version in
CI to catch regressions.

---

# Part E — Debugging scenarios

Answer format: **symptom → hypothesis → check → fix.**

| # | Symptom | Likely cause | Check | Fix |
|---|---|---|---|---|
| E1 | Every chat returns HTTP 500 "Blocked by the content-safety guardrail … unreachable" | Guard vLLM down, loading or OOM | `kubectl get pods -n llm-inference \| grep qwen3guard`; describe | Wait for load; memory ≥ ~9 GiB; `./model-manager deploy qwen3guard --wait` |
| E2 | Long prompts blocked: "prompt is longer than the guard model's context window" | Guard context < served context | Compare `max_model_len` via each pod's `/v1/models` | Longer-context guard or chunked screening; don't just raise `--max-model-len` |
| E3 | A legitimate prompt blocked as "Controversial" | `guard_block_on_controversial: true` | Config | Set to false (the default) |
| E4 | Model pod CrashLoopBackOff, exit **137** | OOM: footprint > limit | `kubectl describe pod` → OOMKilled | Raise `memory`, raise TP, or carefully reduce KV |
| E5 | `NRI pre-flight failed: not enough physical cores` | `cpu: auto` consumed a NUMA node | `models.yaml` | Explicit `cpu:`; undeploy; re-install |
| E6 | `CreateContainerError: no balloon for annotation` | TP doesn't match topology | Model TP vs NUMA nodes | Fix `--tensor-parallel-size` |
| E7 | vLLM fails with `core ids=[]` | Memory limit > NUMA node, so `cpuset.mems` widened | Pod memory limit | Keep TP=1 ≤ 200 GiB, or raise TP |
| E8 | vLLM crash `shm.cpp thread_num mismatch` | TP=1 spanning NUMA nodes | `cpu` value | Keep within one socket or force TP=1 correctly |
| E9 | Tool calls appear as plain text | Wrong `--tool-call-parser` / chat template, or the model fell back to `defaultModelConfigs` | Pod args | Add a proper model entry |
| E10 | `WRONGPASS` from Redis | URL without the `default:` user | Client URL | Use `REDIS_URL` from the Secret |
| E11 | 401 from the sandbox router | Missing or invalid SA token | Request headers | `kubectl create token …`; set the session header |
| E12 | `commands.run("a && b")` fails | No shell | — | `sh -c "a && b"` |
| E13 | Sandbox `pip install` hangs or fails | Public-only egress; no proxy; public DNS blocked | NetworkPolicy; network rules | Pre-bake packages; private mirror via a custom policy; OpenShell path |
| E14 | OpenShell sandbox: `pip install` → 403 | Deny-all policy (by design) | `openshell logs <sb> \| grep DENIED` | Add the endpoint to `--policy` at create time |
| E15 | `binary … not allowed in policy '_provider_genai_gateway'` | Calling binary not listed | Resolved binary path | Add it to the provider profile; re-run or `provider profile update` |
| E16 | Kata pod `FailedCreatePodSandBox … ENOENT` | devmapper not active (kata-fc) | `systemctl status containerd-devmapper`; `ctr plugins ls` | Fix the thin-pool or use `kata-qemu` |
| E17 | Kata sandbox Pending | No node with `ei-kata-eligible=true` + kata runtime label | `kubectl get nodes --show-labels` | Fix KVM / labels |
| E18 | `uname -r` in a "Kata" sandbox equals the host | Landed on runc | `spec.runtimeClassName` | Use `warmpool="kata-pool"` |
| E19 | Re-install fails with `secrets is forbidden` on `kubeadm token create` | Earlier install stopped mid-kubeadm | Preflight "unfinished install" | `teardown kubernetes`, then install |
| E20 | vLLM-SR loses hot reload: "too many open files" | inotify instances exhausted | `sysctl fs.inotify` | 8192 / 1048576 |
| E21 | Hybrid Router always picks the same model | Single candidate in the tier, or compressed rewards | Logs, `router_state()` | Add candidates; tune `target_tpt`; check boundaries |
| E22 | pgvector insert error "expected 1536 dimensions, not 768" | Schema fixed at 1536; bge-base-en is 768 | Table definition | New table `VECTOR(768)` or parameterise the schema |

---

# Part F — Critique: weaknesses and improvements

Interviewers often ask *"What would you improve?"* Strong answers name a concrete issue, its
impact, a fix, and how you would verify the fix.

| # | Weakness (evidence) | Impact | Improvement | Verify by |
|---|---|---|---|---|
| F1 | No published inference performance numbers | Customers can't size without measuring; the Xeon story lacks evidence | Benchmark suite per SKU (D5) + gated CI test | Published curves; CI thresholds |
| F2 | `VECTOR(1536)` vs 768-d bge-base-en | Local-model inserts fail | Parameterise the dimension (`pgvector_embedding_dim`); per-model tables | Insert test in `validate` |
| F3 | Router default `target_tpt = 1.0` compresses rewards | Slow learning; weak separation | Calibrate from observed time-per-token; expose a metric | Arm-share convergence |
| F4 | Router reward is speed only | Could favour fast but weaker models | Use `quality_weight` with an evaluation signal | Task-success per tier |
| F5 | Router state per process (🔎) | Replicas disagree; state lost on restart | Shared state in Redis | Consistent arm shares |
| F6 | Monkey-patch on LiteLLM internals | Silent breakage on upgrade | Pin the version; router smoke test in validate | Validate fails on breakage |
| F7 | Sandbox router accepts any SA token | Any workload can create sandboxes | Audience-bound tokens or a namespace allow-list | Negative test |
| F8 | Single-instance Redis and pgvector; no password rotation | Downtime; credential hygiene | Operators with replicas; rotation runbook | Failover test |
| F9 | Guard fail-closed with one replica (Recreate) | Guard outage = chat outage | Replicas on separate nodes; capacity planning | Chaos test |
| F10 | Blocks return HTTP 500 | Clients may retry blocked prompts | Client guidance; map to 4xx at the edge if possible | Client tests |
| F11 | Only input guardrail, single check | No output or PII screening | Post-call checks; parallel checks outside the sandbox | Red-team suite |
| F12 | Sandbox egress needs public DNS, no proxy | Breaks on corporate networks | Configurable DNS/proxy for templates | Test on a proxied lab |
| F13 | Upstream router manifests patched by string replace | Fragile if upstream changes | Kustomize patches or a vendored, versioned manifest | Render diff in CI |
| F14 | Many features documented but "not in this release" | Confusing for users | Separate roadmap doc; feature flags with status | Docs review |
| F15 | Docker exposes Postgres/Redis on host ports | Risky on shared hosts | Bind to loopback by default (as Flowise does) | Port scan |
| F16 | Small doc inconsistencies (e.g. Kata template comment shows `template=` while the v1.0.10 SDK uses warm pools; chart vs role defaults differ: Redis 1 Gi vs 10 Gi, pgvector 10 Gi vs 20 Gi) | Confusion when running charts standalone | Align defaults and comments | Lint/docs check |

---

# Part G — Trade-off and opinion questions

Good answers name **both sides** and the **condition** that would change your mind.

- **CPU-first inference?** Yes for the control plane and small-to-mid models with routing (cost,
  availability, data residency). For large dense models at high concurrency, GPUs win on throughput,
  so add a GPU tier behind the same gateway. Decide per tier using measured tokens/s per currency
  unit.
- **Rules or ML classifier for routing?** Rules are free, explainable and tunable but brittle;
  embeddings are robust but cost a model call. Start with rules + bandit; switch if task-success
  data shows misrouting.
- **Fail-closed or fail-open?** Fail-closed for safety, but invest in guard availability. Fail-open
  for optimisations (e.g. routing falls back to the default model).
- **Warm-pool size?** Little's law: pool ≥ claim rate × time to create a pod. Bigger pools cost
  idle resources; smaller ones cause cold starts.
- **pgvector or a dedicated vector DB?** pgvector keeps relational and vector data and operations
  together. Move when recall@k or p95 latency targets at your scale demand it.
- **Ansible or GitOps?** Ansible fits bare metal and host-level steps (Kata, DNS, CPU pinning) and
  the parent installer; GitOps fits continuous reconciliation of in-cluster state. A hybrid is
  common.
- **Report-only preflight?** Avoids false blocks; the risk is ignored warnings. A `--strict` mode
  would suit CI.
- **Kata always on?** No: KVM requirement, devmapper, boot cost and memory. Turn it on for untrusted
  code or multi-tenant platforms.
- **Ambient vs sidecar mesh?** Ambient means no sidecar per pod (lighter, simpler sandboxes) but
  needs exceptions for out-of-mesh workloads (OpenShell, Kata). The repo handles them with
  PeerAuthentication and `dataplane-mode: none`.
- **One shared Redis for all agents?** Simple and cheap, but noisy neighbours and blast radius
  grow. Use ACL users per agent or team, or separate instances for strict isolation.

---

# Part H — Behavioural answers (STAR)

Fill these **only with true experiences**. Situation · Task · Action · Result; quantify where you can.

1. **"Learning a complex system quickly."**
   S: new to agent infrastructure. T: understand a multi-layer platform. A: read code rather than
   just docs; traced one request end to end; mapped layers via `components.yaml`; drew architecture,
   component and sequence diagrams; wrote ADRs and a design doc. R: *(your real result, e.g. you
   can deploy, explain and critique it; documents adopted by the team)*.
2. **"You found a problem others missed."** Candidates from this study (only if you actually raised
   them): the 1536 vs 768 embedding dimension; reward compression in the router; any-SA-token
   access to the sandbox router; no inference benchmarks.
3. **"A trade-off you made."** Fail-closed vs availability; Kata isolation vs cost; rules vs ML
   routing.
4. **"Working across teams."** The product spans layers owned by different groups. Talk about
   interface contracts (`components.yaml`, the OpenAI API, Secrets with connection URLs) as the way
   to coordinate.
5. **"Improving reliability."** Idempotency patterns (secret reuse, failed-release recovery,
   upserts) and preflight catching problems before a 30-minute install.

---

# Part I — Rapid-fire flashcards

Cover the right column and answer.

| Question | Answer |
|---|---|
| Tag line | Production agentic AI stack on Xeon in hours, not months |
| Core insight | Control plane runs efficiently on CPUs |
| Number of blocks | Seven |
| Pattern | Provider Design Pattern |
| Licence | Apache 2.0 |
| Installer | `es_auto_installer.sh` (Toolkit Manager, enterprise-ai-solutions) |
| This repo's layer | agent-toolkit; depends on platform + inference |
| Components on by default | redis_stack, pgvector, agent_sandbox |
| Off by default | openshell, kuberay |
| Keycloak realm when | auth is not LiteLLM |
| Config loaded last | `config.agent-toolkit.yaml` |
| Gateway | LiteLLM :4000 |
| Master key Secret | `litellm-master-key` |
| Default auth | `litellm_vkey` (virtual keys) |
| `api_key: dummy` is | Placeholder for unauthenticated vLLM backends |
| Router virtual model | `hybrid-router` |
| Router tiers | SIMPLE, MEDIUM, COMPLEX, REASONING |
| Tier boundaries | 0.15 / 0.35 / 0.60 |
| Default bandit | Thompson sampling |
| Reward | target_tpt / (target_tpt + latency/tokens) |
| Router code delivery | ConfigMap + callback + monkey-patch |
| Guard model | Qwen3Guard-Gen-0.6B |
| Guardrail name / mode | `content_safety` / `pre_call` |
| Guard failure policy | Fail-closed |
| Block status | HTTP 500 |
| Guard registration | Upsert with PUT |
| Semantic router model | `vllm-sr/auto` |
| Default chat model | qwen2-5-coder-14b |
| Embedding model | bge-base-en (768-d) |
| Speculative variants | `-specdec` |
| TP=1 memory limit | 200 GiB |
| TP ≥ 2 memory limit | 400 GiB |
| `cpu: auto` | One NUMA node of free cores per TP rank |
| Default install memory | ~131 GiB |
| Redis URL user | `default` |
| Redis HBONE port | 15008 |
| pgvector DB/user | agentdb / agentuser |
| pgvector tables | agent_memory, agent_events, agent_cache |
| Vector column | VECTOR(1536), HNSW cosine, m 16, ef_construction 64 |
| pgvector startup budget | 15 min |
| Sandbox version | v1.0.10 |
| Sandbox CRDs | Sandbox, SandboxTemplate, SandboxClaim, SandboxWarmPool |
| Router port / pod port | 8080 / 8888 |
| Router auth | TokenReview, token required |
| Default warm pool | python-pool, 5 |
| Sandbox egress | Public only |
| Sandbox user | uid 1000, drop ALL |
| Extra policy name | eat-sandbox-pool-egress |
| Kata runtimes | kata-fc, kata-qemu |
| Firecracker boot | ~125 ms |
| Kata pool | kata-pool, 1 |
| OpenShell version | 0.1.6 |
| OpenShell key | openshell-sandboxes, budget 50 |
| Placeholder format | `openshell:resolve:env:…` |
| OpenShell workspace class | local-path (NFS ≈ 16 min) |
| Ray versions | operator 1.3.0, Ray 2.40.0 |
| Ray head CPUs | 0 |
| Ray client port | 10001 |
| Preflight cap | 5 min |
| Validate healthy | failed=0 |
| CI scanners | ansible-lint, ShellCheck, Bandit, Checkov, Trivy, Scorecard, dependency review |
| Docker LiteLLM | v1.83.14-stable.patch.2 |
| Docker engines | vLLM (/v1) or OVMS (/v3) |

---

# Part J — Mock rounds, questions to ask, checklist

## J1. Mock round 1: screening (20 minutes)
1. Tell me about this project. *(A2 2-minute pitch)*
2. What is an agent, and what does it need from infrastructure? *(C1, Q1–Q5)*
3. Why LiteLLM? Is it really used? *(Q25–Q30)*
4. How do agents run code safely? *(Q96–Q103)*
5. What would you improve? *(Part F: pick F1, F2, F7)*

## J2. Mock round 2: technical deep dive (45 minutes)
1. Walk me through a request to `hybrid-router`. *(B3–B5)*
2. Explain the bandit and compute a reward. *(Q43–Q47)*
3. Size a model and explain NUMA pinning. *(Q67–Q73)*
4. Why fail-closed? What are the risks? *(Q57–Q64)*
5. Read this YAML: what does it do? *(Q157–Q164)*
6. Debug: chat returns 500 for every request. *(E1)*

## J3. Mock round 3: system design (45 minutes)
- D1 (5,000 developers), then follow-ups: HA (D3), multi-tenant (D4), adding GPUs (D2).

## J4. Questions to ask the interviewer
- Which blocks do customers replace most often, and why?
- How do you benchmark CPU inference per Xeon generation, and how do results feed model defaults?
- Is router state shared across LiteLLM replicas? How do you measure routing quality, not just speed?
- What's the plan for output guardrails and PII, given the `pre_call` latency budget?
- How are rack-scale and Arc (XPU) prioritised for the next release?
- What are the most common failures in customer deployments?

## J5. Seven-day plan

| Day | Study | Practise |
|---|---|---|
| 1 | Part A + B1–B3 | Pitches out loud; draw A3 |
| 2 | B4–B7 | Reward and memory maths by hand |
| 3 | B8–B13 | Explain the sandbox and OpenShell flows without notes |
| 4 | B14–B20 + C1–C6 | Answer aloud; time yourself |
| 5 | C7–C14 + Part D | One design session (45 min) |
| 6 | Parts E, F, G | Diagnose E1–E22 from the symptom only |
| 7 | Parts H, I, J | Full mock; record; fix weak answers |

## J6. Readiness checklist

- [ ] 30-second and 2-minute pitches, without notes
- [ ] Draw the architecture and narrate the request sequence
- [ ] State exactly what this repo installs vs the other layers
- [ ] Explain LiteLLM's real use and what `api_key: dummy` means
- [ ] Compute the router reward and explain Thompson sampling
- [ ] Explain fail-closed and its cost; explain the guard context rule
- [ ] Size a model (weights + TP × KV + runtime) and explain NUMA limits
- [ ] List the sandbox security layers and why `eat-sandbox-pool-egress` exists
- [ ] Explain OpenShell credential isolation end to end
- [ ] Describe the pgvector schema and the 1536-vs-768 issue
- [ ] Name five deployment-automation patterns from B16
- [ ] Diagnose E1, E4, E5, E10, E11, E22 instantly
- [ ] Give three improvements with impact and verification (Part F)
- [ ] Answer one full system-design question in 45 minutes

---

*Companion documents: [`01-understanding-the-agent-toolkit.md`](01-understanding-the-agent-toolkit.md)
(concepts from zero), [`02-design.md`](02-design.md) (design and KPIs), [`adr/`](adr/README.md)
(decisions), [`diagrams/`](diagrams/) (architecture, component, sequence).*
