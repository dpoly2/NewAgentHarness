# HubClient.swift

_Generated on 2026-06-24 03:23 UTC from the shared iOS network client._

## Overview

`HubClient` centralizes auth, HTTP requests, WebSocket connectivity, online/offline state, and server URL persistence for the iOS app.

## Responsibilities

- Persist and read the server URL from `UserDefaults`.
- Persist and read the JWT token from the keychain.
- Build authenticated GET/POST/PUT/DELETE calls.
- Maintain a WebSocket connection and reconnect loop.
- Publish server events through a Combine `PassthroughSubject`.

## Public methods

| Method | Line | Signature |
| --- | --- | --- |
| login | 42 | func login(username: String, password: String) async throws -> LoginResponse { |
| delete | 118 | func delete(_ path: String) async throws { |
| connectWebSocket | 122 | func connectWebSocket() { |
| disconnectWebSocket | 137 | func disconnectWebSocket() { |
| setToken | 144 | func setToken(_ value: String, persist: Bool = true) { |
| clearToken | 151 | func clearToken() { |
| applyHealthResponse | 157 | func applyHealthResponse(_ health: HealthResponse) { |
| checkHealth | 163 | func checkHealth() async { |

## Auth handling

- Login posts to `/api/auth/login` and saves the returned token.
- `Authorization: Bearer <token>` is attached automatically when a token is present.
- `clearToken()` wipes the keychain entry and disconnects the socket.

## Error handling

- Invalid URL and response issues map to `APIError.invalidURL` and `APIError.invalidResponse`.
- Non-200 HTTP responses are parsed for `detail`/`message` fields before falling back to status text.
- Decoding failures print a response snippet to help diagnose contract drift.

## WebSocket handling

- `connectWebSocket()` creates a `URLSessionWebSocketTask` and attaches the bearer token as a header when present.
- `receiveWebSocketMessage()` attempts to decode each message into `WSEvent` and falls back to a generic text event.
- Reconnect attempts use exponential backoff up to 30 seconds.

## Contract caveat

The server currently expects an initial JSON auth message after the WebSocket connection is accepted, while the iOS client sends auth in the header only. If real-time events are failing in practice, this mismatch is the first thing to inspect.

## Related Documentation

- [WebSocket API](../api/websocket.md)
- [Authentication API](../api/authentication.md)
- [iOS models](models.md)

## Source References

- `projects/archonhub-ios/ArchonHub/Network/HubClient.swift`
- `projects/archonhub-ios/ArchonHub/Shared/AppSupport.swift`

## Implementation Checklist

- Confirm `hubclient` responses use ISO 8601 UTC timestamps.
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

- `hubclient` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
