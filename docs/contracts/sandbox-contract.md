# Sandbox Contract

_Generated on 2026-06-24 03:23 UTC._

## Overview

The sandbox contract combines the execute request and execute result into a single implementer-facing reference.

## JSON Schema

```json
{
  "type": "object",
  "properties": {
    "code": {
      "type": "string",
      "description": "Python source text."
    },
    "language": {
      "type": "string",
      "description": "Currently `python`."
    },
    "data_files": {
      "type": "array",
      "description": "Optional uploaded data files."
    },
    "success": {
      "type": "boolean",
      "description": "Execution success flag."
    },
    "execution_id": {
      "type": "string",
      "description": "Unique execution UUID."
    },
    "stdout": {
      "type": "string",
      "description": "Captured stdout."
    },
    "stderr": {
      "type": "string",
      "description": "Captured stderr."
    },
    "exit_code": {
      "type": "integer",
      "description": "Process exit code."
    },
    "execution_time_ms": {
      "type": "integer",
      "description": "Elapsed time in milliseconds."
    },
    "generated_files": {
      "type": "array",
      "description": "Generated output files."
    },
    "error": {
      "type": "string",
      "description": "Structured error text or null."
    },
    "blocked_reason": {
      "type": "string",
      "description": "Why the code was blocked or null."
    },
    "mode": {
      "type": "string",
      "description": "docker|subprocess"
    }
  }
}
```

## Field Descriptions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| code | string | no | Python source text. |
| language | string | no | Currently `python`. |
| data_files | array | no | Optional uploaded data files. |
| success | boolean | no | Execution success flag. |
| execution_id | string | no | Unique execution UUID. |
| stdout | string | no | Captured stdout. |
| stderr | string | no | Captured stderr. |
| exit_code | integer | no | Process exit code. |
| execution_time_ms | integer | no | Elapsed time in milliseconds. |
| generated_files | array | no | Generated output files. |
| error | string | no | Structured error text or null. |
| blocked_reason | string | no | Why the code was blocked or null. |
| mode | string | no | docker|subprocess |

## Validation Rules

- Blocked imports include os, sys, subprocess, socket, urllib, http, requests, shutil, ctypes, multiprocessing, threading, importlib, and additional archive/network modules present in the code.
- Request code must be non-empty and less than 50 KB.
- Generated files are base64 encoded and size-limited.
- Mode is either `docker` or `subprocess`.

## Example

```json
{
  "code": "print(\"hello\")",
  "language": "python",
  "data_files": [],
  "success": true,
  "execution_id": "uuid",
  "stdout": "hello\n",
  "stderr": "",
  "exit_code": 0,
  "execution_time_ms": 12,
  "generated_files": [],
  "error": null,
  "blocked_reason": null,
  "mode": "subprocess"
}
```

## Related Documentation

- [Code sandbox feature](../features/code-sandbox.md)
- [Sandbox API](../api/sandbox.md)

## Source References

- `User request contract`
- `.agents/agentharness/app/v3/code_sandbox.py`
- `.agents/agentharness/app/v3/hub_server.py:4600-4654`

## Implementation Checklist

- Confirm `Sandbox Contract` responses use ISO 8601 UTC timestamps.
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

- `Sandbox Contract` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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
