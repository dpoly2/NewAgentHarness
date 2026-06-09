# [AppName] — AI Agent Harness Platform
# Product Requirements Document Template
#
# USAGE: Replace all [PLACEHOLDER] values with your project-specific details.
# This template is based on ArchonHub v1.1.0 and covers a full 5-surface
# AI agent orchestration platform: Server, Desktop, Web, iOS, Watch.
#
# ─────────────────────────────────────────────────────────────────────────────

**Version:** 1.0.0
**Last Updated:** [DATE]
**Owner:** [OWNER / ORGANIZATION]

---

## 1. Overview

[AppName] is an always-on AI agent orchestration platform for managing a portfolio of projects, clients, agents, and scheduled automations. It consists of five surfaces:

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
    │   │   ├── hub_server.py       # FastAPI server (port [PORT])
    │   │   ├── hub_db.py           # SQLite database layer (WAL mode)
    │   │   ├── hub_nodes.py        # LangGraph node functions (shared)
    │   │   ├── hub_scheduler.py    # APScheduler job engine
    │   │   ├── hub_client.py       # Desktop ↔ Hub HTTP/WS client
    │   │   ├── main_m365.py        # Tkinter desktop app
    │   │   ├── ah_logging.py       # Structured per-module logging
    │   │   ├── web/index.html      # Single-file web dashboard
    │   │   ├── requirements.txt
    │   │   ├── start.ps1
    │   │   ├── hub_start.ps1
    │   │   └── launch_v3.ps1       # Root launch shortcut
    │   └── memory/
    │       └── runs_v3.db          # SQLite database
    ├── agents/projects/            # Agent skill .md files
    │   └── [project-slug]/
    │       └── [agent-id].md
    ├── data/
    │   └── logs/
    └── .env                        # API keys and config
projects/
└── [appname]-ios/                  # SwiftUI iOS + Watch app
branding/
└── [platform]/                     # Brand assets per platform
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
bcrypt>=4.0.0
python-jose[cryptography]>=3.3.0

# Utilities
requests>=2.31.0
python-dotenv>=1.0.0
python-dateutil>=2.8.0
markdown>=3.5
```

**Runtime:** Python 3.11+

---

## 4. Environment Variables (.agents/.env)

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | OpenAI key for LangGraph LLM calls |
| `ANTHROPIC_API_KEY` | Optional | Claude model support |
| `OPENAI_MODEL` | Optional | Default: `gpt-4o-mini` |
| `HUB_PORT` | Optional | Default: `[PORT]` |
| `ADMIN_PASSWORD` | Optional | Override default admin password |

---

## 5. Hub Server Requirements (hub_server.py)

### 5.1 General
- FastAPI application running on **port [PORT]**
- REST API at `/api/...`, WebSocket at `/ws`, Web dashboard at `/web`
- Auto-docs at `/docs` (Swagger UI)
- CORS enabled for all origins (local-first design)
- Startup: creates SQLite schema, seeds default admin, starts scheduler
- Graceful shutdown via SIGINT/SIGTERM

### 5.2 Authentication
- **JWT-based auth** using `python-jose`, 24-hour token expiry
- `POST /api/auth/login` — returns JWT token
- `POST /api/auth/register` — create new user (admin-only after first user)
- `GET /api/auth/me` — current user info
- **Admin PIN** — `[ADMIN_PIN]` — used in desktop app only
- Default admin: username `admin`, password `[DEFAULT_PASSWORD]`
- Bearer token auth on all `/api/` endpoints

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

### 5.5 WebSocket (ws://localhost:[PORT]/ws)
- JWT auth on connect
- Real-time events: `run_started`, `run_completed`, `run_failed`, `run_cancelled`, `node_update`, `notif`, `todo_update`, `briefing_ready`
- Ping/pong heartbeat: 30s interval, 10s timeout

### 5.6 Thread Pool
- Default 3 concurrent agent execution threads
- Configurable via hub config API

---

## 6. LangGraph Execution Engine (hub_nodes.py)

### 6.1 Graphs (4 built-in)

| Graph Key | Nodes | Use Case |
|---|---|---|
| `reflexion` | load_memory → act → evaluate → [revise*] → save_memory | General tasks |
| `research` | load_memory → plan → search → synthesize → evaluate → [revise*] → save_memory | Research tasks |
| `wordpress` | load_memory → wp_plan → wp_implement → wp_verify → evaluate → [revise*] → save_memory | WP dev |
| `business-law` | load_memory → legal_analyze → legal_draft → legal_review → evaluate → [revise*] → save_memory | Legal docs |

- Reflexion loop: score < 0.75 triggers revision; default max 2 revisions
- Skill auto-upgrade when score < threshold
- Cancel flag (threading.Event) checked between nodes

---

## 7. Database Schema (SQLite / WAL mode)

| Table | Purpose |
|---|---|
| `runs` | Agent execution history |
| `skills` | Agent skill versions + scores |
| `job_queue` | Pending/active job queue |
| `todos` | Task management |
| `notifications` | Push notification history |
| `hub_config` | Key-value configuration |
| `users` | User accounts |
| `scheduled_jobs` | Persisted scheduler jobs |
| `travel_trips` | Travel planning |
| `email_connectors` | IMAP/SMTP integrations |
| `projects` | Project registry |
| `clients` | Client CRM |
| `conversations` | Chat threads |
| `messages` | Per-conversation messages |
| `agent_memory` | Per-agent key-value memory |
| `daily_briefs` | Cached briefing documents |

---

## 8. Scheduler (hub_scheduler.py)

**Engine:** APScheduler AsyncIOScheduler
**Timezone:** [TIMEZONE] (e.g. America/Chicago)

Define your scheduled jobs here:

| Job ID | Schedule | Description |
|---|---|---|
| `daily_briefing` | Daily [TIME] | Pre-compute morning briefing |
| `daily_reflexion` | Daily [TIME] | Generate daily reflexion report |
| `nightly_db_cleanup` | Daily 2:00 AM | Remove runs older than 90 days |
| `[custom_job_1]` | [CRON_EXPR] | [DESCRIPTION] |
| `[custom_job_2]` | [CRON_EXPR] | [DESCRIPTION] |

---

## 9. Desktop Application (main_m365.py)

### 9.1 Design System
Microsoft 365-inspired layout:
- Narrow left nav rail (icon navigation)
- Wide content area: Command + Detail panes
- Fluent Design colour tokens

### 9.2 Brand Palette
| Token | Hex | Usage |
|---|---|---|
| `BG_CANVAS` | `[HEX]` | App canvas |
| `BG_RAIL` | `[HEX]` | Left nav rail |
| `BG_PANEL` | `[HEX]` | Cards, panels |
| `BG_CARD` | `[HEX]` | Elevated card |
| `ACCENT` | `[HEX]` | Primary brand color |
| `SUCCESS` | `[HEX]` | Success state |
| `WARNING` | `[HEX]` | Warning state |
| `ERROR` | `[HEX]` | Error state |
| `TEXT_PRIMARY` | `[HEX]` | Primary text |

### 9.3 Navigation Sections (Left Rail)
Customize for your project:
1. **Home** — Agent grid + quick run
2. **Runs** — Run history, live execution log
3. **Todos** — Task management
4. **Daily Digest** — Morning briefing
5. **Schedule** — Scheduler jobs
6. **Clients** — Client roster
7. **Travel** — Trip planning
8. **Connectors** — Email integrations
9. **Admin** — PIN-locked control panel

### 9.4 Admin Panel
- PIN-gated (set `ADMIN_PIN`)
- 5 tabs: Hub Control, Config, Users, Scheduler, Logs

---

## 10. Web Dashboard (web/index.html)

**Single-file SPA** served at `http://localhost:[PORT]/web`

### Pages
1. Dashboard — Health stats, active runs, todos
2. Runs — Run history with status badges
3. Queue — Live job queue + cancel
4. Agents — Skill viewer, run dispatcher
5. Todos — CRUD with filters
6. Schedule — Scheduler jobs
7. Clients — Client directory
8. Projects — Project registry
9. Connectors — Email connector management
10. Travel — Trip planner
11. Briefing — Daily digest
12. Chat — Conversation interface
13. Settings / Admin — Config, users, API token

### Auth
- JWT login (stored in localStorage)
- WebSocket post-login for real-time updates
- Auto-redirect to login on token expiry

---

## 11. Agent Registry

Define your teams and agents:

```python
AGENT_REGISTRY = {
    "[Team Name]": ["[agent-id-1]", "[agent-id-2]", ...],
    # Add teams and agents for your project
}

PROJECTS = ["[project-slug-1]", "[project-slug-2]", ...]
```

Skill files location: `.agents/agents/projects/<project-slug>/<agent-id>.md`

---

## 12. iOS & Apple Watch Application

**Location:** `projects/[appname]-ios/`
**Requirements:** Xcode 15+, iOS 17+, watchOS 10+

### iPhone Features
| Tab | API Endpoints |
|---|---|
| Dashboard | `GET /api/health`, `GET /api/runs?limit=5` |
| Runs | `GET /api/runs`, `POST /api/runs/{id}/cancel` |
| Todos | `GET/POST/PUT/DELETE /api/todos` |
| Briefing | `GET /api/briefing` |
| Settings | Server URL, logout |

### Watch Features
| Screen | Description |
|---|---|
| Status | Hub online/offline, run count, todo count |
| Quick Run | Agent picker + dispatch |
| Notifications | Last 5 notifications |
| Complication | Active runs or todo count |

### Network
- Base URL: configurable (default `http://localhost:[PORT]`)
- JWT Bearer token in UserDefaults
- WebSocket auto-reconnect (5s backoff)
- `async/await` + `URLSession`, no external dependencies

---

## 13. Branding Assets

```
branding/
├── master/         # Full logo, brandmark, wordmark (PNG + SVG)
├── web/            # favicon.ico, favicon-192/512.png, logo.svg, sidebar-logo.svg, login-banner.png
├── desktop/        # app-icon.ico, tray-icon.ico, splash.png
├── ios/            # AppIcon.appiconset/ (all sizes), launch-screen.png
├── watch/          # AppIcon.appiconset/, complication-logo.png
├── social/         # Social media assets
└── marketing/      # Hero banners, App Store previews
```

---

## 14. Security Notes

- JWT secret: change in production
- Default admin credentials: change after first login
- Admin PIN: desktop app only
- API token auto-generated on first start
- CORS: open for local dev; lock down for production

---

## 15. Launch

### Windows
```powershell
# Full stack (hub + desktop)
powershell -ExecutionPolicy Bypass -File launch_v3.ps1

# Hub only
powershell -ExecutionPolicy Bypass -File .agents\agentharness\app\v3\hub_start.ps1

# Desktop only
powershell -ExecutionPolicy Bypass -File .agents\agentharness\app\v3\start.ps1
```

### Access
- Web dashboard: `http://localhost:[PORT]/web`
- API docs: `http://localhost:[PORT]/docs`
- WebSocket: `ws://localhost:[PORT]/ws`

---

## 16. Verification Checklist

- [ ] `python hub_server.py` starts on port [PORT]
- [ ] `GET /api/health` returns `{"status":"ok","app":"[AppName]",...}`
- [ ] `http://localhost:[PORT]/web` loads login page
- [ ] Login with default credentials succeeds
- [ ] POST `/api/runs` enqueues and runs a job
- [ ] WebSocket connects and receives events
- [ ] Desktop app launches with M365 nav rail
- [ ] Hub online indicator shows green
- [ ] Admin PIN unlocks Admin panel
- [ ] Scheduler shows built-in jobs
- [ ] iOS app builds in Xcode without errors
- [ ] Watch app registers complication
