# ArchonHub — AI Agent Operating System

**Version:** 3.0  
**Updated:** June 2026  
**Status:** Active Development

ArchonHub is a self-hosted, multi-agent AI operating system with a FastAPI backend, SQLite database, iOS/watchOS client, and a growing suite of autonomous agents. Agents can browse the web, execute code, manage email, trade paper options, write content, and proactively monitor your world — all driven by a persistent Global Memory of 160+ personal facts extracted from your history.

---

## Architecture

```
NewAgentHarness/
├── .agents/agentharness/
│   ├── app/v3/                  # Hub Server + all agent modules
│   │   ├── hub_server.py        # FastAPI server (port 8765, JWT auth)
│   │   ├── hub_db.py            # SQLite schema + migrations
│   │   ├── hub_scheduler.py     # Background task scheduler
│   │   ├── inez_agent.py        # Inez — Chief of Staff AI
│   │   ├── agent_runner.py      # Agent execution engine
│   │   ├── agent_orchestrator.py# Multi-agent coordination
│   │   ├── global_memory.py     # Personal memory engine (160+ facts)
│   │   ├── code_sandbox.py      # Python execution sandbox (AST security)
│   │   ├── web_search.py        # SerpAPI web search integration
│   │   ├── email_analyzer.py    # Email cleanup analysis
│   │   ├── email_executor.py    # Email bulk action execution
│   │   ├── document_rag.py      # Document RAG (vector search)
│   │   ├── markets_tab.py       # Markets + options data
│   │   ├── paper_trading.py     # Paper trading engine
│   │   ├── morning_brief.py     # Daily briefing generator
│   │   ├── llm_router.py        # Multi-provider LLM routing
│   │   ├── free_llm_keys.py     # Free LLM key pool management
│   │   ├── model_catalog.py     # LLM model catalog
│   │   ├── proactive_monitor.py # Proactive event monitoring
│   │   ├── main_m365.py         # Microsoft 365 integration
│   │   └── oauth_connector.py   # OAuth2 for external services
│   └── memory/
│       ├── runs_v3.db           # SQLite database (gitignored)
│       ├── inez-chief-of-staff.txt
│       ├── finance-cfo.txt
│       ├── markets-project-lead.txt
│       ├── sigma-signal-writer.txt
│       ├── solar-marketing-agent.txt
│       ├── travel-flights-agent.txt
│       ├── pbs-fundraising-agent.txt
│       ├── grants-research-agent.txt
│       ├── yepc-grant-writer-agent.txt
│       └── yepc-project-manager.txt  (+ 12 more agents)
├── projects/
│   ├── archonhub-ios/           # iOS + watchOS app (SwiftUI)
│   ├── pbs/                     # PBS WordPress plugin
│   ├── xftc-redevelopment/      # XFTC WordPress theme + plugin
│   ├── sigma-signal-*/          # Sigma Signal newsletter
│   └── yepc/                    # YEPC grant management
├── Dockerfile                   # Docker deployment
├── docker-compose.yml
└── .agents/.env                 # API keys (gitignored)
```

---

## Quick Start

### Local (macOS)

```bash
cd .agents/agentharness/app/v3

# Install dependencies
pip3 install fastapi uvicorn openai serpapi requests

# Configure API keys
cp ../.env.example ../.env   # then edit with your keys

# Start the server
python3 hub_server.py
# → Running at http://localhost:8765
```

### Docker

```bash
docker-compose up --build
# → Running at http://localhost:8765
```

### Environment Variables (`.agents/.env`)

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
SERPAPI_KEY=...          # Web search
HUB_PORT=8765
# Security — set these before exposing the server:
JWT_SECRET=<random-32-byte-hex>   # python -c "import secrets; print(secrets.token_hex(32))"
CORS_ORIGINS=https://app.archonhub.app,http://localhost:8765
```

---

## Features

### 🧠 Global Memory System
160+ personal facts extracted from 538 ChatGPT conversations using `gpt-4o-mini`. Automatically injected into every Inez prompt for personalised, context-aware responses.

- **Categories:** projects, technical, preferences, people, finance, ministry, rules, deadlines
- **API:** `GET/POST/PUT/DELETE /api/memory/global`
- **Auto-learning:** New facts extracted from agent conversations and stored automatically
- **iOS:** Browse, search, filter, create, edit, and delete facts from the Memory tab

### 🤖 Agents

| Agent | Identity | Capabilities |
|-------|----------|-------------|
| **Inez** | Chief of Staff | Orchestrates all agents, manages tasks, email, calendar |
| **Finance CFO** | CFO | Financial analysis, P&L, budgeting |
| **Markets** | Options Strategist | NVDA iron condors, covered calls, market analysis |
| **Sigma Signal** | Content Writer | Newsletter generation, SoulSpeak style content |
| **Solar Marketing** | Marketing Lead | Solar sales campaigns and lead generation |
| **Travel** | Travel Agent | Flight search, itinerary planning |
| **PBS Fundraising** | Fundraising Agent | PBS donor campaigns, event commerce |
| **Grants Research** | Grant Researcher | Multi-hop grant discovery for nonprofits |
| **YEPC Grant Writer** | Grant Writer | Full grant application drafting |
| **YEPC PM** | Project Manager | YEPC project tracking and coordination |

### 🐍 Code Execution Sandbox
Securely execute Python code server-side and return results to iOS.

- **Security:** AST-based import scanning blocks `os`, `sys`, `subprocess`, `socket`, etc.
- **Packages:** `pandas`, `numpy`, `matplotlib`, `scipy`, `sklearn` available
- **Output:** stdout, stderr, generated files (images, CSVs) returned as base64
- **Modes:** Docker (when available) → subprocess fallback
- **API:** `POST /api/sandbox/execute`, `GET /api/sandbox/status`

### 🔍 Web Search
SerpAPI-powered real-time web search integrated into agent workflows.

- Agents auto-search when answering questions about current events, prices, news
- Configurable via Settings in iOS app
- API: `POST /api/search`

### 📧 Email Cleanup
Intelligent email analysis and bulk cleanup with approval workflow.

- Analyses mailbox by sender, age, and size
- Generates cleanup plan with one-click approval
- Rollback support
- API: `GET/POST /api/email/cleanup`

### 📊 Markets & Paper Trading
Real-time market data, options chain analysis, and paper trading simulation.

- NVDA iron condor strategy tracking
- Paper portfolio management
- Morning market brief generation

### 📋 Microsoft 365 Integration
Full M365 integration via `main_m365.py`:
- Email read/send via Microsoft Graph API
- Calendar events and scheduling
- OneDrive file access
- Teams messaging

### ☀️ Daily Briefing
Automated morning brief combining:
- Pending todos and agent runs
- Market summary
- Calendar events
- Email highlights

---

## API Reference

### Authentication
All endpoints require JWT bearer token.
```
POST /api/auth/login  → { token }
GET  /api/auth/me
```

### Agents
```
GET    /api/agents                    # List all agents
POST   /api/runs                      # Start agent run
GET    /api/runs                      # Run history
GET    /api/runs/{id}                 # Run detail
GET    /api/dispatches                # Pending dispatches
POST   /api/dispatches/{id}/execute   # Execute dispatch
```

### Global Memory
```
GET    /api/memory/global             # List all facts (with counts)
POST   /api/memory/global             # Create fact
PUT    /api/memory/global/{id}        # Update fact
DELETE /api/memory/global/{id}        # Delete fact
GET    /api/memory/global/search?q=   # Search facts
POST   /api/memory/global/extract     # Extract facts from conversation
```

### Code Sandbox
```
POST /api/sandbox/execute    # Run Python code
GET  /api/sandbox/status     # Sandbox availability
```

### Other
```
GET  /api/todos               # Todos list
POST /api/todos               # Create todo
GET  /api/briefing            # Daily briefing
GET  /api/reports             # Agent reports
GET  /api/documents           # Document library
POST /api/documents/search    # RAG document search
GET  /api/models              # LLM model catalog
POST /api/search              # Web search
GET  /api/files/_search       # Semantic doc search (note: _search, not /search)
GET  /api/monitoring/notifications  # Proactive monitoring alerts
```

---

## iOS & Watch App

See [`projects/archonhub-ios/README.md`](projects/archonhub-ios/README.md) for the full iOS/watchOS client documentation.

---

## Database

SQLite at `.agents/agentharness/memory/runs_v3.db` (gitignored).

Key tables: `users`, `agent_runs`, `dispatches`, `todos`, `global_memory`, `documents`, `email_accounts`, `email_cleanup_plans`, `prompt_templates`, `feedback`, `messages`, `paper_trades`

---

## Security Notes

- `.agents/.env` is gitignored — never commit API keys
- `runs_v3.db` is gitignored — all personal memory stays local
- Code sandbox uses AST-level import blocking (no runtime monkey-patching)
- All API endpoints require JWT authentication
- Set `JWT_SECRET` in `.env` to a random value — server logs a security warning on startup if using the default
- Set `CORS_ORIGINS=https://app.archonhub.app,http://localhost:8765` in `.env` to restrict browser access (defaults to `*` when unset)
- Login endpoint is rate-limited: 10 attempts per IP per 5-minute window

