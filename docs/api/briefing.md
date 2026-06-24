# Briefing API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

The briefing surface covers quick operational summaries, the dedicated morning brief generator, and stored briefing history.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Line |
| --- | --- | --- | --- | --- |
| GET | /api/briefing | get_briefing | Bearer JWT | 2999 |
| GET | /api/briefing/morning | get_morning_briefing | Public | 4053 |
| GET | /api/briefing/history | get_briefing_history | Public | 4098 |
| GET | /api/briefs | list_briefs | Bearer JWT | 2844 |
| POST | /api/briefs | create_brief | Bearer JWT | 2853 |
| DELETE | /api/briefs | unknown | Bearer JWT | 0 |

## Detailed Endpoints

### GET `/api/briefing`

- **Handler:** `get_briefing`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:2999`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns the current general briefing surface.

#### Example

```bash
curl -X GET http://localhost:8765/api/briefing \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/briefing/morning`

- **Handler:** `get_morning_briefing`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4053`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Generates or retrieves the personalized morning brief.

#### Example

```bash
curl -X GET http://localhost:8765/api/briefing/morning \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/briefing/history`

- **Handler:** `get_briefing_history`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4098`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns prior morning briefs or briefing history rows.

#### Example

```bash
curl -X GET http://localhost:8765/api/briefing/history \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/briefs`

- **Handler:** `list_briefs`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:2844`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Legacy/list surface for brief rows.

#### Example

```bash
curl -X GET http://localhost:8765/api/briefs \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### POST `/api/briefs`

- **Handler:** `create_brief`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:2853`

#### Request Body

| Field | Type | Notes |
| --- | --- | --- |
| user_message | string | Required; source text for memory extraction |
| agent_response | string | Optional response text for better extraction context |

#### Response Schema

- Creates a brief row via generic payload.

#### Example

```bash
curl -X POST http://localhost:8765/api/briefs \
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

### DELETE `/api/briefs`

- **Handler:** `unknown`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:0`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Clears or deletes stored briefs depending on parameters.

#### Example

```bash
curl -X DELETE http://localhost:8765/api/briefs \
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
- [Scheduler API](scheduler.md)

## Source References

- `.agents/agentharness/app/v3/hub_server.py`
- `.agents/agentharness/app/v3/morning_brief.py`
- `.agents/agentharness/app/v3/hub_scheduler.py`
