# Sandbox API

_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._

## Overview

The sandbox API exposes secure code execution for Python snippets, optionally with uploaded data files. Execution is screened for dangerous imports and can run in Docker or a restricted subprocess.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Line |
| --- | --- | --- | --- | --- |
| GET | /api/sandbox/status | sandbox_status | Bearer JWT | 4605 |
| POST | /api/sandbox/execute | sandbox_execute | Bearer JWT | 4615 |

## Detailed Endpoints

### GET `/api/sandbox/status`

- **Handler:** `sandbox_status`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4605`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Returns availability and mode configuration for Docker/subprocess execution.

#### Example

```bash
curl -X GET http://localhost:8765/api/sandbox/status \
  -H 'Authorization: Bearer <jwt>'
```

```json
{
  "success": true,
  "docker_available": false,
  "subprocess_available": true,
  "default_mode": "subprocess"
}
```

### POST `/api/sandbox/execute`

- **Handler:** `sandbox_execute`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/hub_server.py:4615`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Executes code and returns stdout, stderr, exit code, timing, generated files, and block/error metadata.

#### Example

```bash
curl -X POST http://localhost:8765/api/sandbox/execute \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"value": "example"}'
```

```json
{
  "success": true,
  "execution_id": "uuid",
  "stdout": "hello\n",
  "stderr": "",
  "exit_code": 0,
  "execution_time_ms": 11,
  "generated_files": [],
  "error": null,
  "blocked_reason": null,
  "mode": "subprocess"
}
```

## Error Handling

- `400` indicates validation or bad input.
- `401` indicates a missing or invalid JWT.
- `403` indicates the caller is authenticated but lacks the required role, usually admin-only surfaces.
- `404` indicates the resource identifier does not exist.
- `500` indicates an unhandled subsystem error such as missing optional dependencies, database failures, or third-party API failures.

## Client Notes

- The SwiftUI app consumes many of these routes through `HubClient.swift` and `Models.swift`.
- Treat list responses as dynamic; some endpoints return arrays directly instead of a named `items` wrapper.
- Nullable JSON fields appear in several resources and are intentionally modelled as optional in Swift.

## Related Documentation

- [Sandbox contract](../contracts/sandbox-contract.md)
- [Code sandbox feature](../features/code-sandbox.md)

## Source References

- `.agents/agentharness/app/v3/hub_server.py:4600-4654`
- `.agents/agentharness/app/v3/code_sandbox.py`

## Implementation Checklist

- Confirm `Sandbox API` responses use ISO 8601 UTC timestamps.
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

- `Sandbox API` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Extra Source Anchors

- `.agents/agentharness/app/v3/hub_server.py:4600-4654`
- `.agents/agentharness/app/v3/code_sandbox.py`

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
