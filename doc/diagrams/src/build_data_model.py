"""Generates the data-model diagram as SVG.

    python3 build_data_model.py    # writes data-model.svg here
    node render.js                 # turns it into ../data-model.png

Tables, columns, indexes, users and databases are copied from
charts/pgvector/templates/configmap.yaml, charts/redis-stack/, and docker/deploy.sh.
"""
import os

from svglib import SVG, THEMES

HERE = os.path.dirname(os.path.abspath(__file__))


def table(s, x, y, w, name, purpose, cols, idx, theme="repo"):
    """Draw an ER-style table: header, purpose line, columns, index footer. Returns height."""
    fill, stroke, tcol = THEMES[theme]
    row = 19
    h = 56 + row * len(cols) + 12 + row * len(idx) + 10
    s.rect(x, y, w, h, "#FFFFFF", stroke, rx=8, sw=1.6)
    s.rect(x, y, w, 34, fill, stroke, rx=8, sw=1.6)
    s.text(x + 12, y + 23, name, size=15, weight=800, fill=tcol)
    s.text(x + 12, y + 52, purpose, size=11.5, fill="#475569", italic=True)
    cy = y + 56
    for c, t, note in cols:
        cy += row
        s.text(x + 14, cy, c, size=12, weight=700 if note == "PK" else 500, fill="#0F172A")
        s.text(x + 170, cy, t, size=12, fill="#1D4ED8")
        if note:
            s.text(x + w - 12, cy, note, size=11, weight=700, fill="#9A3412", anchor="end")
    cy += 10
    s.line(x + 8, cy, x + w - 8, cy, colour="#CBD5E1")
    for i in idx:
        cy += row
        s.text(x + 14, cy, i, size=11.5, fill="#334155")
    return h


def build():
    s = SVG(1760, 1120, preserve_space=True)
    s.text(40, 42, "Intel® Agent Toolkit — Data model (Redis, PostgreSQL + pgvector)", size=24, weight=800)
    s.text(40, 66, "What the repository actually defines. Kubernetes path: charts/pgvector init SQL + charts/redis-stack. "
           "Docker path: docker/deploy.sh (postgres/init.sql, redis/acl.conf).", size=13.5, fill="#475569")

    # ---------------- Kubernetes agentdb ----------------
    s.container(30, 90, 1110, 650, "Kubernetes · namespace pgvector · StatefulSet pgvector-0 · "
                "postgres://agentuser@pgvector.pgvector.svc:5432/agentdb · extension vector 0.8.0", theme="repo")

    h1 = table(s, 50, 130, 340, "agent_memory", "long-term memory, searched by meaning", [
        ("id", "BIGSERIAL", "PK"),
        ("agent_id", "TEXT", "NOT NULL"),
        ("user_id", "TEXT", "def 'default'"),
        ("session_id", "TEXT", ""),
        ("content", "TEXT", "NOT NULL"),
        ("embedding", "VECTOR(1536)", ""),
        ("metadata", "JSONB", "def '{}'"),
        ("created_at", "TIMESTAMPTZ", "NOW()"),
        ("updated_at", "TIMESTAMPTZ", "NOW()"),
    ], [
        "HNSW (embedding vector_cosine_ops)",
        "   m = 16, ef_construction = 64",
        "B-tree (agent_id, user_id)",
    ])
    h2 = table(s, 420, 130, 340, "agent_events", "audit log: actions, tool calls, LLM replies", [
        ("id", "BIGSERIAL", "PK"),
        ("agent_id", "TEXT", "NOT NULL"),
        ("user_id", "TEXT", "def 'default'"),
        ("session_id", "TEXT", ""),
        ("event_type", "TEXT", "NOT NULL"),
        ("payload", "JSONB", "def '{}'"),
        ("duration_ms", "INTEGER", ""),
        ("created_at", "TIMESTAMPTZ", "NOW()"),
    ], [
        "B-tree (agent_id, session_id,",
        "        created_at DESC)",
    ])
    h3 = table(s, 790, 130, 330, "agent_cache", "persistent cache: tool results, LLM replies", [
        ("id", "BIGSERIAL", "PK"),
        ("cache_key", "TEXT", "UNIQUE"),
        ("embedding", "VECTOR(1536)", ""),
        ("value", "JSONB", "NOT NULL"),
        ("hit_count", "INTEGER", "def 0"),
        ("expires_at", "TIMESTAMPTZ", ""),
        ("created_at", "TIMESTAMPTZ", "NOW()"),
    ], [
        "HNSW (embedding vector_cosine_ops)",
        "   m = 16, ef_construction = 64",
        "UNIQUE (cache_key)",
    ])

    # logical link note
    s.box(50, 466, 1070, 254, "How the tables are meant to be used (no foreign keys: agent_id · user_id · session_id are logical links)", [
        "Remember:  INSERT INTO agent_memory (agent_id, user_id, session_id, content, embedding, metadata) VALUES (…)",
        "Recall:    SELECT content FROM agent_memory WHERE agent_id = $1 AND user_id = $2 ORDER BY embedding <=> $q LIMIT 5",
        "Audit:     INSERT INTO agent_events (agent_id, session_id, event_type, payload, duration_ms) VALUES (…, 'tool_call', …)",
        "Cache:     exact  → SELECT value FROM agent_cache WHERE cache_key = $k AND (expires_at IS NULL OR expires_at > NOW())",
        "           semantic → ORDER BY embedding <=> $q LIMIT 1, reuse if distance below your threshold; then hit_count = hit_count + 1",
        "Created once at first start by 01-init-extensions.sql (extension + grants) and 02-create-agent-tables.sql (SET ROLE agentuser).",
    ], theme="white", title_size=13, line_size=12, line_gap=28)

    # ---------------- Redis ----------------
    s.container(1170, 90, 560, 360, "Redis Stack (RediSearch) · no schema: agents choose keys and indexes", theme="gateway")
    s.box(1186, 120, 528, 150, "Kubernetes · ns redis · redis-stack-server-0 :6379", [
        "user: default + password (--requirepass), 10 Gi PVC",
        "REDIS_URL = redis://default:<pw>@redis-stack-server",
        "            .redis.svc.cluster.local:6379",
        "for: session state · short-term memory · semantic cache",
        "validate: PING → PONG · MODULE LIST has 'search'",
    ], theme="white", title_size=12.5, line_size=11.8)
    s.box(1186, 284, 528, 150, "Docker · agentic-redis :6379 · redis/acl.conf", [
        "user default OFF (nopass nocommands)",
        "users admin · litellm · flowise · langfuse (SHA-256 pw)",
        "each: ~* &* +@all  → separate credentials, SHARED keys",
        "litellm: routing cache · flowise: job queue",
        "langfuse: events · agents/RAG: RediSearch",
    ], theme="white", title_size=12.5, line_size=11.8)

    # ---------------- Docker Postgres ----------------
    s.container(1170, 470, 560, 270, "Docker · agentic-postgres (pgvector/pgvector:pg16) · postgres/init.sql", theme="client")
    dbs = [("litellm", "owner litellm", "LiteLLM's own tables"),
           ("flowisedb", "owner flowise", "Flowise's own tables"),
           ("langfuse", "owner langfuse", "Langfuse's own tables"),
           ("agentdb", "owner agentuser", "extension vector ONLY")]
    for i, (db, own, what) in enumerate(dbs):
        x = 1186 + (i % 2) * 268
        y = 500 + (i // 2) * 86
        th = "danger" if db == "agentdb" else "white"
        s.box(x, y, 256, 74, db, [own, what], theme=th, title_size=12.5, line_size=11.5)
    s.text(1186, 690, "REVOKE CONNECT ON DATABASE … FROM PUBLIC → each user reaches only its own DB.", size=11.5, fill="#334155")
    s.text(1186, 710, "Runs once, when the postgres-data volume is empty.", size=11.5, fill="#334155")

    # ---------------- Issues ----------------
    s.box(30, 770, 1700, 250, "Things to know (and to raise in reviews)", [
        "1. Embedding size: VECTOR(1536) matches OpenAI-style embeddings; the bundled bge-base-en produces 768 dimensions → inserts from the "
        "local model fail. Fix: parameterise the dimension, or one table per embedding model.",
        "2. Schema drift: the three agent tables exist only on Kubernetes; Docker's agentdb has the extension but no tables.",
        "3. Not defined here: the litellm, langfuse and flowisedb schemas are created and migrated by those applications themselves.",
        "4. Single instances: Redis and pgvector have one replica each; no HA, no automated password rotation.",
        "5. Teardown deletes data: removing the namespace removes the PVC (Redis, pgvector).",
        "6. Docker Redis users all have ~* (all keys): credentials are separate, data is not. Use key-prefix ACLs for isolation.",
        "7. Passwords are generated once and reused on re-install (Secret lookup on Kubernetes, vault.yml on Docker), so clients never break.",
    ], theme="note", title_size=14, line_size=12.2, line_gap=26)

    s.text(40, 1060, "Source: charts/pgvector/templates/configmap.yaml, charts/pgvector/values.yaml, roles/pgvector, "
           "charts/redis-stack/, roles/redis_stack, docker/deploy.sh. Drawn for study.",
           size=11.5, fill="#64748B", italic=True)
    s.save(os.path.join(HERE, "data-model.svg"))


if __name__ == "__main__":
    build()
    print("wrote data-model.svg")
