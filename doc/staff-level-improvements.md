# Five Big Improvements to the Agent Toolkit — Explained Simply, With Proof

> **Who this is for:** anyone, including a fresher engineer. Every idea is explained in plain words
> first, then backed by **proof from the repository**, then solved with **pseudocode** (Python or
> Java) you can explain on a whiteboard.
>
> **Why this document exists:** "add more metrics" is a fine improvement, but it's housekeeping. At a
> senior (Staff) level the question is: **what stops customers from running agents in production on
> Intel Xeon, and what would make Xeon the *better* choice?** These five improvements answer that.
>
> **How to read each section:**
>
> | Mark | Meaning |
> |---|---|
> | 🧩 **In plain words** | The problem, explained like you would to a friend |
> | 🔍 **Proof** | Exact lines from this repo (`file:line`), not opinions |
> | 💡 **Fix** | What to change, step by step |
> | 🧪 **Pseudocode** | Short, readable code showing the fix (not production code, not tested) |
> | ✅ **How we know it worked** | The number that should move |
> | ⚖️ **Trade-off** | What it costs, honestly |
> | 🎤 **Say it in the interview** | A short answer you can speak, plus likely follow-up questions |
>
> 📚 = general knowledge about other projects (vLLM, LiteLLM, Kubernetes, Intel hardware), to verify
> for your exact versions. ⚠️ = an assumption we must measure before building.

## Contents

- [The five ideas in one minute](#the-five-ideas-in-one-minute)
- [First, four clarifications](#first-four-clarifications)
- [Improvement 1 — Keep a conversation's memory warm (KV-cache-aware serving)](#improvement-1--keep-a-conversations-memory-warm-kv-cache-aware-serving)
- [Improvement 2 — Make the router chase "cheap AND correct", not just "fast"](#improvement-2--make-the-router-chase-cheap-and-correct-not-just-fast)
- [Improvement 3 — Know who is acting, and what they are allowed to do](#improvement-3--know-who-is-acting-and-what-they-are-allowed-to-do)
- [Improvement 4 — Build the missing "Actions & Tools" block](#improvement-4--build-the-missing-actions--tools-block)
- [Improvement 5 — Design for "day 2", and fix things upstream](#improvement-5--design-for-day-2-and-fix-things-upstream)
- [How to sequence the work](#how-to-sequence-the-work)
- [Interview cheat sheet](#interview-cheat-sheet)

---

## The five ideas in one minute

The toolkit's job: **make Xeon a great place to run AI agents, and get customers from a demo to
production quickly.** Measured against that job:

1. **Serving:** when an agent's conversation hops between models, the model loses its "short-term
   memory" (the KV cache) and has to re-read everything. That's the most expensive thing a CPU does.
   → *Keep conversations on one model and play to Xeon's big memory.*
2. **Routing:** the router picks models by **speed only**. It can happily choose fast but wrong
   answers. → *Pick by "cheapest answer that is correct".*
3. **Security:** the platform can't tell **which customer or user** an agent is acting for, and it
   has no rule about **which tools** an agent may use. → *One identity end to end, plus a permission
   check on every action.*
4. **Tools:** the README promises an "Actions & Tools" block, but the repo ships **nothing** for it.
   → *Build a safe tool gateway.*
5. **Running it for years:** install is fast, but upgrades, backups, high availability and patching
   upstream code are weak. → *Design for day 2; push fixes upstream.*

---

## First, four clarifications

These clear up ideas that are easy to get wrong.

### C1. Is prefix caching used today? **Yes, and it works.**

- **Prefix caching** means: if a new request starts with text the model has already processed (for
  example, the same long system prompt), the model reuses that work instead of redoing it.
- 🔍 It's switched on for the vLLM models: `docker/model-configs.yaml:70` (and 15 more lines) set
  `--enable-prefix-caching`. On Kubernetes the flags live in the inference layer, outside this repo
  (📚 newer vLLM versions enable it by default).
- Each model runs as **one** server today, so every request for that model reaches the same cache.
- **So the cache itself is fine.** The real problem is the router *sending one conversation to
  different models* (Improvement 1).

### C2. What is a "replica"? **A copy of the same model server. Not used in the repo yet.**

- A **replica** is a second (third, …) identical copy of the same model server, added to handle
  more traffic.
- 🔍 The docs talk about settings "per replica" (`docs/xeon-model-configuration.md:111`, `:130`),
  but no replica count or autoscaling is configured anywhere. Each model is one server
  (`docker/scripts/generate-docker-compose.sh:774` `main()` creates one container per model).
- **So replica-aware routing is a suggestion for later**, when a model needs more than one copy.

### C3. Why is the Kubernetes path bf16 only? **Probably on purpose.** The repo doesn't say; these are reasonable guesses

- 🔍 Kubernetes and Docker vLLM configs use `--dtype bfloat16` (`docker/model-configs.yaml:63`,
  `docs/guardrails.md:137`). Only the Docker OpenVINO path uses `weight_format: int4`
  (`docker/ovms-model-configs.yaml:73`).
- Likely reasons:
  1. **Accuracy.** bf16 is almost the original model. Agents need exact JSON for tool calls and
     correct code, and shrinking the model (int4/int8) can break those.
  2. **One tested setup.** One engine (vLLM), one number format, fewer combinations to test.
  3. **No conversion step.** The Docker docs warn that converting to OpenVINO can take 30+ minutes and
     a lot of memory, which works against "install in hours".
  4. **Xeon's AMX units run bf16 natively.**
  5. **The memory saving is smaller than people think.** For Qwen2.5-Coder-14B, weights are
     30.8 GiB but the KV cache is 160 GiB (`docs/xeon-model-configuration.md`). Shrinking the weights
     doesn't shrink the KV cache.
- **So the improvement isn't "switch to int4".** It's: *offer smaller-number versions per model, only
  after they pass an accuracy test* (Improvement 1, step 4).

### C4. What is Intel RDT? **A way to stop one program stealing another's memory speed.** Not in the repo; a suggestion

- 🔍 Today the toolkit pins each model to **its own CPU cores** (NRI balloons; see
  `docs/xeon-model-configuration.md`).
- But all cores on a chip still **share** two things: the big L3 **cache** and the **memory
  bandwidth** (how fast data moves between memory and the CPU).
- An LLM generating text is limited mainly by memory bandwidth. If a busy neighbour (say a sandbox
  crunching a huge file) hogs bandwidth, the LLM slows down even though "its" cores are free.
  - **Analogy:** each person has their own desk (cores), but everyone shares one corridor
    (bandwidth). If someone pushes trolleys up and down the corridor, everyone gets slower.
- **Intel RDT** (Resource Director Technology) is a Xeon hardware feature that can **measure** who
  uses the corridor, **reserve** part of the cache for someone, and **cap** how much bandwidth a
  group may use.
- 🔍 Sandboxes currently have **no node placement rule** (`charts/agent-sandbox/default-templates.yaml`
  has no `nodeSelector`; only the Kata template does, at `kata-templates.yaml:36`), so they can land
  on the same machines as the models.
- **The simple fix first:** put sandboxes on separate machines. Use RDT only when they *must* share.

---

## Improvement 1 — Keep a conversation's memory warm (KV-cache-aware serving)

### 🧩 In plain words

When a model reads a conversation, it builds a **KV cache**, a kind of short-term memory of
everything it has read. With prefix caching, the next turn of the same conversation can reuse it.

But the **Hybrid Router** chooses a model **separately for every message**. So one conversation can
go like this:

```
turn 1  "hi, list the files"           → classified SIMPLE  → llama-3-1-8b      (builds memory)
turn 2  "now refactor the parser…"     → classified COMPLEX → qwen3-coder-30b   (never saw turns 1–2: re-reads all)
turn 3  "thanks, rename it to x"       → classified SIMPLE  → llama-3-1-8b      (its memory is now out of date)
```

Every hop means the new model **re-reads the whole conversation**. Reading (called "prefill") is the
most expensive step on a CPU. So we pay again and again.

There's a hidden second problem: the router learns which model is "fastest". A model that happens to
receive later turns of a conversation it already holds looks faster than it really is. **The router
partly learns from noise it creates itself.**

### 🔍 Proof

| What | Where |
|---|---|
| The router classifies **each request** into a tier | `docs/hybrid-router.md:62`: `HybridRouter.classify() → SIMPLE / MEDIUM / COMPLEX / REASONING` |
| …then a learning algorithm picks a model **per request** | `docs/hybrid-router.md:63`: `HybridRouter.pick_model() → best real model for that tier (MAB bandit)` |
| It keeps exploring between models in a tier | `docs/hybrid-router.md:39`: "an online multi-armed bandit … learns which candidate model is…" |
| Nothing mentions a session or conversation ID | `docs/hybrid-router.md` (whole file): no session, stickiness or affinity concept |
| The reward is based on observed latency | `docs/hybrid-router.md:108–109`: `time_per_token = latency / tokens`; `reward = target_tpt / (target_tpt + time_per_token)` |
| Prefix caching is on (so warm memory matters) | `docker/model-configs.yaml:70` |
| The KV cache dominates memory | `docs/xeon-model-configuration.md`: Qwen2.5-Coder-14B is 30.8 GiB of weights vs 160 GiB of KV |
| Sandboxes can share machines with models | `charts/agent-sandbox/default-templates.yaml` has no `nodeSelector` |

### 💡 Fix, in four steps

1. **Measure first (⚠️ assumption check).** Find out how often conversations hop between models, and
   how much slower the first token is after a hop. If it's small, stop here.
2. **Sticky sessions.** Remember which model a conversation is using. Keep it there. Only move **up**
   to a bigger model if a message is clearly harder, never back down within a session.
3. **Sticky copies (later, when there are replicas).** If a model has several copies, always send the
   same conversation to the same copy, using a hash of the session ID.
4. **Use Xeon's strengths.**
   - Keep KV caches longer, in the large DRAM (📚 or CXL memory) that Xeon servers have and GPUs
     don't.
   - Offer smaller-number (int8/int4) model versions **only** after they pass a tool-call accuracy
     test.
   - Keep sandboxes on separate machines (RDT only if they must share).

### 🧪 Pseudocode

**Step 1: measure the hop penalty** (Python, over exported Langfuse traces):

```python
# Each trace: session_id, turn_no, model, ttft_seconds  (the agent must send session_id as metadata)
from collections import defaultdict
from statistics import median

by_session = defaultdict(list)
for t in load_traces():                                  # e.g. Langfuse export
    by_session[t.session_id].append(t)

stayed, switched = [], []
for turns in by_session.values():
    turns.sort(key=lambda t: t.turn_no)
    for prev, cur in zip(turns, turns[1:]):
        (stayed if cur.model == prev.model else switched).append(cur.ttft_seconds)

print("switch rate :", len(switched) / max(1, len(stayed) + len(switched)))
print("TTFT stayed :", median(stayed))
print("TTFT switched:", median(switched))   # if this is much larger → the problem is real
```

**Step 2: sticky sessions inside the Hybrid Router** (Python):

```python
TIER_ORDER = ["SIMPLE", "MEDIUM", "COMPLEX", "REASONING"]

def choose_model(request, session_store, router):
    session_id = request.metadata.get("session_id")      # sent by the agent
    tier = router.classify(request.messages)             # existing step (docs/hybrid-router.md:62)

    if session_id:
        pinned = session_store.get(session_id)           # e.g. Redis hash: {"tier": ..., "model": ...}
        if pinned:
            # stay on the pinned model unless this message needs a HIGHER tier
            if TIER_ORDER.index(tier) <= TIER_ORDER.index(pinned["tier"]):
                return pinned["model"]                   # warm KV cache, no re-reading

    model = router.pick_model(tier)                      # existing bandit step (docs/hybrid-router.md:63)
    if session_id:
        session_store.set(session_id, {"tier": tier, "model": model}, ttl_seconds=1800)
    return model
```

The reward fix belongs here too: only feed the bandit with **non-switched** turns, or record "was the
cache warm?" alongside the latency, so cache luck doesn't fool it.

**Step 3: sticky copies when a model has replicas** (Python; rendezvous hashing):

```python
import hashlib

def pick_replica(session_id, replicas):
    """Same session → same replica, and only 1/N of sessions move when a replica is added or removed."""
    def score(replica):
        return hashlib.sha256(f"{session_id}:{replica}".encode()).hexdigest()
    return max(replicas, key=score)

# pick_replica("sess-42", ["qwen-coder-a", "qwen-coder-b", "qwen-coder-c"])  → always the same one
```

**Step 4: keep sandboxes off the model machines** (Kubernetes YAML, the simple first fix):

```yaml
# label machines:  kubectl label node worker3 workload-class=sandbox
# charts/agent-sandbox/default-templates.yaml (add under podTemplate.spec)
nodeSelector:
  workload-class: sandbox
```

### ✅ How we know it worked

- Switch rate per conversation goes down.
- The prefix cache hit rate (📚 a vLLM metric) goes up.
- Time to first token for turns 2+ drops.
- **Agent turns per server per dollar** at the same latency goes up.

### ⚖️ Trade-off

Some easy messages run on a bigger model than strictly needed, which costs a little more. We accept
that if the saving from not re-reading is bigger. Step 1 tells us.

---

## Improvement 2 — Make the router chase "cheap AND correct", not just "fast"

### 🧩 In plain words

The router is like a taxi dispatcher who only asks "which driver arrives fastest?" and never "did the
passenger reach the right place?". It can learn to prefer the fastest model **even if its answers are
wrong**, and nothing would notice.

Three more weaknesses:
- The default reward setting makes all models look **almost equally good**, so it learns slowly.
- Its memory **resets on restart** and isn't shared between copies.
- It's attached to LiteLLM by **patching LiteLLM's internals**, which can break on any upgrade.

### 🔍 Proof

| What | Where |
|---|---|
| Reward = speed only | `docs/hybrid-router.md:108–109` (latency per token) |
| Quality is ignored by default | `docs/hybrid-router.md:170`: `quality_weight` default `0.0` ("0 = pure efficiency") |
| Default `target_tpt = 1.0` | `docs/hybrid-router.md:169` |
| Failures count as 0 reward, wrong answers don't | `docs/hybrid-router.md:112`: "Failures record a reward of 0" (an HTTP failure, not a wrong answer) |
| Router state is read from the running object | `docs/hybrid-router.md:324`: `HybridRouterProxy.router_state()` (in-process; ⚠️ confirm in code) |
| Attached by patching LiteLLM | `docs/hybrid-router.md:50`: "the custom module monkey-patches `litellm.router.Router`" |

**Worked numbers** showing why models look alike with `target_tpt = 1.0`:

| Model | Latency | Tokens | Time per token | Reward |
|---|---|---|---|---|
| A (fast) | 3 s | 150 | 0.02 s | 1 / (1 + 0.02) = **0.98** |
| B (slow) | 12 s | 60 | 0.20 s | 1 / (1 + 0.20) = **0.83** |

B is **10× slower per token**, but its reward is only 15 % lower. With `target_tpt = 0.05` the rewards
become 0.71 vs 0.20, which is a clear difference.

### 💡 Fix

1. **Reward success, not just speed:** reward = "was the task done correctly?" minus a cost/latency
   penalty, within a latency limit.
2. **Cascade:** try the small CPU model first, **check** the answer cheaply (valid JSON? tests pass?),
   and go to the big model only if the check fails.
3. **Shared memory:** keep the learning state in Redis, so restarts and copies share it.
4. **Test before switching on:** replay old traffic offline to see how a new policy would have done.
5. **Get off the patch:** contribute the router upstream to LiteLLM, or run it as its own small
   routing service.

### 🧪 Pseudocode

**Cascade with a validator** (Python):

```python
def answer_with_cascade(request, models_small_to_large, validate):
    """Try cheap models first; escalate only when the answer fails a cheap check."""
    for model in models_small_to_large:            # e.g. ["llama-3-1-8b", "qwen2-5-coder-14b", "qwen3-coder-30b"]
        reply = call_llm(model, request)
        ok, reason = validate(request, reply)       # cheap, deterministic checks
        record_outcome(model, success=ok, latency=reply.latency, cost=reply.cost)
        if ok:
            return reply
    return reply                                    # best effort from the largest model

def validate_tool_call(request, reply):
    """Example validator for agents: is the tool call well-formed and allowed?"""
    if not reply.tool_calls:
        return True, "plain answer"
    for call in reply.tool_calls:
        try:
            args = json.loads(call.function.arguments)
        except ValueError:
            return False, "tool arguments are not valid JSON"
        if not schema_for(call.function.name).is_valid(args):
            return False, "tool arguments don't match schema"
    return True, "ok"
```

**Outcome-based reward with shared state** (Python, Thompson sampling with Redis):

```python
import random

def reward(success, latency_s, cost, max_latency_s=8.0, cost_weight=0.2):
    if not success or latency_s > max_latency_s:
        return 0.0                                  # wrong or too slow = no reward
    return 1.0 - cost_weight * min(1.0, cost / BUDGET_PER_CALL)

def pick_model(tier, candidates, redis):
    """Thompson sampling: draw from each model's Beta(alpha, beta); pick the best draw."""
    best, best_draw = None, -1
    for m in candidates:
        a = float(redis.hget(f"bandit:{tier}:{m}", "alpha") or 1)
        b = float(redis.hget(f"bandit:{tier}:{m}", "beta") or 1)
        draw = random.betavariate(a, b)
        if draw > best_draw:
            best, best_draw = m, draw
    return best

def update(tier, model, r, redis):
    # atomic, shared by every router replica; survives restarts
    redis.hincrbyfloat(f"bandit:{tier}:{model}", "alpha", r)
    redis.hincrbyfloat(f"bandit:{tier}:{model}", "beta", 1.0 - r)
```

**Offline replay before going live** (Python):

```python
def replay(policy, logged_requests):
    """Estimate how a new routing policy would have done on yesterday's traffic."""
    cost = successes = 0
    for req in logged_requests:                     # from Langfuse: prompt, chosen model, outcome, cost
        model = policy(req)
        outcome = lookup_or_rerun(req, model)       # reuse logged result if same model, else re-run on a sample
        cost += outcome.cost
        successes += outcome.success
    return {"cost": cost, "success_rate": successes / len(logged_requests)}
```

### ✅ How we know it worked

The **share of traffic served on CPU at the same task success rate** goes up. That number is Intel's
whole argument.

### ⚖️ Trade-off

Validators add a little work per answer, and escalations add latency for those requests. We need to
track escalation rate and keep validators much cheaper than one big-model call.

---

## Improvement 3 — Know who is acting, and what they are allowed to do

### 🧩 In plain words

Agents don't just talk; they **do things**: run code, call APIs, write to databases. A company will
ask: *"Which user is this agent acting for? Is it allowed to do this? Can we prove what happened?"*

Today the platform mostly **can't answer those questions**:
- **Anyone in the cluster** with any service token can create sandboxes.
- **All** OpenShell sandboxes share **one** AI key.
- In Docker, every Redis user can read every other service's data.
- Agent memory separates users with only a text column; the **database** doesn't enforce it.
- The safety check reads the **user's** message, not text that comes back from tools (a web page can
  hide "ignore your instructions…").
- There is **no rule** about which tools an agent may call.

### 🔍 Proof

| What | Where |
|---|---|
| Any ServiceAccount token is accepted | `docs/agent-sandbox.md:456`: "Any ServiceAccount token in the cluster is accepted" |
| Router only checks *who you are*, not *what you may do* | `roles/agent_sandbox/tasks/install.yaml:82`: `--authz-mode=tokenreview`, `--authz-tokenreview-require-token=true` |
| One shared key for all OpenShell sandboxes | `roles/openshell/defaults/main.yaml:65`: `openshell_genai_key_alias: "openshell-sandboxes"`, `:67` budget 50 |
| Docker Redis users can read all keys | `docker/deploy.sh:608–609`: `user litellm on … ~* &* +@all` (`~*` = every key) |
| Memory separated by a plain column | `charts/pgvector/templates/configmap.yaml:29`: `user_id TEXT NOT NULL DEFAULT 'default'`; no row-level security anywhere |
| Safety check only before the call, on the request | `docs/guardrails.md:27` (`pre_call`); output and other checks are roadmap (`docs/guardrails.md:497`) |
| No tool permission rules | No policy or authorisation code anywhere in the repo for tool calls |

### 💡 Fix

1. **One identity, carried everywhere:** user → agent → AI key → sandbox → database row (Keycloak/OIDC
   is already an option in the repo).
2. **Ask "may you?", not just "who are you?"** at the sandbox router (Kubernetes
   SubjectAccessReview, or an allow-list of namespaces).
3. **Per-customer keys, budgets and sandbox pools.**
4. **Make the database enforce separation** (PostgreSQL row-level security).
5. **A permission check before every tool call,** with human approval for dangerous actions and a log
   that can't be edited.
6. **Screen what comes back from tools**, not only what the user typed.

### 🧪 Pseudocode

**Sandbox router: check permission, not just identity** (Python with the Kubernetes client):

```python
from kubernetes import client

def can_use_sandbox(token: str, pool: str) -> bool:
    authn = client.AuthenticationV1Api()
    authz = client.AuthorizationV1Api()

    # 1) who are you?  (what the router does today)
    review = authn.create_token_review(client.V1TokenReview(spec=client.V1TokenReviewSpec(token=token)))
    if not review.status.authenticated:
        return False
    user = review.status.user

    # 2) may you claim a sandbox from THIS pool?  (new)
    sar = client.V1SubjectAccessReview(spec=client.V1SubjectAccessReviewSpec(
        user=user.username, groups=user.groups,
        resource_attributes=client.V1ResourceAttributes(
            group="extensions.agents.x-k8s.io", resource="sandboxclaims",
            verb="create", namespace="agent-sandbox-system", name=pool)))
    return authz.create_subject_access_review(sar).status.allowed
```

**One AI key per tenant** (Python; the same API the OpenShell role already calls at
`roles/openshell/tasks/install.yaml:247`):

```python
def mint_tenant_key(tenant, models, budget):
    return post("/key/generate", {
        "key_alias": f"tenant-{tenant}",           # instead of one shared "openshell-sandboxes" key
        "models": models,                           # only the models this tenant may use
        "max_budget": budget,                       # its own spending limit
        "metadata": {"tenant": tenant},
    })["key"]
```

**Database-enforced separation** (PostgreSQL row-level security):

```sql
ALTER TABLE agent_memory ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'default';
ALTER TABLE agent_memory ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON agent_memory
  USING (tenant_id = current_setting('app.tenant_id'));        -- rows of other tenants are invisible

-- the agent sets its tenant once per connection:
SET app.tenant_id = 'acme';
SELECT content FROM agent_memory ORDER BY embedding <=> $1 LIMIT 5;   -- only acme's rows come back
```

**Permission check before every tool call** (Java):

```java
public final class ToolPolicyGuard {

    public enum Decision { ALLOW, DENY, NEEDS_HUMAN_APPROVAL }

    private final PolicyStore policies;     // e.g. backed by OPA/Cedar or a simple YAML file
    private final AuditLog audit;           // append-only (e.g. agent_events, no UPDATE/DELETE grants)

    public Decision check(Identity who, ToolCall call) {
        Policy p = policies.forTenant(who.tenantId());

        if (!p.allowedTools().contains(call.toolName())) {
            return record(who, call, Decision.DENY, "tool not allowed for tenant");
        }
        if (p.destructiveTools().contains(call.toolName())) {          // e.g. "delete_table", "send_payment"
            return record(who, call, Decision.NEEDS_HUMAN_APPROVAL, "destructive action");
        }
        if (call.touchesDataOf() != null && !call.touchesDataOf().equals(who.tenantId())) {
            return record(who, call, Decision.DENY, "cross-tenant access");
        }
        return record(who, call, Decision.ALLOW, "ok");
    }

    private Decision record(Identity who, ToolCall call, Decision d, String reason) {
        audit.append(who.userId(), who.agentId(), call.toolName(), d.name(), reason);
        return d;
    }
}
```

**Screen what tools return** (Python):

```python
def safe_tool_result(raw_text, guard):
    verdict = guard.check(raw_text)                 # reuse the existing guard model (Qwen3Guard)
    if verdict == "Unsafe" or looks_like_instructions(raw_text):
        return "[tool output withheld: possible prompt injection]"
    # mark it as DATA so the model treats it as content, not as commands
    return f"<untrusted_tool_output>\n{raw_text}\n</untrusted_tool_output>"
```

### ✅ How we know it worked

- The platform passes a **customer security review without custom work**.
- Zero cross-tenant reads in tests.
- Every tool call has an audit entry.

### ⚖️ Trade-off

More setup (identity, policies) and a small delay per tool call. Most of it reuses things already in
the stack: Keycloak, Postgres, the guard model.

---

## Improvement 4 — Build the missing "Actions & Tools" block

### 🧩 In plain words

The README says the toolkit has seven building blocks. One of them, **Actions & Tools** (letting
agents use APIs, databases and business systems safely), **isn't actually in the repo.** So every
customer has to build it themselves, which is the very work the toolkit promises to save.

### 🔍 Proof

| What | Where |
|---|---|
| The block is advertised | `README.md:129`: `### Actions & Tools`; `README.md:132`: "Default provider: Intel MCP (Model Context Protocol) · ETL / Ingestion Services" |
| Use cases aren't included | `README.md:190`: "Example Business Use Cases (Not pre-bundled)" |
| Nothing in the code | A search for "mcp" outside the docs finds only `README.md`: no role, chart, template or connector |

### 💡 Fix

A **tool gateway**: one front door every agent tool call goes through. It:
1. **Lists** the available tools (a catalogue).
2. **Checks permission** (Improvement 3).
3. **Adds the secret credential** itself, so the agent never sees passwords (the same idea OpenShell
   already uses with placeholder keys).
4. **Limits** how often and how much (rate limits, budgets).
5. **Logs** every call.
6. Ships 2–3 **ready connectors**: SQL, Git, ticketing. These match the README's own use cases.

### 🧪 Pseudocode

**The gateway's request flow** (Java):

```java
public final class ToolGateway {

    private final ToolRegistry registry;        // name → connector + JSON schema
    private final ToolPolicyGuard guard;        // from Improvement 3
    private final SecretVault vault;            // real credentials live here, never in the agent
    private final RateLimiter limiter;
    private final AuditLog audit;

    public ToolResult call(Identity who, ToolCall call) {
        Tool tool = registry.find(call.toolName())
                .orElseThrow(() -> new NotFound("unknown tool " + call.toolName()));

        tool.schema().validateOrThrow(call.arguments());                 // 1. well-formed?

        switch (guard.check(who, call)) {                                 // 2. allowed?
            case DENY:                 return ToolResult.denied("not permitted");
            case NEEDS_HUMAN_APPROVAL: return ToolResult.pending(approvals.request(who, call));
            default: break;
        }

        if (!limiter.tryAcquire(who.tenantId(), tool.name())) {          // 3. within limits?
            return ToolResult.denied("rate limit");
        }

        Credentials creds = vault.forTool(who.tenantId(), tool.name());   // 4. inject secret here
        long start = System.nanoTime();
        ToolResult result = tool.connector().invoke(call.arguments(), creds);

        audit.append(who, call, result.status(), (System.nanoTime() - start) / 1_000_000);  // 5. log
        return result.withoutSecrets();
    }
}
```

**A tool definition an agent sees** (what the catalogue publishes, MCP-style):

```json
{
  "name": "sql_query_readonly",
  "description": "Run a read-only SQL query on the sales warehouse",
  "input_schema": {
    "type": "object",
    "properties": { "sql": { "type": "string", "maxLength": 4000 } },
    "required": ["sql"]
  }
}
```

### ✅ How we know it worked

- Time for a customer to connect their first real tool drops (target: under a day).
- The share of agent actions going through the gateway rises.

### ⚖️ Trade-off

It's real product work. If the team is small, adopt an existing open MCP gateway **behind the same
contract** (the toolkit's Provider Pattern) instead of building everything.

---

## Improvement 5 — Design for "day 2", and fix things upstream

### 🧩 In plain words

"Day 0" is installing. "Day 2" is **living with it for years**: upgrading, backing up, recovering
from failures, keeping up with new versions. The toolkit is excellent at day 0 ("hours, not
months") but weak at day 2. And every local workaround it carries is code Intel must keep fixing
forever, so it's better to fix the original (upstream) projects.

### 🔍 Proof

| What | Where |
|---|---|
| Database tables are created **only on first start**, so there's no way to change them later | `charts/pgvector/templates/statefulset.yaml:62`: init scripts mounted at `/docker-entrypoint-initdb.d` (runs once) |
| Redis and pgvector are **single copies** | `charts/pgvector/templates/statefulset.yaml:8` `replicas: 1`; `charts/redis-stack/charts/redis-stack-server/values.yaml:6` `replicas: 1` |
| Teardown **deletes the data** | `roles/redis_stack/tasks/teardown.yaml:16–20` removes the namespace (and its disk); same in `roles/pgvector/tasks/teardown.yaml:29` |
| The safety guard is fail-closed and single, so guard down means **all chat down** | `docs/guardrails.md` (fail-closed) and `:163` (Recreate strategy, one copy) |
| Upstream files are fixed by **find-and-replace** | `roles/agent_sandbox/tasks/install.yaml:78–79`: `map('replace', '…:latest', …)`, `map('replace', '- --cache-enabled=true', …)` |
| The router depends on LiteLLM's insides | `docs/hybrid-router.md:50` (monkey-patch) |
| No backup or restore anywhere | No backup task, CronJob or doc in the repo |

### 💡 Fix

1. **Versioned database migrations**, run on every install (like Flyway/Liquibase/Alembic).
2. **Backups and restore** for Postgres and Redis, tested regularly.
3. **Two or more copies** of the safety guard (it blocks everything when down), plus
   high-availability options for the memory stores.
4. **Teardown keeps data unless asked:** a `retain_data` flag.
5. **Declarative patches instead of find-and-replace** (Kustomize), and a **version compatibility
   matrix** tested in CI.
6. **Upstream-first:** contribute fixes to the original projects (agent-sandbox, LiteLLM, vLLM). Every
   Xeon user benefits, and Intel stops carrying the patches.

### 🧪 Pseudocode

**A tiny migration runner** (Python; what a role would run on every install):

```python
MIGRATIONS = [
    (1, "001_agent_tables.sql"),       # today's 02-create-agent-tables.sql
    (2, "002_add_tenant_id.sql"),      # Improvement 3
    (3, "003_kpi_views.sql"),
]

def migrate(db):
    db.execute("CREATE TABLE IF NOT EXISTS schema_version (version INT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT NOW())")
    done = {row[0] for row in db.query("SELECT version FROM schema_version")}
    for version, file in MIGRATIONS:
        if version in done:
            continue                                 # safe to run on every install (idempotent)
        with db.transaction():
            db.execute(read(file))
            db.execute("INSERT INTO schema_version (version) VALUES (%s)", [version])
```

**Keep data on teardown unless asked** (Ansible):

```yaml
# roles/redis_stack/tasks/teardown.yaml
- name: "redis_stack | teardown | Remove namespace (deletes data!)"
  kubernetes.core.k8s:
    state: absent
    kind: Namespace
    name: "{{ redis_stack_namespace }}"
  when: not (retain_data | default(true) | bool)      # default: keep the data
```

**A redundant guard** (Helm values sketch for the inference layer):

```yaml
replicaCount: 2                          # two copies on different machines
podDisruptionBudget: { minAvailable: 1 } # never take both down for maintenance
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector: { matchLabels: { app: qwen3guard } }
        topologyKey: kubernetes.io/hostname
```

**Declarative patch instead of find-and-replace** (Kustomize):

```yaml
# kustomization.yaml — fails loudly if upstream changes, instead of silently not matching
resources: [ https://raw.githubusercontent.com/kubernetes-sigs/agent-sandbox/v1.0.10/sandbox-router/deploy/deployment.yaml ]
images:
  - { name: registry.k8s.io/agent-sandbox/sandbox-router-go, newTag: v1.0.10 }
patches:
  - target: { kind: Deployment, name: sandbox-router }
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/args/-
        value: --authz-mode=tokenreview
      - op: add
        path: /spec/template/spec/containers/0/args/-
        value: --authz-tokenreview-require-token=true
```

### ✅ How we know it worked

- Upgrades between releases succeed with no data loss.
- A restore drill passes every quarter.
- The guard keeps serving through a node failure.
- The number of local patches goes **down** over time.

### ⚖️ Trade-off

More engineering on things customers don't see in a demo. But it's what they need to run the product
for years, and upstreaming reduces Intel's long-term cost.

---

## How to sequence the work

| Order | Improvement | Why this order |
|---|---|---|
| 1 | **2 (router objective)** + Improvement 1, step 1 (measure hops) | Cheapest, and it proves or disproves the main idea with numbers |
| 2 | **3 (identity and permissions)** | It's the gate between "demo" and "production" for companies |
| 3 | **1 (warm KV cache)** | The biggest CPU performance win for agents, once measured |
| 4 | **4 (tool gateway)** and **5 (day 2)**, in parallel | Large but well understood; upstream contributions run throughout |

**Working across teams:** these touch the inference team, platform team, toolkit team and open-source
projects. Run each as a short design document (RFC). Agree the shared interfaces first (identity
claims, the session ID, the metrics), then build.

---

## Interview cheat sheet

### Opening (30 seconds)

> "The toolkit's job is to make Xeon a great place to run agents and get customers from demo to
> production. I looked for what blocks that, using the code as evidence. I found five things:
> conversations hop between models and lose their cached memory; the router rewards speed, not
> correct answers; there's no identity or permission model for agents that take actions; the
> advertised Actions & Tools block is empty; and day-2 operations like upgrades, backups and high
> availability are thin. For each I have proof in the repo, a fix, and the number that would show
> it worked."

### One line per improvement

| # | One line you can say |
|---|---|
| 1 | "The router decides per message, so a conversation can hop between models and re-read its whole history each time, which is the most expensive CPU step. Make sessions sticky, measure first." |
| 2 | "The reward is speed only, and with the default setting a 10× slower model scores only 15 % lower. Reward correct answers, cascade small to large with a cheap check, share state in Redis." |
| 3 | "Any service token can create sandboxes, one key serves every sandbox, and the database doesn't enforce tenant separation. Carry one identity end to end and check permission on every tool call." |
| 4 | "The README promises an Actions & Tools block, but the only 'MCP' in the repo is in the README. Build a tool gateway: catalogue, permissions, secret injection, limits, audit." |
| 5 | "Schema runs once, teardown deletes data, and the fail-closed guard is a single copy. Add migrations, backups, a redundant guard, Kustomize patches and upstream fixes." |

### Likely follow-up questions

| Question | Simple answer |
|---|---|
| *Is prefix caching broken?* | No, it's on and works with one server per model. The issue is the router sending one conversation to different models |
| *What's a replica, and do you have them today?* | A copy of the same model server for more traffic. Not configured today; sticky routing across copies is for when they're added |
| *Why not just switch to int4 for speed?* | Accuracy for tool calls and code, one tested setup, and no long conversion. The KV cache dominates memory anyway, so offer int4/int8 per model only after an accuracy test |
| *What is RDT, in one sentence?* | A Xeon feature that stops one program hogging the shared cache and memory bandwidth that the LLM needs. But first just keep sandboxes on separate machines |
| *How do you know improvement 1 is worth it?* | I don't yet. Step 1 measures how often conversations switch and how much slower those turns are. If it's small, we stop |
| *Where does "correct" come from for the router?* | Cheap checks: valid JSON for tool calls, tests passing for code, user accepting the answer. Agents log outcomes, the router learns from them |
| *What's the riskiest assumption overall?* | That CPUs can serve most agent traffic at good quality. Improvement 2 measures exactly that. If it's false, the strategy becomes "Xeon for the control plane, GPUs for heavy reasoning" |
| *Which would you cut with half the team?* | Building the tool gateway ourselves: adopt an open one behind the same contract, and keep people on 1–3, which are specific to Intel's goals |
| *How do you get other teams to agree?* | Show the data (traces of hopping and cost), prove it in code we own, then write the design doc with the owning team as co-author |

---

*Related documents: [`improvement.md`](improvement.md) (measurement and KPIs),
[`improvement-implementation.md`](improvement-implementation.md) (how to build the metrics),
[`03-interview-prep.md`](03-interview-prep.md) (full interview guide),
[`04-code-walkthrough.md`](04-code-walkthrough.md) (code, file by file).*
