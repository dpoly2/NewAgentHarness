# Environment Variables

_Generated on 2026-06-24 03:23 UTC by scanning the local Python runtime modules and `.agents/.env.example`._

## Overview

This reference combines the checked-in `.agents/.env.example` with environment variables discovered in the current Python source tree.

## Variables from `.agents/.env.example`

| Variable | Example / default |
| --- | --- |
| OPENAI_API_KEY | sk-... |
| ANTHROPIC_API_KEY |  |
| OPENAI_MODEL | gpt-4o-mini |
| HUB_PORT | 8765 |
| HUB_HOST | 0.0.0.0 |
| JWT_SECRET | CHANGE-ME-use-a-long-random-string-in-production |
| ADMIN_PASSWORD | ArchonHub2024! |
| OUTLOOK_CLIENT_ID |  |
| OUTLOOK_CLIENT_SECRET |  |
| OUTLOOK_TENANT_ID |  |
| LOG_LEVEL | INFO |

## Variables discovered in code

| Variable | Referenced at |
| --- | --- |
| ADMIN_PASSWORD | .agents/agentharness/app/v3/hub_server.py:150 |
| ARCHONHUB_PASSWORD | .agents/agentharness/app/v3/hub_client.py:50 |
| ARCHONHUB_REDIRECT_BASE | .agents/agentharness/app/v3/oauth_connector.py:71 |
| ARCHONHUB_USER | .agents/agentharness/app/v3/hub_client.py:49 |
| GITHUB_TOKEN | .agents/agentharness/app/v3/llm_router.py:307<br>.agents/agentharness/app/v3/hub_nodes.py:152 |
| HUB_HOST | .agents/agentharness/app/v3/hub_server.py:4728 |
| HUB_PORT | .agents/agentharness/app/v3/hub_server.py:4727 |
| JWT_SECRET | .agents/agentharness/app/v3/hub_server.py:145 |
| LLM_BASE_URL | .agents/agentharness/app/v3/hub_nodes.py:96 |
| LLM_PROVIDER | .agents/agentharness/app/v3/hub_nodes.py:95 |
| OLLAMA_HOST | .agents/agentharness/app/v3/llm_router.py:41 |
| OPENAI_API_KEY | .agents/agentharness/app/v3/inez_agent.py:121<br>.agents/agentharness/app/v3/llm_router.py:308<br>.agents/agentharness/app/v3/global_memory.py:383<br>.agents/agentharness/app/v3/test_followups.py:153<br>.agents/agentharness/app/v3/hub_nodes.py:97<br>.agents/agentharness/app/v3/hub_nodes.py:131 |
| OPENAI_MODEL | .agents/agentharness/app/v3/inez_agent.py:62<br>.agents/agentharness/app/v3/global_memory.py:411<br>.agents/agentharness/app/v3/hub_nodes.py:78<br>.agents/agentharness/app/v3/hub_nodes.py:98 |
| SERPAPI_API_KEY | .agents/agentharness/app/v3/inez_agent.py:1308<br>.agents/agentharness/app/v3/test_inez_search.py:21<br>.agents/agentharness/app/v3/test_inez_search.py:131<br>.agents/agentharness/app/v3/web_search.py:67 |

## Important variables

- `OPENAI_API_KEY`: Enables most LLM-backed features and document embeddings.
- `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `PERPLEXITY_API_KEY`, `GITHUB_TOKEN`: Provider-specific model catalog support.
- `OPENAI_MODEL`: Overrides the default cloud model in some paths.
- `JWT_SECRET`: Required for secure JWT signing.
- `ADMIN_PASSWORD`: Seeded admin password.
- `HUB_HOST`, `HUB_PORT`: Network binding for the FastAPI server.
- `ARCHONHUB_REDIRECT_BASE`: OAuth callback base URL.
- `SERPAPI_API_KEY`: Fresh web search.
- `OLLAMA_HOST`: Local Ollama discovery endpoint.

## Security notes

- Never commit filled `.agents/.env` secrets to source control.
- Rotate JWT and OAuth credentials for any shared or production-like deployment.
- Use app passwords or OAuth tokens for mailbox access; do not hardcode WordPress or mailbox secrets in code.

## Related Documentation

- [Local deployment](local.md)
- [Docker deployment](docker.md)
- [Connectors API](../api/connectors.md)

## Source References

- `.agents/.env.example`
- `.agents/agentharness/app/v3/hub_client.py:49`
- `.agents/agentharness/app/v3/hub_client.py:50`
- `.agents/agentharness/app/v3/hub_nodes.py:95`
- `.agents/agentharness/app/v3/hub_nodes.py:96`
- `.agents/agentharness/app/v3/hub_server.py:145`
- `.agents/agentharness/app/v3/hub_server.py:150`
- `.agents/agentharness/app/v3/hub_server.py:4727`
- `.agents/agentharness/app/v3/hub_server.py:4728`
- `.agents/agentharness/app/v3/inez_agent.py:121`
- `.agents/agentharness/app/v3/inez_agent.py:1308`
- `.agents/agentharness/app/v3/inez_agent.py:62`
- `.agents/agentharness/app/v3/llm_router.py:307`
- `.agents/agentharness/app/v3/llm_router.py:41`
- `.agents/agentharness/app/v3/oauth_connector.py:71`

## Implementation Checklist

- Confirm `environment variables` responses use ISO 8601 UTC timestamps.
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

- `environment variables` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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
