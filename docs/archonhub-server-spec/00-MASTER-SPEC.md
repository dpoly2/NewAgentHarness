# 00-MASTER-SPEC

_Generated from the current ArchonHub source tree on 2026-07-03._

## Project overview

ArchonHub is the server-side control plane for a multi-agent AI operating system. In the current repository it lives at `D:\projects\NewAgentHarness\.agents\agentharness\app\v3\` and acts as the durable runtime behind Inez, specialist agents, scheduled workflows, portfolio memory, and realtime client updates.

Primary users:
- **Operator / principal user** using Inez for orchestration, synthesis, and execution.
- **Administrators** managing models, configs, users, connectors, schedules, and reports.
- **Agents and automations** executing delegated tasks against controlled DB write surfaces.

The current server exposes **34 mounted APIRouter modules**, **214 HTTP endpoints**, and a standalone authenticated **`/ws`** realtime channel.

## Purpose

The server exists to do five jobs reliably:
1. authenticate humans and trusted machine callers;
2. persist all operational state in SQLite;
3. execute agent runs through LangGraph-based reflexion flows;
4. orchestrate multi-agent collaboration through Inez;
5. stream durable progress and status updates to connected clients.

This specification is a rebuild contract for the **server only**. Client applications, dashboards, iOS, watchOS, and future UX layers are explicitly deferred.

## Architecture overview

Current architectural stack:
- **FastAPI** — HTTP routing, dependency-injected auth, OpenAPI surface, WebSocket endpoint.
- **SQLite** — primary operational store for CRUD data, queue state, event logs, FTS, and scheduler coordination.
- **LangGraph / LangChain** — run graphs and reflexion lifecycle.
- **APScheduler** — built-in cadence and user-defined schedules.
- **WebSocket** — DB-backed realtime fan-out using `ws_events`.
- **ThreadPoolExecutor** — background run pool (`_executor`, 3 threads) and interactive Inez pool (`_inez_executor`, 2 threads).

## Key design principles

### Karpathy guidelines as runtime prompt policy
All specialist runs are wrapped with the standing behavioral guidance from `.agents\rules\karpathy-guidelines.md`:
- think before acting;
- prefer the simplest sufficient solution;
- make surgical changes instead of broad refactors;
- define verifiable success criteria.

### Reflexion as a first-class contract
The current server does not treat evaluation as optional reporting. The execution system actively scores outputs and can revise them before persistence.

Scoring rubric from `.agents\rules\agent-logging-protocol.md`:
- `overall = completion * 0.5 + quality * 0.35 + efficiency * 0.15`
- `>= 0.90`: excellent
- `0.75–0.89`: good / minor note
- `0.60–0.74`: review-worthy
- `< 0.60`: poor; revise skill guidance

### Persistence before fan-out
Queue events, socket broadcasts, notifications, and run replay are table-backed. The rebuild must preserve this durability-first posture.

### Server-side safety, not client-side hope
Auth, AgentShield screening, login throttling, WebSocket admission, and DB write whitelisting are enforced in the server.

## Technology decisions and rationale

### FastAPI
Chosen because the existing implementation depends heavily on typed request models, dependency injection (`get_current_user`, `get_admin_user`), async handlers, and a built-in docs surface. A faithful rebuild should keep those advantages.

### SQLite
SQLite currently acts as:
- CRUD database
- job queue backing store
- scheduler lease store
- websocket replay/fan-out log
- run replay log
- FTS5 search index

That consolidation is intentional for the current single-host / small-cluster operating model.

### LangGraph
LangGraph gives the server an explicit execution graph instead of opaque chained helper calls. The key contract is `load_memory -> act -> evaluate -> revise? -> save_memory`.

### APScheduler + DB lease
APScheduler handles time-based triggers, while the DB-backed scheduler lease guarantees only one worker process is authoritative for built-in jobs at a time.

## Non-functional requirements

### Performance
- health checks must stay lightweight;
- queue claiming must remain low-latency;
- Inez must not be starved by background jobs;
- websocket updates must survive client disconnects.

### Security
- JWT HS256, 24-hour lifetime;
- nearly all routes require bearer auth;
- login rate limit: 10 attempts per IP in 5 minutes;
- `/ws` requires auth message within 15 seconds or closes with code 1008;
- AgentShield scans both Inez requests and delegated agent tasks;
- agent DB writes are restricted to an allowlist.

### Scalability
- 5 DB workers per process;
- one scheduler leader at a time;
- durable events shared across workers;
- Postgres seam exists in parts of the code and should not be blocked by the rebuild.

## In scope

- FastAPI app factory and lifespan behavior
- HTTP API contract
- WebSocket contract
- SQLite schema and migration plan
- run queue and worker model
- Inez orchestration pipeline
- LangGraph reflexion pipeline
- scheduler and recurring jobs
- security and operations guidance

## Deferred

- iOS/watch/web/desktop app implementation
- UI redesigns
- non-server product strategy work
- any client-specific rendering concerns

## Glossary

- **agent_id** — canonical runtime identity like `markets-cro` or `inez-chief-of-staff`.
- **skill_file** — Markdown system prompt under `.agents\agents\projects\<project>\<agent>.md`.
- **reflexion loop** — `load_memory -> act -> evaluate -> revise? -> save_memory` execution pattern.
- **dispatch** — one delegated task emitted by Inez for a specialist agent.
- **synthesis** — Inez's second-pass executive summary over agent results.
- **emit** — callback used to publish durable websocket events.
- **hub_config** — key/value configuration and lease table.
- **job_queue** — DB-backed queue of queued/running/cancelled runs.
- **run_events** — durable replay log for Inez and interactive runs.
- **ws_events** — durable websocket fan-out log across worker processes.
- **AgentShield** — safety scanner invoked before orchestration and execution.
- **GOAP plan** — goal-oriented action plan optionally written when Inez dispatches larger work sets.
- **skill badge** — progressive-intelligence metadata injected into prompts.

## Source anchors

This master specification is grounded in:
- `hub_server.py`
- `core\auth.py`, `core\config.py`, `core\database.py`, `core\hub.py`
- `agent_runner.py`, `inez_agent.py`, `hub_nodes.py`, `hub_scheduler.py`
- `.agents\rules\karpathy-guidelines.md`
- `.agents\rules\agent-logging-protocol.md`
