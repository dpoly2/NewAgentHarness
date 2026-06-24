# Todos API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

Todos are one of the most reused entities in the system: the dashboard, workspace, Inez, morning briefs, and some automations all depend on them.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Source File |
| --- | --- | --- | --- | --- |
| GET | /api/todos | get_todos | Bearer JWT | .agents/agentharness/app/v3/routers/todos.py |
| POST | /api/todos | create_todo | Bearer JWT | .agents/agentharness/app/v3/routers/todos.py |
| GET | /api/todos/{id} | get_todo | Bearer JWT | .agents/agentharness/app/v3/routers/todos.py |
| PUT | /api/todos/{id} | update_todo | Bearer JWT | .agents/agentharness/app/v3/routers/todos.py |
| DELETE | /api/todos/{id} | delete_todo | Bearer JWT | .agents/agentharness/app/v3/routers/todos.py |
## Detailed Endpoints

### GET `/api/todos`

- **Handler:** `get_todos`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/todos.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Lists todo rows; consumers should tolerate nullable description/project/tags values.

#### Example

```bash
curl -X GET http://localhost:8765/api/todos \
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

### POST `/api/todos`

- **Handler:** `create_todo`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/todos.py`

#### Request Body

| Field | Type | Default / Rule |
| --- | --- | --- |
| title | str | required |
| description | str | "" |
| priority | str | "medium" |
| status | str | "pending" |
| project | str | "" |
| due_date | str | "" |
| tags | List[Any] | Field(default_factory=list) |
| source | str | "user" |

#### Response Schema

- Creates a todo row.

#### Example

```bash
curl -X POST http://localhost:8765/api/todos \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"title": "Example title", "description": "string", "priority": "string", "status": "string", "project": "markets", "due_date": "string", "tags": [], "source": "string"}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/todos/{id}`

- **Handler:** `get_todo`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/todos.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns one todo by id.

#### Example

```bash
curl -X GET http://localhost:8765/api/todos/{id} \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### PUT `/api/todos/{id}`

- **Handler:** `update_todo`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/todos.py`

#### Request Body

| Field | Type | Default / Rule |
| --- | --- | --- |
| title | Optional[str] | None |
| description | Optional[str] | None |
| priority | Optional[str] | None |
| status | Optional[str] | None |
| project | Optional[str] | None |
| due_date | Optional[str] | None |
| tags | Optional[List[Any]] | None |

#### Response Schema

- Updates title, description, status, project, tags, or due date.

#### Example

```bash
curl -X PUT http://localhost:8765/api/todos/{id} \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"title": "Example title", "description": "string", "priority": "string", "status": "string", "project": "markets", "due_date": "string", "tags": []}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### DELETE `/api/todos/{id}`

- **Handler:** `delete_todo`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/todos.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Deletes the todo row.

#### Example

```bash
curl -X DELETE http://localhost:8765/api/todos/{id} \
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

- [Briefing API](briefing.md)
- [iOS views](../ios/views.md)

## Source References

- `.agents/agentharness/app/v3/routers/todos.py`
