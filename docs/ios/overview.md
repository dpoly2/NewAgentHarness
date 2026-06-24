# iOS App Overview

_Generated on 2026-06-24 03:23 UTC._

## Overview

The SwiftUI client in `projects/archonhub-ios/ArchonHub` is the primary mobile front end for ArchonHub. It pairs with a watchOS app and shares auth, network, and model contracts with the local hub server.

## App structure

| Area | Primary files | Role |
| --- | --- | --- |
| App bootstrap | `App/ArchonHubApp.swift` | Bootstraps auth store, shared hub client, and watch coordination. |
| Root nav | `App/ContentView.swift` | Defines five primary tabs plus two segmented hub views. |
| Models | `Models/Models.swift` | Codable API contracts for server payloads. |
| Networking | `Network/HubClient.swift`, `Network/AuthStore.swift` | HTTP, WebSocket, token storage, login state. |
| Shared support | `Shared/AppSupport.swift` | Theme, constants, date formatting, API error types. |
| Views | `Views/**` | Feature-specific screens for runs, Inez, documents, memory, automations, sandbox, reports, etc. |

## Tab layout

| Tab | Contents |
| --- | --- |
| Dashboard | Health, quick actions, summary metrics |
| Inez | Executive chat and memory surfaces |
| Activity | Runs, reports, briefing, notifications |
| Workspace | Todos, documents, memory, automations |
| Settings | Server URL, auth, model and connector-adjacent settings |

## Setup

1. Open `projects/archonhub-ios/ArchonHub.xcodeproj` in Xcode.
2. Start the local hub server or point the app to a reachable hosted URL.
3. Configure the server URL in Settings if not using the default.
4. Log in with local credentials (default admin is documented, but should be changed in production).
5. Allow the app to connect the WebSocket for live updates after successful auth.

## Runtime behavior

- `HubClient.shared` is a singleton `ObservableObject` that owns the server URL, auth token, online/offline state, and WebSocket stream.
- The app stores the auth token in the keychain rather than `UserDefaults`.
- The watch app receives mirrored auth/session context via the watch coordinator in the app entry point.

## Feature coverage

- Runs and reports.
- Inez chat and memory.
- Todos, documents, automations.
- Code sandbox execution.
- Notifications, briefing, settings, and model views.

## Related Documentation

- [iOS views](views.md)
- [iOS models](models.md)
- [HubClient](hubclient.md)
- [watchOS](watchos.md)

## Source References

- `projects/archonhub-ios/README.md`
- `projects/archonhub-ios/ArchonHub/App/ArchonHubApp.swift`
- `projects/archonhub-ios/ArchonHub/App/ContentView.swift`

## Implementation Checklist

- Confirm `ios overview` responses use ISO 8601 UTC timestamps.
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

- `ios overview` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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
