# Feedback Learning

_Generated on 2026-06-24 03:23 UTC._

## Overview

Feedback Learning captures user reactions, explicit corrections, and inferred style preferences so ArchonHub can improve future outputs and detect systematic quality issues.

## Architecture

```
message rendered
  → POST /api/messages/{id}/feedback or /api/corrections
  → message_feedback / corrections tables
  → feedback analysis / learning pass
  → user_style_preferences updated
  → API exposes stats, analysis, and preferences
```

## Data stores

| Table | Purpose |
| --- | --- |
| `message_feedback` | Raw positive/negative ratings with timestamps and metadata. |
| `corrections` | User-provided corrected text or guidance. |
| `user_style_preferences` | Learned preferences for tone, structure, or formatting. |

## How it works

1. The client sends thumbs-up/down or a correction payload.
2. The feedback row is written to SQLite.
3. Aggregate endpoints compute ratings and trends.
4. Learned preferences can be surfaced back into prompting or UI settings.
5. Monitoring can treat unusual feedback spikes as an anomaly worth notifying about.

## Configuration

- Tables are created by `add_feedback_system.py`.
- The iOS client can call feedback endpoints directly even though the core app currently focuses more on runs, memory, and documents.

## API Endpoints Used

| Endpoint | Purpose |
| --- | --- |
| `POST /api/messages/{message_id}/feedback` | Store simple feedback |
| `POST /api/corrections` | Store explicit correction |
| `GET /api/feedback/stats` | Aggregate counts (`total_feedback`, `positive_count`, `negative_count`, `correction_count`) |
| `GET /api/feedback/analyze` | Higher-order analysis |
| `GET /api/feedback/preferences` | Learned style preferences |

## `GET /api/feedback/stats` Response Shape

```json
{
  "success": true,
  "stats": {
    "total_feedback": 42,
    "positive_count": 30,
    "negative_count": 8,
    "correction_count": 4
  },
  "recent_feedback": [...]
}
```

> **Note:** The field names are `positive_count`, `negative_count`, `correction_count` — not `positive`, `negative`, `correction`.

## Client Surfaces

| Surface | Feature |
| --- | --- |
| Desktop (Connectors tab) | Stats panel with KPI counts, recent feedback list |
| Webapp (`showFeedback()`) | 5 KPI cards (total, positive, negative, corrections, net score), analysis panel |
| iOS | Thumbs up/down per message |

## Error Handling

- Missing message ids or malformed payloads return `400`/`404` depending on the route implementation.
- Analysis endpoints can degrade if optional rows do not yet exist; callers should tolerate empty arrays or empty preference sets.

## Why it matters

- It creates an explicit loop from user reaction back into system behavior.
- It gives operators a way to distinguish one-off mistakes from persistent prompt or model issues.
- It supplies anomaly signals for proactive monitoring.

## Related Documentation

- [Feedback API](../api/feedback.md)
- [Progressive intelligence](progressive-intelligence.md)
- [Proactive monitor](proactive-monitor.md)

## Source References

- `.agents/agentharness/app/v3/add_feedback_system.py`
- `.agents/agentharness/app/v3/feedback_learner.py`
- `.agents/agentharness/app/v3/proactive_monitor.py`

## Implementation Checklist

- Confirm `feedback learning` responses use ISO 8601 UTC timestamps.
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

- `feedback learning` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
