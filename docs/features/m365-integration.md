# Microsoft 365 Integration

_Generated on 2026-06-24 03:23 UTC._

## Overview

Microsoft 365 integration is implemented primarily through the Outlook/Office 365 OAuth connector path. The current local code focuses on email (IMAP/SMTP OAuth), but the architecture is compatible with broader Microsoft Graph expansion for calendar, OneDrive, and Teams workflows.

## Architecture

```
M365 user intent
  → connector row with provider `microsoft`
  → OAuth init endpoint
  → Microsoft auth URL + redirect callback
  → token exchange + refresh token storage
  → XOAUTH2 for IMAP / SMTP
  → email cleanup / future calendar / file workflows
```

## Current implementation scope

- Implemented: Microsoft OAuth authorization code flow, token refresh handling, IMAP/SMTP access for Outlook/Office 365 mailboxes.
- Not yet fully implemented in the local code: direct Microsoft Graph API clients for calendar events, OneDrive files, or Teams chat/actions.

## OAuth details

| Item | Value |
| --- | --- |
| Authorization URL | `https://login.microsoftonline.com/common/oauth2/v2.0/authorize` |
| Token URL | `https://login.microsoftonline.com/common/oauth2/v2.0/token` |
| Scopes | `https://outlook.office.com/IMAP.AccessAsUser.All https://outlook.office.com/SMTP.Send offline_access email openid` |
| Redirect | `http://localhost:8765/api/connectors/oauth/microsoft/callback` by default |
| IMAP host | `outlook.office365.com:993` |
| SMTP host | `smtp.office365.com:587` |

## How it works

1. Create a connector with provider `microsoft` and OAuth client credentials.
2. Call the init endpoint to obtain an authorization URL and state.
3. Complete the browser sign-in and callback.
4. Persist the access token, refresh token, expiry, and email metadata in `email_connectors.credentials`.
5. Use `get_valid_access_token(...)` to transparently refresh expired tokens.
6. Reuse the connector for inbox analysis or SMTP send flows.

## Configuration

- Environment variable `ARCHONHUB_REDIRECT_BASE` can change the redirect host.
- Azure App Registration must allow the configured redirect URI.
- Offline access is necessary for long-lived background automations.

## API Endpoints Used

| Endpoint | Purpose |
| --- | --- |
| `GET /api/connectors/oauth/microsoft/init` | Begin OAuth |
| `GET /api/connectors/oauth/microsoft/callback` | Handle callback |
| `GET /api/connectors` | List configured connectors |
| `POST /api/email/cleanup/analyze` | Use connector for mailbox workflows |

## Error Handling

- Missing client id/secret or mismatched redirect URI will stop the flow before token exchange completes.
- Expired or revoked refresh tokens will break automated access until the connector is re-authorized.
- The current code is email-centric; requests for calendar/OneDrive/Teams features require additional Graph-layer implementation.

## Expansion path

- Calendar briefings can sit naturally beside the morning brief.
- OneDrive file sync can share the same document-RAG ingestion pipeline.
- Teams notifications can reuse the current notifications/reporting abstractions.

## Related Documentation

- [Connectors API](../api/connectors.md)
- [Email cleanup feature](email-cleanup.md)
- [Environment variables](../deployment/environment.md)

## Source References

- `.agents/agentharness/app/v3/oauth_connector.py`
- `.agents/agentharness/app/v3/hub_server.py`

## Implementation Checklist

- Confirm `m365 integration` responses use ISO 8601 UTC timestamps.
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

- `m365 integration` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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
