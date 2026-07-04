# 06-SCHEDULER-OPERATIONS

_Generated from the current ArchonHub source tree on 2026-07-03._

## Ownership model

ArchonHub treats APScheduler as a **single-leader** service even though multiple server processes may be running.

- Lease TTL: **30 seconds**
- Renew interval: **10 seconds**
- Safety belt: `_make_tracked()` re-checks leadership before each job fires, so a brief handover window should not double-run jobs.
- Timezone: **America/Chicago**

## Job classes

1. **Built-in jobs** are declared in `_JOB_SPECS` and are automatically registered.
2. **User-defined jobs** are read from `scheduled_jobs` at startup and exposed via `/api/scheduler`.
3. **Immediate/manual runs** can be triggered through HTTP without waiting for the next cron tick.

## Built-in cadence from `_JOB_SPECS`

| Job id | Cadence |
| --- | --- |
| `log_monitor` | every 15 minutes |
| `daily_briefing` | 06:50 CT daily |
| `daily_reflexion` | 07:00 CT daily |
| `grant_research_sweep` | Monday 08:00 CT |
| `hutto_planning_monitor` | Monday 08:30 CT |
| `weekly_fare_alert` | Monday 13:30 CT |
| `sigma_signal_check` | daily 14:00 CT |
| `markets_daily_premarket_brief` | Mon-Fri 08:30 CT |
| `markets_weekly_picks_digest` | Monday 07:00 CT |
| `markets_monthly_portfolio_review` | first Monday window at 09:00 CT |
| `markets_v2_morning_pipeline` | Mon-Fri 05:30-08:15 CT sequence |
| `markets_v2_hourly_monitoring` | Mon-Fri 10:00/10:15/10:30 through 15:30 CT |
| `markets_v2_eod` | Mon-Fri 16:00/16:15/16:30/16:45 CT |
| `markets_v2_weekly_monday` | Monday 09:30/10:00/10:30/11:00 CT |
| `markets_v2_monthly_first_monday` | first Monday 07:30/08:00/10:00/11:00 CT |
| `capitol_trades_daily_refresh` | Mon-Fri 09:00 CT |
| `capitol_trades_signal_digest` | Mon-Fri 09:30 CT |
| `nightly_db_cleanup` | 02:00 CT daily |
| `nightly_db_backup` | 03:00 CT daily |
| `sync_free_llm_keys` | 07:15 CT daily |

## Operational consequences

- The scheduler is not just a generic cron wrapper; it is a portfolio operating cadence spanning market intelligence, Capitol Trades ingestion, daily briefing/reflexion, backups, and grant/travel sweeps.
- Because scheduler leadership is lease-based, losing one Uvicorn worker does not require a full server restart; another worker can acquire the lease.
- Each tracked job records run metadata back to the DB through the `record_job_run()` path so operators can inspect last-run state.

## HTTP management surface

- `GET /api/scheduler`: inspect configured jobs
- `POST /api/scheduler`: create a user-defined scheduled job
- `DELETE /api/scheduler/{id}`: remove a scheduled job
- `POST /api/scheduler/{id}/trigger`: fire a scheduled job immediately

## Source references

- `.agents\agentharness\app\v3\hub_scheduler.py`
- `.agents\agentharness\app\v3\core\hub.py`
