"""
hub_scheduler.py — ArchonHub APScheduler engine
Timezone: America/Chicago

Job registration:
  All built-in jobs are defined in _JOB_SPECS (a module-level dict defined after the
  job functions). BUILT_IN_JOB_IDS is derived from _JOB_SPECS — they cannot diverge.
  To add a new built-in job:
    1. Define the async job function (job_<name>(hub) pattern)
    2. Add an entry to _JOB_SPECS
  That's it — BUILT_IN_JOB_IDS updates automatically.

User-defined jobs (created via POST /api/scheduler) are loaded from the DB on startup
and registered via HubScheduler.add_user_job().
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except Exception:
    AsyncIOScheduler = None

try:
    from apscheduler.triggers.cron import CronTrigger
except Exception:
    CronTrigger = None

try:
    from apscheduler.triggers.interval import IntervalTrigger
except Exception:
    IntervalTrigger = None

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

try:
    import pytz
except Exception:
    pytz = None

try:
    from hub_db import save_notification, list_scheduled_jobs, update_scheduled_job, record_job_run
except Exception:
    save_notification = None
    list_scheduled_jobs = None
    update_scheduled_job = None
    record_job_run = None

try:
    from ah_logging import get_logger
except Exception:
    import logging

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(f"archonhub.{name}")

TIMEZONE_NAME = "America/Chicago"
SCHEDULE_FIELD_NAMES = {
    "id",
    "name",
    "cron_expr",
    "interval_sec",
    "run_type",
    "scheduled_at",
    "next_fire",
    "status",
    "created_at",
    "updated_at",
    "job_data",
    "year",
    "month",
    "day",
    "week",
    "day_of_week",
    "hour",
    "minute",
    "second",
}
# _JOB_SPECS and BUILT_IN_JOB_IDS are defined after the job functions (below _run_user_job)


def _get_timezone() -> Any:
    if ZoneInfo is not None:
        try:
            return ZoneInfo(TIMEZONE_NAME)
        except Exception:
            pass
    if pytz is not None:
        try:
            return pytz.timezone(TIMEZONE_NAME)
        except Exception:
            pass
    return None


def _now_in_timezone() -> datetime:
    tz = _get_timezone()
    if tz is not None:
        return datetime.now(tz)
    return datetime.now()


def _serialize_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _notify(message: str, logger) -> None:
    if callable(save_notification):
        try:
            save_notification(message)
        except Exception:
            logger.exception("Failed saving notification: %s", message)
    logger.info(message)


def _update_job_state(job_id: str, logger, **fields: Any) -> None:
    if not callable(update_scheduled_job):
        return

    attempts = (
        lambda: update_scheduled_job(job_id, fields),
        lambda: update_scheduled_job(job_id, **fields),
        lambda: update_scheduled_job({"id": job_id, **fields}),
    )
    for attempt in attempts:
        try:
            attempt()
            return
        except TypeError:
            continue
        except Exception:
            logger.exception("Failed updating scheduled job state for %s", job_id)
            return


def _is_scheduler_leader() -> bool:
    """Best-effort check of whether this worker owns the scheduler lease.

    Lazily imports the hub singleton to avoid a circular import (core.hub imports
    this module). Defaults to True if the hub can't be resolved so we never silently
    stop firing jobs in a degraded/standalone setup.
    """
    try:
        from core.hub import hub as _hub
    except Exception:
        return True
    checker = getattr(_hub, "is_scheduler_leader", None)
    if callable(checker):
        try:
            return bool(checker())
        except Exception:
            return True
    return bool(getattr(_hub, "_is_scheduler_leader", True))


def _make_tracked(func, job_id: str):
    """Wrap a job coroutine to record last_run_at, last_run_status, run_count in DB.

    Also enforces single-owner scheduling: if this worker is not the current
    scheduler leader, the job is skipped (no-op). This is a belt-and-suspenders
    guard on top of only starting APScheduler in the leader — it prevents a
    duplicate fire during a brief lease handover window.
    """
    import functools

    @functools.wraps(func)
    async def _wrapper(*args, **kwargs):
        if not _is_scheduler_leader():
            logger = get_logger("scheduler")
            logger.debug("Skipping scheduled job %s — not scheduler leader", job_id)
            return
        status = "success"
        try:
            await func(*args, **kwargs)
        except Exception:
            status = "error"
            raise
        finally:
            if callable(record_job_run):
                try:
                    record_job_run(job_id, status)
                except Exception:
                    pass

    return _wrapper


async def _submit_via_hub(hub, config: dict, logger, notification_text: str | None = None) -> bool:
    if hub is None or not hasattr(hub, "submit_job"):
        logger.warning("Hub unavailable; skipped scheduled job for %s", config.get("agent_id", "unknown-agent"))
        return False

    try:
        await hub.submit_job(config)
    except Exception:
        logger.exception("Scheduled job submission failed for %s", config.get("agent_id", "unknown-agent"))
        return False

    if notification_text:
        _notify(notification_text, logger)
    return True


async def job_daily_briefing_compute(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "inez-chief-of-staff",
        "project": "archonhub",
        "graph": "reflexion",
        "task": "Generate a comprehensive daily briefing covering all portfolio projects, pending todos, active runs, and key priorities for today.",
    }
    await _submit_via_hub(hub, config, logger, "Daily briefing computed")
    try:
        from report_monitor import run_report_job
        await run_report_job("daily_briefing")
    except Exception:
        logger.exception("Daily briefing report generation failed")


async def job_daily_reflexion_report(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "finance-cfo",
        "project": "smithcap-finance",
        "graph": "reflexion",
        "task": "Generate daily reflexion report: review yesterday's agent runs, identify patterns, flag issues, suggest improvements.",
    }
    await _submit_via_hub(hub, config, logger, "Daily reflexion report queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("daily_reflexion")
    except Exception:
        logger.exception("Daily reflexion report generation failed")


async def job_grant_research_sweep(hub):
    logger = get_logger("scheduler")
    configs = [
        {
            "agent_id": "grants-research-agent",
            "project": "grants",
            "graph": "research",
            "task": "Weekly grant research sweep: find new grant opportunities, deadlines, and funding sources relevant to grants.",
        },
        {
            "agent_id": "yepc-grant-writer-agent",
            "project": "yepc",
            "graph": "research",
            "task": "Weekly grant research sweep: find new grant opportunities, deadlines, and funding sources relevant to yepc.",
        },
        {
            "agent_id": "pbs-fundraising-agent",
            "project": "pbs-foundation",
            "graph": "research",
            "task": "Weekly grant research sweep: find new grant opportunities, deadlines, and funding sources relevant to pbs-foundation.",
        },
        {
            "agent_id": "solar-marketing-agent",
            "project": "solar-repair",
            "graph": "research",
            "task": "Weekly grant research sweep: find new grant opportunities, deadlines, and funding sources relevant to solar-repair.",
        },
    ]

    submitted = 0
    for config in configs:
        if await _submit_via_hub(hub, config, logger):
            submitted += 1

    if submitted:
        _notify("Grant research sweep queued (4 agents)", logger)
    try:
        from report_monitor import run_report_job
        await run_report_job("grant_research_sweep")
    except Exception:
        logger.exception("Grant research report generation failed")


async def job_hutto_planning_monitor(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "yepc-project-manager",
        "project": "yepc",
        "graph": "research",
        "task": "Monitor Hutto TX city and county planning commission agendas, new developments, zoning changes, and real estate opportunities relevant to YEPC mission.",
    }
    await _submit_via_hub(hub, config, logger, "Hutto planning monitor queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("hutto_planning_monitor")
    except Exception:
        logger.exception("Hutto planning report generation failed")


async def job_weekly_fare_alert(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "travel-flights-agent",
        "project": "travel",
        "graph": "research",
        "task": "Research current travel fare deals from Austin-Bergstrom (AUS) airport. Find best deals for upcoming 60 days. Include airlines, prices, and booking links.",
    }
    await _submit_via_hub(hub, config, logger, "Weekly fare alert queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("weekly_fare_alert")
    except Exception:
        logger.exception("Fare alert report generation failed")


async def job_sigma_signal_check(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "sigma-signal-writer",
        "project": "sigma-signal",
        "graph": "reflexion",
        "task": "Check and process Sigma Signal newsletter submission inbox. Review pending submissions, draft responses, prepare content pipeline update.",
    }
    await _submit_via_hub(hub, config, logger, "Sigma Signal check queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("sigma_signal_check")
    except Exception:
        logger.exception("Sigma Signal report generation failed")


async def job_nightly_db_cleanup(hub):
    logger = get_logger("scheduler")
    deleted = 0
    try:
        from hub_db import get_db

        cutoff = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=90)).isoformat()
        conn = get_db()
        try:
            cur = conn.execute("DELETE FROM runs WHERE created_at < ?", (cutoff,))
            conn.commit()
            deleted = cur.rowcount or 0
        finally:
            conn.close()
    except Exception:
        logger.exception("Nightly DB cleanup failed")
    _notify("Nightly DB cleanup completed", logger)
    logger.info("Nightly DB cleanup removed %s runs older than 90 days", deleted)


async def job_nightly_db_backup(hub):
    logger = get_logger("scheduler")
    try:
        from hub_backup import backup_all
        backup_all()
        _notify("Nightly DB backup completed", logger)
    except Exception:
        logger.exception("Nightly DB backup failed")


async def job_markets_daily_premarket_brief(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-tactical-alpha",
        "project": "markets",
        "graph": "research",
        "task": "V2 Pre-Market Intelligence Briefing: Synthesize overnight macro (macro-analyst), news catalysts (news-intelligence), sentiment scores (sentiment-intelligence), whale activity (whale-tracker), regime classification (regime-engine). Produce unified pre-market brief with top 5 watchlist, key levels, risk-on/off bias, and confidence score. Deliver to Inez for executive summary.",
    }
    await _submit_via_hub(hub, config, logger, "Markets pre-market brief queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("markets_daily_premarket_brief")
    except Exception:
        logger.exception("Markets pre-market report generation failed")


async def job_markets_weekly_picks_digest(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-tactical-alpha",
        "project": "markets",
        "graph": "research",
        "task": "V2 Weekly Market Intelligence Digest: Coordinate all 9 departments. Compile top 3-5 high-conviction setups validated by probability-engine and approved by cro. Include options wheel candidates, swing setups, dividend picks. Attach backtesting summary for each setup. Produce executive digest for David via Inez.",
    }
    await _submit_via_hub(hub, config, logger, "Markets weekly picks digest queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("markets_weekly_picks_digest")
    except Exception:
        logger.exception("Markets weekly picks report generation failed")


async def job_markets_monthly_portfolio_review(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-cio",
        "project": "markets",
        "graph": "reflexion",
        "task": "V2 Monthly Portfolio Review: Full portfolio health assessment — allocation vs targets (portfolio-optimizer), position P&L (position-manager), strategy performance vs backtest (backtesting-engine), risk metrics (cro), regime alignment (regime-engine). Produce rebalancing recommendations and next-month strategy plan.",
    }
    await _submit_via_hub(hub, config, logger, "Markets monthly portfolio review queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("markets_monthly_portfolio_review")
    except Exception:
        logger.exception("Markets monthly portfolio review generation failed")


# ── V2 Market Morning Pipeline ─────────────────────────────────────────────

async def job_markets_v2_overnight_macro(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-macro-analyst",
        "project": "markets",
        "graph": "research",
        "task": "Overnight macro intelligence sweep: Federal Reserve posture, overnight futures moves, international markets, treasury yields, DXY, oil, gold. Classify macro environment as Risk-On or Risk-Off. Output Macro Score (0-100) and key overnight developments. This feeds the morning pipeline.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 overnight macro queued")


async def job_markets_v2_news_intelligence(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-news-intelligence",
        "project": "markets",
        "graph": "research",
        "task": "Pre-market news intelligence scan: Breaking news, SEC filings, FDA decisions, earnings beats/misses, M&A announcements, analyst upgrades/downgrades, geopolitical events. Score each catalyst (0-100) and list affected tickers. Flag URGENT items needing immediate attention.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 news intelligence queued")


async def job_markets_v2_sentiment_scan(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-sentiment-intelligence",
        "project": "markets",
        "graph": "research",
        "task": "Pre-market sentiment assessment: Fear & Greed Index, VIX level and trend, put/call ratio, social sentiment, news sentiment. Classify overall market sentiment (bearish/neutral/bullish). Output Market Sentiment Score and key sentiment drivers.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 sentiment scan queued")


async def job_markets_v2_whale_activity(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-whale-tracker",
        "project": "markets",
        "graph": "research",
        "task": "Pre-market institutional activity scan: Review publicly available dark pool prints, large block trades, ETF fund flows, options sweeps, gamma exposure changes. Output Institutional Confidence Score and top institutional conviction tickers. Note: based on publicly disclosed data only.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 whale activity queued")


async def job_markets_v2_insider_scan(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-insider-tracker",
        "project": "markets",
        "graph": "research",
        "task": "Pre-market insider transaction review: Review recent SEC Form 4 filings. Flag CEO, Director, CFO purchases above $100k. Note repeat insider accumulation patterns. Output Insider Conviction Score per ticker. Reminder: filings have 2-business-day lag.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 insider scan queued")


async def job_markets_v2_regime_assessment(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-regime-engine",
        "project": "markets",
        "graph": "research",
        "task": "Daily market regime classification: Synthesize macro score, sentiment score, technical structure, and volatility. Classify regime as: Bull / Bear / Sideways / High-Volatility / Low-Volatility / Recovery / Correction. Output regime with confidence score and recommended strategy bias for the day. This sets the tone for all other agents.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 regime assessment queued")


async def job_markets_v2_options_flow(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-options-strategist",
        "project": "markets",
        "graph": "research",
        "task": "Pre-market options flow analysis: Review unusual options activity, large call/put sweeps, high-IV candidates for wheel strategy. Identify best CSP candidates (IV rank > 30, strong support). Output options flow summary, top wheel candidates with IV rank and expected premium.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 options flow queued")


async def job_markets_v2_watchlist_generation(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-tactical-alpha",
        "project": "markets",
        "graph": "research",
        "task": "Daily watchlist generation: Synthesize inputs from all morning intelligence agents (macro, news, sentiment, whale, insider, regime, technical, SMC). Build prioritized watchlist of top 5-10 tickers. For each: setup type, entry zone, stop, target, R:R ratio, confidence score, contributing signals. Rank by conviction.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 watchlist generation queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("markets_v2_watchlist_generation")
    except Exception:
        logger.exception("Markets V2 watchlist report generation failed")


async def job_markets_v2_probability_scan(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-probability-engine",
        "project": "markets",
        "graph": "research",
        "task": "Pre-market probability assessment: For each ticker on today's watchlist, calculate probability of success, expected value, historical similarity to current setup, max drawdown estimate. Output confidence band (low/mid/high). Flag any setups with expected value < 1.5:1 for removal from watchlist.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 probability scan queued")


async def job_markets_v2_executive_briefing(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-tactical-alpha",
        "project": "markets",
        "graph": "research",
        "task": "Morning executive briefing for David via Inez: Synthesize full morning pipeline results into a 5-minute briefing. Include: market regime, macro bias (risk-on/off), top 3 watchlist items with setup summaries, pending signals needing review, overnight news catalysts, key risk factors. Keep it sharp and actionable. Inez delivers this at 8:15 AM.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 executive briefing queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("markets_v2_executive_briefing")
    except Exception:
        logger.exception("Markets V2 executive briefing report generation failed")


# ── V2 Market Hourly Jobs ────────────────────────────────────────────────────

async def job_markets_v2_hourly_position_review(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-position-manager",
        "project": "markets",
        "graph": "research",
        "task": "Hourly position review: Check all open positions P&L vs targets and stops. Flag any position approaching stop loss (within 1 ATR). Flag any position hitting profit target. Review trailing stop adjustments needed. Output position summary with action items.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 hourly position review queued")


async def job_markets_v2_hourly_trailing_stops(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-trailing-trade-manager",
        "project": "markets",
        "graph": "research",
        "task": "Hourly trailing stop update: Review all open positions with trailing stops. Recommend trail adjustments based on current price action, ATR changes, and volatility. Flag positions where trail should be tightened or moved to breakeven. Protect any positions up more than 2R.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 hourly trailing stops queued")


async def job_markets_v2_hourly_news_refresh(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-news-intelligence",
        "project": "markets",
        "graph": "research",
        "task": "Hourly news refresh: Scan for breaking news, new SEC filings, intraday catalysts affecting open positions or watchlist tickers. Immediately flag URGENT items (FDA decisions, earnings surprises, major news). Update catalyst scores for affected tickers.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 hourly news refresh queued")


# ── V2 Market End-of-Day Jobs ────────────────────────────────────────────────

async def job_markets_v2_eod_performance(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-performance-analytics",
        "project": "markets",
        "graph": "reflexion",
        "task": "End-of-day performance metrics: Calculate today's P&L across all positions. Update win rate, profit factor, average gain/loss. Compute daily discipline score (did we follow entry/exit rules?). Flag any rule violations. Store metrics for weekly and monthly rollups.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 EOD performance metrics queued")


async def job_markets_v2_eod_risk_assessment(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-cro",
        "project": "markets",
        "graph": "reflexion",
        "task": "End-of-day risk assessment: Review portfolio drawdown, sector concentration, correlation between positions, total market exposure vs cash. Flag any positions exceeding 2% portfolio risk. Recommend position sizing adjustments for tomorrow. Output risk score and red flags.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 EOD risk assessment queued")


async def job_markets_v2_eod_journal(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-tactical-alpha",
        "project": "markets",
        "graph": "reflexion",
        "task": "End-of-day trading journal: Document all trades taken today (entry, exit, reason). Evaluate each trade against the original setup criteria. Note what worked and what didn't. Record emotional discipline observations. Summarize key lessons. This feeds the Personal Trade Coach v3 roadmap.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 EOD journal queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("markets_v2_eod_journal")
    except Exception:
        logger.exception("Markets V2 EOD journal report generation failed")


async def job_markets_v2_eod_next_day_plan(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-tactical-alpha",
        "project": "markets",
        "graph": "research",
        "task": "Next-day trading plan: Based on today's journal, tomorrow's economic calendar, overnight macro setup, and current open positions — build tomorrow's game plan. Key levels to watch, potential setups to monitor, risk events to respect. Keep it to 5 actionable items.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 EOD next-day plan queued")


# ── V2 Market Weekly Jobs ────────────────────────────────────────────────────

async def job_markets_v2_weekly_portfolio_review(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-portfolio-optimizer",
        "project": "markets",
        "graph": "reflexion",
        "task": "Weekly portfolio review: Assess current allocation vs target (core/growth/income/options/cash/speculative). Review sector exposure and correlation. Identify over/under-allocated areas. Produce rebalancing recommendations ranked by priority. Calculate weekly Sharpe and Sortino.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 weekly portfolio review queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("markets_v2_weekly_portfolio_review")
    except Exception:
        logger.exception("Markets V2 weekly portfolio review failed")


async def job_markets_v2_weekly_strategy_optimization(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-backtesting-engine",
        "project": "markets",
        "graph": "research",
        "task": "Weekly strategy optimization: Review last week's backtest data vs live results. Identify strategy drift. Run updated backtests on active strategies with last 4 weeks of data. Flag any strategy with win rate drop > 10% vs historical baseline. Recommend parameter adjustments or strategy retirement.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 weekly strategy optimization queued")


async def job_markets_v2_weekly_marketing_content(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-content-studio",
        "project": "markets",
        "graph": "research",
        "task": "Weekly marketing content plan: Based on this week's best trade setups and market insights, draft 3 educational content pieces (1 LinkedIn post, 1 short-form video script, 1 newsletter section). Frame around education and market awareness — no specific buy/sell recommendations. Include compliance disclaimer in all pieces.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 weekly marketing content queued")


async def job_markets_v2_weekly_performance_report(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-community-manager",
        "project": "markets",
        "graph": "reflexion",
        "task": "Weekly performance report and recap: Produce the weekly market recap covering the week's best setups, what the market did, key lessons, watchlist performance. Create the weekly watchlist summary for community distribution. Include win/loss stats, key takeaways, and next week outlook.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 weekly performance report queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("markets_v2_weekly_performance_report")
    except Exception:
        logger.exception("Markets V2 weekly performance report failed")


# ── V2 Market Monthly Jobs ───────────────────────────────────────────────────

async def job_markets_v2_monthly_backtest_update(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-backtesting-engine",
        "project": "markets",
        "graph": "reflexion",
        "task": "Monthly backtest update: Run comprehensive backtests on all active strategies using full prior month data. Update win rate, profit factor, Sharpe, Sortino, max drawdown for each strategy. Retire any strategy with less than positive expectancy over 30+ sample trades. Add new strategy candidates for next month testing.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 monthly backtest update queued")


async def job_markets_v2_monthly_strategy_tuning(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-quant",
        "project": "markets",
        "graph": "reflexion",
        "task": "Monthly strategy tuning: Analyze full month of market data. Adjust strategy parameters (entry criteria, stop distances, trailing percentages, position sizing) based on volatility regime. Run Monte Carlo simulation on top 3 strategies for next month. Document all changes with reasoning.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 monthly strategy tuning queued")


async def job_markets_v2_monthly_rebalance(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-portfolio-optimizer",
        "project": "markets",
        "graph": "reflexion",
        "task": "Monthly portfolio rebalance: Full portfolio rebalancing review. Compare current vs target allocations. Recommend specific rebalancing trades. Review dividend income received. Update options wheel position cycle status. Confirm cash allocation is within target range. Produce formal rebalance memo for CIO approval.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 monthly portfolio rebalance queued")
    try:
        from report_monitor import run_report_job
        await run_report_job("markets_v2_monthly_rebalance")
    except Exception:
        logger.exception("Markets V2 monthly rebalance failed")


async def job_markets_v2_monthly_curriculum_refresh(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-trading-education",
        "project": "markets",
        "graph": "research",
        "task": "Monthly educational curriculum refresh: Review which trading concepts were most relevant this month. Update beginner/advanced guide content to reflect current market conditions. Draft 1 new lesson based on a key trade or market event from the past month. Review and update the trading glossary with new terms encountered.",
    }
    await _submit_via_hub(hub, config, logger, "Markets V2 monthly curriculum refresh queued")


# ── Capitol Trades Automation ────────────────────────────────────────────────

async def job_capitol_trades_daily_refresh(hub):
    """Refresh politician trade disclosures via the Capitol Trades API."""
    logger = get_logger("scheduler")
    _notify("Capitol Trades: refreshing politician disclosures...", logger)
    try:
        import os as _os
        import httpx
        _hub_host = _os.environ.get("HUB_HOST", "localhost")
        _hub_port = _os.environ.get("HUB_PORT", "8765")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"http://{_hub_host}:{_hub_port}/api/capitol-trades/refresh-all")
            if resp.status_code == 200:
                data = resp.json()
                new_trades = data.get("total_new_trades", 0)
                new_signals = data.get("total_new_signals", 0)
                _notify(f"Capitol Trades: {new_trades} new disclosures, {new_signals} copy signals generated", logger)
            else:
                logger.warning("Capitol Trades refresh returned %s", resp.status_code)
    except Exception:
        logger.exception("Capitol Trades daily refresh failed")


async def job_capitol_trades_signal_digest(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "markets-intelligence-desk",
        "project": "markets",
        "graph": "research",
        "task": "Congress Edge signal digest: Review pending copy trade signals at GET /api/capitol-trades/signals?status=pending. For each signal, summarize the politician's tracking reason, the trade they made, and the copy_reason. Flag strong-conviction signals (signal_strength=strong) to CRO immediately. Produce a ranked signal digest for the markets team.",
    }
    await _submit_via_hub(hub, config, logger, "Capitol Trades signal digest queued")


async def job_sync_free_llm_keys(hub):
    """Fetch and activate free daily LLM API keys from the public key registry."""
    logger = get_logger("scheduler")
    _notify("Free LLM key sync starting...", logger)
    try:
        import asyncio
        from free_llm_keys import sync_free_keys, get_retry_count, increment_retry_count, MAX_RETRIES_PER_DAY
        # Run the sync in a thread pool so it doesn't block the event loop
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, sync_free_keys)
        synced_list = ", ".join(result.get("synced", {}).keys()) or "none"
        _notify(
            f"Free LLM keys synced: {len(result.get('synced', {}))} providers activated ({synced_list})",
            logger,
        )
        # If no providers synced successfully, schedule a retry (max MAX_RETRIES_PER_DAY per day)
        if not result.get("synced") or "error" in result:
            retry_count = get_retry_count()
            if retry_count < MAX_RETRIES_PER_DAY:
                new_count = increment_retry_count()
                logger.warning(
                    "Free LLM key sync yielded 0 providers — scheduling retry %d/%d in 2 hours",
                    new_count, MAX_RETRIES_PER_DAY,
                )
                try:
                    from datetime import datetime, timezone, timedelta
                    from apscheduler.triggers.date import DateTrigger
                    retry_run_time = datetime.now(timezone.utc) + timedelta(hours=2)
                    retry_job_id = f"sync_free_llm_keys_retry_{new_count}"
                    hub_scheduler = getattr(hub, "scheduler", None)
                    if hub_scheduler and hasattr(hub_scheduler, "scheduler"):
                        hub_scheduler.scheduler.add_job(
                            job_sync_free_llm_keys,
                            args=[hub],
                            trigger=DateTrigger(run_date=retry_run_time),
                            id=retry_job_id,
                            name=f"Free LLM Keys Retry #{new_count}",
                            replace_existing=True,
                            max_instances=1,
                        )
                        _notify(
                            f"Free LLM key retry #{new_count} scheduled for {retry_run_time.strftime('%H:%M')} UTC",
                            logger,
                        )
                except Exception as sched_err:
                    logger.warning("Could not schedule free LLM key retry: %s", sched_err)
            else:
                logger.error(
                    "Free LLM key sync failed %d times today — no more retries", retry_count
                )
                _notify(
                    f"⚠️ Free LLM key sync failed {retry_count + 1}x today — all providers remain disabled",
                    logger,
                )
    except Exception:
        logger.exception("Free LLM key sync failed")


async def _run_user_job(hub, job_config: dict):
    logger = get_logger("scheduler")
    submit_config = {k: v for k, v in dict(job_config).items() if k not in SCHEDULE_FIELD_NAMES}
    submit_config.setdefault("project", "archonhub")
    submit_config.setdefault("graph", "reflexion")
    await _submit_via_hub(
        hub,
        submit_config,
        logger,
        f"Scheduled job queued: {job_config.get('name') or job_config.get('id') or submit_config.get('agent_id', 'user-job')}",
    )


# ---------------------------------------------------------------------------
# DevOps log monitor — read NEW error lines from .agents/data/logs/ since the
# last sweep (per-file byte-offset watermark in hub_config) and build a digest.
# ---------------------------------------------------------------------------

_LOG_ERROR_RE = None


def _collect_new_log_errors(max_chars: int = 6000) -> tuple[str, int]:
    """Return (digest, count) of new error lines across the runtime logs.

    Uses a per-file byte offset stored in hub_config (key ``logwm_<name>``) so
    each line is only ever reported once. Handles truncation/rotation by
    resetting the offset when the file shrinks. Returns ("", 0) when quiet so
    the caller can skip dispatching the team (cheap when there are no errors).
    """
    import os
    import re
    from pathlib import Path

    global _LOG_ERROR_RE
    if _LOG_ERROR_RE is None:
        _LOG_ERROR_RE = re.compile(
            r"(Traceback \(most recent call last\)|\bERROR\b|\bCRITICAL\b|"
            r"\bException\b|Request timed out|\[LLM call failed|OperationalError|"
            r"database is locked|\b50[234]\b|\b524\b|no such (?:table|column))",
            re.IGNORECASE,
        )

    try:
        from hub_db import get_config, set_config
    except Exception:
        get_config = set_config = None  # type: ignore

    log_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "logs"
    if not log_dir.exists():
        return "", 0

    blocks: list[str] = []
    total = 0
    for log_path in sorted(log_dir.glob("*.log")):
        name = log_path.stem
        try:
            size = log_path.stat().st_size
        except Exception:
            continue
        wm_key = f"logwm_{name}"
        offset = 0
        if callable(get_config):
            try:
                offset = int(get_config(wm_key) or 0)
            except Exception:
                offset = 0
        if offset > size:          # rotated/truncated
            offset = 0
        if offset >= size:         # nothing new
            continue
        try:
            with log_path.open("r", encoding="utf-8", errors="ignore") as fh:
                fh.seek(offset)
                new_text = fh.read()
        except Exception:
            continue
        if callable(set_config):
            try:
                set_config(wm_key, size)
            except Exception:
                pass
        hits = [ln.strip() for ln in new_text.splitlines() if ln.strip() and _LOG_ERROR_RE.search(ln)]
        if hits:
            total += len(hits)
            blocks.append(f"### {log_path.name} ({len(hits)} new error line(s))\n" + "\n".join(hits[:40]))

    if not blocks:
        return "", 0
    digest = "## New log errors since last sweep\n\n" + "\n\n".join(blocks)
    return digest[:max_chars], total


async def job_log_monitor(hub):
    """Every cycle: scan logs for new errors; if any, dispatch the devops team
    (devops-log-monitor → root-cause → fix-engineer) which opens tickets and
    proposes fixes. Skips entirely when the logs are quiet."""
    logger = get_logger("scheduler")
    try:
        digest, count = _collect_new_log_errors()
    except Exception:
        logger.exception("log_monitor: failed collecting log errors")
        return
    if not digest:
        return  # quiet — no LLM dispatch
    logger.info("log_monitor: %d new error line(s) detected — dispatching devops team", count)
    try:
        from report_monitor import run_report_job
        await run_report_job("log_monitor", extra_context=digest)
    except Exception:
        logger.exception("log_monitor: devops team dispatch failed")


# Single source of truth for all built-in jobs.
# Format: job_id -> (func, display_name, cron_kwargs)
_JOB_SPECS: dict[str, tuple] = {
    "log_monitor":                               (job_log_monitor,                          "DevOps Log Monitor",                 {"minute": "*/15"}),
    "daily_briefing":                            (job_daily_briefing_compute,               "Daily Briefing",                     {"hour": 6,  "minute": 50}),
    "daily_reflexion":                           (job_daily_reflexion_report,               "Daily Reflexion",                    {"hour": 7,  "minute": 0}),
    "grant_research_sweep":                      (job_grant_research_sweep,                 "Grant Research Sweep",               {"day_of_week": "mon", "hour": 8,  "minute": 0}),
    "hutto_planning_monitor":                    (job_hutto_planning_monitor,               "Hutto Planning Monitor",             {"day_of_week": "mon", "hour": 8,  "minute": 30}),
    "weekly_fare_alert":                         (job_weekly_fare_alert,                    "Weekly Fare Alert",                  {"day_of_week": "mon", "hour": 13, "minute": 30}),
    "sigma_signal_check":                        (job_sigma_signal_check,                   "Sigma Signal Check",                 {"hour": 14, "minute": 0}),
    "markets_daily_premarket_brief":             (job_markets_daily_premarket_brief,        "Markets Pre-Market Brief",           {"day_of_week": "mon-fri", "hour": 8, "minute": 30}),
    "markets_weekly_picks_digest":               (job_markets_weekly_picks_digest,          "Markets Weekly Picks Digest",        {"day_of_week": "mon", "hour": 7,  "minute": 0}),
    "markets_monthly_portfolio_review":          (job_markets_monthly_portfolio_review,     "Markets Monthly P&L Review",         {"day": "1-7", "day_of_week": "mon", "hour": 9, "minute": 0}),
    # V2 Morning Pipeline (Mon-Fri)
    "markets_v2_overnight_macro":                (job_markets_v2_overnight_macro,           "V2 Overnight Macro Review",          {"day_of_week": "mon-fri", "hour": 5,  "minute": 30}),
    "markets_v2_news_intelligence":              (job_markets_v2_news_intelligence,         "V2 News Intelligence Scan",          {"day_of_week": "mon-fri", "hour": 5,  "minute": 45}),
    "markets_v2_sentiment_scan":                 (job_markets_v2_sentiment_scan,            "V2 Sentiment Scan",                  {"day_of_week": "mon-fri", "hour": 6,  "minute": 0}),
    "markets_v2_whale_activity":                 (job_markets_v2_whale_activity,            "V2 Whale Activity Scan",             {"day_of_week": "mon-fri", "hour": 6,  "minute": 15}),
    "markets_v2_insider_scan":                   (job_markets_v2_insider_scan,              "V2 Insider Transaction Scan",        {"day_of_week": "mon-fri", "hour": 6,  "minute": 30}),
    "markets_v2_regime_assessment":              (job_markets_v2_regime_assessment,         "V2 Market Regime Assessment",        {"day_of_week": "mon-fri", "hour": 6,  "minute": 45}),
    "markets_v2_options_flow":                   (job_markets_v2_options_flow,              "V2 Options Flow Analysis",           {"day_of_week": "mon-fri", "hour": 7,  "minute": 0}),
    "markets_v2_watchlist_generation":           (job_markets_v2_watchlist_generation,      "V2 Watchlist Generation",            {"day_of_week": "mon-fri", "hour": 7,  "minute": 30}),
    "markets_v2_probability_scan":               (job_markets_v2_probability_scan,          "V2 Probability Assessment",          {"day_of_week": "mon-fri", "hour": 8,  "minute": 0}),
    "markets_v2_executive_briefing":             (job_markets_v2_executive_briefing,        "V2 Executive Briefing",              {"day_of_week": "mon-fri", "hour": 8,  "minute": 15}),
    # V2 Hourly (Mon-Fri market hours)
    "markets_v2_hourly_position_review":         (job_markets_v2_hourly_position_review,    "V2 Hourly Position Review",          {"day_of_week": "mon-fri", "hour": "10-15", "minute": 0}),
    "markets_v2_hourly_trailing_stops":          (job_markets_v2_hourly_trailing_stops,     "V2 Hourly Trailing Stop Update",     {"day_of_week": "mon-fri", "hour": "10-15", "minute": 15}),
    "markets_v2_hourly_news_refresh":            (job_markets_v2_hourly_news_refresh,       "V2 Hourly News Refresh",             {"day_of_week": "mon-fri", "hour": "10-15", "minute": 30}),
    # V2 End of Day (Mon-Fri)
    "markets_v2_eod_performance":                (job_markets_v2_eod_performance,           "V2 EOD Performance Metrics",         {"day_of_week": "mon-fri", "hour": 16, "minute": 0}),
    "markets_v2_eod_risk_assessment":            (job_markets_v2_eod_risk_assessment,       "V2 EOD Risk Assessment",             {"day_of_week": "mon-fri", "hour": 16, "minute": 15}),
    "markets_v2_eod_journal":                    (job_markets_v2_eod_journal,               "V2 EOD Trading Journal",             {"day_of_week": "mon-fri", "hour": 16, "minute": 30}),
    "markets_v2_eod_next_day_plan":              (job_markets_v2_eod_next_day_plan,         "V2 EOD Next-Day Plan",               {"day_of_week": "mon-fri", "hour": 16, "minute": 45}),
    # V2 Weekly (Monday)
    "markets_v2_weekly_portfolio_review":        (job_markets_v2_weekly_portfolio_review,        "V2 Weekly Portfolio Review",      {"day_of_week": "mon", "hour": 9,  "minute": 30}),
    "markets_v2_weekly_strategy_optimization":   (job_markets_v2_weekly_strategy_optimization,   "V2 Weekly Strategy Optimization", {"day_of_week": "mon", "hour": 10, "minute": 0}),
    "markets_v2_weekly_marketing_content":       (job_markets_v2_weekly_marketing_content,       "V2 Weekly Marketing Content",     {"day_of_week": "mon", "hour": 10, "minute": 30}),
    "markets_v2_weekly_performance_report":      (job_markets_v2_weekly_performance_report,      "V2 Weekly Performance Report",    {"day_of_week": "mon", "hour": 11, "minute": 0}),
    # V2 Monthly (1st Monday)
    "markets_v2_monthly_backtest_update":        (job_markets_v2_monthly_backtest_update,        "V2 Monthly Backtest Update",      {"day": "1-7", "day_of_week": "mon", "hour": 7,  "minute": 30}),
    "markets_v2_monthly_strategy_tuning":        (job_markets_v2_monthly_strategy_tuning,        "V2 Monthly Strategy Tuning",      {"day": "1-7", "day_of_week": "mon", "hour": 8,  "minute": 0}),
    "markets_v2_monthly_rebalance":              (job_markets_v2_monthly_rebalance,              "V2 Monthly Portfolio Rebalance",  {"day": "1-7", "day_of_week": "mon", "hour": 10, "minute": 0}),
    "markets_v2_monthly_curriculum_refresh":     (job_markets_v2_monthly_curriculum_refresh,     "V2 Monthly Curriculum Refresh",   {"day": "1-7", "day_of_week": "mon", "hour": 11, "minute": 0}),
    # Capitol Trades
    "capitol_trades_daily_refresh":              (job_capitol_trades_daily_refresh,         "Capitol Trades Daily Refresh",       {"day_of_week": "mon-fri", "hour": 9,  "minute": 0}),
    "capitol_trades_signal_digest":              (job_capitol_trades_signal_digest,         "Capitol Trades Signal Digest",       {"day_of_week": "mon-fri", "hour": 9,  "minute": 30}),
    "nightly_db_cleanup":                        (job_nightly_db_cleanup,                   "Nightly DB Cleanup",                 {"hour": 2,  "minute": 0}),
    "nightly_db_backup":                         (job_nightly_db_backup,                    "Nightly DB Backup",                  {"hour": 3,  "minute": 0}),
    "sync_free_llm_keys":                        (job_sync_free_llm_keys,                   "Sync Free LLM Keys",                 {"hour": 7,  "minute": 15}),
}

# Single source of truth for built-in job IDs (derived from _JOB_SPECS)
BUILT_IN_JOB_IDS: frozenset[str] = frozenset(_JOB_SPECS.keys())


class HubScheduler:
    def __init__(self, hub=None):
        self.hub = hub  # reference to HubServer (for submit_job)
        if AsyncIOScheduler is None:
            raise RuntimeError("APScheduler AsyncIOScheduler is not available")
        self.scheduler = AsyncIOScheduler(timezone="America/Chicago")
        self.logger = get_logger("scheduler")

    def build(self):
        """Register all built-in jobs from _JOB_SPECS."""
        if CronTrigger is None:
            raise RuntimeError("APScheduler CronTrigger is not available")

        tz = _get_timezone()

        for job_id, (func, name, cron_kwargs) in _JOB_SPECS.items():
            trigger = CronTrigger(timezone=tz, **cron_kwargs)
            self.scheduler.add_job(
                _make_tracked(func, job_id),
                trigger=trigger,
                id=job_id,
                name=name,
                args=[self.hub],
                replace_existing=True,
                coalesce=True,
                max_instances=1,
                misfire_grace_time=3600,
            )

        if callable(list_scheduled_jobs):
            try:
                for job_config in list_scheduled_jobs():
                    job_id = str(job_config.get("id") or "")
                    if job_id and job_id not in BUILT_IN_JOB_IDS:
                        self.add_user_job(job_config)
            except Exception:
                self.logger.exception("Failed loading user-defined scheduled jobs from DB")

        self.logger.info("Registered %s built-in scheduler jobs", len(BUILT_IN_JOB_IDS))
        return self

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def get_job_list(self) -> list[dict]:
        """Returns serializable list of all jobs with next_fire times"""
        jobs: list[dict] = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_fire": _serialize_datetime(getattr(job, "next_run_time", None)),
                    "trigger": str(job.trigger),
                    "built_in": job.id in BUILT_IN_JOB_IDS,
                }
            )
        return sorted(jobs, key=lambda item: (item["next_fire"] is None, item["next_fire"] or "", item["id"] or ""))

    def add_user_job(self, job_config: dict) -> str:
        """Add a user-defined job from DB config"""
        if CronTrigger is None or IntervalTrigger is None:
            raise RuntimeError("APScheduler triggers are not available")

        config = dict(job_config)
        job_id = str(config.get("id") or f"user_job_{int(datetime.now(timezone.utc).timestamp())}")
        config["id"] = job_id
        name = config.get("name") or job_id.replace("_", " ").title()
        tz = _get_timezone()

        cron_expr = config.get("cron_expr")
        interval_sec = config.get("interval_sec")
        cron_fields = {
            field: config[field]
            for field in ("year", "month", "day", "week", "day_of_week", "hour", "minute", "second")
            if config.get(field) not in (None, "")
        }

        if cron_expr:
            trigger = CronTrigger.from_crontab(str(cron_expr), timezone=tz)
        elif cron_fields:
            trigger = CronTrigger(timezone=tz, **cron_fields)
        elif interval_sec is not None:
            trigger = IntervalTrigger(seconds=int(interval_sec), timezone=tz)
        else:
            raise ValueError("job_config must include cron_expr, cron fields, or interval_sec")

        self.scheduler.add_job(
            _make_tracked(_run_user_job, job_id),
            trigger=trigger,
            id=job_id,
            name=name,
            args=[self.hub, config],
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=int(config.get("misfire_grace_time", 3600)),
        )

        job = self.scheduler.get_job(job_id)
        if job is not None:
            _update_job_state(
                job_id,
                self.logger,
                next_fire=_serialize_datetime(job.next_run_time),
                status="active",
            )
        self.logger.info("Added user-defined scheduled job %s", job_id)
        return job_id

    def remove_job(self, job_id: str) -> bool:
        job = self.scheduler.get_job(job_id)
        if job is None:
            return False
        self.scheduler.remove_job(job_id)
        _update_job_state(job_id, self.logger, status="cancelled", next_fire=None)
        self.logger.info("Removed scheduled job %s", job_id)
        return True

    def trigger_job(self, job_id: str) -> bool:
        """Manually trigger a scheduled job immediately"""
        job = self.scheduler.get_job(job_id)
        if job is None:
            return False
        run_at = _now_in_timezone()
        job.modify(next_run_time=run_at)
        if hasattr(self.scheduler, "wakeup"):
            self.scheduler.wakeup()
        _update_job_state(job_id, self.logger, next_fire=_serialize_datetime(run_at), status="active")
        self.logger.info("Triggered scheduled job %s for immediate execution", job_id)
        return True


def build_scheduler(hub) -> HubScheduler:
    scheduler = HubScheduler(hub)
    scheduler.build()
    return scheduler
