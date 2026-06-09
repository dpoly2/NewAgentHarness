# ArchonHub — Replication Prompt
Use this prompt with an AI coding agent (GitHub Copilot, Cursor, Claude, etc.) to rebuild ArchonHub from scratch on a new system or repository.

---

## PROMPT

You are building **ArchonHub v1.0.0** — an always-on AI agent orchestration platform for a multi-project business portfolio. Build the complete system from scratch exactly as described below.

---

### SYSTEM OVERVIEW

ArchonHub has three surfaces:
1. **Hub Server** (`hub_server.py`) — FastAPI backend, port 8765, REST API + WebSocket + APScheduler
2. **Desktop App** (`main_m365.py`) — Python Tkinter, M365-style UI, connects to Hub
3. **Web Dashboard** (`web/index.html`) — Single-file SPA served by Hub

All files live at: `.agents/agentharness/app/v3/`  
Database: `.agents/agentharness/memory/runs_v3.db` (SQLite, WAL mode)  
Agent skill files: `.agents/agents/projects/<project>/<agent-id>.md`  
Logs: `.agents/data/logs/`

---

### FILE STRUCTURE TO CREATE

```
.agents/
├── .env                           # (user provides — not created by you)
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
│   └── memory/                    # Created at runtime
└── agents/projects/               # Populated separately with .md files
launch_v3.ps1                      # At repo root
```

---

### REQUIREMENTS FILE (.agents/agentharness/app/v3/requirements.txt)

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
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
requests>=2.31.0
python-dotenv>=1.0.0
python-dateutil>=2.8.0
markdown>=3.5
```

---

### MODULE 1: hub_db.py

Build a complete SQLite database layer with WAL mode. Create all tables on init (idempotent). Include full CRUD functions for every entity.

**Database path:** resolved relative to `__file__` → `.agents/agentharness/memory/runs_v3.db`

**Tables to create:**
- `runs` — (id, run_id, agent_id, project, graph, task, score, critique, revision_count, output, skill_version, status, created_at)
- `skills` — (id, agent_id, skill_name, version, content, avg_score, last_critique, created_at)
- `job_queue` — (id TEXT PK, agent_id, project, graph DEFAULT 'reflexion', task, priority DEFAULT 'normal', status DEFAULT 'queued', max_revisions DEFAULT 2, queued_at, started_at, completed_at, job_data)
- `todos` — (id TEXT PK, title, description, priority DEFAULT 'medium', status DEFAULT 'pending', project, due_date, tags DEFAULT '[]', source DEFAULT 'user', created_at, updated_at)
- `notifications` — (id INTEGER PK AUTOINCREMENT, text, color, category DEFAULT 'system', created_at, read DEFAULT 0)
- `hub_config` — (key TEXT PK, value, updated_at)
- `users` — (id INTEGER PK AUTOINCREMENT, username UNIQUE, email UNIQUE, hashed_password, role DEFAULT 'user', is_active DEFAULT 1, created_at, last_login)
- `scheduled_jobs` — (id TEXT PK, agent_id, project, graph, task, run_type, cron_expr, interval_sec, scheduled_at, next_fire, status DEFAULT 'active', created_at, job_data)
- `travel_trips` — (id TEXT PK, name, destination, depart_date, return_date, status DEFAULT 'planning', budget REAL DEFAULT 0, spent REAL DEFAULT 0, notes, created_at, updated_at)
- `email_connectors` — (id TEXT PK, label, email_address, provider DEFAULT 'imap', auth_type DEFAULT 'password', imap_host, imap_port DEFAULT 993, smtp_host, smtp_port DEFAULT 587, username, credentials DEFAULT '{}', status DEFAULT 'pending', last_error, last_synced, created_at, updated_at)
- `projects` — (id TEXT PK, slug UNIQUE, name, description, status DEFAULT 'active', lead_agent, tags DEFAULT '[]', created_at, updated_at)
- `clients` — (id TEXT PK, slug UNIQUE, name, business_type, service, contact_name, contact_email, engagement DEFAULT 'retainer', status DEFAULT 'active', project_slug, notes, created_at, updated_at)
- `conversations` — (id TEXT PK, slug DEFAULT 'global', title, created_at, updated_at)
- `messages` — (id TEXT PK, conversation_id, role, content, agent_id DEFAULT '', created_at)
- `agent_memory` — (id INTEGER PK AUTOINCREMENT, agent_id, key, value, updated_at, UNIQUE(agent_id, key))
- `daily_briefs` — (id TEXT PK, content, created_at)

**Also add indices for:** runs(agent_id, status, created_at), job_queue(status), todos(status), notifications(read), travel_trips(status, depart_date), email_connectors(status), messages(conversation_id), agent_memory(agent_id), projects(slug), clients(slug)

**Auth helpers:**
- `DEFAULT_ADMIN_USERNAME = "admin"`, `DEFAULT_ADMIN_PASSWORD = "ArchonHub2024!"`
- `_hash_pw(password)` using bcrypt
- `_verify_pw(plain, hashed)` using bcrypt

**CRUD functions needed:** full create/get/list/update/delete for all entities. Also:
- `init_schema()` — creates all tables, seeds admin user if no users exist
- `save_run()`, `load_runs(limit)`, `agent_stats()`
- `enqueue_job()`, `update_job_status()`, `load_pending_jobs()`, `get_job()`, `list_jobs()`
- `save_skill()`, `load_skill(skill_name)`, `list_skills()`
- `load_memory_context(agent_id)` — returns string of memory entries for agent
- `save_notification()`, `list_notifications()`, `mark_notifications_read()`, `clear_notifications()`
- `get_config()`, `set_config()`, `update_config(dict)`
- `get_briefing_cache()`, `cache_briefing(dict)`
- `migrate_todos_json()` — migrate any legacy JSON todos to table

---

### MODULE 2: hub_nodes.py

Shared LangGraph execution nodes used by both Hub and Desktop. No GUI imports.

**AgentState TypedDict fields:** run_id, agent_id, project, graph_type, task, skill_name, skill_content, skill_version, memory_context, output, score, critique, revision_count, max_revisions, messages (Annotated[List, add_messages]), cancel_flag

**LLM factory:**
```python
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
def _llm(temperature=0.2): return ChatOpenAI(model=MODEL, temperature=temperature, api_key=os.environ.get("OPENAI_API_KEY",""))
```

**Helper functions:**
- `read_agent_skill_file(agent_id)` — rglob `.agents/agents/projects/` for `{agent_id}.md`
- `write_agent_skill_file(agent_id, content)` — update the .md file on disk

**Node functions (all take state + emit callable):**
- `node_load_memory` — loads skill content + memory_context into state
- `node_act` — calls LLM with system prompt (skill + memory) + task, stores output
- `node_evaluate` — scores output 0.0–1.0 with critique, stores score/critique in state
- `node_revise` — rewrites skill content if score < 0.75, saves new version to DB + disk
- `node_save_memory` — saves run to DB, emits run_completed event
- `node_plan` — research graph: creates research plan
- `node_search` — research graph: executes research
- `node_synthesize` — research graph: synthesizes findings
- `node_wp_plan`, `node_wp_implement`, `node_wp_verify` — wordpress graph nodes
- `node_legal_analyze`, `node_legal_draft`, `node_legal_review` — business law graph nodes

**Graph builders (return compiled StateGraph):**
- `build_reflexion_graph()`
- `build_research_graph()`
- `build_wordpress_graph()`
- `build_business_law_graph()`

Each graph uses Reflexion loop: after evaluate, if score < 0.75 AND revision_count < max_revisions → route to revise → back to act; else → save_memory → END.

**Main entry point:**
```python
def run_graph(config: dict, emit: callable = None) -> dict:
    # config: {agent_id, project, graph, task, max_revisions, run_id?, cancel_flag?}
    # emit: callable(event_type, **data)
    # Returns final state dict
```

---

### MODULE 3: hub_scheduler.py

APScheduler AsyncIOScheduler with timezone `America/Chicago`.

**Built-in jobs (register all in `build_scheduler(hub)`):**

| Job ID | Schedule | Function |
|---|---|---|
| `daily_briefing` | CronTrigger(hour=6, minute=50) | `job_daily_briefing_compute` |
| `daily_reflexion` | CronTrigger(hour=7, minute=0) | `job_daily_reflexion_report` |
| `grant_research_sweep` | CronTrigger(day_of_week='mon', hour=8, minute=0) | `job_grant_research_sweep` |
| `hutto_planning_monitor` | CronTrigger(day_of_week='mon', hour=8, minute=30) | `job_hutto_planning_monitor` |
| `weekly_fare_alert` | CronTrigger(day_of_week='mon', hour=13, minute=30) | `job_weekly_fare_alert` |
| `sigma_signal_check` | CronTrigger(hour=14, minute=0) | `job_sigma_signal_check` |
| `nightly_db_cleanup` | CronTrigger(hour=2, minute=0) | `job_nightly_db_cleanup` |

**Job functions** submit agent runs via `hub.submit_job(config)` and call `save_notification()`.

**Grant sweep agents:** grants-research-agent (grants), yepc-grant-writer-agent (yepc), pbs-fundraising-agent (pbs), solar-finance-agent (solar)

**`get_job_list(scheduler)`** — returns serializable list of all scheduled jobs.

---

### MODULE 4: hub_server.py

FastAPI application. Port 8765.

**Auth setup:**
- JWT with `SECRET_KEY = "archonhub-jwt-secret-change-in-production-2024"`, `ALGORITHM = "HS256"`, 24-hour expiry
- `POST /api/auth/login` — accepts `{username, password}`, returns `{access_token, token_type, user}`
- `POST /api/auth/register` — admin-only after first user
- `GET /api/auth/me` — returns current user
- `X-API-Token` header as alternate admin auth
- `get_current_user()` and `get_admin_user()` FastAPI dependencies

**HubServer class** with:
- `_queue: asyncio.Queue` — job submission queue
- `_active_runs: dict` — run_id → cancel_flag
- `_clients: set` — connected WebSocket clients
- `_executor: ThreadPoolExecutor(max_workers=3)`
- `async submit_job(config)` — enqueues job
- `async broadcast(event_dict)` — sends to all WS clients
- `async _worker_loop()` — pulls from queue, runs `run_graph()` in thread pool
- `cancel_run(run_id)` — sets cancel_flag Event

**Startup** (`@app.on_event("startup")`):
- `init_schema()`
- Seed admin user if no users in DB
- Start scheduler via `build_scheduler(hub)`
- Start `_worker_loop()` background task
- Write PID to `.agents/data/hub.pid`

**REST endpoints — implement all of these:**

```
GET  /api/health         → {status, app, version, uptime, active_runs, queue_depth, ws_clients, scheduler_jobs, thread_pool, langgraph_ok, pending_todos, total_runs}
POST /api/runs           → submit job → {run_id, status}
GET  /api/runs           → list runs (query: limit, agent_id, project, status)
POST /api/runs/{id}/cancel
GET  /api/queue          → list queued jobs
POST /api/queue/pause
POST /api/queue/resume

GET/POST        /api/todos
GET/PUT/DELETE  /api/todos/{id}

GET/POST        /api/notifications
POST            /api/notifications/read
DELETE          /api/notifications

GET/POST        /api/trips
GET/PUT/DELETE  /api/trips/{id}

GET/POST        /api/connectors
GET/PUT/DELETE  /api/connectors/{id}
POST            /api/connectors/{id}/test

GET/POST        /api/projects
GET/PUT/DELETE  /api/projects/{id}

GET/POST        /api/clients
GET/PUT/DELETE  /api/clients/{id}

GET/POST        /api/conversations
GET             /api/conversations/{id}/messages
POST            /api/conversations/{id}/messages

GET/PUT         /api/memory/{agent_id}

GET/POST        /api/briefs
DELETE          /api/briefs/{id}

GET             /api/skills
GET/PUT         /api/skills/{agent_id}

GET/POST        /api/scheduler
DELETE          /api/scheduler/{id}
POST            /api/scheduler/{id}/trigger

GET/PUT         /api/config

GET             /api/briefing
GET             /api/stats

GET/POST        /api/users
GET/PUT/DELETE  /api/users/{id}
```

**WebSocket endpoint** (`/ws`):
- Accept connection, verify JWT token
- Add to `_clients` set
- Send `{type: "connected", ...}` on join
- Listen for client messages (e.g., ping/pong)
- Remove from `_clients` on disconnect
- Broadcast node_update, run_started, run_completed, run_failed, run_cancelled, notif, todo_update, briefing_ready events

**Static files:** Mount `.agents/agentharness/app/v3/web` at `/web`, add redirect `/` → `/web`

**CORS:** Allow all origins (local-first design)

---

### MODULE 5: hub_client.py

Desktop ↔ Hub connector. Gracefully degrades when Hub is offline.

```python
HUB_BASE = "http://localhost:8765"
HUB_WS   = "ws://localhost:8765/ws"
TIMEOUT  = 5.0
RECONNECT = 30
```

**HubClient class:**
- `online: bool = False`
- `start()` — begin background WebSocket connect loop
- `stop()` — clean shutdown
- `poll_events()` → list of events since last poll
- HTTP methods (all return None/[] on offline): `submit_run()`, `list_runs()`, `queue_jobs()`, `list_todos()`, `create_todo()`, `update_todo()`, `delete_todo()`, `list_trips()`, `create_trip()`, `update_trip()`, `delete_trip()`, `list_connectors()`, `create_connector()`, `update_connector()`, `delete_connector()`, `test_connector()`, `get_briefing()`, `list_notifications()`, `clear_notifications()`, `list_scheduler_jobs()`, `cancel_run()`, `run_stats()`, `get_config()`, `update_config()`, `pause_queue()`, `resume_queue()`
- WebSocket thread: connects, listens, puts events in internal queue, auto-reconnects on disconnect

---

### MODULE 6: main_m365.py

Tkinter desktop app. Python 3.11+ compatible. Windows-first, macOS/Linux supported.

**Design tokens — use exactly:**
```python
BG_CANVAS="#0B0F17"  BG_RAIL="#080C13"  BG_PANEL="#111827"  BG_CARD="#0A1F44"
BG_INPUT="#0d1520"   BG_HOVER="#0e2444"  BG_SELECTED="#0f2d57"
ACCENT="#00B8FF"     ACCENT_LIGHT="#2DD4FF"  ACCENT_DARK="#0090cc"
SUCCESS="#22c55e"    WARNING="#f59e0b"   ERROR="#ef4444"
TEXT_PRIMARY="#D9E3F0"  TEXT_BODY="#a0b4cc"  TEXT_MUTED="#4a6080"
DIVIDER="#0A1F44"    BORDER_CARD="#0e2a55"
```

**AGENT_REGISTRY (hardcoded, used for UI dropdowns):**
```python
AGENT_REGISTRY = {
    "Business Law":    ["business-law-project-lead","business-law-entity-agent","business-law-contracts-agent","business-law-ip-agent","business-law-employment-agent","business-law-realestate-agent","business-law-regulatory-agent"],
    "XFTC":            ["xftc-project-lead","xftc-plugin-dev","xftc-frontend-dev","xftc-payments-agent","xftc-qa-agent"],
    "Grants / YEPC":   ["grants-research-agent","grant-writer-agent","yepc-grant-writer-agent","yepc-real-estate-research-agent","yepc-project-manager"],
    "S2T Designs":     ["s2t-project-lead","s2t-webdev-agent","s2t-seo-agent"],
    "SmithCap Finance":["finance-cfo","finance-cpa","finance-tax-strategist","finance-bookkeeper","finance-advisor"],
    "Ministry":        ["ministry-project-lead","ministry-sermon-writer"],
    "Social Media":    ["social-project-lead","social-content-strategist","social-copywriter","social-ads-manager"],
    "Solar":           ["solar-project-lead","solar-marketing-agent"],
    "Sigma Signal":    ["sigma-signal-project-lead","sigma-signal-writer"],
    "Holdings":        ["holdings-project-lead","holdings-legal-agent","holdings-finance-agent","holdings-tax-agent","holdings-compliance-agent"],
    "Markets":         ["markets-project-lead","markets-cio","markets-cro","markets-options-strategist","markets-quant","markets-intelligence-desk","markets-equity-analyst","markets-macro-analyst","markets-tactical-alpha","markets-technical-analyst"],
    "Nutrue":          ["nutrue-project-lead","nutrue-brand-agent","nutrue-ecommerce-agent","nutrue-finance-agent","nutrue-inbro-retrofit-agent","nutrue-legal-agent","nutrue-marketing-agent"],
    "Night King":      ["nightking-project-lead","nightking-brand-agent","nightking-design-agent","nightking-media-agent"],
    "PBS Foundation":  ["pbs-project-lead","pbs-board-agent","pbs-communications-agent","pbs-fundraising-agent","pbs-legal-agent","pbs-programs-agent"],
    "Elevation":       ["elevation-project-lead","elevation-brand-agent","elevation-events-agent","elevation-funding-agent","elevation-legal-agent","elevation-marketing-agent"],
}
```

**PROJECTS list:**
```python
PROJECTS = ["xftc","yepc","pbs-foundation","s2tdesigns","smithcap","smithcap-finance",
            "ministry","business-law","social-media","solar-repair","sigma-signal",
            "nutrue","the-elevation","travel","holdings","markets","nightking"]
```

**Navigation sections (left rail icons → views):**
1. Home — Agent card grid, quick-run panel, Hub status indicator
2. Runs — Run history treeview + live log stream, cancel button
3. Todos — CRUD list with priority badges (urgent/high/medium/low), project filter
4. Daily Digest — Briefing from Hub (stats, flagged agents, urgent todos, blockers)
5. Schedule — Scheduler jobs table from Hub
6. Clients — S2T Designs client roster loaded from CLIENT-ROSTER.md + client subdirs
7. Travel — Trip planning CRUD
8. Connectors — Email connector CRUD with test button
9. Admin — PIN-gated (PIN: `1914`) with 5 sub-tabs: Hub Control, Config (LLM/API keys), Users, Scheduler, Logs

**Graph visualizer:** Canvas widget showing graph nodes with colored circles and directional arrows. Highlights current node in yellow during execution.

**Node colors:**
```python
NC = {
    "load_memory":"#00bcf2","act":"#8b5cf6","evaluate":"#f8b400",
    "revise":"#e74856","save_memory":"#92c353","plan":"#06b6d4",
    "search":"#3b82f6","synthesize":"#a855f7","wp_plan":"#06b6d4",
    "wp_implement":"#8b5cf6","wp_verify":"#92c353","legal_analyze":"#f97316",
    "legal_draft":"#ec4899","legal_review":"#14b8a6","END":"#475569"
}
```

**Hub integration:**
- Create `HubClient` on init, call `hub.start()`
- Show Hub online/offline indicator in status bar
- Fall back to embedded `run_graph()` execution when Hub offline
- Poll `hub.poll_events()` every 500ms for real-time updates

**Admin Panel PIN:** `1914` — Phi Beta Sigma founding year. Show "Incorrect PIN" on wrong entry.

**LLM selector:** Dropdown in settings/admin for model selection (gpt-4o, gpt-4o-mini, claude-3-5-sonnet, etc.)

---

### MODULE 7: web/index.html

Single-file SPA. No build tools. Vanilla JS + inline CSS.

**CSS variables:**
```css
:root {
    --bg: #0B0F17; --bg-card: #111827; --bg-panel: #0A1F44;
    --accent: #00B8FF; --accent-light: #2DD4FF;
    --text: #D9E3F0; --text-body: #D9E3F0; --text-muted: #8899aa;
    --success: #22c55e; --warning: #f59e0b; --error: #ef4444;
    --border: #1e3a5f; --shadow: 0 18px 36px rgba(0,0,0,0.28);
    --radius: 16px; --sidebar-desktop: 220px; --sidebar-collapsed: 56px;
}
body { background: radial-gradient(circle at top right, rgba(0,184,255,0.12), transparent 28%), var(--bg); }
```

**Font stack:** `Inter, Segoe UI, system-ui, -apple-system, sans-serif`

**Layout:**
- Fixed sidebar (220px desktop, collapsible to 56px, full overlay on mobile)
- Main content area fills remaining width
- All pages rendered into a single `#content` div via JS

**Pages to implement:**
1. **login** — username/password form, POST /api/auth/login, store JWT in localStorage
2. **dashboard** — GET /api/health, show stat cards (total runs, active runs, pending todos, queue depth, ws_clients)
3. **runs** — GET /api/runs, table with run_id, agent, project, graph, score badge, status badge, created_at
4. **queue** — GET /api/queue, live list with cancel button per job
5. **todos** — GET/POST/PUT/DELETE /api/todos, filter by priority + status, add todo form
6. **schedule** — GET /api/scheduler, table of jobs with next_fire
7. **clients** — GET /api/clients, card grid
8. **projects** — GET /api/projects, card grid
9. **connectors** — GET/POST/PUT/DELETE /api/connectors, test button
10. **travel** — GET/POST/PUT/DELETE /api/trips
11. **briefing** — GET /api/briefing, formatted briefing display
12. **chat** — GET/POST /api/conversations + messages, chat bubble UI
13. **settings** — GET/PUT /api/config, user management, API token display

**WebSocket:**
```javascript
const ws = new WebSocket(`ws://${location.host}/ws`);
// Auth: send {type:"auth", token} after open
// Handle: node_update (live run progress), todo_update (refresh todos), notif (toast)
```

**Auth flow:**
- On load: check localStorage for token → if missing, show login page
- POST /api/auth/login → store token → navigate to dashboard
- All API calls include `Authorization: Bearer <token>` header
- On 401: clear token, redirect to login

**Toast notifications:** overlay div that appears on `notif` WebSocket events, auto-dismiss after 4s

---

### MODULE 8: start.ps1 (Windows launch — desktop)

```powershell
# Resolves repo root, activates .venv, loads .agents/.env, launches main_m365.py
# Sets PYTHONIOENCODING=utf-8 and PYTHONUTF8=1 for Windows Unicode safety
```

### MODULE 9: hub_start.ps1 (Windows launch — hub only)

```powershell
# Same pattern as start.ps1 but launches hub_server.py instead
```

### MODULE 10: launch_v3.ps1 (repo root — starts both)

```powershell
# Starts hub_server.py in a new background window
# Then starts main_m365.py in the current window
# Both loaded from .venv with .env applied
```

---

### IMPLEMENTATION NOTES

1. **All path resolution** must be relative to `__file__` — no hardcoded absolute paths
2. **Graceful degradation** — every import wrapped in try/except with meaningful fallback
3. **Windows Unicode safety** — always set `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` in launch scripts; reconfigure stdout/stderr at top of main_m365.py
4. **Python 3.13 compatibility** — use `passlib[bcrypt]` OR import `bcrypt` directly (passlib passthrough causes issues on 3.13 — prefer direct bcrypt import)
5. **Tkinter thread safety** — never call tkinter methods from background threads; use a `queue.Queue` + `root.after(100, poll_queue)` pattern
6. **Hub offline fallback** — desktop app must work standalone without Hub running
7. **WAL mode** — always `PRAGMA journal_mode=WAL` so desktop and Hub can read/write simultaneously
8. **Agent skill auto-discovery** — Hub uses `rglob(f"{agent_id}.md")` — never hardcode skill paths
9. **JWT secret** — must be changed in production; default is `archonhub-jwt-secret-change-in-production-2024`
10. **Admin seeding** — on startup, if `users` table is empty, create default admin (`admin` / `ArchonHub2024!`)
11. **Cancel flag** — `threading.Event` passed through AgentState so long-running LangGraph executions can be cancelled mid-run
12. **Score threshold** — 0.75 triggers revision; max_revisions default is 2
13. **Logging** — use `ah_logging.py` for structured per-module logging to `.agents/data/logs/`
14. **CORS** — open for local dev; comment saying "lock down for production"

---

### WHAT TO BUILD FIRST (suggested order)

1. `hub_db.py` — schema + all CRUD
2. `hub_nodes.py` — LangGraph nodes + graph builders
3. `hub_scheduler.py` — scheduler jobs
4. `hub_server.py` — FastAPI server wiring everything together
5. `hub_client.py` — desktop↔hub bridge
6. `web/index.html` — web dashboard
7. `main_m365.py` — Tkinter desktop app
8. Launch scripts (`start.ps1`, `hub_start.ps1`, `launch_v3.ps1`)
9. iOS + Watch app — SwiftUI project at `projects/archonhub-ios/`

---

### MODULE 11: iOS & Apple Watch App (SwiftUI)

**Location:** `projects/archonhub-ios/`  
**Requirements:** Xcode 15+, iOS 17+, watchOS 10+, no external dependencies

Build the following targets:

**iPhone target (`ArchonHub`):**
- `ArchonHubApp.swift` — @main, auth gate (LoginView vs ContentView)
- `ContentView.swift` — TabView with 5 tabs: Dashboard, Runs, Todos, Briefing, Settings
- `Models/Models.swift` — all Codable structs (AgentRun, Todo, HealthResponse, etc.)
- `Network/HubClient.swift` — singleton, async/await REST + WebSocket, JWT Bearer auth
- `Network/AuthStore.swift` — ObservableObject, login/logout, token persistence
- `Views/Dashboard/` — stats grid, recent runs, Hub status banner
- `Views/Runs/` — run list with filters, run detail sheet, cancel button
- `Views/Todos/` — CRUD list, swipe-to-delete, swipe-to-complete, add form sheet
- `Views/Briefing/` — daily digest text display, pull-to-refresh
- `Views/Chat/` — conversation list + chat bubble thread
- `Views/Settings/` — server URL config, logout, about

**Apple Watch target (`ArchonHubWatch`):**
- `ArchonHubWatchApp.swift` — @main
- `WatchMainView.swift` — vertical TabView paging
- `Views/WatchStatusView.swift` — online dot, runs count, todos count
- `Views/WatchQuickRunView.swift` — agent picker + run dispatch
- `Views/WatchNotificationsView.swift` — last 5 notifications
- `Complications/ArchonHubComplication.swift` — ClockKit gauge/text complication

**Network:** Base URL configurable (default `http://localhost:8765`). JWT stored in UserDefaults. WebSocket auto-reconnect. `convertFromSnakeCase` JSON decoding.

**Brand colors:**
```swift
extension Color {
    static let archonAccent  = Color(hex: "#00B8FF")
    static let archonBG      = Color(hex: "#0B0F17")
    static let archonCard    = Color(hex: "#111827")
    static let archonText    = Color(hex: "#D9E3F0")
    static let archonSuccess = Color(hex: "#22c55e")
    static let archonWarning = Color(hex: "#f59e0b")
    static let archonError   = Color(hex: "#ef4444")
}
```

App icons from `branding/ios/AppIcon.appiconset/` (iPhone) and `branding/watch/AppIcon.appiconset/` (Watch).

---

### VERIFICATION CHECKLIST

After building, verify:
- [ ] `python hub_server.py` starts without errors on port 8765
- [ ] `GET http://localhost:8765/api/health` returns `{"status":"ok","app":"ArchonHub",...}`
- [ ] `http://localhost:8765/web` loads the login page
- [ ] Login with `admin` / `ArchonHub2024!` succeeds and returns JWT
- [ ] POST `/api/runs` with a test job enqueues and runs
- [ ] WebSocket at `ws://localhost:8765/ws` connects and receives events
- [ ] `python main_m365.py` launches Tkinter window with M365 nav rail
- [ ] Hub online indicator shows green in desktop app
- [ ] Admin PIN `1914` unlocks Admin panel in desktop app
- [ ] Scheduler shows 7 built-in jobs at `/api/scheduler`
- [ ] iOS app builds in Xcode without errors (iOS 17+)
- [ ] iPhone login screen connects to Hub and authenticates
- [ ] Watch app shows Hub status on status screen
- [ ] Watch complication registers in ClockKit

