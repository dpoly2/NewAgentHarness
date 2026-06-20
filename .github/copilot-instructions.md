# AgentHarness — Copilot Instructions

## Architecture Overview

AgentHarness is a multi-agent AI operating system built on two parallel planes:

1. **Base44 Superagent** — The primary cloud runtime. Agents are configured and run at `app.base44.com`. Agent skill files, rules, and memory live in `.agents/` and are sync'd to Base44.

2. **ArchonHub (local engine)** — A self-hosted Python engine in `.agents/agentharness/app/v3/`. It runs a FastAPI hub server + SQLite DB + Tkinter desktop UI as an alternative/complement to Base44.

### Directory Map

```
.agents/
  agentharness/           # Local Python engine (ArchonHub)
    app/v3/               # Hub server, desktop app, LLM router, tests
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

### MCP Servers
Configured in `.agents/mcps/config.json`. Currently empty; add MCP server entries there to enable tool extensions.
