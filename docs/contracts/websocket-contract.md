# WebSocket Contract

_Generated on 2026-06-24 03:23 UTC._

## Overview

The WebSocket contract documents both the initial auth handshake and the event payload families used by the server and clients.

## JSON Schema

```json
{
  "type": "object",
  "properties": {
    "type": {
      "type": "string",
      "description": "Event type."
    },
    "run_id": {
      "type": "string",
      "description": "Associated run id if applicable."
    },
    "agent_id": {
      "type": "string",
      "description": "Associated agent id if applicable."
    },
    "token": {
      "type": "string",
      "description": "JWT used only in the initial auth message."
    },
    "message": {
      "type": "string",
      "description": "Human-readable message."
    },
    "summary": {
      "type": "string",
      "description": "One-line summary for completion events."
    },
    "db_writes": {
      "type": "array",
      "description": "Database write summaries."
    },
    "todos": {
      "type": "array",
      "description": "Todo suggestions or created todos."
    }
  }
}
```

## Field Descriptions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| type | string | no | Event type. |
| run_id | string | no | Associated run id if applicable. |
| agent_id | string | no | Associated agent id if applicable. |
| token | string | no | JWT used only in the initial auth message. |
| message | string | no | Human-readable message. |
| summary | string | no | One-line summary for completion events. |
| db_writes | array | no | Database write summaries. |
| todos | array | no | Todo suggestions or created todos. |

## Validation Rules

- Target URL in local mode is `ws://localhost:8765/ws`.
- Current server implementation expects an initial JSON auth message after connect.
- After connecting, the client must send `{"type":"auth","token":"<jwt>"}` within **15 seconds** or the server closes the connection with WebSocket close code `1008 (Policy Violation)`.
- Common events include connected, run updates, notifications, and ping/pong heartbeats.
- Broadcast delivery is DB-mediated: `broadcast()` writes to `ws_events`, and each worker polls that table every 200ms before forwarding events to its connected clients.
- `connected.queue_depth` is a DB count from `SELECT COUNT(*) FROM job_queue WHERE status = 'queued'`, not an in-process queue size.

## Example

```json
{
  "connect": {
    "type": "auth",
    "token": "<jwt>"
  },
  "event_types": [
    "agent_start",
    "agent_thinking",
    "agent_complete",
    "inez_thinking",
    "inez_response",
    "run_update",
    "notification"
  ]
}
```

## Related Documentation

- [WebSocket API](../api/websocket.md)
- [HubClient](../ios/hubclient.md)

## Source References

- `.agents/agentharness/app/v3/hub_server.py`
- `.agents/agentharness/app/v3/core/auth.py`

## Implementation Checklist

- Confirm `WebSocket Contract` responses use ISO 8601 UTC timestamps.
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

- `WebSocket Contract` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
