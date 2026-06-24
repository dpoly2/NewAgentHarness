# Dispatch Contract

_Generated on 2026-06-24 03:23 UTC._

## Overview

A dispatch is the concrete task object Inez creates when she routes work to a specialist during a conversation.

## JSON Schema

```json
{
  "type": "object",
  "required": [
    "id",
    "agent_id",
    "task",
    "project",
    "status",
    "result",
    "created_at"
  ],
  "properties": {
    "id": {
      "type": "string",
      "description": "UUID dispatch id."
    },
    "agent_id": {
      "type": "string",
      "description": "Target agent id."
    },
    "task": {
      "type": "string",
      "description": "Natural-language task description."
    },
    "project": {
      "type": "string",
      "description": "Project slug."
    },
    "status": {
      "type": "string",
      "description": "pending|running|complete|failed"
    },
    "result": {
      "type": "object",
      "description": "Null or structured agent output."
    },
    "created_at": {
      "type": "string",
      "description": "ISO timestamp."
    }
  }
}
```

## Field Descriptions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | string | yes | UUID dispatch id. |
| agent_id | string | yes | Target agent id. |
| task | string | yes | Natural-language task description. |
| project | string | yes | Project slug. |
| status | string | yes | pending|running|complete|failed |
| result | object | yes | Null or structured agent output. |
| created_at | string | yes | ISO timestamp. |

## Validation Rules

- Agent ids should correspond to known portfolio agent ids.
- Status should follow the run lifecycle closely enough for the UI to render progress.
- Result can stay null until completion.

## Example

```json
{
  "id": "uuid",
  "agent_id": "markets-project-lead",
  "task": "Build today's pre-market brief.",
  "project": "markets",
  "status": "pending",
  "result": null,
  "created_at": "2026-06-23T00:00:00Z"
}
```

## Related Documentation

- [Agent output contract](agent-output-contract.md)
- [Inez API](../api/inez.md)

## Source References

- `.agents/agentharness/app/v3/routers/runs.py`
- `.agents/agentharness/app/v3/core/hub.py`
- `.agents/agentharness/app/v3/inez_agent.py`

## Implementation Checklist

- Confirm `Dispatch Contract` responses use ISO 8601 UTC timestamps.
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

- `Dispatch Contract` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
