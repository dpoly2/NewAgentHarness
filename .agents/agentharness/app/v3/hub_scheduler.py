"""
hub_scheduler.py — ArchonHub APScheduler engine
Timezone: America/Chicago
"""
from __future__ import annotations

from datetime import datetime, timedelta
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
BUILT_IN_JOBS = (
    ("daily_briefing",                     "Daily Briefing",                     {"hour": 6,  "minute": 50},                                   "Compute morning briefing"),
    ("daily_reflexion",                    "Daily Reflexion",                    {"hour": 7,  "minute": 0},                                    "Daily reflexion report"),
    ("grant_research_sweep",               "Grant Research Sweep",               {"day_of_week": "mon", "hour": 8,  "minute": 0},              "Grant research across 4 orgs"),
    ("hutto_planning_monitor",             "Hutto Planning Monitor",             {"day_of_week": "mon", "hour": 8,  "minute": 30},             "Hutto city planning monitor"),
    ("weekly_fare_alert",                  "Weekly Fare Alert",                  {"day_of_week": "mon", "hour": 13, "minute": 30},             "Travel fare alerts from AUS"),
    ("sigma_signal_check",                 "Sigma Signal Check",                 {"hour": 14, "minute": 0},                                    "Sigma Signal inbox check"),
    ("markets_daily_premarket_brief",      "Markets Pre-Market Brief",           {"day_of_week": "mon-fri", "hour": 8, "minute": 30},          "Markets daily pre-market intelligence"),
    ("markets_weekly_picks_digest",        "Markets Weekly Picks Digest",        {"day_of_week": "mon", "hour": 7,  "minute": 0},              "Markets weekly actionable picks"),
    ("markets_monthly_portfolio_review",   "Markets Monthly P&L Review",         {"day": "1-7", "day_of_week": "mon", "hour": 9, "minute": 0}, "Markets monthly portfolio review"),
    # V2 Morning Pipeline (Mon-Fri)
    ("markets_v2_overnight_macro",         "V2 Overnight Macro Review",          {"day_of_week": "mon-fri", "hour": 5,  "minute": 30},         "Overnight macro intelligence sweep"),
    ("markets_v2_news_intelligence",       "V2 News Intelligence Scan",          {"day_of_week": "mon-fri", "hour": 5,  "minute": 45},         "Pre-market news and catalyst scan"),
    ("markets_v2_sentiment_scan",          "V2 Sentiment Scan",                  {"day_of_week": "mon-fri", "hour": 6,  "minute": 0},          "Pre-market sentiment assessment"),
    ("markets_v2_whale_activity",          "V2 Whale Activity Scan",             {"day_of_week": "mon-fri", "hour": 6,  "minute": 15},         "Institutional activity pre-market scan"),
    ("markets_v2_insider_scan",            "V2 Insider Transaction Scan",        {"day_of_week": "mon-fri", "hour": 6,  "minute": 30},         "SEC Form 4 insider transaction review"),
    ("markets_v2_regime_assessment",       "V2 Market Regime Assessment",        {"day_of_week": "mon-fri", "hour": 6,  "minute": 45},         "Daily market regime classification"),
    ("markets_v2_options_flow",            "V2 Options Flow Analysis",           {"day_of_week": "mon-fri", "hour": 7,  "minute": 0},          "Pre-market options flow and wheel candidates"),
    ("markets_v2_watchlist_generation",    "V2 Watchlist Generation",            {"day_of_week": "mon-fri", "hour": 7,  "minute": 30},         "Daily watchlist synthesis from all agents"),
    ("markets_v2_probability_scan",        "V2 Probability Assessment",          {"day_of_week": "mon-fri", "hour": 8,  "minute": 0},          "Pre-market probability scoring per setup"),
    ("markets_v2_executive_briefing",      "V2 Executive Briefing",              {"day_of_week": "mon-fri", "hour": 8,  "minute": 15},         "Morning executive briefing via Inez"),
    # V2 Hourly (Mon-Fri market hours)
    ("markets_v2_hourly_position_review",  "V2 Hourly Position Review",          {"day_of_week": "mon-fri", "hour": "10-15", "minute": 0},    "Hourly position P&L and stop review"),
    ("markets_v2_hourly_trailing_stops",   "V2 Hourly Trailing Stop Update",     {"day_of_week": "mon-fri", "hour": "10-15", "minute": 15},   "Hourly trailing stop adjustments"),
    ("markets_v2_hourly_news_refresh",     "V2 Hourly News Refresh",             {"day_of_week": "mon-fri", "hour": "10-15", "minute": 30},   "Hourly intraday news and catalyst refresh"),
    # V2 End of Day (Mon-Fri)
    ("markets_v2_eod_performance",         "V2 EOD Performance Metrics",         {"day_of_week": "mon-fri", "hour": 16, "minute": 0},          "End-of-day performance metrics"),
    ("markets_v2_eod_risk_assessment",     "V2 EOD Risk Assessment",             {"day_of_week": "mon-fri", "hour": 16, "minute": 15},         "End-of-day CRO risk review"),
    ("markets_v2_eod_journal",             "V2 EOD Trading Journal",             {"day_of_week": "mon-fri", "hour": 16, "minute": 30},         "End-of-day trading journal"),
    ("markets_v2_eod_next_day_plan",       "V2 EOD Next-Day Plan",               {"day_of_week": "mon-fri", "hour": 16, "minute": 45},         "End-of-day next-day planning"),
    # V2 Weekly (Monday)
    ("markets_v2_weekly_portfolio_review",      "V2 Weekly Portfolio Review",      {"day_of_week": "mon", "hour": 9,  "minute": 30},             "Weekly portfolio allocation review"),
    ("markets_v2_weekly_strategy_optimization", "V2 Weekly Strategy Optimization", {"day_of_week": "mon", "hour": 10, "minute": 0},              "Weekly strategy backtesting update"),
    ("markets_v2_weekly_marketing_content",     "V2 Weekly Marketing Content",     {"day_of_week": "mon", "hour": 10, "minute": 30},             "Weekly educational content creation"),
    ("markets_v2_weekly_performance_report",    "V2 Weekly Performance Report",    {"day_of_week": "mon", "hour": 11, "minute": 0},              "Weekly performance recap and community report"),
    # V2 Monthly (1st Monday)
    ("markets_v2_monthly_backtest_update",      "V2 Monthly Backtest Update",      {"day": "1-7", "day_of_week": "mon", "hour": 7,  "minute": 30}, "Monthly comprehensive backtest update"),
    ("markets_v2_monthly_strategy_tuning",      "V2 Monthly Strategy Tuning",      {"day": "1-7", "day_of_week": "mon", "hour": 8,  "minute": 0},  "Monthly strategy parameter optimization"),
    ("markets_v2_monthly_rebalance",            "V2 Monthly Portfolio Rebalance",  {"day": "1-7", "day_of_week": "mon", "hour": 10, "minute": 0},  "Monthly portfolio rebalancing"),
    ("markets_v2_monthly_curriculum_refresh",   "V2 Monthly Curriculum Refresh",   {"day": "1-7", "day_of_week": "mon", "hour": 11, "minute": 0},  "Monthly educational curriculum update"),
    # Capitol Trades
    ("capitol_trades_daily_refresh",       "Capitol Trades Daily Refresh",       {"day_of_week": "mon-fri", "hour": 9,  "minute": 0},          "Refresh politician trade disclosures"),
    ("capitol_trades_signal_digest",       "Capitol Trades Signal Digest",       {"day_of_week": "mon-fri", "hour": 9,  "minute": 30},         "Congress Edge signal digest for CRO"),
    ("nightly_db_cleanup",                 "Nightly DB Cleanup",                 {"hour": 2,  "minute": 0},                                    "Remove runs older than 90 days"),
    ("nightly_db_backup",                  "Nightly DB Backup",                  {"hour": 3,  "minute": 0},                                    "Export critical tables to JSON backup"),
    ("sync_free_llm_keys",                 "Sync Free LLM Keys",                 {"hour": 7,  "minute": 15},                                   "Fetch and activate free daily LLM API keys"),
)
BUILT_IN_JOB_IDS = {job_id for job_id, _, _, _ in BUILT_IN_JOBS}


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


def _make_tracked(func, job_id: str):
    """Wrap a job coroutine to record last_run_at, last_run_status, run_count in DB."""
    import functools

    @functools.wraps(func)
    async def _wrapper(*args, **kwargs):
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

        cutoff = (datetime.utcnow() - timedelta(days=90)).isoformat()
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
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post("http://localhost:8765/api/capitol-trades/refresh-all")
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
        from free_llm_keys import sync_free_keys
        # Run the sync in a thread pool so it doesn't block the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sync_free_keys)
        synced_list = ", ".join(result.get("synced", {}).keys()) or "none"
        _notify(
            f"Free LLM keys synced: {len(result.get('synced', {}))} providers activated ({synced_list})",
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


class HubScheduler:
    def __init__(self, hub=None):
        self.hub = hub  # reference to HubServer (for submit_job)
        if AsyncIOScheduler is None:
            raise RuntimeError("APScheduler AsyncIOScheduler is not available")
        self.scheduler = AsyncIOScheduler(timezone="America/Chicago")
        self.logger = get_logger("scheduler")

    def build(self):
        """Register all built-in jobs"""
        if CronTrigger is None:
            raise RuntimeError("APScheduler CronTrigger is not available")

        tz = _get_timezone()
        job_specs = {
            "daily_briefing":                       (job_daily_briefing_compute,               "Daily Briefing",                     {"hour": 6,  "minute": 50}),
            "daily_reflexion":                      (job_daily_reflexion_report,               "Daily Reflexion",                    {"hour": 7,  "minute": 0}),
            "grant_research_sweep":                 (job_grant_research_sweep,                 "Grant Research Sweep",               {"day_of_week": "mon", "hour": 8,  "minute": 0}),
            "hutto_planning_monitor":               (job_hutto_planning_monitor,               "Hutto Planning Monitor",             {"day_of_week": "mon", "hour": 8,  "minute": 30}),
            "weekly_fare_alert":                    (job_weekly_fare_alert,                    "Weekly Fare Alert",                  {"day_of_week": "mon", "hour": 13, "minute": 30}),
            "sigma_signal_check":                   (job_sigma_signal_check,                   "Sigma Signal Check",                 {"hour": 14, "minute": 0}),
            "markets_daily_premarket_brief":        (job_markets_daily_premarket_brief,        "Markets Pre-Market Brief",           {"day_of_week": "mon-fri", "hour": 8, "minute": 30}),
            "markets_weekly_picks_digest":          (job_markets_weekly_picks_digest,          "Markets Weekly Picks Digest",        {"day_of_week": "mon", "hour": 7,  "minute": 0}),
            "markets_monthly_portfolio_review":     (job_markets_monthly_portfolio_review,     "Markets Monthly P&L Review",         {"day": "1-7", "day_of_week": "mon", "hour": 9, "minute": 0}),
            "markets_v2_overnight_macro":           (job_markets_v2_overnight_macro,           "V2 Overnight Macro Review",          {"day_of_week": "mon-fri", "hour": 5,  "minute": 30}),
            "markets_v2_news_intelligence":         (job_markets_v2_news_intelligence,         "V2 News Intelligence Scan",          {"day_of_week": "mon-fri", "hour": 5,  "minute": 45}),
            "markets_v2_sentiment_scan":            (job_markets_v2_sentiment_scan,            "V2 Sentiment Scan",                  {"day_of_week": "mon-fri", "hour": 6,  "minute": 0}),
            "markets_v2_whale_activity":            (job_markets_v2_whale_activity,            "V2 Whale Activity Scan",             {"day_of_week": "mon-fri", "hour": 6,  "minute": 15}),
            "markets_v2_insider_scan":              (job_markets_v2_insider_scan,              "V2 Insider Transaction Scan",        {"day_of_week": "mon-fri", "hour": 6,  "minute": 30}),
            "markets_v2_regime_assessment":         (job_markets_v2_regime_assessment,         "V2 Market Regime Assessment",        {"day_of_week": "mon-fri", "hour": 6,  "minute": 45}),
            "markets_v2_options_flow":              (job_markets_v2_options_flow,              "V2 Options Flow Analysis",           {"day_of_week": "mon-fri", "hour": 7,  "minute": 0}),
            "markets_v2_watchlist_generation":      (job_markets_v2_watchlist_generation,      "V2 Watchlist Generation",            {"day_of_week": "mon-fri", "hour": 7,  "minute": 30}),
            "markets_v2_probability_scan":          (job_markets_v2_probability_scan,          "V2 Probability Assessment",          {"day_of_week": "mon-fri", "hour": 8,  "minute": 0}),
            "markets_v2_executive_briefing":        (job_markets_v2_executive_briefing,        "V2 Executive Briefing",              {"day_of_week": "mon-fri", "hour": 8,  "minute": 15}),
            "markets_v2_hourly_position_review":    (job_markets_v2_hourly_position_review,    "V2 Hourly Position Review",          {"day_of_week": "mon-fri", "hour": "10-15", "minute": 0}),
            "markets_v2_hourly_trailing_stops":     (job_markets_v2_hourly_trailing_stops,     "V2 Hourly Trailing Stop Update",     {"day_of_week": "mon-fri", "hour": "10-15", "minute": 15}),
            "markets_v2_hourly_news_refresh":       (job_markets_v2_hourly_news_refresh,       "V2 Hourly News Refresh",             {"day_of_week": "mon-fri", "hour": "10-15", "minute": 30}),
            "markets_v2_eod_performance":           (job_markets_v2_eod_performance,           "V2 EOD Performance Metrics",         {"day_of_week": "mon-fri", "hour": 16, "minute": 0}),
            "markets_v2_eod_risk_assessment":       (job_markets_v2_eod_risk_assessment,       "V2 EOD Risk Assessment",             {"day_of_week": "mon-fri", "hour": 16, "minute": 15}),
            "markets_v2_eod_journal":               (job_markets_v2_eod_journal,               "V2 EOD Trading Journal",             {"day_of_week": "mon-fri", "hour": 16, "minute": 30}),
            "markets_v2_eod_next_day_plan":         (job_markets_v2_eod_next_day_plan,         "V2 EOD Next-Day Plan",               {"day_of_week": "mon-fri", "hour": 16, "minute": 45}),
            "markets_v2_weekly_portfolio_review":   (job_markets_v2_weekly_portfolio_review,   "V2 Weekly Portfolio Review",         {"day_of_week": "mon", "hour": 9,  "minute": 30}),
            "markets_v2_weekly_strategy_optimization": (job_markets_v2_weekly_strategy_optimization, "V2 Weekly Strategy Optimization", {"day_of_week": "mon", "hour": 10, "minute": 0}),
            "markets_v2_weekly_marketing_content":  (job_markets_v2_weekly_marketing_content,  "V2 Weekly Marketing Content",        {"day_of_week": "mon", "hour": 10, "minute": 30}),
            "markets_v2_weekly_performance_report": (job_markets_v2_weekly_performance_report, "V2 Weekly Performance Report",       {"day_of_week": "mon", "hour": 11, "minute": 0}),
            "markets_v2_monthly_backtest_update":   (job_markets_v2_monthly_backtest_update,   "V2 Monthly Backtest Update",         {"day": "1-7", "day_of_week": "mon", "hour": 7,  "minute": 30}),
            "markets_v2_monthly_strategy_tuning":   (job_markets_v2_monthly_strategy_tuning,   "V2 Monthly Strategy Tuning",         {"day": "1-7", "day_of_week": "mon", "hour": 8,  "minute": 0}),
            "markets_v2_monthly_rebalance":         (job_markets_v2_monthly_rebalance,         "V2 Monthly Portfolio Rebalance",     {"day": "1-7", "day_of_week": "mon", "hour": 10, "minute": 0}),
            "markets_v2_monthly_curriculum_refresh": (job_markets_v2_monthly_curriculum_refresh, "V2 Monthly Curriculum Refresh",     {"day": "1-7", "day_of_week": "mon", "hour": 11, "minute": 0}),
            "capitol_trades_daily_refresh":         (job_capitol_trades_daily_refresh,         "Capitol Trades Daily Refresh",       {"day_of_week": "mon-fri", "hour": 9,  "minute": 0}),
            "capitol_trades_signal_digest":         (job_capitol_trades_signal_digest,         "Capitol Trades Signal Digest",       {"day_of_week": "mon-fri", "hour": 9,  "minute": 30}),
            "nightly_db_cleanup":                   (job_nightly_db_cleanup,                   "Nightly DB Cleanup",                 {"hour": 2,  "minute": 0}),
            "nightly_db_backup":                    (job_nightly_db_backup,                    "Nightly DB Backup",                  {"hour": 3,  "minute": 0}),
            "sync_free_llm_keys":                   (job_sync_free_llm_keys,                   "Sync Free LLM Keys",                 {"hour": 7,  "minute": 15}),
        }

        for job_id, (func, name, cron_kwargs) in job_specs.items():
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
                    "next_fire": _serialize_datetime(job.next_run_time),
                    "trigger": str(job.trigger),
                    "built_in": job.id in BUILT_IN_JOB_IDS,
                }
            )
        return sorted(jobs, key=lambda item: (item["next_fire"] is None, item["next_fire"] or "", item["id"]))

    def add_user_job(self, job_config: dict) -> str:
        """Add a user-defined job from DB config"""
        if CronTrigger is None or IntervalTrigger is None:
            raise RuntimeError("APScheduler triggers are not available")

        config = dict(job_config)
        job_id = str(config.get("id") or f"user_job_{int(datetime.utcnow().timestamp())}")
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
