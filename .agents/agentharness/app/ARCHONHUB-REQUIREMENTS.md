# ArchonHub — Product Requirements Document
**Version:** 1.1.0  
**Last Updated:** June 2026  
**Owner:** Smith Capital Portfolio

---

## 1. Overview

ArchonHub is an always-on AI agent orchestration platform built for managing a portfolio of projects, clients, agents, and scheduled automations. It consists of five surfaces:

| Surface | Technology | Purpose |
|---|---|---|
| **Hub Server** | Python / FastAPI / SQLite | Always-on backend, REST API, WebSocket, scheduler |
| **Desktop App** | Python / Tkinter | M365-style native desktop client |
| **Web Dashboard** | Single-file HTML/JS | Browser-based dashboard served by Hub |
| **iPhone App** | Swift / SwiftUI (iOS 17+) | Mobile client — dashboard, runs, todos, briefing, chat |
| **Apple Watch App** | Swift / SwiftUI (watchOS 10+) | Glance view, quick run dispatch, complications |

---

## 2. System Architecture

```
repo/
└── .agents/
    ├── agentharness/
    │   ├── app/v3/
    │   │   ├── hub_server.py       # FastAPI server (port 8765)
    │   │   ├── hub_db.py           # SQLite database layer (WAL mode)
    │   │   ├── hub_nodes.py        # LangGraph node functions (shared)
    │   │   ├── hub_scheduler.py    # APScheduler job engine
    │   │   ├── hub_client.py       # Desktop ↔ Hub HTTP/WS client
    │   │   ├── main_m365.py        # Tkinter desktop app
    │   │   ├── ah_logging.py       # Structured per-module logging
    │   │   ├── web/index.html      # Single-file web dashboard
    │   │   ├── requirements.txt
    │   │   ├── start.ps1           # Windows launch script (desktop)
    │   │   ├── hub_start.ps1       # Windows launch script (hub only)
    │   │   └── launch_v3.ps1       # Root shortcut (hub + desktop)
    │   └── memory/
    │       └── runs_v3.db          # SQLite database
    ├── agents/projects/            # Agent skill .md files
    │   ├── business-law/
    │   ├── xftc/
    │   ├── markets/
    │   ├── nutrue/
    │   ├── nightking/
    │   └── ... (17 project folders, 116+ .md skill files)
    ├── data/
    │   └── logs/                   # Hub + module log files
    └── .env                        # API keys and config
```

---

## 3. Python Dependencies

```
# AI / Agent Engine
langgraph>=0.2.0
langchain>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.1.0
langchain-community>=0.3.0
openai>=1.0.0

# Hub Server
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
apscheduler>=3.10.0
websockets>=12.0
httpx>=0.27.0

# Data / Validation
pydantic>=2.0.0
sqlite-utils>=3.35.0
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0

# Utilities
requests>=2.31.0
python-dotenv>=1.0.0
python-dateutil>=2.8.0
markdown>=3.5
```

**Runtime:** Python 3.11+ (Python 3.13 compatible)  
**tkinter:** Bundled with official Python installer (Windows); `brew install python-tk@3.11` on macOS; `sudo apt-get install python3-tk` on Ubuntu

---

## 4. Environment Variables (.agents/.env)

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | OpenAI key for LangGraph LLM calls |
| `ANTHROPIC_API_KEY` | Optional | Claude model support |
| `OPENAI_MODEL` | Optional | Default: `gpt-4o-mini` |
| `HUB_PORT` | Optional | Default: `8765` |
| `ADMIN_PASSWORD` | Optional | Override default admin password |

---

## 5. Hub Server Requirements (hub_server.py)

### 5.1 General
- FastAPI application running on **port 8765**
- Serves REST API at `/api/...`
- Serves WebSocket at `/ws`
- Serves static web dashboard at `/web` (redirected from `/`)
- Auto-docs at `/docs` (Swagger UI)
- CORS enabled for all origins (local-first design)
- Startup creates SQLite schema, seeds default admin user, starts scheduler
- Graceful shutdown via SIGINT/SIGTERM

### 5.2 Authentication
- **JWT-based auth** using `python-jose`
- 24-hour token expiry
- `POST /api/auth/login` — returns JWT token
- `POST /api/auth/register` — create new user (admin-only after first user)
- `GET /api/auth/me` — current user info
- **Admin PIN** — `1914` (Phi Beta Sigma founding year) — used in desktop app only
- Default admin: username `admin`, password `ArchonHub2024!`
- Bearer token auth on all `/api/` endpoints
- `X-API-Token` header supported as alternative auth (server-generated token)

### 5.3 Agent Execution API
| Endpoint | Method | Description |
|---|---|---|
| `/api/runs` | POST | Submit an agent job |
| `/api/runs` | GET | List run history |
| `/api/runs/{run_id}/cancel` | POST | Cancel running job |
| `/api/queue` | GET | List queued jobs |
| `/api/queue/pause` | POST | Pause the job queue |
| `/api/queue/resume` | POST | Resume the job queue |
| `/api/health` | GET | Server health + stats |

### 5.4 Entity APIs (full CRUD)
| Resource | Base Path |
|---|---|
| Todos | `/api/todos` |
| Notifications | `/api/notifications` |
| Skills | `/api/skills` |
| Travel Trips | `/api/trips` |
| Email Connectors | `/api/connectors` |
| Projects | `/api/projects` |
| Clients | `/api/clients` |
| Conversations | `/api/conversations` |
| Messages | `/api/conversations/{id}/messages` |
| Agent Memory | `/api/memory` |
| Daily Briefs | `/api/briefs` |
| Scheduled Jobs | `/api/scheduler` |
| Users | `/api/users` |
| Config | `/api/config` |
| Daily Briefing | `/api/briefing` |

### 5.5 WebSocket (ws://localhost:8765/ws)
- JWT auth on connect
- Real-time events pushed to all connected clients:
  - `run_started`, `run_completed`, `run_failed`, `run_cancelled`
  - `node_update` — live graph node progress
  - `notif` — push notifications
  - `todo_update` — todo changes
  - `briefing_ready` — morning briefing cached
- Ping/pong heartbeat: 30s interval, 10s timeout

### 5.6 Thread Pool
- Default 3 concurrent agent execution threads
- Configurable via hub config API

---

## 6. LangGraph Execution Engine (hub_nodes.py)

### 6.1 Agent State Schema
```python
AgentState = TypedDict({
    run_id, agent_id, project, graph_type, task,
    skill_name, skill_content, skill_version, memory_context,
    output, score, critique, revision_count, max_revisions,
    messages: Annotated[List, add_messages],
    cancel_flag: threading.Event
})
```

### 6.2 Graphs (4 built-in)

| Graph Key | Nodes | Use Case |
|---|---|---|
| `reflexion` | load_memory → act → evaluate → [revise*] → save_memory | General tasks, any agent |
| `research` | load_memory → plan → search → synthesize → evaluate → [revise*] → save_memory | Grant research, market intel |
| `wordpress` | load_memory → wp_plan → wp_implement → wp_verify → evaluate → [revise*] → save_memory | WP dev, plugin work |
| `business-law` | load_memory → legal_analyze → legal_draft → legal_review → evaluate → [revise*] → save_memory | Legal docs, contracts |

- All graphs use **Reflexion loop**: evaluate scores 0.0–1.0; if score < 0.75, revise and re-evaluate
- `max_revisions` configurable per run (default 2)
- **Skill auto-upgrade**: if score < 0.75, new skill version saved to SQLite + .md file updated on disk
- **Cancel flag**: threading.Event checked between nodes; run cancellable at any node boundary
- LLM model: configurable via `OPENAI_MODEL` env var (default: `gpt-4o-mini`)
- Agent skill files read dynamically from `.agents/agents/projects/<project>/<agent-id>.md`

### 6.3 Memory System
- Per-agent memory stored in `agent_memory` table
- Loaded as context on every run start
- Skill versions tracked in `skills` table with score history

---

## 7. Database Schema (SQLite / WAL mode)

**File:** `.agents/agentharness/memory/runs_v3.db`  
**Mode:** WAL (Write-Ahead Logging) for concurrent desktop + hub access

| Table | Purpose |
|---|---|
| `runs` | All agent execution history (run_id, agent_id, project, graph, task, score, critique, output, skill_version, status) |
| `skills` | Agent skill versions with avg_score and critique |
| `job_queue` | Job queue (queued/running/completed/failed/cancelled) |
| `todos` | Task management (title, description, priority, status, project, due_date, tags) |
| `notifications` | Push notification history |
| `hub_config` | Key-value configuration store |
| `users` | Admin/user accounts with bcrypt-hashed passwords |
| `scheduled_jobs` | Persisted scheduler jobs |
| `travel_trips` | Travel planning (destination, dates, budget, status) |
| `email_connectors` | IMAP/SMTP email integrations |
| `projects` | Project registry |
| `clients` | Client CRM entries |
| `conversations` | Chat conversation threads |
| `messages` | Per-conversation messages |
| `agent_memory` | Per-agent key-value memory |
| `daily_briefs` | Cached daily briefing documents |

---

## 8. Scheduler (hub_scheduler.py)

**Engine:** APScheduler AsyncIOScheduler  
**Timezone:** America/Chicago (CT)

| Job ID | Schedule | Description |
|---|---|---|
| `daily_briefing` | Daily 6:50 AM CT | Pre-compute morning briefing |
| `daily_reflexion` | Daily 7:00 AM CT | Generate daily reflexion report |
| `grant_research_sweep` | Monday 8:00 AM CT | Grant research across all orgs (4 agents) |
| `hutto_planning_monitor` | Monday 8:30 AM CT | Hutto city/county planning monitor (YEPC) |
| `weekly_fare_alert` | Monday 1:30 PM CT | Travel fare deals from AUS |
| `sigma_signal_check` | Daily 2:00 PM CT | Sigma Signal submission inbox check |
| `nightly_db_cleanup` | Daily 2:00 AM CT | Remove runs older than 90 days |

User-defined scheduled jobs also supported via `/api/scheduler` CRUD.

---

## 9. Desktop Application (main_m365.py)

### 9.1 Design System
**Microsoft 365-inspired layout:**
- Narrow left nav rail (icon navigation like Teams/Outlook)
- Wide content area split into Command + Detail panes
- Fluent Design colour tokens

**Brand Palette (ArchonHub Official):**
| Token | Hex | Usage |
|---|---|---|
| `BG_CANVAS` | `#0B0F17` | App canvas (Carbon Black) |
| `BG_RAIL` | `#080C13` | Left nav rail |
| `BG_PANEL` | `#111827` | Cards, panels |
| `BG_CARD` | `#0A1F44` | Elevated card (Deep Space Blue) |
| `ACCENT` | `#00B8FF` | Electric Blue (primary brand) |
| `ACCENT_LIGHT` | `#2DD4FF` | Neon Blue |
| `SUCCESS` | `#22c55e` | Green |
| `WARNING` | `#f59e0b` | Amber |
| `ERROR` | `#ef4444` | Red |
| `TEXT_PRIMARY` | `#D9E3F0` | Metallic Silver |

### 9.2 Navigation Sections (Left Rail)
1. **Home** — Agent grid + quick run
2. **Runs** — Run history, live execution log
3. **Todos** — Task management
4. **Daily Digest** — Morning briefing from Hub
5. **Schedule** — Scheduler jobs viewer
6. **Clients** — S2T Designs client roster
7. **Travel** — Trip planning
8. **Connectors** — Email integrations
9. **Admin** — PIN-locked (PIN: `1914`) — Hub control panel, LLM config, users

### 9.3 Hub Integration
- Connects to Hub via `HubClient` on startup
- Auto-reconnects every 30 seconds when Hub offline
- Falls back to embedded LangGraph execution when Hub offline (no features lost)
- Polls WebSocket events for real-time UI updates

### 9.4 LLM Selection
- Multi-provider support: OpenAI, Anthropic, local
- Configurable per-session and via Admin panel

### 9.5 Admin Panel (PIN-gated)
- 5-tab layout behind PIN `1914`
- Hub Control: start/stop/status
- Config: API keys, model selection, thread pool
- Users: manage Hub user accounts
- Scheduler: view/trigger jobs
- Logs: live log viewer

---

## 10. Web Dashboard (web/index.html)

**Single-file SPA** served from Hub at `http://localhost:8765/web`

### 10.1 Design
- Same ArchonHub brand palette as desktop app
- Inter / Segoe UI font stack
- Responsive sidebar (collapsible to 56px on mobile)
- CSS variables for full theming
- Radial gradient background `rgba(0, 184, 255, 0.12)`

### 10.2 Pages / Tabs
1. **Dashboard** — Health stats, active runs, pending todos
2. **Runs** — Agent run history with status badges
3. **Queue** — Live job queue with cancel controls
4. **Agents** — Skill viewer, run dispatcher
5. **Todos** — Full CRUD with priority/status filters
6. **Schedule** — Scheduler jobs and next-fire times
7. **Clients** — Client directory
8. **Projects** — Project registry
9. **Connectors** — Email connector management
10. **Travel** — Trip planner
11. **Briefing** — Daily digest view
12. **Chat** — Conversation interface
13. **Settings / Admin** — Hub config, users, API token

### 10.3 Authentication
- JWT login screen (username + password)
- Token stored in `localStorage`
- Auto-redirect to login when token missing/expired
- WebSocket connection established post-login

### 10.4 Real-time Updates
- WebSocket connection to `ws://localhost:8765/ws`
- Live run progress via `node_update` events
- Todo list auto-refreshes on `todo_update` events
- Notification toast on `notif` events

---

## 11. Agent Registry

### 11.1 Teams & Agents

| Team | Emoji | Agents |
|---|---|---|
| Business Law | ⚖️ | business-law-project-lead, entity, contracts, IP, employment, real-estate, regulatory |
| XFTC | 🏃 | xftc-project-lead, plugin-dev, frontend-dev, payments, qa |
| Grants / YEPC | 📋 | grants-research, grant-writer, yepc-grant-writer, yepc-real-estate-research, yepc-PM |
| S2T Designs | 🎨 | s2t-project-lead, webdev, seo |
| SmithCap Finance | 💰 | finance-cfo, cpa, tax-strategist, bookkeeper, advisor |
| Ministry | ✝️ | ministry-project-lead, sermon-writer |
| Social Media | 📱 | social-project-lead, content-strategist, copywriter, ads-manager |
| Solar | ☀️ | solar-project-lead, marketing |
| Sigma Signal | Σ | sigma-signal-project-lead, writer |
| Holdings | 🏢 | holdings-project-lead, legal, finance, tax, compliance |
| **Markets** | 📈 | markets-project-lead, cio, cro, options-strategist, quant, intelligence-desk, equity-analyst, macro-analyst, tactical-alpha, technical-analyst |
| **Nutrue** | 👕 | nutrue-project-lead, brand, ecommerce, finance, inbro-retrofit, legal, marketing |
| **Night King** | 👑 | nightking-project-lead, brand, design, media |
| **PBS Foundation** | 🏛️ | pbs-project-lead, board, communications, fundraising, legal, programs |
| **Elevation** | 🎭 | elevation-project-lead, brand, events, funding, legal, marketing |

**Total:** 15 teams, 70+ registered agents, 116+ .md skill files on disk

### 11.2 Skill File Location
```
.agents/agents/projects/<project-slug>/<agent-id>.md
```
- Read dynamically — no hardcoded paths in Hub
- Auto-discovered via `rglob(f"{agent_id}.md")` in `hub_nodes.py`
- Updated on disk when skill auto-upgrades (score < 0.75)

---

## 12. Projects List

```python
PROJECTS = [
    "xftc", "yepc", "pbs-foundation", "s2tdesigns", "smithcap", "smithcap-finance",
    "ministry", "business-law", "social-media", "solar-repair", "sigma-signal",
    "nutrue", "the-elevation", "travel", "holdings", "markets", "nightking"
]
```

---

## 13. Launch & Start

### Windows
```powershell
# Full stack (hub + desktop)
powershell -ExecutionPolicy Bypass -File launch_v3.ps1

# Hub only (headless)
powershell -ExecutionPolicy Bypass -File .agents\agentharness\app\v3\hub_start.ps1

# Desktop only (assumes hub already running)
powershell -ExecutionPolicy Bypass -File .agents\agentharness\app\v3\start.ps1
```

### Manual
```bash
# Hub
cd .agents/agentharness/app/v3
python hub_server.py

# Desktop (separate terminal)
python main_m365.py
```

### Access
- Web dashboard: `http://localhost:8765/web`
- API docs: `http://localhost:8765/docs`
- WebSocket: `ws://localhost:8765/ws`

---

## 14. Security Notes

- JWT secret key: `archonhub-jwt-secret-change-in-production-2024` (**change in production**)
- Default admin: `admin` / `ArchonHub2024!` (**change after first login**)
- Admin PIN: `1914` (desktop app only)
- API token auto-generated on first start, stored in `hub_config`
- CORS: open (local-first; lock down for production deployments)

---

## 15. File Structure Summary

```
repo root/
├── launch_v3.ps1                  # Root launch shortcut
├── .agents/
│   ├── .env                       # API keys
│   ├── agentharness/
│   │   ├── app/v3/               # ArchonHub app (all source)
│   │   └── memory/runs_v3.db     # SQLite database
│   ├── agents/projects/           # 116+ agent .md skill files
│   ├── data/logs/                 # Runtime logs
│   └── projects/                  # Project docs, specs, assets
└── _archive/                      # Legacy v1/v2 (not active)
```

---

## 16. iOS & Apple Watch Application

**Project location:** `projects/archonhub-ios/`  
**Requirements:** Xcode 15+, iOS 17+, watchOS 10+  
**No external dependencies** — pure Apple frameworks (SwiftUI, Combine, Foundation, ClockKit, WatchKit)

### 16.1 Architecture

```
projects/archonhub-ios/
├── ArchonHub/                     # iPhone app target
│   ├── App/
│   │   ├── ArchonHubApp.swift     # @main entry, auth gate
│   │   └── ContentView.swift      # TabView navigation (5 tabs)
│   ├── Models/
│   │   └── Models.swift           # Codable model structs
│   ├── Network/
│   │   ├── HubClient.swift        # REST + WebSocket client (singleton)
│   │   └── AuthStore.swift        # JWT auth state (ObservableObject)
│   ├── Views/
│   │   ├── Dashboard/             # DashboardView + ViewModel
│   │   ├── Runs/                  # RunsView + RunDetailView
│   │   ├── Todos/                 # TodosView + AddTodoView
│   │   ├── Briefing/              # BriefingView
│   │   ├── Chat/                  # ChatView
│   │   └── Settings/              # SettingsView
│   └── Resources/
│       └── Assets.xcassets/       # Icons from branding/ios/
├── ArchonHubWatch/                # Apple Watch target
│   ├── App/
│   │   ├── ArchonHubWatchApp.swift
│   │   └── WatchMainView.swift    # TabView (vertical paging)
│   ├── Views/
│   │   ├── WatchStatusView.swift  # Hub status glance
│   │   ├── WatchQuickRunView.swift# Quick agent dispatch
│   │   └── WatchNotificationsView.swift
│   ├── Complications/
│   │   └── ArchonHubComplication.swift  # ClockKit complication
│   └── Resources/
│       └── Assets.xcassets/
├── ArchonHub.xcodeproj/
└── README.md
```

### 16.2 iPhone Features

| Tab | View | API Endpoints |
|---|---|---|
| Dashboard | Stats grid, recent runs, Hub status | `GET /api/health`, `GET /api/runs?limit=5` |
| Runs | Run list + detail, cancel control | `GET /api/runs`, `POST /api/runs/{id}/cancel` |
| Todos | CRUD list, swipe actions, add form | `GET/POST/PUT/DELETE /api/todos` |
| Briefing | Daily digest full-text display | `GET /api/briefing` |
| Settings | Server URL, logout, about | `GET/PUT /api/config` |

### 16.3 Apple Watch Features

| Screen | Description |
|---|---|
| Status | Hub online/offline, active runs count, pending todos |
| Quick Run | Agent picker + task dispatch → `POST /api/runs` |
| Notifications | Last 5 notifications from `GET /api/notifications` |
| Complication | Active run count or pending todo count (gauge/text) |

### 16.4 Network Layer

- **Base URL:** Configurable, default `http://localhost:8765`
- **Auth:** JWT Bearer token stored in UserDefaults (Keychain recommended for production)
- **WebSocket:** `ws://<host>/ws` — receives `node_update`, `notif`, `todo_update`, `run_completed` events
- **Retry:** Auto-reconnect WebSocket on disconnect (5s backoff)
- All network calls use `async/await` + `URLSession`
- JSON decoding uses `convertFromSnakeCase` strategy

### 16.5 Branding Assets

App icons sourced from:
- iPhone: `branding/ios/AppIcon.appiconset/` (all sizes 20pt → 1024pt)
- Watch: `branding/watch/AppIcon.appiconset/`
- Watch complication: `branding/watch/complication-logo.png`

### 16.6 Build & Run

```bash
# Open in Xcode
open projects/archonhub-ios/ArchonHub.xcodeproj

# Ensure Hub server is running first
python .agents/agentharness/app/v3/hub_server.py

# Default credentials
# Username: admin
# Password: ArchonHub2024!
```

