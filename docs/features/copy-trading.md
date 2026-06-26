# Politician Copy Trading

_Updated on 2026-06-25._

## Overview

ArchonHub now includes a politician copy-trading workflow for the markets team. Users track specific lawmakers with a mandatory thesis, ingest public STOCK Act disclosures, generate copy-trade signals, route them to CRO review, and optionally execute approved orders through Alpaca.

## STOCK Act Background

Members of Congress must disclose covered securities trades under the STOCK Act, typically within 45 days. This feature turns those delayed disclosures into a structured monitoring and review workflow rather than a blind auto-trading system.

## Setup

1. Open the **Copy Trading** tab in the web UI.
2. Add a politician name, chamber, and a required **tracking reason** explaining why the markets team wants to copy them.
3. Optionally capture party and state metadata.
4. Save the politician to trigger an immediate disclosure refresh.

Example tracking reason:

> Consistent tech sector timing, historically outperforms S&P by 18% on NVDA and AMD positions.

## Signal Flow

1. `POST /api/capitol-trades/politicians` stores the tracked politician and required reason.
2. `core/capitol_trades_client.py` fetches House + Senate trade disclosures from free public APIs.
3. New disclosures are normalized into `politician_trades`.
4. Recent valid trades create `copy_trade_signals` with a generated `copy_reason` combining:
   - why the politician is tracked
   - the trade side, ticker, asset name, amount range, and dates
5. Pending signals wait for CRO review before any broker execution occurs.

## CRO Approval

CRO reviews pending signals at `GET /api/capitol-trades/signals?status=pending`.

Approval workflow:
- Read `copy_reason` first
- Check Alpaca account status and buying power
- Verify the ticker and market clock
- Size the trade conservatively
- Approve or reject with notes

Approval endpoint:

```json
POST /api/capitol-trades/signals/{id}/review
{
  "action": "approve",
  "qty": 5,
  "cro_notes": "Valid signal, size capped"
}
```

Rejection endpoint:

```json
POST /api/capitol-trades/signals/{id}/review
{
  "action": "reject",
  "cro_notes": "Ticker too illiquid"
}
```

## Alpaca Execution

Approved signals call `core.alpaca_client.place_order()` and persist the resulting order ID in both `copy_trade_signals` and `alpaca_orders`. If CRO does not specify quantity, the system sizes automatically from the disclosed amount midpoint, capped at a default $5,000 notional.

## Performance Tracking

Tracked politicians store:
- total signals
- approved signals
- profitable signals
- aggregate return estimate

The leaderboard ranks politicians by win rate (`profitable_signals / approved_signals`) and total return estimate.

## Data Sources

- House disclosures: `https://housestockwatcher.com/api`
- Senate disclosures: `https://senatestockwatcher.com/api`

Both sources are free and do not require API keys.

## API Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/capitol-trades/status` | Public source/alpaca health check |
| GET | `/api/capitol-trades/politicians` | List tracked politicians |
| POST | `/api/capitol-trades/politicians` | Add tracked politician with required reason |
| GET | `/api/capitol-trades/politicians/{id}` | Single politician stats |
| PATCH | `/api/capitol-trades/politicians/{id}` | Update reason / performance note / active flag |
| DELETE | `/api/capitol-trades/politicians/{id}` | Soft delete tracked politician |
| GET | `/api/capitol-trades/politicians/{id}/trades` | Politician trade history |
| GET | `/api/capitol-trades/politicians/{id}/signals` | Politician signal history |
| POST | `/api/capitol-trades/politicians/{id}/refresh` | Pull latest disclosures for one politician |
| GET | `/api/capitol-trades/trades` | Cross-politician trade feed |
| GET | `/api/capitol-trades/signals` | Signal queue / execution feed |
| POST | `/api/capitol-trades/signals/{id}/review` | CRO approve or reject a signal |
| POST | `/api/capitol-trades/refresh-all` | Refresh all active politicians |
| GET | `/api/capitol-trades/leaderboard` | Win-rate / return leaderboard |

## Related Files

- `.agents/agentharness/app/v3/core/capitol_trades_client.py`
- `.agents/agentharness/app/v3/routers/capitol_trades.py`
- `.agents/agentharness/app/v3/core/database.py`
- `.agents/agentharness/app/v3/web/index.html`
- `.agents/agents/projects/markets/markets-intelligence-desk.md`
- `.agents/agents/projects/markets/markets-cro.md`
