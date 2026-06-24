# Inez API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

Inez is the executive agent surface for the system. These routes handle conversation turns, short briefings, operational status, and in-memory fact views for the executive layer.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Source File |
| --- | --- | --- | --- | --- |
| POST | /api/inez/chat | inez_chat | Bearer JWT | .agents/agentharness/app/v3/routers/inez.py |
| GET | /api/inez/brief | inez_morning_brief | Bearer JWT | .agents/agentharness/app/v3/routers/inez.py |
| GET | /api/inez/status | inez_status | Bearer JWT | .agents/agentharness/app/v3/routers/inez.py |
| GET | /api/inez/memory | inez_memory | Bearer JWT | .agents/agentharness/app/v3/routers/inez.py |
| DELETE | /api/inez/memory/facts/{key} | delete_inez_fact | Bearer JWT | .agents/agentharness/app/v3/routers/inez.py |
## Detailed Endpoints

### POST `/api/inez/chat`

- **Handler:** `inez_chat`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/inez.py`

#### Request Body

| Field | Type | Default / Rule |
| --- | --- | --- |
| message | str | required |
| conversation_id | Optional[str] | None |

#### Response Schema

- Returns an Inez message, dispatch suggestions, queued runs, and follow-up hints.

#### Example

```bash
curl -X POST http://localhost:8765/api/inez/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"message": "Give me the morning briefing.", "conversation_id": "string"}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/inez/brief`

- **Handler:** `inez_morning_brief`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/inez.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns the short executive brief synthesized from the current system state.

#### Example

```bash
curl -X GET http://localhost:8765/api/inez/brief \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/inez/status`

- **Handler:** `inez_status`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/inez.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns awareness text, urgent count, and active missions.

#### Example

```bash
curl -X GET http://localhost:8765/api/inez/status \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/inez/memory`

- **Handler:** `inez_memory`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/inez.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns Inez-relevant memory facts or memory summary.

#### Example

```bash
curl -X GET http://localhost:8765/api/inez/memory \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### DELETE `/api/inez/memory/facts/{key}`

- **Handler:** `delete_inez_fact`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/inez.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Deletes a keyed Inez memory fact by logical key.

#### Example

```bash
curl -X DELETE http://localhost:8765/api/inez/memory/facts/{key} \
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

- [Inez agent](../agents/inez.md)
- [Global memory feature](../features/global-memory.md)
- [Progressive intelligence](../features/progressive-intelligence.md)

## Source References

- `.agents/agentharness/app/v3/routers/inez.py`
