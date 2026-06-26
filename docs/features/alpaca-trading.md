# Alpaca Trading Integration

_Updated on 2026-06-25. Live credentials configured and verified._

## Overview

ArchonHub includes a full Alpaca Markets brokerage integration for the Legacy Alpha Capital AI markets team. The integration provides a `core/alpaca_client.py` SDK wrapper, 15 authenticated FastAPI endpoints, a local `alpaca_orders` audit trail, a complete webapp trading console, and a desktop Alpaca sub-tab inside the Markets panel.

## Live Paper Account

| Field | Value |
|-------|-------|
| Account number | PA3O44BTG1MG |
| Status | ACTIVE |
| Mode | Paper (`paper-api.alpaca.markets/v2`) |
| Starting equity | $100.00 |
| Starting buying power | $100.00 |

## Setup

Required values in `.agents/.env`:

```env
ALPACA_API_KEY=<your-key>
ALPACA_API_SECRET=<your-secret>
ALPACA_BASE_URL=https://paper-api.alpaca.markets/v2
ALPACA_PAPER=true
```

- `ALPACA_PAPER=true` keeps all traffic on `paper-api.alpaca.markets`. Set to `false` only after CRO approval for live execution.
- `ALPACA_BASE_URL` — override the base URL if pointing to a different environment.
- If credentials are missing, `GET /api/alpaca/status` returns `{"configured": false}` and the UI stays read-only.

## Dependency

```
alpaca-py>=0.43.0
```

Install with `pip install alpaca-py`. Confirmed working at `0.43.4`.

## Architecture

```
.env (ALPACA_API_KEY / ALPACA_API_SECRET / ALPACA_BASE_URL)
  → core/alpaca_client.py       lazy-initialized TradingClient + StockHistoricalDataClient
  → routers/alpaca.py           15 REST endpoints under /api/alpaca/*
  → core/database.py            alpaca_orders audit table
```

## Client Surfaces

| Surface | Status | Features |
|---------|--------|---------|
| **Webapp** (`showAlpaca()`) | ✅ Fully implemented | Account summary (4 KPI cards), market clock, positions table, open orders + cancel, quick order form (all types), sync to local market_positions, 30s auto-refresh |
| **Desktop** (Markets → Alpaca tab) | ⏳ Planned | Account summary, positions treeview, orders treeview, quick order form |
| **iOS** | Planned | Account/positions via HubClient |

## API Endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/api/alpaca/status` | Public | Config/install check — returns `{configured, paper, alpaca_ok}` |
| GET | `/api/alpaca/account` | Bearer JWT | Account balances, equity, buying power, cash, status |
| GET | `/api/alpaca/positions` | Bearer JWT | All open positions |
| GET | `/api/alpaca/positions/{symbol}` | Bearer JWT | Single open position by symbol |
| GET | `/api/alpaca/orders?status=open&limit=50` | Bearer JWT | Orders list (status: open/closed/all) |
| POST | `/api/alpaca/orders` | Bearer JWT | Submit order (market/limit/stop/stop_limit) |
| DELETE | `/api/alpaca/orders/{order_id}` | Bearer JWT | Cancel one order |
| DELETE | `/api/alpaca/orders` | Bearer JWT | Cancel all open orders |
| GET | `/api/alpaca/portfolio/history?period=1W&timeframe=1D` | Bearer JWT | Portfolio equity history |
| GET | `/api/alpaca/assets/{symbol}` | Bearer JWT | Asset details (tradable, fractionable, etc.) |
| GET | `/api/alpaca/quotes/{symbol}` | Bearer JWT | Latest bid/ask quote |
| GET | `/api/alpaca/bars/{symbol}?timeframe=1D&limit=30` | Bearer JWT | Historical OHLCV bars |
| GET | `/api/alpaca/clock` | Bearer JWT | Market open/close state, next open, next close |
| GET | `/api/alpaca/calendar?start=&end=` | Bearer JWT | Trading calendar (market days) |
| POST | `/api/alpaca/sync-positions` | Bearer JWT | Mirror live Alpaca positions → local `market_positions` table |

## Order Request Schema (`POST /api/alpaca/orders`)

```json
{
  "symbol": "AAPL",
  "qty": 1.0,
  "side": "buy",
  "order_type": "market",
  "time_in_force": "day",
  "limit_price": null,
  "stop_price": null,
  "extended_hours": false,
  "client_order_id": null,
  "order_class": "simple",
  "agent_reason": "Markets quant signal: iron condor hedge"
}
```

Valid values:
- `side`: `buy`, `sell`
- `order_type`: `market`, `limit`, `stop`, `stop_limit`
- `time_in_force`: `day`, `gtc`, `ioc`, `fok`

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
