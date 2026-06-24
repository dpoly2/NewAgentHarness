# API Response Contract

_Generated on 2026-06-24 03:23 UTC._

## Overview

ArchonHub APIs mostly follow a pragmatic FastAPI pattern: feature endpoints return `{ "success": true, ... }`, while auth and a few list/detail routes return bare domain objects or arrays. Errors always use FastAPI-style `detail` payloads.

## JSON Schema

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Standard success flag for feature endpoints."
    },
    "detail": {
      "type": "string",
      "description": "Error message for failed requests."
    },
    "timestamp": {
      "type": "string",
      "description": "ISO 8601 UTC timestamp when included."
    }
  }
}
```

## Field Descriptions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| success | boolean | no | Standard success flag for feature endpoints. |
| detail | string | no | Error message for failed requests. |
| timestamp | string | no | ISO 8601 UTC timestamp when included. |

## Validation Rules

- Success responses should set `success: true` when the handler uses an envelope.
- Error responses should use `{ "detail": "error message" }` with the proper HTTP status.
- Unhandled `500` responses are normalized by the global exception handler to `{ "detail": "internal server error" }`.
- Auth uses Bearer JWT in the `Authorization` header.
- Timestamps should be interpreted as ISO 8601 UTC values.

## Example

```json
{
  "success": true,
  "data": {
    "id": "example"
  },
  "generated_at": "2026-06-23T00:00:00Z"
}
```

## Related Documentation

- [Authentication API](../api/authentication.md)
- [HubClient](../ios/hubclient.md)

## Source References

- `.agents/agentharness/app/v3/core/auth.py`
- `.agents/agentharness/app/v3/routers/auth_routes.py`
- `projects/archonhub-ios/ArchonHub/Network/HubClient.swift`

## Implementation Checklist

- Confirm `API Response Contract` responses use ISO 8601 UTC timestamps.
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

- `API Response Contract` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
