# AI Agent Harness Platform — Replication Prompt Template
#
# USAGE: Fill in all [PLACEHOLDER] values, then use this prompt with any
# AI coding agent (GitHub Copilot, Cursor, Claude, etc.) to build your
# custom AI agent orchestration platform from scratch.
#
# Based on ArchonHub v1.1.0 — proven, production-ready architecture.
# ─────────────────────────────────────────────────────────────────────────────

## PROMPT

You are building **[AppName] v1.0.0** — an always-on AI agent orchestration platform for [DESCRIBE YOUR USE CASE / BUSINESS DOMAIN]. Build the complete system from scratch exactly as described below.

---

### SYSTEM OVERVIEW

[AppName] has five surfaces:
1. **Hub Server** (`hub_server.py`) — FastAPI backend, port [PORT], REST API + WebSocket + APScheduler
2. **Desktop App** (`main_m365.py`) — Python Tkinter, M365-style UI, connects to Hub
3. **Web Dashboard** (`web/index.html`) — Single-file SPA served by Hub
4. **iPhone App** — SwiftUI iOS 17+, connects to Hub REST API
5. **Apple Watch App** — SwiftUI watchOS 10+, status glance + quick run dispatch

All Python files live at: `.agents/agentharness/app/v3/`
Database: `.agents/agentharness/memory/runs_v3.db` (SQLite, WAL mode)
Agent skill files: `.agents/agents/projects/<project>/<agent-id>.md`
Logs: `.agents/data/logs/`
iOS project: `projects/[appname]-ios/`

---

### FILE STRUCTURE TO CREATE

```
.agents/
├── .env
├── agentharness/
│   ├── app/v3/
│   │   ├── hub_server.py
│   │   ├── hub_db.py
│   │   ├── hub_nodes.py
│   │   ├── hub_scheduler.py
│   │   ├── hub_client.py
│   │   ├── main_m365.py
│   │   ├── ah_logging.py
│   │   ├── requirements.txt
│   │   ├── start.ps1
│   │   ├── hub_start.ps1
│   │   └── web/
│   │       └── index.html
│   └── memory/
└── agents/projects/
launch_v3.ps1
projects/[appname]-ios/
branding/
```

---

### REQUIREMENTS FILE

```
langgraph>=0.2.0
langchain>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.1.0
langchain-community>=0.3.0
openai>=1.0.0
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
apscheduler>=3.10.0
websockets>=12.0
httpx>=0.27.0
pydantic>=2.0.0
sqlite-utils>=3.35.0
bcrypt>=4.0.0
python-jose[cryptography]>=3.3.0
requests>=2.31.0
python-dotenv>=1.0.0
python-dateutil>=2.8.0
markdown>=3.5
```

---

### MODULE 1: hub_db.py

SQLite WAL-mode database layer. All tables idempotent (CREATE TABLE IF NOT EXISTS).

**Tables:**
- `runs` — agent execution history
- `skills` — agent skill versions + scores
- `job_queue` — pending/active/completed jobs
- `todos` — task management
- `notifications` — push notification log
- `hub_config` — key-value config store
- `users` — user accounts (bcrypt passwords)
- `scheduled_jobs` — persisted scheduler jobs
- `travel_trips` — travel planning
- `email_connectors` — IMAP/SMTP integrations
- `projects` — project registry
- `clients` — client CRM
- `conversations` + `messages` — chat threads
- `agent_memory` — per-agent key-value memory
- `daily_briefs` — cached briefing documents

**Auth:** Use `bcrypt` directly (not passlib — Python 3.13 compat).
**Default admin:** `[ADMIN_USERNAME]` / `[DEFAULT_PASSWORD]`
**Default config seed:** api_token (uuid), llm_model ([DEFAULT_MODEL]), thread_pool_size (3), queue_paused (false)

Implement full CRUD for every entity. All datetimes as ISO strings. UUID IDs where not provided.

---

### MODULE 2: hub_nodes.py

Shared LangGraph execution nodes. No GUI imports.

**AgentState fields:** run_id, agent_id, project, graph_type, task, skill_name, skill_content, skill_version, memory_context, output, score, critique, revision_count, max_revisions, messages, cancel_flag

**LLM:** `os.environ.get("OPENAI_MODEL", "[DEFAULT_MODEL]")`

**Helpers:**
- `read_agent_skill_file(agent_id)` — rglob `.agents/agents/projects/` for `{agent_id}.md`
- `write_agent_skill_file(agent_id, content)` — write updated content back to disk

**Nodes (all check cancel_flag):** node_load_memory, node_act, node_evaluate, node_revise, node_save_memory, node_plan, node_search, node_synthesize, node_wp_plan, node_wp_implement, node_wp_verify, node_legal_analyze, node_legal_draft, node_legal_review

**Graphs:** build_reflexion_graph(), build_research_graph(), build_wordpress_graph(), build_business_law_graph()

**Reflexion loop:** score < 0.75 AND revision_count < max_revisions → revise; else → save_memory → END

**Entry point:** `run_graph(config: dict, emit: callable = None) -> dict`

All LangGraph imports wrapped in try/except with LANGGRAPH_OK flag + graceful fallback.

---

### MODULE 3: hub_scheduler.py

APScheduler AsyncIOScheduler. Timezone: `[TIMEZONE]`

**Built-in jobs to implement:**

| Job ID | CronTrigger | What it does |
|---|---|---|
| `daily_briefing` | hour=[H], minute=[M] | Compute morning briefing |
| `daily_reflexion` | hour=[H], minute=[M] | Daily reflexion report |
| `nightly_db_cleanup` | hour=2, minute=0 | Delete runs older than 90 days |
| `[custom_job_1]` | [CRON] | [DESCRIPTION] — agent: [AGENT_ID], project: [PROJECT] |
| `[custom_job_2]` | [CRON] | [DESCRIPTION] — agent: [AGENT_ID], project: [PROJECT] |

`build_scheduler(hub) -> HubScheduler` — creates scheduler, registers all jobs, returns it.
`get_job_list(scheduler)` — returns serializable list with next_fire times.

---

### MODULE 4: hub_server.py

FastAPI app. Port [PORT].

**JWT:** SECRET_KEY from env, ALGORITHM="HS256", 24h expiry.
**Auth endpoints:** POST /api/auth/login, POST /api/auth/register, GET /api/auth/me
**Alt auth:** X-API-Token header

**HubServer class:**
- asyncio.Queue for job submission
- ThreadPoolExecutor(max_workers=3) for run_graph execution
- broadcast() sends JSON to all WebSocket clients
- cancel_run() sets threading.Event cancel flag

**All REST endpoints** (implement fully):
GET /api/health, POST/GET /api/runs, POST /api/runs/{id}/cancel,
GET /api/queue, POST /api/queue/pause, POST /api/queue/resume,
Full CRUD: /api/todos, /api/notifications, /api/trips, /api/connectors,
/api/projects, /api/clients, /api/conversations, /api/memory/{agent_id},
/api/briefs, /api/skills, /api/scheduler, /api/config, /api/users,
GET /api/briefing, GET /api/stats

**WebSocket /ws:** JWT auth on connect, broadcast events, ping/pong.

**Static files:** Mount `web/` at `/web`. Redirect `/` → `/web`.
**CORS:** Open (local-first; comment to lock down for production).

---

### MODULE 5: hub_client.py

Desktop ↔ Hub HTTP/WS bridge. Gracefully degrades offline.

`HUB_BASE = "http://localhost:[PORT]"`, `TIMEOUT = 5.0`, `RECONNECT_INTERVAL = 30`

**HubClient:** background WS thread, login/reconnect loop, event queue, `poll_events()`.
All HTTP methods return None/[] when offline — never raise.
Implement: submit_run, list_runs, cancel_run, queue_jobs, pause/resume_queue,
list/create/update/delete todos, trips, connectors, list_scheduler_jobs,
trigger_job, get_briefing, list_notifications, clear_notifications,
get_config, update_config, get_health, list_projects, list_clients,
list_conversations, create_conversation, list_messages, send_message, list_users.

---

### MODULE 6: main_m365.py

Tkinter M365-style desktop app.

**Design tokens:**
```python
BG_CANVAS="[HEX]"   BG_RAIL="[HEX]"    BG_PANEL="[HEX]"   BG_CARD="[HEX]"
BG_INPUT="[HEX]"    BG_HOVER="[HEX]"   BG_SELECTED="[HEX]"
ACCENT="[HEX]"      ACCENT_LIGHT="[HEX]" ACCENT_DARK="[HEX]"
SUCCESS="[HEX]"     WARNING="[HEX]"    ERROR="[HEX]"
TEXT_PRIMARY="[HEX]" TEXT_BODY="[HEX]" TEXT_MUTED="[HEX]"
```

**AGENT_REGISTRY:**
```python
AGENT_REGISTRY = {
    "[Team 1]": ["[agent-id-1]", "[agent-id-2]"],
    "[Team 2]": ["[agent-id-3]", "[agent-id-4]"],
    # ... add all your teams
}
PROJECTS = ["[project-1]", "[project-2]", ...]
```

**Left rail (9 nav sections):** Home, Runs, Todos, Daily Digest, Schedule, Clients, Travel, Connectors, Admin

**Admin PIN:** `[ADMIN_PIN]` — 5-tab admin panel behind PIN gate.

**Windows Unicode safety:** `sys.stdout.reconfigure(encoding="utf-8")` at top.
**Thread safety:** `queue.Queue` + `root.after(100, _poll_queue)`.
**Fallback:** embedded `run_graph()` when Hub offline — no features lost.
**Branding:** `root.iconbitmap(str(APP_ROOT / "branding" / "desktop" / "app-icon.ico"))`

---

### MODULE 7: web/index.html

Single-file SPA. Vanilla HTML/CSS/JS only. No build tools.

**CSS variables:**
```css
:root {
    --bg: [HEX]; --bg-card: [HEX]; --bg-panel: [HEX];
    --accent: [HEX]; --accent-light: [HEX];
    --text: [HEX]; --text-muted: [HEX];
    --success: [HEX]; --warning: [HEX]; --error: [HEX];
    --border: [HEX]; --radius: 16px;
    --sidebar-desktop: 220px; --sidebar-collapsed: 56px;
}
body { background: radial-gradient(circle at top right, rgba([R],[G],[B],0.12), transparent 28%), var(--bg); }
```

**Branding in `<head>`:**
```html
<link rel="icon" type="image/x-icon" href="/web/favicon.ico" />
<link rel="icon" type="image/png" sizes="192x192" href="/web/favicon-192.png" />
```

**13 pages:** login, dashboard, runs, queue, todos, schedule, clients, projects, connectors, travel, briefing, chat, settings

**Auth:** JWT in localStorage. All calls: `Authorization: Bearer <token>`. On 401: logout.
**WebSocket:** Connect post-login. Handle: node_update, todo_update, notif (toast), run_completed.
**Sidebar:** Logo from `/web/logo.svg` with text fallback. Collapsible to 56px. Full overlay on mobile.

---

### MODULE 8: iOS App (SwiftUI)

Location: `projects/[appname]-ios/`

**Targets:** [AppName] (iOS 17+) + [AppName]Watch (watchOS 10+)

**iPhone — key files:**
- `[AppName]App.swift` — @main, auth gate
- `ContentView.swift` — TabView (Dashboard, Runs, Todos, Briefing, Settings)
- `Models/Models.swift` — Codable structs (AgentRun, Todo, HealthResponse, etc.)
- `Network/HubClient.swift` — async/await REST + WebSocket, JWT Bearer
- `Network/AuthStore.swift` — ObservableObject, login/logout

**Watch — key files:**
- `[AppName]WatchApp.swift` — @main
- `WatchMainView.swift` — vertical TabView paging
- `WatchStatusView.swift`, `WatchQuickRunView.swift`, `WatchNotificationsView.swift`
- `Complications/[AppName]Complication.swift` — ClockKit gauge/text

**Brand colors extension:**
```swift
extension Color {
    static let appAccent  = Color(hex: "[HEX]")
    static let appBG      = Color(hex: "[HEX]")
    static let appCard    = Color(hex: "[HEX]")
    static let appText    = Color(hex: "[HEX]")
    static let appSuccess = Color(hex: "[HEX]")
    static let appWarning = Color(hex: "[HEX]")
    static let appError   = Color(hex: "[HEX]")
}
```

App icons from `branding/ios/AppIcon.appiconset/` and `branding/watch/AppIcon.appiconset/`.

---

### LAUNCH SCRIPTS

**start.ps1** — Loads .env, activates .venv, launches main_m365.py
**hub_start.ps1** — Loads .env, activates .venv, launches hub_server.py
**launch_v3.ps1** (repo root) — Starts hub in new window, then desktop in current window

Set `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` in all scripts.

---

### IMPLEMENTATION NOTES

1. **All path resolution** relative to `__file__` — no hardcoded absolute paths
2. **Graceful degradation** — every import wrapped in try/except with fallback
3. **Windows Unicode safety** — `PYTHONIOENCODING=utf-8` everywhere
4. **Python 3.13 compat** — use `bcrypt` directly, not passlib passthrough
5. **Tkinter thread safety** — `queue.Queue` + `root.after()` pattern
6. **Hub offline fallback** — desktop works standalone without Hub
7. **WAL mode** — always `PRAGMA journal_mode=WAL`
8. **Skill auto-discovery** — `rglob(f"{agent_id}.md")` — never hardcode
9. **Cancel flag** — `threading.Event` through AgentState
10. **Score threshold** — 0.75 triggers revision; max_revisions default 2
11. **CORS** — open for dev; comment "lock down for production"

---

### WHAT TO BUILD (suggested order)

1. `hub_db.py`
2. `hub_nodes.py`
3. `hub_scheduler.py`
4. `hub_server.py`
5. `hub_client.py`
6. `web/index.html`
7. `main_m365.py`
8. Launch scripts
9. iOS + Watch SwiftUI app

---

### VERIFICATION CHECKLIST

- [ ] `python hub_server.py` starts on port [PORT]
- [ ] `GET /api/health` returns `{"status":"ok","app":"[AppName]",...}`
- [ ] Web dashboard loads and login works
- [ ] POST `/api/runs` enqueues and executes
- [ ] WebSocket connects and receives events
- [ ] Desktop app launches with M365 nav rail
- [ ] Admin PIN `[ADMIN_PIN]` unlocks Admin panel
- [ ] Scheduler shows built-in jobs
- [ ] iOS app builds in Xcode (iOS 17+)
- [ ] Watch complication registers in ClockKit
