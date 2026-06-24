# Agent Output Contract

_Generated on 2026-06-24 03:23 UTC._

## Overview

Agents should return structured JSON so that Inez, automations, and the UI can safely interpret output and convert it into downstream actions.

## JSON Schema

```json
{
  "type": "object",
  "required": [
    "response",
    "summary",
    "db_writes",
    "todos",
    "follow_up_agents"
  ],
  "properties": {
    "response": {
      "type": "string",
      "description": "Human-readable answer for the operator."
    },
    "summary": {
      "type": "string",
      "description": "One-sentence summary suitable for Inez or dashboards."
    },
    "db_writes": {
      "type": "array",
      "description": "Requested database write operations.",
      "items": {
        "type": "object"
      }
    },
    "todos": {
      "type": "array",
      "description": "Todo suggestions created by the agent.",
      "items": {
        "type": "object"
      }
    },
    "follow_up_agents": {
      "type": "array",
      "description": "Requested follow-up dispatches.",
      "items": {
        "type": "object"
      }
    }
  }
}
```

## Field Descriptions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| response | string | yes | Human-readable answer for the operator. |
| summary | string | yes | One-sentence summary suitable for Inez or dashboards. |
| db_writes | array | yes | Requested database write operations. |
| todos | array | yes | Todo suggestions created by the agent. |
| follow_up_agents | array | yes | Requested follow-up dispatches. |

## Validation Rules

- Every response must include both `response` and `summary`.
- Database writes should use `insert`, `update`, or `upsert` only.
- When `op` is `update`, provide a stable `id`.
- Todo priorities should be one of `low`, `medium`, or `high`.
- Follow-up agent rows should reference valid `agent_id` values used in the portfolio.

## Example

```json
{
  "response": "I reviewed the inbox cleanup proposal and recommend archiving the newsletter batch first.",
  "summary": "Archive the newsletter batch and schedule a second-pass review tomorrow.",
  "db_writes": [
    {
      "table": "todos",
      "op": "insert",
      "data": {
        "title": "Approve inbox cleanup batch",
        "priority": "medium"
      }
    }
  ],
  "todos": [
    {
      "title": "Approve inbox cleanup batch",
      "project": "archonhub",
      "priority": "medium",
      "description": "Review the top 25 newsletter suggestions."
    }
  ],
  "follow_up_agents": [
    {
      "agent_id": "finance-cfo",
      "task": "Summarize billing emails before cleanup.",
      "project": "smithcap-finance"
    }
  ]
}
```

## Related Documentation

- [Dispatch contract](dispatch-contract.md)
- [Agent overview](../agents/overview.md)

## Source References

- `User request contract`
- `.agents/agentharness/app/v3/hub_server.py`

## Implementation Checklist

- Confirm `Agent Output Contract` responses use ISO 8601 UTC timestamps.
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

- `Agent Output Contract` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
