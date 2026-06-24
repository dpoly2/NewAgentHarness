from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException

from core.config import DB_PATH, SKILLS_ROOT

try:
    import hub_db as db
except ImportError:
    db = None  # type: ignore

try:
    from ah_logging import get_logger
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

    def get_logger(name: str):
        return logging.getLogger(f'archonhub.{name}')

logger = get_logger('database')

def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _now_iso() -> str:
    return _utcnow().isoformat()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def _json_dumps(value: Any) -> str:
    def _default(obj: Any) -> Any:
        # LangChain / LangGraph message objects
        if hasattr(obj, "content") and hasattr(obj, "type"):
            return {"type": getattr(obj, "type", obj.__class__.__name__), "content": obj.content}
        # Any object with __dict__
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)
    return json.dumps(value, ensure_ascii=False, default=_default)


def _json_loads(value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default if default is not None else value


_table_columns_cache: dict[str, set[str]] = {}


def _table_columns(table: str) -> set[str]:
    if table in _table_columns_cache:
        return _table_columns_cache[table]
    conn = _db_connection()
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        result = {row[1] for row in rows}
        _table_columns_cache[table] = result
        return result
    except Exception:
        return set()
    finally:
        conn.close()


def _db_connection() -> sqlite3.Connection:
    if db and hasattr(db, "get_db"):
        try:
            return db.get_db()  # type: ignore[attr-defined]
        except Exception:
            pass
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")   # safe with WAL; faster than FULL
    conn.execute("PRAGMA cache_size=-32000")    # 32 MB page cache
    conn.execute("PRAGMA temp_store=MEMORY")    # temp tables in RAM
    return conn


def _row_to_dict(row: Any, json_fields: Optional[set[str]] = None) -> dict | None:
    if row is None:
        return None
    data = dict(row)
    for field in json_fields or set():
        if field in data:
            default = [] if field == "tags" else {}
            data[field] = _json_loads(data[field], default)
    for field in ("read", "is_active"):
        if field in data and data[field] is not None:
            data[field] = bool(data[field])
    return data


def _filter_record(table: str, data: dict, json_fields: Optional[set[str]] = None) -> dict:
    columns = _table_columns(table)
    filtered: dict[str, Any] = {}
    for key, value in data.items():
        if key in columns:
            filtered[key] = _json_dumps(value) if key in (json_fields or set()) and value is not None else value
    return filtered


def _create_record(table: str, data: dict, json_fields: Optional[set[str]] = None) -> dict:
    payload = _filter_record(table, data, json_fields)
    if not payload:
        raise HTTPException(500, f"No writable columns found for {table}")
    columns = list(payload.keys())
    placeholders = ", ".join("?" for _ in columns)
    conn = _db_connection()
    try:
        conn.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            [payload[col] for col in columns],
        )
        conn.commit()
    finally:
        conn.close()
    return _get_record(table, data.get("id"), json_fields=json_fields) if "id" in data else payload


def _get_record(table: str, record_id: Any, pk: str = "id", json_fields: Optional[set[str]] = None) -> dict | None:
    conn = _db_connection()
    try:
        row = conn.execute(f"SELECT * FROM {table} WHERE {pk} = ?", (record_id,)).fetchone()
        return _row_to_dict(row, json_fields)
    finally:
        conn.close()


def _list_records(
    table: str,
    where: Optional[list[str]] = None,
    params: Optional[list[Any]] = None,
    order_by: str = "created_at DESC",
    limit: Optional[int] = None,
    json_fields: Optional[set[str]] = None,
) -> list[dict]:
    sql = f"SELECT * FROM {table}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    if order_by:
        sql += f" ORDER BY {order_by}"
    if limit is not None:
        sql += " LIMIT ?"
        params = (params or []) + [limit]
    conn = _db_connection()
    try:
        rows = conn.execute(sql, params or []).fetchall()
        return [_row_to_dict(row, json_fields) for row in rows if row is not None]
    finally:
        conn.close()


def _update_record(
    table: str,
    record_id: Any,
    updates: dict,
    pk: str = "id",
    json_fields: Optional[set[str]] = None,
) -> dict | None:
    payload = _filter_record(table, updates, json_fields)
    if not payload:
        return _get_record(table, record_id, pk=pk, json_fields=json_fields)
    columns = list(payload.keys())
    sql = ", ".join(f"{column} = ?" for column in columns)
    conn = _db_connection()
    try:
        cur = conn.execute(
            f"UPDATE {table} SET {sql} WHERE {pk} = ?",
            [payload[column] for column in columns] + [record_id],
        )
        conn.commit()
        if cur.rowcount <= 0:
            return None
    finally:
        conn.close()
    return _get_record(table, record_id, pk=pk, json_fields=json_fields)


def _delete_record(table: str, record_id: Any, pk: str = "id") -> bool:
    conn = _db_connection()
    try:
        cur = conn.execute(f"DELETE FROM {table} WHERE {pk} = ?", (record_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def _hash_password(password: str) -> str:
    try:
        from passlib.context import CryptContext

        return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)
    except Exception:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
        return f"pbkdf2_sha256$200000${_b64url_encode(salt)}${_b64url_encode(digest)}"


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    # bcrypt hashes start with $2b$ or $2a$
    if hashed_password.startswith("$2"):
        try:
            import bcrypt as _bcrypt
            return _bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            pass
        try:
            from passlib.context import CryptContext
            return CryptContext(schemes=["bcrypt"], deprecated="auto").verify(plain_password, hashed_password)
        except Exception:
            return False
    if hashed_password.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt_text, digest_text = hashed_password.split("$", 3)
            salt = _b64url_decode(salt_text)
            expected = _b64url_decode(digest_text)
            actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, int(iterations))
            return hmac.compare_digest(actual, expected)
        except Exception:
            return False
    return hmac.compare_digest(plain_password, hashed_password)


def _fallback_init_schema() -> None:
    conn = _db_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                agent_id TEXT,
                project TEXT,
                graph TEXT,
                task TEXT,
                score REAL,
                critique TEXT,
                revision_count INTEGER,
                output TEXT,
                skill_version INTEGER,
                status TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                skill_name TEXT,
                version INTEGER,
                content TEXT,
                avg_score REAL,
                last_critique TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS job_queue (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                project TEXT,
                graph TEXT DEFAULT 'reflexion',
                task TEXT,
                priority TEXT DEFAULT 'normal',
                status TEXT DEFAULT 'queued',
                max_revisions INTEGER DEFAULT 2,
                queued_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                job_data TEXT
            );
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT DEFAULT '',
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                project TEXT DEFAULT '',
                due_date TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                source TEXT DEFAULT 'user',
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                color TEXT,
                category TEXT DEFAULT 'system',
                created_at TEXT,
                read INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS hub_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                hashed_password TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                last_login TEXT
            );
            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                project TEXT,
                graph TEXT,
                task TEXT,
                run_type TEXT,
                cron_expr TEXT,
                interval_sec INTEGER,
                scheduled_at TEXT,
                next_fire TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT,
                job_data TEXT
            );
            CREATE TABLE IF NOT EXISTS travel_trips (
                id TEXT PRIMARY KEY,
                name TEXT,
                destination TEXT,
                depart_date TEXT DEFAULT '',
                return_date TEXT DEFAULT '',
                status TEXT DEFAULT 'planning',
                budget REAL DEFAULT 0,
                spent REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS email_connectors (
                id TEXT PRIMARY KEY,
                label TEXT,
                email_address TEXT,
                provider TEXT DEFAULT 'imap',
                auth_type TEXT DEFAULT 'password',
                imap_host TEXT DEFAULT '',
                imap_port INTEGER DEFAULT 993,
                smtp_host TEXT DEFAULT '',
                smtp_port INTEGER DEFAULT 587,
                username TEXT DEFAULT '',
                credentials TEXT DEFAULT '{}',
                status TEXT DEFAULT 'pending',
                last_error TEXT,
                last_synced TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                slug TEXT UNIQUE,
                name TEXT,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                lead_agent TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                slug TEXT UNIQUE,
                name TEXT,
                business_type TEXT DEFAULT '',
                service TEXT DEFAULT '',
                contact_name TEXT DEFAULT '',
                contact_email TEXT DEFAULT '',
                engagement TEXT DEFAULT 'retainer',
                status TEXT DEFAULT 'active',
                project_slug TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                slug TEXT DEFAULT 'global',
                title TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                agent_id TEXT DEFAULT '',
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                key TEXT,
                value TEXT,
                updated_at TEXT,
                UNIQUE(agent_id, key)
            );
            CREATE TABLE IF NOT EXISTS daily_briefs (
                id TEXT PRIMARY KEY,
                content TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS implementation_plans (
                plan_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                project TEXT DEFAULT '',
                status TEXT DEFAULT 'draft',
                authored_by TEXT DEFAULT 'human',
                graph_json TEXT,
                preflight_json TEXT,
                version INTEGER DEFAULT 1,
                run_id TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS plan_node_events (
                id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                node_id TEXT,
                event_type TEXT NOT NULL,
                payload_json TEXT,
                timestamp TEXT,
                FOREIGN KEY (plan_id) REFERENCES implementation_plans(plan_id)
            );
            CREATE INDEX IF NOT EXISTS idx_runs_agent_status_created ON runs (agent_id, status, created_at);
            CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue (status);
            CREATE INDEX IF NOT EXISTS idx_todos_status ON todos (status);
            CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications (read);
            CREATE INDEX IF NOT EXISTS idx_travel_trips_status_depart_date ON travel_trips (status, depart_date);
            CREATE INDEX IF NOT EXISTS idx_email_connectors_status ON email_connectors (status);
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages (conversation_id);
            CREATE INDEX IF NOT EXISTS idx_agent_memory_agent_id ON agent_memory (agent_id);
            CREATE INDEX IF NOT EXISTS idx_projects_slug ON projects (slug);
            CREATE INDEX IF NOT EXISTS idx_clients_slug ON clients (slug);
            """
        )
        conn.commit()
    finally:
        conn.close()


def _ensure_plan_schema() -> None:
    conn = _db_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS implementation_plans (
                plan_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                project TEXT DEFAULT '',
                status TEXT DEFAULT 'draft',
                authored_by TEXT DEFAULT 'human',
                graph_json TEXT,
                preflight_json TEXT,
                version INTEGER DEFAULT 1,
                run_id TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS plan_node_events (
                id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                node_id TEXT,
                event_type TEXT NOT NULL,
                payload_json TEXT,
                timestamp TEXT,
                FOREIGN KEY (plan_id) REFERENCES implementation_plans(plan_id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def _init_schema() -> None:
    if db and hasattr(db, "init_schema"):
        try:
            db.init_schema()  # type: ignore[attr-defined]
            _ensure_plan_schema()
            return
        except Exception:
            pass
    _fallback_init_schema()
    _ensure_plan_schema()


def _config_value(key: str, default: Any = None) -> Any:
    if db and hasattr(db, "get_config"):
        try:
            return db.get_config(key, default)  # type: ignore[attr-defined]
        except Exception:
            pass
    conn = _db_connection()
    try:
        row = conn.execute("SELECT value FROM hub_config WHERE key = ?", (key,)).fetchone()
        if not row:
            return default
        return _json_loads(row["value"], default)
    finally:
        conn.close()


def _all_config() -> dict:
    conn = _db_connection()
    try:
        rows = conn.execute("SELECT key, value FROM hub_config ORDER BY key").fetchall()
        return {row["key"]: _json_loads(row["value"]) for row in rows}
    finally:
        conn.close()


def _set_config_value(key: str, value: Any) -> None:
    if db and hasattr(db, "set_config"):
        try:
            db.set_config(key, value)  # type: ignore[attr-defined]
            return
        except Exception:
            pass
    conn = _db_connection()
    try:
        conn.execute(
            """
            INSERT INTO hub_config (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, _json_dumps(value), _now_iso()),
        )
        conn.commit()
    finally:
        conn.close()


def _update_config_values(values: dict) -> dict:
    if db and hasattr(db, "update_config"):
        try:
            return db.update_config(values)  # type: ignore[attr-defined]
        except Exception:
            pass
    for key, value in values.items():
        _set_config_value(key, value)
    return _all_config()


def _count_rows(table: str, where: Optional[str] = None, params: Optional[list[Any]] = None) -> int:
    conn = _db_connection()
    try:
        sql = f"SELECT COUNT(*) FROM {table}"
        if where:
            sql += f" WHERE {where}"
        row = conn.execute(sql, params or []).fetchone()
        return int(row[0] if row else 0)
    finally:
        conn.close()


def _user_public(user: dict | None) -> dict | None:
    if not user:
        return None
    cleaned = dict(user)
    cleaned.pop("hashed_password", None)
    if "is_active" in cleaned:
        cleaned["is_active"] = bool(cleaned["is_active"])
    return cleaned


def _user_by_username(username: str) -> dict | None:
    conn = _db_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _user_by_id(user_id: int) -> dict | None:
    conn = _db_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _create_user(username: str, email: str, password: str, role: str = "user", is_active: bool = True) -> dict:
    conn = _db_connection()
    try:
        conn.execute(
            """
            INSERT INTO users (username, email, hashed_password, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, email, _hash_password(password), role, 1 if is_active else 0, _now_iso()),
        )
        conn.commit()
    finally:
        conn.close()
    return _user_public(_user_by_username(username)) or {}


def _update_user_last_login(user_id: int) -> None:
    conn = _db_connection()
    try:
        conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (_now_iso(), user_id))
        conn.commit()
    finally:
        conn.close()


def _authenticate_user(username: str, password: str) -> dict | None:
    user = _user_by_username(username)
    if not user or not bool(user.get("is_active")):
        return None
    if not _verify_password(password, user.get("hashed_password", "")):
        return None
    _update_user_last_login(int(user["id"]))
    return _user_public(_user_by_id(int(user["id"])))

def _queue_job_record(config: dict) -> None:
    record = {
        "id": config["run_id"],
        "agent_id": config["agent_id"],
        "project": config.get("project", ""),
        "graph": config.get("graph", "reflexion"),
        "task": config["task"],
        "priority": config.get("priority", "normal"),
        "status": "queued",
        "max_revisions": config.get("max_revisions", 2),
        "queued_at": _now_iso(),
        "job_data": config,
    }
    if db and hasattr(db, "enqueue_job"):
        try:
            db.enqueue_job(record)  # type: ignore[attr-defined]
            return
        except Exception:
            pass
    payload = _filter_record("job_queue", record, {"job_data"})
    columns = list(payload.keys())
    conn = _db_connection()
    try:
        conn.execute(
            f"INSERT OR REPLACE INTO job_queue ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
            [payload[column] for column in columns],
        )
        conn.commit()
    finally:
        conn.close()


def _update_job_record(run_id: str, state: str, extra: Optional[dict] = None) -> None:
    if db and hasattr(db, "update_job_status"):
        try:
            db.update_job_status(run_id, state, **(extra or {}))  # type: ignore[attr-defined]
            return
        except Exception:
            pass
    updates = {"status": state}
    if state == "running":
        updates["started_at"] = _now_iso()
    if state in {"completed", "complete", "failed", "cancelled"}:
        updates["completed_at"] = _now_iso()
    updates.update(extra or {})
    _update_record("job_queue", run_id, updates, json_fields={"job_data"})


def _list_job_records(status_filter: Optional[str] = None) -> list[dict]:
    if db and hasattr(db, "list_jobs"):
        try:
            return db.list_jobs(status=status_filter)  # type: ignore[attr-defined]
        except Exception:
            pass
    where, params = [], []
    if status_filter:
        where.append("status = ?")
        params.append(status_filter)
    return _list_records("job_queue", where=where, params=params, order_by="queued_at ASC", json_fields={"job_data"})


def _load_pending_jobs() -> list[dict]:
    if db and hasattr(db, "load_pending_jobs"):
        try:
            return db.load_pending_jobs()  # type: ignore[attr-defined]
        except Exception:
            pass
    return _list_job_records("queued")


def _save_run_record(result: dict) -> None:
    if db and hasattr(db, "save_run"):
        try:
            db.save_run(result)  # type: ignore[attr-defined]
            return
        except Exception:
            pass
    conn = _db_connection()
    try:
        conn.execute(
            """
            INSERT INTO runs (run_id, agent_id, project, graph, task, score, critique,
                              revision_count, output, skill_version, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.get("run_id"),
                result.get("agent_id"),
                result.get("project"),
                result.get("graph", "reflexion"),
                result.get("task"),
                result.get("score"),
                result.get("critique"),
                result.get("revision_count", 0),
                result.get("output"),
                result.get("skill_version", 1),
                result.get("status", "completed"),
                _now_iso(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _list_runs(limit: int = 50, agent_id: Optional[str] = None, project: Optional[str] = None, status_filter: Optional[str] = None) -> list[dict]:
    if db and hasattr(db, "load_runs"):
        try:
            return db.load_runs(limit=limit, agent_id=agent_id, project=project, status=status_filter)  # type: ignore[attr-defined]
        except Exception:
            pass
    where, params = [], []
    if agent_id:
        where.append("agent_id = ?")
        params.append(agent_id)
    if project:
        where.append("project = ?")
        params.append(project)
    if status_filter:
        where.append("status = ?")
        params.append(status_filter)
    return _list_records("runs", where=where, params=params, order_by="id DESC", limit=limit)


def _agent_stats() -> dict:
    if db and hasattr(db, "agent_stats"):
        try:
            return db.agent_stats()  # type: ignore[attr-defined]
        except Exception:
            pass
    conn = _db_connection()
    try:
        rows = conn.execute(
            """
            SELECT agent_id, COUNT(*) AS runs, AVG(score) AS avg_score, MAX(score) AS best_score, MAX(created_at) AS last_run
            FROM runs
            GROUP BY agent_id
            ORDER BY agent_id
            """
        ).fetchall()
        return {
            row["agent_id"]: {
                "runs": int(row["runs"] or 0),
                "avg": round(float(row["avg_score"] or 0), 2),
                "best": round(float(row["best_score"] or 0), 2),
                "last_run": row["last_run"],
            }
            for row in rows
        }
    finally:
        conn.close()


def _briefing_cache() -> Any:
    if db and hasattr(db, "get_briefing_cache"):
        try:
            return db.get_briefing_cache()  # type: ignore[attr-defined]
        except Exception:
            pass
    return _config_value("briefing_cache")


def _memory_dict(agent_id: str) -> dict:
    rows = _list_records(
        "agent_memory",
        where=["agent_id = ?"],
        params=[agent_id],
        order_by="updated_at DESC",
    )
    return {row["key"]: _json_loads(row["value"]) for row in rows if "key" in row}


def _upsert_memory(agent_id: str, data: dict) -> dict:
    conn = _db_connection()
    try:
        for key, value in data.items():
            conn.execute(
                """
                INSERT INTO agent_memory (agent_id, key, value, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(agent_id, key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (agent_id, key, _json_dumps(value), _now_iso()),
            )
        conn.commit()
    finally:
        conn.close()
    return _memory_dict(agent_id)


def _find_skill_path(agent_id: str) -> Optional[Path]:
    if not SKILLS_ROOT.exists():
        return None
    matches = list(SKILLS_ROOT.rglob(f"{agent_id}.md"))
    return matches[0] if matches else None


def _read_skill_content(agent_id: str) -> str:
    skill_path = _find_skill_path(agent_id)
    if skill_path and skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return ""


def _write_skill_content(agent_id: str, content: str, project: Optional[str] = None) -> Path:
    skill_path = _find_skill_path(agent_id)
    if not skill_path:
        target_dir = SKILLS_ROOT / (project or "global")
        target_dir.mkdir(parents=True, exist_ok=True)
        skill_path = target_dir / f"{agent_id}.md"
    skill_path.write_text(content, encoding="utf-8")
    return skill_path


def _latest_skill(agent_id: str) -> dict:
    skill_name = agent_id.replace("-", "_")
    conn = _db_connection()
    try:
        row = conn.execute(
            """
            SELECT * FROM skills
            WHERE agent_id = ? OR skill_name = ?
            ORDER BY version DESC, id DESC
            LIMIT 1
            """,
            (agent_id, skill_name),
        ).fetchone()
    finally:
        conn.close()
    if row:
        data = dict(row)
        data["content"] = data.get("content") or _read_skill_content(agent_id)
        return data
    return {"agent_id": agent_id, "skill_name": skill_name, "version": 1, "content": _read_skill_content(agent_id)}


def _save_skill(agent_id: str, content: str, version: Optional[int] = None) -> dict:
    latest = _latest_skill(agent_id)
    next_version = int(version or (latest.get("version") or 0) + 1)
    record = {
        "agent_id": agent_id,
        "skill_name": agent_id.replace("-", "_"),
        "version": next_version,
        "content": content,
        "avg_score": latest.get("avg_score", 0.0),
        "last_critique": "Manual update",
        "created_at": _now_iso(),
    }
    _create_record("skills", record)
    _write_skill_content(agent_id, content)
    return _latest_skill(agent_id)


# ── Plan helpers ───────────────────────────────────────────────────────────────

def _save_plan(plan: dict) -> dict:
    """Insert or replace a full plan dict."""
    conn = _db_connection()
    now = _now_iso()
    plan_id = plan.get("plan_id") or uuid.uuid4().hex
    plan["plan_id"] = plan_id
    plan["updated_at"] = now
    if not plan.get("created_at"):
        plan["created_at"] = now
    preflight_report = plan.pop("preflight_report", None)
    preflight_json = _json_dumps(preflight_report)
    graph_json = _json_dumps(plan)
    plan["preflight_report"] = preflight_report
    try:
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO implementation_plans
                (plan_id, title, project, status, authored_by, graph_json, preflight_json, version, run_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    plan.get("title", ""),
                    plan.get("project", ""),
                    plan.get("status", "draft"),
                    plan.get("authored_by", "human"),
                    graph_json,
                    preflight_json,
                    plan.get("version", 1),
                    plan.get("run_id"),
                    plan.get("created_at", now),
                    now,
                ),
            )
    finally:
        conn.close()
    return plan


def _load_plan(plan_id: str) -> dict | None:
    """Load a plan by ID, reconstituting graph_json + preflight_json."""
    conn = _db_connection()
    try:
        row = conn.execute(
            "SELECT graph_json, preflight_json FROM implementation_plans WHERE plan_id = ?",
            (plan_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    plan = _json_loads(row[0], {})
    if not isinstance(plan, dict):
        return None
    plan["preflight_report"] = _json_loads(row[1])
    return plan


def _list_plans(project: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> list[dict]:
    """List plans as summary rows (no full graph_json for performance)."""
    conn = _db_connection()
    wheres: list[str] = []
    params: list[Any] = []
    if project:
        wheres.append("project = ?")
        params.append(project)
    if status:
        wheres.append("status = ?")
        params.append(status)
    where_clause = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    try:
        rows = conn.execute(
            f"""
            SELECT plan_id, title, project, status, authored_by, version, run_id, created_at, updated_at
            FROM implementation_plans {where_clause}
            ORDER BY updated_at DESC LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
    finally:
        conn.close()
    cols = ["plan_id", "title", "project", "status", "authored_by", "version", "run_id", "created_at", "updated_at"]
    return [dict(zip(cols, row)) for row in rows]


def _append_plan_event(plan_id: str, node_id: Optional[str], event_type: str, payload: dict) -> None:
    """Append a plan node event to the audit log."""
    conn = _db_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO plan_node_events (id, plan_id, node_id, event_type, payload_json, timestamp) VALUES (?,?,?,?,?,?)",
                (uuid.uuid4().hex, plan_id, node_id, event_type, _json_dumps(payload), _now_iso()),
            )
    finally:
        conn.close()


def _get_plan_events(plan_id: str, limit: int = 200) -> list[dict]:
    """Get event log for a plan."""
    conn = _db_connection()
    try:
        rows = conn.execute(
            "SELECT id, plan_id, node_id, event_type, payload_json, timestamp FROM plan_node_events WHERE plan_id = ? ORDER BY timestamp ASC LIMIT ?",
            (plan_id, limit),
        ).fetchall()
    finally:
        conn.close()
    cols = ["id", "plan_id", "node_id", "event_type", "payload_json", "timestamp"]
    result = []
    for row in rows:
        item = dict(zip(cols, row))
        item["payload"] = _json_loads(item.pop("payload_json", "{}"), {})
        result.append(item)
    return result
