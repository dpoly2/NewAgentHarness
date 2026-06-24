from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.auth import get_current_user
from core.database import _create_record, _delete_record, _get_record, _list_records, _now_iso, _update_record
from core.hub import hub
from core.models import TodoCreate, TodoUpdate

router = APIRouter()

@router.get("/todos")
async def get_todos(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    project: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    del current_user
    where, params = [], []
    if status_filter:
        where.append("status = ?")
        params.append(status_filter)
    if project:
        where.append("project = ?")
        params.append(project)
    return _list_records("todos", where=where, params=params, order_by="updated_at DESC", json_fields={"tags"})


@router.post("/todos")
async def create_todo(body: TodoCreate, current_user: dict = Depends(get_current_user)):
    del current_user
    todo = _create_record(
        "todos",
        {
            "id": uuid.uuid4().hex,
            "title": body.title,
            "description": body.description,
            "priority": body.priority,
            "status": body.status,
            "project": body.project,
            "due_date": body.due_date,
            "tags": body.tags,
            "source": body.source,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        },
        json_fields={"tags"},
    )
    await hub.broadcast({"type": "todo_update", "action": "created", "todo": todo})
    return todo


@router.get("/todos/{id}")
async def get_todo(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    todo = _get_record("todos", id, json_fields={"tags"})
    if not todo:
        raise HTTPException(404, "Todo not found")
    return todo


@router.put("/todos/{id}")
async def update_todo(id: str, body: TodoUpdate, current_user: dict = Depends(get_current_user)):
    del current_user
    updates = {key: value for key, value in body.model_dump(exclude_unset=True).items()}
    updates["updated_at"] = _now_iso()
    todo = _update_record("todos", id, updates, json_fields={"tags"})
    if not todo:
        raise HTTPException(404, "Todo not found")
    await hub.broadcast({"type": "todo_update", "action": "updated", "todo": todo})
    return todo


@router.delete("/todos/{id}")
async def delete_todo(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    if not _delete_record("todos", id):
        raise HTTPException(404, "Todo not found")
    await hub.broadcast({"type": "todo_update", "action": "deleted", "todo": {"id": id}})
    return {"id": id, "deleted": True}
