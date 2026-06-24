# Email Cleanup API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

ArchonHub can analyze an inbox, generate a cleanup plan, collect human approval, execute the approved actions, and keep a history of runs.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Line |
| --- | --- | --- | --- | --- |
| POST | /api/email/cleanup/analyze | analyze_email_cleanup | Public | 4276 |
| GET | /api/email/cleanup/plans | list_cleanup_plans | Public | 4301 |
| GET | /api/email/cleanup/plans/{plan_id} | get_cleanup_plan | Public | 4324 |
| PUT | /api/email/cleanup/plans/{plan_id}/approve | approve_cleanup_items | Public | 4343 |
| POST | /api/email/cleanup/plans/{plan_id}/execute | execute_cleanup_plan | Public | 4375 |
| GET | /api/email/cleanup/history | get_cleanup_history | Public | 4396 |

## Detailed Endpoints

### POST `/api/email/cleanup/analyze`

- **Handler:** `analyze_email_cleanup`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4276`

#### Request Body

| Field | Type | Notes |
| --- | --- | --- |
| user_message | string | Required; source text for memory extraction |
| agent_response | string | Optional response text for better extraction context |

#### Response Schema

- Starts analysis for a connector/account and returns a generated cleanup plan.

#### Example

```bash
curl -X POST http://localhost:8765/api/email/cleanup/analyze \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"user_message": "Remember that YEPC zoning review is next week.", "agent_response": "Stored."}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/email/cleanup/plans`

- **Handler:** `list_cleanup_plans`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4301`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Lists cleanup plans.

#### Example

```bash
curl -X GET http://localhost:8765/api/email/cleanup/plans \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/email/cleanup/plans/{plan_id}`

- **Handler:** `get_cleanup_plan`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4324`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns a single cleanup plan with items.

#### Example

```bash
curl -X GET http://localhost:8765/api/email/cleanup/plans/{plan_id} \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### PUT `/api/email/cleanup/plans/{plan_id}/approve`

- **Handler:** `approve_cleanup_items`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4343`

#### Request Body

| Field | Type | Notes |
| --- | --- | --- |
| user_message | string | Required; source text for memory extraction |
| agent_response | string | Optional response text for better extraction context |

#### Response Schema

- Marks item approvals before execution.

#### Example

```bash
curl -X PUT http://localhost:8765/api/email/cleanup/plans/{plan_id}/approve \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"user_message": "Remember that YEPC zoning review is next week.", "agent_response": "Stored."}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### POST `/api/email/cleanup/plans/{plan_id}/execute`

- **Handler:** `execute_cleanup_plan`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4375`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Executes approved cleanup actions and returns summary counts.

#### Example

```bash
curl -X POST http://localhost:8765/api/email/cleanup/plans/{plan_id}/execute \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/email/cleanup/history`

- **Handler:** `get_cleanup_history`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4396`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns historical cleanup executions and plan outcomes.

#### Example

```bash
curl -X GET http://localhost:8765/api/email/cleanup/history \
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

- [Email cleanup feature](../features/email-cleanup.md)
- [Connectors API](connectors.md)

## Source References

- `.agents/agentharness/app/v3/hub_server.py`
- `.agents/agentharness/app/v3/email_analyzer.py`
- `.agents/agentharness/app/v3/email_executor.py`
- `.agents/agentharness/app/v3/oauth_connector.py`
