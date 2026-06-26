# Alpaca Trading Integration

_Updated on 2026-06-25._

## Overview

ArchonHub now includes a full Alpaca Markets integration for the Legacy Alpha Capital AI markets team. The integration adds authenticated FastAPI endpoints, a lazy-initialized `alpaca-py` client wrapper, a web trading console, and a local `alpaca_orders` audit trail.

## Setup

Add these values to `.agents/.env`:

```env
ALPACA_API_KEY=
ALPACA_API_SECRET=
ALPACA_PAPER=true
```

- `ALPACA_PAPER=true` keeps the system on `paper-api.alpaca.markets`.
- Set `ALPACA_PAPER=false` only when the team is ready for live brokerage execution.
- If credentials are missing, `/api/alpaca/status` reports that the integration is not configured and the UI stays read-only.

## Architecture

- `core/alpaca_client.py` — singleton wrapper around `alpaca-py`
- `routers/alpaca.py` — authenticated REST API under `/api/alpaca/*`
- `core/database.py` — `alpaca_orders` audit table plus Alpaca sync schema updates
- `web/index.html` — Alpaca Trading control surface for account, clock, positions, and orders

## API Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/alpaca/status` | Health/config check (no auth) |
| GET | `/api/alpaca/account` | Account balances, buying power, portfolio value |
| GET | `/api/alpaca/positions` | Open Alpaca positions |
| GET | `/api/alpaca/positions/{symbol}` | Single open position |
| GET | `/api/alpaca/orders` | Open/closed order list |
| POST | `/api/alpaca/orders` | Submit order |
| DELETE | `/api/alpaca/orders/{order_id}` | Cancel one order |
| DELETE | `/api/alpaca/orders` | Cancel all open orders |
| GET | `/api/alpaca/portfolio/history` | Portfolio P&L history |
| GET | `/api/alpaca/assets/{symbol}` | Asset details |
| GET | `/api/alpaca/quotes/{symbol}` | Latest bid/ask quote |
| GET | `/api/alpaca/bars/{symbol}` | Historical bars |
| GET | `/api/alpaca/clock` | Market open/close state |
| GET | `/api/alpaca/calendar` | Trading calendar |
| POST | `/api/alpaca/sync-positions` | Mirror Alpaca positions into local `market_positions` |

## Order Workflow

1. Intelligence Desk identifies the catalyst.
2. Quant validates probability and structure.
3. CRO reviews risk, size, and stop-loss discipline.
4. Execution submits `POST /api/alpaca/orders`.
5. The order is written into local `alpaca_orders` with `agent_reason`, submitter, timestamps, and raw Alpaca response JSON.

## Operational Rules

- Always check `GET /api/alpaca/clock` before approving or sending an order.
- Default to paper trading for testing and model validation.
- Preserve the `agent_reason` field for every broker submission so the markets team has an audit trail.
- Use `/api/alpaca/sync-positions` to align local dashboards with brokerage truth.

## Paper vs Live

| Mode | Setting | Use |
| --- | --- | --- |
| Paper | `ALPACA_PAPER=true` | Safe testing, dry runs, strategy validation |
| Live | `ALPACA_PAPER=false` | Real execution after CRO approval |

## Error Handling

- Missing `alpaca-py` returns `503`.
- Missing Alpaca credentials returns `422`.
- Alpaca API and validation errors return `400` with the broker/client message in `detail`.

## Related Files

- `.agents/agentharness/app/v3/core/alpaca_client.py`
- `.agents/agentharness/app/v3/routers/alpaca.py`
- `.agents/agentharness/app/v3/core/database.py`
- `.agents/agentharness/app/v3/web/index.html`
- `.agents/agents/projects/markets/markets-project-lead.md`
- `.agents/agents/projects/markets/markets-cro.md`
