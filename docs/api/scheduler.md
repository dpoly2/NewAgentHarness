# Scheduler API

_Generated from the current ArchonHub source tree on 2026-06-25._

## Overview

Scheduler routes let the UI and administrators inspect persisted schedules, create cron/interval jobs, delete them, and trigger them manually. Built-in jobs run in `America/Chicago` and now include the Tactical Alpha Market Intelligence Division V2 automation stack plus Capitol Trades refresh/digest jobs.

## Authentication and Response Rules

- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.

## Endpoint Index

| Method | Path | Handler | Auth | Source File |
| --- | --- | --- | --- | --- |
| GET | /api/scheduler | list_scheduler | Bearer JWT | .agents/agentharness/app/v3/routers/scheduler.py |
| POST | /api/scheduler | create_scheduler_job | Bearer JWT | .agents/agentharness/app/v3/routers/scheduler.py |
| DELETE | /api/scheduler/{id} | delete_scheduler_job | Bearer JWT | .agents/agentharness/app/v3/routers/scheduler.py |
| POST | /api/scheduler/{id}/trigger | trigger_scheduler_job | Bearer JWT | .agents/agentharness/app/v3/routers/scheduler.py |

## Detailed Endpoints

### GET `/api/scheduler`

- **Handler:** `list_scheduler`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/scheduler.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Lists persisted scheduler rows and/or in-memory job details.

### POST `/api/scheduler`

- **Handler:** `create_scheduler_job`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/scheduler.py`

#### Request Body

| Field | Type | Default / Rule |
| --- | --- | --- |
| agent_id | str | required |
| project | str | required |
| graph | str | `"reflexion"` |
| task | str | required |
| run_type | str | `"cron"` |
| cron_expr | str | `""` |
| interval_sec | int | `0` |

#### Response Schema

- Creates a cron or interval job from `SchedulerJobCreate`.

### DELETE `/api/scheduler/{id}`

- **Handler:** `delete_scheduler_job`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/scheduler.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Deletes a scheduled job.

### POST `/api/scheduler/{id}/trigger`

- **Handler:** `trigger_scheduler_job`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/scheduler.py`

#### Request Body

No JSON body; use query/path parameters only.

#### Response Schema

- Manually triggers a scheduled job immediately.

## Built-in Jobs

All times are Central Time (`America/Chicago`).

### System & Maintenance

| Job ID | Schedule | Purpose |
| --- | --- | --- |
| `daily_briefing` | Daily 6:50 AM | Compute morning briefing |
| `daily_reflexion` | Daily 7:00 AM | Generate daily reflexion report |
| `nightly_db_cleanup` | Daily 2:00 AM | Remove runs older than 90 days |
| `nightly_db_backup` | Daily 3:00 AM | Export critical tables to JSON backup |
| `sync_free_llm_keys` | Daily 7:15 AM | Fetch and activate free daily LLM API keys |

### Markets V2 Morning Pipeline

| Job ID | Schedule | Purpose |
| --- | --- | --- |
| `markets_v2_overnight_macro` | Mon-Fri 5:30 AM | Overnight macro intelligence sweep |
| `markets_v2_news_intelligence` | Mon-Fri 5:45 AM | Pre-market news and catalyst scan |
| `markets_v2_sentiment_scan` | Mon-Fri 6:00 AM | Pre-market sentiment assessment |
| `markets_v2_whale_activity` | Mon-Fri 6:15 AM | Institutional activity pre-market scan |
| `markets_v2_insider_scan` | Mon-Fri 6:30 AM | SEC Form 4 insider transaction review |
| `markets_v2_regime_assessment` | Mon-Fri 6:45 AM | Daily market regime classification |
| `markets_v2_options_flow` | Mon-Fri 7:00 AM | Pre-market options flow and wheel candidates |
| `markets_v2_watchlist_generation` | Mon-Fri 7:30 AM | Daily watchlist synthesis from all agents |
| `markets_v2_probability_scan` | Mon-Fri 8:00 AM | Pre-market probability scoring per setup |
| `markets_v2_executive_briefing` | Mon-Fri 8:15 AM | Morning executive briefing via Inez |

### Markets V2 Hourly

| Job ID | Schedule | Purpose |
| --- | --- | --- |
| `markets_v2_hourly_position_review` | Mon-Fri 10:00 AM-3:00 PM hourly | Hourly position P&L and stop review |
| `markets_v2_hourly_trailing_stops` | Mon-Fri 10:15 AM-3:15 PM hourly | Hourly trailing stop adjustments |
| `markets_v2_hourly_news_refresh` | Mon-Fri 10:30 AM-3:30 PM hourly | Hourly intraday news and catalyst refresh |

### Markets V2 End of Day

| Job ID | Schedule | Purpose |
| --- | --- | --- |
| `markets_v2_eod_performance` | Mon-Fri 4:00 PM | End-of-day performance metrics |
| `markets_v2_eod_risk_assessment` | Mon-Fri 4:15 PM | End-of-day CRO risk review |
| `markets_v2_eod_journal` | Mon-Fri 4:30 PM | End-of-day trading journal |
| `markets_v2_eod_next_day_plan` | Mon-Fri 4:45 PM | End-of-day next-day planning |

### Markets V2 Weekly

| Job ID | Schedule | Purpose |
| --- | --- | --- |
| `markets_v2_weekly_portfolio_review` | Monday 9:30 AM | Weekly portfolio allocation review |
| `markets_v2_weekly_strategy_optimization` | Monday 10:00 AM | Weekly strategy backtesting update |
| `markets_v2_weekly_marketing_content` | Monday 10:30 AM | Weekly educational content creation |
| `markets_v2_weekly_performance_report` | Monday 11:00 AM | Weekly performance recap and community report |

### Markets V2 Monthly

| Job ID | Schedule | Purpose |
| --- | --- | --- |
| `markets_v2_monthly_backtest_update` | 1st Monday 7:30 AM | Monthly comprehensive backtest update |
| `markets_v2_monthly_strategy_tuning` | 1st Monday 8:00 AM | Monthly strategy parameter optimization |
| `markets_v2_monthly_rebalance` | 1st Monday 10:00 AM | Monthly portfolio rebalancing |
| `markets_v2_monthly_curriculum_refresh` | 1st Monday 11:00 AM | Monthly educational curriculum update |

### Capitol Trades Automation

| Job ID | Schedule | Purpose |
| --- | --- | --- |
| `capitol_trades_daily_refresh` | Mon-Fri 9:00 AM | Refresh politician trade disclosures |
| `capitol_trades_signal_digest` | Mon-Fri 9:30 AM | Congress Edge signal digest for CRO |

### Other Projects

| Job ID | Schedule | Purpose |
| --- | --- | --- |
| `grant_research_sweep` | Monday 8:00 AM | Grant research across 4 orgs |
| `hutto_planning_monitor` | Monday 8:30 AM | Hutto city planning monitor |
| `weekly_fare_alert` | Monday 1:30 PM | Travel fare alerts from AUS |
| `sigma_signal_check` | Daily 2:00 PM | Sigma Signal inbox check |
| `markets_daily_premarket_brief` | Mon-Fri 8:30 AM | Legacy V2 pre-market intelligence brief |
| `markets_weekly_picks_digest` | Monday 7:00 AM | Legacy V2 weekly actionable picks digest |
| `markets_monthly_portfolio_review` | 1st Monday 9:00 AM | Legacy V2 monthly portfolio review |

## Error Handling

- `400` indicates validation or bad input.
- `401` indicates a missing or invalid JWT.
- `403` indicates the caller is authenticated but lacks the required role, usually admin-only surfaces.
- `404` indicates the resource identifier does not exist.
- `500` indicates an unhandled subsystem error such as missing optional dependencies, database failures, or third-party API failures.

## Related Documentation

- [Morning briefing feature](../features/morning-briefing.md)
- [Markets and trading](../features/markets-trading.md)
- [Market operations center](../architecture/market-operations-center.md)
