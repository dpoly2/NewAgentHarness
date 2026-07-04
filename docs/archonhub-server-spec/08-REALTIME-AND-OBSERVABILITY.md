# 08-REALTIME-AND-OBSERVABILITY

_Generated from the current ArchonHub source tree on 2026-07-03._

## Websocket behavior

After successful auth, the server immediately sends:

```json
{
  "type": "connected",
  "queue_depth": <int>,
  "active_runs": ["run-id", "..."]
}
```

Connected clients can send `{"type":"ping"}` and receive `{"type":"pong"}`. All other business updates are server-emitted.

## Broadcast transport

`core\hub.py` treats `ws_events` as the durable broadcast log.

- **SQLite mode:** `_event_poll_loop()` polls `ws_events` every 200 ms and periodically cleans old rows.
- **Postgres mode:** `_ws_listen_loop()` uses `LISTEN/NOTIFY` with `ws_events` still acting as the durable replay table.
- **Notifications:** `broadcast()` also mirrors `notif` events into the `notifications` table.

## Common event types emitted by the current runtime

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

## Durable replay with `run_events`

Inez-backed interactive runs are additionally appended to `run_events` so reconnecting clients can recover progress that happened while a websocket was offline.

Relevant endpoints in the current router set:

- `GET /api/inez/events/{run_id}`
- `GET /api/inez/conversations/{conversation_id}/events`

This is separate from `ws_events`: `run_events` is conversation/run scoped for replay, while `ws_events` is the general fan-out bus used by all worker processes.

## Operational observability stores

| Store | Purpose |
| --- | --- |
| `runs` | Final run record, score, critique, output preview |
| `job_queue` | Claim state and in-flight job status |
| `worker_nodes` | Heartbeat + worker-capacity registry |
| `ws_events` | Broadcast/replay log for websocket fan-out |
| `run_events` | Conversation/run replay log for Inez |
| `notifications` | User-visible alerts and system toasts |
| `reflexion_log` | Post-run scoring and critique history |

## Failure and recovery notes

- If a websocket client disconnects, it is simply removed from the in-process `_clients` set; the durable tables remain intact.
- If a worker crashes, the reaper loop can mark stale jobs failed and another worker can continue future work.
- Because both websocket fan-out and run replay are DB-backed, state is recoverable across process restarts in a way a purely in-memory queue would not be.

## Source references

- `.agents\agentharness\app\v3\hub_server.py`
- `.agents\agentharness\app\v3\core\hub.py`
- `.agents\agentharness\app\v3\run_events.py`
- `.agents\agentharness\app\v3\routers\inez.py`
