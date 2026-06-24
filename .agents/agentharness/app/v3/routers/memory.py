from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.database import _memory_dict, _upsert_memory
from core.models import MemoryFactBody, MemoryUpdate

router = APIRouter()


# ── Per-agent memory ──────────────────────────────────────────────────────────

@router.get("/memory/agents/{agent_id}")
async def get_memory(agent_id: str, _: dict = Depends(get_current_user)):
    return {"agent_id": agent_id, "data": _memory_dict(agent_id)}


@router.put("/memory/agents/{agent_id}")
async def update_memory(agent_id: str, body: MemoryUpdate, _: dict = Depends(get_current_user)):
    return {"agent_id": agent_id, "data": _upsert_memory(agent_id, body.data)}


# ── Global memory ─────────────────────────────────────────────────────────────

@router.get("/memory/global")
async def list_global_memory(
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    _: dict = Depends(get_current_user),
):
    try:
        import global_memory as gm
        facts = gm.list_facts(category=category, limit=limit, offset=offset)
        counts = gm.count_facts()
        return {"success": True, "facts": facts, "counts": counts, "categories": list(gm.CATEGORIES.keys())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/global/search")
async def search_global_memory(q: str, _: dict = Depends(get_current_user)):
    try:
        import global_memory as gm
        results = gm.search_facts(q)
        return {"success": True, "results": results, "query": q}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/global")
async def create_global_memory_fact(body: MemoryFactBody, _: dict = Depends(get_current_user)):
    try:
        import global_memory as gm
        result = gm.upsert_fact(
            category=body.category,
            key=body.key,
            value=body.value,
            source=body.source,
            confidence=body.confidence,
            importance=body.importance,
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return {"success": True, "fact": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/memory/global/{fact_id}")
async def update_global_memory_fact(fact_id: str, body: MemoryFactBody, _: dict = Depends(get_current_user)):
    try:
        import global_memory as gm
        result = gm.upsert_fact(
            category=body.category,
            key=body.key,
            value=body.value,
            source=body.source,
            confidence=body.confidence,
            importance=body.importance,
            fact_id=fact_id,
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return {"success": True, "fact": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/global/{fact_id}")
async def delete_global_memory_fact(fact_id: str, _: dict = Depends(get_current_user)):
    try:
        import global_memory as gm
        success = gm.delete_fact(fact_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/global/extract")
async def extract_memory_from_conversation(body: dict, _: dict = Depends(get_current_user)):
    try:
        import global_memory as gm
        user_msg = body.get("user_message", "")
        agent_resp = body.get("agent_response", "")
        if not user_msg:
            raise HTTPException(status_code=400, detail="user_message required")
        stored = gm.extract_and_store(user_msg, agent_resp, source="agent_learned")
        return {"success": True, "extracted": len(stored), "facts": stored}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))







