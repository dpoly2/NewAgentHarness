# 07-OPERATIONS-RUNBOOK

_Generated from the current ArchonHub source tree on 2026-07-03._

## Start / stop

### Start hub server only
```powershell
python .agents\agentharness\app\v3\hub_server.py
```

### Start the broader local stack
```powershell
.\launch_v3.ps1
```

### Windows service
Expected service name:
```powershell
ArchonHub
```

Install helper referenced by the repo:
```powershell
hub_install_service.ps1
```

Restart command:
```powershell
Restart-Service -Name "ArchonHub" -Force
```

## Runtime endpoints

- Web dashboard: `http://localhost:8765/web`
- API docs: `http://localhost:8765/docs`
- Health check: `http://localhost:8765/api/health`
- WebSocket: `ws://localhost:8765/ws`

Default bind values in `hub_server.py`:
- host: `0.0.0.0`
- port: `8765` (`HUB_PORT` override)
- Uvicorn worker processes: `5`

## Filesystem paths operators care about

- DB: `.agents\agentharness\memory\runs_v3.db`
- PID file: `.agents\data\hub.pid`
- uploads: `.agents\data\uploads\`
- skill files: `.agents\agents\projects\**\*.md`
- web assets: `.agents\agentharness\app\v3\web\`

## Health expectations

`GET /api/health` should surface:
- `status: ok` or `degraded`
- `queue_depth`
- `active_runs`
- `scheduler_jobs`
- `scheduler_ok`
- `worker_ok`
- `thread_pool_size`
- `llm_provider` and `llm_model`

`degraded` means either worker loops or scheduler state are not healthy.

## Logging and observability

Important runtime stores:
- `runs` — final run records
- `job_queue` — queued/running/cancelled state
- `worker_nodes` — worker heartbeat registry
- `ws_events` — websocket fan-out log
- `run_events` — interactive replay log
- `notifications` — user-visible alerts
- `reflexion_log` — scoring and critique history

Common websocket event types emitted by the runtime:
- `run_queued`
- `run_started`
- `run_completed`
- `run_cancelled`
- `node_update`
- `agent_start`
- `agent_thinking`
- `agent_complete`
- `agent_result`
- `inez_thinking`
- `inez_response`
- `notif`

## WebSocket operations

Admission contract:
1. connect to `/ws`
2. send auth frame within 15 seconds:
   - `{ "type": "auth", "token": "<jwt>" }`, or
   - `{ "type": "auth", "api_token": "<token>" }`
3. expect initial `{ type: "connected", queue_depth, active_runs }`
4. client may send `{ type: "ping" }` and receive `{ type: "pong" }`

Failure behavior:
- close code `1008` on timeout, malformed first frame, or failed auth
- disconnected clients are removed from the worker-local `_clients` set
- state remains recoverable from `ws_events` and `run_events`

## Queue and worker operations

Per process, the current server runs:
- 5 async DB workers
- 3-thread graph executor
- 2-thread Inez executor
- heartbeat loop
- stale-job reaper loop
- websocket fan-out loop
- scheduler lease loop

Troubleshooting checklist:
- **queue depth growing**: inspect `job_queue`, worker heartbeat freshness, and service logs
- **runs stuck running**: inspect `worker_nodes.last_heartbeat`, `heartbeat_at`, and reaper timing
- **Inez slow or starved**: verify `_inez_executor` availability and upstream LLM responsiveness
- **websocket quiet**: confirm `ws_events` are still being inserted and poll/listen loop is healthy

## Scheduler operations

The scheduler is single-leader even though multiple Uvicorn worker processes may exist.

Current lease settings:
- TTL: 30 seconds
- renew interval: 10 seconds
- timezone: America/Chicago

Built-in cadence families include:
- log monitor every 15 minutes
- daily briefing / reflexion
- grant + travel sweeps
- markets V1 and V2 morning, hourly, EOD, weekly, monthly jobs
- Capitol Trades 09:00 refresh and 09:30 digest
- nightly DB cleanup and backup
- free-key sync at 07:15

Management endpoints:
- `GET /api/scheduler`
- `POST /api/scheduler`
- `DELETE /api/scheduler/{id}`
- `POST /api/scheduler/{id}/trigger`

## Database and config operations

### Live model change example
The current runtime reads DB-backed config at call time, so changing the configured model does not require restart:

```sql
UPDATE hub_config SET value='gemini-2.5-flash' WHERE key='llm_model';
```

### Code changes
Code changes **do** require service restart because the default run mode is not auto-reload.

### Schema changes
Primary schema owners:
- `core\database.py`
- `hub_db.py`
- focused migration scripts such as `add_fts_search.py`, `add_feedback_system.py`, `add_file_uploads.py`, `add_agent_messaging.py`, and `run_events.py`

## Backup and recovery

Referenced backup helper:
```powershell
hub_backup.py
```

Nightly DB backup also exists as a scheduled job.

Recovery outline:
1. stop the service;
2. restore the latest good `runs_v3.db` copy;
3. restart the server;
4. verify `/api/health`, `/api/scheduler`, and websocket connectivity;
5. re-run targeted migrations if feature-specific tables are missing.

## Integration notes

### Alpaca
- keys must remain in `.env`
- public readiness probe: `GET /api/alpaca/status`
- local sync path: `POST /api/alpaca/sync-positions`

### Open Design daemon
Repository note:
```powershell
Set-Location D:\projects\open-design\deploy
docker compose up -d
```

### Obsidian CLI
`hub_nodes.node_load_memory()` uses the `obsidian search` CLI best-effort. Missing CLI should degrade gracefully, not fail the run.

## Security operations

Startup refuses insecure defaults unless `ARCHONHUB_UNSAFE_DEFAULTS=1` is set explicitly. Operators should always verify:
- `JWT_SECRET` is not the repo default
- `ADMIN_PASSWORD` is not the repo default
- production `CORS_ORIGINS` is locked down
- Alpaca and provider keys live only in `.env` / deployment secrets

## Useful direct SQL checks

```sql
SELECT COUNT(*) FROM job_queue WHERE status='queued';
SELECT run_id, agent_id, status, created_at FROM runs ORDER BY created_at DESC LIMIT 20;
SELECT id, type, created_at FROM ws_events ORDER BY id DESC LIMIT 20;
SELECT id, run_id, type, created_at FROM run_events ORDER BY id DESC LIMIT 50;
SELECT key, value FROM hub_config ORDER BY key;
SELECT id, status, next_fire, last_run_at, last_run_status FROM scheduled_jobs ORDER BY created_at DESC;
```
