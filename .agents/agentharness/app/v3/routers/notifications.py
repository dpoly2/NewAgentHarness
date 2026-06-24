from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.auth import get_current_user
from core.config import DB_PATH
from core.database import _db_connection, _list_records

try:
    from ah_logging import get_logger
except ImportError:
    import logging

    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("notifications")
router = APIRouter()

@router.get("/notifications")
async def list_notifications(
    unread_only: bool = Query(False),
    current_user: dict = Depends(get_current_user),
):
    del current_user
    where = ["read = 0"] if unread_only else None
    return _list_records("notifications", where=where, params=[], order_by="id DESC")


@router.post("/notifications/read")
async def mark_notifications_read(current_user: dict = Depends(get_current_user)):
    del current_user
    conn = _db_connection()
    try:
        conn.execute("UPDATE notifications SET read = 1")
        conn.commit()
    finally:
        conn.close()
    return {"status": "ok"}


@router.delete("/notifications")
async def clear_notifications(current_user: dict = Depends(get_current_user)):
    del current_user
    conn = _db_connection()
    try:
        conn.execute("DELETE FROM notifications")
        conn.commit()
    finally:
        conn.close()
    return {"status": "cleared"}

@router.get("/monitoring/notifications")
async def get_monitoring_notifications(
    viewed: Optional[bool] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """Get notifications for user."""
    try:
        user_id = current_user.get("username", "default_user")
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            
            # Build query
            where_clauses = ["user_id = ?"]
            params = [user_id]
            
            if viewed is not None:
                where_clauses.append("viewed = ?")
                params.append(1 if viewed else 0)
            
            where_sql = " AND ".join(where_clauses)
            
            cursor.execute(f"""
                SELECT notification_id, type, priority, title, details,
                       created_at, viewed, dismissed
                FROM notifications
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT ?
            """, params + [limit])
            
            notifications = [dict(row) for row in cursor.fetchall()]
            
            return {
                "success": True,
                "notifications": notifications,
                "count": len(notifications)
            }
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Get notifications error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/notifications/{notification_id}/dismiss")
async def dismiss_monitoring_notification(notification_id: str, _: dict = Depends(get_current_user)):
    """Mark notification as dismissed."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE notifications
                SET dismissed = 1, dismissed_at = ?
                WHERE notification_id = ?
            """, (datetime.utcnow().isoformat(), notification_id))
            conn.commit()
            
            return {"success": True}
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Dismiss notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
