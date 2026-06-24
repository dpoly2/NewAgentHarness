# Morning Briefing

_Generated on 2026-06-24 03:23 UTC._

## Overview

Morning Briefing is the daily executive summary surface. It compiles active todos, key memory facts, and other operational signals into a concise start-of-day update for David Smith and the ArchonHub clients.

## Architecture

```
scheduler 6:50 AM CT
  → job_daily_briefing_compute(...)
  → queue run for `inez-chief-of-staff`
  → optional report generation
  → morning_brief.generate_brief(user_id)
  → gather todos / memory / placeholders for email + markets
  → save morning_briefs row
  → expose via /api/briefing/morning and history routes
```

## Data sources

- Active todos (`pending`, `in_progress`).
- Global memory category `projects` for active missions.
- Global memory category `deadlines` for same-day urgency hints.
- Report scheduler hook outputs for broader operational summaries.
- Placeholder slots for urgent emails and market movers, which are not fully implemented in the helper class yet.

## How it works

1. The scheduler enqueues a daily briefing run for Inez.
2. The `MorningBriefAgent` can also generate a direct stored morning brief from SQLite sources.
3. The brief is saved to `morning_briefs` with basic stats.
4. Clients call `/api/briefing/morning` or `/api/briefing/history` to retrieve current and past briefings.

## Configuration

- Timezone for built-in scheduling: `America/Chicago`.
- The built-in briefing job is defined as `daily_briefing` at 6:50 AM CT in `hub_scheduler.py`.

## API Endpoints Used

| Endpoint | Purpose |
| --- | --- |
| `GET /api/briefing` | General briefing |
| `GET /api/briefing/morning` | Morning briefing |
| `GET /api/briefing/history` | Historical briefings |
| `GET /api/inez/status` | Related operational awareness surface |

## Error Handling

- The helper functions degrade to empty lists if email/market collectors are not implemented.
- SQLite issues surface as server errors to the API caller.
- Because the morning brief table is created lazily, the first run is responsible for bootstrapping that table if needed.

## Schedule

- Built-in schedule: `daily_briefing` at 6:50 AM Central.
- Separate reflexion/report jobs run around the briefing window, so morning context can incorporate overnight status and the prior day's summaries.

## Related Documentation

- [Briefing API](../api/briefing.md)
- [Scheduler API](../api/scheduler.md)
- [Inez agent](../agents/inez.md)

## Source References

- `.agents/agentharness/app/v3/morning_brief.py`
- `.agents/agentharness/app/v3/hub_scheduler.py`
- `.agents/agentharness/app/v3/hub_server.py`

## Implementation Checklist

- Confirm `morning briefing` responses use ISO 8601 UTC timestamps.
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

- `morning briefing` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
