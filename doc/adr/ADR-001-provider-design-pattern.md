# ADR-001: Provider Design Pattern — pluggable blocks behind standard interfaces

**Status:** Accepted (reconstructed) · **Scope:** whole product

## Context

- Enterprises already own parts of the stack (a gateway, a vector database, a monitoring
  system) and fear vendor lock-in.
- The AI-infrastructure landscape changes monthly; a component that is best today may be
  replaced next year.
- Intel wants the stack to be adoptable *incrementally*: start with defaults, swap pieces
  later.

## Decision

Organise the platform as **seven functional blocks** (gateway, memory, routing, tools,
sandbox, observability, deployment). Each block defines a **capability contract** (what it
does) and ships an **Intel-validated default provider** (how). Consumers depend only on
**standard interfaces**: the OpenAI HTTP API, the Redis protocol, the PostgreSQL protocol,
an HTTP sandbox API, MCP and OTel. Every component has an independent on/off switch
(`*_enabled`).

## Alternatives considered

| Alternative | Why not |
|---|---|
| A tightly integrated, opinionated monolith | Faster to build, but forces big-bang replacements and creates lock-in, which contradicts the open-ecosystem goal |
| A proprietary Intel runtime/API | Would limit framework compatibility and adoption |
| "Bring everything yourself" (docs only) | No time-to-value advantage; the core problem stays unsolved |

## Consequences

- ✅ Swap one provider at a time; no lock-in; works with any OpenAI-compatible framework.
- ✅ Each component can be installed, validated and torn down on its own (see ADR-011).
- ⚠️ Integration testing grows with every supported combination; the project validates the
  *defaults*.
- ⚠️ "Standard interface" is only as strong as the clients' use of it (e.g. RediSearch-specific
  commands tie an agent to Redis).

## Evidence in the repository

- `README.md` → "Provider Design Pattern", "Provider Blocks", "Can I replace individual components?"
- `components.yaml` → independent `enabled` flags per component.
- `config.yaml` → per-component switches; `docs/configuring-inference-config-cfg-file.md`.
