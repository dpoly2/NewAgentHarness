# Intelligence Contract

_Generated on 2026-06-24 03:23 UTC._

## Overview

This contract documents the major records used by Progressive Intelligence: agent skill levels and reflexion log entries.

## JSON Schema

```json
{
  "type": "object",
  "properties": {
    "skill_level": {
      "type": "string",
      "description": "novice|intermediate|expert|master"
    },
    "total_runs": {
      "type": "integer",
      "description": "Total recorded runs for an agent."
    },
    "successful_runs": {
      "type": "integer",
      "description": "Successful runs."
    },
    "avg_quality": {
      "type": "number",
      "description": "Average quality score."
    },
    "score": {
      "type": "number",
      "description": "Reflexion score from 0.0 to 1.0."
    },
    "critique": {
      "type": "string",
      "description": "Reflexion critique summary."
    },
    "skill_rewritten": {
      "type": "boolean",
      "description": "Whether the skill file was rewritten."
    }
  }
}
```

## Field Descriptions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| skill_level | string | no | novice|intermediate|expert|master |
| total_runs | integer | no | Total recorded runs for an agent. |
| successful_runs | integer | no | Successful runs. |
| avg_quality | number | no | Average quality score. |
| score | number | no | Reflexion score from 0.0 to 1.0. |
| critique | string | no | Reflexion critique summary. |
| skill_rewritten | boolean | no | Whether the skill file was rewritten. |

## Validation Rules

- Novice: 0-9 runs OR <60% success.
- Intermediate: 10-49 runs AND >=60% success.
- Expert: 50-199 runs AND >=80% success.
- Master: 200+ runs AND >=90% success.
- Reflexion rewrite threshold: 0.75.

## Example

```json
{
  "skill_level": "expert",
  "total_runs": 84,
  "successful_runs": 74,
  "avg_quality": 0.86,
  "score": 0.72,
  "critique": "Strong analysis but missed the requested final recommendation.",
  "skill_rewritten": true
}
```

## Related Documentation

- [Progressive intelligence feature](../features/progressive-intelligence.md)
- [Intelligence API](../api/intelligence.md)

## Source References

- `.agents/agentharness/app/v3/progressive_intelligence.py`
- `.agents/agentharness/app/v3/routers/intelligence.py`

## Implementation Checklist

- Confirm `Intelligence Contract` responses use ISO 8601 UTC timestamps.
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

- `Intelligence Contract` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
