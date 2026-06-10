"""
report_monitor.py — ArchonHub Daily Report Monitor
====================================================
Monitors daily automation jobs, dispatches the correct agent team,
and writes structured reports to the `reports` DB table.

Each report job:
  1. Determines which agents cover the domain
  2. Dispatches agents via agent_runner.run_agent()
  3. Collects output + db_writes
  4. Saves a structured report to hub_db.create_report()

Reports are browsable from the Reports tab in the desktop app.

REPORT TYPES:
  daily_briefing    — morning portfolio brief (6:50am daily)
  daily_reflexion   — prior-day run review (7:00am daily)
  grant_research    — grant opportunity sweep (Monday 8am)
  hutto_planning    — city planning monitor (Monday 8:30am)
  fare_alert        — weekly travel deals (Monday 1:30pm)
  sigma_signal      — newsletter inbox check (daily 2pm)
  project_status    — per-project status (any time)
  custom            — user-defined automation reports

Scheduler integration: each HubScheduler job calls
  report_monitor.run_report_job(job_id, hub) after submitting the hub job.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
AGENTS_DIR = HARNESS.parent

import sys
for _p in (HERE, HARNESS, AGENTS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    import hub_db as db
    DB_OK = True
except ImportError:
    db = None  # type: ignore
    DB_OK = False

try:
    from agent_runner import run_agent, build_synthesis_context
    RUNNER_OK = True
except ImportError:
    RUNNER_OK = False

try:
    from ah_logging import get_logger
    logger = get_logger("report_monitor")
except Exception:
    import logging
    logger = logging.getLogger("report_monitor")

# ---------------------------------------------------------------------------
# Report job definitions — maps job_id → (report_type, title, agent_team)
# ---------------------------------------------------------------------------
# Each agent_team entry: {"agent_id": str, "task": str, "project": str}

REPORT_JOBS: dict[str, dict] = {
    "daily_briefing": {
        "report_type": "briefing",
        "title_template": "Morning Briefing — {date}",
        "project_slug": "archonhub",
        "agents": [
            {
                "agent_id": "inez-chief-of-staff",
                "project": "archonhub",
                "task": (
                    "Generate a comprehensive morning briefing for David Smith. Include:\n"
                    "1. Executive summary (2-3 sentences)\n"
                    "2. Immediate priorities (top 3 action items)\n"
                    "3. Active agent runs and their status\n"
                    "4. Pending todos by project\n"
                    "5. Key deadlines this week\n"
                    "6. Automation health — which jobs ran overnight, any failures\n"
                    "Format as clean markdown with clear sections."
                ),
            },
        ],
    },

    "daily_reflexion": {
        "report_type": "reflexion",
        "title_template": "Daily Reflexion — {date}",
        "project_slug": "archonhub",
        "agents": [
            {
                "agent_id": "finance-cfo",
                "project": "smithcap-finance",
                "task": (
                    "Daily reflexion report. Review all agent runs from the past 24 hours:\n"
                    "1. Which agents ran and what did they produce?\n"
                    "2. Quality assessment — were outputs useful?\n"
                    "3. Patterns or recurring issues\n"
                    "4. Recommended improvements for tomorrow\n"
                    "5. Portfolio financial indicators update\n"
                    "Format as structured markdown."
                ),
            },
        ],
    },

    "grant_research_sweep": {
        "report_type": "research",
        "title_template": "Weekly Grant Research — {date}",
        "project_slug": "grants",
        "agents": [
            {
                "agent_id": "grants-research-agent",
                "project": "yepc",
                "task": "Weekly grant research sweep for YEPC: identify new federal, state, and local grants available for youth entrepreneurship and community programs. Include deadlines, amounts, and application requirements.",
            },
            {
                "agent_id": "yepc-grant-writer-agent",
                "project": "yepc",
                "task": "Review current YEPC grant pipeline status. Which applications are in progress? What needs to be submitted this week? Draft action list.",
            },
            {
                "agent_id": "pbs-fundraising-agent",
                "project": "pbs-foundation",
                "task": "Weekly grant and fundraising research for PBS Foundation 501(c)(3): find new donation drives, matching opportunities, and grant sources for performing arts nonprofits.",
            },
            {
                "agent_id": "solar-marketing-agent",
                "project": "solar-repair",
                "task": "Research federal and Texas state incentive programs, grants, and rebates for solar installation businesses. Include new IRA provisions and SECO programs.",
            },
        ],
    },

    "hutto_planning_monitor": {
        "report_type": "research",
        "title_template": "Hutto Planning Monitor — {date}",
        "project_slug": "yepc",
        "agents": [
            {
                "agent_id": "yepc-project-manager",
                "project": "yepc",
                "task": (
                    "Monitor Hutto TX and Williamson County planning activity:\n"
                    "1. New development applications filed this week\n"
                    "2. Zoning changes or variances approved/pending\n"
                    "3. City council agenda items relevant to YEPC mission\n"
                    "4. New commercial real estate opportunities near YEPC service area\n"
                    "5. School district updates affecting youth programs\n"
                    "Format as structured intelligence report."
                ),
            },
        ],
    },

    "weekly_fare_alert": {
        "report_type": "travel",
        "title_template": "Weekly Fare Alert — {date}",
        "project_slug": "travel",
        "agents": [
            {
                "agent_id": "travel-flights-agent",
                "project": "travel",
                "task": (
                    "Weekly fare alert from Austin-Bergstrom (AUS):\n"
                    "1. Best domestic deals departing AUS in next 60 days\n"
                    "2. Alert if Atlanta (ATL) fares drop below $400 RT\n"
                    "3. Top 5 flash sale destinations this week\n"
                    "4. Southwest, Delta, American notable fare drops\n"
                    "Save findings to knowledge_base table with category='travel'."
                ),
            },
        ],
    },

    "sigma_signal_check": {
        "report_type": "operations",
        "title_template": "Sigma Signal Inbox — {date}",
        "project_slug": "sigma-signal",
        "agents": [
            {
                "agent_id": "sigma-signal-writer",
                "project": "sigma-signal",
                "task": (
                    "Sigma Signal newsletter operations check:\n"
                    "1. Pending submission queue status\n"
                    "2. Content pipeline — articles ready to publish\n"
                    "3. Subscriber growth and engagement this week\n"
                    "4. Next edition schedule and content outline\n"
                    "5. Social amplification tasks needed\n"
                    "Format as operations brief."
                ),
            },
        ],
    },

    "markets_daily_premarket_brief": {
        "report_type": "daily",
        "title_template": "Markets Pre-Market Brief — {date}",
        "project_slug": "markets",
        "agents": [
            {
                "agent_id": "markets-macro-analyst",
                "project": "markets",
                "task": (
                    "Pre-market intelligence report:\n"
                    "1. Overnight futures (S&P, Nasdaq, Dow, Russell)\n"
                    "2. International market closes (Europe, Asia)\n"
                    "3. Key economic data releases today and this week\n"
                    "4. Fed speakers or FOMC events\n"
                    "5. Major earnings reports today\n"
                    "6. Pre-market movers >3% with catalyst\n"
                    "7. Key technical levels: S&P support/resistance\n"
                    "Format as concise intelligence brief. Save to knowledge_base category=markets."
                ),
            },
            {
                "agent_id": "markets-project-lead",
                "project": "markets",
                "task": (
                    "Based on the macro analyst pre-market data, synthesize the daily pre-market brief:\n"
                    "1. Overall market posture (risk-on / risk-off / neutral)\n"
                    "2. Top 3 opportunities or setups to watch today\n"
                    "3. Key risks or events to avoid\n"
                    "4. Watchlist updates\n"
                    "Format as actionable morning brief. Save summary to knowledge_base."
                ),
            },
        ],
    },

    "markets_weekly_picks_digest": {
        "report_type": "research",
        "title_template": "Markets Weekly Picks Digest — {date}",
        "project_slug": "markets",
        "agents": [
            {
                "agent_id": "markets-equity-analyst",
                "project": "markets",
                "task": (
                    "Weekly equity research sweep:\n"
                    "1. Top 3 stock setups — earnings plays, technical breakouts, fundamentals\n"
                    "2. For each: ticker, thesis, entry zone, target, stop-loss, catalyst\n"
                    "3. Sector rotation — which sectors are leading/lagging?\n"
                    "4. Earnings calendar highlights for the week\n"
                    "Save findings to knowledge_base category=markets."
                ),
            },
            {
                "agent_id": "markets-options-strategist",
                "project": "markets",
                "task": (
                    "Weekly options income opportunities:\n"
                    "1. Top 2-3 covered call candidates (high IV, liquid chains)\n"
                    "2. Top 2 cash-secured put candidates for premium capture\n"
                    "3. Any defined-risk spread setups with favorable R/R\n"
                    "4. For each: ticker, strike, expiry, premium, max risk, thesis\n"
                    "Never risk more than 2% of account per position."
                ),
            },
            {
                "agent_id": "markets-project-lead",
                "project": "markets",
                "task": (
                    "Compile the Weekly Picks Digest from equity and options research:\n"
                    "1. Top 3-5 actionable ideas ranked by conviction\n"
                    "2. Each with: entry, target, stop, position sizing per risk framework\n"
                    "3. Overall portfolio allocation guidance\n"
                    "4. What to avoid this week\n"
                    "Format as clean structured digest. Save as document type=research."
                ),
            },
        ],
    },

    "markets_monthly_portfolio_review": {
        "report_type": "reflexion",
        "title_template": "Markets Monthly Portfolio Review — {date}",
        "project_slug": "markets",
        "agents": [
            {
                "agent_id": "markets-equity-analyst",
                "project": "markets",
                "task": (
                    "Monthly equity position review:\n"
                    "1. All open positions — is the thesis still valid?\n"
                    "2. Any positions that triggered stops or need to be closed?\n"
                    "3. New positions to add based on current market conditions\n"
                    "4. P&L breakdown by position"
                ),
            },
            {
                "agent_id": "markets-options-strategist",
                "project": "markets",
                "task": (
                    "Monthly options portfolio review:\n"
                    "1. All open options positions — roll, close, or let expire?\n"
                    "2. Overall options P&L this month\n"
                    "3. Adjustments needed based on delta/theta profile\n"
                    "4. Next month income generation plan"
                ),
            },
            {
                "agent_id": "markets-project-lead",
                "project": "markets",
                "task": (
                    "Monthly Portfolio Review Report:\n"
                    "1. Total P&L summary (equity + options)\n"
                    "2. Risk metrics vs framework limits (10% max position, 25% sector, 2% options risk)\n"
                    "3. Drawdown analysis — were any weekly 5% limits approached?\n"
                    "4. Strategy adjustments for next month\n"
                    "5. Capital allocation changes\n"
                    "Format as executive P&L report. Save as document type=reflexion."
                ),
            },
        ],
    },
}

# ---------------------------------------------------------------------------
# Per-project status reports (dispatched on demand or on schedule)
# ---------------------------------------------------------------------------

def _build_project_agents(project_slug: str) -> list[dict]:
    """Build agent team for a per-project status report."""
    if not DB_OK:
        return []
    try:
        agents = [
            a for a in db.list_agents()
            if a.get("project_slug") == project_slug and a.get("status") == "active"
        ]
        if not agents:
            return []
        # Use up to 2 agents: lead + one specialist
        team = agents[:2]
        return [
            {
                "agent_id": a.get("agent_id", ""),
                "project": project_slug,
                "task": (
                    f"Generate a project status report for '{project_slug}':\n"
                    "1. What was accomplished this week?\n"
                    "2. What is currently in progress?\n"
                    "3. Blockers or risks\n"
                    "4. Next steps\n"
                    "5. Budget/timeline status if applicable\n"
                    "Save a summary to the knowledge_base with category='project_status'."
                ),
            }
            for a in team
        ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def run_report_job_sync(
    job_id: str,
    emit: Callable | None = None,
    extra_context: str = "",
) -> dict[str, Any]:
    """
    Synchronously execute a report job:
      - Look up agent team for job_id
      - Run each agent via agent_runner
      - Synthesise output into a single report
      - Save to hub_db.reports

    Returns: {"report_id": str, "title": str, "status": str, "error": str|None}
    """
    if not DB_OK or not RUNNER_OK:
        return {"report_id": "", "title": "", "status": "failed",
                "error": "DB or agent_runner not available"}

    job_def = REPORT_JOBS.get(job_id)
    if not job_def:
        # Try dynamic project status report
        if job_id.startswith("project_status_"):
            project_slug = job_id.replace("project_status_", "")
            agents = _build_project_agents(project_slug)
            if not agents:
                return {"report_id": "", "title": "", "status": "skipped",
                        "error": f"No active agents found for project {project_slug}"}
            job_def = {
                "report_type": "project_status",
                "title_template": f"{project_slug.upper()} Status — {{date}}",
                "project_slug": project_slug,
                "agents": agents,
            }
        else:
            return {"report_id": "", "title": "", "status": "failed",
                    "error": f"Unknown job_id: {job_id}"}

    date_str = _today()
    title = job_def["title_template"].format(date=date_str)
    report_type = job_def["report_type"]
    project_slug = job_def.get("project_slug", "")
    agent_team = job_def.get("agents", [])

    # Create a placeholder report in "generating" status
    rid = str(uuid.uuid4())
    try:
        db.create_report(
            id=rid,
            title=title,
            report_type=report_type,
            content="",
            summary="Generating...",
            project_slug=project_slug,
            generated_by=agent_team[0]["agent_id"] if agent_team else "system",
            job_id=job_id,
            status="generating",
        )
    except Exception as e:
        logger.error("Failed to create placeholder report: %s", e)

    if emit:
        emit("report_generating", job_id=job_id, title=title, report_id=rid)

    # Run all agents
    agent_results = []
    for agent_def in agent_team:
        agent_id = agent_def.get("agent_id", "")
        task = agent_def.get("task", "")
        project = agent_def.get("project", project_slug)
        ctx = agent_def.get("context", "") + ("\n\n" + extra_context if extra_context else "")
        if not agent_id or not task:
            continue
        logger.info("report_monitor: running agent=%s for job=%s", agent_id, job_id)
        result = run_agent(
            agent_id=agent_id,
            task=task,
            project=project,
            extra_context=ctx,
            emit=emit,
        )
        agent_results.append(result)

    # Synthesise all agent outputs into the final report content
    sections = [f"# {title}\n*Generated: {_now()}*\n"]

    for r in agent_results:
        agent_id = r.get("agent_id", "unknown")
        response = r.get("response", "")
        if response:
            sections.append(f"\n## {agent_id.replace('-', ' ').title()}\n{response}")
        if r.get("error"):
            sections.append(f"\n⚠️ **{agent_id} error:** {r['error']}")

    content = "\n".join(sections)

    # Build a brief summary from first agent's summary
    summaries = [r.get("summary", "") for r in agent_results if r.get("summary")]
    summary = summaries[0] if summaries else f"{title} generated with {len(agent_results)} agent(s)."

    total_db_writes = sum(r.get("db_writes_applied", 0) for r in agent_results)
    total_todos = sum(r.get("todos_created", 0) for r in agent_results)
    status = "complete" if not any(r.get("error") for r in agent_results) else "partial"

    # Update the report record
    try:
        db.update_report(rid,
                         content=content,
                         summary=summary,
                         status=status,
                         generated_by=",".join(r.get("agent_id","") for r in agent_results))
    except Exception as e:
        logger.error("Failed to update report %s: %s", rid, e)

    logger.info(
        "report_monitor: job=%s complete — %d agents, %d db_writes, %d todos, status=%s",
        job_id, len(agent_results), total_db_writes, total_todos, status,
    )

    if emit:
        emit("report_complete", job_id=job_id, report_id=rid, title=title, status=status)

    return {
        "report_id":   rid,
        "title":       title,
        "status":      status,
        "db_writes":   total_db_writes,
        "todos":       total_todos,
        "error":       None,
    }


async def run_report_job(
    job_id: str,
    emit: Callable | None = None,
    extra_context: str = "",
) -> dict[str, Any]:
    """Async wrapper — runs the sync report job in a thread to avoid blocking the event loop."""
    return await asyncio.to_thread(run_report_job_sync, job_id, emit, extra_context)


# ---------------------------------------------------------------------------
# Automation run monitor — checks automations table and dispatches overdue runs
# ---------------------------------------------------------------------------

def check_automation_schedules(emit: Callable | None = None) -> list[dict]:
    """
    Scan the automations table for active cron-triggered automations.
    Returns list of automation slugs that are due to run.
    Called by the scheduler every minute (or on demand).
    """
    if not DB_OK:
        return []

    due: list[dict] = []
    now = datetime.now(timezone.utc)

    try:
        autos = db.list_automations(status="active")
        for auto in autos:
            trigger_type = auto.get("trigger_type", "")
            if trigger_type not in ("schedule", "cron", "daily", "weekly"):
                continue
            # Parse next_run from trigger_config JSON
            config_raw = auto.get("trigger_config", "{}")
            try:
                config = json.loads(config_raw) if isinstance(config_raw, str) else config_raw
            except Exception:
                config = {}
            next_run_str = config.get("next_run", "")
            if not next_run_str:
                due.append(auto)  # No next_run set → treat as due
                continue
            try:
                next_run = datetime.fromisoformat(next_run_str.replace("Z", "+00:00"))
                if next_run.tzinfo is None:
                    next_run = next_run.replace(tzinfo=timezone.utc)
                if now >= next_run:
                    due.append(auto)
            except ValueError:
                due.append(auto)
    except Exception as e:
        logger.error("check_automation_schedules error: %s", e)

    return due


def dispatch_automation(auto: dict, emit: Callable | None = None) -> dict:
    """
    Dispatch agents for a single automation and save a report.
    The automation's agent_id and task come from the automations table.
    """
    job_id = f"automation_{auto.get('slug','unknown')}"
    agent_id = auto.get("agent_id", "")
    project = auto.get("project_slug", "")

    steps_raw = auto.get("steps", "[]")
    try:
        steps = json.loads(steps_raw) if isinstance(steps_raw, str) else steps_raw
    except Exception:
        steps = []

    task = (
        f"Execute automation '{auto.get('name','')}' for project '{project}'.\n"
        + (f"Steps:\n" + "\n".join(f"- {s}" for s in steps) if steps else "")
    )

    if not agent_id:
        return {"status": "skipped", "error": "No agent_id on automation"}

    # Run as a synthetic report job
    rid = str(uuid.uuid4())
    title = f"Automation: {auto.get('name','')} — {_today()}"
    try:
        db.create_report(
            id=rid,
            title=title,
            report_type="automation",
            content="",
            summary="Running...",
            project_slug=project,
            generated_by=agent_id,
            job_id=job_id,
            status="generating",
        )
    except Exception:
        pass

    result = run_agent(agent_id=agent_id, task=task, project=project, emit=emit)

    try:
        db.update_report(rid,
                         content=result.get("response", ""),
                         summary=result.get("summary", ""),
                         status="complete" if not result.get("error") else "failed")
        # Increment run_count on the automation
        db._record_automation_run(auto.get("id", ""), "complete" if not result.get("error") else "failed")
    except Exception:
        pass

    return {"report_id": rid, "status": "complete", "error": result.get("error")}
