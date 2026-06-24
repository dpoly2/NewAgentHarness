# Local Deployment

_Generated on 2026-06-24 03:23 UTC._

## Overview

Local ArchonHub development is centered on the Python engine in `.agents/agentharness/app/v3/`, a `.agents/.env` file, and the commands documented in the repository instructions.

## Prerequisites

- macOS (per the current workstation target) or another platform supported by Python + FastAPI.
- Python environment, typically `.venv/` in the repository root workflow.
- `.agents/.env` created from `.agents/.env.example`.
- Optional extras: Docker, Ollama, SerpAPI key, ChromaDB dependencies, OpenAI key, Outlook/Google OAuth credentials.

## Setup steps

```bash
cp .agents/.env.example .agents/.env
# fill in keys and secrets
python .agents/agentharness/app/v3/hub_server.py
```

## Full stack launcher

```powershell
.\launch_v3.ps1
```

## Server details

- Default port: `8765`.
- Health check: `http://localhost:8765/api/health`.
- API docs: `http://localhost:8765/docs`.
- Web dashboard: `http://localhost:8765/web`.

## Local tests

```powershell
cd .agents/agentharness/app/v3/tests
python run_tests.py
python run_tests.py db
python run_tests.py server
python run_tests.py markets
python run_tests.py oauth
python run_tests.py ui
python run_tests.py --fast
python run_tests.py --verbose
```

## Environment highlights

- `OPENAI_API_KEY` is required for many LLM-backed features.
- `JWT_SECRET` and `ADMIN_PASSWORD` should be changed for any non-personal environment.
- `HUB_HOST` and `HUB_PORT` control bind address/port.

## Troubleshooting

- If `/api/docs` does not load, confirm FastAPI/Uvicorn dependencies are installed.
- If embeddings fail, verify both ChromaDB dependencies and `OPENAI_API_KEY`.
- If WebSocket live updates fail, inspect the auth-handshake mismatch documented in the WebSocket and HubClient docs.
- If scheduler jobs do not appear, verify APScheduler is installed and the server startup path invoked the scheduler builder.

## Related Documentation

- [Docker deployment](docker.md)
- [Environment variables](environment.md)
- [Architecture overview](../architecture/overview.md)

## Source References

- `.github/copilot-instructions.md`
- `.agents/.env.example`
- `.agents/agentharness/app/v3/requirements.txt`

## Implementation Checklist

- Confirm `local deployment` responses use ISO 8601 UTC timestamps.
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

- `local deployment` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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
