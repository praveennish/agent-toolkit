# Intel® Agent Toolkit — Study Documents

A self-contained learning pack about the **Intel® Agent Toolkit**
(fork [`praveennish/agent-toolkit`](https://github.com/praveennish/agent-toolkit) of
`intel/enterprise-agent-toolkit`). It is written for **any engineer**, starting from zero and
building up step by step. Everything is derived from the repository's own README, docs, Ansible
roles, Helm charts and Docker files. Interpretations are clearly labelled.

## Reading order

| # | Document | What you get | Time |
|---|---|---|---|
| 1 | [`01-understanding-the-agent-toolkit.md`](01-understanding-the-agent-toolkit.md) | Teacher-style answers, level by level: purpose, Intel business goal, nature of the project, tech stack, performance tools and report, Agentic AI and ML concepts | 60–90 min |
| 2 | [`diagrams/`](diagrams/) | Architecture, component and sequence diagrams (PNG) | 15 min |
| 3 | [`02-design.md`](02-design.md) | Comprehensive design: architecture, component design, flows, deployment, security, KPIs, risks | 60 min |
| 4 | [`adr/`](adr/README.md) | 12 Architecture Decision Records: the *why* behind the design | 45 min |
| 5 | [`03-interview-prep.md`](03-interview-prep.md) | Complete interview guide: knowledge base with code, 164 Q&As, 5 worked system designs, 22 debugging cases, critique, flashcards, mock rounds | 1–2 days |
| 6 | [`04-code-walkthrough.md`](04-code-walkthrough.md) | File-by-file walkthrough of the code in execution order, with `file:line` references, trace exercises and findings | 2–3 h |
| 7 | [`improvement.md`](improvement.md) | Audit of what is measured today vs gaps, 11 proposed KPIs with owner layer and advantages, rollout plan, and a 2-minute interview narration | 30 min |

## Diagrams

| Diagram | File |
|---|---|
| Architecture (layered view) | [`diagrams/architecture.png`](diagrams/architecture.png) |
| Component (namespaces, ports, interfaces) | [`diagrams/component.png`](diagrams/component.png) |
| Sequence (one agent task end to end) | [`diagrams/sequence.png`](diagrams/sequence.png) |
| Code map: Kubernetes path (installer → preflight → registry → roles → charts) | [`diagrams/code-map-kubernetes.png`](diagrams/code-map-kubernetes.png) |
| Code map: Docker path (`deploy.sh` steps and generators) | [`diagrams/code-map-docker.png`](diagrams/code-map-docker.png) |
| Data model (Redis, pgvector tables, Docker databases) | [`diagrams/data-model.png`](diagrams/data-model.png) |

The diagrams are generated from code so they can be edited and re-rendered:

```bash
cd doc/diagrams/src && python3 build_diagrams.py && python3 build_code_maps.py && python3 build_data_model.py && node render.js
```

(`render.js` needs Node.js with Playwright and Chromium.)

## Key facts to remember about scope

- This repository is the **agent-toolkit layer** of Intel's Toolkit Manager
  (`intel/enterprise-ai-solutions`). It installs Redis Stack, pgvector, Agent Sandbox
  (+ Kata template), OpenShell, KubeRay and a Keycloak realm, plus preflight checks, a Docker
  Compose path and the documentation.
- The gateway (LiteLLM), Hybrid Router, guardrail, vLLM model serving and Langfuse are installed
  by the **inference layer**. Kubernetes, mesh, storage and observability come from the
  **infrastructure/platform layers**.
- The repository publishes **no measured LLM inference numbers**. Its measured results cover
  rack-scale networking and storage. `01-…` §4.5 and `02-design.md` §7 explain how to produce
  the inference report.
- Several documented features are marked **"not available in this release"** (rack-scale
  fabric, Intel® Arc™ XPU, Flowise plugin, parts of vLLM Semantic Router).
