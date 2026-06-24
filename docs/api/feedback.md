# Feedback API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

Feedback routes collect explicit reaction data, store corrections, expose aggregate stats, and surface learned style preferences.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Source File |
| --- | --- | --- | --- | --- |
| POST | /api/messages/{message_id}/feedback | submit_feedback | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
| POST | /api/corrections | submit_correction | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
| GET | /api/feedback/stats | get_feedback_stats | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
| GET | /api/feedback/analyze | analyze_feedback | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
| GET | /api/feedback/preferences | get_user_preferences | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
## Detailed Endpoints

### POST `/api/messages/{message_id}/feedback`

- **Handler:** `submit_feedback`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/feedback.py`

#### Request Body

| Field | Type | Notes |
| --- | --- | --- |
| user_message | string | Required; source text for memory extraction |
| agent_response | string | Optional response text for better extraction context |

#### Response Schema

- Stores positive/negative rating feedback for a message.

#### Example

```bash
curl -X POST http://localhost:8765/api/messages/{message_id}/feedback \
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

### POST `/api/corrections`

- **Handler:** `submit_correction`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/feedback.py`

#### Request Body

| Field | Type | Notes |
| --- | --- | --- |
| user_message | string | Required; source text for memory extraction |
| agent_response | string | Optional response text for better extraction context |

#### Response Schema

- Stores an explicit correction record.

#### Example

```bash
curl -X POST http://localhost:8765/api/corrections \
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

### GET `/api/feedback/stats`

- **Handler:** `get_feedback_stats`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/feedback.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns feedback volume, rating distribution, and similar stats.

#### Example

```bash
curl -X GET http://localhost:8765/api/feedback/stats \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/feedback/analyze`

- **Handler:** `analyze_feedback`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/feedback.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Runs higher-order feedback analysis / learning summary.

#### Example

```bash
curl -X GET http://localhost:8765/api/feedback/analyze \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```

### GET `/api/feedback/preferences`

- **Handler:** `get_user_preferences`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/feedback.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns learned user style preferences.

#### Example

```bash
curl -X GET http://localhost:8765/api/feedback/preferences \
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

- [Feedback learning feature](../features/feedback-learning.md)
- [Database schema](../architecture/database-schema.md)

## Source References

- `.agents/agentharness/app/v3/routers/feedback.py`
