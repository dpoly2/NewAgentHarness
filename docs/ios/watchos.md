# watchOS App

_Generated on 2026-06-24 03:23 UTC._

## Overview

The watchOS companion gives ArchonHub a glanceable status surface, a quick-run launcher, recent notifications, and a complication for active runs.

## App structure

| File | Role |
| --- | --- |
| `ArchonHubWatch/App/ArchonHubWatchApp.swift` | watchOS app entry point |
| `ArchonHubWatch/App/WatchMainView.swift` | Root paging tab view |
| `ArchonHubWatch/Views/WatchStatusView.swift` | Status dashboard |
| `ArchonHubWatch/Views/WatchQuickRunView.swift` | One-tap run launcher |
| `ArchonHubWatch/Views/WatchNotificationsView.swift` | Recent alerts list |
| `ArchonHubWatch/Complications/ArchonHubComplication.swift` | Watch face complication |

## Screens

- **Status:** shows hub reachability, active runs, and pending todos.
- **Quick Run:** launches a curated agent/task workflow from the wrist.
- **Notifications:** surfaces recent alerts from the backend notification stream.
- **Complication:** shows active run count using shared app state persisted by the iOS client.

## How it works

1. The iOS app shares auth/session context with watch components.
2. The watch app renders lightweight status-oriented views instead of full management surfaces.
3. Quick actions call into the same network/client layer abstractions or shared state patterns.

## Error handling

- The watch app should treat the hub as offline whenever health or auth checks fail.
- Because the watch UI is compact, errors should surface as concise status banners rather than verbose debug detail.

## Notes

- The watch app complements rather than mirrors the full phone UI.
- The complication relies on a small set of summary values (`activeRuns`, `pendingTodos`) stored by the shared client.

## Related Documentation

- [iOS overview](overview.md)
- [HubClient](hubclient.md)
- [WebSocket contract](../contracts/websocket-contract.md)

## Source References

- `projects/archonhub-ios/ArchonHubWatch/App/WatchMainView.swift`
- `projects/archonhub-ios/ArchonHubWatch/Views/WatchStatusView.swift`
- `projects/archonhub-ios/ArchonHubWatch/Complications/ArchonHubComplication.swift`

## Implementation Checklist

- Confirm `watchos` responses use ISO 8601 UTC timestamps.
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

- `watchos` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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
