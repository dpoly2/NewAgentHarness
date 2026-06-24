# Web Search

_Generated on 2026-06-24 03:23 UTC._

## Overview

The web search subsystem adds fresh, source-backed knowledge to ArchonHub using SerpAPI over Google Search. It is especially useful for markets, breaking news, research, and any question where stale model knowledge is not acceptable.

## Architecture

```
user query / agent need
  → SearchAnalyzer.should_search(query)
  → SerpAPIClient.search(query)
  → parse `organic_results`
  → SearchResult + SearchSource objects
  → format_search_context_for_llm(...)
  → LLM answer with [cite:N] markers
  → CitationFormatter.format_with_citations(...)
```

## Search Heuristics

### Regex patterns that trigger a search

- `\b(?:latest|recent|current|today|this week|breaking|news about)\b`
- `\b(?:what is|what are|what\`
- `\b(?:price|stock|market|trading) (?:of|for)\b`
- `\b(?:weather|temperature) in\b`
- `\b(?:how much|cost) (?:is|does)\b`
- `\b(?:find|search for|look up|get info about)\b`
- `\b(?:when is|when will|when did)\b.{0,50}\b(?:next|upcoming)\b`
- `\b(?:status|state|condition) of\b`
- `\b(?:compare|versus|vs\.?) `

### Fresh-data topics

- `market`
- `stock`
- `price`
- `trading`
- `earnings`
- `news`
- `weather`
- `sports`
- `election`
- `covid`
- `virus`
- `outbreak`
- `breaking`
- `latest`
- `current`
- `recent`

## How it works (step by step)

1. A query is classified for freshness using `SearchAnalyzer.should_search(...)`.
2. `SerpAPIClient` calls `https://serpapi.com/search` with the configured API key.
3. Organic results are mapped into typed `SearchSource` rows.
4. Search context is formatted for the answering LLM.
5. Citation markers are normalized into a source footer for the final user-visible response.

## Configuration

- Environment variable: `SERPAPI_API_KEY`.
- Default language: `en`.
- Default country: `us`.
- Requested result count is capped at 20 per search call.

## API Endpoints Used

| Endpoint | Purpose |
| --- | --- |
| `GET /api/search` | Direct search surface |
| Inez / research agent flows | Indirect use when freshness is required |

## Error Handling

- Missing API key raises a value error and should surface as a server or feature error to the caller.
- HTTP 401 is interpreted as an invalid SerpAPI key.
- HTTP 429 is interpreted as a SerpAPI rate limit.
- If `requests` is not installed, the feature cannot execute.

## Agent Usage

- Markets agents can use this feature for catalysts, earnings chatter, price-sensitive events, and macro headlines.
- Research-oriented agents can use it to gather sources before composing outputs.
- Citation formatting makes it possible to store search evidence in conversation history or feedback review flows.

## Related Documentation

- [Search API](../api/search.md)
- [Feedback learning](feedback-learning.md)
- [Models API](../api/models.md)

## Source References

- `.agents/agentharness/app/v3/web_search.py`
- `.agents/agentharness/app/v3/hub_server.py`

## Implementation Checklist

- Confirm `web search` responses use ISO 8601 UTC timestamps.
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

- `web search` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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
