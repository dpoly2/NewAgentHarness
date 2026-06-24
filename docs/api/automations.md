# Automations API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

Automations are named workflows with trigger configuration, run history, and attached documents. They are distinct from the lower-level scheduler but may be driven by it.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Line |
| --- | --- | --- | --- | --- |
| GET | /api/automations | list_automations | Bearer JWT | 3173 |
| POST | /api/automations | create_automation | Bearer JWT | 3188 |
| GET | /api/automations/{id} | get_automation | Bearer JWT | 3202 |
| PUT | /api/automations/{id} | update_automation | Bearer JWT | 3210 |
| DELETE | /api/automations/{id} | delete_automation | Bearer JWT | 3220 |
| POST | /api/automations/{id}/trigger | trigger_automation | Bearer JWT | 3227 |
| GET | /api/automations/{id}/runs | list_automation_runs | Bearer JWT | 3244 |
| GET | /api/automations/{id}/documents | list_automation_docs | Bearer JWT | 3250 |
| POST | /api/automations/{id}/documents | create_automation_doc | Bearer JWT | 3256 |

## Detailed Endpoints

### GET `/api/automations`

- **Handler:** `list_automations`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3173`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Lists automation definitions.

#### Example

```bash
curl -X GET http://localhost:8765/api/automations \
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

### POST `/api/automations`

- **Handler:** `create_automation`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3188`

#### Request Body

| Field | Type | Default / Rule |
| --- | --- | --- |
| slug | str | required |
| name | str | required |
| description | str | "" |
| project_slug | str | "" |
| agent_id | str | "" |
| trigger_type | str | "manual" |
| trigger_config | dict | Field(default_factory=dict) |
| steps | List[Any] | Field(default_factory=list) |
| status | str | "active" |

#### Response Schema

- Creates an automation definition.

#### Example

```bash
curl -X POST http://localhost:8765/api/automations \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"slug": "example-slug", "name": "string", "description": "string", "project_slug": "string", "agent_id": "markets-project-lead", "trigger_type": "string", "trigger_config": {}, "steps": [], "status": "string"}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/automations/{id}`

- **Handler:** `get_automation`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3202`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns one automation definition.

#### Example

```bash
curl -X GET http://localhost:8765/api/automations/{id} \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### PUT `/api/automations/{id}`

- **Handler:** `update_automation`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3210`

#### Request Body

| Field | Type | Default / Rule |
| --- | --- | --- |
| name | Optional[str] | None |
| description | Optional[str] | None |
| project_slug | Optional[str] | None |
| agent_id | Optional[str] | None |
| trigger_type | Optional[str] | None |
| trigger_config | Optional[dict] | None |
| steps | Optional[List[Any]] | None |
| status | Optional[str] | None |

#### Response Schema

- Updates definition fields such as trigger config or steps.

#### Example

```bash
curl -X PUT http://localhost:8765/api/automations/{id} \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"name": "string", "description": "string", "project_slug": "string", "agent_id": "markets-project-lead", "trigger_type": "string", "trigger_config": "value", "steps": [], "status": "string"}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### DELETE `/api/automations/{id}`

- **Handler:** `delete_automation`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3220`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Deletes the automation definition.

#### Example

```bash
curl -X DELETE http://localhost:8765/api/automations/{id} \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### POST `/api/automations/{id}/trigger`

- **Handler:** `trigger_automation`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3227`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Enqueues or starts an automation run.

#### Example

```bash
curl -X POST http://localhost:8765/api/automations/{id}/trigger \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/automations/{id}/runs`

- **Handler:** `list_automation_runs`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3244`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Lists historical automation runs.

#### Example

```bash
curl -X GET http://localhost:8765/api/automations/{id}/runs \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/automations/{id}/documents`

- **Handler:** `list_automation_docs`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3250`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Lists automation-produced documents.

#### Example

```bash
curl -X GET http://localhost:8765/api/automations/{id}/documents \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### POST `/api/automations/{id}/documents`

- **Handler:** `create_automation_doc`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:3256`

#### Request Body

| Field | Type | Default / Rule |
| --- | --- | --- |
| automation_id | str | "" |
| run_id | str | "" |
| title | str | "" |
| doc_type | str | "report" |
| content | str | "" |
| status | str | "draft" |
| reviewed_by | str | "" |
| review_notes | str | "" |

#### Response Schema

- Creates/attaches an automation document.

#### Example

```bash
curl -X POST http://localhost:8765/api/automations/{id}/documents \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"automation_id": "string", "run_id": "string", "title": "Example title", "doc_type": "string", "content": "string", "status": "string", "reviewed_by": "string", "review_notes": "string"}'
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

- [Documents API](documents.md)
- [Database schema](../architecture/database-schema.md)

## Source References

- `.agents/agentharness/app/v3/hub_server.py`
- `.agents/agentharness/app/v3/hub_db.py`
