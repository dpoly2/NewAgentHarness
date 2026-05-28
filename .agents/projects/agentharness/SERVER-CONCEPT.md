# AgentHarness v3 — Server Platform Concept
## "AgentHarness Hub" — Hybrid Architecture Design

**Date:** 2026-05-28
**Status:** Concept for Review
**Author:** AgentJames (Chief of Staff)

---

## 1. The Problem with the Current Architecture

AgentHarness v3 is a single-process Tkinter desktop app. Everything runs in one Python process on David's local Windows machine:

```
[Desktop App (main_m365.py)]
    ├── UI rendering (Tkinter — main thread)
    ├── LangGraph nodes (node_act, node_evaluate, node_revise) — blocking LLM calls
    ├── SQLite reads/writes (.agents/data/)
    ├── Live bridge (polls SQLite every 5s — daemon thread)
    ├── Scheduler (polls every 60s — daemon thread)
    ├── AgentMajesty chat (SSE stream — background thread)
    └── Push notifications (HTTP calls — background thread)
```

**Pain points:**
- LLM calls (node_act, node_evaluate, node_revise) take 5-30 seconds each. Even threaded, a reflexion loop with 2 revisions = 9+ LLM round trips. The UI stutters or becomes unresponsive.
- The app must be OPEN and RUNNING for any automation to fire. Close the laptop → everything stops.
- No multi-agent parallelism. Agents run one at a time.
- All state lives on one machine. No backup, no sharing, no history if the DB file is corrupted.
- The scheduled task runner is a 60s polling loop inside a GUI app. It cannot run overnight.
- Base44 handles all of this natively for the online agent — we want to mirror that locally.

---

## 2. The Goal — Mirror How Base44 Works

Base44's online agent works like this:
```
[User Browser] ←→ [Base44 Platform API] ←→ [Agent Runtime]
                         ↑
                   Automations / Webhooks
                   Entity DB (persistent)
                   Scheduled tasks
                   Email / Slack connectors
```

The agent is ALWAYS available. The UI is just a window into a running service.
We want the same model — locally hosted, fully controlled.

---

## 3. The Proposed Architecture — AgentHarness Hub

### Core Principle: **The Desktop App Stays the Desktop App**
The Tkinter UI keeps ALL its views, interactions, and visual features.
We only move the HEAVY COMPUTE and PERSISTENCE to a server process.
The app becomes a **dashboard client** — it displays, controls, and monitors.
The server does the **running, storing, and scheduling**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENTHARNESS HUB                             │
│                   (Hybrid Local Architecture)                        │
├──────────────────────────┬──────────────────────────────────────────┤
│   DESKTOP CLIENT         │   HUB SERVER                             │
│   (main_m365.py)         │   (hub_server.py — FastAPI)              │
│                          │                                          │
│   ✅ All UI views         │   ✅ LangGraph execution engine           │
│   ✅ Morning Briefing     │   ✅ Agent queue + job scheduler          │
│   ✅ Tasks/Todos views    │   ✅ SQLite persistence (shared DB)       │
│   ✅ Agents directory     │   ✅ Skill version management             │
│   ✅ AgentMajesty chat    │   ✅ Reflexion loop (all graph types)     │
│   ✅ Settings             │   ✅ REST API for client                  │
│   ✅ Notification drawer  │   ✅ WebSocket for live streaming         │
│   ✅ Clients view         │   ✅ Scheduled run executor               │
│   ✅ Admin panel          │   ✅ Daily reflexion report generator     │
│                          │   ✅ Push notification dispatch            │
│   Communicates via:      │   ✅ Multi-agent parallel execution       │
│   - REST API calls       │   ✅ Run history + audit log              │
│   - WebSocket stream     │   ✅ .env / secrets management            │
│   - Local HTTP           │                                          │
│   (localhost:8765)       │   Runs as:                               │
│                          │   - Windows Service (always-on)          │
│                          │   - OR background process                │
│                          │   - OR systemd service (WSL)             │
└──────────────────────────┴──────────────────────────────────────────┘
                                    │
                           ┌────────┴────────┐
                           │  SHARED LAYER   │
                           │                 │
                           │  SQLite DB      │
                           │  (runs_v3.db)   │
                           │  .agents/data/  │
                           │  Skill files    │
                           │  .env           │
                           └─────────────────┘
```

### What Moves to the Server (Hub)

| Component | Current Location | Moves To |
|-----------|-----------------|----------|
| LangGraph node execution (Act/Evaluate/Revise/Save) | Desktop thread | Hub server |
| Agent job queue | In-memory list | Hub server (SQLite queue) |
| Task scheduler (60s polling) | Desktop daemon thread | Hub server (APScheduler) |
| Daily reflexion report | Base44 automation | Hub server (scheduled job) |
| Skill version save/load | Direct file read | Hub API |
| Run history persistence | SQLite in-process | Hub SQLite (same file, served via API) |
| Push notification dispatch | Desktop thread | Hub server |
| Multi-agent parallelism | Not possible | Hub server (thread pool) |

### What STAYS in the Desktop App

| Component | Reason to Keep |
|-----------|----------------|
| All Tkinter views | UI is purely local — no reason to move |
| AgentMajesty chat | Lightweight SSE stream — already works in a thread |
| Morning Briefing | Reads from Hub API — stays as display layer |
| Todos (CRUD) | Kept local + synced to Hub |
| Settings / .env editor | Local machine config |
| Skill file viewer/editor | Local file access |
| Notification drawer | Receives events from Hub via WebSocket |

---

## 4. Communication Layer — How They Talk

### REST API (Hub → Client, request/response)
Used for: submitting runs, checking status, reading history, managing todos, getting briefing data.

```
POST   /api/run/submit          — queue a new agent run
GET    /api/run/{id}            — get run status + output
GET    /api/runs?limit=50       — list recent runs
GET    /api/runs/stats           — agent stats for Home view
GET    /api/briefing            — morning briefing data
POST   /api/todos               — create todo
PATCH  /api/todos/{id}          — update todo
DELETE /api/todos/{id}          — delete todo
GET    /api/skills/{agent_id}   — get latest skill for agent
GET    /api/scheduler/list      — list scheduled runs
POST   /api/scheduler/add       — schedule a future run
DELETE /api/scheduler/{id}      — cancel scheduled run
GET    /api/health              — server health + version
```

### WebSocket (Hub → Client, push events)
Used for: live run streaming, node highlights, score updates, new run completion alerts.

```
ws://localhost:8765/ws

Events pushed by server:
  { type: "run_started",   run_id, agent_id, graph }
  { type: "node_update",   run_id, node, status }   ← replaces _poll_log
  { type: "run_complete",  run_id, score, critique, output }
  { type: "run_failed",    run_id, error }
  { type: "notif",         text, color, category }
  { type: "briefing_refresh" }                       ← server triggers Home refresh
  { type: "scheduler_fired", run_id, agent_id }
```

### Why Not Just a Shared SQLite File?
The current live bridge polls SQLite every 5 seconds. This works but:
- No real-time push (5s lag minimum)
- SQLite has write contention when server and client both write simultaneously
- No ability to run on a different machine in the future
The WebSocket eliminates all three issues.

---

## 5. Execution Model — How Agent Runs Work

### Current (v3 desktop-only)
```
User clicks ▶ Run
    → _run_agent() — creates threading.Thread
    → _exec_thread() — calls compiled LangGraph in background
    → node_act() — BLOCKING LLM call (10-30s)
    → node_evaluate() — BLOCKING LLM call (5-10s)
    → node_revise() (optional) — BLOCKING LLM call (10-30s)
    → node_save() — writes SQLite
    → _poll_log() — UI polls every 0.5s to update log
```

### Proposed (Hub-based)
```
User clicks ▶ Run in Desktop App
    → POST /api/run/submit { agent_id, task, graph, project }
    → Hub queues job (job_id returned immediately)
    → Desktop shows "Queued" status

Hub (background thread pool):
    → Dequeues job
    → Sends: ws: { type: "run_started", job_id }   ← Desktop lights up pipeline
    → node_act()
    → Sends: ws: { type: "node_update", node: "act", status: "complete" }
    → node_evaluate()
    → Sends: ws: { type: "node_update", node: "evaluate", status: "complete", score }
    → (if revise needed) node_revise()
    → node_save() — writes to Hub SQLite
    → Sends: ws: { type: "run_complete", score, output, critique }

Desktop receives WebSocket events:
    → Updates pipeline graph in real-time (replaces current Canvas redraw)
    → Streams output to Output tab
    → Updates score pill
    → Fires push notification
    → Refreshes Tasks view if open
```

**Key difference:** The desktop UI never blocks. The server handles all compute.

---

## 6. Scheduler — Always-On Agent Execution

The current scheduler lives in the GUI process. When the app is closed, scheduled runs don't fire.

The Hub server runs its scheduler independently using **APScheduler**:

```python
# Hub server scheduler concepts
scheduler.add_job(execute_agent_run, 'date', run_date=target_dt, args=[run_config])
scheduler.add_job(daily_reflexion_report, 'cron', hour=7, minute=0)  # 7 AM CT
scheduler.add_job(grant_research_sweep, 'cron', day_of_week='mon', hour=8)
```

When a scheduled run fires:
1. Hub executes the LangGraph run
2. Sends WebSocket event if desktop is open → Desktop shows it live
3. If desktop is CLOSED → Hub still completes the run, stores results
4. Next time desktop opens → pulls completed runs from `/api/runs`

This mirrors exactly how Base44 automations work — they fire regardless of whether the chat UI is open.

---

## 7. Multi-Agent Parallelism

Currently: one agent runs at a time (single thread).

The Hub uses a **ThreadPoolExecutor** with configurable concurrency:

```
Hub Thread Pool (default: 3 concurrent agents)
    ├── Worker 1: grant-writer-agent running Research graph
    ├── Worker 2: social-content-strategist running Reflexion graph
    └── Worker 3: xftc-plugin-dev running WordPress graph

All three send WebSocket updates simultaneously.
Desktop Tasks view shows all three with live node status.
```

This is how the real Base44 multi-agent system works.

---

## 8. Hub as a Windows Service (Always-On)

The Hub server runs as a **Windows Service** via `pywin32` or as a **WSL systemd service**, meaning:

- Starts automatically when Windows boots
- Runs in the background even when AgentHarness desktop is closed
- Scheduled tasks fire at the correct time regardless of desktop state
- Desktop app connects to it on launch; shows "Hub Online" / "Hub Offline" in status bar

Fallback: if Hub is not running, the desktop falls back to the current embedded execution mode (no features lost).

---

## 9. What This Feels Like in the UI

### Status Bar (bottom of desktop)
```
[Hub: Online ●]  [3 agents active]  [Queue: 2 pending]  [DB: 847 runs]  [v3.1.0]
```

### Run View Changes
- ▶ Run button → submits to Hub, immediately shows "Queued"
- Pipeline diagram animates from WebSocket events (real-time, not polling)
- "Running on Hub" badge replaces the thread spinner

### Tasks View
- Shows all Hub-queued runs, not just local in-memory list
- Filter: All / Running / Queued / Completed / Scheduled
- "Cancel" button sends DELETE /api/run/{id} to Hub

### Home — Morning Briefing
- Fetches from GET /api/briefing
- Hub pre-computes it at 6:50 AM so it's ready when David opens the app at 7 AM

### New: Hub Control Panel (in Admin view)
- Start / Stop Hub service
- View Hub logs
- Configure thread pool size
- Manage scheduled jobs (add, cancel, view next fire time)
- Test connection / ping Hub

---

## 10. Future-Proofing — Remote Access

Once the Hub is running as a service, it's one firewall rule away from being accessible over the network:

- **Phone access**: simple web UI served by Hub → check agent run status from iPhone
- **Remote trigger**: webhook endpoint → POST /api/run/submit from anywhere
- **Tailscale/VPN**: access Hub from any device on your network
- **Shared team access**: other team members could submit agent runs to David's Hub

This mirrors exactly how Base44 works — a persistent backend accessible from any client.

---

## 11. Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Hub server | FastAPI + Uvicorn | Async, fast, WebSocket native, auto-docs |
| Job queue | Python Queue + ThreadPoolExecutor | No Redis needed, stays local |
| Scheduler | APScheduler | Lightweight, cron + interval + one-time, no daemon process |
| WebSocket server | FastAPI WebSocket | Same process as REST API |
| Database | SQLite (same file) | No migration needed, Hub serves it via API |
| Windows service | pywin32 (win32serviceutil) | Native Windows service registration |
| WSL alternative | systemd unit file | For WSL2 users |
| Desktop ↔ Hub | websockets + httpx (async client) | Replaces polling + urllib calls |
| Hub startup | hub_start.ps1 / hub_start.sh | Mirrors install scripts |

**New pip dependencies (Hub only):**
```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
apscheduler>=3.10.0
websockets>=12.0
httpx>=0.27.0
pywin32>=306        # Windows service registration (Windows only)
```

---

## 12. What Stays the Same

To be crystal clear — **nothing is removed from the desktop app**. Every view, every feature, every button continues to work exactly as it does today. The Hub is purely additive:

- Without Hub: app works as today (embedded execution, local SQLite, polling)
- With Hub running: app upgrades automatically (server execution, WebSocket streams, parallel agents, always-on scheduler)

This is the same degraded-gracefully pattern used by VS Code's remote development — the local app is always functional, the server just makes it better.

---

## Summary Decision Points for Review

| Question | Options |
|----------|---------|
| Hub process model | A) Windows Service  B) Background process  C) WSL systemd |
| Concurrency | A) 3 parallel agents (default)  B) Configurable  C) Sequential (current) |
| DB strategy | A) Hub owns SQLite, desktop reads via API  B) Shared file + Hub API |
| Scheduler home | A) Hub only  B) Hub + desktop fallback  C) Desktop only (current) |
| Remote access | A) Local only (Phase 1)  B) Tailscale in Phase 2  C) Not needed |
| Phase priority | A) Hub + WebSocket first  B) Scheduler first  C) Parallel agents first |

---

*AgentHarness Hub Concept v1.0 | 2026-05-28 | AgentJames*
