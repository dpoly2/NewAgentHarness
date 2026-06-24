# Memory Fact Contract

_Generated on 2026-06-24 03:23 UTC._

## Overview

This contract normalizes the persistent facts that power cross-session memory, memory injection, morning briefing context, and proactive reminders.

## JSON Schema

```json
{
  "type": "object",
  "required": [
    "id",
    "category",
    "key",
    "value",
    "source",
    "confidence",
    "importance",
    "usage_count",
    "last_verified",
    "created_at",
    "updated_at"
  ],
  "properties": {
    "id": {
      "type": "string",
      "description": "UUID primary key."
    },
    "category": {
      "type": "string",
      "description": "projects|technical|preferences|people|finance|ministry|rules|deadlines"
    },
    "key": {
      "type": "string",
      "description": "Short snake_case key."
    },
    "value": {
      "type": "string",
      "description": "Detailed fact value."
    },
    "source": {
      "type": "string",
      "description": "manual|conversation|import|agent_learned"
    },
    "confidence": {
      "type": "number",
      "description": "0.0 to 1.0 confidence score."
    },
    "importance": {
      "type": "integer",
      "description": "1 to 10 importance score."
    },
    "usage_count": {
      "type": "integer",
      "description": "How many times the fact has been used or injected."
    },
    "last_verified": {
      "type": "string",
      "description": "ISO 8601 verification timestamp."
    },
    "created_at": {
      "type": "string",
      "description": "Creation timestamp."
    },
    "updated_at": {
      "type": "string",
      "description": "Last update timestamp."
    }
  }
}
```

## Field Descriptions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | string | yes | UUID primary key. |
| category | string | yes | projects|technical|preferences|people|finance|ministry|rules|deadlines |
| key | string | yes | Short snake_case key. |
| value | string | yes | Detailed fact value. |
| source | string | yes | manual|conversation|import|agent_learned |
| confidence | number | yes | 0.0 to 1.0 confidence score. |
| importance | integer | yes | 1 to 10 importance score. |
| usage_count | integer | yes | How many times the fact has been used or injected. |
| last_verified | string | yes | ISO 8601 verification timestamp. |
| created_at | string | yes | Creation timestamp. |
| updated_at | string | yes | Last update timestamp. |

## Validation Rules

- Category should be one of the recognized categories used by `global_memory.py`.
- Key should remain short and stable so repeated upserts can deduplicate cleanly.
- Confidence must be between 0.0 and 1.0.
- Importance must be between 1 and 10.

## Example

```json
{
  "id": "uuid",
  "category": "projects",
  "key": "yepc_zoning_review",
  "value": "YEPC zoning review is next Thursday at 2 PM.",
  "source": "conversation",
  "confidence": 0.92,
  "importance": 9,
  "usage_count": 4,
  "last_verified": "2026-06-23T00:00:00Z",
  "created_at": "2026-06-01T00:00:00Z",
  "updated_at": "2026-06-23T00:00:00Z"
}
```

## Related Documentation

- [Global memory feature](../features/global-memory.md)
- [Memory API](../api/memory.md)

## Source References

- `.agents/agentharness/app/v3/routers/memory.py`
- `.agents/agentharness/app/v3/global_memory.py`

## Implementation Checklist

- Confirm `Memory Fact Contract` responses use ISO 8601 UTC timestamps.
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

- `Memory Fact Contract` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
