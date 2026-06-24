# ArchonHub Documentation

_Generated on 2026-06-24 03:23 UTC from the current local ArchonHub codebase._

## What this docs set covers

- The self-hosted ArchonHub Python engine in `.agents/agentharness/app/v3/`.
- The SQLite schema that backs runs, memory, documents, automations, feedback, and market data.
- The SwiftUI iOS and watchOS clients in `projects/archonhub-ios/`.
- Contracts for agent outputs, API responses, memory facts, sandbox execution, progressive intelligence, dispatch records, and WebSocket events.
- Local deployment, Docker packaging, and environment configuration.

## System Snapshot

- **Backend:** Modular FastAPI hub server — `hub_server.py` is a ~245-line app factory; all route logic lives in `routers/` (28 files) and shared internals in `core/` (config, database, auth, hub, models). Helper modules: `hub_db.py`, `hub_scheduler.py`, `hub_nodes.py`, `llm_router.py`, and optional satellites (`global_memory.py`, `code_sandbox.py`, `web_search.py`, `document_rag.py`, `oauth_connector.py`, `progressive_intelligence.py`, `proactive_monitor.py`).
- **Database:** SQLite at `.agents/agentharness/memory/runs_v3.db`.
- **Agent plane:** Base44 skill files in `.agents/agents/projects/**` plus local ArchonHub orchestration.
- **Client plane:** SwiftUI app and Apple Watch companion.
- **Auth:** JWT Bearer with seeded admin credentials (`admin / ArchonHub2024!`) and optional X-API token fallback for API/WebSocket automation.

## Documentation Map

### Architecture
- [Architecture overview](architecture/overview.md)
- [Database schema](architecture/database-schema.md)

### API
- [Authentication](api/authentication.md)
- [Agents, runs, and queue](api/agents.md)
- [Inez](api/inez.md)
- [Global memory](api/memory.md)
- [Sandbox](api/sandbox.md)
- [Intelligence](api/intelligence.md)
- [Email cleanup](api/email.md)
- [Documents + knowledge + files](api/documents.md)
- [Briefing](api/briefing.md)
- [Scheduler](api/scheduler.md)
- [Automations](api/automations.md)
- [Todos](api/todos.md)
- [Models](api/models.md)
- [Search](api/search.md)
- [Feedback](api/feedback.md)
- [Reports](api/reports.md)
- [Connectors](api/connectors.md)
- [WebSocket](api/websocket.md)
- [Endpoint reference](api/reference.md)

### Features
- [Global memory](features/global-memory.md)
- [Progressive intelligence](features/progressive-intelligence.md)
- [Code sandbox](features/code-sandbox.md)
- [Web search](features/web-search.md)
- [Email cleanup](features/email-cleanup.md)
- [Document RAG](features/document-rag.md)
- [Markets & paper trading](features/markets-trading.md)
- [Morning briefing](features/morning-briefing.md)
- [Microsoft 365 integration](features/m365-integration.md)
- [Feedback learning](features/feedback-learning.md)
- [Proactive monitor](features/proactive-monitor.md)

### Agents
- [Agent system overview](agents/overview.md)
- [Inez](agents/inez.md)
- [Finance CFO](agents/finance-cfo.md)
- [Markets](agents/markets.md)
- [Sigma Signal](agents/sigma-signal.md)
- [Solar marketing](agents/solar-marketing.md)
- [Travel](agents/travel.md)
- [PBS fundraising](agents/pbs-fundraising.md)
- [Grants research](agents/grants-research.md)
- [YEPC grant writer](agents/yepc-grant-writer.md)
- [YEPC project manager](agents/yepc-project-manager.md)

### iOS + watchOS
- [App overview](ios/overview.md)
- [Views](ios/views.md)
- [Models](ios/models.md)
- [HubClient](ios/hubclient.md)
- [watchOS](ios/watchos.md)

### Contracts
- [Agent output contract](contracts/agent-output-contract.md)
- [API response contract](contracts/api-response-contract.md)
- [Memory fact contract](contracts/memory-fact-contract.md)
- [Sandbox contract](contracts/sandbox-contract.md)
- [Intelligence contract](contracts/intelligence-contract.md)
- [Dispatch contract](contracts/dispatch-contract.md)
- [WebSocket contract](contracts/websocket-contract.md)

### Deployment
- [Local setup](deployment/local.md)
- [Docker](deployment/docker.md)
- [Environment variables](deployment/environment.md)

## Recommended Reading Paths

### If you are onboarding to the backend
- Start with [architecture/overview.md](architecture/overview.md).
- Then review [architecture/database-schema.md](architecture/database-schema.md).
- Use [api/reference.md](api/reference.md) as the directory of live routes.
- Dive into feature-specific API pages only after the broad map makes sense.

### If you are building a client
- Read [contracts/api-response-contract.md](contracts/api-response-contract.md).
- Read [contracts/websocket-contract.md](contracts/websocket-contract.md).
- Use [ios/models.md](ios/models.md) to mirror the current Swift contracts.
- Review [api/authentication.md](api/authentication.md), [api/inez.md](api/inez.md), [api/memory.md](api/memory.md), and [api/documents.md](api/documents.md) first.

### If you are extending the agent system
- Review [agents/overview.md](agents/overview.md).
- Review [features/progressive-intelligence.md](features/progressive-intelligence.md).
- Review [contracts/agent-output-contract.md](contracts/agent-output-contract.md).
- Cross-check the relevant skill file under `.agents/agents/projects/**` before changing prompt behavior.

## Key Runtime Paths

| Path | Purpose |
| --- | --- |
| `.agents/agentharness/app/v3/hub_server.py` | App factory — lifespan, CORS, router registration, `/ws` endpoint (~245 lines) |
| `.agents/agentharness/app/v3/core/` | Shared internals: config, database, auth, HubServer class, Pydantic models |
| `.agents/agentharness/app/v3/routers/` | 28 domain APIRouter files (agents, runs, inez, memory, connectors, …) |
| `.agents/agentharness/app/v3/hub_db.py` | SQLite schema migrations (legacy layer called by core/database.py) |
| `.agents/agentharness/memory/runs_v3.db` | Main local SQLite database |
| `.agents/agentharness/memory/*.txt` | Per-agent local memory snapshots |
| `.agents/agents/projects/**` | Skill files / system prompts for agents |
| `projects/archonhub-ios/ArchonHub` | iOS SwiftUI app |
| `projects/archonhub-ios/ArchonHubWatch` | watchOS companion app |

## High-Level Feature Inventory

- Global Memory with category-based fact storage and prompt injection.
- Progressive Intelligence with reflexion scoring, auto-memory, skill progression, and interaction pattern detection.
- Secure code execution sandbox with Docker-first isolation and a subprocess fallback.
- Document upload, parsing, chunking, embedding, and vector search via ChromaDB + OpenAI embeddings.
- SerpAPI-backed web search with citation formatting.
- Email cleanup planning and execution via IMAP/OAuth connectors.
- Daily briefing and monitoring jobs scheduled with APScheduler.
- Model catalog and task-based routing across OpenAI, Anthropic, Gemini, Groq, Perplexity, GitHub Models, and Ollama.
- Feedback collection and preference learning for future response shaping.
- Paper trading tables and reporting hooks for market workflows.

## Accuracy Notes

- The docs prefer the current Python source over older README prose when they disagree.
- Product-level contract details requested by stakeholders are preserved, but mismatches with current code are called out explicitly when necessary.
- Some optional modules fail closed when missing dependencies or API keys; those runtime conditions are documented as implementation notes rather than guaranteed capabilities.

## Source References

- `.github/copilot-instructions.md`
- `README.md`
- `.agents/agentharness/app/v3/hub_server.py`
- `.agents/agentharness/app/v3/hub_db.py`
- `projects/archonhub-ios/README.md`
