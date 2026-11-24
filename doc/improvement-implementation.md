# Implementing the KPI Recommendations — Detailed Guide

> Companion to [`improvement.md`](improvement.md). That document says **what** to measure and
> **why**; this one shows **how**: the files to change, the code, the queries, the alerts, the
> tests and the rollout.
>
> **Status:** a design with code sketches. **Nothing here is applied to the repository yet.**
> Each change names the layer and file it belongs to, so the agent-toolkit layer doesn't absorb
> work owned by the inference or platform layers.
>
> **Labels:** facts about this repo cite files. 📚 = general knowledge of third-party components
> (vLLM, LiteLLM, Prometheus Operator, kube-state-metrics, exporters). Metric names, flags and
> labels vary between versions, so **every 📚 item has a "verify" command; run it first**.

> **Verified against `toolkit-manager` and `enterprise-inference`.** Three simplifications apply:
> 1. Prometheus already discovers ServiceMonitors and PodMonitors in **all namespaces**, with no
>    selector labels needed (`toolkit-manager: roles/observability/tasks/install_helm.yaml:167–170`),
>    so `monitoring_selector_labels` below can stay empty.
> 2. Grafana loads ConfigMaps labelled `grafana_dashboard: "1"` (`…install_helm.yaml:209`), as assumed.
> 3. **§2 (vLLM scraping and dashboard) already exists** in `enterprise-inference: roles/llm_services`
>    (ServiceMonitor `vllm-cpu`, dashboard `vllm-cpu.json`). Only the **PrometheusRule alerts** in §2
>    are new work. The LiteLLM ServiceMonitor (§5.2) exists in its chart but is off by default.

## Contents

0. [Before writing any code: four checks](#0-before-writing-any-code-four-checks)
1. [The common pattern](#1-the-common-pattern)
2. [Phase 1a — vLLM inference metrics (inference layer)](#2-phase-1a--vllm-inference-metrics-inference-layer)
3. [Phase 1b — Guardrail block rate by reason (inference layer)](#3-phase-1b--guardrail-block-rate-by-reason-inference-layer)
4. [Phase 1c — Sandbox warm pool and claim latency (this repo)](#4-phase-1c--sandbox-warm-pool-and-claim-latency-this-repo)
5. [Phase 2 — Memory/OOM, gateway, router](#5-phase-2--memoryoom-gateway-router)
6. [Phase 3 — Redis, pgvector, agent outcomes (this repo)](#6-phase-3--redis-pgvector-agent-outcomes-this-repo)
7. [Phase 4 — Lifecycle, security, CI performance gate](#7-phase-4--lifecycle-security-ci-performance-gate)
8. [Dashboards](#8-dashboards)
9. [Testing the monitoring itself](#9-testing-the-monitoring-itself)
10. [Delivery plan: pull requests, owners, effort](#10-delivery-plan-pull-requests-owners-effort)

---

## 0. Before writing any code: four checks

The platform layer installs the observability stack (`observability_enabled: true`). Confirm what
it provides before building on it:

```bash
# 1. Prometheus Operator CRDs exist (PodMonitor, ServiceMonitor, PrometheusRule)
kubectl get crd podmonitors.monitoring.coreos.com servicemonitors.monitoring.coreos.com prometheusrules.monitoring.coreos.com

# 2. Which labels Prometheus uses to pick up monitors and rules (often a release label)
kubectl get prometheus -A -o jsonpath='{range .items[*]}{.metadata.name}{" podMonitorSelector="}{.spec.podMonitorSelector}{" ruleSelector="}{.spec.ruleSelector}{"\n"}{end}'

# 3. How Grafana discovers dashboards (sidecar label on ConfigMaps)
kubectl get deploy -A -l app.kubernetes.io/name=grafana -o yaml | grep -A3 -i 'LABEL'

# 4. Whether kube-state-metrics runs, and with which flags
kubectl get deploy -A -l app.kubernetes.io/name=kube-state-metrics -o yaml | grep -E 'image:|--custom-resource'
```

**The mesh caveat (important, and easy to miss).** Toolkit namespaces run in the Istio ambient mesh
with **STRICT mTLS** (the OpenShell role notes "the mesh-wide PeerAuthentication is STRICT"). A
Prometheus outside the mesh scraping pods inside it over plaintext will be **rejected**, so
metrics silently go missing. Choose one fix:

| Option | How | Trade-off |
|---|---|---|
| A (preferred) | Enrol the monitoring namespace in the mesh: `kubectl label ns <monitoring-ns> istio.io/dataplane-mode=ambient` | Scrapes are mTLS like everything else |
| B | A port-level PERMISSIVE exception for metrics ports only, the same technique the OpenShell role uses for LiteLLM | Plaintext on metrics ports only; keep the list small |

```yaml
# Option B: example for the Redis exporter port (one per workload with a metrics port)
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata: { name: redis-metrics-permissive, namespace: redis }
spec:
  selector: { matchLabels: { app: redis-stack-server } }
  mtls: { mode: STRICT }
  portLevelMtls:
    "9121": { mode: PERMISSIVE }
```

The same applies to **NetworkPolicies**: the Redis policy only admits the Redis port and HBONE
15008. A metrics port needs its own ingress rule from the monitoring namespace (see §6.1).

---

## 1. The common pattern

Every component gets the same five pieces, **in the layer that owns it**:

```
<component>_metrics_enabled  (switch, default = observability_enabled)
   ├─ scrape:    PodMonitor / ServiceMonitor            → Prometheus collects
   ├─ derive:    PromQL (recording rules for heavy queries)
   ├─ alert:     PrometheusRule (2–3 alerts that matter)
   ├─ show:      Grafana dashboard ConfigMap (sidecar-discovered)
   └─ prove:     validate.yaml asserts the target is up / the rule exists
```

For **this repo**, the Ansible shape is identical in each role. Example for `agent_sandbox`:

```yaml
# roles/agent_sandbox/defaults/main.yaml  (add)
agent_sandbox_metrics_enabled: "{{ observability_enabled | default(false) | bool }}"
agent_sandbox_min_ready_ratio: 0          # 0 = today's behaviour (warn only); e.g. 0.5 makes validate fail
monitoring_namespace: "monitoring"        # where Prometheus/Grafana live (platform layer; verify)
monitoring_selector_labels: {}            # e.g. { release: kube-prometheus-stack } — from check 0.2
grafana_dashboard_label: { grafana_dashboard: "1" }   # from check 0.3 (📚 common default)
```

```yaml
# roles/agent_sandbox/tasks/install.yaml  (append before "Install complete")
- name: "agent_sandbox | Monitoring"
  ansible.builtin.include_tasks: metrics.yaml
  when: agent_sandbox_metrics_enabled | bool
```

```yaml
# roles/agent_sandbox/tasks/metrics.yaml  (new)
- name: "agent_sandbox | metrics | Is the Prometheus Operator installed?"
  kubernetes.core.k8s_info:
    api_version: apiextensions.k8s.io/v1
    kind: CustomResourceDefinition
    name: prometheusrules.monitoring.coreos.com
  register: _prom_crd

- name: "agent_sandbox | metrics | Skip (no Prometheus Operator)"
  ansible.builtin.debug:
    msg: "observability stack not found — metrics skipped (same graceful-skip pattern as Kata)"
  when: _prom_crd.resources | length == 0

- name: "agent_sandbox | metrics | Apply alert rules and dashboard"
  when: _prom_crd.resources | length > 0
  kubernetes.core.k8s:
    state: present
    definition: "{{ lookup('ansible.builtin.template', item) | from_yaml_all | list }}"
  loop:
    - "{{ role_path }}/../../charts/agent-sandbox/monitoring/prometheusrule.yaml.j2"
    - "{{ role_path }}/../../charts/agent-sandbox/monitoring/dashboard-configmap.yaml.j2"
```

This follows the repo's existing conventions: feature detection, then a graceful skip (like Kata
and the OpenShell provider), and `state: present` for idempotency.

---

## 2. Phase 1a — vLLM inference metrics (inference layer)

**Owner:** inference layer (`core/helm-charts/vllm` in enterprise-ai-solutions). Not this repo.

**Why it's cheap:** vLLM already serves Prometheus metrics on its API port at `/metrics` (📚). We
only need Prometheus to scrape it.

**Verify first:**

```bash
POD=$(kubectl get pods -n llm-inference -o name | grep qwen2-5-coder-14b | head -1)
kubectl exec -n llm-inference $POD -c main -- python3 -c \
 "import urllib.request;print(urllib.request.urlopen('http://localhost:8000/metrics').read().decode()[:3000])" \
 | grep -E '^vllm:(time_to_first_token|inter_token|time_per_output|e2e_request|num_requests|kv_cache|gpu_cache|generation_tokens|prompt_tokens|num_preemptions)' | cut -d'{' -f1 | sort -u
kubectl get pods -n llm-inference --show-labels | head -3     # find a stable selector label
```

**Scrape:**

```yaml
# inference layer: vllm chart, templates/podmonitor.yaml (rendered when metrics.enabled)
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: vllm-models
  namespace: llm-inference
  labels: {{ toYaml .Values.metrics.selectorLabels | nindent 4 }}   # e.g. release: kube-prometheus-stack
spec:
  selector:
    matchExpressions:
      - { key: serving.kserve.io/inferenceservice, operator: Exists }   # 📚 verify the label
  podMetricsEndpoints:
    - port: http            # the container's named port serving :8000 (verify name)
      path: /metrics
      interval: 15s
```

**KPI queries** (📚 names from vLLM's metrics; newer versions renamed `gpu_cache_usage_perc` to
`kv_cache_usage_perc`, so use whichever check 1 printed):

| KPI | PromQL |
|---|---|
| TTFT p95 per model | `histogram_quantile(0.95, sum by (le, model_name) (rate(vllm:time_to_first_token_seconds_bucket[5m])))` |
| Inter-token latency p95 | `histogram_quantile(0.95, sum by (le, model_name) (rate(vllm:inter_token_latency_seconds_bucket[5m])))` (older: `vllm:time_per_output_token_seconds_bucket`) |
| Output tokens/s | `sum by (model_name) (rate(vllm:generation_tokens_total[1m]))` |
| Prompt tokens/s | `sum by (model_name) (rate(vllm:prompt_tokens_total[1m]))` |
| Queue | `sum by (model_name) (vllm:num_requests_waiting)`, `… vllm:num_requests_running` |
| KV-cache use | `max by (model_name) (vllm:kv_cache_usage_perc)` |
| Preemptions (KV pressure) | `sum by (model_name) (rate(vllm:num_preemptions_total[5m]))` |

**Alerts:**

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata: { name: vllm-slo, namespace: llm-inference }
spec:
  groups:
  - name: vllm
    rules:
    - alert: VllmSaturated
      expr: sum by (model_name) (vllm:num_requests_waiting) > 0
            and max by (model_name) (vllm:kv_cache_usage_perc) > 0.9
      for: 10m
      labels: { severity: warning }
      annotations:
        summary: "{{ $labels.model_name }}: queue building with KV cache > 90 %"
        runbook: "Add a replica / raise VLLM_CPU_KVCACHE_SPACE within the memory limit / route more to smaller tiers"
    - alert: VllmTtftSloBreach
      expr: histogram_quantile(0.95, sum by (le, model_name) (rate(vllm:time_to_first_token_seconds_bucket[10m]))) > 5
      for: 15m                      # 5 s is a placeholder SLO: set per use case
      labels: { severity: warning }
```

**Result:** the inference report from `01-…` §4.5 becomes a live dashboard rather than a one-off
benchmark.

---

## 3. Phase 1b — Guardrail block rate by reason (inference layer)

**Owner:** inference layer: the guardrail template `roles/litellm/templates/qwen3guard_gen.py.j2`
and the guard vLLM release.

**Constraint:** the guardrail code runs inside LiteLLM's RestrictedPython sandbox: no imports, no
classes, no f-strings, only injected primitives (`block`, `allow`, `http_post`, …). **It cannot
emit metrics directly.** So we make every block **machine-readable**, then count it outside.

**Step 1: a stable reason code in every block message** (template change, sandbox-safe):

```python
# qwen3guard_gen.py.j2 — illustrative; keep the template's existing logic and add the code prefix
# reason codes: unsafe | unreachable | http_error | too_long | unparseable
return block("[guard:unreachable] Blocked by the content-safety guardrail: guard model unreachable")
...
return block("[guard:unsafe] Blocked by the content-safety guardrail: unsafe content (categories: " + cats + ")")
```

The message stays human-readable (no client breakage). The `[guard:<code>]` prefix makes it
countable.

**Step 2: count it.** Choose based on what the platform has:

| Option | How | Notes |
|---|---|---|
| **A. Logs → Loki metric** (no new code) | LiteLLM logs the failed request with the message; derive a metric with LogQL | Needs Loki (platform observability). Verify that the message appears in `kubectl logs -n litellm deploy/litellm` |
| B. Langfuse | Failure callbacks already send failed calls to Langfuse; filter on the error text | Good for investigation; weak for alerting |
| C. LiteLLM Prometheus | If enabled (§5.2), failure counters carry an exception label (📚) | Depends on LiteLLM edition and version |

```logql
# Option A — blocks per reason (Grafana panel or Loki ruler alert)
sum by (reason) (
  count_over_time({namespace="litellm"} |~ "Blocked by the content-safety guardrail"
                  | regexp "\\[guard:(?P<reason>[a-z_]+)\\]" [5m]))
```

**Step 3: guard availability and latency.** The guard is a vLLM release, so the §2 PodMonitor
covers it (model `qwen3guard`). Then:

```yaml
- alert: GuardUnavailable           # fail-closed: this means ALL chat requests are blocked
  expr: absent(up{namespace="llm-inference", pod=~"qwen3guard.*"} == 1)
  for: 2m
  labels: { severity: critical }
  annotations:
    summary: "Content-safety guard is down — every chat request is being blocked (fail-closed)"
    runbook: "kubectl get pods -n llm-inference | grep qwen3guard; ./model-manager deploy qwen3guard --wait"
- alert: GuardBlockSpike
  expr: sum(rate({namespace="litellm"} |~ "\\[guard:(unreachable|http_error|unparseable)\\]" [5m])) > 0
  # Loki ruler syntax; equivalent PromQL if using option C
```

**KPIs gained:** block rate by reason, guard p95 latency (from its vLLM histograms) and guard
availability. Pair "unsafe" blocks with a labelled sample to estimate false positives.

---

## 4. Phase 1c — Sandbox warm pool and claim latency (this repo)

**Owner:** **this repository**: `roles/agent_sandbox`, `charts/agent-sandbox/monitoring/` (new).

### 4.1 Warm-pool readiness as a metric

The warm pool already reports readiness in its status. The existing
`roles/agent_sandbox/tasks/validate.yaml` reads `item.status.readyReplicas` and
`item.spec.replicas`. Export the same fields with **kube-state-metrics Custom Resource State**
(📚), with no new code to maintain:

```yaml
# charts/agent-sandbox/monitoring/ksm-customresourcestate.yaml  (new)
# Add to kube-state-metrics' --custom-resource-state-config (platform layer owns KSM;
# this repo ships the snippet + the RBAC it needs).
kind: CustomResourceStateMetrics
spec:
  resources:
    - groupVersionKind: { group: extensions.agents.x-k8s.io, version: v1beta1, kind: SandboxWarmPool }
      metricNamePrefix: agent_sandbox_warmpool
      labelsFromPath:
        name: [metadata, name]
        namespace: [metadata, namespace]
      metrics:
        - name: desired_replicas
          help: "Sandboxes the pool should keep pre-warmed"
          each: { type: Gauge, gauge: { path: [spec, replicas] } }
        - name: ready_replicas
          help: "Pre-warmed sandboxes ready to hand out"
          each: { type: Gauge, gauge: { path: [status, readyReplicas], nilIsZero: true } }
```

```yaml
# RBAC so kube-state-metrics can read the CRD (applied by the role)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata: { name: ksm-agent-sandbox-reader }
rules:
  - apiGroups: ["extensions.agents.x-k8s.io"]
    resources: ["sandboxwarmpools"]
    verbs: ["list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata: { name: ksm-agent-sandbox-reader }
roleRef: { apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: ksm-agent-sandbox-reader }
subjects:
  - { kind: ServiceAccount, name: kube-state-metrics, namespace: "{{ monitoring_namespace }}" }   # verify SA name
```

**Alerts** (`charts/agent-sandbox/monitoring/prometheusrule.yaml.j2`):

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: agent-sandbox
  namespace: "{{ agent_sandbox_namespace }}"
  labels: {{ monitoring_selector_labels | to_json }}
spec:
  groups:
  - name: agent-sandbox
    rules:
    - record: agent_sandbox:warmpool_ready_ratio
      expr: agent_sandbox_warmpool_ready_replicas / clamp_min(agent_sandbox_warmpool_desired_replicas, 1)
    - alert: SandboxWarmPoolDepleted
      expr: agent_sandbox:warmpool_ready_ratio < 0.5
      for: 5m
      labels: { severity: warning }
      annotations:
        summary: "Warm pool {{ $labels.name }} below 50 % ready — agents will hit cold starts"
        runbook: "Raise agent_sandbox_python_warm_pool_size; check node capacity and image pulls"
    - alert: SandboxWarmPoolEmpty
      expr: agent_sandbox_warmpool_ready_replicas == 0 and agent_sandbox_warmpool_desired_replicas > 0
      for: 2m
      labels: { severity: critical }
    - alert: SandboxOOMKilled
      expr: increase(kube_pod_container_status_restarts_total{namespace="{{ agent_sandbox_namespace }}"}[15m]) > 0
            and on (pod, container) kube_pod_container_status_last_terminated_reason{reason="OOMKilled"} == 1
      labels: { severity: info }
```

### 4.2 Make `validate` enforce readiness (optional, backward-compatible)

Today `validate` only **warns** when a pool has 0 ready. Add a threshold that defaults to today's
behaviour:

```yaml
# roles/agent_sandbox/tasks/validate.yaml  (add after the existing warning task)
- name: "agent_sandbox | validate | Enforce warm-pool readiness ratio"
  ansible.builtin.assert:
    that: >-
      (item.status.readyReplicas | default(0) | int) >=
      ((item.spec.replicas | default(0) | int) * (agent_sandbox_min_ready_ratio | float)) | round(0, 'ceil') | int
    fail_msg: >-
      SandboxWarmPool {{ item.metadata.name }}: {{ item.status.readyReplicas | default(0) }}/{{ item.spec.replicas }}
      ready, below agent_sandbox_min_ready_ratio={{ agent_sandbox_min_ready_ratio }}
    quiet: true
  loop: "{{ _val_warmpools.resources | default([]) }}"
  loop_control: { label: "{{ item.metadata.name }}" }
  when: (agent_sandbox_min_ready_ratio | float) > 0
```

### 4.3 Claim latency and execution time: measured where they happen (agent side)

The sandbox **router** sees each request, but whether it exposes per-claim timings is upstream
behaviour, so verify (`kubectl port-forward svc/sandbox-router-svc 8080:8080` then
`curl -s localhost:8080/metrics`). The reliable place is the **client**, which already wraps every
call. A thin wrapper in the agent:

```python
# agent side (e.g. a shared helper your LangGraph tools import)
import os, time
from prometheus_client import Histogram, Counter, start_http_server
from k8s_agent_sandbox import SandboxClient
from k8s_agent_sandbox.models import SandboxDirectConnectionConfig

CLAIM = Histogram("agent_sandbox_claim_seconds", "create_sandbox latency", ["pool"],
                  buckets=(.05, .1, .25, .5, 1, 2, 5, 10, 30))
EXEC = Histogram("agent_sandbox_exec_seconds", "commands.run latency", ["pool"])
FAIL = Counter("agent_sandbox_exec_nonzero_total", "commands with exit_code != 0", ["pool"])
start_http_server(9400)   # scraped by a PodMonitor on the agent's namespace

client = SandboxClient(connection_config=SandboxDirectConnectionConfig(
    api_url="http://sandbox-router-svc.agent-sandbox-system.svc.cluster.local:8080"))

def new_sandbox(pool="python-pool"):
    t = time.perf_counter()
    sb = client.create_sandbox(warmpool=pool, namespace="agent-sandbox-system")
    CLAIM.labels(pool).observe(time.perf_counter() - t)
    sb.connector.session.headers["Authorization"] = f"Bearer {os.environ['ROUTER_AUTH_TOKEN']}"
    return sb

def run(sb, cmd, pool="python-pool"):
    t = time.perf_counter()
    r = sb.commands.run(cmd)
    EXEC.labels(pool).observe(time.perf_counter() - t)
    if getattr(r, "exit_code", 0) != 0:
        FAIL.labels(pool).inc()
    return r
```

Ship this helper as an **example** in the docs (this repo owns the SDK guidance in
`docs/agent-sandbox.md`), not as toolkit runtime code.

**Using the numbers: warm-pool sizing.** By Little's law, required ready pods ≈ claim rate ×
time to create a fresh pod. Use `rate(agent_sandbox_claim_seconds_count[5m])` for the claim rate.
Measure fresh-pod creation time by setting the pool to 0 in a test.

---

## 5. Phase 2 — Memory/OOM, gateway, router

### 5.1 Memory headroom and OOM (platform layer, rules only)

Uses metrics every Prometheus/kube-state-metrics install already has (📚 cAdvisor + KSM):

```yaml
- record: model:memory_headroom_ratio
  expr: |
    max by (namespace, pod, container) (container_memory_working_set_bytes{namespace="llm-inference", container!=""})
    / on (namespace, pod, container)
    max by (namespace, pod, container) (kube_pod_container_resource_limits{namespace="llm-inference", resource="memory"})
- alert: ModelNearMemoryLimit
  expr: model:memory_headroom_ratio > 0.9
  for: 10m
  annotations:
    summary: "{{ $labels.pod }} at {{ $value | humanizePercentage }} of its memory limit — OOM (exit 137) risk"
    runbook: "Footprint ≈ weights + TP × VLLM_CPU_KVCACHE_SPACE + runtime (docs/xeon-model-configuration.md)"
- alert: ModelOOMKilled
  expr: increase(kube_pod_container_status_restarts_total{namespace="llm-inference"}[15m]) > 0
        and on (pod, container) kube_pod_container_status_last_terminated_reason{reason="OOMKilled"} == 1
  labels: { severity: critical }
```

### 5.2 Gateway metrics (inference layer)

LiteLLM can export Prometheus metrics through a `prometheus` callback, served on the proxy's
`/metrics` (📚 **check your LiteLLM edition and licence**: this has been an enterprise feature in
some versions).

```yaml
# inference layer: LiteLLM config (genai-gateway chart values)
litellm_settings:
  callbacks: ["custom_hybrid_router.proxy_handler_instance", "prometheus"]
  success_callback: ["langfuse"]
  failure_callback: ["langfuse"]
```

```bash
# verify what it exports before writing queries
kubectl port-forward -n litellm svc/litellm 4000:4000 &
curl -s localhost:4000/metrics | grep -E '^litellm_' | cut -d'{' -f1 | sort -u
```

KPIs to chart from the names you find: requests and failures per model and key, latency
histograms, spend per key, remaining budget per key. **Alert on budget before the block**: e.g.
remaining budget < 10 % of `max_budget`, rather than discovering it when requests start failing.

**If the Prometheus callback isn't available:** derive the same KPIs from Langfuse (it already
receives every call), and keep Prometheus for infrastructure only.

### 5.3 Hybrid Router metrics (inference layer)

**Owner:** inference layer, `core/helm-charts/genai-gateway/router/custom_hybrid_router.py` (mounted
from the ConfigMap `litellm-router-code`, so no image rebuild is needed). The router source isn't in
this repo; the hooks below are named in `docs/hybrid-router.md`.

Two complementary outputs:

**(a) Tag every routed request** so Langfuse shows the decision, at zero infrastructure cost:

```python
# inside the pre-routing hook, after classify() and pick_model()
md = data.setdefault("metadata", {})
md.update({"hybrid_router_tier": tier, "hybrid_router_model": chosen})
```

**(b) Export counters and reward for fleet-level dashboards:**

```python
# top of custom_hybrid_router.py — illustrative
from prometheus_client import Counter, Histogram, Gauge, start_http_server
ROUTED  = Counter("hybrid_router_requests_total", "routed requests", ["tier", "model"])
TPT     = Histogram("hybrid_router_time_per_token_seconds", "observed latency/token", ["tier", "model"],
                    buckets=(.005, .01, .02, .05, .1, .2, .5, 1))
REWARD  = Histogram("hybrid_router_reward", "bandit reward", ["tier", "model"],
                    buckets=(.1, .2, .4, .6, .8, .9, .95, .99, 1))
ARMMEAN = Gauge("hybrid_router_arm_mean_reward", "bandit running mean", ["tier", "model"])
try:
    start_http_server(9105)          # once per process
except OSError:
    pass                             # already started (re-import)

# in pick_model():              ROUTED.labels(tier, chosen).inc()
# in async_log_success_event(): TPT.labels(tier, model).observe(tpt); REWARD.labels(tier, model).observe(reward)
#                               ARMMEAN.labels(tier, model).set(router_state()[tier][model]["mean"])   # per router_state() shape
```

Then: add `containerPort: 9105` (named `router-metrics`) to the LiteLLM deployment, a PodMonitor for
it, and the mesh/NetworkPolicy exceptions from §0.

📚 **Pitfall:** if LiteLLM runs several worker *processes*, each has its own in-memory registry
(and its own bandit). Either run one worker per pod and scale by pods, or use prometheus_client's
multiprocess mode (`PROMETHEUS_MULTIPROC_DIR`). This also highlights the per-replica bandit-state
issue (F5 in the critique).

**Router KPIs:**

| KPI | PromQL |
|---|---|
| Tier mix | `sum by (tier) (rate(hybrid_router_requests_total[1h])) / ignoring(tier) group_left sum(rate(hybrid_router_requests_total[1h]))` |
| Model share within tier | `sum by (tier, model) (rate(hybrid_router_requests_total[1h]))` |
| Reward compression check | `histogram_quantile(0.1, sum by (le, tier) (rate(hybrid_router_reward_bucket[1h])))`: if p10 is already > 0.9, rewards are compressed, so lower `target_tpt` |
| Time per token by model | `histogram_quantile(0.5, sum by (le, model) (rate(hybrid_router_time_per_token_seconds_bucket[30m])))` |

---

## 6. Phase 3 — Redis, pgvector, agent outcomes (this repo)

### 6.1 Redis exporter sidecar (`charts/redis-stack`)

```yaml
# charts/redis-stack/charts/redis-stack-server/values.yaml  (add)
metrics:
  enabled: false
  image: "oliver006/redis_exporter"   # 📚 widely used exporter
  tag: "<pin-a-release>"              # pin exactly, as the repo does for every image
  port: 9121
  monitoringNamespace: "monitoring"
  podMonitorLabels: {}
```

```yaml
# templates/redis-stack-server.yaml — inside spec.template.spec.containers (append)
{{- if .Values.metrics.enabled }}
      - name: metrics
        image: "{{ .Values.metrics.image }}:{{ .Values.metrics.tag }}"
        ports: [{ name: metrics, containerPort: {{ .Values.metrics.port }} }]
        env:
        - { name: REDIS_ADDR, value: "redis://localhost:{{ .Values.redis_stack_server.port }}" }
        - name: REDIS_PASSWORD
          valueFrom: { secretKeyRef: { name: "{{ .Values.name }}-credentials", key: REDIS_PASSWORD } }
        securityContext: { allowPrivilegeEscalation: false, runAsNonRoot: true, capabilities: { drop: [ALL] } }
        resources: { requests: { cpu: 10m, memory: 32Mi }, limits: { cpu: 200m, memory: 128Mi } }
{{- end }}
```

```yaml
# templates/networkpolicy.yaml — add a SECOND ingress rule (keep the existing one unchanged)
{{- if .Values.metrics.enabled }}
  - from:
    - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: {{ .Values.metrics.monitoringNamespace | quote }} } }
    ports:
    - { protocol: TCP, port: {{ .Values.metrics.port }} }
{{- end }}
```

```yaml
# templates/podmonitor.yaml (new)
{{- if .Values.metrics.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: "{{ .Values.name }}"
  labels: {{ toYaml .Values.metrics.podMonitorLabels | nindent 4 }}
spec:
  selector: { matchLabels: { app: "{{ .Values.name }}" } }
  podMetricsEndpoints: [{ port: metrics, interval: 30s }]
{{- end }}
```

The role passes `metrics.enabled: "{{ redis_stack_metrics_enabled }}"` in its existing Helm
`values:` block (`roles/redis_stack/tasks/install.yaml:60`).

**Redis KPIs** (📚 exporter names): `redis_up`, `redis_memory_used_bytes`,
`redis_evicted_keys_total`, `redis_connected_clients`,
`rate(redis_commands_duration_seconds_total[5m]) / rate(redis_commands_total[5m])` (mean command
latency by command). Alert when memory is > 85 % of the container limit, or on any evictions.

### 6.2 pgvector exporter + table growth (`charts/pgvector`)

Same sidecar pattern with the Postgres exporter (📚 `prometheuscommunity/postgres-exporter`,
port 9187). It connects as `agentuser` over localhost, using the role-created Secret:

```yaml
env:
- name: DATA_SOURCE_NAME
  value: "postgresql://$(PGUSER):$(PGPASSWORD)@localhost:5432/agentdb?sslmode=disable"
- name: PGUSER
  valueFrom: { secretKeyRef: { name: pgvector-credentials, key: username } }
- name: PGPASSWORD
  valueFrom: { secretKeyRef: { name: pgvector-credentials, key: password } }
```

A custom query for the agent tables (📚 the exporter's custom-queries file), mounted from a
ConfigMap:

```yaml
agent_tables:
  query: >
    SELECT relname AS table_name,
           pg_total_relation_size(relid) AS bytes,
           n_live_tup AS rows
    FROM pg_stat_user_tables WHERE relname LIKE 'agent\_%'
  metrics:
    - table_name: { usage: LABEL }
    - bytes:      { usage: GAUGE, description: "table + index size" }
    - rows:       { usage: GAUGE, description: "estimated live rows" }
```

This gives `agent_tables_bytes{table_name="agent_events"}`. Alert on growth, e.g.
`predict_linear(agent_tables_bytes[7d], 30*24*3600) > 0.8 * <pvc bytes>` (it closes risk D7:
unbounded `agent_events` / `agent_cache`).

**Vector search quality and latency** are application KPIs: measure p95 query time in the agent,
and run an **offline recall@k** job:

```python
# recall@k: compare HNSW results with exact (sequential-scan) results on a sample of queries
cur.execute("SET enable_indexscan = off")            # force exact search
exact = {q: ids(cur, q, k) for q in sample}
cur.execute("SET enable_indexscan = on; SET hnsw.ef_search = 40")
approx = {q: ids(cur, q, k) for q in sample}
recall = sum(len(set(exact[q]) & set(approx[q])) / k for q in sample) / len(sample)
```

### 6.3 Agent-outcome view (`charts/pgvector` + `roles/pgvector`)

The init SQL runs **only on first start** (`/docker-entrypoint-initdb.d`), so existing databases
wouldn't get a new view. Apply it **idempotently from the role** on every install:

```sql
-- charts/pgvector/sql/03-kpi-views.sql  (new; CREATE OR REPLACE = safe to re-run)
CREATE OR REPLACE VIEW agent_task_kpis AS
SELECT agent_id,
       date_trunc('day', created_at) AS day,
       count(*) FILTER (WHERE event_type = 'task_end')                                  AS tasks,
       avg((payload->>'success')::int)      FILTER (WHERE event_type = 'task_end')     AS success_rate,
       avg((payload->>'cost')::numeric)     FILTER (WHERE event_type = 'task_end')     AS cost_per_task,
       avg(duration_ms)                     FILTER (WHERE event_type = 'task_end')     AS avg_task_ms,
       count(*) FILTER (WHERE event_type = 'tool_call' AND (payload->>'exit_code')::int <> 0)::numeric
         / NULLIF(count(*) FILTER (WHERE event_type = 'tool_call'), 0)                  AS tool_error_rate
FROM agent_events
GROUP BY agent_id, day;
```

```yaml
# roles/pgvector/tasks/install.yaml  (append after "Create credentials secret")
- name: "pgvector | Apply KPI views (idempotent)"
  kubernetes.core.k8s_exec:
    namespace: "{{ pgvector_namespace }}"
    pod: "{{ _pgvector_pods.resources[0].metadata.name }}"
    command: >-
      psql -v ON_ERROR_STOP=1 -U {{ pgvector_username }} -d {{ pgvector_database }}
      -c "{{ lookup('ansible.builtin.file', role_path ~ '/../../charts/pgvector/sql/03-kpi-views.sql') | replace('\"', '\\\"') }}"
  changed_when: false
```

**Event contract to document** (so the view works). Agents write:

| `event_type` | `payload` keys | `duration_ms` |
|---|---|---|
| `task_start` | `task`, `input_ref` | — |
| `task_end` | `success` (0/1), `cost` (from LiteLLM usage), `steps` | Task wall time |
| `llm_call` | `model`, `tier`, `prompt_tokens`, `completion_tokens`, `cost` | Call latency |
| `tool_call` | `tool`, `exit_code`, `sandbox_pool` | Execution time |

Expose it to Grafana with a PostgreSQL data source (read-only role) or via the exporter's custom
queries.

---

## 7. Phase 4 — Lifecycle, security, CI performance gate

### 7.1 Lifecycle KPIs (this repo: preflight report)

Add timing to the report Play 2 already writes (`playbooks/preflight-check.yml:88`, "Pin
timestamps"): `started_at`, `finished_at`, `duration_s`, and counts by status. The installer layer
can add `install_duration_s` per component from its logs. Trend these per release in CI.

### 7.2 Security KPIs (this repo: OpenShell and router; via Loki)

```logql
# sandbox router rejections (TokenReview failures)
sum(count_over_time({namespace="agent-sandbox-system", app="sandbox-router"} |= " 401 " [5m]))

# OpenShell policy denials by engine (verify the supervisor writes these to pod logs; otherwise use `openshell logs`)
sum by (engine) (count_over_time({namespace="openshell-sandboxes"} |= "DENIED"
                 | regexp "engine:(?P<engine>[a-z0-9]+)" [5m]))
```

Alert on a sudden rise in 401s (misconfigured agent, or probing). Chart denials per policy to tune
policies.

### 7.3 CI performance gate (release pipeline, separate from the toolkit runtime)

Runs on a **self-hosted Xeon runner** against a test deployment; fixed model, prompts and
concurrency:

```yaml
# .github/workflows/perf-gate.yml — illustrative
name: perf-gate
on: { workflow_dispatch: {}, schedule: [{ cron: "15 2 * * 1" }] }
jobs:
  bench:
    runs-on: [self-hosted, xeon-perf]
    steps:
      - uses: actions/checkout@<pinned-sha>      # pin by SHA like the existing workflows
      - name: Benchmark through the gateway
        env: { BASE_URL: "${{ secrets.PERF_LITELLM_URL }}", API_KEY: "${{ secrets.PERF_LITELLM_KEY }}" }
        run: |
          # 📚 vLLM ships a serving benchmark (`vllm bench serve` in recent versions; flags vary)
          vllm bench serve --backend openai-chat --base-url "$BASE_URL" --endpoint /v1/chat/completions \
            --model qwen2-5-coder-14b --dataset-name random --random-input-len 512 --random-output-len 256 \
            --num-prompts 200 --max-concurrency 8 --save-result --result-filename result.json
      - name: Enforce thresholds
        run: |
          python3 - <<'PY'
          import json, sys
          r = json.load(open("result.json"))
          ttft_p95 = r.get("p95_ttft_ms") or r.get("p99_ttft_ms")   # key names depend on version
          tput = r["output_throughput"]
          ok = ttft_p95 is not None and ttft_p95 < 5000 and tput > 40   # placeholder thresholds per SKU
          print(f"ttft_p95={ttft_p95}ms output_throughput={tput} tok/s -> {'PASS' if ok else 'FAIL'}")
          sys.exit(0 if ok else 1)
          PY
```

Store `result.json` as an artefact per release to build the per-SKU trend that's missing today.

---

## 8. Dashboards

Ship each dashboard as a ConfigMap with the Grafana sidecar label (check 0.3), owned by the layer
of its component.

| Dashboard | Owner | Panels |
|---|---|---|
| **Inference** | Inference layer | TTFT p50/p95 · ITL p95 · output tokens/s · waiting vs running · KV-cache % · preemptions · memory headroom % per model pod |
| **Gateway & safety** | Inference layer | Requests/s by model · errors by code · p95 latency · spend and remaining budget per key · guardrail blocks by reason · guard p95 latency and up |
| **Router** | Inference layer | Tier mix · model share per tier · reward distribution · time per token per model |
| **Agent Sandbox** | **This repo** | Warm-pool ready/desired per pool · claims/min · claim latency p95 · exec duration p95 · non-zero exits · router 401s · sandbox OOMs |
| **Agent memory** | **This repo** | Redis memory, evictions, clients, command latency · Postgres connections and cache hit · agent table sizes and growth forecast |
| **Agent outcomes** | **This repo** (view) + agent | Tasks/day · success rate · cost per task · time per task · tool error rate, by agent |

```yaml
# charts/agent-sandbox/monitoring/dashboard-configmap.yaml.j2 — skeleton
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-sandbox-dashboard
  namespace: "{{ monitoring_namespace }}"
  labels: {{ grafana_dashboard_label | to_json }}
data:
  agent-sandbox.json: |
    {"title": "Agent Sandbox", "panels": [
      {"type": "timeseries", "title": "Warm pool ready / desired",
       "targets": [{"expr": "agent_sandbox_warmpool_ready_replicas"},
                   {"expr": "agent_sandbox_warmpool_desired_replicas"}]},
      {"type": "timeseries", "title": "Claim latency p95",
       "targets": [{"expr": "histogram_quantile(0.95, sum by (le, pool) (rate(agent_sandbox_claim_seconds_bucket[5m])))"}]}
    ]}
```

---

## 9. Testing the monitoring itself

Monitoring that isn't tested fails silently. Three layers of tests:

**1. Unit-test alert rules** with `promtool` (in CI, next to Checkov and Trivy):

```yaml
# charts/agent-sandbox/monitoring/tests/warmpool_test.yaml
rule_files: [ ../rendered-prometheusrule.yaml ]        # render the .j2 first, extract spec.groups
evaluation_interval: 1m
tests:
  - interval: 1m
    input_series:
      - series: 'agent_sandbox_warmpool_ready_replicas{name="python-pool"}'
        values: '5 5 2 2 2 2 2 2'
      - series: 'agent_sandbox_warmpool_desired_replicas{name="python-pool"}'
        values: '5 5 5 5 5 5 5 5'
    alert_rule_test:
      - eval_time: 7m
        alertname: SandboxWarmPoolDepleted
        exp_alerts: [{ exp_labels: { severity: warning, name: python-pool } }]
```

```bash
promtool test rules charts/agent-sandbox/monitoring/tests/warmpool_test.yaml
```

**2. Prove scrape targets are up** (add to each role's `validate.yaml`):

```yaml
- name: "agent_sandbox | validate | Metrics present in Prometheus"
  ansible.builtin.uri:
    url: "{{ prometheus_url }}/api/v1/query?query=count(agent_sandbox_warmpool_desired_replicas)"
    return_content: true
  register: _prom_q
  failed_when: (_prom_q.json.data.result | length) == 0
  when: agent_sandbox_metrics_enabled | bool
```

**3. Chaos checks** on a test cluster. Each must fire the expected alert:

| Action | Expected alert |
|---|---|
| `kubectl scale … qwen3guard --replicas=0` (or delete the guard pod) | `GuardUnavailable` within ~2 min; chat returns `[guard:unreachable]` blocks |
| Set `python-pool` replicas very high on a small node | `SandboxWarmPoolDepleted` |
| Lower a test model's memory limit below its footprint | `ModelOOMKilled` |
| Send a burst at concurrency far above the knee | `VllmSaturated` |

---

## 10. Delivery plan: pull requests, owners, effort

Effort sizes are rough (S ≈ ≤ 2 days, M ≈ ≤ 1 week, L ≈ > 1 week) and assume the observability
stack already exists.

| PR | Repo / layer | Contents | Size | Depends on |
|---|---|---|---|---|
| 1 | Platform | Mesh decision for Prometheus (§0); memory/OOM rules (§5.1) | S | — |
| 2 | Inference | vLLM PodMonitor + rules + Inference dashboard (§2) | S | 1 |
| 3 | Inference | Guardrail reason codes + Loki metric + `GuardUnavailable` (§3) | S–M | 1, 2 |
| 4 | **agent-toolkit** | Sandbox: KSM config + RBAC, rules, dashboard, `metrics.yaml`, validate threshold, docs example (§4) | M | 1 |
| 5 | Inference | LiteLLM Prometheus or Langfuse-derived gateway KPIs (§5.2) | S–M | 1 |
| 6 | Inference | Router metadata tags + metrics export (§5.3) | M | 1 |
| 7 | **agent-toolkit** | Redis + pgvector exporters, NetworkPolicy rule, PodMonitors, dashboard (§6.1–6.2) | M | 1 |
| 8 | **agent-toolkit** | KPI view + event contract docs + outcome dashboard (§6.3) | S | 7 |
| 9 | **agent-toolkit** | Preflight timings; security LogQL panels (§7.1–7.2) | S | 1 |
| 10 | CI | promtool tests in CI; perf-gate workflow on a Xeon runner (§7.3, §9) | M | 2 |

**Definition of done for every PR:**
- Off by default unless `observability_enabled`.
- Graceful skip when the CRDs are missing.
- Images pinned.
- No secrets in logs (`no_log`).
- promtool tests pass.
- `validate` proves the target is up.
- A runbook link in each alert.
- Docs updated: `improvement.md` status table and §7 of `02-design.md`.
