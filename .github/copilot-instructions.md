# AgentHarness — Copilot Instructions

## Architecture Overview

AgentHarness is a multi-agent AI operating system built on two parallel planes:

1. **Base44 Superagent** — The primary cloud runtime. Agents are configured and run at `app.base44.com`. Agent skill files, rules, and memory live in `.agents/` and are sync'd to Base44.

2. **ArchonHub (local engine)** — A self-hosted Python engine in `.agents/agentharness/app/v3/`. It runs a FastAPI hub server + SQLite DB + Tkinter desktop UI as an alternative/complement to Base44.

### Directory Map

```
.agents/
  agentharness/           # Local Python engine (ArchonHub)
    app/v3/               # ArchonHub server — modular package layout
      hub_server.py       # ~245-line app factory (lifespan + router registration + /ws)
      core/               # Shared internals — no routes
        config.py         # Paths, env vars, constants (DB_PATH, SECRET_KEY, CORS_ORIGINS)
        database.py       # SQLite connection, CRUD helpers, schema init
        auth.py           # JWT, passwords, get_current_user, login rate limiter
        hub.py            # HubServer class, 5 DB-backed workers, ws_events broadcast, make_emit
        models.py         # All 30+ Pydantic request/response models
      routers/            # 28 domain APIRouter files (~200 lines each)
        auth_routes.py    # /api/auth/*
        runs.py           # /api/runs, /api/queue
        agents.py         # /api/agents CRUD + collaborate + capabilities
        inez.py           # /api/inez/*
        memory.py         # /api/memory + /api/memory/global
        todos.py          # /api/todos
        notifications.py  # /api/notifications + /api/monitoring/notifications
        connectors.py     # /api/connectors + OAuth callbacks
        projects.py       # /api/projects + /api/clients
        conversations.py  # /api/conversations + messages
        scheduler.py      # /api/scheduler
        skills.py         # /api/skills
        briefing.py       # /api/briefing + /api/briefs + morning/history
        files.py          # /api/files + /api/files/_search
        feedback.py       # /api/feedback + /api/corrections
        email_cleanup.py  # /api/email/cleanup/*
        knowledge.py      # /api/knowledge + /api/documents + /api/integrations
        sandbox.py        # /api/sandbox
        intelligence.py   # /api/intelligence
        reports.py        # /api/reports
        models_api.py     # /api/models (catalog, toggle, providers)
        config_api.py     # /api/config + /api/stats + /api/health
        users.py          # /api/users
        automations.py    # /api/automations
        search.py         # /api/search + /api/context + /api/events
        prompt_templates.py # /api/prompt-templates
        providers.py      # /api/providers + /api/import
        trips.py          # /api/trips
      hub_db.py           # SQLite schema migrations (legacy layer)
      hub_nodes.py        # LangGraph node functions
      hub_scheduler.py    # APScheduler job definitions
      web/                # Single-file web dashboard
      tests/              # Test suites
    graphs/               # LangGraph agent graphs (reflexion_loop, research_graph, wordpress_graph)
    nodes/                # Individual graph nodes (act, evaluate, revise, memory)
    state/                # AgentState TypedDict
    memory/               # SQLite DB (runs_v3.db) + per-agent .txt memory files
  agents/projects/        # Skill files per project/agent — one .md per agent
  rules/                  # Standing rules auto-loaded into every agent session
  skills/                 # Reusable Python scripts (agent_logger.py, github_push.js)
  mcps/config.json        # MCP server configuration (currently empty)
  .env                    # Runtime secrets (copy from .env.example)
  .memory/                # Conversation logs and agent memory

projects/
  archonhub-ios/          # iOS + Apple Watch app (Xcode, bundle: com.smithcapital.archonhub)
  xftc-redevelopment/     # WordPress plugin + theme (PHP)
  pbs/                    # PBS Foundation files
  yepc/                   # YEPC real estate development
```

## Running the System

**Start full stack (hub + desktop):**
```powershell
.\launch_v3.ps1
```

**Start hub server only:**
```powershell
python .agents\agentharness\app\v3\hub_server.py
```
Hub runs on port `8765` by default (`HUB_PORT` in `.env`).
- Web dashboard: `http://localhost:8765/web`
- API docs: `http://localhost:8765/docs`
- Health check: `http://localhost:8765/api/health`

**Environment setup:**
```powershell
cp .agents\.env.example .agents\.env   # then fill in values
# Python venv expected at .venv\
```

## Tests (ArchonHub Python engine)

All tests live in `.agents/agentharness/app/v3/tests/`.

```powershell
cd .agents\agentharness\app\v3\tests

# Run all suites
python run_tests.py

# Run a single suite
python run_tests.py db        # SQLite layer
python run_tests.py server    # FastAPI endpoints
python run_tests.py markets   # Paper trading
python run_tests.py oauth     # OAuth connector
python run_tests.py ui        # Tkinter surfaces

# Fast mode — unit tests only (skips server + ui)
python run_tests.py --fast

# Verbose output
python run_tests.py --verbose
```

## PHP (PBS Plugin)

CI runs on pushes to `.agents/projects/xftc-plugin-product/pbs-ticketing/plugin/pbs-event-commerce/**`.

```bash
# Syntax lint (PHP 7.4 / 8.1 / 8.2)
find . -name "*.php" -not -path "./vendor/*" -exec php -l {} \;

# Static analysis
vendor/bin/phpstan analyse --level=5 includes/

# Unit tests
vendor/bin/phpunit --testdox
```

## Core LangGraph Architecture

The **reflexion loop** is the central agent execution pattern:

```
load_memory → act → evaluate → save_memory
                        ↓ (score < threshold)
                     revise → act (loops until score passes)
```

- `graphs/reflexion_loop.py` — wires the graph; entry point `build_reflexion_graph(adapter)`
- `graphs/research_graph.py` / `graphs/wordpress_graph.py` — domain-specific variants
- Adapters: `Base44Adapter` (cloud) or `LocalAdapter` (SQLite) — both satisfy the same interface

## Key Conventions

### Agent IDs
Follow the pattern `<project>-<role>`. Always use the exact IDs from `.agents/rules/agent-logging-protocol.md`:
```
xftc-plugin-dev, markets-cro, pbs-project-lead, finance-cfo, etc.
```

### Skill Files
Each agent has one skill file at `.agents/agents/projects/<project>/<agent>.md`. These are the agent's system prompt + behavioral rules. When a run scores **< 0.75**, the skill file must be revised and a new version logged to `AgentSkillVersion`.

### Reflexion Scoring
Every agent run is scored and logged to `AgentRunLog`:
```
overall = completion * 0.5 + quality * 0.35 + efficiency * 0.15
```
| Score | Action |
|-------|--------|
| ≥ 0.90 | No action |
| 0.75–0.89 | Minor note |
| 0.60–0.74 | Flag for review |
| < 0.60 | Revise skill file, log new version to `AgentSkillVersion` |

### LLM Routing
`llm_router.py` routes by skill type — **Ollama-first** (localhost:11434), cloud fallback. Default cloud model: `gpt-4o-mini` (override via `OPENAI_MODEL` in `.env`). Per-agent model overrides are stored in `agent_registry.config`.

### WordPress Credentials
Always stored in `.agents/.env` — never hardcoded. WordPress agents use app passwords (not login passwords).

### ArchonHub iOS CI
- Build number (`CURRENT_PROJECT_VERSION`) auto-increments on every push to `main` via `archonhub-build-bump.yml`. Commit messages containing `[build-bump]` are skipped to prevent loops.
- TestFlight deploys trigger on tags matching `archonhub/v*`.

### BOOTSTRAP.md
`.agents/BOOTSTRAP.md` is the first-run onboarding script for new agent sessions. It should be deleted after the agent has (1) completed at least one real task and (2) saved an agent name to `IDENTITY.md`. Do not modify it for permanent behavior changes — put those in `.agents/rules/` instead.

### ArchonHub Server — Security Posture (v1.2)
Key rules enforced server-side — do not regress these:
- **5 workers** — DB-backed queue + broadcast; APScheduler leader lock prevents duplicate scheduler execution.
- **JWT secret** — server logs a startup warning if `JWT_SECRET` is still the default. Change it in `.agents/.env` for any non-personal deployment.
- **CORS** — production CORS is locked to `https://app.archonhub.app` via `CORS_ORIGINS` in `.env`. Localhost origins are allowed for local dev.
- **Login rate limiting** — `POST /api/auth/login` returns HTTP 429 after 10 attempts from the same IP within 5 minutes.
- **WebSocket auth timeout** — the server closes the connection with code 1008 if the client does not send `{"type":"auth","token":"..."}` within 15 seconds.
- **All routes require Bearer JWT** — only `/api/auth/login`, `/api/auth/register`, and `/` are public. Routes that were previously open (capabilities, collaborate, conversation history) now require auth.
- **Renamed endpoints** — `/api/files/search` is now `/api/files/_search`; the second notifications handler is `/api/monitoring/notifications` (not `/api/notifications`).

### MCP Servers
Configured in `.agents/mcps/config.json`. Currently empty; add MCP server entries there to enable tool extensions.


### Market Team and Scheduler
- The markets project now uses the **Tactical Alpha Market Intelligence Division V2**: 31 agents across 9 departments, with skill files under `.agents/agents/projects/markets/`.
- `hub_scheduler.py` carries the full market cadence: morning pipeline (5:30-8:15 AM CT), hourly monitoring (10:00 AM-3:30 PM CT), end-of-day review (4:00-4:45 PM CT), weekly Monday rollups, and first-Monday monthly optimization jobs.
- Capitol Trades is part of the smart-money automation layer: a 9:00 AM disclosure refresh and 9:30 AM Congress Edge digest route lagged public signals to the markets team and CRO.
- Alpaca is the downstream execution endpoint after Tactical Alpha synthesis, probability validation, and CRO approval; treat it as execution infrastructure, not thesis generation.
