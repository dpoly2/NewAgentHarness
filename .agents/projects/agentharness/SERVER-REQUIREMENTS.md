# AgentHarness Hub — Server Platform Requirements
## PRD v1.0 — Full Specification

**Date:** 2026-05-28
**Status:** Requirements — Pending Approval
**Preceded by:** SERVER-CONCEPT.md
**Affects:** main_m365.py (desktop client), new hub_server.py (server)

---

## Part 1 — Project Overview

### 1.1 Goal
Build a lightweight local server process ("AgentHarness Hub") that handles agent execution, scheduling, persistence, and event streaming — freeing the desktop app to focus purely on display and control. The result mirrors how Base44's online agent platform works: a persistent backend that runs regardless of whether the UI is open.

### 1.2 Non-Goals
- This is NOT a cloud deployment. The Hub runs on David's local Windows machine.
- The desktop app is NOT deprecated. All current features remain intact.
- No external database. SQLite only.
- No authentication/security layer in Phase 1 (localhost only).
- No paid hosted infrastructure in Phase 1.

### 1.3 Success Criteria
- Hub starts in under 3 seconds
- Agent run submitted from desktop appears in Hub queue within 200ms
- WebSocket event reaches desktop within 100ms of being fired by Hub
- Desktop app works fully (fallback mode) when Hub is offline
- Scheduled tasks fire within 5 seconds of their target time when Hub is running
- 3 agents can run in parallel without deadlock or data corruption

---

## Part 2 — Hub Server Requirements

### 2.1 Process Model

**REQ-HUB-01:** Hub server SHALL be a single Python process running FastAPI + Uvicorn on `localhost:8765`.

**REQ-HUB-02:** Hub SHALL support three startup modes:
- `a` — Direct process: `python hub_server.py` (development/testing)
- `b` — Windows Service: registered via `pywin32`, starts on Windows boot
- `c` — WSL systemd: for users running WSL2 (bonus, not Phase 1 blocker)

**REQ-HUB-03:** Hub startup SHALL complete initialization in under 3 seconds including:
- SQLite schema validation / migration
- APScheduler initialization and job reload from DB
- WebSocket server binding
- Loading all pending scheduled runs

**REQ-HUB-04:** Hub SHALL write a PID file to `.agents/data/hub.pid` on start and remove it on clean shutdown.

**REQ-HUB-05:** Hub SHALL expose `GET /api/health` that returns:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 3847,
  "active_runs": 2,
  "queue_depth": 1,
  "db_run_count": 847,
  "scheduler_jobs": 4
}
```

---

### 2.2 REST API — Agent Runs

**REQ-API-01:** `POST /api/run/submit`
Request body:
```json
{
  "agent_id": "grant-writer-agent",
  "project": "grants",
  "graph": "research",
  "task": "Find USDA rural development grants for youth athletic facilities",
  "max_revisions": 2,
  "priority": "normal"
}
```
Response:
```json
{
  "job_id": "a3f8b2c1",
  "status": "queued",
  "position": 2,
  "estimated_start_seconds": 45
}
```

**REQ-API-02:** `GET /api/run/{job_id}` — returns full run record including status, output, score, critique, node trace.

**REQ-API-03:** `DELETE /api/run/{job_id}` — cancels a queued or running job. Running jobs receive a cancellation signal; queued jobs are removed immediately.

**REQ-API-04:** `GET /api/runs` — list runs with filters:
- `?status=complete|running|queued|failed`
- `?agent_id=grant-writer-agent`
- `?project=grants`
- `?limit=50&skip=0`
- `?since=2026-05-01` (ISO date)

**REQ-API-05:** `GET /api/runs/stats` — returns per-agent aggregates:
```json
{
  "grant-writer-agent": { "runs": 12, "avg_score": 0.84, "last_run": "2026-05-28T08:00:00" },
  ...
}
```

**REQ-API-06:** `GET /api/runs/briefing` — returns pre-computed morning briefing data (see REQ-SCHED-05):
```json
{
  "generated_at": "2026-05-28T06:50:00",
  "total_runs": 847,
  "agents_total": 45,
  "passing_agents": 31,
  "flagged_agents": ["xftc-qa-agent", "social-analyst"],
  "flagged_details": [...],
  "top_todos": [...],
  "blockers": [...],
  "active_scheduled": 4,
  "last_24h_runs": 7
}
```

---

### 2.3 REST API — Skills

**REQ-API-10:** `GET /api/skills/{agent_id}` — returns latest skill content, version number, avg score.

**REQ-API-11:** `PUT /api/skills/{agent_id}` — manually update a skill file (from desktop editor). Body: `{ "content": "...", "version": 3 }`.

**REQ-API-12:** `GET /api/skills` — list all agents with their current skill version and avg score.

---

### 2.4 REST API — Todos

**REQ-API-20:** `GET /api/todos` — returns all todos, supports `?status=pending|done&priority=urgent|high|medium|low`.

**REQ-API-21:** `POST /api/todos` — create todo. Body mirrors current todos.json schema.

**REQ-API-22:** `PATCH /api/todos/{id}` — update status, priority, title.

**REQ-API-23:** `DELETE /api/todos/{id}` — delete todo.

**REQ-API-24:** Todos SHALL be stored in Hub SQLite (not todos.json file). Desktop app reads/writes via API. Local todos.json kept as offline fallback only.

---

### 2.5 REST API — Scheduler

**REQ-API-30:** `GET /api/scheduler/jobs` — list all scheduled runs:
```json
[
  {
    "id": "sched-001",
    "agent_id": "grant-writer-agent",
    "cron": "0 8 * * 1",
    "run_type": "weekly",
    "next_fire": "2026-06-01T08:00:00",
    "status": "active"
  }
]
```

**REQ-API-31:** `POST /api/scheduler/add` — add a new scheduled run:
```json
{
  "agent_id": "social-content-strategist",
  "graph": "reflexion",
  "task": "Generate weekly content calendar for LEBC",
  "run_type": "weekly",
  "scheduled_at": "2026-06-02T09:00:00",
  "repeat": true
}
```

**REQ-API-32:** `DELETE /api/scheduler/{id}` — cancel/remove a scheduled job.

**REQ-API-33:** `PATCH /api/scheduler/{id}` — update next fire time or enable/disable.

---

### 2.6 REST API — Notifications

**REQ-API-40:** `GET /api/notifications?limit=100` — return notification history.

**REQ-API-41:** `POST /api/notifications/push` — manually push a notification to all connected desktop clients via WebSocket.

**REQ-API-42:** `DELETE /api/notifications` — clear notification history.

---

### 2.7 REST API — Hub Control

**REQ-API-50:** `GET /api/health` — described in REQ-HUB-05.

**REQ-API-51:** `POST /api/queue/pause` — pause job queue (no new runs start; queued jobs wait).

**REQ-API-52:** `POST /api/queue/resume` — resume paused queue.

**REQ-API-53:** `GET /api/config` — return current Hub configuration (thread pool size, scheduler status, active providers).

**REQ-API-54:** `PATCH /api/config` — update Hub config live (e.g. change thread pool size from 3 to 5 without restarting).

---

## Part 3 — WebSocket Requirements

### 3.1 Connection

**REQ-WS-01:** WebSocket endpoint: `ws://localhost:8765/ws`

**REQ-WS-02:** Hub SHALL support multiple simultaneous WebSocket clients (e.g. desktop app + phone web UI + admin panel).

**REQ-WS-03:** On new client connection, Hub SHALL immediately send current state snapshot:
```json
{
  "type": "state_snapshot",
  "active_runs": [...],
  "queue_depth": 2,
  "scheduler_jobs": 4,
  "hub_version": "1.0.0"
}
```

**REQ-WS-04:** Hub SHALL send a heartbeat ping every 30 seconds. Clients that don't respond within 10 seconds are disconnected.

### 3.2 Event Types (Hub → Client)

**REQ-WS-10:** `run_queued` — job added to queue
```json
{ "type": "run_queued", "job_id": "a3f8b2c1", "agent_id": "...", "position": 2 }
```

**REQ-WS-11:** `run_started` — job dequeued and execution begun
```json
{ "type": "run_started", "job_id": "a3f8b2c1", "agent_id": "...", "graph": "reflexion" }
```

**REQ-WS-12:** `node_update` — a graph node completed
```json
{ "type": "node_update", "job_id": "...", "node": "act|evaluate|revise|save", "status": "running|complete|failed", "data": { "score": 0.87 } }
```

**REQ-WS-13:** `run_complete` — run finished successfully
```json
{ "type": "run_complete", "job_id": "...", "score": 0.87, "critique": "...", "output_preview": "first 200 chars..." }
```

**REQ-WS-14:** `run_failed` — run encountered an unrecoverable error
```json
{ "type": "run_failed", "job_id": "...", "error": "OpenAI rate limit exceeded" }
```

**REQ-WS-15:** `run_cancelled` — run was cancelled by user
```json
{ "type": "run_cancelled", "job_id": "..." }
```

**REQ-WS-16:** `notif` — push notification for display in desktop drawer
```json
{ "type": "notif", "text": "...", "color": "#22c55e", "category": "run|todo|system|chat" }
```

**REQ-WS-17:** `scheduler_fired` — a scheduled job was triggered
```json
{ "type": "scheduler_fired", "job_id": "...", "agent_id": "...", "scheduled_at": "..." }
```

**REQ-WS-18:** `briefing_ready` — morning briefing pre-compute finished
```json
{ "type": "briefing_ready", "generated_at": "..." }
```

**REQ-WS-19:** `todo_update` — a todo was created/modified/deleted (allows multi-client sync)
```json
{ "type": "todo_update", "action": "create|update|delete", "todo": {...} }
```

### 3.3 Events (Client → Hub)

**REQ-WS-20:** `subscribe_run` — client subscribes to updates for a specific job
```json
{ "type": "subscribe_run", "job_id": "a3f8b2c1" }
```

**REQ-WS-21:** `cancel_run` — client requests cancellation
```json
{ "type": "cancel_run", "job_id": "a3f8b2c1" }
```

**REQ-WS-22:** `ping` / `pong` — heartbeat response

---

## Part 4 — Job Queue & Execution Engine

### 4.1 Queue

**REQ-QUEUE-01:** Hub SHALL maintain an in-memory FIFO job queue backed by `asyncio.Queue`.

**REQ-QUEUE-02:** Queue SHALL support priority levels: `urgent`, `normal`, `low`. Urgent jobs jump ahead of normal and low.

**REQ-QUEUE-03:** Queue depth SHALL be persisted to SQLite so jobs survive a Hub restart (status = `queued` in DB).

**REQ-QUEUE-04:** On Hub startup, all jobs with status `queued` in DB SHALL be reloaded into the in-memory queue.

**REQ-QUEUE-05:** Queue SHALL expose current depth and per-priority counts via `/api/health`.

### 4.2 Thread Pool

**REQ-EXEC-01:** Hub SHALL use a `ThreadPoolExecutor` with configurable worker count (default: 3, range: 1-10).

**REQ-EXEC-02:** Each worker runs one LangGraph graph (reflexion / research / wordpress / business-law).

**REQ-EXEC-03:** Workers SHALL be isolated — one agent's failure SHALL NOT affect other workers.

**REQ-EXEC-04:** Each LangGraph execution runs the EXACT SAME node functions as the current desktop app (node_act, node_evaluate, node_revise, node_save). These functions are shared code, not duplicated.

**REQ-EXEC-05:** Workers SHALL emit WebSocket events at each node transition (REQ-WS-12).

**REQ-EXEC-06:** Cancellation SHALL be implemented via a `threading.Event` cancel flag checked between nodes. A running node_act cannot be interrupted mid-LLM-call, but the loop stops before the next node.

### 4.3 Error Handling

**REQ-EXEC-10:** OpenAI rate limit errors (429) SHALL trigger exponential backoff: 5s, 10s, 20s, then fail.

**REQ-EXEC-11:** Network errors during LLM calls SHALL retry up to 3 times before marking run as failed.

**REQ-EXEC-12:** All failures SHALL be stored in DB with status `failed` and the error message.

**REQ-EXEC-13:** Failed runs SHALL emit `run_failed` WebSocket event.

**REQ-EXEC-14:** Hub SHALL log all errors to `.agents/data/logs/hub_YYYY-MM-DD.log`.

---

## Part 5 — Scheduler Requirements

**REQ-SCHED-01:** Hub SHALL use APScheduler with SQLAlchemyJobStore backed by the Hub SQLite DB.

**REQ-SCHED-02:** Scheduler SHALL support three trigger types:
- `date` — one-time at a specific datetime
- `cron` — standard cron expression (5-field)
- `interval` — every N minutes/hours/days

**REQ-SCHED-03:** All scheduled runs from `.agents/data/scheduled_runs.json` SHALL be migrated into APScheduler on Hub first start.

**REQ-SCHED-04:** When a scheduled job fires, it submits to the job queue (not bypassing concurrency control).

**REQ-SCHED-05:** Hub SHALL pre-schedule a daily briefing compute job at `06:50 AM CT` (results ready before David opens the app at 7 AM). Output cached in memory and served by `/api/runs/briefing`.

**REQ-SCHED-06:** Built-in recurring jobs (all migrated from current Base44 automations):
| Job | Schedule | Agent |
|-----|----------|-------|
| Grant & Funding Research Sweep | Monday 8:00 AM CT | grants-research-agent |
| Morning Briefing Pre-compute | Daily 6:50 AM CT | (internal — no LLM) |
| Weekly Fare Alert | Monday 1:30 PM CT | travel-project-lead |
| Sigma Signal Submission Check | Daily 2:00 PM CT | sigma-signal-submissions |
| Daily Reflexion Report | Daily 7:00 AM CT | (internal report) |

**REQ-SCHED-07:** Scheduler SHALL emit `scheduler_fired` WebSocket event whenever a job fires, even if the desktop app is closed (stored in notification history for next session).

---

## Part 6 — Database Requirements

### 6.1 Schema

**REQ-DB-01:** Hub uses the EXISTING `runs_v3.db` SQLite file (no migration needed for existing `runs` and `skills` tables).

**REQ-DB-02:** New tables added by Hub:

```sql
-- Job queue persistence
CREATE TABLE IF NOT EXISTS job_queue (
    id          TEXT PRIMARY KEY,
    agent_id    TEXT NOT NULL,
    project     TEXT,
    graph       TEXT DEFAULT 'reflexion',
    task        TEXT NOT NULL,
    priority    TEXT DEFAULT 'normal',
    status      TEXT DEFAULT 'queued',  -- queued|running|complete|failed|cancelled
    max_revisions INTEGER DEFAULT 2,
    queued_at   TEXT NOT NULL,
    started_at  TEXT,
    completed_at TEXT,
    job_data    TEXT  -- JSON blob for full run config
);

-- Todos (migrated from todos.json)
CREATE TABLE IF NOT EXISTS todos (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    priority    TEXT DEFAULT 'medium',  -- urgent|high|medium|low
    status      TEXT DEFAULT 'pending', -- pending|done
    project     TEXT,
    due_date    TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT
);

-- Notifications history
CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    text        TEXT NOT NULL,
    color       TEXT,
    category    TEXT DEFAULT 'system',
    created_at  TEXT NOT NULL,
    read        INTEGER DEFAULT 0
);

-- Hub config key/value store
CREATE TABLE IF NOT EXISTS hub_config (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TEXT
);
```

**REQ-DB-03:** Hub SHALL use WAL (Write-Ahead Logging) mode for SQLite to allow simultaneous reads from the desktop app without locking.

**REQ-DB-04:** Hub SHALL run a nightly cleanup job at 2:00 AM removing runs older than 90 days (configurable).

---

## Part 7 — Desktop Client Changes

### 7.1 Hub Connection Manager

**REQ-CLIENT-01:** Desktop app SHALL include a `HubClient` class that:
- Tries to connect to `ws://localhost:8765/ws` on startup (3s timeout)
- If connected: routes all run submissions, data reads, and notifications through Hub
- If not connected: falls back to current embedded execution mode
- Shows Hub status in the status bar: `Hub: Online ●` or `Hub: Offline ○`
- Reconnects automatically every 30 seconds when Hub is offline

**REQ-CLIENT-02:** All REST calls SHALL use `httpx` (async-compatible) with a 5-second timeout.

**REQ-CLIENT-03:** Desktop SHALL detect Hub coming online mid-session and switch from fallback to Hub mode without restart.

### 7.2 Run View Changes

**REQ-CLIENT-10:** When Hub is online, clicking ▶ Run SHALL:
1. Call `POST /api/run/submit`
2. Show "Queued (position: N)" immediately
3. Listen on WebSocket for `run_started` → activate pipeline diagram
4. Listen for `node_update` events → highlight nodes in real-time
5. Listen for `run_complete` → show score, output, push notification

**REQ-CLIENT-11:** When Hub is offline, ▶ Run SHALL behave exactly as it does today (embedded LangGraph in thread).

**REQ-CLIENT-12:** The pipeline canvas diagram SHALL animate from WebSocket `node_update` events when Hub is online, replacing the current `_poll_log` SQLite polling.

### 7.3 Tasks View Changes

**REQ-CLIENT-20:** When Hub is online, Tasks view SHALL:
- Fetch running/queued jobs from `GET /api/runs?status=running,queued`
- Subscribe to WebSocket for live updates
- Show "Cancel" button that calls `DELETE /api/run/{id}`
- Show Hub queue depth as a badge: "Queue: 3"

**REQ-CLIENT-21:** Completed runs section reads from `GET /api/runs?status=complete&limit=100`.

### 7.4 Morning Briefing Changes

**REQ-CLIENT-30:** Briefing card SHALL call `GET /api/runs/briefing` when Hub is online.
**REQ-CLIENT-31:** Briefing SHALL refresh when `briefing_ready` WebSocket event is received.
**REQ-CLIENT-32:** When Hub is offline, Briefing falls back to computing locally from SQLite (current behavior).

### 7.5 Notification Drawer Changes

**REQ-CLIENT-40:** When Hub is online, notification drawer SHALL subscribe to WebSocket `notif` events (replaces current `_push_notif` calls from threads).
**REQ-CLIENT-41:** Notification history SHALL load from `GET /api/notifications` on panel open.
**REQ-CLIENT-42:** "Export log" SHALL call Hub API to get full history.

### 7.6 New: Hub Control Panel (in Admin view)

**REQ-CLIENT-50:** Admin view SHALL include a "Hub" tab with:
- Hub status (online/offline), uptime, version
- Active runs list with Cancel buttons
- Queue depth + pause/resume queue controls
- Thread pool size slider (1-10)
- Scheduled jobs list with next fire time + Cancel buttons
- "Start Hub" / "Stop Hub" buttons (launches/kills hub_server.py subprocess)
- Hub log viewer (tail of `.agents/data/logs/hub_*.log`)
- "Launch as Windows Service" button

---

## Part 8 — New File Structure

```
AgentHarness/
├── .agents/
│   ├── agentharness/
│   │   └── app/
│   │       └── v3/
│   │           ├── main_m365.py          (desktop client — modified)
│   │           ├── hub_server.py         (NEW — FastAPI server)
│   │           ├── hub_client.py         (NEW — HubClient class for desktop)
│   │           ├── hub_nodes.py          (NEW — shared LangGraph nodes, extracted from main_m365.py)
│   │           ├── hub_scheduler.py      (NEW — APScheduler setup + built-in jobs)
│   │           ├── hub_db.py             (NEW — Hub SQLite schema + helpers)
│   │           ├── hub_start.ps1         (NEW — Windows start script for Hub)
│   │           ├── hub_install_service.ps1 (NEW — Windows service registration)
│   │           ├── install.ps1           (UPDATED — installs Hub dependencies too)
│   │           ├── install.sh            (UPDATED)
│   │           ├── requirements.txt      (UPDATED — adds fastapi, uvicorn, apscheduler, httpx)
│   │           └── start.ps1             (starts BOTH Hub and Desktop)
│   └── data/
│       ├── runs_v3.db                    (EXISTING — Hub adds new tables)
│       ├── hub.pid                       (NEW — Hub process ID)
│       ├── todos.json                    (DEPRECATED after Hub — kept as fallback)
│       ├── scheduled_runs.json           (DEPRECATED after Hub — migrated to APScheduler)
│       └── logs/
│           ├── hub_2026-05-28.log        (NEW — Hub daily log)
│           └── notif-log-*.txt           (EXISTING)
```

---

## Part 9 — Implementation Phases

### Phase 1 — Hub Core + WebSocket (Priority: HIGH)
**Scope:** Get the Hub running and the desktop talking to it.
1. Create `hub_db.py` — schema + helpers for new tables
2. Create `hub_nodes.py` — extract node functions from main_m365.py (shared code)
3. Create `hub_server.py` — FastAPI app, job queue, thread pool, WebSocket
4. Implement REST endpoints: `/api/run/submit`, `/api/runs`, `/api/health`
5. Implement WebSocket: `run_started`, `node_update`, `run_complete`, `notif`
6. Create `hub_client.py` — HubClient class with fallback mode
7. Patch `main_m365.py` — use HubClient for ▶ Run, animate pipeline from WS events
8. Update `install.ps1` + `requirements.txt` — add new dependencies
9. Write `hub_start.ps1`
**Test:** Hub starts, Desktop connects, agent run submitted, pipeline animates live, result appears.

### Phase 2 — Scheduler Migration (Priority: HIGH)
**Scope:** Always-on scheduled runs.
1. Create `hub_scheduler.py` — APScheduler setup, job store in SQLite
2. Migrate `.agents/data/scheduled_runs.json` → APScheduler on Hub start
3. Implement built-in recurring jobs (grant sweep, briefing compute, reflexion report)
4. REST endpoints: `/api/scheduler/*`
5. WebSocket events: `scheduler_fired`
6. Desktop Hub Control Panel tab in Admin view
7. Desktop Scheduler modal uses Hub API instead of local JSON
**Test:** Close desktop app, Hub fires scheduled grant sweep at 8 AM Monday, results in DB.

### Phase 3 — Todos + Notifications via Hub (Priority: MEDIUM)
**Scope:** Move Todos and notification history to Hub.
1. Migrate `todos.json` → Hub SQLite `todos` table
2. REST endpoints: `/api/todos/*`
3. Desktop Todos view reads/writes via HubClient (fallback: local JSON)
4. Notifications history stored in Hub SQLite
5. REST endpoints: `/api/notifications`
6. Desktop notification drawer reads from Hub
7. WebSocket `todo_update` events for multi-client sync
**Test:** Create todo in desktop, read from Hub API via curl, delete from API, desktop reflects change.

### Phase 4 — Windows Service + Always-On (Priority: MEDIUM)
**Scope:** Hub runs automatically at Windows boot.
1. Create `hub_install_service.ps1` — registers Hub as Windows service via pywin32
2. Hub writes/reads `hub.pid`
3. Desktop "Start Hub" / "Stop Hub" buttons in Admin
4. Hub log viewer in Admin
5. Hub survives desktop app close + Windows lock without stopping
6. Graceful shutdown handler (SIGTERM → drain queue → stop)
**Test:** Reboot Windows, open desktop, Hub is already online, pending runs resumed.

### Phase 5 — Parallel Agents + Advanced Features (Priority: LOW)
**Scope:** Multi-agent concurrency and future-proofing.
1. Thread pool default raised to 3, configurable to 10
2. Tasks view shows all 3 parallel runs simultaneously
3. Morning briefing fetched from Hub `/api/runs/briefing`
4. Remote access prep: Hub bind address configurable (localhost → 0.0.0.0 for Tailscale)
5. Simple read-only web dashboard served by Hub at `http://localhost:8765/`
6. Webhook endpoint: `POST /api/webhook/run` for external triggers
**Test:** Submit 3 agent runs simultaneously, all appear in Tasks view with live node updates.

---

## Part 10 — Updated Requirements.txt (Hub additions)

```
# Existing (unchanged)
langgraph>=0.2.0
langchain>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.1.0
langchain-community>=0.3.0
openai>=1.0.0
pydantic>=2.0.0
sqlite-utils>=3.35.0
requests>=2.31.0
python-dotenv>=1.0.0
python-dateutil>=2.8.0
markdown>=3.5

# Hub server additions
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
apscheduler>=3.10.0
websockets>=12.0
httpx>=0.27.0
pywin32>=306; platform_system=="Windows"
```

---

## Part 11 — Open Questions / Decisions Needed

| # | Question | Default Assumption | Needs David's Input |
|---|----------|-------------------|---------------------|
| 1 | Hub port | 8765 | Change if conflicts |
| 2 | Thread pool default size | 3 | More = more OpenAI cost |
| 3 | Windows Service vs background process for Phase 1 | Background process | Service in Phase 4 |
| 4 | Migrate todos.json in Phase 1 or Phase 3 | Phase 3 | — |
| 5 | Daily cleanup threshold | 90 days | Adjust as needed |
| 6 | Remote access (Tailscale) | Phase 5, optional | Confirm if desired |
| 7 | Built-in jobs: run all 5 on Hub or keep some on Base44 | Hub handles them all | Confirm |
| 8 | Max revisions default | 2 (current) | — |
| 9 | OpenAI API key: Hub reads from .env | Yes | — |

---

*AgentHarness Hub — Requirements v1.0 | 2026-05-28 | AgentJames*
