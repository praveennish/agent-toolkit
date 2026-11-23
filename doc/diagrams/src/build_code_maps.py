"""Generates the two code-walkthrough diagrams as SVG.

    python3 build_code_maps.py     # writes code-map-kubernetes.svg, code-map-docker.svg here
    node render.js                 # turns every *.svg listed there into ../*.png

Names of files, tasks and functions are taken verbatim from the agent-toolkit
repository (roles/, playbooks/, charts/, docker/). Keep it that way when editing.
"""
import os

from svglib import SVG

HERE = os.path.dirname(os.path.abspath(__file__))


def title(s, text, sub):
    s.text(40, 42, text, size=24, weight=800, fill="#0F172A")
    s.text(40, 66, sub, size=13.5, fill="#475569")


def numbered(s, x, y, w, h, n, t, lines, theme="white", line_gap=17, size=11.5):
    s.box(x, y, w, h, f"{n}  {t}" if n else t, lines, theme=theme, title_size=12.5,
          line_size=size, line_gap=line_gap)


# =============================================================================
# Kubernetes / Ansible path
# =============================================================================
def kubernetes():
    s = SVG(1820, 1330)
    title(s, "Code walkthrough — Kubernetes path (Ansible roles, playbooks, charts)",
          "Read left to right: entry & configuration → preflight playbook → component registry & dispatch → "
          "what each role's install.yaml does → resources created. Orange = files in this repository.")

    # ---------------- Column 1: entry + config ----------------
    s.container(30, 90, 330, 1000, "1 · Entry point & configuration", theme="deploy")
    numbered(s, 44, 120, 302, 112, "", "es_auto_installer.sh", [
        "(enterprise-ai-solutions)",
        "configure → init agent-toolkit",
        "install | validate | teardown",
        "[--only] [-- -e var=value]",
    ], theme="white")
    numbered(s, 44, 248, 302, 160, "", "env/<name>/  (load order)", [
        "1 global_config.yaml",
        "2 config.inference.yaml",
        "3 config.agent-toolkit.yaml  ← LAST, wins",
        "  models.yaml (model catalog)",
        "  inventory/hosts.yaml (nodes)",
        "  kubespray_extra.yml (DNS fix)",
    ], theme="white")
    numbered(s, 44, 424, 302, 96, "", "config.yaml", [
        "this repo's defaults; seeded into",
        "config.agent-toolkit.yaml by init",
        "e.g. auth_type, *_enabled, sizes",
    ], theme="repo")
    numbered(s, 44, 536, 302, 96, "", "roles/<c>/defaults/main.yaml", [
        "lowest precedence: namespaces,",
        "versions, images, sizes, URLs",
        "(overridden by config.yaml / env)",
    ], theme="repo")
    numbered(s, 44, 648, 302, 186, "", "Variable precedence (low → high)", [
        "role defaults",
        "  < config.yaml (seeded copy)",
        "  < env/<name>/*.yaml",
        "  < -e extra vars on the command",
        "",
        "component_action = install |",
        "  validate | teardown",
    ], theme="white")
    numbered(s, 44, 850, 302, 226, "", "Commands you run", [
        "./es_auto_installer.sh install agent-toolkit",
        "./es_auto_installer.sh validate agent-toolkit",
        "./es_auto_installer.sh teardown agent-toolkit",
        "./es_auto_installer.sh install <c> --only",
        "standalone preflight:",
        " .venv/bin/ansible-playbook -i",
        "  env/<name>/inventory/hosts.yaml",
        "  ext/enterprise.agent-toolkit/",
        "  playbooks/preflight-check.yml",
    ], theme="white", size=11)

    # ---------------- Column 2: preflight ----------------
    s.container(390, 90, 420, 1000, "2 · playbooks/preflight-check.yml  (report-only, ≤ 5 min)", theme="repo")
    numbered(s, 404, 120, 392, 92, "", "Play 1 — hosts: all, gather_facts: true", [
        "init per-host results · read machine-id",
        "clean old results (host + controller)",
        "include the two layer files below",
    ], theme="white")
    numbered(s, 404, 228, 392, 112, "", "preflight/layer-network.yml", [
        "default gateway: ping → TCP/22 → TCP/443",
        "external DNS: getent hosts huggingface.co",
        "append JSON to",
        "/tmp/validate-stack-host-results.jsonl",
    ], theme="repo")
    numbered(s, 404, 356, 392, 232, "", "preflight/layer-platform-health.yml", [
        "kubelet DNS: no systemd-resolved anywhere →",
        "  write kube_resolv_conf=/etc/resolv.conf",
        "  (+ resolvconf_mode none); mixed → FAIL",
        "NTP (chronyc tracking | timedatectl)",
        "root + containerd disk (<10% free = FAIL)",
        "kernel/OS · kubelet · unfinished install",
        "swap · CPU governor (scaling_governor)",
        "NUMA + sockets (lscpu) · THP",
        "node pressure (cluster) · HF token check",
    ], theme="repo")
    numbered(s, 404, 604, 392, 72, "", "fetch per-host results → controller", [
        "(avoids hostvars re-templating with",
        " ansible_connection: local)",
    ], theme="white")
    numbered(s, 404, 692, 392, 206, "", "Play 2 — hosts: localhost (Report & Gate)", [
        "machine-id via delegation vs direct",
        "  → detects missing ansible_connection",
        "aggregate · stamp · dedup",
        "merge into cumulative latest report",
        "write JSON (latest + archive)",
        "render templates/health-report.html.j2",
        "  and health-report.txt.j2",
        "print summary + PREFLIGHT WARNING block",
    ], theme="white")
    numbered(s, 404, 914, 392, 92, "", "Output", [
        "env/<name>/logs/health-report-latest",
        "  .json · .html · .txt",
        "FAIL / WARN / PENDING / OK — never blocks",
    ], theme="obs")
    s.arrow([(600, 212), (600, 228)], colour="orange")
    s.arrow([(600, 340), (600, 356)], colour="orange")
    s.arrow([(600, 588), (600, 604)], colour="orange")
    s.arrow([(600, 676), (600, 692)], colour="orange")
    s.arrow([(600, 898), (600, 914)], colour="orange")

    # ---------------- Column 3: registry + dispatch ----------------
    s.container(840, 90, 430, 1000, "3 · Registry & uniform dispatch", theme="repo")
    numbered(s, 854, 120, 402, 214, "", "components.yaml", [
        "layer agent-toolkit",
        "  depends_on: [platform, inference]",
        "redis_stack       enabled default true",
        "pgvector          enabled default true",
        "agent_sandbox     enabled default true",
        "openshell         default false",
        "     depends_on: [agent_sandbox]",
        "kuberay           default false",
        "keycloak_agent_config  when auth ≠ litellm",
    ], theme="repo")
    numbered(s, 854, 350, 402, 150, "", "roles/<c>/tasks/main.yaml  (same in all 6)", [
        "include_tasks:",
        "  \"{{ component_action | default('install') }}.yaml\"",
        "when: action != 'install'",
        "      or <c>_enabled | bool",
        "→ install skipped if disabled;",
        "  validate / teardown always run",
    ], theme="repo")
    numbered(s, 854, 516, 402, 128, "", "install.yaml", [
        "namespace (+ ambient label if istio_enabled)",
        "secret reuse · failed-release cleanup",
        "helm / kubectl apply · patch upstream YAML",
        "readiness polling (until/retries/delay)",
        "no_log on every secret-handling task",
    ], theme="repo")
    numbered(s, 854, 660, 402, 128, "", "validate.yaml", [
        "redis: pod Running · PING=PONG · MODULE search",
        "pgvector: pod · vector extension · Secret",
        "sandbox: controller · router · CRDs · template",
        "  · warm pool ready · kata template",
        "openshell: gateway ready · kuberay: op + head",
    ], theme="repo")
    numbered(s, 854, 804, 402, 128, "", "teardown.yaml", [
        "redis: helm release · namespace (PVC goes too)",
        "pgvector: release · Secret · namespace",
        "sandbox: router · RBAC · manifest · namespace",
        "openshell: release · PeerAuthentication · nss",
        "kuberay: cluster · operator · namespace",
    ], theme="repo")
    numbered(s, 854, 948, 402, 128, "", "meta/main.yaml + defaults/main.yaml", [
        "galaxy_info: Apache-2.0, ansible ≥ 2.15",
        "dependencies: [] (ordering from registry)",
        "checkov:skip=CKV_SECRET_6 on Secret NAMES",
        "  (names, not values)",
    ], theme="white")
    s.arrow([(1055, 334), (1055, 350)], colour="orange")
    s.arrow([(1055, 500), (1055, 516)], colour="orange")

    # ---------------- Column 4: per-role install ----------------
    s.container(1300, 90, 490, 1000, "4 · What each install.yaml does (in order)", theme="repo")
    roles = [
        ("redis_stack", 128, [
            "ns → read redis-stack-server-credentials →",
            "  reuse pw or generate (24 chars) → helm_info",
            "→ remove FAILED release → helm charts/redis-stack",
            "  (auth on, meshPort 15008) → assert → wait pods",
        ]),
        ("pgvector", 128, [
            "ns → reuse pw (also chart's POSTGRES_PASSWORD)",
            "→ failed-release cleanup → helm charts/pgvector",
            "  (timeout 15m) → wait → psql: vector ext?",
            "→ Secret pgvector-credentials (DATABASE_URL)",
        ]),
        ("agent_sandbox", 182, [
            "ns → apply upstream sandbox-with-extensions.yaml",
            "→ wait controller → get_url router YAML ×7",
            "  (retries 5, delay 30: GitHub 429)",
            "→ patch: image :latest → pinned; add",
            "  --authz-mode=tokenreview + require-token",
            "→ template → NetworkPolicy eat-sandbox-pool-egress",
            "→ SandboxWarmPool python-pool (5) → [Kata] → wait",
        ]),
        ("openshell", 182, [
            "TG1 nodes reachable · Sandbox CRD serves v1beta1",
            "TG2 2 ns · local-path? · helm (values merged)",
            "   · copy client TLS · NodeLocal DNS · NetPol",
            "TG3 PeerAuthentication · kubectl exec LiteLLM:",
            "   /key/delete + /key/generate → Secret",
            "   · CLI 0700 · profile + provider · rm creds",
            "TG4 summary",
        ]),
        ("kuberay", 128, [
            "ns → remove failed releases → helm repo",
            "→ operator 1.3.0 → charts/kuberay RayCluster",
            "→ wait head + workers ready → dashboard route",
            "  + basic-auth Secret (created once)",
        ]),
        ("keycloak_agent_config", 110, [
            "wait StatefulSet keycloak → KeycloakRealmImport",
            "  realm agent-toolkit → wait Done | HasErrors",
            "→ fail with the import's error message",
        ]),
    ]
    y = 120
    for name, h, lines in roles:
        numbered(s, 1314, y, 462, h, "", name, lines, theme="white", line_gap=17, size=11)
        y += h + 12

    # ---------------- Bottom: resources ----------------
    s.container(30, 1110, 1760, 150, "5 · charts/ and upstream artefacts → Kubernetes resources", theme="platform")
    res = [
        ("charts/redis-stack", ["StatefulSet + Service (ClusterIP)", "Secret (fails if no pw) · NetPol"]),
        ("charts/pgvector", ["StatefulSet · Service · Secret", "init ConfigMap: 3 agent tables"]),
        ("charts/agent-sandbox", ["default-templates.yaml", "kata-templates.yaml"]),
        ("upstream agent-sandbox", ["CRDs + controller (manifest)", "router YAML (patched)"]),
        ("charts/openshell", ["values.yaml overlay", "genai-gateway-provider.yaml"]),
        ("charts/kuberay", ["RayCluster (in-tree autoscaling)", "head num-cpus 0 · workers 1–4"]),
    ]
    for i, (t, ln) in enumerate(res):
        s.box(46 + i * 290, 1140, 274, 104, t, ln, theme="repo", title_size=12.5, line_size=11.5)

    # Arrows between columns
    s.arrow([(346, 176), (404, 166)], colour="#CA8A04")
    s.arrow([(796, 960), (826, 960), (826, 230), (854, 230)], colour="orange",
            label="then components", label_at=(722, 1080))
    s.arrow([(1256, 580), (1314, 580)], colour="orange")
    s.arrow([(1545, 1090), (1545, 1140)], colour="orange")

    s.text(40, 1300, "Source: agent-toolkit repository (components.yaml, config.yaml, roles/*/tasks/*.yaml, "
           "playbooks/preflight*, charts/). Drawn for study.", size=11.5, fill="#64748B", italic=True)
    s.save(os.path.join(HERE, "code-map-kubernetes.svg"))


# =============================================================================
# Docker Compose path
# =============================================================================
def docker():
    s = SVG(1820, 1090)
    title(s, "Code walkthrough — Docker Compose path (docker/deploy.sh and generators)",
          "The numbered boxes are the order deploy.sh runs in. Left: inputs it reads. Right: files it writes "
          "and containers it starts.")

    # Inputs
    s.container(30, 90, 290, 640, "Inputs (you edit / it keeps)", theme="client")
    ins = [
        ("docker/config.cfg", ["hugging_face_token", "serving_engine=vllm|openvino",
                               "models=<HF IDs, comma-sep>", "tool_call_parser",
                               "deploy_agenticai_plugin", "deploy_observability",
                               "deploy_docker_fresh · proxies"], 196),
        ("model-configs.yaml", ["vLLM: env, command_args,", "resources, served_name,", "litellm_mode"], 96),
        ("ovms-model-configs.yaml", ["OVMS: task, weight_format,", "tool_parser, source_model"], 80),
        ("chat-templates/*.jinja", ["gemma4 · hermes · qwen3coder"], 62),
        ("docker/vault.yml", ["all secrets; created once", "by generate-vault-secrets.sh"], 80),
    ]
    y = 118
    for t, ln, h in ins:
        s.box(44, y, 262, h, t, ln, theme="white", title_size=12.5, line_size=11.5)
        y += h + 10

    # Steps
    steps = [
        ("1", "Parse args", ["--observability --full --down", "--skip-build --pull", "--skip-confirmation"]),
        ("2", "Profiles + engine", ["no flags → read deploy_* from", "config.cfg → flowise /", "observability; engine →", "agentic-vllm-* | agentic-ovms-*"]),
        ("3", "Docker + prereqs", ["install_docker_fresh (opt,", "apt/yum + proxy) · compose v2", "daemon reachable"]),
        ("4", "--down?", ["compose down --volumes", "(passwords regenerate)", "→ exit"]),
        ("5", "Secrets", ["vault.yml missing →", "generate-vault-secrets.sh", "read every secret;", "die with fix if missing"]),
        ("6", "ACL + SQL", ["redis/acl.conf: admin, litellm,", "flowise, langfuse users", "postgres/init.sql: per-service", "users + DBs, REVOKE PUBLIC"]),
        ("7", ".env", ["NO_PROXY += service names", "remember old NO_PROXY", "keep FLOWISE_DENYLIST_URLS", "write .env from vault"]),
        ("8", "Show + check", ["print config (secrets masked)", "check_system_resources", "(base 8 GB + per model)", "confirm [y/N]"]),
        ("9", "Generate", ["generate-docker-compose.sh", "(see detail box below)", "hash litellm/config.yaml", "before/after"]),
        ("10", "Engine switch", ["cleanup_other_engine_containers", "(model volumes kept)"]),
        ("11", "Start", ["remove stray network", "compose pull (opt)", "compose up -d --no-recreate", "+ profiles"]),
        ("12", "Reconcile LiteLLM", ["NO_PROXY changed →", "  up --force-recreate litellm", "config hash changed →", "  restart litellm"]),
        ("13", "Flowise lock", ["owner exists →", "DENYLIST_URLS=", "/api/v1/account/register", "→ recreate flowise"]),
        ("14", "Langfuse bucket", ["observability profile →", "create MinIO bucket"]),
        ("15", "Summary", ["URLs: LiteLLM :4000,", "models :2080+, Flowise", ":3000, Langfuse :3002"]),
    ]
    sx, sy, w, h, gx, gy = 350, 100, 214, 132, 16, 24
    per_row = 5
    for i, (n, t, ln) in enumerate(steps):
        r, c = divmod(i, per_row)
        x = sx + c * (w + gx)
        y = sy + r * (h + gy)
        s.box(x, y, w, h, f"{n}  {t}", ln, theme="repo", title_size=12.5, line_size=11, line_gap=17)
        if c < per_row - 1 and i < len(steps) - 1:
            s.arrow([(x + w, y + h / 2), (x + w + gx, y + h / 2)], colour="orange")
        elif i < len(steps) - 1:
            s.arrow([(x + w / 2, y + h), (x + w / 2, y + h + 8), (sx + w / 2, y + h + 8), (sx + w / 2, y + h + gy)],
                    colour="orange")

    # Generator detail
    s.container(350, 580, 1150, 300, "generate-docker-compose.sh → main()", theme="repo")
    gen = [
        ("read_serving_engine", ["sets engine, config library,", "output file (vllm | ovms)"]),
        ("read_tool_call_parser", ["update_default_tool_call_parser", "(idempotent rewrite of default)"]),
        ("read_models_from_config", ["validate_model_id (org/name)", "get_hf_model_id strips -Specdec"]),
        ("per model (port 2080, 2081 …)", ["generate_vllm_service | generate_ovms_service", "(+ ovms-model-store-init)"]),
    ]
    for i, (t, ln) in enumerate(gen):
        s.box(366 + i * 282, 610, 268, 84, t, ln, theme="white", title_size=12, line_size=11)
        if i < 3:
            s.arrow([(366 + i * 282 + 268, 652), (366 + (i + 1) * 282, 652)], colour="orange")
    s.box(366, 708, 548, 158, "generate_vllm_service (one container per model)", [
        "image vllm/vllm-openai-cpu · container agentic-vllm-<served_name>",
        "--model <HF id> --served-model-name <full HF id> --port 8000",
        "+ env / command_args from model-configs.yaml (default: block)",
        "+ speculative args for -Specdec · ports <2080+i>:8000",
        "volume vllm-model-cache-<i> · shm · memory limit (80g default)",
        "healthcheck curl /health · start_period 300s",
    ], theme="white", title_size=12, line_size=11)
    s.box(928, 708, 558, 158, "then: volumes · networks · rm stale file · generate_litellm_config", [
        "drop the OTHER engine's compose file (no stale definitions)",
        "litellm/config.yaml: langfuse success/failure callbacks",
        "  model_list: model_name <HF id> → openai/<HF id>",
        "  api_base http://agentic-<engine>-<name>:8000/v1|/v3",
        "  api_key: dummy (backends have no auth)",
        "  embedding → encoding_format: float · model_info.mode",
    ], theme="white", title_size=12, line_size=11)

    # Outputs
    s.container(1530, 90, 260, 790, "Outputs", theme="obs")
    outs = [
        ("docker/.env", ["secrets + settings for compose"]),
        ("redis/acl.conf", ["per-service Redis users"]),
        ("postgres/init.sql", ["users, DBs, pgvector on agentdb", "(runs once on first start)"]),
        ("docker-compose.vllm.yml", ["or docker-compose.ovms.yml", "(generated, don't edit)"]),
        ("litellm/config.yaml", ["model routing (generated)"]),
        ("Running containers", ["agentic-postgres :5432", "agentic-redis :6379", "agentic-litellm :4000",
                                "agentic-vllm-*|ovms-* :2080+", "agentic-flowise 127.0.0.1:3000",
                                "langfuse :3002 + clickhouse + minio"]),
    ]
    y = 118
    for t, ln in outs:
        h = 44 + 17 * len(ln)
        s.box(1544, y, 232, h, t, ln, theme="white", title_size=12.5, line_size=11)
        y += h + 10

    s.arrow([(306, 220), (350, 166)], colour="blue", label="reads", label_at=(300, 200))
    s.arrow([(1500, 760), (1544, 760)], colour="purple")

    s.text(40, 920, "How to read it", size=14, weight=700)
    notes = [
        "• deploy.sh is re-runnable: unchanged model containers are not restarted (--no-recreate); LiteLLM is only "
        "recreated/restarted when its inputs changed.",
        "• Secrets live in vault.yml and stay stable across runs; --down deletes volumes because passwords would "
        "otherwise mismatch the initialised databases.",
        "• Switching serving_engine removes the other engine's compose file and containers but keeps model caches "
        "(named volumes), so switching back re-downloads nothing.",
        "• Containers drop all capabilities; Flowise is loopback-only until its first owner exists.",
    ]
    for i, n in enumerate(notes):
        s.text(40, 946 + i * 24, n, size=12.5, fill="#334155")
    s.text(40, 1060, "Source: docker/deploy.sh, docker/scripts/generate-docker-compose.sh, "
           "docker/scripts/generate-vault-secrets.sh, docker/docker-compose.yml. Drawn for study.",
           size=11.5, fill="#64748B", italic=True)
    s.save(os.path.join(HERE, "code-map-docker.svg"))


if __name__ == "__main__":
    kubernetes()
    docker()
    print("wrote code-map-kubernetes.svg, code-map-docker.svg")
