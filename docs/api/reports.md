# Reports API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

Reports give ArchonHub a durable, human-readable output layer on top of runs, schedules, and monitoring. Several built-in jobs trigger report generation as a second step.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Line |
| --- | --- | --- | --- | --- |
| GET | /api/reports | list_reports_endpoint | Bearer JWT | 3515 |
| GET | /api/reports/types/summary | report_types_summary | Bearer JWT | 3531 |
| GET | /api/reports/{report_id} | get_report_endpoint | Bearer JWT | 3541 |
| DELETE | /api/reports/{report_id} | delete_report_endpoint | Bearer JWT (admin) | 3552 |
| POST | /api/reports/run | run_report_endpoint | Bearer JWT (admin) | 3562 |

## Detailed Endpoints

### GET `/api/reports`

- **Handler:** `list_reports_endpoint`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3515`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Lists reports with optional filters for type, project, or job id.

#### Example

```bash
curl -X GET http://localhost:8765/api/reports \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"value": "example"}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/reports/types/summary`

- **Handler:** `report_types_summary`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3531`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns counts per report type for UI headers.

#### Example

```bash
curl -X GET http://localhost:8765/api/reports/types/summary \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/reports/{report_id}`

- **Handler:** `get_report_endpoint`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3541`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns one report row.

#### Example

```bash
curl -X GET http://localhost:8765/api/reports/{report_id} \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### DELETE `/api/reports/{report_id}`

- **Handler:** `delete_report_endpoint`
- **Auth required:** Admin Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3552`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Deletes a report row; admin-only.

#### Example

```bash
curl -X DELETE http://localhost:8765/api/reports/{report_id} \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### POST `/api/reports/run`

- **Handler:** `run_report_endpoint`
- **Auth required:** Admin Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3562`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Queues a manual report job run by `job_id`.

#### Example

```bash
curl -X POST http://localhost:8765/api/reports/run \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"value": "example"}'
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

- [Scheduler API](scheduler.md)
- [Morning briefing feature](../features/morning-briefing.md)

## Source References

- `.agents/agentharness/app/v3/hub_server.py:3511-3577`
- `.agents/agentharness/app/v3/report_monitor.py`
