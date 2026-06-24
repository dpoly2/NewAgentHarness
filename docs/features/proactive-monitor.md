# Proactive Monitor

_Generated on 2026-06-24 03:23 UTC._

## Overview

The Proactive Monitor scans the system for deadline risk, urgent todo language, feedback anomalies, and high error counts, then stores notifications for later review.

## Architecture

```
scheduled or manual monitor run
  → check_deadlines()
  → scan global_memory for deadline keywords
  → scan todos for urgent markers
  → check_anomalies()
  → analyze feedback spikes + message error rates
  → store_alerts(...)
  → notifications table / API / UI
```

## Checks currently implemented

- Deadline keyword detection in global memory (`today`, `tomorrow`, `this week`, `next week`, `urgent`, `deadline`).
- Urgent todo title detection.
- Daily feedback spike detection.
- Negative feedback spike detection.
- Basic message error-rate detection based on `error` / `failed` terms in message content.

## How it works

1. A monitor run starts manually or from a background schedule.
2. `check_deadlines(...)` scans memory rows and pending todos.
3. `check_anomalies(...)` computes simple baselines from recent feedback and messages.
4. `store_alerts(...)` persists notification rows for the UI and alert feeds.

## Configuration

- Database path: shared `runs_v3.db`.
- Notification storage can coexist with the base notification schema in `hub_db.py`; note the module also contains a lazy table-creation path with a slightly different shape.
- This feature is intentionally conservative and heuristic-driven in the current implementation.

## API Endpoints Used

| Endpoint | Purpose |
| --- | --- |
| `POST /api/monitoring/run` | Manual trigger |
| `GET /api/notifications` | Read alerts |
| `POST /api/notifications/read` | Mark read |
| `DELETE /api/notifications` | Clear alerts |

## Error Handling

- Missing optional tables can be tolerated with local `OperationalError` handling in specific branches.
- False positives are possible because date extraction is keyword-based rather than full natural-language date parsing.
- The module intentionally stores best-effort alerts instead of blocking any other subsystem.

## Notification dispatch

- Notifications are stored in SQLite and can also be broadcast over WebSocket from the hub server when higher-level flows call the broadcast helpers.
- The iOS alert surfaces consume notifications as part of the Activity hub.

## Related Documentation

- [Briefing API](../api/briefing.md)
- [WebSocket contract](../contracts/websocket-contract.md)
- [iOS watchOS docs](../ios/watchos.md)

## Source References

- `.agents/agentharness/app/v3/proactive_monitor.py`
- `.agents/agentharness/app/v3/routers/config_api.py`
- `.agents/agentharness/app/v3/routers/notifications.py`
- `.agents/agentharness/app/v3/core/hub.py`

## Implementation Checklist

- Confirm `proactive monitor` responses use ISO 8601 UTC timestamps.
- Confirm Bearer JWT is attached on authenticated requests.
- Confirm error payloads use `{"detail": "..."}`.
- Confirm the iOS client can decode optional/null fields safely.
- Confirm background jobs publish notifications or run status events when relevant.
- Confirm SQLite writes update `created_at` / `updated_at` consistently when the table includes them.
- Confirm WebSocket listeners gracefully handle reconnects and unauthorized closes.
- Confirm scheduler or automation side effects are idempotent where retries can occur.
- Confirm prompt, memory, and document payloads are trimmed before persistence when the source code enforces size caps.
- Confirm optional modules fail closed with `503` or `500` rather than silently corrupting state.

## Operational Notes

- `proactive monitor` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
