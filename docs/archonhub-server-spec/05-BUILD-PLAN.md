# 05-BUILD-PLAN

_Generated from the current ArchonHub source tree on 2026-07-03._

This plan rebuilds the ArchonHub server in deliberate dependency order. The current implementation couples auth, DB persistence, queueing, reflexion, Inez orchestration, scheduler leadership, and realtime fan-out tightly enough that skipping ahead would create false progress.

---

## Phase 0: Foundation (Week 1-2)

**Entry criteria**
- Empty or clean server workspace
- Python version and package manager selected
- Environment secret strategy chosen

**Deliverables**
- FastAPI app factory with lifespan hooks
- typed config module and `.env` loading
- SQLite connection layer
- core Pydantic request/response models
- base schema bootstrap
- JWT auth, register/login, password change
- login rate limiting
- `/api/health`

**Dependencies**
- none

**Acceptance tests**
- bootstrap first admin in an empty DB
- login returns a working bearer JWT
- `/api/auth/me` resolves the active user
- 11th failed login in 5 minutes returns 429
- `/api/health` responds without background loops crashing

---

## Phase 1: Agent Registry & Core CRUD (Week 3-4)

**Entry criteria**
- Phase 0 complete

**Deliverables**
- `agent_registry` CRUD
- `users` admin CRUD
- `projects` CRUD
- `clients` CRUD
- `todos` CRUD
- initial `/ws` auth + connection registry

**Dependencies**
- Phase 0

**Acceptance tests**
- CRUD endpoints round-trip JSON columns correctly
- admin-only routes reject non-admin callers
- todo mutations emit `todo_update` websocket events

---

## Phase 2: Memory & Knowledge (Week 5-6)

**Entry criteria**
- core CRUD resources working

**Deliverables**
- `agent_memory` helpers
- global memory CRUD/search/extract
- `knowledge_base` CRUD/search
- `documents` CRUD
- `integrations` CRUD with masked list responses
- file upload metadata and chunk storage
- messages FTS5 index and triggers

**Dependencies**
- Phase 1

**Acceptance tests**
- per-agent memory loads and saves
- global memory search returns stored facts
- `/api/search` returns FTS hits from seeded messages
- uploaded file delete removes chunk rows

---

## Phase 3: LLM Infrastructure (Week 7-8)

**Entry criteria**
- persistence and memory stable

**Deliverables**
- `free_llm_keys` activation/sync
- shared `_llm()` gateway
- `llm_router` with per-agent overrides
- model catalog endpoints
- AgentShield hooks
- Karpathy guideline injection
- `_RUNNER_INSTRUCTIONS` JSON output contract

**Dependencies**
- Phases 0-2

**Acceptance tests**
- model routing selects an enabled backend
- agent runner can execute with remote and local fallback paths
- AgentShield blocks known prompt-injection samples
- provider status shows active/stale free-key state

---

## Phase 4: Agent Execution Pipeline (Week 9-10)

**Entry criteria**
- LLM routing usable
- memory and skills available

**Deliverables**
- `run_agent()` end-to-end implementation
- DB write allowlist enforcement
- `run_dispatches()` helper
- LangGraph state object and nodes
- reflexion graph + graph selector
- `runs`, `job_queue`, `run_events`, `ws_events` integration
- progressive-intelligence post-run hook

**Dependencies**
- Phases 0-3

**Acceptance tests**
- `POST /api/runs` queues work that completes through workers
- low-score runs enter revise path before save_memory
- forbidden `db_writes` are blocked
- run progress can be replayed from `run_events`

---

## Phase 5: Inez + Dispatch (Week 11-12)

**Entry criteria**
- specialist execution pipeline verified

**Deliverables**
- `think()` orchestration flow
- travel/email/web-search prefetch hooks
- dispatch parsing and validation
- parallel specialist fan-out
- synthesis pass
- Inez exchange memory persistence
- GOAP plan generation for larger worksets
- `agent_result` and `inez_response` events

**Dependencies**
- Phases 2-4

**Acceptance tests**
- direct-answer requests return without dispatch
- multi-agent requests produce specialist results and final synthesis
- 3+ dispatches write a GOAP inbox plan
- synthesis-failure path still surfaces partial agent output

---

## Phase 6: Scheduler (Week 13-14)

**Entry criteria**
- queue, runs, and websocket events stable

**Deliverables**
- APScheduler wrapper
- `scheduled_jobs` persistence
- scheduler DB leader lease
- built-in `_JOB_SPECS` registration
- manual trigger API
- tracked last-run metadata
- current cadence families: daily brief/reflexion, markets V1/V2, Capitol Trades, cleanup, backup, free-key sync, log monitor

**Dependencies**
- Phases 0, 4, 5

**Acceptance tests**
- only one process owns scheduler leadership at a time
- manual trigger queues immediate work
- lease failover hands scheduling to another process
- built-in jobs remain single-fire during leadership transitions

---

## Phase 7: Domain Routers (Week 15-18)

**Entry criteria**
- shared runtime pieces stable

**Deliverables**
- conversations/messages
- briefs + morning brief history
- notifications + monitoring notifications
- automations + automation docs/runs
- reports
- prompt templates
- feedback + corrections
- search/context/events
- email cleanup
- sandbox
- users/admin surfaces

**Dependencies**
- Phases 1-6

**Acceptance tests**
- each router has contract tests for happy path + auth failures
- prompt-template system rows cannot be edited/deleted
- sandbox rejects oversized code payloads
- monitoring notifications can be listed and dismissed

---

## Phase 8: Integrations (Week 19-20)

**Entry criteria**
- domain routers and shared runtime complete

**Deliverables**
- Alpaca status/account/order/position sync
- Capitol Trades ingest and review flow
- OAuth connectors for Google/Gmail and Microsoft
- MCP config plumbing for Ruflo + Open Design
- Obsidian CLI memory hook
- provider import and free-key sync flows

**Dependencies**
- Phases 2-7

**Acceptance tests**
- OAuth callbacks persist active connector state
- Capitol Trades review can approve/reject signals
- Alpaca sync populates local position tables
- external failures degrade cleanly without DB corruption

---

## Phase 9: Intelligence Layer (Week 21-22)

**Entry criteria**
- real run and integration data flowing

**Deliverables**
- `agent_skill_levels`, `reflexion_log`, `interaction_patterns`
- intelligence summary/patterns/per-agent endpoints
- proactive monitoring + report-monitor hooks
- morning-brief generation parity
- market intelligence reporting surfaces

**Dependencies**
- Phases 4, 5, 6, 8

**Acceptance tests**
- repeated runs change skill tiers correctly
- low-score runs create reflexion log entries
- pattern detection surfaces repeated topics
- morning brief caches today's generated result

---

## Phase 10: Hardening (Week 23-24)

**Entry criteria**
- full feature surface present

**Deliverables**
- router and integration regression suite
- worker/scheduler concurrency profiling
- CORS lockdown for production origins
- insecure-default startup enforcement
- websocket auth-timeout verification
- DB write whitelist review
- backup/restore validation
- deployment packaging and service scripts

**Dependencies**
- all prior phases

**Acceptance tests**
- full suite passes on a clean DB
- startup fails on insecure defaults unless explicit dev override is set
- non-travel agents cannot write `travel_trips`
- unauthenticated websocket closes with code 1008 after ~15s
- dual-process scheduler test still produces a single job fire

---

## Cross-phase dependency summary

- **Foundation first** because auth and DB shape every later concern.
- **Memory before orchestration** because Inez and specialists both depend on memory/document state.
- **LLM routing before LangGraph** because reflexion needs a stable model-selection layer.
- **Execution before scheduler** because scheduled work ultimately submits into the same queue pipeline.
- **Integrations before intelligence** because intelligence endpoints are only useful once external data exists.

## Suggested verification strategy

For every phase, keep the verification stack consistent:
1. schema tests
2. auth tests
3. router contract tests
4. queue/worker integration tests
5. websocket replay tests
6. scheduler single-leader tests

That matches the failure domains of the current server and keeps the rebuild anchored to production-relevant behavior.
