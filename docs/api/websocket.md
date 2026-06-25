# WebSocket API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

The WebSocket surface gives clients near-real-time visibility into queue/runs/notifications. The server fans out events via a shared `ws_events` table so all 5 workers deliver the same event stream to their connected clients. The server requires an initial JSON auth message after connect and enforces a 15-second authentication timeout.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Source File |
| --- | --- | --- | --- | --- |
| WEBSOCKET | /ws | websocket_endpoint | WS auth message | .agents/agentharness/app/v3/hub_server.py |
## Detailed Endpoints

### WEBSOCKET `/ws`

- **Handler:** `websocket_endpoint`
- **Auth required:** Send an initial auth message after connect.
- **Source:** `.agents/agentharness/app/v3/hub_server.py`

#### Request Body

| Field | Type | Notes |
| --- | --- | --- |
| type | string | Must be `auth` |
| token | string | JWT token |
| api_token | string | Optional X-API-Token alternative |

#### Response Schema

- After connect, send `{ "type": "auth", "token": "<jwt>" }` within 15 seconds. On success the server returns `{ "type": "connected", "queue_depth": <int>, "active_runs": [...] }`, where `queue_depth` comes from `SELECT COUNT(*) FROM job_queue WHERE status = 'queued'`, and then emits run / notification events. Connections that do not authenticate in time are closed with code `1008 (Policy Violation)`.

#### Example

```bash
curl -X WEBSOCKET http://localhost:8765/ws \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"type": "auth", "token": "<jwt>"}'
```

```json
{
  "type": "connected",
  "queue_depth": 0,
  "active_runs": []
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

- [WebSocket contract](../contracts/websocket-contract.md)
- [HubClient](../ios/hubclient.md)

## Source References

- `.agents/agentharness/app/v3/hub_server.py`
- `.agents/agentharness/app/v3/core/auth.py`
- `projects/archonhub-ios/ArchonHub/Network/HubClient.swift`

## Implementation Checklist

- Confirm `WebSocket API` responses use ISO 8601 UTC timestamps.
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

- `WebSocket API` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
