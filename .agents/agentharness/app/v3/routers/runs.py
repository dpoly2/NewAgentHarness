from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.auth import get_current_user
from core.database import _list_job_records, _list_runs, _update_job_record
from core.hub import hub
from core.models import RunRequest

router = APIRouter()

@router.post("/runs")
async def create_run(body: RunRequest, current_user: dict = Depends(get_current_user)):
    del current_user
    run_id = await hub.submit_job(body.model_dump())
    return {"run_id": run_id, "status": "queued"}


@router.get("/runs")
async def list_runs(
    limit: int = Query(50, ge=1, le=500),
    agent_id: Optional[str] = Query(default=None),
    project: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: dict = Depends(get_current_user),
):
    del current_user
    return _list_runs(limit=limit, agent_id=agent_id, project=project, status_filter=status_filter)


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    if not hub.cancel_run(run_id):
        raise HTTPException(404, "Run is not active")
    _update_job_record(run_id, "cancelled")
    await hub.broadcast({"type": "run_cancelled", "run_id": run_id})
    return {"run_id": run_id, "status": "cancelled"}


@router.get("/queue")
async def get_queue(current_user: dict = Depends(get_current_user)):
    del current_user
    queued = _list_job_records("queued")
    return queued if queued else []


@router.post("/queue/pause")
async def pause_queue(current_user: dict = Depends(get_current_user)):
    del current_user
    hub._queue_paused = True
    return {"status": "paused"}


@router.post("/queue/resume")
async def resume_queue(current_user: dict = Depends(get_current_user)):
    del current_user
    hub._queue_paused = False
    return {"status": "running"}
