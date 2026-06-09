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
    from hub_db import save_notification, list_scheduled_jobs, update_scheduled_job
except Exception:
    save_notification = None
    list_scheduled_jobs = None
    update_scheduled_job = None

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
    ("daily_briefing", "Daily Briefing", {"hour": 6, "minute": 50}, "Compute morning briefing"),
    ("daily_reflexion", "Daily Reflexion", {"hour": 7, "minute": 0}, "Daily reflexion report"),
    ("grant_research_sweep", "Grant Research Sweep", {"day_of_week": "mon", "hour": 8, "minute": 0}, "Grant research across 4 orgs"),
    ("hutto_planning_monitor", "Hutto Planning Monitor", {"day_of_week": "mon", "hour": 8, "minute": 30}, "Hutto city planning monitor"),
    ("weekly_fare_alert", "Weekly Fare Alert", {"day_of_week": "mon", "hour": 13, "minute": 30}, "Travel fare alerts from AUS"),
    ("sigma_signal_check", "Sigma Signal Check", {"hour": 14, "minute": 0}, "Sigma Signal inbox check"),
    ("nightly_db_cleanup", "Nightly DB Cleanup", {"hour": 2, "minute": 0}, "Remove runs older than 90 days"),
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
        "agent_id": "grants-research-agent",
        "project": "archonhub",
        "graph": "reflexion",
        "task": "Generate a comprehensive daily briefing covering all portfolio projects, pending todos, active runs, and key priorities for today.",
    }
    await _submit_via_hub(hub, config, logger, "Daily briefing computed")


async def job_daily_reflexion_report(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "finance-cfo",
        "project": "smithcap-finance",
        "graph": "reflexion",
        "task": "Generate daily reflexion report: review yesterday's agent runs, identify patterns, flag issues, suggest improvements.",
    }
    await _submit_via_hub(hub, config, logger, "Daily reflexion report queued")


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


async def job_hutto_planning_monitor(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "yepc-project-manager",
        "project": "yepc",
        "graph": "research",
        "task": "Monitor Hutto TX city and county planning commission agendas, new developments, zoning changes, and real estate opportunities relevant to YEPC mission.",
    }
    await _submit_via_hub(hub, config, logger, "Hutto planning monitor queued")


async def job_weekly_fare_alert(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "finance-advisor",
        "project": "travel",
        "graph": "research",
        "task": "Research current travel fare deals from Austin-Bergstrom (AUS) airport. Find best deals for upcoming 60 days. Include airlines, prices, and booking links.",
    }
    await _submit_via_hub(hub, config, logger, "Weekly fare alert queued")


async def job_sigma_signal_check(hub):
    logger = get_logger("scheduler")
    config = {
        "agent_id": "sigma-signal-writer",
        "project": "sigma-signal",
        "graph": "reflexion",
        "task": "Check and process Sigma Signal newsletter submission inbox. Review pending submissions, draft responses, prepare content pipeline update.",
    }
    await _submit_via_hub(hub, config, logger, "Sigma Signal check queued")


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
        """Register all 7 built-in jobs"""
        if CronTrigger is None:
            raise RuntimeError("APScheduler CronTrigger is not available")

        tz = _get_timezone()
        job_specs = {
            "daily_briefing": (job_daily_briefing_compute, "Daily Briefing", {"hour": 6, "minute": 50}),
            "daily_reflexion": (job_daily_reflexion_report, "Daily Reflexion", {"hour": 7, "minute": 0}),
            "grant_research_sweep": (job_grant_research_sweep, "Grant Research Sweep", {"day_of_week": "mon", "hour": 8, "minute": 0}),
            "hutto_planning_monitor": (job_hutto_planning_monitor, "Hutto Planning Monitor", {"day_of_week": "mon", "hour": 8, "minute": 30}),
            "weekly_fare_alert": (job_weekly_fare_alert, "Weekly Fare Alert", {"day_of_week": "mon", "hour": 13, "minute": 30}),
            "sigma_signal_check": (job_sigma_signal_check, "Sigma Signal Check", {"hour": 14, "minute": 0}),
            "nightly_db_cleanup": (job_nightly_db_cleanup, "Nightly DB Cleanup", {"hour": 2, "minute": 0}),
        }

        for job_id, (func, name, cron_kwargs) in job_specs.items():
            trigger = CronTrigger(timezone=tz, **cron_kwargs)
            self.scheduler.add_job(
                func,
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
            _run_user_job,
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
