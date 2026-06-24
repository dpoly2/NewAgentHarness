from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.database import _create_record, _delete_record, _get_record, _list_records, _now_iso, _update_record
from core.models import ClientCreate, ClientUpdate, ProjectCreate, ProjectUpdate

router = APIRouter()

@router.get("/projects")
async def list_projects(current_user: dict = Depends(get_current_user)):
    del current_user
    return _list_records("projects", order_by="updated_at DESC", json_fields={"tags"})


@router.post("/projects")
async def create_project(body: ProjectCreate, current_user: dict = Depends(get_current_user)):
    del current_user
    return _create_record(
        "projects",
        {
            "id": uuid.uuid4().hex,
            "slug": body.slug,
            "name": body.name,
            "description": body.description,
            "status": body.status,
            "lead_agent": body.lead_agent,
            "tags": body.tags,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        },
        json_fields={"tags"},
    )


@router.get("/projects/{id}")
async def get_project(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    project = _get_record("projects", id, json_fields={"tags"})
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.put("/projects/{id}")
async def update_project(id: str, body: ProjectUpdate, current_user: dict = Depends(get_current_user)):
    del current_user
    updates = {key: value for key, value in body.model_dump(exclude_unset=True).items()}
    updates["updated_at"] = _now_iso()
    project = _update_record("projects", id, updates, json_fields={"tags"})
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.delete("/projects/{id}")
async def delete_project(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    if not _delete_record("projects", id):
        raise HTTPException(404, "Project not found")
    return {"id": id, "deleted": True}


@router.get("/clients")
async def list_clients(current_user: dict = Depends(get_current_user)):
    del current_user
    return _list_records("clients", order_by="updated_at DESC")


@router.post("/clients")
async def create_client(body: ClientCreate, current_user: dict = Depends(get_current_user)):
    del current_user
    return _create_record(
        "clients",
        {
            "id": uuid.uuid4().hex,
            "slug": body.slug,
            "name": body.name,
            "business_type": body.business_type,
            "service": body.service,
            "contact_name": body.contact_name,
            "contact_email": body.contact_email,
            "engagement": body.engagement,
            "status": body.status,
            "project_slug": body.project_slug,
            "notes": body.notes,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        },
    )


@router.get("/clients/{id}")
async def get_client(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    client = _get_record("clients", id)
    if not client:
        raise HTTPException(404, "Client not found")
    return client


@router.put("/clients/{id}")
async def update_client(id: str, body: ClientUpdate, current_user: dict = Depends(get_current_user)):
    del current_user
    updates = {key: value for key, value in body.model_dump(exclude_unset=True).items()}
    updates["updated_at"] = _now_iso()
    client = _update_record("clients", id, updates)
    if not client:
        raise HTTPException(404, "Client not found")
    return client


@router.delete("/clients/{id}")
async def delete_client(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    if not _delete_record("clients", id):
        raise HTTPException(404, "Client not found")
    return {"id": id, "deleted": True}
