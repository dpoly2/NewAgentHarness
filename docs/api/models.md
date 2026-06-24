# Models and Providers API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

This group exposes the model catalog, per-model enable/disable flags, task-based routing, and free-key provider utilities.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Source File |
| --- | --- | --- | --- | --- |
| GET | /api/models | list_models | Bearer JWT | .agents/agentharness/app/v3/routers/models_api.py |
| PUT | /api/models/toggle | toggle_model | Admin JWT | .agents/agentharness/app/v3/routers/models_api.py |
| POST | /api/models/route | route_model | Bearer JWT | .agents/agentharness/app/v3/routers/models_api.py |
| GET | /api/models/providers | list_providers | Bearer JWT | .agents/agentharness/app/v3/routers/models_api.py |
| POST | /api/providers/sync-free-keys | sync_free_llm_keys_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/providers.py |
| GET | /api/providers/free-keys-status | free_keys_status | Bearer JWT | .agents/agentharness/app/v3/routers/providers.py |
## Detailed Endpoints

### GET `/api/models`

- **Handler:** `list_models`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/models_api.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns the full provider/model catalog with enabled flags and API-key visibility.

#### Example

```bash
curl -X GET http://localhost:8765/api/models \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### PUT `/api/models/toggle`

- **Handler:** `toggle_model`
- **Auth required:** Admin JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/models_api.py`

#### Request Body

| Field | Type | Default / Rule |
| --- | --- | --- |
| provider | str | required |
| model_id | str | required |
| enabled | bool | required |

#### Response Schema

- Enables or disables a single provider/model combination.

#### Example

```bash
curl -X PUT http://localhost:8765/api/models/toggle \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"provider": "string", "model_id": "string", "enabled": true}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### POST `/api/models/route`

- **Handler:** `route_model`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/models_api.py`

#### Request Body

| Field | Type | Default / Rule |
| --- | --- | --- |
| task_type | str | required |
| agent_id | str | "" |

#### Response Schema

- Resolves a best model for a task type and optional agent id.

#### Example

```bash
curl -X POST http://localhost:8765/api/models/route \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"task_type": "string", "agent_id": "markets-project-lead"}'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/models/providers`

- **Handler:** `list_providers`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/models_api.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns provider-level rollups such as total models and enabled counts.

#### Example

```bash
curl -X GET http://localhost:8765/api/models/providers \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### POST `/api/providers/sync-free-keys`

- **Handler:** `sync_free_llm_keys_endpoint`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/providers.py`

#### Request Body

| Field | Type | Notes |
| --- | --- | --- |
| user_message | string | Required; source text for memory extraction |
| agent_response | string | Optional response text for better extraction context |

#### Response Schema

- Pulls public free-key registry data and activates discovered providers.

#### Example

```bash
curl -X POST http://localhost:8765/api/providers/sync-free-keys \
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

### GET `/api/providers/free-keys-status`

- **Handler:** `free_keys_status`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/providers.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns last sync time and active free-key providers.

#### Example

```bash
curl -X GET http://localhost:8765/api/providers/free-keys-status \
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

- [LLM routing feature reference](../features/progressive-intelligence.md)
- [Environment variables](../deployment/environment.md)

## Source References

- `.agents/agentharness/app/v3/routers/models_api.py`
- `.agents/agentharness/app/v3/routers/providers.py`
