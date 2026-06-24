# Memory API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

The memory surface covers both per-agent key/value memory and the higher-value Global Memory fact store that powers persistent cross-session context.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Line |
| --- | --- | --- | --- | --- |
| GET | /api/memory/agents/{agent_id} | get_memory | Bearer JWT | 2381 |
| PUT | /api/memory/agents/{agent_id} | update_memory | Bearer JWT | 2387 |
| GET | /api/memory/global | list_global_memory | Bearer JWT | 4427 |
| POST | /api/memory/global | create_global_memory_fact | Bearer JWT | 4466 |
| PUT | /api/memory/global/{fact_id} | update_global_memory_fact | Bearer JWT | 4491 |
| DELETE | /api/memory/global/{fact_id} | delete_global_memory_fact | Bearer JWT | 4518 |
| POST | /api/memory/global/extract | extract_memory_from_conversation | Bearer JWT | 4532 |

## Detailed Endpoints

### GET `/api/memory/agents/{agent_id}`

- **Handler:** `get_memory`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:2381`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns per-agent memory key/value pairs from `agent_memory`.

#### Example

```bash
curl -X GET http://localhost:8765/api/memory/agents/{agent_id} \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### PUT `/api/memory/agents/{agent_id}`

- **Handler:** `update_memory`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:2387`

#### Request Body

| Field | Type | Default / Rule |
| --- | --- | --- |
| data | dict | required |

#### Response Schema

- Replaces or updates agent memory using a generic `data` dict.

#### Example

```bash
curl -X PUT http://localhost:8765/api/memory/agents/{agent_id} \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"data": {}}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/memory/global`

- **Handler:** `list_global_memory`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4427`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Lists global facts with optional filters such as category/limit/offset.

#### Example

```bash
curl -X GET http://localhost:8765/api/memory/global \
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

### POST `/api/memory/global`

- **Handler:** `create_global_memory_fact`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4466`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Upserts a global memory fact and returns `{ success: true, fact }`.

#### Example

```bash
curl -X POST http://localhost:8765/api/memory/global \
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

### PUT `/api/memory/global/{fact_id}`

- **Handler:** `update_global_memory_fact`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4491`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Updates a specific fact id while preserving the shared schema.

#### Example

```bash
curl -X PUT http://localhost:8765/api/memory/global/{fact_id} \
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

### DELETE `/api/memory/global/{fact_id}`

- **Handler:** `delete_global_memory_fact`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4518`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Deletes a specific global memory fact.

#### Example

```bash
curl -X DELETE http://localhost:8765/api/memory/global/{fact_id} \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### POST `/api/memory/global/extract`

- **Handler:** `extract_memory_from_conversation`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4532`

#### Request Body

| Field | Type | Notes |
| --- | --- | --- |
| user_message | string | Required; source text for memory extraction |
| agent_response | string | Optional response text for better extraction context |

#### Response Schema

- Runs `extract_and_store(...)` against a user/agent turn pair.

#### Example

```bash
curl -X POST http://localhost:8765/api/memory/global/extract \
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

- [Global memory feature](../features/global-memory.md)
- [Memory fact contract](../contracts/memory-fact-contract.md)
- [Inez API](inez.md)

## Source References

- `.agents/agentharness/app/v3/hub_server.py:4428-4550`
- `.agents/agentharness/app/v3/global_memory.py`
- `.agents/agentharness/app/v3/add_global_memory.py`
