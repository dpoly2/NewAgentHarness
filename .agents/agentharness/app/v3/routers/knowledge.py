from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_admin_user, get_current_user
from core.database import _create_record, _db_connection, _delete_record, _get_record, _list_records, _now_iso, _row_to_dict, _update_record
from core.models import DocumentCreate, DocumentUpdate, IntegrationUpsert, KnowledgeCreate, KnowledgeUpdate

router = APIRouter()

# ── Knowledge Base ─────────────────────────────────────────────────────────

_KB_JSON = {"tags"}

@router.get("/knowledge")
async def list_knowledge(
    category: Optional[str] = None,
    project_slug: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    del current_user
    if q:
        like = f"%{q}%"
        conn = _db_connection()
        try:
            where = "is_active = 1 AND (title LIKE ? OR content LIKE ?)"
            params_q: list[Any] = [like, like]
            if category:
                where += " AND category = ?"; params_q.append(category)
            if project_slug:
                where += " AND project_slug = ?"; params_q.append(project_slug)
            rows = conn.execute(
                f"SELECT * FROM knowledge_base WHERE {where} ORDER BY updated_at DESC LIMIT ?",
                params_q + [limit],
            ).fetchall()
            return [_row_to_dict(r, _KB_JSON) for r in rows]
        finally:
            conn.close()
    where_l, params_l = ["is_active = 1"], []
    if category:
        where_l.append("category = ?"); params_l.append(category)
    if project_slug:
        where_l.append("project_slug = ?"); params_l.append(project_slug)
    return _list_records("knowledge_base", where=where_l, params=params_l,
                          order_by="updated_at DESC", limit=limit, json_fields=_KB_JSON)

@router.post("/knowledge")
async def create_knowledge(body: KnowledgeCreate, current_user: dict = Depends(get_current_user)):
    del current_user
    now = _now_iso()
    return _create_record("knowledge_base", {
        "id": uuid.uuid4().hex,
        "title": body.title, "content": body.content,
        "source": body.source, "source_type": body.source_type,
        "category": body.category, "tags": body.tags,
        "project_slug": body.project_slug, "agent_id": body.agent_id,
        "is_active": 1, "created_at": now, "updated_at": now,
    }, json_fields=_KB_JSON)

@router.get("/knowledge/{id}")
async def get_knowledge(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    rec = _get_record("knowledge_base", id, json_fields=_KB_JSON)
    if not rec:
        raise HTTPException(404, "Knowledge entry not found")
    return rec

@router.put("/knowledge/{id}")
async def update_knowledge(id: str, body: KnowledgeUpdate, current_user: dict = Depends(get_current_user)):
    del current_user
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    updates["updated_at"] = _now_iso()
    if "is_active" in updates:
        updates["is_active"] = 1 if updates["is_active"] else 0
    rec = _update_record("knowledge_base", id, updates, json_fields=_KB_JSON)
    if not rec:
        raise HTTPException(404, "Knowledge entry not found")
    return rec

@router.delete("/knowledge/{id}")
async def delete_knowledge(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    if not _delete_record("knowledge_base", id):
        raise HTTPException(404, "Knowledge entry not found")
    return {"id": id, "deleted": True}


# ── Documents ──────────────────────────────────────────────────────────────

_DOC_JSON = {"tags"}

@router.get("/documents")
async def list_documents(
    project_slug: Optional[str] = None,
    doc_type: Optional[str] = None,
    client_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    del current_user
    where, params = [], []
    if project_slug:
        where.append("project_slug = ?"); params.append(project_slug)
    if doc_type:
        where.append("doc_type = ?"); params.append(doc_type)
    if client_id:
        where.append("client_id = ?"); params.append(client_id)
    return _list_records("documents", where=where or None, params=params or None,
                          order_by="updated_at DESC", json_fields=_DOC_JSON)

@router.post("/documents")
async def create_document(body: DocumentCreate, current_user: dict = Depends(get_current_user)):
    del current_user
    now = _now_iso()
    return _create_record("documents", {
        "id": uuid.uuid4().hex,
        "title": body.title, "doc_type": body.doc_type,
        "content": body.content, "format": body.format,
        "project_slug": body.project_slug, "client_id": body.client_id,
        "tags": body.tags, "created_by": body.created_by,
        "version": 1, "status": "draft",
        "created_at": now, "updated_at": now,
    }, json_fields=_DOC_JSON)

@router.get("/documents/{id}")
async def get_document(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    rec = _get_record("documents", id, json_fields=_DOC_JSON)
    if not rec:
        raise HTTPException(404, "Document not found")
    return rec

@router.put("/documents/{id}")
async def update_document(id: str, body: DocumentUpdate, current_user: dict = Depends(get_current_user)):
    del current_user
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    updates["updated_at"] = _now_iso()
    rec = _update_record("documents", id, updates, json_fields=_DOC_JSON)
    if not rec:
        raise HTTPException(404, "Document not found")
    return rec

@router.delete("/documents/{id}")
async def delete_document_ep(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    if not _delete_record("documents", id):
        raise HTTPException(404, "Document not found")
    return {"id": id, "deleted": True}


# ── Integrations ───────────────────────────────────────────────────────────

_INT_JSON = {"credentials", "metadata"}

@router.get("/integrations")
async def list_integrations(
    provider: Optional[str] = None,
    entity_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    del current_user
    where, params = [], []
    if provider:
        where.append("provider = ?"); params.append(provider)
    if entity_type:
        where.append("entity_type = ?"); params.append(entity_type)
    recs = _list_records("integrations", where=where or None, params=params or None,
                          order_by="updated_at DESC", json_fields=_INT_JSON)
    # Strip credential values from list response
    for r in recs:
        if "credentials" in r and isinstance(r["credentials"], dict):
            r["credentials"] = {k: "***" for k in r["credentials"]}
    return recs

@router.post("/integrations")
async def upsert_integration(body: IntegrationUpsert, current_user: dict = Depends(get_current_user)):
    del current_user
    now = _now_iso()
    return _create_record("integrations", {
        "id": uuid.uuid4().hex,
        "name": body.name, "provider": body.provider,
        "entity_type": body.entity_type, "entity_id": body.entity_id,
        "auth_type": body.auth_type, "credentials": body.credentials,
        "scope": body.scope, "status": body.status,
        "metadata": body.metadata, "created_at": now, "updated_at": now,
    }, json_fields=_INT_JSON)

@router.get("/integrations/{id}")
async def get_integration(id: str, admin_user: dict = Depends(get_admin_user)):
    del admin_user
    rec = _get_record("integrations", id, json_fields=_INT_JSON)
    if not rec:
        raise HTTPException(404, "Integration not found")
    return rec

@router.delete("/integrations/{id}")
async def delete_integration(id: str, admin_user: dict = Depends(get_admin_user)):
    del admin_user
    if not _delete_record("integrations", id):
        raise HTTPException(404, "Integration not found")
    return {"id": id, "deleted": True}
