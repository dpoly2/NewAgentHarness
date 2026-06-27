"""Scheduler API routes for ArchonHub.

Job lifecycle:
  POST   /api/scheduler           — create a new user-defined scheduled job
  GET    /api/scheduler           — list all jobs (built-in + user)
  DELETE /api/scheduler/{id}      — cancel and remove a job
  POST   /api/scheduler/{id}/trigger — fire a job immediately

Implementation notes:
  User jobs are created via HubScheduler.add_user_job() (not APScheduler directly).
  Triggering calls both HubScheduler.trigger_job() (to update scheduler state) and
  hub.submit_job() (to immediately queue the run).
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.database import _create_record, _get_record, _now_iso, _update_record
from core.hub import hub
from core.models import SchedulerJobCreate

router = APIRouter()


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
        "last_run": db_job.get("last_run_at"),
        "last_status": db_job.get("last_run_status"),
        "run_count": db_job.get("run_count", 0),
    }


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
    payload["id"] = job_id
    payload.setdefault("name", f"{body.agent_id}:{body.project}")

    # Validate trigger config before touching the scheduler
    if body.run_type == "interval":
        if not body.interval_sec or body.interval_sec <= 0:
            raise HTTPException(400, "interval_sec must be greater than zero")
    elif body.run_type == "cron":
        if not body.cron_expr:
            raise HTTPException(400, "cron_expr is required for cron jobs")
        if len(body.cron_expr.split()) != 5:
            raise HTTPException(400, "cron_expr must have 5 fields")
    else:
        raise HTTPException(400, "run_type must be 'cron' or 'interval'")

    try:
        hub._scheduler.add_user_job(payload)
    except Exception as exc:
        raise HTTPException(500, f"Unable to create job: {exc}") from exc

    # Retrieve next_fire from the scheduler's job list
    next_fire = None
    try:
        job_list = hub._scheduler.get_job_list()
        job_info = next((j for j in job_list if j.get("id") == job_id), {})
        next_fire = job_info.get("next_fire")
    except Exception:
        pass

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
            "next_fire": next_fire or "",
            "status": "active",
            "created_at": _now_iso(),
            "job_data": payload,
        },
        json_fields={"job_data"},
    )
    return {"id": job_id, "status": "scheduled", "next_fire": next_fire}


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

    # Use HubScheduler.trigger_job() so APScheduler state is updated correctly,
    # then also submit directly to the job queue for immediate execution.
    triggered_via_scheduler = False
    if hub._scheduler and hasattr(hub._scheduler, "trigger_job"):
        triggered_via_scheduler = hub._scheduler.trigger_job(id)

    # Always submit to the job queue directly for immediate background execution.
    payload = job.get("job_data") if isinstance(job.get("job_data"), dict) else job
    run_id = await hub.submit_job(
        {
            "agent_id": payload.get("agent_id", job.get("agent_id", "")),
            "project": payload.get("project", job.get("project", "")),
            "graph": payload.get("graph", "reflexion"),
            "task": payload.get("task", job.get("task", "")),
            "max_revisions": payload.get("max_revisions", 2),
            "priority": payload.get("priority", "normal"),
        }
    )
    await hub.broadcast({"type": "scheduler_triggered", "id": id, "run_id": run_id})
    return {"id": id, "run_id": run_id, "status": "triggered", "scheduler_updated": triggered_via_scheduler}
