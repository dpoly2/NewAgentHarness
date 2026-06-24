# Progressive Intelligence API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

These endpoints expose the four-layer self-improvement system: reflexion, auto-memory, skill progression, and pattern detection.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Source File |
| --- | --- | --- | --- | --- |
| GET | /api/intelligence/summary | intelligence_summary | Bearer JWT | .agents/agentharness/app/v3/routers/intelligence.py |
| GET | /api/intelligence/skills | intelligence_skills | Bearer JWT | .agents/agentharness/app/v3/routers/intelligence.py |
| GET | /api/intelligence/patterns | intelligence_patterns | Bearer JWT | .agents/agentharness/app/v3/routers/intelligence.py |
| GET | /api/intelligence/agent/{agent_id} | intelligence_agent | Bearer JWT | .agents/agentharness/app/v3/routers/intelligence.py |
## Detailed Endpoints

### GET `/api/intelligence/summary`

- **Handler:** `intelligence_summary`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/intelligence.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns the broad system summary, usually including skill rows, reflexion history, and pattern suggestions.

#### Example

```bash
curl -X GET http://localhost:8765/api/intelligence/summary \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "agent_skill_levels": [],
  "reflexion_log": [],
  "patterns": []
}
```

### GET `/api/intelligence/skills`

- **Handler:** `intelligence_skills`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/intelligence.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns just the `agent_skill_levels` view.

#### Example

```bash
curl -X GET http://localhost:8765/api/intelligence/skills \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "agent_skill_levels": [],
  "reflexion_log": [],
  "patterns": []
}
```

### GET `/api/intelligence/patterns`

- **Handler:** `intelligence_patterns`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/intelligence.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns detected patterns and proactive suggestions.

#### Example

```bash
curl -X GET http://localhost:8765/api/intelligence/patterns \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "agent_skill_levels": [],
  "reflexion_log": [],
  "patterns": []
}
```

### GET `/api/intelligence/agent/{agent_id}`

- **Handler:** `intelligence_agent`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/intelligence.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns a single agent intelligence profile with run stats, skill badge, and recent reflexion info.

#### Example

```bash
curl -X GET http://localhost:8765/api/intelligence/agent/{agent_id} \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "agent_skill_levels": [],
  "reflexion_log": [],
  "patterns": []
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

- [Progressive intelligence feature](../features/progressive-intelligence.md)
- [Intelligence contract](../contracts/intelligence-contract.md)

## Source References

- `.agents/agentharness/app/v3/routers/intelligence.py`
- `.agents/agentharness/app/v3/progressive_intelligence.py`

## Implementation Checklist

- Confirm `Progressive Intelligence API` responses use ISO 8601 UTC timestamps.
- Confirm Bearer JWT is attached on authenticated requests.
- Confirm error payloads use `{"detail": "..."}`.
- Confirm the iOS client can decode optional/null fields safely.
- Confirm background jobs publish notifications or run status events when relevant.
- Confirm SQLite writes update `created_at` / `updated_at` consistently when the table includes them.
- Confirm WebSocket listeners gracefully handle reconnects and unauthorized closes.
- Confirm scheduler or automation side effects are idempotent where retries can occur.
- Confirm prompt, memory, and document payloads are trimmed before persistence when the source code enforces size caps.
- Confirm optional modules fail closed with `503` or `500` rather than silently corrupting state.

## Operational Notes

- `Progressive Intelligence API` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

