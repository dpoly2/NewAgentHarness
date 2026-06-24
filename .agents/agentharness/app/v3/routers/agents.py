from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.config import DB_PATH
from core.database import _db_connection, _filter_record, _list_records, _now_iso
from core.models import AgentUpdate, AgentUpsert

try:
    from ah_logging import get_logger
except ImportError:
    import logging

    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("agents")
router = APIRouter()

_AGENT_JSON = {"capabilities", "integrations", "config", "metadata"}

@router.get("/agents")
async def list_agents_endpoint(
    project_slug: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    del current_user
    where, params = [], []
    if project_slug:
        where.append("project_slug = ?"); params.append(project_slug)
    if type:
        where.append("type = ?"); params.append(type)
    if status:
        where.append("status = ?"); params.append(status)
    return _list_records("agent_registry", where=where or None, params=params or None,
                          order_by="project_slug ASC, name ASC", json_fields=_AGENT_JSON)

@router.post("/agents")
async def upsert_agent_endpoint(body: AgentUpsert, current_user: dict = Depends(get_current_user)):
    del current_user
    now = _now_iso()
    data = {
        "id": uuid.uuid4().hex,
        "agent_id": body.agent_id,
        "name": body.name,
        "type": body.type,
        "role": body.role,
        "description": body.description,
        "project_slug": body.project_slug,
        "capabilities": body.capabilities,
        "integrations": body.integrations,
        "status": body.status,
        "system_prompt": body.system_prompt,
        "config": body.config,
        "metadata": body.metadata,
        "created_at": now,
        "updated_at": now,
    }
    conn = _db_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM agent_registry WHERE agent_id = ?", (body.agent_id,)
        ).fetchone()
        if existing:
            data.pop("id"); data.pop("created_at")
            data["updated_at"] = now
            payload = _filter_record("agent_registry", data, _AGENT_JSON)
            cols = ", ".join(f"{c} = ?" for c in payload)
            conn.execute(
                f"UPDATE agent_registry SET {cols} WHERE agent_id = ?",
                list(payload.values()) + [body.agent_id],
            )
        else:
            payload = _filter_record("agent_registry", data, _AGENT_JSON)
            cols = list(payload.keys())
            conn.execute(
                f"INSERT INTO agent_registry ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
                [payload[c] for c in cols],
            )
        conn.commit()
    finally:
        conn.close()
    return _list_records("agent_registry", where=["agent_id = ?"], params=[body.agent_id],
                          json_fields=_AGENT_JSON)[0]

@router.get("/agents/{agent_id}")
async def get_agent_endpoint(agent_id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    rec = _list_records("agent_registry", where=["agent_id = ?"], params=[agent_id],
                         json_fields=_AGENT_JSON)
    if not rec:
        raise HTTPException(404, "Agent not found")
    return rec[0]

@router.put("/agents/{agent_id}")
async def update_agent_endpoint(agent_id: str, body: AgentUpdate, current_user: dict = Depends(get_current_user)):
    del current_user
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    updates["updated_at"] = _now_iso()
    conn = _db_connection()
    try:
        payload = _filter_record("agent_registry", updates, _AGENT_JSON)
        if payload:
            cols = ", ".join(f"{c} = ?" for c in payload)
            conn.execute(
                f"UPDATE agent_registry SET {cols} WHERE agent_id = ?",
                list(payload.values()) + [agent_id],
            )
            conn.commit()
    finally:
        conn.close()
    recs = _list_records("agent_registry", where=["agent_id = ?"], params=[agent_id],
                          json_fields=_AGENT_JSON)
    if not recs:
        raise HTTPException(404, "Agent not found")
    return recs[0]

@router.post("/agents/collaborate")
async def agent_collaboration(request: dict, current_user: dict = Depends(get_current_user)):
    """Orchestrate multi-agent collaboration on a task."""
    try:
        from agent_orchestrator import AgentOrchestrator
        
        query = request.get('query')
        user_id = current_user.get("username", "default_user")
        agents = request.get('agents')  # Optional: explicit agent list
        
        if not query:
            raise HTTPException(status_code=400, detail="Query required")
        
        orchestrator = AgentOrchestrator(DB_PATH)
        result = await orchestrator.orchestrate_collaboration(
            user_id=user_id,
            query=query,
            explicit_agents=agents
        )
        
        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent collaboration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/capabilities")
async def get_agent_capabilities(agent_name: Optional[str] = None, _: dict = Depends(get_current_user)):
    """Get agent capabilities."""
    try:
        from agent_orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator(DB_PATH)
        capabilities = orchestrator.get_agent_capabilities(agent_name)
        
        return {
            "success": True,
            "agents": capabilities,
            "count": len(capabilities)
        }
    except Exception as e:
        logger.error(f"Get capabilities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/conversations/{conversation_id}")
async def get_conversation_history(conversation_id: str, _: dict = Depends(get_current_user)):
    """Get agent conversation history."""
    try:
        from agent_orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator(DB_PATH)
        history = orchestrator.get_conversation_history(conversation_id)
        
        return {
            "success": True,
            "conversation": history
        }
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
