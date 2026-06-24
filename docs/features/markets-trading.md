# Markets and Paper Trading

_Generated on 2026-06-24 03:23 UTC._

## Overview

ArchonHub includes a growing markets subsystem for watchlists, paper trades, trade theories, positions, daily pre-market briefs, and project-specific agent workflows under the Legacy Alpha Capital AI umbrella.

## Architecture

```
markets agents / scheduler jobs
  → runs + reports + notifications
  → market_watchlist / market_positions / market_trade_theories / market_paper_trades
  → morning briefs / reports / dashboards
  → iOS reads run history and reports
  → market project lead coordinates specialist desks
```

## Data model

| Table | Purpose |
| --- | --- |
| `market_watchlist` | Tracked tickers and target prices. |
| `market_positions` | Open/closed positions with P&L fields. |
| `market_trade_theories` | Strategy containers with win/loss stats and balances. |
| `market_paper_trades` | Trade-by-trade paper positions tied to a theory. |

## How it works

1. Markets agents generate research, trade ideas, or monitoring output.
2. Scheduler jobs can queue recurring market briefs and weekly/monthly reviews.
3. Reports are persisted through the reports subsystem.
4. Paper trades and theories provide a structured record for simulation and review.
5. Inez can surface the resulting status as part of a daily or ad-hoc executive summary.

## Configuration

- The main orchestration agent is `markets-project-lead`.
- Supporting agents include CIO, CRO, quant, intelligence desk, options strategist, tactical alpha, macro analyst, equity analyst, and technical analyst.
- The README identifies NVDA tracking and options workflows as active themes in the portfolio context; treat those as project content rather than hardcoded market logic.

## API Endpoints Used

| Endpoint / surface | Purpose |
| --- | --- |
| `POST /api/runs` | Launch markets agents |
| `GET /api/runs` | Inspect run history |
| `GET /api/reports` | Read market reports |
| `GET /api/briefing` | Surface current market-relevant briefing content |
| Scheduler jobs in `hub_scheduler.py` | Pre-market brief, weekly picks, monthly review |

## Error Handling

- Market modules rely heavily on agent execution and optional external data; failures typically surface as failed runs or missing report content rather than a dedicated REST error type.
- Paper trading data itself is local SQLite state and does not depend on a brokerage integration.

## Notable scheduled jobs

- `markets_daily_premarket_brief`
- `markets_weekly_picks_digest`
- `markets_monthly_portfolio_review`

## Practical note

This subsystem is closer to an agent-driven operating workflow than a full brokerage engine. The tables are in place, the scheduler hooks exist, and the project-level skill files are rich, but some live market data integrations are still prompt/tool driven rather than directly coded.

## Related Documentation

- [Markets agent](../agents/markets.md)
- [Scheduler API](../api/scheduler.md)
- [Reports API](../api/reports.md)

## Source References

- `README.md`
- `.agents/agentharness/app/v3/hub_db.py`
- `.agents/agentharness/app/v3/hub_scheduler.py`
- `.agents/agents/projects/markets/markets-project-lead.md`

## Implementation Checklist

- Confirm `markets trading` responses use ISO 8601 UTC timestamps.
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

- `markets trading` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
