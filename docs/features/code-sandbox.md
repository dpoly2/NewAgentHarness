# Code Sandbox

_Generated on 2026-06-24 03:23 UTC._

## Overview

ArchonHub includes a secure code execution sandbox for Python snippets. It is exposed over the API and surfaced in the iOS app. The implementation prefers Docker for isolation, then falls back to a restricted subprocess mode for local development.

## Architecture

```
POST /api/sandbox/execute
  → validate code length and non-empty payload
  → code_sandbox._scan_code(code)
     • string-level blocked patterns
     • AST import analysis
  → choose Docker if image/runtime available, else subprocess
  → execute with timeout + output caps
  → collect stdout/stderr/exit code/files
  → return SandboxResult payload
```

## Security Model

- Timeout: 30 seconds.
- Output cap: 64 KB stdout, 8 KB stderr in the current helper implementation.
- Memory target: 512 MB in Docker mode.
- Network: Docker mode uses `--network=none`.
- File extraction only returns safe output types such as PNG, JPG, SVG, CSV, JSON, and TXT under the size cap.

## Allowed packages

- `abc`
- `base64`
- `collections`
- `copy`
- `csv`
- `dataclasses`
- `datetime`
- `decimal`
- `enum`
- `fractions`
- `functools`
- `io`
- `itertools`
- `json`
- `math`
- `matplotlib`
- `matplotlib.pyplot`
- `numpy`
- `pandas`
- `pathlib`
- `random`
- `re`
- `scipy`
- `seaborn`
- `sklearn`
- `statistics`
- `statsmodels`
- `string`
- `textwrap`
- `typing`

## Blocked imports

- `ctypes`
- `fabric`
- `ftplib`
- `gzip`
- `http`
- `imp`
- `importlib`
- `multiprocessing`
- `os`
- `paramiko`
- `pexpect`
- `pkgutil`
- `requests`
- `shutil`
- `smtplib`
- `socket`
- `subprocess`
- `sys`
- `tarfile`
- `threading`
- `urllib`
- `zipfile`

## Blocked patterns

- `__import__(`
- `exec(`
- `eval(`
- `compile(`
- `globals()`
- `locals()`
- `open(`
- `builtins`

## How it works (step by step)

1. The client posts code plus optional base64 data files.
2. `_scan_code(...)` rejects risky constructs such as `exec`, `eval`, `open`, `__import__`, or disallowed imports like `os` and `subprocess`.
3. The executor writes wrapped code into a temporary working directory and copies uploaded data files into the same directory.
4. If Docker is available, the system runs inside `archonhub-sandbox:latest` with a pinned scientific-Python toolchain. Otherwise, subprocess mode applies platform resource limits.
5. The executor collects generated files, truncates logs to safe sizes, and returns structured metadata.

## Configuration

- Docker image name: `archonhub-sandbox:latest`.
- Available scientific stack in the generated Dockerfile: pandas, numpy, matplotlib, seaborn, scipy, scikit-learn, statsmodels.
- Upload directory constant exists for future persisted file support.

## API Endpoints Used

| Endpoint | Purpose |
| --- | --- |
| `GET /api/sandbox/status` | Capability discovery |
| `POST /api/sandbox/execute` | Run code |

## Client Surfaces

| Surface | Feature |
| --- | --- |
| Desktop (⚡ Sandbox tab) | Code editor textarea, execute button, stdout/stderr display |
| Webapp (`showSandbox()`) | Code textarea, execute button, output panel, status indicator |
| iOS `CodeExecutionView` | Interactive client surface |

## Error Handling

- Empty code returns `400`.
- Code larger than 50 KB returns `400`.
- Security violations return a blocked result with `blocked_reason` rather than a Python traceback.
- Timeout produces a structured timeout error payload.
- Missing Docker does not fail the feature if subprocess mode is available.

## Related Documentation

- [Sandbox API](../api/sandbox.md)
- [Sandbox contract](../contracts/sandbox-contract.md)
- [iOS HubClient](../ios/hubclient.md)

## Source References

- `.agents/agentharness/app/v3/code_sandbox.py`
- `.agents/agentharness/app/v3/routers/sandbox.py`

## Implementation Checklist

- Confirm `code sandbox` responses use ISO 8601 UTC timestamps.
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

- `code sandbox` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.
