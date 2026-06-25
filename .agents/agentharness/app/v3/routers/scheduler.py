from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.database import _create_record, _get_record, _now_iso, _update_record
from core.hub import hub
from core.models import SchedulerJobCreate

router = APIRouter()

def _scheduler_job_count() -> int:
    try:
        if not hub._scheduler:
            return 0
        # HubScheduler wraps APScheduler — use inner .scheduler.get_jobs()
        inner = getattr(hub._scheduler, "scheduler", hub._scheduler)
        return len(inner.get_jobs())
    except Exception:
        return 0


def _serialize_scheduler_job(job: Any) -> dict:
    from core.database import _get_record
    db_job = {}
    try:
        db_job = _get_record("scheduled_jobs", getattr(job, "id", "")) or {}
    except Exception:
        pass
    return {
        "id": getattr(job, "id", None),
        "name": getattr(job, "name", None),
        "next_fire": getattr(getattr(job, "next_run_time", None), "isoformat", lambda: None)(),
        "trigger": str(getattr(job, "trigger", "")),
        "last_run": db_job.get("last_run"),
        "last_status": db_job.get("last_status"),
        "run_count": db_job.get("run_count", 0),
    }

def _scheduler_trigger(job: SchedulerJobCreate):
    try:
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger
    except Exception as exc:
        raise HTTPException(500, f"APScheduler is unavailable: {exc}") from exc
    if job.run_type == "interval":
        if job.interval_sec <= 0:
            raise HTTPException(400, "interval_sec must be greater than zero")
        return IntervalTrigger(seconds=job.interval_sec)
    if job.run_type == "cron":
        if not job.cron_expr:
            raise HTTPException(400, "cron_expr is required for cron jobs")
        parts = job.cron_expr.split()
        if len(parts) != 5:
            raise HTTPException(400, "cron_expr must have 5 fields")
        return CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            timezone="America/Chicago",
        )
    raise HTTPException(400, "run_type must be 'cron' or 'interval'")


async def _fire_scheduled_job(job_id: str, payload: dict) -> str:
    run_id = await hub.submit_job(
        {
            "agent_id": payload["agent_id"],
            "project": payload.get("project", ""),
            "graph": payload.get("graph", "reflexion"),
            "task": payload["task"],
            "max_revisions": payload.get("max_revisions", 2),
            "priority": payload.get("priority", "normal"),
        }
    )
    await hub.broadcast({"type": "scheduler_triggered", "id": job_id, "run_id": run_id})
    return run_id

@router.get("/scheduler")
async def list_scheduler(current_user: dict = Depends(get_current_user)):
    del current_user
    if hub._scheduler and hasattr(hub._scheduler, "get_job_list"):
        return hub._scheduler.get_job_list()
    jobs = []
    if hub._scheduler:
        try:
            inner = getattr(hub._scheduler, "scheduler", hub._scheduler)
            jobs.extend(_serialize_scheduler_job(job) for job in inner.get_jobs())
        except Exception:
            pass
    return jobs


@router.post("/scheduler")
async def create_scheduler_job(body: SchedulerJobCreate, current_user: dict = Depends(get_current_user)):
    del current_user
    if not hub._scheduler:
        raise HTTPException(500, "Scheduler is not available")
    job_id = uuid.uuid4().hex
    payload = body.model_dump()
    trigger = _scheduler_trigger(body)

    async def _runner():
        await _fire_scheduled_job(job_id, payload)

    try:
        hub._scheduler.add_job(_runner, trigger=trigger, id=job_id, name=f"{body.agent_id}:{body.project}", replace_existing=True)
    except Exception as exc:
        raise HTTPException(500, f"Unable to create job: {exc}") from exc
    job = hub._scheduler.get_job(job_id)
    _create_record(
        "scheduled_jobs",
        {
            "id": job_id,
            "agent_id": body.agent_id,
            "project": body.project,
            "graph": body.graph,
            "task": body.task,
            "run_type": body.run_type,
            "cron_expr": body.cron_expr,
            "interval_sec": body.interval_sec,
            "scheduled_at": "",
            "next_fire": job.next_run_time.isoformat() if job and job.next_run_time else "",
            "status": "active",
            "created_at": _now_iso(),
            "job_data": payload,
        },
        json_fields={"job_data"},
    )
    return {"id": job_id, "status": "scheduled", "next_fire": job.next_run_time.isoformat() if job and job.next_run_time else None}


@router.delete("/scheduler/{id}")
async def delete_scheduler_job(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    if hub._scheduler:
        try:
            hub._scheduler.remove_job(id)
        except Exception:
            pass
    job = _update_record("scheduled_jobs", id, {"status": "cancelled"})
    if not job and not _get_record("scheduled_jobs", id):
        raise HTTPException(404, "Scheduled job not found")
    return {"id": id, "deleted": True}


@router.post("/scheduler/{id}/trigger")
async def trigger_scheduler_job(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    job = _get_record("scheduled_jobs", id, json_fields={"job_data"})
    if not job:
        raise HTTPException(404, "Scheduled job not found")
    payload = job.get("job_data") if isinstance(job.get("job_data"), dict) else job
    run_id = await _fire_scheduled_job(id, payload)
    return {"id": id, "run_id": run_id, "status": "triggered"}
