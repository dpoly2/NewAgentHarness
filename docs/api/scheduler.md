# Scheduler API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

Scheduler routes let the UI and administrators inspect persisted schedules, create cron/interval jobs, delete them, and trigger them manually.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Line |
| --- | --- | --- | --- | --- |
| GET | /api/scheduler | list_scheduler | Bearer JWT | 2900 |
| POST | /api/scheduler | create_scheduler_job | Bearer JWT | 2912 |
| DELETE | /api/scheduler/{id} | delete_scheduler_job | Bearer JWT | 2951 |
| POST | /api/scheduler/{id}/trigger | trigger_scheduler_job | Bearer JWT | 2965 |

## Detailed Endpoints

### GET `/api/scheduler`

- **Handler:** `list_scheduler`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:2900`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Lists persisted scheduler rows and/or in-memory job details.

#### Example

```bash
curl -X GET http://localhost:8765/api/scheduler \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### POST `/api/scheduler`

- **Handler:** `create_scheduler_job`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:2912`

#### Request Body

| Field | Type | Default / Rule |
| --- | --- | --- |
| agent_id | str | required |
| project | str | required |
| graph | str | "reflexion" |
| task | str | required |
| run_type | str | "cron" |
| cron_expr | str | "" |
| interval_sec | int | 0 |

#### Response Schema

- Creates a cron or interval job from `SchedulerJobCreate`.

#### Example

```bash
curl -X POST http://localhost:8765/api/scheduler \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"agent_id": "markets-project-lead", "project": "markets", "graph": "string", "task": "Generate a pre-market brief.", "run_type": "string", "cron_expr": "string", "interval_sec": 1}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### DELETE `/api/scheduler/{id}`

- **Handler:** `delete_scheduler_job`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:2951`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Deletes a scheduled job.

#### Example

```bash
curl -X DELETE http://localhost:8765/api/scheduler/{id} \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### POST `/api/scheduler/{id}/trigger`

- **Handler:** `trigger_scheduler_job`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:2965`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Manually triggers a scheduled job immediately.

#### Example

```bash
curl -X POST http://localhost:8765/api/scheduler/{id}/trigger \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

## Error Handling

- `400` indicates validation or bad input.
- `401` indicates a missing or invalid JWT.
- `403` indicates the caller is authenticated but lacks the required role, usually admin-only surfaces.
- `404` indicates the resource identifier does not exist.
- `500` indicates an unhandled subsystem error such as missing optional dependencies, database failures, or third-party API failures.

## Client Notes

- The SwiftUI app consumes many of these routes through `HubClient.swift` and `Models.swift`.
- Treat list responses as dynamic; some endpoints return arrays directly instead of a named `items` wrapper.
- Nullable JSON fields appear in several resources and are intentionally modelled as optional in Swift.

## Related Documentation

- [Morning briefing feature](../features/morning-briefing.md)
- [Proactive monitor](../features/proactive-monitor.md)
- [Deployment/local](../deployment/local.md)

## Source References

- `.agents/agentharness/app/v3/hub_server.py`
- `.agents/agentharness/app/v3/hub_scheduler.py`
