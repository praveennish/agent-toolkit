"""Generates the three diagrams of the Agent Toolkit study docs as SVG.

    python3 build_diagrams.py      # writes architecture.svg, component.svg, sequence.svg here
    node render.js                 # turns them into ../*.png

Every name, port and setting drawn here comes from the agent-toolkit repository
(README.md, docs/, roles/, charts/, docker/). Keep it that way when editing.
"""
import os

from svglib import SVG

HERE = os.path.dirname(os.path.abspath(__file__))


def title(s, text, sub):
    s.text(40, 42, text, size=24, weight=800, fill="#0F172A")
    s.text(40, 66, sub, size=13.5, fill="#475569")


# =============================================================================
# 1. ARCHITECTURE — layered view
# =============================================================================
def architecture():
    s = SVG(1720, 1250)
    title(s, "Intel® Agent Toolkit — Architecture (layered view)",
          "Seven provider blocks on Kubernetes, on Intel® Xeon®. Orange = what this repository installs. "
          "Other colours = layers installed by Toolkit Manager (enterprise-ai-solutions).")

    L, MW = 40, 1240           # main column left, width
    LANE = 1262                # right lane for "direct" calls

    # Row A — clients
    s.box(L, 92, MW, 84, "Your agent application (the 'brain' you write)", [
        "Frameworks: LangGraph · CrewAI · Microsoft Agent Framework · OpenClaw · any OpenAI-compatible client",
        "It sees ONE model URL:  https://litellm.<base_domain_name>/v1   (OpenAI API, Bearer <virtual key>)",
    ], theme="client")

    # Row B — edge
    s.box(L, 206, 1200, 62, "Platform edge — Envoy Gateway · TLS (cert-manager) · LoadBalancer IP (MetalLB)", [
        "Host names: litellm.<domain>  ·  langfuse.<domain>  ·  vllm-sr.<domain>  ·  ray.<domain>",
    ], theme="edge", title_size=14)
    s.arrow([(L + 600, 176), (L + 600, 206)], colour="blue")

    # Row C — Block 1 gateway
    s.box(L, 298, 1200, 160, "Block 1 · API Gateway & Policy — LiteLLM 'GenAI Gateway' (:4000)", [],
          theme="gateway", badge="inference layer")
    subw, gap, sx = 285, 13, L + 12
    subs = [
        ("Auth, keys, budgets", ["Master key (admin only)", "Virtual key per agent/sandbox", "Budgets · rate limits · spend"]),
        ("content_safety guardrail", ["Runs on pre_call (before LLM)", "Asks guard model: Safe/Unsafe", "Fail-closed → HTTP 500 block"]),
        ("Hybrid Router (virtual model)", ["model = 'hybrid-router'", "1) classify complexity tier", "2) bandit picks cheapest-fast model"]),
        ("Telemetry callback", ["Trace every call to Langfuse", "Tokens · cost · latency", "Which model answered"]),
    ]
    for i, (t, ln) in enumerate(subs):
        s.box(sx + i * (subw + gap), 334, subw, 110, t, ln, theme="white", title_size=13.5, line_size=12)
    s.arrow([(L + 600, 268), (L + 600, 298)], colour="blue")

    # Direct lane: agents -> agent toolkit backends
    s.arrow([(1250, 176), (LANE, 176), (LANE, 490)], colour="orange")
    s.label(1268, 250, "direct,", colour="#EA580C", size=11)
    s.label(1268, 265, "in-cluster", colour="#EA580C", size=11)
    s.label(1268, 280, "(memory,", colour="#EA580C", size=11)
    s.label(1268, 295, "sandbox,", colour="#EA580C", size=11)
    s.label(1268, 310, "Ray)", colour="#EA580C", size=11)

    # Row D left — inference
    s.box(L, 490, 560, 300, "Block 3 · Inference & Routing", [], theme="infer", badge="inference layer")
    s.box(L + 12, 526, 536, 100, "KServe + vLLM on Xeon (namespace llm-inference)", [
        "Chat models: qwen2-5-coder-14b (default) · qwen3-coder-30b · llama-3-1-8b",
        "gemma-4-26b · qwen3-30b-a3b · '-specdec' = speculative decoding variants",
        "Reached through the AI gateway: /llm-inference/<model>/v1",
    ], theme="white", title_size=13.5, line_size=12)
    s.box(L + 12, 636, 262, 66, "Guard model", ["Qwen3Guard-Gen-0.6B (CPU)"], theme="white", title_size=13.5, line_size=12)
    s.box(L + 286, 636, 262, 66, "Embedding / rerank", ["bge-base-en · bge-reranker"], theme="white", title_size=13.5, line_size=12)
    s.box(L + 12, 712, 262, 66, "vLLM Semantic Router", ["optional · model 'vllm-sr/auto'"], theme="white",
          title_size=13.5, line_size=12, dash="5 4")
    s.box(L + 286, 712, 262, 66, "Cloud / GPU LLMs", ["optional · OpenAI · Claude · Gemini"], theme="white",
          title_size=13.5, line_size=12, dash="5 4")
    s.arrow([(L + 300, 458), (L + 300, 490)], colour="green", label="routed model call", label_at=(L + 310, 478))

    # Row D right — THIS REPO
    RX, RW = 620, 660
    s.box(RX, 490, RW, 300, "Agent Toolkit layer — THIS REPOSITORY", [], theme="repo", badge="agent-toolkit layer")
    cw, ch = 206, 118
    cells = [
        ("Block 2 · Memory", ["Redis Stack + RediSearch", "  short-term / session state", "PostgreSQL 16 + pgvector", "  long-term memory · RAG"], None),
        ("Block 5 · Sandbox", ["Agent Sandbox controller", "  + router + warm pools", "Kata microVMs (opt-in)", "OpenShell policy (opt-in)"], None),
        ("Parallel compute", ["KubeRay operator", "Ray head + 1–4 workers", "parallel tool calls", "(off by default)"], "5 4"),
        ("Identity", ["Keycloak realm", "'agent-toolkit'", "(only in JWT mode)"], "5 4"),
        ("Block 4 · Actions & Tools", ["MCP servers / your tools", "plug in beside the stack", "(templates are not in", " this repository)"], "5 4"),
        ("Checks", ["Preflight: node readiness", "Validate: per component", "Teardown: per component"], None),
    ]
    for i, (t, ln, dash) in enumerate(cells):
        cx = RX + 12 + (i % 3) * (cw + 11)
        cy = 526 + (i // 3) * (ch + 12)
        s.box(cx, cy, cw, ch, t, ln, theme="white", title_size=13.5, line_size=12, dash=dash, line_gap=19)

    # Row E — observability
    s.box(L, 820, MW, 70, "Block 6 · Observability & Telemetry", [
        "Langfuse (LLM traces: prompt, tokens, cost, model chosen)  ·  Prometheus (metrics)  ·  Grafana (dashboards)  ·  "
        "Loki (logs)  ·  Tempo + OTel Collector (traces)",
    ], theme="obs", badge="platform layer")

    # Row F — platform
    s.box(L, 920, MW, 104, "Platform — Kubernetes (Kubespray) for production · Docker Compose for development", [
        "Helm · Istio ambient mesh (mutual TLS between namespaces) · NetworkPolicy (Calico) · cert-manager · MetalLB · Envoy Gateway",
        "NRI balloons (pin each model to the cores of one NUMA node) · NFD (CPU feature labels) · Storage: local-path / NFS / Ceph",
        "Kata Containers runtime classes kata-fc / kata-qemu (opt-in, needs /dev/kvm)",
    ], theme="platform", badge="infrastructure + platform layers")

    # Row G — compute
    s.box(L, 1054, MW, 78, "Compute — Intel® Xeon®", [
        "Runs the agent control plane (gateway, memory, sandboxes, routing) AND CPU LLM inference (bf16, AMX, NUMA-aware)",
        "GPUs or cloud LLMs can be added behind the same gateway for the heaviest reasoning work",
    ], theme="compute")

    # Right column — Block 7 deployment
    DX, DW = 1330, 350
    s.box(DX, 92, DW, 1040, "Block 7 · Deployment & lifecycle", [], theme="deploy")
    steps = [
        ("1  Toolkit Manager", ["es_auto_installer.sh", "configure → init agent-toolkit", "→ install agent-toolkit"]),
        ("2  Your settings", ["env/<name>/global_config.yaml", "config.agent-toolkit.yaml", "config.inference.yaml · models.yaml"]),
        ("3  Preflight (report only)", ["NTP, swap, disk, DNS, gateway", "CPU governor, THP, NUMA", "HF token"]),
        ("4  Component registry", ["components.yaml: layer", "agent-toolkit depends_on", "[platform, inference]"]),
        ("5  Ansible roles", ["roles/<component>/tasks/", "install · validate · teardown", "idempotent, re-runnable"]),
        ("6  Helm charts + manifests", ["charts/redis-stack, pgvector,", "kuberay, openshell values,", "upstream agent-sandbox YAML"]),
        ("7  Validate", ["./es_auto_installer.sh", "validate agent-toolkit", "healthy = failed=0"]),
    ]
    sy = 132
    for i, (t, ln) in enumerate(steps):
        s.box(DX + 16, sy, DW - 32, 112, t, ln, theme="white", title_size=13.5, line_size=12, line_gap=20)
        if i < len(steps) - 1:
            s.arrow([(DX + DW / 2, sy + 112), (DX + DW / 2, sy + 136)], colour="#CA8A04")
        sy += 136

    # Legend
    ly = 1170
    s.text(L, ly, "Legend", size=13, weight=700)
    items = [("repo", "installed by this repository"), ("gateway", "inference layer"),
             ("obs", "observability"), ("platform", "platform / infrastructure"), ("deploy", "deployment flow")]
    lx = L + 70
    for th, txt in items:
        from svglib import THEMES
        f, st, _ = THEMES[th]
        s.rect(lx, ly - 13, 26, 16, f, st, rx=4)
        s.text(lx + 34, ly, txt, size=12.5)
        lx += 34 + len(txt) * 7.2 + 30
    s.rect(lx, ly - 13, 26, 16, "#FFFFFF", "#94A3B8", rx=4, dash="5 4")
    s.text(lx + 34, ly, "dashed border = optional / off by default", size=12.5)
    s.text(L, ly + 30, "Source: agent-toolkit repository (README.md, docs/, components.yaml, config.yaml, roles/, charts/). "
           "Drawn for study; not an official Intel diagram.", size=11.5, fill="#64748B", italic=True)
    s.save(os.path.join(HERE, "architecture.svg"))


# =============================================================================
# 2. COMPONENT — runtime components, namespaces, ports, interfaces
# =============================================================================
def component():
    s = SVG(1800, 1290)
    title(s, "Intel® Agent Toolkit — Component diagram (runtime view)",
          "Kubernetes namespaces (dashed), the components inside them, their ports, and who calls whom. "
          "Orange = installed by this repository.")

    # --- Deployment strip -----------------------------------------------------
    s.container(40, 88, 1720, 118, "Deployment-time components (run from the control machine)", theme="deploy")
    chain = [
        ("es_auto_installer.sh", ["Toolkit Manager CLI", "install · validate · teardown"]),
        ("env/<name>/*.yaml", ["your switches + sizing", "e.g. openshell_enabled"]),
        ("components.yaml", ["component registry", "depends_on + enabled"]),
        ("roles/<component>", ["Ansible: install.yaml", "validate · teardown"]),
        ("charts/ + upstream YAML", ["Helm charts (Redis, pgvector,", "KubeRay) · sandbox manifests"]),
        ("Kubernetes API server", ["applies the resources", "below (desired state)"]),
    ]
    bx, bw = 56, 262
    for i, (t, ln) in enumerate(chain):
        x = bx + i * (bw + 22)
        s.box(x, 112, bw, 82, t, ln, theme="white" if i < 5 else "platform", title_size=13.5, line_size=12)
        if i < len(chain) - 1:
            s.arrow([(x + bw, 153), (x + bw + 22, 153)], colour="#CA8A04")

    # --- Agent namespace ---------------------------------------------------------
    s.container(40, 262, 270, 250, "ns: <your-agent>", theme="client")
    s.box(54, 290, 242, 208, "Agent application pod", [
        "Your code + a framework",
        "Client libraries it uses:",
        " • OpenAI SDK → LiteLLM",
        " • k8s-agent-sandbox SDK",
        " • redis / psycopg clients",
        " • ray client (optional)",
        "Holds: virtual key,",
        "ServiceAccount token",
    ], theme="client", title_size=13.5, line_size=12, line_gap=19)

    # --- LiteLLM namespace -------------------------------------------------------
    s.container(360, 262, 430, 300, "ns: litellm   (inference layer)", theme="gateway")
    s.box(374, 290, 402, 258, "LiteLLM proxy — svc litellm:4000", [
        "POST /v1/chat/completions · GET /v1/models",
        "Admin: /key/generate · /model/new · /guardrails",
        "Secret litellm-master-key (master key)",
    ], theme="gateway", title_size=13.5, line_size=12)
    s.box(388, 382, 180, 74, "content_safety", ["custom_code guardrail", "mode: pre_call"], theme="white",
          title_size=12.5, line_size=11.5)
    s.box(582, 382, 180, 74, "Hybrid Router", ["callback, ConfigMap", "litellm-router-code"], theme="white",
          title_size=12.5, line_size=11.5)
    s.box(388, 466, 374, 70, "Virtual key 'openshell-sandboxes'", ["minted by the openshell role · budget 50",
                                                                   "(+ one key per agent you create)"],
          theme="white", title_size=12.5, line_size=11.5)

    # --- AI gateway + inference --------------------------------------------------
    s.container(360, 600, 430, 92, "ns: envoy-gateway-system", theme="edge")
    s.box(374, 624, 402, 56, "AI gateway", ["routes /llm-inference/<model>/v1 to the model"], theme="edge",
          title_size=13, line_size=12)
    s.container(360, 730, 430, 232, "ns: llm-inference   (KServe + vLLM on Xeon)", theme="infer")
    s.box(374, 756, 402, 60, "qwen2-5-coder-14b · :8000  (default chat model)", ["tool-call parser · bf16 · KV cache"],
          theme="white", title_size=12.5, line_size=11.5)
    s.box(374, 824, 196, 56, "qwen3-coder-30b", ["2nd model (optional)"], theme="white", title_size=12.5, line_size=11.5)
    s.box(580, 824, 196, 56, "bge-base-en", ["embeddings"], theme="white", title_size=12.5, line_size=11.5)
    s.box(374, 888, 402, 60, "qwen3guard  (Qwen3Guard-Gen-0.6B)", ["answers 'Safety: Safe | Unsafe | Controversial'"],
          theme="white", title_size=12.5, line_size=11.5)

    s.arrow([(575, 548), (575, 624)], colour="green", label="model call", label_at=(583, 592))
    s.arrow([(575, 680), (575, 756)], colour="green")

    # --- Langfuse -------------------------------------------------------------
    s.container(40, 790, 270, 172, "ns: langfuse   (inference layer)", theme="obs")
    s.box(54, 816, 242, 130, "Langfuse web + worker", [
        "project 'inference'",
        "trace per request: input,",
        "output, tokens, cost,",
        "latency, llm.model_name",
    ], theme="obs", title_size=13.5, line_size=12, line_gap=19)
    s.arrow([(374, 520), (334, 520), (334, 880), (296, 880)], colour="purple",
            label="trace callback", label_at=(328, 700), label_anchor="end")

    # --- Agent Sandbox namespace (THIS REPO) -------------------------------------
    s.container(840, 262, 520, 450, "ns: agent-sandbox-system (this repo)", theme="repo")
    s.box(856, 300, 236, 94, "sandbox-router  (×2)", [
        "svc sandbox-router-svc:8080",
        "Go · --authz-mode=tokenreview",
        "only part that calls K8s API",
    ], theme="repo", title_size=13.5, line_size=12)
    s.box(1108, 300, 236, 94, "agent-sandbox-controller", [
        "operator v1.0.10",
        "reconciles Sandbox CRs",
        "into pods",
    ], theme="repo", title_size=13.5, line_size=12)
    s.box(884, 410, 460, 62, "CRDs (v1beta1)", [
        "Sandbox · SandboxTemplate (python-sandbox-template)",
        "SandboxClaim · SandboxWarmPool",
    ], theme="white", title_size=13, line_size=11.5, line_gap=16)
    s.box(856, 488, 300, 112, "python-pool  (warm pool, 5 pods)", [
        "sandbox pod: python-runtime-sandbox",
        "uvicorn :8888  POST /execute",
        "→ {stdout, stderr, exit_code}",
        "non-root · drop ALL caps · 1 CPU/1Gi",
    ], theme="repo", title_size=13, line_size=11.5)
    s.box(1170, 488, 174, 112, "kata-pool (opt-in)", [
        "size 1",
        "runtimeClassName",
        "kata-fc / kata-qemu",
        "own guest kernel",
    ], theme="white", title_size=13, line_size=11.5, dash="5 4")
    s.box(856, 614, 488, 84, "NetworkPolicy eat-sandbox-pool-egress", [
        "Ingress: only from app=sandbox-router (same namespace)",
        "Egress: public internet only — 10/8, 172.16/12, 192.168/16, 169.254/16 blocked",
    ], theme="danger", title_size=13, line_size=11.5)

    # --- K8s API --------------------------------------------------------------
    s.box(1400, 270, 160, 70, "Kubernetes API", ["TokenReview,", "SandboxClaim"], theme="platform",
          title_size=13.5, line_size=12)

    # --- Ray -----------------------------------------------------------------
    s.container(1400, 400, 360, 200, "ns: ray-system  (this repo · optional)", theme="repo", dash="4 4")
    s.box(1414, 426, 332, 50, "kuberay-operator 1.3.0", ["watches RayCluster CR"], theme="white",
          title_size=12.5, line_size=11.5)
    s.box(1414, 484, 332, 50, "Ray head  ray-cluster-head-svc", [":10001 client · :8265 dashboard · num-cpus=0"],
          theme="white", title_size=12.5, line_size=11.5)
    s.box(1414, 542, 332, 46, "Ray workers (autoscaled 1–4)", [], theme="white", title_size=12.5)

    # --- Redis + pgvector ------------------------------------------------------
    s.container(840, 750, 250, 140, "ns: redis   (this repo)", theme="repo")
    s.box(854, 776, 222, 100, "redis-stack-server-0", [
        ":6379 · ClusterIP only",
        "password required",
        "RediSearch · 10Gi PVC",
    ], theme="repo", title_size=13, line_size=12)
    s.container(1110, 750, 250, 140, "ns: pgvector   (this repo)", theme="repo")
    s.box(1124, 776, 222, 100, "pgvector-0  (StatefulSet)", [
        ":5432 · db agentdb",
        "user agentuser · PG 16",
        "vector ext 0.8.0 · 20Gi",
    ], theme="repo", title_size=13, line_size=12)

    # --- OpenShell ----------------------------------------------------------------
    s.container(1400, 640, 360, 322, "ns: openshell-system + openshell-sandboxes (opt-in)", theme="repo", dash="4 4")
    s.box(1414, 666, 332, 72, "openshell-0  (gateway)", [":8080 gRPC over mTLS", "policies + provider credentials"],
          theme="white", title_size=12.5, line_size=11.5)
    s.box(1414, 750, 332, 120, "sandbox pod", [
        "agent process (your code)",
        "+ OpenShell supervisor:",
        "  egress default-deny · L7 rules",
        "  Landlock · seccomp",
        "  placeholder key → real key",
    ], theme="white", title_size=12.5, line_size=11.5, line_gap=17)
    s.box(1414, 880, 332, 68, "provider 'genai-gateway'", ["Secret openshell-genai-key", "(never mounted in the sandbox)"],
          theme="white", title_size=12.5, line_size=11.5)
    s.arrow([(1580, 738), (1580, 750)], colour="orange")

    # --- Keycloak --------------------------------------------------------------
    s.container(840, 920, 520, 60, "ns: keycloak  — realm 'agent-toolkit' (this repo · only when auth is Keycloak JWT)",
                theme="repo", dash="4 4")

    # --- Arrows: agent -> things ----------------------------------------------------
    s.arrow([(296, 445), (374, 445)], colour="blue")
    s.label(335, 424, "OpenAI API", colour="#0284C7", size=10.5, anchor="middle")
    s.label(335, 438, "+ virtual key", colour="#0284C7", size=10.5, anchor="middle")
    # agent -> sandbox router, over the top lane
    s.arrow([(200, 290), (200, 238), (974, 238), (974, 300)], colour="orange",
            label="HTTP :8080 + Bearer <ServiceAccount token>  (create_sandbox, commands.run)", label_at=(330, 232))
    # agent -> ray
    s.arrow([(280, 290), (280, 250), (1700, 250), (1700, 426)], colour="orange", dashed=True,
            label="ray://…:10001 (optional)", label_at=(1460, 244))
    # agent -> redis / pgvector, lane under the litellm box
    s.arrow([(130, 498), (130, 718), (1050, 718), (1050, 776)], colour="orange",
            label="RESP :6379 (session state, vector search)", label_at=(620, 712))
    s.arrow([(1050, 718), (1310, 718), (1310, 776)], colour="orange", label="SQL :5432", label_at=(1140, 712))

    # sandbox router <-> api <-> controller
    s.arrow([(1060, 300), (1060, 289), (1400, 289)], colour="default")
    s.label(1128, 284, "TokenReview · SandboxClaim", colour="#334155", size=11)
    s.arrow([(1400, 328), (1344, 328)], colour="default", label="watch", label_at=(1350, 350))
    s.arrow([(1226, 394), (1226, 410)], colour="default")
    s.arrow([(1040, 472), (1040, 488)], colour="default", label="claim a warm pod", label_at=(1048, 485))
    s.arrow([(868, 394), (868, 488)], colour="orange")
    s.label(876, 485, ":8888 /execute", colour="#EA580C", size=11)

    # openshell -> K8s API and supervisor -> litellm
    s.arrow([(1746, 690), (1772, 690), (1772, 330), (1560, 330)], colour="default", label="Sandbox CR",
            label_at=(1690, 372))
    s.arrow([(1414, 810), (1380, 810), (1380, 1000), (815, 1000), (815, 500), (776, 500)], colour="orange",
            label="supervisor → LiteLLM :4000 with injected virtual key", label_at=(840, 1018))

    # Legend
    s.text(40, 1080, "How to read this diagram", size=14, weight=700)
    notes = [
        "1. Solid arrows = a call made at runtime; the label says the protocol/port.  Dashed arrow / border = optional component.",
        "2. The agent never talks to vLLM directly: every model call goes through LiteLLM (auth, guardrail, routing, tracing).",
        "3. The agent never talks to the Kubernetes API: the sandbox router does that, so the agent needs no RBAC permissions.",
        "4. Toolkit namespaces run in the Istio ambient mesh with strict mTLS; backends are ClusterIP only (no NodePort / LoadBalancer).",
        "5. Ports and names come from docs/backend-connection-reference.md, docs/agent-sandbox.md, docs/openshell.md and roles/*/defaults.",
    ]
    for i, n in enumerate(notes):
        s.text(40, 1106 + i * 22, n, size=12.5, fill="#334155")
    s.text(40, 1232, "Drawn for study from the agent-toolkit repository; not an official Intel diagram.",
           size=11.5, fill="#64748B", italic=True)
    s.save(os.path.join(HERE, "component.svg"))


# =============================================================================
# 3. SEQUENCE — one agent task end to end
# =============================================================================
def sequence():
    lanes = [
        ("User", ""),
        ("Agent app", "(your code)"),
        ("LiteLLM", "GenAI Gateway"),
        ("Guardrail", "→ qwen3guard"),
        ("Hybrid Router", "(in LiteLLM)"),
        ("vLLM model", "on Xeon"),
        ("Langfuse", "tracing"),
        ("Sandbox router", ":8080"),
        ("Sandbox pod", "warm pool"),
        ("Redis / pgvector", "memory"),
    ]
    X0, DX = 110, 178
    xs = [X0 + i * DX for i in range(len(lanes))]
    W = xs[-1] + 140
    s = SVG(W, 1560)
    title(s, "Intel® Agent Toolkit — Sequence diagram: one agent task, end to end",
          "Example task: “Fix the failing unit test.”  The agent loops LLM call → tool call → result until the model "
          "stops asking for tools.")

    TOP, BOTTOM = 96, 1470
    for (name, sub), x in zip(lanes, xs):
        th = "repo" if name in ("Sandbox router", "Sandbox pod", "Redis / pgvector") else (
            "client" if name in ("User", "Agent app") else ("obs" if name == "Langfuse" else (
                "infer" if name == "vLLM model" else "gateway")))
        s.box(x - 78, TOP, 156, 52, name, [sub] if sub else [], theme=th, align="center", title_size=13.5,
              line_size=11.5, line_gap=17)
        s.line(x, TOP + 52, x, BOTTOM, colour="#CBD5E1", sw=1.4, dash="5 5")
        s.box(x - 78, BOTTOM, 156, 34, name, [], theme=th, align="center", title_size=12.5)

    y = [178]

    def step(n=40):
        y[0] += n
        return y[0]

    def msg(a, b, text, ret=False, colour="default", num=None):
        yy = y[0]
        x1, x2 = xs[a], xs[b]
        pad = 4 if x2 > x1 else -4
        s.arrow([(x1 + pad, yy), (x2 - pad, yy)], colour="grey" if ret else colour, dashed=ret, sw=1.5)
        lbl = f"{num}. {text}" if num else text
        mid = (x1 + x2) / 2
        s.label(mid, yy - 7, lbl, colour="#475569" if ret else "#0F172A", size=11.5, anchor="middle",
                weight=500 if ret else 600)

    def self_msg(a, text, num=None, lines=None):
        yy = y[0]
        x = xs[a]
        s.arrow([(x + 4, yy - 10), (x + 34, yy - 10), (x + 34, yy + 6), (x + 6, yy + 6)], colour="default", sw=1.4)
        lbl = f"{num}. {text}" if num else text
        s.label(x + 42, yy, lbl, colour="#0F172A", size=11.5)
        if lines:
            for i, ln in enumerate(lines):
                s.label(x + 42, yy + 16 * (i + 1), ln, colour="#475569", size=11, weight=500)

    def frame(x1, y1, x2, y2, tag, text, theme="note", insert_at=None):
        start = len(s.parts)
        fill, stroke, tcol = {"note": ("#FFFBEB", "#D97706", "#78350F"),
                              "danger": ("#FEF2F2", "#DC2626", "#991B1B"),
                              "loop": ("#F8FAFC", "#475569", "#1E293B")}[theme]
        s.rect(x1, y1, x2 - x1, y2 - y1, fill, stroke, rx=6, sw=1.3, opacity=0.10)
        tw = len(tag) * 7.6 + 16
        s.rect(x1, y1, tw, 20, stroke, stroke, rx=4, sw=0)
        s.text(x1 + 8, y1 + 14, tag, size=11.5, weight=700, fill="#FFFFFF")
        s.text(x1 + tw + 8, y1 + 14, text, size=11.5, weight=600, fill=tcol)
        if insert_at is not None:          # draw the frame behind the arrows it encloses
            new = s.parts[start:]
            del s.parts[start:]
            s.parts[insert_at:insert_at] = new

    n = [0]

    def nx():
        n[0] += 1
        return n[0]

    msg(0, 1, "task: “fix the failing unit test”", num=nx())
    step()
    msg(1, 9, "load session state (Redis) + vector search for similar past work (pgvector)", num=nx(), colour="orange")
    step(32)
    msg(9, 1, "context: history + relevant memories", ret=True)

    loop_top = step(40)
    loop_idx = len(s.parts)
    step(50)
    msg(1, 2, "POST /v1/chat/completions  model='hybrid-router'  Bearer <virtual key>", num=nx(), colour="blue")
    step(42)
    self_msg(2, "check key, budget, rate limit", num=nx())
    step(40)
    msg(2, 3, "pre_call: screen the prompt", num=nx(), colour="blue")
    step(32)
    msg(3, 2, "Safety: Safe", ret=True)

    alt_top = step(26)
    alt_idx = len(s.parts)
    step(50)
    msg(2, 1, "HTTP 500 “Blocked by the content-safety guardrail…”", colour="red")
    step(22)
    frame(xs[1] - 70, alt_top, xs[3] + 150, y[0], "alt",
          "if Unsafe, guard unreachable, prompt too long or verdict unparseable → block (fail-closed)", theme="danger",
          insert_at=alt_idx)

    step(46)
    msg(2, 4, "async_pre_routing_hook (only for model 'hybrid-router')", num=nx(), colour="blue")
    step(42)
    self_msg(4, "classify → tier", num=nx(),
             lines=["rules score: tokens, code/reasoning keywords,", "multi-step patterns → SIMPLE/MEDIUM/COMPLEX/REASONING"])
    step(56)
    self_msg(4, "bandit picks a model of that tier", num=nx(),
             lines=["Thompson sampling (default) over tier candidates"])
    step(42)
    msg(4, 2, "model = qwen3-coder-30b", ret=True)
    step(40)
    msg(2, 5, "forward request via AI gateway → /llm-inference/qwen3-coder-30b/v1", num=nx(), colour="green")
    step(32)
    msg(5, 2, "completion with tool_call: run_shell(“pytest -x”)", ret=True)
    step(40)
    msg(2, 4, "success event: latency, completion tokens", num=nx(), colour="blue")
    step(40)
    self_msg(4, "reward = target_tpt / (target_tpt + latency/tokens)", num=nx(),
             lines=["bandit.update(tier, model, reward)  → learns over time"])
    step(50)
    msg(2, 6, "trace: prompt, output, tokens, cost, latency, llm.model_name", num=nx(), colour="purple")
    step(36)
    msg(2, 1, "response (assistant message + tool_call)", ret=True)

    step(44)
    msg(1, 7, "create_sandbox(warmpool='python-pool')  Bearer <SA token>", num=nx(), colour="orange")
    step(42)
    self_msg(7, "TokenReview, then SandboxClaim", num=nx(), lines=["controller hands over an already-running pod"])
    step(44)
    msg(7, 1, "sandbox handle (no cold start)", ret=True)
    step(40)
    msg(1, 7, "commands.run(“pytest -x”)", num=nx(), colour="orange")
    step(32)
    msg(7, 8, "POST :8888/execute {command}", num=nx(), colour="orange")
    step(32)
    msg(8, 7, "{stdout, stderr, exit_code}", ret=True)
    step(30)
    msg(7, 1, "tool result", ret=True)
    step(36)
    self_msg(1, "append tool result to messages; call the LLM again", num=nx())
    step(30)
    frame(xs[1] - 70, loop_top, xs[9] + 100, y[0], "loop",
          "agent loop — repeat steps 3–17 until the model replies without a tool call (cap the number of turns)",
          theme="loop", insert_at=loop_idx)

    step(52)
    msg(1, 9, "save session state + embedding of the outcome (long-term memory)", num=nx(), colour="orange")
    step(40)
    msg(1, 7, "sandbox.terminate()  — pool refills in the background", num=nx(), colour="orange")
    step(40)
    msg(1, 0, "final answer: “test fixed — here is the diff”", ret=True)

    # Notes
    ny = BOTTOM + 58
    s.text(40, ny, "Colours: blue = gateway work · green = model inference · orange = toolkit backends (this repository) · "
           "purple = telemetry · red = blocked request · grey dashed = reply.", size=12, fill="#334155")
    s.save(os.path.join(HERE, "sequence.svg"))


if __name__ == "__main__":
    architecture()
    component()
    sequence()
    print("wrote architecture.svg, component.svg, sequence.svg")
