from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.auth import get_current_user
from core.database import _db_connection, _list_records, _row_to_dict, db

router = APIRouter()

@router.get("/search")
async def search_conversations(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    current_user: dict = Depends(get_current_user)
):
    """
    Full-text search across all conversations and messages.
    Uses FTS5 index for fast keyword search.
    """
    del current_user
    
    if not q or len(q.strip()) < 2:
        raise HTTPException(400, "Search query must be at least 2 characters")
    
    conn = _db_connection()
    try:
        # Check if FTS5 index exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts'"
        )
        if not cursor.fetchone():
            raise HTTPException(500, "Search index not available. Run add_fts_search.py to enable search.")
        
        # Search messages using FTS5
        # Escape query for FTS5 by wrapping in quotes if it contains special chars
        search_query = f'"{q.strip()}"' if any(c in q for c in [':', '-', '*', '"']) else q.strip()
        
        cursor = conn.execute("""
            SELECT 
                m.id,
                m.conversation_id,
                m.role,
                m.content,
                m.created_at,
                c.title as conversation_title,
                c.slug as conversation_slug
            FROM messages m
            INNER JOIN conversations c ON m.conversation_id = c.id
            WHERE m.rowid IN (
                SELECT rowid FROM messages_fts WHERE messages_fts MATCH ?
            )
            ORDER BY m.created_at DESC
            LIMIT ?
        """, (search_query, limit))
        
        results = []
        for row in cursor.fetchall():
            # Create excerpt with keyword highlighted context
            content = row['content']
            query_lower = q.lower()
            content_lower = content.lower()
            
            # Find first occurrence of query
            idx = content_lower.find(query_lower)
            if idx == -1:
                # Fallback: just take first 200 chars
                excerpt = content[:200]
            else:
                # Extract context around match (±100 chars)
                start = max(0, idx - 100)
                end = min(len(content), idx + len(q) + 100)
                excerpt = content[start:end]
                if start > 0:
                    excerpt = "..." + excerpt
                if end < len(content):
                    excerpt = excerpt + "..."
            
            results.append({
                "message_id": row['id'],
                "conversation_id": row['conversation_id'],
                "conversation_title": row['conversation_title'],
                "conversation_slug": row['conversation_slug'],
                "role": row['role'],
                "excerpt": excerpt,
                "created_at": row['created_at'],
            })
        
        return {
            "query": q,
            "count": len(results),
            "results": results
        }
    finally:
        conn.close()

@router.get("/events")
async def list_events(
    event_type: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    del current_user
    where, params = [], []
    if event_type:
        where.append("event_type = ?"); params.append(event_type)
    if level:
        where.append("level = ?"); params.append(level)
    return _list_records("events_log", where=where or None, params=params or None,
                          order_by="created_at DESC", limit=limit, json_fields={"detail"})


# ── Context / Memory ───────────────────────────────────────────────────────

@router.get("/context")
async def get_full_context(current_user: dict = Depends(get_current_user)):
    """Return complete portfolio context — agents, projects, clients, automations, todos."""
    del current_user
    if db and hasattr(db, "get_full_context"):
        try:
            return db.get_full_context()  # type: ignore[attr-defined]
        except Exception:
            pass
    return {
        "projects": _list_records("projects", order_by="name ASC", json_fields={"tags"}),
        "clients": _list_records("clients", order_by="name ASC"),
        "agents": _list_records("agent_registry", where=["status = ?"], params=["active"],
                                 order_by="project_slug ASC, name ASC",
                                 json_fields={"capabilities", "integrations", "config", "metadata"}),
        "automations": _list_records("automations", where=["status = ?"], params=["active"],
                                      order_by="name ASC", json_fields={"trigger_config", "steps"}),
        "todos": _list_records("todos",
                                where=["status IN ('pending','in_progress')"], params=[],
                                order_by="created_at DESC"),
    }
