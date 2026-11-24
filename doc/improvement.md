# Improvement Proposal — Measurement and KPIs

> **What this is:** an audit of what the Intel® Agent Toolkit repository *actually measures* today,
> the gaps, and a prioritised list of KPIs to add, with **where** each belongs and **what it buys**.
> It ends with a **2-minute narration** you can say in an interview.
>
> **Labels:** facts about the repo cite files. 📚 = general industry knowledge, to verify against the
> exact component versions. (proposed) = a suggestion, not something that exists.
>
> **How to build it:** [`improvement-implementation.md`](improvement-implementation.md) (code, queries, alerts, tests, PR plan).
>
> Related: [`02-design.md` §7](02-design.md#7-kpis--what-to-measure-and-why) (target KPIs),
> [`03-interview-prep.md` Part F](03-interview-prep.md#part-f--critique-weaknesses-and-improvements)
> (broader critique).

## Contents

1. [The 2-minute narration](#1-the-2-minute-narration)
2. [Headline finding](#2-headline-finding)
3. [What is measured today](#3-what-is-measured-today)
4. [What is not measured](#4-what-is-not-measured)
5. [KPIs to add: where and why](#5-kpis-to-add-where-and-why)
6. [How to add them without blurring the layers](#6-how-to-add-them-without-blurring-the-layers)
7. [Rollout plan](#7-rollout-plan)
8. [Likely follow-up questions](#8-likely-follow-up-questions)

---

## 1. The 2-minute narration

*About 300 words at a calm pace. Bold phrases are the ones to stress.*

> "I audited what the Agent Toolkit actually measures, versus what the docs promise.
>
> The short answer: **it measures readiness and health, not performance.** Before install, a
> preflight playbook checks every node: time sync, disk headroom, swap, CPU governor, transparent
> huge pages, NUMA layout, DNS, gateway reachability and the Hugging Face token. It produces an
> OK / WARN / FAIL report. After install, each component has a validate step that is pass or fail:
> Redis answers PING, pgvector has its extension, the sandbox warm pool is ready.
>
> At runtime it **hands telemetry to others**. LiteLLM sends every LLM call to Langfuse with tokens,
> cost, latency and the model chosen, and it enforces budgets per key. The Hybrid Router measures
> time-per-token to make its routing decisions, but **never exports it**. The guardrail's block reason
> is only inside an error message. And the repo ships **no Prometheus scrape configs, no alert rules
> and no dashboards**.
>
> So the gaps are exactly the numbers a customer needs to size and trust the platform: **time to
> first token, tokens per second, KV-cache and memory headroom, guardrail block rate, warm-pool
> exhaustion, and cost per completed task.**
>
> I'd fix it with one pattern applied in the layer that owns each component: a metrics switch, a
> PodMonitor so Prometheus scrapes it, a dashboard, two or three alerts, and a validate step that
> checks the scrape target is up.
>
> I'd start with three. **vLLM's built-in metrics**, because they prove the Xeon story and show
> saturation before users feel it. **Guardrail block rate by reason**, because the guard is
> fail-closed: if it's down, chat is down. And **sandbox warm-pool readiness**, so pools are sized by
> data instead of the default of five.
>
> Then I'd add agent-level outcomes, task success and cost per task, using the agent_events table the
> repo already creates. That ties infrastructure spend to business value."

**60-second version** (if you're asked to be brief):

> "It measures readiness and health, not performance: a preflight node report and pass/fail validate
> checks. Runtime telemetry goes to Langfuse, and nothing is exported to Prometheus: no TTFT,
> tokens/s, guardrail block rate or warm-pool metrics. I'd add them per layer with a metrics switch,
> a PodMonitor, a dashboard and alerts, starting with vLLM metrics, guardrail blocks by reason and
> warm-pool readiness, then cost per task from the agent_events table."

---

## 2. Headline finding

**The repository measures readiness and health, not performance.** It ships no `ServiceMonitor`,
`PodMonitor` or `PrometheusRule`, and no Grafana dashboard. A search of the code (excluding
documentation) found none. Runtime telemetry is delegated to Langfuse (through LiteLLM) and to the
platform layer's generic monitoring.

---

## 3. What is measured today

### 3.1 Before install: preflight (`playbooks/preflight/*.yml`)

Point-in-time checks with a status (OK / WARN / FAIL / PENDING), an `evidence` value and a `hint`.

| Check | Evidence recorded | Rule |
|---|---|---|
| Time sync | `chronyc tracking` / `timedatectl` | Not synchronised → FAIL |
| Root disk headroom | `% free` of `/` | > 90 % used → FAIL |
| Containerd disk headroom | `% free` of `/var/lib/containerd` | > 90 % used → FAIL |
| Swap | `swap_total`, `swap_used` MB | Swap in use → FAIL |
| CPU governor | governor, current and max MHz | ≠ `performance` → WARN |
| THP | current mode | `always` → WARN |
| Hardware | `numa_nodes`, `sockets`, `cpus`, `memory GB` | Info |
| Kernel / OS / kubelet | versions | Info |
| Kubelet DNS file | resolv.conf present | Missing → FAIL (auto-fixed when no node runs systemd-resolved) |
| Unfinished Kubernetes install | kubelet config without the env kubeconfig | → FAIL |
| Node connection | machine ID direct vs delegated | Mismatch → FAIL |
| Gateway reachability | ping → TCP/22 → TCP/443 | Unreachable → FAIL |
| External DNS | `getent hosts huggingface.co` | Fails → FAIL |
| Node resource pressure | cluster query | Pressure → FAIL; no cluster → PENDING |
| Hugging Face token | HTTP status from the HF API | ≠ 200 → WARN; unset → PENDING |

Output: `env/<name>/logs/health-report-latest.{json,html,txt}`, cumulative across runs.

### 3.2 After install: validate (`roles/*/tasks/validate.yaml`)

Pass/fail; healthy = `failed=0`.

| Component | Asserted |
|---|---|
| Redis | Pod Running; `PING` → `PONG`; `MODULE LIST` contains `search` |
| pgvector | Pod Running; `vector` extension; Secret `pgvector-credentials` |
| Agent Sandbox | Controller and router ready; CRDs; `python-sandbox-template`; warm-pool readiness (0 ready → **warning only**); Kata template if enabled |
| OpenShell | Gateway ready |
| KubeRay | Operator; head pod |
| Keycloak realm | `KeycloakRealmImport` exists |

### 3.3 At runtime: delegated, not implemented in this repo

| Signal | Producer | Destination | Exported as a metric? |
|---|---|---|---|
| Per LLM call: input, output, tokens, cost, latency, `llm.model_name` | LiteLLM `success_callback` / `failure_callback: ["langfuse"]` (`docker/docker-compose.yml`, generated `litellm/config.yaml`; on Kubernetes the inference layer) | Langfuse | Trace data, not Prometheus |
| Spend per virtual key vs `max_budget` | LiteLLM | LiteLLM database / UI | **Enforced**; no alerting |
| Latency, completion tokens → time per token → reward; arm counts and means | Hybrid Router (inference layer) | In memory, logs, `router_state()` | **No.** Used only for routing |
| Guardrail block reason | Guardrail code | Inside the HTTP 500 `error.message` | **No** |
| Policy denials | OpenShell supervisor | `openshell logs … DENIED` | **No** |
| Liveness | Kubernetes probes; Docker healthchecks | Restarts | Only via the platform's kube-state-metrics |

### 3.4 One-off benchmark numbers (manual; rack-scale, not in this release)

iperf3 83.1 Gbit/s cross-leaf; pod RTT 0.7 ms; Ceph sequential write 1.42 GB/s; 29 k / 12.5 k 4K
IOPS; fabric NIC 18–20 Gbit/s under load. They're documented in `docs/rack-scale-deployment.md`,
not automated or repeated.

### 3.5 Docker path

`check_system_resources` in `docker/deploy.sh` estimates memory (8 GB base + per model) and warns;
containers have healthchecks.

---

## 4. What is not measured

| Area | Missing |
|---|---|
| Inference | Time to first token (TTFT), inter-token latency (ITL), tokens/s, queue depth, KV-cache usage |
| Capacity | Memory headroom vs limit per model pod; OOM-kill counts as an alert |
| Gateway | Request and error rates, rate-limited (429) and budget-rejected counts, overhead latency |
| Guardrail | Block rate by reason; latency added; guard availability |
| Router | Tier distribution; traffic share per model; reward trend |
| Sandbox | Claim latency; warm-pool exhaustion; execution duration and failure rate |
| Memory stores | Redis and Postgres latency, size, connections; vector query latency and recall |
| Business | Task success rate; cost per task; time per task |
| Release quality | Install duration and validate pass rate over releases; performance regressions |

---

## 5. KPIs to add: where and why

Ranked by value. **Owner layer** decides which repository changes: *this repo* = agent-toolkit
layer; *inference* / *platform* = layers of `enterprise-ai-solutions`.

| # | KPI | Owner layer: where exactly | Advantage |
|---|---|---|---|
| 1 | **Inference:** TTFT p50/p95, ITL, output tokens/s, running and waiting requests, KV-cache use % | Inference: scrape vLLM's built-in `/metrics` (📚) with a `PodMonitor` in the model chart; Grafana dashboard | Core evidence for the Xeon story; per-SKU sizing; shows saturation before users feel it |
| 2 | **Memory headroom and OOM:** working set vs limit per model pod; OOMKilled restarts | Platform: `PrometheusRule` on cAdvisor and kube-state-metrics for `llm-inference` | Catches KV-cache blow-ups (exit 137) before outages |
| 3 | **Gateway:** request rate, errors by code, p95 latency, 429s, budget rejections, spend per key vs budget | Inference: LiteLLM's Prometheus integration (📚 check edition and licence) or derive from Langfuse | Service levels; cost governance with alerts instead of silent blocks |
| 4 | **Guardrail:** block rate *by reason* (unsafe / unreachable / too long / unparseable), added latency, guard availability | Inference: a reason label in the guardrail template; scrape the guard vLLM's metrics | Fail-closed means guard downtime = chat downtime; tune false positives with data |
| 5 | **Router:** share of requests per tier, traffic share per model, mean reward per tier, escalation rate | Inference: export `router_state()` as metrics, or tag Langfuse traces with tier and reward | Proves cost and latency savings; exposes reward compression at the default `target_tpt = 1.0` |
| 6 | **Sandbox:** claim latency, warm-pool ready/size, pool-exhaustion events, execution duration, non-zero exit rate, sandbox OOMs, router 401s | **This repo**, `roles/agent_sandbox`: `PodMonitor` for controller and router (📚 controller-runtime operators usually expose `/metrics`); alert on pool readiness; threshold in `validate.yaml` instead of a warning | Size warm pools from data (Little's law) instead of the default 5; catch cold starts and capacity limits |
| 7 | **Redis and pgvector:** command latency, memory, evictions, clients; Postgres connections, cache hit, table and index size, slow queries; **vector query latency and recall@k** | **This repo**, `charts/redis-stack`, `charts/pgvector`: optional exporter sidecars (📚 standard redis and postgres exporters) behind `*_metrics_enabled`, `PodMonitor`, dashboard | Capacity planning for single-instance stores; catches unbounded growth of `agent_events` and `agent_cache` |
| 8 | **Agent outcomes:** task success rate, steps per task, tool-call error rate, **cost per task**, time per task | Agent side, enabled by **this repo**: a reference SQL view over `agent_events` + Langfuse traces; documented `event_type` values | The only business-level KPIs; ties infrastructure cost to completed work |
| 9 | **Install and lifecycle:** install duration, preflight critical count, validate pass rate per release | Installer + CI: add duration fields to the preflight report | Turns "hours, not months" into a measured number |
| 10 | **Security:** OpenShell denials per policy, sandbox router 401s, secret age | **This repo**, `roles/openshell` + router: log-based metrics via Loki | Shows isolation works; flags credentials due for rotation |
| 11 | **Performance gate in CI:** tokens/s at the TTFT target, fixed model and prompt set | Release CI (e.g. a Workload Services Framework test case, kept separate from the toolkit) | Catches regressions when vLLM or LiteLLM versions change |

**Example agent-outcome view** (proposed, for KPI #8; assumes agents write `task_start` / `task_end`
events with a `success` flag and a `cost` in `payload`):

```sql
CREATE VIEW agent_task_kpis AS
SELECT agent_id,
       date_trunc('day', created_at)                                  AS day,
       count(*) FILTER (WHERE event_type = 'task_end')                AS tasks,
       avg((payload->>'success')::int) FILTER (WHERE event_type = 'task_end') AS success_rate,
       avg((payload->>'cost')::numeric) FILTER (WHERE event_type = 'task_end') AS cost_per_task,
       avg(duration_ms) FILTER (WHERE event_type = 'task_end')        AS avg_task_ms,
       count(*) FILTER (WHERE event_type = 'tool_call' AND (payload->>'exit_code')::int <> 0)
         ::numeric / NULLIF(count(*) FILTER (WHERE event_type = 'tool_call'), 0) AS tool_error_rate
FROM agent_events
GROUP BY agent_id, day;
```

---

## 6. How to add them without blurring the layers

Apply one pattern per component, **in the layer that owns it**:

| Step | Artefact | Example for `agent_sandbox` (this repo) |
|---|---|---|
| 1 | A switch `<component>_metrics_enabled` (default on when `observability_enabled`) | `agent_sandbox_metrics_enabled` in `roles/agent_sandbox/defaults/main.yaml` |
| 2 | A `PodMonitor` / `ServiceMonitor` so the platform Prometheus scrapes it | Controller and router metrics ports |
| 3 | A dashboard ConfigMap the platform Grafana picks up | "Agent Sandbox": pool ready/size, claims/min, claim latency, exec duration |
| 4 | A `PrometheusRule` with 2–3 alerts that matter | Pool < 50 % ready for 5 min; router 5xx > 1 %; sandbox OOMs > 0 |
| 5 | A `validate.yaml` assertion that the scrape target is up | Fail validate if the target is down |

Ownership summary:

| Layer | KPIs |
|---|---|
| **This repo (agent-toolkit)** | #6 sandbox, #7 Redis/pgvector, #8 agent-outcome view, #10 security |
| Inference layer | #1 vLLM, #3 gateway, #4 guardrail, #5 router |
| Platform layer | #2 memory/OOM alerts, Grafana and Prometheus hosting |
| CI / release | #9 lifecycle, #11 performance gate |

---

## 7. Rollout plan

| Phase | Scope | Exit criterion |
|---|---|---|
| 1 (first) | #1 vLLM metrics, #4 guardrail by reason, #6 warm pool | Dashboards live; three alerts firing correctly in a test |
| 2 | #2 OOM alerts, #3 gateway, #5 router | Router savings visible on mixed traffic; budget alerts before blocks |
| 3 | #7 stores, #8 outcome view | Cost per task reported per agent |
| 4 | #9, #10, #11 | Per-release KPI report with a CI performance gate |

**Why this order:** phase 1 covers what every request goes through (inference) and the two things
that can take the whole service down (the fail-closed guard and warm-pool exhaustion).

---

## 8. Likely follow-up questions

| Question | Short answer |
|---|---|
| Isn't Langfuse enough? | It's per-request tracing for debugging and cost, not time-series metrics with alerting. You need both: Langfuse to explain one request, Prometheus to watch the fleet |
| Why not put all metrics in this repo? | Ownership: vLLM, LiteLLM, the router and the guardrail belong to the inference layer. Changing them here would blur the layer boundary and couple releases |
| What's the first alert you'd create? | Guard unreachable, because with fail-closed it blocks every chat request |
| How do you size the warm pool from these metrics? | Little's law: pool ≥ claim rate × time to create a fresh pod; adjust until pool exhaustion events stay at zero at peak |
| How would you prove the router saves money? | A/B on mixed traffic: `hybrid-router` vs always-largest model; compare average latency and cost at equal task success (KPI #8) |
| Which KPI goes to leadership? | Cost per successful task, and output tokens/s at the TTFT target per server |
