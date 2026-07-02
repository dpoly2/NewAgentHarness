from __future__ import annotations

"""
run_events.py — durable, replayable event log for agent/Inez runs.

Every step of a run (progress + the final message) is appended here as an event.
The WebSocket is a live tail; this table is the source of truth, so a dropped
socket or a proxy-timed-out HTTP request can be recovered by replaying from the
last seen cursor. This is the foundation for the event-sourced rebuild (see
docs/ARCHITECTURE-REBUILD.md §7/§8).

Non-breaking: callers keep their existing HTTP/WS behaviour and additionally
persist events here. The global autoincrement `id` is the monotonic cursor used
for replay (`get_events(run_id, after_id=...)`).
"""

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any

from core.config import DB_PATH

try:
    from ah_logging import get_logger
    logger = get_logger("run_events")
except Exception:
    import logging
    logger = logging.getLogger("archonhub.run_events")

_init_lock = threading.Lock()
_initialised = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _conn():
    """Backend-selected connection (contract C1). Routes through core.db_backend
    so run_events works on both SQLite and Postgres; callers close in a finally."""
    from core import db_backend
    return db_backend.get_connection()


def _ensure_schema(conn) -> None:
    global _initialised
    if _initialised:
        return
    with _init_lock:
        if _initialised:
            return
        from core import db_backend
        # Per-backend DDL: AUTOINCREMENT -> Postgres IDENTITY (contract C3/C10).
        conn.execute(
            db_backend.translate_ddl(
                """
            CREATE TABLE IF NOT EXISTS run_events (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          TEXT NOT NULL,
                conversation_id TEXT,
                type            TEXT NOT NULL,
                data            TEXT,
                created_at      TEXT NOT NULL
            )
            """
            )
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_run_events_run ON run_events(run_id, id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_run_events_conv ON run_events(conversation_id, id)")
        conn.commit()
        _initialised = True


def append_event(run_id: str, event_type: str, data: dict[str, Any] | None = None,
                 conversation_id: str = "") -> int:
    """Persist one run event. Returns the global cursor id (or 0 on failure).

    Never raises — event logging must not break the run it is recording.
    """
    if not run_id or not event_type:
        return 0
    try:
        conn = _conn()
        try:
            _ensure_schema(conn)
            # RETURNING id is portable (SQLite >=3.35, Postgres); replaces
            # cursor.lastrowid, which psycopg does not provide (contract C3).
            row = conn.execute(
                "INSERT INTO run_events (run_id, conversation_id, type, data, created_at) "
                "VALUES (?, ?, ?, ?, ?) RETURNING id",
                (run_id, conversation_id or "", event_type,
                 json.dumps(data or {}, ensure_ascii=False), _now()),
            ).fetchone()
            conn.commit()
            return int((row[0] if row else 0) or 0)
        finally:
            conn.close()
    except Exception as exc:
        logger.debug("append_event failed: %s", exc)
        return 0


def get_events(run_id: str = "", conversation_id: str = "", after_id: int = 0,
               limit: int = 500) -> list[dict[str, Any]]:
    """Replay events for a run (or a whole conversation) after a cursor id."""
    try:
        conn = _conn()
        try:
            _ensure_schema(conn)
            if run_id:
                where, params = "run_id = ?", [run_id]
            elif conversation_id:
                where, params = "conversation_id = ?", [conversation_id]
            else:
                return []
            rows = conn.execute(
                f"SELECT id, run_id, conversation_id, type, data, created_at "
                f"FROM run_events WHERE {where} AND id > ? ORDER BY id ASC LIMIT ?",
                (*params, int(after_id), int(limit)),
            ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                try:
                    d["data"] = json.loads(d.get("data") or "{}")
                except Exception:
                    d["data"] = {}
                out.append(d)
            return out
        finally:
            conn.close()
    except Exception as exc:
        logger.debug("get_events failed: %s", exc)
        return []
