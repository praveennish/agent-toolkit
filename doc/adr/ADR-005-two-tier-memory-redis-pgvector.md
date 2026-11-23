# ADR-005: Two-tier memory — Redis Stack (short-term) + PostgreSQL/pgvector (long-term)

**Status:** Accepted (reconstructed) · **Scope:** agent-toolkit layer (`roles/redis_stack`, `roles/pgvector`)

## Context

- LLMs are stateless. Agents need **working memory** within a task (fast, frequently updated,
  can expire) and **long-term memory** across sessions (durable, searchable by meaning, often
  joined with business data).
- RAG requires vector similarity search.
- The memory backends must be secure (agent session data is sensitive) and shared by many agents.

## Decision

Deploy two shared backends, each in its own namespace:

- **Redis Stack + RediSearch** (`redis`, `:6379`): sessions, semantic cache, fast vector
  search. Password mandatory, generated and stored in Secret `redis-stack-server-credentials`
  (with a ready `REDIS_URL`), ClusterIP only, NetworkPolicy, 10 Gi persistence.
- **PostgreSQL 16 + pgvector** (`pgvector`, `:5432`, db `agentdb`): durable vectors and
  relational data together. Secret `pgvector-credentials` with `DATABASE_URL`, 20 Gi.

Both are on by default.

## Alternatives considered

| Alternative | Why not |
|---|---|
| One store for everything (only Postgres or only Redis) | Redis is fastest for hot session state; Postgres gives durability, SQL joins and transactional safety. One store compromises one side |
| A dedicated vector DB (Milvus, Qdrant, Weaviate) | Another system to run and secure; pgvector covers RAG at enterprise scale for many cases and keeps relational and vector data together |
| In-memory / framework-local memory | Lost on pod restart; not shared between agents |

## Consequences

- ✅ Matches the agent memory model (short-term vs long-term) with mature, well-known databases.
- ✅ Credentials are delivered as ready-made connection URLs: agents never construct or hard-code them.
- ✅ Re-runs keep the existing password (no broken clients after a re-install).
- ⚠️ Single instances: no HA, no automated password rotation (documented).
- ⚠️ Agents choose *how* to use memory (schemas, TTLs, index design); the toolkit provides the backends only.

## Evidence in the repository

- `roles/redis_stack/*`, `charts/redis-stack/*` (NetworkPolicy with HBONE port 15008).
- `roles/pgvector/*`, `charts/pgvector/*`.
- `docs/backend-connection-reference.md`, `docs/single-node-deployment.md` Steps 2 / 2b.
