"""
AgentHarness Hub — Scheduler
hub_scheduler.py

APScheduler-based always-on task runner.
Runs inside hub_server.py — fires agent jobs even when the desktop is closed.
All built-in jobs (grant sweep, daily report, etc.) are defined here.
"""

from __future__ import annotations
import json
import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from hub_db import (
    save_scheduled_job, list_scheduled_jobs, delete_scheduled_job,
    list_todos, agent_stats, get_briefing_cache, cache_briefing,
    save_notification, load_runs, DATA_DIR
)

if TYPE_CHECKING:
    from hub_server import HubServer

# ── Paths ─────────────────────────────────────────────────────────────────────
HERE        = Path(__file__).parent
AGENTS_ROOT = HERE.parent.parent.parent  # repo/.agents

# ── Timezone ──────────────────────────────────────────────────────────────────
CT_TZ = "America/Chicago"


# ════════════════════════════════════════════════════════════════════════════════
# BUILT-IN JOB FUNCTIONS
# These run on the Hub scheduler — no desktop needed.
# ════════════════════════════════════════════════════════════════════════════════

async def job_grant_research_sweep(hub: "HubServer"):
    """Weekly Monday 8:00 AM CT — Grant & funding research across all orgs."""
    print("[Scheduler] Firing: grant_research_sweep")
    save_notification("Scheduler: Grant research sweep started", "#60a5fa", "system")

    orgs = [
        ("grants-research-agent", "grants",   "Find new federal and state grant opportunities for Xtreme Force Track Club — focus on youth sports, Title I, and rural development programs"),
        ("yepc-grant-writer-agent","yepc",     "Research capital infrastructure grants for a 110-acre youth athletic complex in Hutto TX — focus on USDA, HUD, TX Parks & Wildlife, and economic development funds"),
        ("pbs-fundraising-agent",  "pbs",      "Find grants and funding opportunities for Psi Beta Sigma Collegiate Pathways Foundation — focus on 501c3 scholarship and mentorship programs"),
        ("solar-finance-agent",    "solar",    "Research solar industry grants, incentives, and programs available to Clarity Solar Services — focus on TX residential solar repair"),
    ]

    for agent_id, project, task in orgs:
        config = {
            "agent_id":      agent_id,
            "project":       project,
            "graph":         "research",
            "task":          task,
            "max_revisions": 1,
            "priority":      "normal",
        }
        await hub.submit_job(config)
        save_notification(f"Queued: {agent_id} grant sweep", "#60a5fa", "run")

    await hub.broadcast({"type": "notif", "text": "Weekly grant research sweep started (4 agents)", "color": "#60a5fa", "category": "system"})


async def job_daily_briefing_compute(hub: "HubServer"):
    """Daily 6:50 AM CT — Pre-compute morning briefing so it's ready at 7 AM."""
    print("[Scheduler] Firing: daily_briefing_compute")

    stats        = agent_stats()
    todos        = list_todos(status="pending")
    recent_runs  = load_runs(limit=50)
    all_runs     = load_runs(limit=500)

    total_runs    = len(all_runs)
    agents_total  = len(stats)
    passing       = [a for a, s in stats.items() if s["avg"] >= 0.75 and s["runs"] > 0]
    flagged       = [a for a, s in stats.items() if s["avg"] < 0.60 and s["runs"] > 0]
    last_24h      = [r for r in recent_runs if r.get("created_at","") >= datetime.now(timezone.utc).strftime("%Y-%m-%dT") ]

    urgent_todos  = [t for t in todos if t.get("priority") == "urgent"]
    high_todos    = [t for t in todos if t.get("priority") == "high"]

    flagged_details = [
        {"agent_id": a, "avg_score": stats[a]["avg"], "runs": stats[a]["runs"]}
        for a in flagged[:10]
    ]
    top_todos = sorted(
        todos,
        key=lambda t: {"urgent":0,"high":1,"medium":2,"low":3}.get(t.get("priority","low"), 3)
    )[:8]

    blockers = [
        "PBS site: Golf Tournament + Chapter Dues pages need payment links",
        "XFTC Gmail: forwarding rule required for signup logger",
        "Smith Capital LLC: reactivation filings overdue with TX Comptroller",
        "Clarity Solar: TX SB 1036 GL insurance deadline Sep 1, 2026",
        "Smith Capital Holdings LLC: S-Corp election (Form 2553) not yet filed",
        "AgentHarness Hub: Hub server not yet deployed as Windows Service",
    ]

    briefing = {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "total_runs":     total_runs,
        "agents_total":   agents_total,
        "passing_agents": len(passing),
        "flagged_agents": flagged,
        "flagged_details":flagged_details,
        "top_todos":      top_todos,
        "todos_pending":  len(todos),
        "urgent_todos":   len(urgent_todos),
        "high_todos":     len(high_todos),
        "blockers":       blockers,
        "last_24h_runs":  len(last_24h),
    }

    cache_briefing(briefing)
    await hub.broadcast({"type": "briefing_ready", "generated_at": briefing["generated_at"]})
    print(f"[Scheduler] Briefing cached — {agents_total} agents, {len(flagged)} flagged")


async def job_daily_reflexion_report(hub: "HubServer"):
    """Daily 7:00 AM CT — Generate and send reflexion digest."""
    print("[Scheduler] Firing: daily_reflexion_report")

    stats      = agent_stats()
    runs_today = load_runs(limit=200)
    now_str    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_runs = [r for r in runs_today if (r.get("created_at") or "")[:10] == now_str]

    flagged    = {a: s for a, s in stats.items() if s["avg"] < 0.75 and s["runs"] > 0}
    passing    = {a: s for a, s in stats.items() if s["avg"] >= 0.75 and s["runs"] > 0}

    lines = [
        f"# AgentHarness Daily Reflexion Report",
        f"**Date:** {now_str}",
        f"**Generated:** {datetime.now().strftime('%H:%M CT')}",
        "",
        "## Portfolio Summary",
        f"- Total agents tracked: {len(stats)}",
        f"- Agents passing (avg ≥ 0.75): {len(passing)}",
        f"- Agents flagged (avg < 0.75): {len(flagged)}",
        f"- Runs today: {len(today_runs)}",
        "",
    ]

    if flagged:
        lines += ["## Flagged Agents — Need Attention", ""]
        for agent, s in sorted(flagged.items(), key=lambda x: x[1]["avg"]):
            lines.append(f"- **{agent}** — avg score: {s['avg']:.2f} over {s['runs']} runs")
        lines.append("")

    if passing:
        lines += ["## Performing Well", ""]
        for agent, s in sorted(passing.items(), key=lambda x: -x[1]["avg"])[:10]:
            lines.append(f"- {agent} — avg: {s['avg']:.2f} ({s['runs']} runs)")
        lines.append("")

    if today_runs:
        lines += ["## Today's Runs", ""]
        for r in today_runs[:15]:
            icon = "✅" if (r.get("score") or 0) >= 0.75 else "⚠️"
            lines.append(f"- {icon} {r['agent_id']} ({r['project']}) — score: {r.get('score',0):.2f}")
        lines.append("")

    report_text = "\n".join(lines)

    # Write to log file
    log_path = DATA_DIR / "logs" / f"reflexion-{now_str}.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(report_text)

    save_notification("Daily reflexion report generated", "#92c353", "system")
    await hub.broadcast({
        "type":    "notif",
        "text":    f"Daily reflexion report ready — {len(flagged)} flagged, {len(passing)} passing",
        "color":   "#92c353",
        "category":"system"
    })
    print(f"[Scheduler] Reflexion report written to {log_path}")


async def job_sigma_signal_check(hub: "HubServer"):
    """Daily 2:00 PM CT — Check Sigma Signal submission inbox."""
    print("[Scheduler] Firing: sigma_signal_check")
    config = {
        "agent_id":      "sigma-signal-submissions",
        "project":       "sigma-signal",
        "graph":         "reflexion",
        "task":          "Check thesigmasignal.1stvp1914@gmail.com inbox for new newsletter submissions. Log what was received, from whom, and what section it belongs to (Chapter Spotlight, Poem, Trivia, Tips, News). Notify David of new submissions.",
        "max_revisions": 0,
        "priority":      "low",
    }
    await hub.submit_job(config)
    save_notification("Sigma Signal: submission check queued", "#60a5fa", "run")


async def job_weekly_fare_alert(hub: "HubServer"):
    """Monday 1:30 PM CT — Search for travel fare deals."""
    print("[Scheduler] Firing: weekly_fare_alert")
    config = {
        "agent_id":      "travel-project-lead",
        "project":       "travel",
        "graph":         "research",
        "task":          "Search Google Flights and Kayak for the best current fares on David's frequent routes from AUS (Austin): ATL, DFW, IAH, ORD, LAX. Flag any fares under $200 one-way or $400 round trip. Check for price drops on the AUS-ATL route (outbound Jun 2, return Jun 7). Compile weekly digest with top deals and cheapest travel days.",
        "max_revisions": 0,
        "priority":      "low",
    }
    await hub.submit_job(config)
    save_notification("Travel: weekly fare alert queued", "#60a5fa", "run")


async def job_hutto_planning_monitor(hub: "HubServer"):
    """Weekly Monday 8:30 AM CT — Monitor Hutto City Council / Williamson County for CR 132 updates."""
    print("[Scheduler] Firing: hutto_planning_monitor")
    config = {
        "agent_id":      "yepc-project-manager",
        "project":       "yepc",
        "graph":         "research",
        "task":          "Monitor Hutto City Council agendas and Williamson County planning commission for any updates related to CR 132, SH-130 corridor development, zoning changes, or infrastructure projects near the YEPC 110-acre site. Report any new agenda items, approved permits, or public notices.",
        "max_revisions": 0,
        "priority":      "normal",
    }
    await hub.submit_job(config)
    save_notification("YEPC: Hutto planning monitor queued", "#60a5fa", "run")


async def job_nightly_db_cleanup(hub: "HubServer"):
    """Daily 2:00 AM CT — Remove runs older than 90 days."""
    print("[Scheduler] Firing: nightly_db_cleanup")
    from hub_db import get_db
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    conn = get_db()
    cur  = conn.execute("DELETE FROM runs WHERE created_at < ?", (cutoff,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    if deleted:
        save_notification(f"DB cleanup: removed {deleted} runs older than 90 days", "#f59e0b", "system")
    print(f"[Scheduler] DB cleanup: removed {deleted} old runs")


# ════════════════════════════════════════════════════════════════════════════════
# SCHEDULER SETUP
# ════════════════════════════════════════════════════════════════════════════════

def build_scheduler(hub: "HubServer") -> AsyncIOScheduler:
    """
    Create and configure the APScheduler instance with all built-in jobs.
    Returns a configured (but not yet started) AsyncIOScheduler.
    """
    scheduler = AsyncIOScheduler(timezone=CT_TZ)

    # ── Built-in jobs ─────────────────────────────────────────────────────────

    # Daily briefing pre-compute — 6:50 AM CT (ready before David opens app at 7)
    scheduler.add_job(
        job_daily_briefing_compute, CronTrigger(hour=6, minute=50, timezone=CT_TZ),
        id="daily_briefing", name="Daily Briefing Pre-compute",
        args=[hub], replace_existing=True
    )

    # Daily reflexion report — 7:00 AM CT
    scheduler.add_job(
        job_daily_reflexion_report, CronTrigger(hour=7, minute=0, timezone=CT_TZ),
        id="daily_reflexion", name="Daily Reflexion Report",
        args=[hub], replace_existing=True
    )

    # Weekly grant research sweep — Monday 8:00 AM CT
    scheduler.add_job(
        job_grant_research_sweep, CronTrigger(day_of_week="mon", hour=8, minute=0, timezone=CT_TZ),
        id="grant_research_sweep", name="Weekly Grant Research Sweep",
        args=[hub], replace_existing=True
    )

    # Hutto planning monitor — Monday 8:30 AM CT
    scheduler.add_job(
        job_hutto_planning_monitor, CronTrigger(day_of_week="mon", hour=8, minute=30, timezone=CT_TZ),
        id="hutto_planning_monitor", name="Hutto/YEPC Planning Monitor",
        args=[hub], replace_existing=True
    )

    # Weekly fare alert — Monday 1:30 PM CT
    scheduler.add_job(
        job_weekly_fare_alert, CronTrigger(day_of_week="mon", hour=13, minute=30, timezone=CT_TZ),
        id="weekly_fare_alert", name="Weekly Travel Fare Alert",
        args=[hub], replace_existing=True
    )

    # Sigma Signal submission check — daily 2:00 PM CT
    scheduler.add_job(
        job_sigma_signal_check, CronTrigger(hour=14, minute=0, timezone=CT_TZ),
        id="sigma_signal_check", name="Sigma Signal Submission Check",
        args=[hub], replace_existing=True
    )

    # Nightly DB cleanup — 2:00 AM CT
    scheduler.add_job(
        job_nightly_db_cleanup, CronTrigger(hour=2, minute=0, timezone=CT_TZ),
        id="nightly_db_cleanup", name="Nightly DB Cleanup (90-day)",
        args=[hub], replace_existing=True
    )

    print(f"[Scheduler] {len(scheduler.get_jobs())} built-in jobs registered")
    return scheduler


def get_job_list(scheduler: AsyncIOScheduler) -> list:
    """Return serializable list of all scheduled jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id":        job.id,
            "name":      job.name,
            "trigger":   str(job.trigger),
            "next_fire": next_run.isoformat() if next_run else None,
            "status":    "active" if next_run else "paused",
        })
    return jobs
