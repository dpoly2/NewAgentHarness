# 04-RUNTIME-EXECUTION

_Generated from the current ArchonHub source tree on 2026-07-03._

## Queue-driven execution path

### 1. Submission

- `POST /api/runs` accepts `RunRequest` (`agent_id`, `project`, `graph`, `task`, `max_revisions`, `priority`).
- `HubServer.submit_job()` normalizes defaults, writes into `job_queue`, and broadcasts `run_queued` with `run_id`, `agent_id`, `project`, `graph`, and current queue depth.

### 2. Claiming and cancellation

- Each `HubServer` instance runs **5** `_db_worker_loop()` coroutines.
- Workers call `_claim_queued_job()` to atomically take unclaimed work.
- Each claimed run gets a `threading.Event` cancel flag stored in `_active_runs`.
- While the executor future is running, the loop polls `_check_job_cancel_flag(run_id)` every 2 seconds so `/api/runs/{run_id}/cancel` can interrupt long-running work.

### 3. Graph execution

`hub_nodes.run_graph()` is the canonical background execution entrypoint.

- Initializes a run state with `run_id`, `agent_id`, `project`, `graph_type`, `task`, `skill_name`, `skill_version`, `memory_context`, `output`, `score`, `critique`, `revision_count`, and `max_revisions`.
- Emits `run_started` before invoking any graph.
- Selects one of four graphs: `reflexion`, `research`, `wordpress`, `business-law`.
- If LangGraph is unavailable, it returns a mock failed state rather than crashing the worker.

## Reflexion graph contract

The local `hub_nodes.py` reflexion flow matches the higher-level `graphs\reflexion_loop.py` design:

```text
load_memory -> act -> evaluate -> (revise if score < 0.75 and revision_count < max_revisions) -> save_memory
```

### Node responsibilities

- **load_memory:** load skill text + prior memory context.
- **act:** invoke the selected model and produce an initial answer.
- **evaluate:** score output and generate critique.
- **revise:** rewrite the output and optionally version a revised skill in the DB.
- **save_memory:** persist run summary, critique, output preview, and refreshed agent memory.

### Revision policy

`should_revise()` returns `revise` only when:

- `score < 0.75`, and
- `revision_count < max_revisions`.

Otherwise the flow goes directly to `save_memory`.

## Worker resilience loops

`core\hub.py` keeps the server alive with four long-running coordination loops in addition to DB workers:

- **heartbeat loop:** updates `worker_nodes` so other processes can detect liveness.
- **reaper loop:** marks orphaned `running` jobs as failed if a worker disappears.
- **websocket fan-out loop:** uses either SQLite polling (`_event_poll_loop`) or Postgres `LISTEN/NOTIFY` (`_ws_listen_loop`) to push `ws_events` to connected clients.
- **scheduler lease loop:** acquires and renews the single-owner APScheduler lease.

## Persistence side effects

A successful run writes to multiple stores:

- `job_queue`: final status and result payload snapshot
- `runs`: durable run record (`run_id`, agent, graph, score, critique, output, revision count, status)
- `agent_memory`: refreshed memory context for the agent
- `ws_events`: broadcast log used for realtime fan-out and replay
- `run_events`: Inez-specific durable event stream when the run originated from the interactive chat path

## Execution capacities to budget around

Per server process:

- **graph executor:** 3 background run slots
- **Inez executor:** 2 interactive slots
- **DB worker coroutines:** 5 queue claimers

With the default `uvicorn workers=5`, practical concurrency is higher, but all workers coordinate by claiming rows in the shared DB instead of sharing an in-memory queue.

## Source references

- `.agents\agentharness\app\v3\core\hub.py`
- `.agents\agentharness\app\v3\hub_nodes.py`
- `.agents\agentharness\graphs\reflexion_loop.py`
