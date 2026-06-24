from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.database import _create_record, _delete_record, _get_record, _list_records, _now_iso, _update_record
from core.models import AutomationCreate, AutomationDocCreate, AutomationUpdate

router = APIRouter()

_AUTO_JSON = {"trigger_config", "steps", "metadata"}

@router.get("/automations")
async def list_automations(
    project_slug: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    del current_user
    where, params = [], []
    if project_slug:
        where.append("project_slug = ?"); params.append(project_slug)
    if status:
        where.append("status = ?"); params.append(status)
    return _list_records("automations", where=where or None, params=params or None,
                          order_by="updated_at DESC", json_fields=_AUTO_JSON)

@router.post("/automations")
async def create_automation(body: AutomationCreate, current_user: dict = Depends(get_current_user)):
    del current_user
    now = _now_iso()
    return _create_record("automations", {
        "id": uuid.uuid4().hex,
        "slug": body.slug, "name": body.name,
        "description": body.description, "project_slug": body.project_slug,
        "agent_id": body.agent_id, "trigger_type": body.trigger_type,
        "trigger_config": body.trigger_config, "steps": body.steps,
        "status": body.status, "run_count": 0,
        "created_at": now, "updated_at": now,
    }, json_fields=_AUTO_JSON)

@router.get("/automations/{id}")
async def get_automation(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    rec = _get_record("automations", id, json_fields=_AUTO_JSON)
    if not rec:
        raise HTTPException(404, "Automation not found")
    return rec

@router.put("/automations/{id}")
async def update_automation(id: str, body: AutomationUpdate, current_user: dict = Depends(get_current_user)):
    del current_user
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    updates["updated_at"] = _now_iso()
    rec = _update_record("automations", id, updates, json_fields=_AUTO_JSON)
    if not rec:
        raise HTTPException(404, "Automation not found")
    return rec

@router.delete("/automations/{id}")
async def delete_automation(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    if not _delete_record("automations", id):
        raise HTTPException(404, "Automation not found")
    return {"id": id, "deleted": True}

@router.post("/automations/{id}/trigger")
async def trigger_automation(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    auto = _get_record("automations", id, json_fields=_AUTO_JSON)
    if not auto:
        raise HTTPException(404, "Automation not found")
    run_id = uuid.uuid4().hex
    now = _now_iso()
    _create_record("automation_runs", {
        "id": run_id, "automation_id": id,
        "automation_slug": auto.get("slug", ""),
        "triggered_by": "manual", "status": "running",
        "started_at": now,
    })
    _update_record("automations", id, {"last_run_at": now, "last_run_status": "running"})
    return {"run_id": run_id, "automation_id": id, "status": "running"}

@router.get("/automations/{id}/runs")
async def list_automation_runs(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    return _list_records("automation_runs", where=["automation_id = ?"], params=[id],
                          order_by="started_at DESC", json_fields={"metadata"})

@router.get("/automations/{id}/documents")
async def list_automation_docs(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    return _list_records("automation_documents", where=["automation_id = ?"], params=[id],
                          order_by="created_at DESC")

@router.post("/automations/{id}/documents")
async def create_automation_doc(id: str, body: AutomationDocCreate, current_user: dict = Depends(get_current_user)):
    del current_user
    now = _now_iso()
    return _create_record("automation_documents", {
        "id": uuid.uuid4().hex,
        "automation_id": id,
        "run_id": body.run_id, "title": body.title,
        "doc_type": body.doc_type, "content": body.content,
        "status": body.status, "reviewed_by": body.reviewed_by,
        "review_notes": body.review_notes,
        "created_at": now, "updated_at": now,
    })
