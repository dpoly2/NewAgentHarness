# Docker Deployment

_Generated on 2026-06-24 03:23 UTC._

## Overview

The repository ships a Dockerfile and `docker-compose.yml` for running the local ArchonHub hub server in a container with persisted volumes.

## Files

| File | Purpose |
| --- | --- |
| `Dockerfile` | Builds a slim Python image, installs requirements (including `pyyaml>=6.0`), creates `/app/uploads` and `/app/chroma_db`, runs as non-root user `archonhub` (uid `1000`), exposes port 8765, and defines the container `HEALTHCHECK`. |
| `docker-compose.yml` | Runs the `hub` service with persisted volumes for memory, runtime data, uploads, and ChromaDB. |

## Compose summary

- Service name: `hub`.
- Container name: `archonhub`.
- Port mapping: `8765:8765`.
- Volumes: `archonhub_memory`, `archonhub_data`, `archonhub_uploads`, `archonhub_chroma`.
- Env file: `.agents/.env`.

## Build and run

```bash
docker compose up --build -d
```

## Health check

```bash
python -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/api/health', timeout=5)"
```

## Dockerfile highlights

- Base image: `python:3.13-slim`.
- Installs system libraries for PyMuPDF, Pillow, and ChromaDB-related native dependencies.
- Copies `.agents/agentharness/app/v3/requirements.txt` first for better build caching.
- Runs as non-root user `archonhub` (uid `1000`).
- Creates `/app/uploads` for evidence file refs and `/app/chroma_db` for the vector store.
- The container `HEALTHCHECK` now lives in the Dockerfile itself, in addition to any compose-level health settings.
- `pyyaml>=6.0` is included in requirements for YAML plan authoring.
- Starts with `CMD ["python", "hub_server.py"]`.

## Volumes and persistence

- `archonhub_memory` keeps the SQLite database and other persisted hub memory.
- `archonhub_data` keeps logs, backups, and other runtime data.
- `archonhub_uploads` keeps uploaded evidence files and file references.
- `archonhub_chroma` keeps the ChromaDB vector store.

## Limitations

- The Dockerfile targets the hub server only, not the iOS/watchOS clients.
- Some local paths and relative directory assumptions should be re-verified if you substantially change the folder layout.
- Sandbox Docker mode is a separate concern from running the hub itself in Docker.

## Related Documentation

- [Local deployment](local.md)
- [Environment variables](environment.md)

## Source References

- `Dockerfile`
- `docker-compose.yml`

## Implementation Checklist

- Confirm `docker deployment` responses use ISO 8601 UTC timestamps.
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

- `docker deployment` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
