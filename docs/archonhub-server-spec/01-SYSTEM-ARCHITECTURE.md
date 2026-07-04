# 01-SYSTEM-ARCHITECTURE

_Generated from the current ArchonHub source tree on 2026-07-03._

## Scope

This spec covers the local ArchonHub server implemented under `D:\projects\NewAgentHarness\.agents\agentharness\app\v3\`. It documents the shipped FastAPI hub, the DB-backed run queue, the LangGraph execution layer, the Inez orchestration path, and the live SQLite schema at `D:\projects\NewAgentHarness\.agents\agentharness\memory\runs_v3.db`.

## System shape

- **HTTP surface:** `hub_server.py` mounts **34** `APIRouter` modules under `/api` and exposes `/ws` separately.
- **Route volume:** the mounted routers contain **214** HTTP route decorators; adding `/` and `/ws` yields **216** externally reachable transport surfaces.
- **Static UI:** `/` redirects to `/web`, which serves the bundled dashboard from `web\`.
- **Execution plane:** background jobs are queued into `job_queue`, claimed by DB workers, executed via `hub_nodes.run_graph()`, and mirrored to `runs`, `run_events`, and `ws_events`.
- **Interactive plane:** Inez handles live conversation turns through `/api/inez/chat`, emits progress over websocket + `run_events`, and can dispatch specialist agents through `agent_runner.py`.

## Boot and process model

`hub_server.py` does more than create a FastAPI app:

1. Initializes schema with `core.database._init_schema()`.
2. Rejects insecure startup unless explicitly overridden when `JWT_SECRET` or `ADMIN_PASSWORD` still use default values.
3. Registers the worker node in `worker_nodes` before work starts.
4. Starts **5 DB worker coroutines per server process**.
5. Starts a heartbeat loop, stale-job reaper, websocket fan-out loop, and scheduler lease loop.
6. Builds APScheduler jobs but only starts them in the process that owns the scheduler lease.

The default `__main__` path launches **5 Uvicorn worker processes**. Because each process creates five DB-polling worker coroutines, concurrency is coordinated at the database level rather than through a single in-process queue.

## Concurrency and executors

Inside each `HubServer` instance (`core\hub.py`):

- `_executor = ThreadPoolExecutor(max_workers=3)` handles background graph runs.
- `_inez_executor = ThreadPoolExecutor(max_workers=2)` reserves capacity for interactive Inez chat turns.
- `_active_runs` holds cancel flags for live jobs.
- `_clients` tracks connected websocket clients for this process.
- Scheduler leadership uses a DB lease with **30-second TTL** and **10-second renewal**.

## Major code modules

| Area | Primary files | Role |
| --- | --- | --- |
| App shell | `hub_server.py` | App factory, lifespan, CORS, `/`, `/ws`, router mounting |
| Shared core | `core\config.py`, `core\database.py`, `core\auth.py`, `core\hub.py`, `core\models.py` | Configuration, auth, DB access, worker loops, Pydantic models |
| HTTP routers | `routers\*.py` | Domain endpoints under `/api` |
| Graph runtime | `hub_nodes.py`, `graphs\reflexion_loop.py` | LangGraph node wiring and graph selection |
| Interactive orchestration | `inez_agent.py`, `agent_runner.py` | Inez reasoning, specialist dispatch, synthesis, memory writes |
| Scheduling | `hub_scheduler.py` | Built-in cadence + user job loading |
| Durable runtime logs | `run_events.py`, `progressive_intelligence.py` | Replayable events, reflexion tracking |

## Request/Run lifecycle

### HTTP run submission

1. `POST /api/runs` validates a `RunRequest`.
2. `HubServer.submit_job()` writes the payload into `job_queue` and emits a `run_queued` websocket event.
3. A DB worker claims the job, creates a cancellation flag, emits `run_started`, and executes `hub_nodes.run_graph()` in `_executor`.
4. The graph persists results into `runs`, updates `job_queue`, and emits `run_completed` or `run_cancelled`.

### Interactive Inez turn

1. `/api/inez/chat` accepts a user message.
2. Inez pre-screens with AgentShield.
3. Optional prefetches run (travel, email read/send, web search).
4. Inez performs the main LLM reasoning pass and may produce dispatch JSON.
5. If specialists are dispatched, `run_dispatches()` executes the first wave in parallel and optionally a single follow-up depth.
6. Inez synthesizes specialist results, persists todos/memory/patterns, and emits `inez_response`.

## Storage model at a glance

The live SQLite DB contains **62 raw tables** in `sqlite_master`; **61** of those are application-owned and **1** (`sqlite_sequence`) is SQLite internal bookkeeping. Major storage domains are:

- execution/runtime (`job_queue`, `runs`, `worker_nodes`, `ws_events`, `run_events`)
- agent registry and memory (`agent_registry`, `agent_memory`, `skills`, `agent_skill_levels`)
- collaboration/content (`conversations`, `messages`, `documents`, `knowledge_base`, `prompt_templates`)
- operations (`scheduled_jobs`, `notifications`, `todos`, `reports`, `implementation_plans`)
- market/trading (`alpaca_orders`, `tracked_politicians`, `copy_trade_signals`, `market_*`)
- file search (`uploaded_files`, `file_chunks`, `messages_fts*`)

## Router inventory

| Mounted group | Routes |
| --- | ---: |
| Hub entrypoints (`/`, `/ws`) | 2 |
| Authentication | 4 |
| Runs and queue | 6 |
| Todos | 5 |
| Notifications | 5 |
| Trips | 5 |
| Connectors and OAuth | 12 |
| Projects and clients | 10 |
| Conversations | 4 |
| DevOps | 1 |
| Agents | 8 |
| Automations | 9 |
| Scheduler | 4 |
| Skills | 3 |
| Memory | 8 |
| GOAP planning | 1 |
| Inez orchestration | 7 |
| Briefing and briefs | 6 |
| Search, events, and context | 3 |
| Prompt templates | 5 |
| Knowledge, documents, and integrations | 14 |
| Files | 7 |
| Feedback and corrections | 5 |
| Email cleanup | 6 |
| Reports | 5 |
| Models | 4 |
| Sandbox | 2 |
| Intelligence | 4 |
| Users | 5 |
| Config, stats, health, and briefing | 6 |
| Providers and import | 3 |
| Plans | 15 |
| Alpaca brokerage | 15 |
| Capitol Trades | 14 |
| Web search | 3 |

## Source references

- `.agents\agentharness\app\v3\hub_server.py`
- `.agents\agentharness\app\v3\core\hub.py`
- `.agents\agentharness\app\v3\core\auth.py`
- `.agents\agentharness\app\v3\hub_nodes.py`
- `.agents\agentharness\app\v3\agent_runner.py`
- `.agents\agentharness\app\v3\inez_agent.py`
