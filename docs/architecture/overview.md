# Architecture Overview

_Generated on 2026-06-24 03:23 UTC._

## Executive Summary

ArchonHub is the local, self-hosted plane of the AgentHarness ecosystem. It pairs a FastAPI hub server with a SQLite persistence layer, specialized agent skill files, background scheduling, a WebSocket event bus, and SwiftUI clients for iPhone and Apple Watch. It runs alongside the Base44 Superagent plane rather than replacing it.

## Topology Diagram

```
                                   ┌───────────────────────────┐
                                   │   Base44 Superagent Plane  │
                                   │ .agents/agents/projects/** │
                                   │ .agents/rules/**           │
                                   └─────────────┬─────────────┘
                                                 │ skill sync / shared prompts
                                                 │
┌──────────────────────────┐         ┌──────────▼──────────┐         ┌──────────────────────────┐
│ iOS SwiftUI App          │  HTTPS  │  ArchonHub Hub      │  SQLite │ runs_v3.db               │
│ watchOS Companion        ├────────►│  FastAPI + WS       ├────────►│ core + feature tables    │
│ HubClient + AuthStore    │         │  app factory +      │         │ memory + reports + RAG   │
│                          │         │  routers/core       │         │                          │
└────────────┬─────────────┘         └─────┬─────────┬─────┘         └──────────────────────────┘
             │                             │         │
             │ WS `/ws`                    │         │ imports / jobs / helpers
             │                             │         │
             │                    ┌────────▼───┐ ┌──▼──────────────────────┐
             │                    │ Scheduler  │ │ Feature Modules         │
             │                    │ APScheduler│ │ global_memory.py        │
             │                    │ hub_sched. │ │ progressive_intelligence│
             │                    └────────────┘ │ code_sandbox.py         │
             │                                   │ document_rag.py         │
             │                                   │ email_* / oauth_*       │
             │                                   │ web_search.py           │
             │                                   └──────────┬──────────────┘
             │                                              │
             │                                   ┌──────────▼──────────────┐
             └──────────────────────────────────►│ Agent graph execution   │
                                                 │ hub_nodes / LangGraph   │
                                                 │ skill files + memory    │
                                                 └─────────────────────────┘
```

## Component Map

| Component | Primary file(s) | Role |
| --- | --- | --- |
| Hub entrypoint | `.agents/agentharness/app/v3/hub_server.py` | App factory (~245 lines) that wires lifespan, CORS, `/ws`, `/`, `/web`, and router registration. |
| Core config | `.agents/agentharness/app/v3/core/config.py` | Centralizes paths, env vars, JWT defaults, CORS origins, and version metadata. |
| Core database | `.agents/agentharness/app/v3/core/database.py` | Owns schema initialization plus shared SQLite CRUD and query helpers. |
| Core auth | `.agents/agentharness/app/v3/core/auth.py` | JWT create/verify helpers, current/admin-user dependencies, login rate limiting, and global exception handler. |
| Core hub runtime | `.agents/agentharness/app/v3/core/hub.py` | Defines `HubServer`, the `hub` singleton, worker loop, scheduler wiring, and emit helpers. |
| Core models | `.agents/agentharness/app/v3/core/models.py` | Holds the shared Pydantic request/response models used across routers. |
| API routers | `.agents/agentharness/app/v3/routers/*.py` | 28 domain routers partition the REST surface by feature area (`auth_routes.py`, `runs.py`, `agents.py`, etc.). |
| Global Memory | `.agents/agentharness/app/v3/global_memory.py` | Persistent fact store plus prompt injection helpers. |
| Progressive Intelligence | `.agents/agentharness/app/v3/progressive_intelligence.py` | Reflexion scoring, skill levels, auto-memory, and pattern detection. |
| Sandbox | `.agents/agentharness/app/v3/code_sandbox.py` | Restricted Python execution with AST screening and Docker/subprocess modes. |
| RAG | `.agents/agentharness/app/v3/document_rag.py` | Chunking, embeddings, ChromaDB vector storage, semantic search. |
| Email/OAuth | `.agents/agentharness/app/v3/oauth_connector.py`, `email_analyzer.py`, `email_executor.py` | Connector auth, message analysis, cleanup planning, cleanup execution, rollback. |
| Search | `.agents/agentharness/app/v3/web_search.py` | SerpAPI integration, freshness heuristics, citation formatting. |
| Scheduling | `.agents/agentharness/app/v3/hub_scheduler.py` | APScheduler jobs for briefings, reflexion, grant sweeps, markets, backups, and sync tasks. |
| Monitoring | `.agents/agentharness/app/v3/proactive_monitor.py` | Deadline and anomaly checks that create notifications. |
| LLM routing | `.agents/agentharness/app/v3/llm_router.py`, `model_catalog.py` | Ollama-first routing, provider catalog, capability-based model selection. |
| iOS client | `projects/archonhub-ios/ArchonHub/**` | SwiftUI app for auth, Inez, runs, docs, memory, automations, and settings. |
| watchOS client | `projects/archonhub-ios/ArchonHubWatch/**` | Status, quick run, notifications, complication surfaces. |

## Request Flow

```
User action
  → HubClient builds HTTP request / WS message
  → FastAPI route validates auth and request body
  → Hub server reads/writes SQLite or dispatches helper module
  → Optional background task / queue entry / agent run
  → Server returns JSON response
  → For long-running work, `/ws` broadcasts run and notification events
```

## Agent Run Lifecycle

```
POST /api/runs
  → hub.submit_job(config)
  → job_queue row created
  → background worker dequeues item
  → graph execution via hub_nodes / run_graph
  → runs row updated with output, score, critique, status
  → reflexion + skill updates may occur
  → broadcast run update over WebSocket
  → notifications / todos / reports may be written
```

## Storage Layers

| Store | Location | Contains |
| --- | --- | --- |
| SQLite | `.agents/agentharness/memory/runs_v3.db` | Operational tables, memory facts, runs, documents, automations, feedback, reports, paper trading, uploaded files, and more. |
| Agent memory text files | `.agents/agentharness/memory/*.txt` | Human-readable per-agent memory snapshots / reflexion traces. |
| ChromaDB | `.agents/agentharness/memory/chromadb` | Persistent vector store for document chunks. |
| Uploads | `.agents/data/uploads` or local upload path | Raw uploaded files for parsing / embedding. |
| Skill files | `.agents/agents/projects/**` | Long-lived system prompts and operational rules. |

## Authentication Model

- JWT Bearer is the main mechanism for HTTP routes.
- WebSocket clients authenticate by sending an initial `{ "type": "auth", "token": "..." }` message within 15 seconds of connection or the server closes the socket with code `1008`.
- `X-API-Token` fallback exists for automation use cases through `hub_config.api_token`.
- Default seeded admin credentials are `admin / ArchonHub2024!` unless overridden by `.agents/.env`.
- Current source code uses `HS256` and a 24-hour expiry constant; stakeholder-facing docs often describe a 30-day token target. Treat that difference as a product gap to resolve.

## Security Architecture

- CORS is activated through `CORS_ORIGINS`; if unset the server allows `*`, while production uses `https://app.archonhub.app,http://localhost:8765,http://localhost:3000`.
- `POST /api/auth/login` applies IP-based rate limiting and returns HTTP `429` after 10 failed attempts within 5 minutes.
- Startup logs a warning if `JWT_SECRET` is still the factory default, but the process continues booting.
- A global exception handler catches unhandled server errors and returns `{"detail":"internal server error"}` instead of exposing tracebacks.
- The modular split keeps HTTP entrypoints in `routers/` and sensitive shared logic in `core/`, reducing the blast radius of future changes.

## Runtime Dependencies

| Dependency | Why it matters | Behavior when missing |
| --- | --- | --- |
| FastAPI / Uvicorn | HTTP API + OpenAPI server | Local engine cannot serve HTTP; many modules still import for static analysis. |
| python-jose | JWT encode/decode | Hub server falls back to a local HMAC JWT implementation. |
| APScheduler | Scheduler runtime | Scheduler builder falls back to a no-op scheduler wrapper. |
| ChromaDB + OpenAI API key | Document embeddings and semantic retrieval | Upload still works; embedding/search features return disabled-style failures. |
| SerpAPI key | Fresh web search | Search endpoint returns key-related errors. |
| Docker | Strongest sandbox isolation | Sandbox can still run in subprocess mode if available. |
| Ollama | Local-first LLM routing | Router falls back to cloud providers if configured. |

## Scheduler and Background Work

- Built-in jobs include daily briefing, daily reflexion, grant sweeps, planning monitors, fare alerts, Sigma Signal checks, markets reports, database cleanup, database backup, and free-key sync.
- Queue-driven agent work is separate from APScheduler timing; the scheduler submits jobs into the same hub orchestration pipeline.
- Reporting hooks (`report_monitor.py`) are invoked after several built-in jobs to persist human-readable summaries.

## Client Architecture

- `ArchonHubApp.swift` wires `AuthStore` and `HubClient.shared` into the environment.
- `ContentView.swift` exposes five top-level tabs: Dashboard, Inez, Activity, Workspace, Settings.
- The watch app uses a paging `TabView` with status, quick-run, and notifications screens plus a complication.

## Implementation Caveats

- Several feature modules are deliberately partial. For example, the morning brief agent has placeholder email/market data collection, and proactive monitor anomaly checks are a thin first pass.
- Optional migrations (`add_fts_search.py`, `add_citations_schema.py`) enable richer search and citation behavior beyond the base schema.
- The local engine and Base44 cloud plane share prompt assets but not necessarily the same runtime capabilities or state guarantees.

## Related Documentation

- [Database schema](database-schema.md)
- [API reference](../api/reference.md)
- [Agent overview](../agents/overview.md)
- [iOS overview](../ios/overview.md)

## Source References

- `.agents/agentharness/app/v3/hub_server.py`
- `.agents/agentharness/app/v3/core/config.py`
- `.agents/agentharness/app/v3/core/database.py`
- `.agents/agentharness/app/v3/core/auth.py`
- `.agents/agentharness/app/v3/core/hub.py`
- `.agents/agentharness/app/v3/core/models.py`
- `.agents/agentharness/app/v3/routers/`
- `.agents/agentharness/app/v3/hub_scheduler.py`
- `.agents/agentharness/app/v3/global_memory.py`
- `.agents/agentharness/app/v3/progressive_intelligence.py`
- `projects/archonhub-ios/ArchonHub/App/ArchonHubApp.swift`
- `projects/archonhub-ios/ArchonHub/App/ContentView.swift`

## Implementation Checklist

- Confirm `architecture overview` responses use ISO 8601 UTC timestamps.
- Confirm Bearer JWT is attached on authenticated requests.
- Confirm error payloads use `{"detail": "..."}`.
- Confirm the iOS client can decode optional/null fields safely.
- Confirm background jobs publish notifications or run status events when relevant.
- Confirm SQLite writes update `created_at` / `updated_at` consistently when the table includes them.
- Confirm WebSocket listeners gracefully handle reconnects and unauthorized closes.
- Confirm scheduler or automation side effects are idempotent where retries can occur.
- Confirm prompt, memory, and document payloads are trimmed before persistence when the source code enforces size caps.
- Confirm optional modules fail closed with `503` or `500` rather than silently corrupting state.

## Operational Notes

- `architecture overview` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
