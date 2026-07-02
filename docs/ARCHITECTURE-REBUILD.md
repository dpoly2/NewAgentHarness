# ArchonHub — Architecture Review & Rebuild Proposal

> Status: proposal / RFC · Author: engineering · Date: 2026-06-30
> Grounded in concrete failure modes observed in production, not a speculative rewrite.

---

## 1. Current state (measured)

| Metric | Value |
|---|---|
| Python modules (`app/v3`) | 108 |
| Python LOC (`app/v3`) | ~38,200 |
| Frontend | single `index.html`, **5,569 lines** |
| Database | one SQLite file `runs_v3.db`, **60 tables**, ~13 MB |
| Agent skill files | 148 `.md` files |
| Runtime | 1 nssm Windows service, 5 uvicorn workers |
| Largest modules | `hub_db.py` (3,293), `main_m365.py` (2,707), `inez_agent.py` (1,758), `core/database.py` (1,547), `hub_scheduler.py` (1,099), `org_chart.py` (1,026) |

### What it is
A FastAPI **monolith** where a single process serves HTTP + WebSockets, runs a
DB-polling **job queue**, hosts an **APScheduler**, *and* embeds **Tkinter desktop
GUIs** (`org_chart.py`, `main_m365.py`). Cross-cutting concerns are duplicated:

- **3 LLM entry points** — `hub_nodes._llm`, `llm_router.get_llm_for_agent`, `inez_agent._llm`
- **2 data layers** — `hub_db.py` and `core/database.py` (two `get_config`, `_HubDbFallback`, etc.)
- **2 execution paths** — `hub_nodes.run_graph` (reflexion via job_queue) and `agent_runner.run_agent` (JSON db_writes contract)

---

## 2. Observed failure modes

Every item below was hit and diagnosed in production, not hypothesized.

| # | Symptom | Root cause |
|---|---|---|
| 1 | Agents emit `"LangGraph not installed - mock output"` | A model **timeout mislabeled** as a missing dependency — error handling that lies |
| 2 | 25 agent `.md` files gutted to stubs | Reflexion loop **overwrites human-authored source** every run (via `write_agent_skill_file` *and* `progressive_intelligence.post_run_hook`) |
| 3 | Inez chat "completes in background but not on screen" | Long turn on a **blocking HTTP request**; the final answer is returned via HTTP only, **never emitted over WS**. A proxy 524 loses it. |
| 4 | 3 jobs stuck `running` for **5+ days** | DB job queue with **no heartbeat / reaper** for orphaned runs |
| 5 | Duplicate log-monitor sweeps | Scheduler runs in **all 5 workers** — no leader lock |
| 6 | `database is locked` | Many concurrent writers on **one SQLite file** |
| 7 | Every agent 401 → timeout | **One dead free-key** poisoned all routing; no circuit-breaker; 3 divergent fallback policies |
| 8 | Everything slow | Sync `.invoke()` in thread-pool executors on **CPU-bound local models**; skills `rglob`'d from disk on every call |

**Through-line:** one process doing too many jobs, three copies of every
cross-cutting concern, and no separation between durable state and in-flight work.

---

## 3. Target architecture

Four clean seams, introduced via **strangler-fig** (no flag day). Principle:
*fewer moving parts each doing one thing well; long-running agent work is
first-class, not bolted onto request/response.*

### Seam 1 — LLM Gateway  *(fixes #1, #7; removes 3-path divergence)*
One module all callers go through.
- **Task-based tiering** — cheap/fast model for classify/evaluate, capable for
  reasoning/synthesis, local only as explicit fallback. Today it's backwards
  (local-first), which is why everything is slow.
- **Circuit breaker + provider health** — a provider that 401s/times out opens
  automatically for a cooldown. (A partial version was bolted on as
  `note_free_call_failure`; it belongs in the gateway core.)
- **Async + streaming** — `async` clients, token streaming to the UI; removes the
  thread-pool-executor-blocks-worker pattern.
- **Single retry/fallback policy** instead of three subtly different ones.

### Seam 2 — Event-sourced runs over a broker  *(fixes #3, #4, #5)*
- `POST /inez/chat` returns a `run_id` **immediately**; **all** output (progress
  *and* final message) streams over WS/SSE. The transcript is source of truth, so
  reconnect recovers the answer.
- Replace DB-polling queue (`_claim_queued_job` + `sleep(0.5)`) with a real broker
  (Redis/RQ, NATS, or Celery) → **heartbeats + visibility timeouts** → orphaned
  jobs auto-requeue instead of rotting.
- **One scheduler owner** (dedicated process or advisory lock) → no duplicate sweeps.

### Seam 3 — Postgres + one DAL  *(fixes #6; kills 2-DB split)*
- Move to **Postgres** (WAL, real concurrency, `LISTEN/NOTIFY` for events). Keep
  SQLite as the dev target behind one DAL.
- Collapse `hub_db.py` + `core/database.py` into **one typed repository layer**.

### Seam 4 — Skills & config as versioned data  *(fixes #2)*
- Agent definitions become **immutable, versioned records**. The reflexion loop
  may only propose a *new version*; overwriting source is structurally impossible.
- Config/secrets in a typed settings store, not JSON-in-a-cell (today's `api_token`
  decodes to binary).

### Structural cleanups
- **Extract the Tkinter GUIs** (`org_chart.py`, `main_m365.py`, ~3.7k LOC) out of the server package.
- **Componentize `index.html`** into ES modules + a WS store. It's currently
  unmodifiable without risk (the devops dashboard was shipped as a *separate* page
  to avoid touching it).

---

## 4. Migration path
1. **LLM Gateway** — highest pain / lowest risk, purely internal.
2. **Event stream to WS/SSE for Inez** — fixes the visible stuck-UI bug.
3. **Swap job queue** to a broker behind the existing `submit_job` signature.
4. **Postgres** behind the unified DAL.
5. Frontend + skills-as-data last.

Each step ships and reverts independently.

## 5. If you only do three things
1. **Unify LLM access behind one gateway with a circuit breaker.**
2. **Stream the final Inez result over WS; return HTTP immediately.**
3. **Add a job reaper + single-owner scheduler.**

Days of work, not a rewrite — eliminates ~80% of the failure modes above.

---

## 6. Deep dive — LLM Gateway

### Problem in detail
Three entry points, each with its own tiering, fallback, timeout, and key logic:
- `hub_nodes._llm(weight=...)` — free-key round-robin → Ollama; 80s timeout, `max_tokens`.
- `llm_router.get_llm_for_agent` — per-agent override → model_catalog → free-key → Ollama → global.
- `inez_agent._llm` — now OpenAI-preferred → hub factory → bare OpenAI.

Because they diverge, a fix in one (e.g. the 401 self-heal) doesn't protect the
others, and behavior depends on which path a call happens to take.

### Design
```
             ┌──────────────────────── LLMGateway ────────────────────────┐
 caller ───▶ │  complete(task_type, messages, *, json=False, stream=False) │ ──▶ provider
             │                                                             │
             │  1. policy = ROUTING[task_type]      # tier + fallbacks     │
             │  2. for provider in policy.chain:                          │
             │       if breaker.open(provider): continue                  │
             │       try: return await provider.acomplete(...)            │
             │       except AuthError:  breaker.trip(provider, 6h)        │
             │       except Timeout:    breaker.trip(provider, 2m)        │
             │  3. raise AllProvidersDown                                 │
             └────────────────────────────────────────────────────────────┘
```

- **`task_type`** (`classify | evaluate | reason | synthesize | draft`) selects a
  **policy**: model tier, temperature default, token cap, and an ordered
  **fallback chain** (e.g. `reason → [openai:gpt-4o-mini, local:mistral, local:llama3.2:1b]`).
- **Circuit breaker** per provider: `AuthError`→ long trip (dead key), `Timeout`/`5xx`→ short trip. Half-open probe on expiry. State shared across workers (Redis/DB), not per-process.
- **Async + streaming**: `acomplete()` and `astream()`; callers `await`. No executor threads held for the duration of a call.
- **JSON mode** centralized: `json=True` binds `response_format` for OpenAI-compatible providers (incl. Ollama) — one place, not per-caller.
- **Observability**: every call emits `{task_type, provider, model, latency, tokens, outcome}`. Misleading strings like "LangGraph not installed" become impossible.

### Interface (illustrative)
```python
class LLMGateway:
    async def complete(self, task_type: str, messages: list[Msg], *,
                       json: bool = False, temperature: float | None = None,
                       max_tokens: int | None = None) -> LLMResult: ...
    async def stream(self, task_type: str, messages: list[Msg], **kw) -> AsyncIterator[str]: ...
```
Every existing caller becomes a one-line delegation; the three current factories
are deleted.

### Payoff
No dead key or slow model can take down all agents; behavior is deterministic per
task type; freed worker threads; honest errors.

---

## 7. Deep dive — Event-sourced runs & streaming

### Problem in detail
`POST /inez/chat` blocks in a thread executor running `think()` (reasoning +
dispatch + synthesis), emits *progress* over WS, then returns the **final answer
in the HTTP response body**. If the turn exceeds the reverse-proxy limit (~100s →
Cloudflare 524), the browser's request dies while the backend completes and saves
the message — so the UI is stuck on the last progress step (`"Synthesizing…"`)
even though the answer exists in the DB. Progress and result travel on **two
different channels**, only one of which is durable.

### Design — one durable channel
Treat a chat turn as a **run** with an append-only **event log**; the socket is
just a live tail of that log.

```
POST /inez/chat ──▶ create run(id) ──▶ enqueue ──▶ 202 {run_id}   (returns instantly)

worker: for each step → append_event(run_id, {type, data}) ──┐
                                                              ├─▶ events table / stream
client: WS/SSE subscribe(run_id) ◀── replay(from_seq) ◀──────┘
        GET /runs/{id}/events?from=seq   (reconnect / catch-up)
```

- **HTTP returns `202 {run_id}` immediately** — no long-lived request, no 524.
- **Every step is an event**: `run_started`, `thinking`, `dispatch_started`,
  `token` (for streaming), `dispatch_result`, `final_message`, `run_completed`.
  The **final message is an event**, not an HTTP body.
- **Durable + replayable**: events persisted with a per-run sequence number. On
  reconnect the client asks `from=last_seq` and catches up — a dropped socket or a
  refreshed tab never loses the answer.
- **Idempotent + resumable**: because the run and its events are durable, a worker
  crash mid-turn resumes/retries from the last event instead of vanishing.
- **Streaming for free**: `token` events let the UI render Inez's reply as it's
  generated instead of waiting for the whole turn.

### Frontend change
The WS store already handles `inez_thinking`; it gains one handler for
`final_message` (render + persist) and optionally `token` (incremental). The
HTTP call becomes fire-and-forget returning `run_id`; rendering is entirely
event-driven. This also removes the "final answer only via HTTP" coupling that
caused the bug.

### Payoff
Chats can't "finish in the background but not on screen"; reconnect/refresh
recovers; long multi-agent turns are fine; tokens stream live.

---

## 8. Implementation notes (ArchonHub-specific touchpoints)

### 8.1 LLM Gateway
Collapses three factories — `hub_nodes._llm(weight)`, `llm_router.get_llm_for_agent`,
`inez_agent._llm` — into one `gateway.complete(task_type, messages, json=…)`. Each old
function becomes a 3-line shim (keeps callers working), then is deleted.

Routing is a **declarative table**, not branches:
```python
ROUTING = {
  "classify":   Tier(chain=["local:llama3.2:1b"],                         max_tokens=64,   temp=0),
  "evaluate":   Tier(chain=["openai:gpt-4o-mini","local:mistral"], json=True, max_tokens=256),
  "reason":     Tier(chain=["openai:gpt-4o-mini","local:mistral","local:llama3.2:1b"], max_tokens=1536),
  "synthesize": Tier(chain=["openai:gpt-4o-mini","local:mistral"],        max_tokens=1024),
}
```
The ad-hoc fixes made under fire (devops→gpt-4o-mini override, Inez→gpt-4o-mini,
1b fast-fallback) become rows here instead of scattered DB config + `agent_registry.config`.

**Circuit-breaker state must be shared across the 5 workers** (in `hub_config` today,
Redis in target) — a per-process breaker means one worker keeps hitting a key another
already knows is dead. `free_llm_keys.note_free_call_failure` is the seed of this.

Sequence (all internal, zero API change): add `gateway.py` wrapping current `build_llm`
→ repoint `inez_agent._llm` and `agent_runner` → repoint `hub_nodes._llm` → move breaker
state to shared store → delete the old factories.

### 8.2 Event-sourced Inez turns
Bug origin: `routers/inez.py` awaits `think()` inline and returns the final answer only in
the HTTP body; a proxy 524 loses it.

1. **Table** `run_events(run_id, seq, type, data, created_at)` — append-only.
2. **`_inez_emit` persists** each event (with a per-run `seq`) in addition to `hub.broadcast`.
   The final message becomes an event (`type="inez_final"`), not just an HTTP body.
3. **Non-breaking rollout:** keep the HTTP response returning `inez_message` (existing
   frontend still works on fast turns); the WS `inez_final` event + replay cover the
   lost-response case. Later, flip the endpoint to return `202 {run_id}` once the
   frontend is fully event-driven.
4. **Replay** `GET /inez/runs/{run_id}/events?from=seq` — a refreshed tab / dropped
   socket catches up. This is the actual fix for "completed in background, not on screen."
5. **Frontend:** the WS store (~`index.html:1392`) already handles `inez_thinking`; add an
   `inez_final` handler and, on socket open, replay from the last seen `seq`. ~30 lines.

Smallest bug-fixing slice = steps 1–2 + 4 (durable, replayable final message) — no broker
or Postgres required yet.

