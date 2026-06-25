from __future__ import annotations

import json
import sqlite3
import uuid

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.config import DB_PATH
from core.database import _create_record, _delete_record, _json_dumps, _json_loads, _list_records, _now_iso

try:
    from ah_logging import get_logger
except ImportError:
    import logging

    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("briefing")
router = APIRouter()

@router.get("/briefs")
async def list_briefs(current_user: dict = Depends(get_current_user)):
    del current_user
    briefs = _list_records("daily_briefs", order_by="created_at DESC")
    for brief in briefs:
        brief["content"] = _json_loads(brief.get("content"))
    return briefs


@router.post("/briefs")
async def create_brief(body: dict, current_user: dict = Depends(get_current_user)):
    del current_user
    content = body.get("content", body)
    brief = _create_record(
        "daily_briefs",
        {"id": uuid.uuid4().hex, "content": _json_dumps(content), "created_at": _now_iso()},
    )
    brief["content"] = _json_loads(brief.get("content"))
    return brief


@router.delete("/briefs/{id}")
async def delete_brief(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    if not _delete_record("daily_briefs", id):
        raise HTTPException(404, "Brief not found")
    return {"id": id, "deleted": True}

_MORNING_BRIEFS_DDL = """
    CREATE TABLE IF NOT EXISTS morning_briefs (
        brief_id   TEXT PRIMARY KEY,
        user_id    TEXT NOT NULL,
        brief_text TEXT NOT NULL,
        stats_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        viewed     BOOLEAN DEFAULT 0,
        viewed_at  TIMESTAMP
    )
"""


def _ensure_morning_briefs_table():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(_MORNING_BRIEFS_DDL)
        conn.commit()
    finally:
        conn.close()


@router.get("/briefing/morning")
async def get_morning_briefing(current_user: dict = Depends(get_current_user)):
    """Retrieve today's morning briefing (generate if none exists yet)."""
    return await _generate_or_fetch_brief(current_user, force=False)


@router.post("/briefing/morning")
async def generate_morning_briefing(current_user: dict = Depends(get_current_user)):
    """Force-regenerate today's morning briefing."""
    return await _generate_or_fetch_brief(current_user, force=True)


async def _generate_or_fetch_brief(current_user: dict, force: bool = False):
    try:
        user_id = current_user.get("username", "default_user")
        from morning_brief import MorningBriefAgent

        _ensure_morning_briefs_table()

        if not force:
            # Return cached brief for today if one exists
            conn = sqlite3.connect(str(DB_PATH))
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT brief_id, brief_text, stats_json, created_at
                    FROM morning_briefs
                    WHERE user_id = ? AND date(created_at) = date('now')
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "success": True,
                        "brief_id": row[0],
                        "brief_text": row[1],
                        "stats": json.loads(row[2]) if row[2] else {},
                        "created_at": row[3],
                        "cached": True,
                    }
            finally:
                conn.close()

        # Generate a fresh brief
        agent = MorningBriefAgent(DB_PATH)
        result = await agent.generate_brief(user_id)
        return {"success": True, "cached": False, **result}
    except Exception as e:
        logger.error(f"Morning briefing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/briefing/history")
async def get_briefing_history(limit: int = 30, current_user: dict = Depends(get_current_user)):
    """Get historical morning briefings."""
    try:
        user_id = current_user.get("username", "default_user")
        _ensure_morning_briefs_table()
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT brief_id, brief_text, stats_json, created_at, viewed
                FROM morning_briefs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            briefs = [dict(row) for row in cursor.fetchall()]
            
            return {
                "success": True,
                "briefs": briefs,
                "count": len(briefs)
            }
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Briefing history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
