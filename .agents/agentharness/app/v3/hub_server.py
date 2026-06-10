from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import logging
import os
import sqlite3
import sys
import uuid
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Any

from dotenv import load_dotenv

HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
AGENTS_DIR = HARNESS.parent
APP_ROOT = AGENTS_DIR.parent
WEB_DIR = HERE / "web"
PID_FILE = AGENTS_DIR / "data" / "hub.pid"
DB_PATH = HARNESS / "memory" / "runs_v3.db"
SKILLS_ROOT = AGENTS_DIR / "agents" / "projects"

for _path in (HERE, HARNESS, AGENTS_DIR, APP_ROOT):
    if str(_path) not in sys.path:
        sys.path.append(str(_path))

load_dotenv(AGENTS_DIR / ".env")

try:
    from fastapi import (
        FastAPI,
        HTTPException,
        Depends,
        WebSocket,
        WebSocketDisconnect,
        status,
        Header,
        Query,
    )
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import RedirectResponse, JSONResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from pydantic import BaseModel, Field
    import uvicorn

    FASTAPI_OK = True
except ImportError:
    FASTAPI_OK = False

    class BaseModel:
        def __init__(self, **data: Any):
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self, *args: Any, **kwargs: Any) -> dict:
            return dict(self.__dict__)

    def Field(default: Any = None, default_factory: Any = None):  # type: ignore
        return default_factory() if default_factory is not None else default

    FastAPI = HTTPException = Depends = WebSocket = WebSocketDisconnect = object  # type: ignore
    status = type("status", (), {"HTTP_401_UNAUTHORIZED": 401, "HTTP_403_FORBIDDEN": 403})  # type: ignore
    CORSMiddleware = StaticFiles = RedirectResponse = JSONResponse = object  # type: ignore
    HTTPBearer = HTTPAuthorizationCredentials = Header = Query = object  # type: ignore
    uvicorn = None  # type: ignore

try:
    from jose import JWTError, jwt

    JWT_OK = True
except ImportError:
    JWT_OK = False

    class JWTError(Exception):
        pass

try:
    import hub_db as db
except ImportError:
    db = None  # type: ignore

try:
    from hub_nodes import run_graph, LANGGRAPH_OK
except ImportError:
    LANGGRAPH_OK = False

    def run_graph(*args: Any, **kwargs: Any) -> dict:
        raise RuntimeError("hub_nodes is not available")

try:
    from hub_scheduler import build_scheduler
except ImportError:
    class _NullScheduler:
        def start(self) -> None:
            return None

        def shutdown(self, wait: bool = False) -> None:
            return None

        def get_jobs(self) -> list:
            return []

        def add_job(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("hub_scheduler is not available")

        def remove_job(self, *args: Any, **kwargs: Any) -> None:
            return None

        def get_job(self, *args: Any, **kwargs: Any) -> Any:
            return None

    def build_scheduler(_hub: Any) -> _NullScheduler:
        return _NullScheduler()

try:
    from ah_logging import get_logger
except ImportError:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")


SECRET_KEY = os.environ.get("JWT_SECRET", "archonhub-jwt-secret-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
APP_VERSION = "1.0.0"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ArchonHub2024!")
security = HTTPBearer(auto_error=False) if FASTAPI_OK else None


def _utcnow() -> datetime:
    return datetime.utcnow()


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


def _table_columns(table: str) -> set[str]:
    conn = _db_connection()
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {row[1] for row in rows}
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


def _init_schema() -> None:
    if db and hasattr(db, "init_schema"):
        try:
            db.init_schema()  # type: ignore[attr-defined]
            return
        except Exception:
            pass
    _fallback_init_schema()


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


def create_access_token(data: dict) -> str:
    payload = dict(data)
    payload["exp"] = int((_utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)).timestamp())
    if JWT_OK:
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    header = {"alg": ALGORITHM, "typ": "JWT"}
    encoded_header = _b64url_encode(_json_dumps(header).encode("utf-8"))
    encoded_payload = _b64url_encode(_json_dumps(payload).encode("utf-8"))
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        f"{encoded_header}.{encoded_payload}".encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{encoded_header}.{encoded_payload}.{_b64url_encode(signature)}"


def verify_token(token: str) -> dict | None:
    try:
        if JWT_OK:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        header, payload, signature = token.split(".")
        expected = hmac.new(
            SECRET_KEY.encode("utf-8"),
            f"{header}.{payload}".encode("utf-8"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(expected, _b64url_decode(signature)):
            return None
        data = json.loads(_b64url_decode(payload).decode("utf-8"))
        if int(data.get("exp", 0)) < int(_utcnow().timestamp()):
            return None
        return data
    except (ValueError, JWTError, json.JSONDecodeError):
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security) if FASTAPI_OK else None,
    x_api_token: Optional[str] = Header(default=None) if FASTAPI_OK else None,
) -> dict:
    api_token = _config_value("api_token")
    if x_api_token and api_token and hmac.compare_digest(str(x_api_token), str(api_token)):
        return {
            "id": 0,
            "username": "api-token",
            "email": "",
            "role": "admin",
            "is_active": True,
        }
    if not credentials or getattr(credentials, "scheme", "").lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("user_id")
    user = _user_by_id(int(user_id)) if user_id is not None else _user_by_username(payload.get("username", ""))
    public_user = _user_public(user)
    if not public_user or not public_user.get("is_active", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")
    return public_user


async def get_admin_user(user: dict = Depends(get_current_user) if FASTAPI_OK else None) -> dict:
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


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


class HubServer:
    def __init__(self):
        self.start_time = _utcnow()
        self._queue: asyncio.Queue | None = None
        self._active_runs: dict[str, threading.Event] = {}
        self._clients: set[Any] = set()
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._scheduler = None
        self._queue_paused = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._worker_task: asyncio.Task | None = None
        self.logger = get_logger("server")

    async def submit_job(self, config: dict) -> str:
        run_id = config.get("run_id") or uuid.uuid4().hex
        payload = dict(config)
        payload["run_id"] = run_id
        payload.setdefault("graph", "reflexion")
        payload.setdefault("max_revisions", 2)
        payload.setdefault("priority", "normal")
        _queue_job_record(payload)
        if self._queue is None:
            raise RuntimeError("Hub queue is not initialized")
        await self._queue.put(payload)
        await self.broadcast(
            {
                "type": "run_queued",
                "run_id": run_id,
                "agent_id": payload.get("agent_id"),
                "project": payload.get("project"),
                "graph": payload.get("graph"),
                "queue_depth": self._queue.qsize(),
            }
        )
        return run_id

    async def broadcast(self, event: dict) -> None:
        dead_clients: list[Any] = []
        for client in list(self._clients):
            try:
                await client.send_json(event)
            except Exception:
                dead_clients.append(client)
        for client in dead_clients:
            self._clients.discard(client)
        if event.get("type") == "notif":
            _create_record(
                "notifications",
                {
                    "text": event.get("text", ""),
                    "color": event.get("color", ""),
                    "category": event.get("category", "system"),
                    "created_at": _now_iso(),
                    "read": 0,
                },
            )

    async def _worker_loop(self) -> None:
        self._loop = asyncio.get_running_loop()
        while True:
            if self._queue_paused:
                await asyncio.sleep(0.25)
                continue
            if self._queue is None:
                await asyncio.sleep(0.25)
                continue
            config = await self._queue.get()
            run_id = config["run_id"]
            cancel_flag = threading.Event()
            self._active_runs[run_id] = cancel_flag
            _update_job_record(run_id, "running")
            await self.broadcast(
                {
                    "type": "run_started",
                    "run_id": run_id,
                    "agent_id": config.get("agent_id"),
                    "project": config.get("project"),
                    "graph": config.get("graph", "reflexion"),
                }
            )
            try:
                loop = asyncio.get_running_loop()

                def _execute() -> dict:
                    payload = dict(config)
                    payload["cancel_flag"] = cancel_flag
                    return run_graph(payload, emit=make_emit(run_id))

                result = await loop.run_in_executor(self._executor, _execute)
                final_status = "cancelled" if cancel_flag.is_set() else str(result.get("status") or "completed")
                save_payload = {
                    "run_id": run_id,
                    "agent_id": config.get("agent_id"),
                    "project": config.get("project"),
                    "graph": config.get("graph", "reflexion"),
                    "task": config.get("task", ""),
                    "score": result.get("score"),
                    "critique": result.get("critique"),
                    "revision_count": result.get("revision_count", 0),
                    "output": result.get("output", ""),
                    "skill_version": result.get("skill_version", 1),
                    "status": final_status,
                }
                _save_run_record(save_payload)
                _update_job_record(run_id, final_status, {"job_data": {**config, "result": result}})
                await self.broadcast(
                    {
                        "type": "run_cancelled" if final_status == "cancelled" else "run_completed",
                        "run_id": run_id,
                        "agent_id": config.get("agent_id"),
                        "project": config.get("project"),
                        "status": final_status,
                        "score": result.get("score"),
                    }
                )
            except Exception as exc:
                self.logger.exception("Run failed: %s", run_id)
                _update_job_record(run_id, "failed", {"job_data": {**config, "error": str(exc)}})
                _save_run_record(
                    {
                        "run_id": run_id,
                        "agent_id": config.get("agent_id"),
                        "project": config.get("project"),
                        "graph": config.get("graph", "reflexion"),
                        "task": config.get("task", ""),
                        "score": 0.0,
                        "critique": str(exc),
                        "revision_count": 0,
                        "output": "",
                        "skill_version": 1,
                        "status": "failed",
                    }
                )
                await self.broadcast(
                    {
                        "type": "run_failed",
                        "run_id": run_id,
                        "agent_id": config.get("agent_id"),
                        "project": config.get("project"),
                        "error": str(exc),
                    }
                )
            finally:
                self._active_runs.pop(run_id, None)
                self._queue.task_done()

    def cancel_run(self, run_id: str) -> bool:
        cancel_flag = self._active_runs.get(run_id)
        if not cancel_flag:
            return False
        cancel_flag.set()
        return True


hub = HubServer()


def make_emit(run_id: str):
    async def _emit(event_type: str, **kwargs: Any):
        await hub.broadcast({"type": event_type, "run_id": run_id, **kwargs})

    def emit(event_type: str, **kwargs: Any):
        loop = hub._loop
        if loop is None:
            return
        asyncio.run_coroutine_threadsafe(_emit(event_type, **kwargs), loop)

    return emit


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"


class RunRequest(BaseModel):
    agent_id: str
    project: str
    graph: str = "reflexion"
    task: str
    max_revisions: int = 2
    priority: str = "normal"


class TodoCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    status: str = "pending"
    project: str = ""
    due_date: str = ""
    tags: List[Any] = Field(default_factory=list)
    source: str = "user"


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    project: Optional[str] = None
    due_date: Optional[str] = None
    tags: Optional[List[Any]] = None


class TripCreate(BaseModel):
    name: str
    destination: str
    depart_date: str = ""
    return_date: str = ""
    status: str = "planning"
    budget: float = 0.0
    notes: str = ""


class TripUpdate(BaseModel):
    name: Optional[str] = None
    destination: Optional[str] = None
    depart_date: Optional[str] = None
    return_date: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    spent: Optional[float] = None
    notes: Optional[str] = None


class ConnectorCreate(BaseModel):
    label: str
    email_address: str
    provider: str = "imap"
    auth_type: str = "password"
    imap_host: str = ""
    imap_port: int = 993
    smtp_host: str = ""
    smtp_port: int = 587
    username: str = ""
    credentials: dict = Field(default_factory=dict)


class ConnectorUpdate(BaseModel):
    label: Optional[str] = None
    email_address: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    username: Optional[str] = None
    credentials: Optional[dict] = None
    status: Optional[str] = None


class ProjectCreate(BaseModel):
    slug: str
    name: str
    description: str = ""
    status: str = "active"
    lead_agent: str = ""
    tags: List[Any] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    lead_agent: Optional[str] = None
    tags: Optional[List[Any]] = None


class ClientCreate(BaseModel):
    slug: str
    name: str
    business_type: str = ""
    service: str = ""
    contact_name: str = ""
    contact_email: str = ""
    engagement: str = "retainer"
    status: str = "active"
    project_slug: str = ""
    notes: str = ""


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    business_type: Optional[str] = None
    service: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    engagement: Optional[str] = None
    status: Optional[str] = None
    project_slug: Optional[str] = None
    notes: Optional[str] = None


class MessageCreate(BaseModel):
    role: str
    content: str
    agent_id: str = ""


class ConversationCreate(BaseModel):
    title: str
    slug: str = "global"


class SchedulerJobCreate(BaseModel):
    agent_id: str
    project: str
    graph: str = "reflexion"
    task: str
    run_type: str = "cron"
    cron_expr: str = ""
    interval_sec: int = 0


class ConfigUpdate(BaseModel):
    data: dict


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class MemoryUpdate(BaseModel):
    data: dict


class AgentUpsert(BaseModel):
    agent_id: str
    name: str
    type: str = "specialist"
    role: str = ""
    description: str = ""
    project_slug: str = ""
    capabilities: List[str] = Field(default_factory=list)
    integrations: List[str] = Field(default_factory=list)
    status: str = "active"
    system_prompt: str = ""
    config: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    project_slug: Optional[str] = None
    capabilities: Optional[List[str]] = None
    integrations: Optional[List[str]] = None
    status: Optional[str] = None
    system_prompt: Optional[str] = None
    config: Optional[dict] = None
    metadata: Optional[dict] = None


class AutomationCreate(BaseModel):
    slug: str
    name: str
    description: str = ""
    project_slug: str = ""
    agent_id: str = ""
    trigger_type: str = "manual"
    trigger_config: dict = Field(default_factory=dict)
    steps: List[Any] = Field(default_factory=list)
    status: str = "active"


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_slug: Optional[str] = None
    agent_id: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[dict] = None
    steps: Optional[List[Any]] = None
    status: Optional[str] = None


class KnowledgeCreate(BaseModel):
    title: str
    content: str
    source: str = ""
    source_type: str = "manual"
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    project_slug: str = ""
    agent_id: str = ""


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    project_slug: Optional[str] = None
    is_active: Optional[bool] = None


class DocumentCreate(BaseModel):
    title: str
    doc_type: str = "general"
    content: str = ""
    format: str = "markdown"
    project_slug: str = ""
    client_id: str = ""
    tags: List[str] = Field(default_factory=list)
    created_by: str = ""


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    doc_type: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class IntegrationUpsert(BaseModel):
    name: str
    provider: str
    entity_type: str = "global"
    entity_id: str = ""
    auth_type: str = "oauth2"
    credentials: dict = Field(default_factory=dict)
    scope: str = ""
    status: str = "pending"
    metadata: dict = Field(default_factory=dict)


class AutomationDocCreate(BaseModel):
    automation_id: str = ""
    run_id: str = ""
    title: str = ""
    doc_type: str = "report"
    content: str = ""
    status: str = "draft"
    reviewed_by: str = ""
    review_notes: str = ""


class InezChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


if FASTAPI_OK:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _init_schema()
        hub._queue = asyncio.Queue()
        hub._loop = asyncio.get_running_loop()
        for pending_job in _load_pending_jobs():
            payload = pending_job.get("job_data") if isinstance(pending_job.get("job_data"), dict) else {}
            merged = {**payload, **pending_job}
            merged["run_id"] = pending_job.get("id") or pending_job.get("run_id")
            if merged.get("run_id"):
                await hub._queue.put(merged)
        hub._worker_task = asyncio.create_task(hub._worker_loop())
        hub._scheduler = build_scheduler(hub)
        try:
            hub._scheduler.start()
        except Exception:
            hub.logger.exception("Unable to start scheduler")
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
        try:
            yield
        finally:
            if hub._worker_task:
                hub._worker_task.cancel()
            if hub._scheduler:
                try:
                    hub._scheduler.shutdown()
                except Exception:
                    pass
            hub._executor.shutdown(wait=False)
            if PID_FILE.exists():
                PID_FILE.unlink()


    app = FastAPI(title="ArchonHub", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    try:
        app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
    except Exception:
        pass


    def _scheduler_job_count() -> int:
        try:
            return len(hub._scheduler.get_jobs()) if hub._scheduler else 0
        except Exception:
            return 0


    def _serialize_scheduler_job(job: Any) -> dict:
        return {
            "id": getattr(job, "id", None),
            "name": getattr(job, "name", None),
            "next_fire": getattr(getattr(job, "next_run_time", None), "isoformat", lambda: None)(),
            "trigger": str(getattr(job, "trigger", "")),
        }


    async def _require_admin_for_registration(
        credentials: Optional[HTTPAuthorizationCredentials],
        x_api_token: Optional[str],
    ) -> None:
        if _count_rows("users") == 0:
            return
        user = await get_current_user(credentials, x_api_token)
        if user.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


    def _scheduler_trigger(job: SchedulerJobCreate):
        try:
            from apscheduler.triggers.cron import CronTrigger
            from apscheduler.triggers.interval import IntervalTrigger
        except Exception as exc:
            raise HTTPException(500, f"APScheduler is unavailable: {exc}") from exc
        if job.run_type == "interval":
            if job.interval_sec <= 0:
                raise HTTPException(400, "interval_sec must be greater than zero")
            return IntervalTrigger(seconds=job.interval_sec)
        if job.run_type == "cron":
            if not job.cron_expr:
                raise HTTPException(400, "cron_expr is required for cron jobs")
            parts = job.cron_expr.split()
            if len(parts) != 5:
                raise HTTPException(400, "cron_expr must have 5 fields")
            return CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
                timezone="America/Chicago",
            )
        raise HTTPException(400, "run_type must be 'cron' or 'interval'")


    async def _fire_scheduled_job(job_id: str, payload: dict) -> str:
        run_id = await hub.submit_job(
            {
                "agent_id": payload["agent_id"],
                "project": payload.get("project", ""),
                "graph": payload.get("graph", "reflexion"),
                "task": payload["task"],
                "max_revisions": payload.get("max_revisions", 2),
                "priority": payload.get("priority", "normal"),
            }
        )
        await hub.broadcast({"type": "scheduler_triggered", "id": job_id, "run_id": run_id})
        return run_id


    @app.get("/")
    async def root():
        return RedirectResponse(url="/web")


    @app.post("/api/auth/login")
    async def login(body: LoginRequest):
        user = _authenticate_user(body.username, body.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = create_access_token(
            {
                "sub": user["username"],
                "username": user["username"],
                "user_id": user["id"],
                "role": user["role"],
            }
        )
        return {"access_token": token, "token_type": "bearer", "user": user}


    @app.post("/api/auth/register")
    async def register(
        body: RegisterRequest,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        x_api_token: Optional[str] = Header(default=None),
    ):
        await _require_admin_for_registration(credentials, x_api_token)
        if _user_by_username(body.username):
            raise HTTPException(400, "Username already exists")
        role = "admin" if _count_rows("users") == 0 else body.role
        user = _create_user(body.username, body.email, body.password, role=role)
        return user


    @app.get("/api/auth/me")
    async def me(current_user: dict = Depends(get_current_user)):
        return current_user


    @app.get("/api/health")
    async def health():
        queue_depth = hub._queue.qsize() if hub._queue else 0
        # Resolve current LLM provider + model from config
        try:
            from hub_nodes import _load_ai_config  # type: ignore
            _ai = _load_ai_config()
            _cfg = _all_config()
            _llm_provider = _cfg.get("llm_provider") or _ai.get("provider", "openai")
            _llm_model    = _cfg.get("llm_model")    or _ai.get("model",    "gpt-4o-mini")
        except Exception:
            _llm_provider, _llm_model = "openai", "gpt-4o-mini"
        return {
            "status": "ok",
            "app": "ArchonHub",
            "version": APP_VERSION,
            "uptime_seconds": int((_utcnow() - hub.start_time).total_seconds()),
            "active_runs": len(hub._active_runs),
            "queue_depth": queue_depth,
            "ws_clients": len(hub._clients),
            "scheduler_jobs": _scheduler_job_count(),
            "thread_pool_size": getattr(hub._executor, "_max_workers", 3),
            "langgraph_ok": LANGGRAPH_OK,
            "pending_todos": _count_rows("todos", "status = ?", ["pending"]),
            "total_runs": _count_rows("runs"),
            "llm_provider": _llm_provider,
            "llm_model":    _llm_model,
        }


    @app.post("/api/runs")
    async def create_run(body: RunRequest, current_user: dict = Depends(get_current_user)):
        del current_user
        run_id = await hub.submit_job(body.model_dump())
        return {"run_id": run_id, "status": "queued"}


    @app.get("/api/runs")
    async def list_runs(
        limit: int = Query(50, ge=1, le=500),
        agent_id: Optional[str] = Query(default=None),
        project: Optional[str] = Query(default=None),
        status_filter: Optional[str] = Query(default=None, alias="status"),
        current_user: dict = Depends(get_current_user),
    ):
        del current_user
        return _list_runs(limit=limit, agent_id=agent_id, project=project, status_filter=status_filter)


    @app.post("/api/runs/{run_id}/cancel")
    async def cancel_run(run_id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if not hub.cancel_run(run_id):
            raise HTTPException(404, "Run is not active")
        _update_job_record(run_id, "cancelled")
        await hub.broadcast({"type": "run_cancelled", "run_id": run_id})
        return {"run_id": run_id, "status": "cancelled"}


    @app.get("/api/queue")
    async def get_queue(current_user: dict = Depends(get_current_user)):
        del current_user
        queued = _list_job_records("queued")
        if queued:
            return queued
        return list(getattr(hub._queue, "_queue", [])) if hub._queue else []


    @app.post("/api/queue/pause")
    async def pause_queue(current_user: dict = Depends(get_current_user)):
        del current_user
        hub._queue_paused = True
        return {"status": "paused"}


    @app.post("/api/queue/resume")
    async def resume_queue(current_user: dict = Depends(get_current_user)):
        del current_user
        hub._queue_paused = False
        return {"status": "running"}


    @app.get("/api/todos")
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


    @app.post("/api/todos")
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


    @app.get("/api/todos/{id}")
    async def get_todo(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        todo = _get_record("todos", id, json_fields={"tags"})
        if not todo:
            raise HTTPException(404, "Todo not found")
        return todo


    @app.put("/api/todos/{id}")
    async def update_todo(id: str, body: TodoUpdate, current_user: dict = Depends(get_current_user)):
        del current_user
        updates = {key: value for key, value in body.model_dump().items() if value is not None}
        updates["updated_at"] = _now_iso()
        todo = _update_record("todos", id, updates, json_fields={"tags"})
        if not todo:
            raise HTTPException(404, "Todo not found")
        await hub.broadcast({"type": "todo_update", "action": "updated", "todo": todo})
        return todo


    @app.delete("/api/todos/{id}")
    async def delete_todo(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if not _delete_record("todos", id):
            raise HTTPException(404, "Todo not found")
        await hub.broadcast({"type": "todo_update", "action": "deleted", "todo": {"id": id}})
        return {"id": id, "deleted": True}


    @app.get("/api/notifications")
    async def list_notifications(
        unread_only: bool = Query(False),
        current_user: dict = Depends(get_current_user),
    ):
        del current_user
        where = ["read = 0"] if unread_only else None
        return _list_records("notifications", where=where, params=[], order_by="id DESC")


    @app.post("/api/notifications/read")
    async def mark_notifications_read(current_user: dict = Depends(get_current_user)):
        del current_user
        conn = _db_connection()
        try:
            conn.execute("UPDATE notifications SET read = 1")
            conn.commit()
        finally:
            conn.close()
        return {"status": "ok"}


    @app.delete("/api/notifications")
    async def clear_notifications(current_user: dict = Depends(get_current_user)):
        del current_user
        conn = _db_connection()
        try:
            conn.execute("DELETE FROM notifications")
            conn.commit()
        finally:
            conn.close()
        return {"status": "cleared"}


    @app.get("/api/trips")
    async def list_trips(current_user: dict = Depends(get_current_user)):
        del current_user
        return _list_records("travel_trips", order_by="updated_at DESC")


    @app.post("/api/trips")
    async def create_trip(body: TripCreate, current_user: dict = Depends(get_current_user)):
        del current_user
        return _create_record(
            "travel_trips",
            {
                "id": uuid.uuid4().hex,
                "name": body.name,
                "destination": body.destination,
                "depart_date": body.depart_date,
                "return_date": body.return_date,
                "status": body.status,
                "budget": body.budget,
                "spent": 0.0,
                "notes": body.notes,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            },
        )


    @app.get("/api/trips/{id}")
    async def get_trip(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        trip = _get_record("travel_trips", id)
        if not trip:
            raise HTTPException(404, "Trip not found")
        return trip


    @app.put("/api/trips/{id}")
    async def update_trip(id: str, body: TripUpdate, current_user: dict = Depends(get_current_user)):
        del current_user
        updates = {key: value for key, value in body.model_dump().items() if value is not None}
        updates["updated_at"] = _now_iso()
        trip = _update_record("travel_trips", id, updates)
        if not trip:
            raise HTTPException(404, "Trip not found")
        return trip


    @app.delete("/api/trips/{id}")
    async def delete_trip(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if not _delete_record("travel_trips", id):
            raise HTTPException(404, "Trip not found")
        return {"id": id, "deleted": True}


    @app.get("/api/connectors")
    async def list_connectors(current_user: dict = Depends(get_current_user)):
        del current_user
        return _list_records("email_connectors", order_by="updated_at DESC", json_fields={"credentials"})


    @app.post("/api/connectors")
    async def create_connector(body: ConnectorCreate, current_user: dict = Depends(get_current_user)):
        del current_user
        return _create_record(
            "email_connectors",
            {
                "id": uuid.uuid4().hex,
                "label": body.label,
                "email_address": body.email_address,
                "provider": body.provider,
                "auth_type": body.auth_type,
                "imap_host": body.imap_host,
                "imap_port": body.imap_port,
                "smtp_host": body.smtp_host,
                "smtp_port": body.smtp_port,
                "username": body.username,
                "credentials": body.credentials,
                "status": "pending",
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            },
            json_fields={"credentials"},
        )


    @app.get("/api/connectors/{id}")
    async def get_connector(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        connector = _get_record("email_connectors", id, json_fields={"credentials"})
        if not connector:
            raise HTTPException(404, "Connector not found")
        return connector


    @app.put("/api/connectors/{id}")
    async def update_connector(id: str, body: ConnectorUpdate, current_user: dict = Depends(get_current_user)):
        del current_user
        updates = {key: value for key, value in body.model_dump().items() if value is not None}
        updates["updated_at"] = _now_iso()
        connector = _update_record("email_connectors", id, updates, json_fields={"credentials"})
        if not connector:
            raise HTTPException(404, "Connector not found")
        return connector


    @app.delete("/api/connectors/{id}")
    async def delete_connector(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if not _delete_record("email_connectors", id):
            raise HTTPException(404, "Connector not found")
        return {"id": id, "deleted": True}


    @app.post("/api/connectors/{id}/test")
    async def test_connector(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        connector = _get_record("email_connectors", id, json_fields={"credentials"})
        if not connector:
            raise HTTPException(404, "Connector not found")
        return {"ok": True, "message": "Connection test not implemented", "connector_id": id}


    @app.get("/api/projects")
    async def list_projects(current_user: dict = Depends(get_current_user)):
        del current_user
        return _list_records("projects", order_by="updated_at DESC", json_fields={"tags"})


    @app.post("/api/projects")
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


    @app.get("/api/projects/{id}")
    async def get_project(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        project = _get_record("projects", id, json_fields={"tags"})
        if not project:
            raise HTTPException(404, "Project not found")
        return project


    @app.put("/api/projects/{id}")
    async def update_project(id: str, body: ProjectUpdate, current_user: dict = Depends(get_current_user)):
        del current_user
        updates = {key: value for key, value in body.model_dump().items() if value is not None}
        updates["updated_at"] = _now_iso()
        project = _update_record("projects", id, updates, json_fields={"tags"})
        if not project:
            raise HTTPException(404, "Project not found")
        return project


    @app.delete("/api/projects/{id}")
    async def delete_project(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if not _delete_record("projects", id):
            raise HTTPException(404, "Project not found")
        return {"id": id, "deleted": True}


    @app.get("/api/clients")
    async def list_clients(current_user: dict = Depends(get_current_user)):
        del current_user
        return _list_records("clients", order_by="updated_at DESC")


    @app.post("/api/clients")
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


    @app.get("/api/clients/{id}")
    async def get_client(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        client = _get_record("clients", id)
        if not client:
            raise HTTPException(404, "Client not found")
        return client


    @app.put("/api/clients/{id}")
    async def update_client(id: str, body: ClientUpdate, current_user: dict = Depends(get_current_user)):
        del current_user
        updates = {key: value for key, value in body.model_dump().items() if value is not None}
        updates["updated_at"] = _now_iso()
        client = _update_record("clients", id, updates)
        if not client:
            raise HTTPException(404, "Client not found")
        return client


    @app.delete("/api/clients/{id}")
    async def delete_client(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if not _delete_record("clients", id):
            raise HTTPException(404, "Client not found")
        return {"id": id, "deleted": True}


    @app.get("/api/conversations")
    async def list_conversations(current_user: dict = Depends(get_current_user)):
        del current_user
        return _list_records("conversations", order_by="updated_at DESC")


    @app.post("/api/conversations")
    async def create_conversation(body: ConversationCreate, current_user: dict = Depends(get_current_user)):
        del current_user
        return _create_record(
            "conversations",
            {
                "id": uuid.uuid4().hex,
                "title": body.title,
                "slug": body.slug,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            },
        )


    @app.get("/api/conversations/{id}/messages")
    async def list_messages(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if not _get_record("conversations", id):
            raise HTTPException(404, "Conversation not found")
        return _list_records("messages", where=["conversation_id = ?"], params=[id], order_by="created_at ASC")


    @app.post("/api/conversations/{id}/messages")
    async def create_message(id: str, body: MessageCreate, current_user: dict = Depends(get_current_user)):
        del current_user
        conversation = _get_record("conversations", id)
        if not conversation:
            raise HTTPException(404, "Conversation not found")
        message = _create_record(
            "messages",
            {
                "id": uuid.uuid4().hex,
                "conversation_id": id,
                "role": body.role,
                "content": body.content,
                "agent_id": body.agent_id,
                "created_at": _now_iso(),
            },
        )
        _update_record("conversations", id, {"updated_at": _now_iso()})
        return message


    @app.get("/api/memory/{agent_id}")
    async def get_memory(agent_id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        return {"agent_id": agent_id, "data": _memory_dict(agent_id)}


    @app.put("/api/memory/{agent_id}")
    async def update_memory(agent_id: str, body: MemoryUpdate, current_user: dict = Depends(get_current_user)):
        del current_user
        return {"agent_id": agent_id, "data": _upsert_memory(agent_id, body.data)}


    # ── Inez Chief of Staff ───────────────────────────────────────────────────

    @app.post("/api/inez/chat")
    async def inez_chat(body: InezChatRequest, current_user: dict = Depends(get_current_user)):
        """Send a message to Inez and receive her structured response."""
        del current_user
        import asyncio

        try:
            from inez_agent import think
        except ImportError:
            raise HTTPException(503, "Inez agent module not available")

        # Resolve or create conversation
        conv_id = body.conversation_id
        if not conv_id:
            conv_id = uuid.uuid4().hex
            _create_record("conversations", {
                "id": conv_id,
                "title": body.message[:60],
                "slug": "inez",
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            })
        else:
            if not _get_record("conversations", conv_id):
                conv_id = uuid.uuid4().hex
                _create_record("conversations", {
                    "id": conv_id,
                    "title": body.message[:60],
                    "slug": "inez",
                    "created_at": _now_iso(),
                    "updated_at": _now_iso(),
                })

        # Store user message
        _create_record("messages", {
            "id": uuid.uuid4().hex,
            "conversation_id": conv_id,
            "role": "user",
            "content": body.message,
            "agent_id": None,
            "created_at": _now_iso(),
        })

        # Load conversation history for context
        history_rows = _list_records(
            "messages",
            where=["conversation_id = ?"],
            params=[conv_id],
            order_by="created_at ASC",
        )
        history = [
            {"role": r.get("role", "user"), "content": r.get("content", "")}
            for r in (history_rows or [])
        ]

        # Call Inez in executor (blocking LLM call)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            hub._executor,
            lambda: think(body.message, history),
        )

        inez_message = result.get("inez_message", "")
        dispatches = result.get("dispatches", [])
        needs_agents = result.get("needs_agents", False)
        error = result.get("error")

        # Store Inez response
        _create_record("messages", {
            "id": uuid.uuid4().hex,
            "conversation_id": conv_id,
            "role": "assistant",
            "content": inez_message,
            "agent_id": "inez-chief-of-staff",
            "created_at": _now_iso(),
        })
        _update_record("conversations", conv_id, {"updated_at": _now_iso()})

        # Enqueue dispatched agent runs
        queued_runs = []
        for dispatch in dispatches:
            agent_id = dispatch.get("agent_id", "")
            project = dispatch.get("project", "")
            graph = dispatch.get("graph", "reflexion")
            task = dispatch.get("task", "")
            if agent_id and task:
                run_id = await hub.submit_job({
                    "agent_id": agent_id,
                    "project": project,
                    "graph": graph,
                    "task": task,
                    "max_revisions": 2,
                    "priority": "high",
                })
                queued_runs.append({"run_id": run_id, "agent_id": agent_id, "project": project})

        return {
            "conversation_id": conv_id,
            "inez_message": inez_message,
            "dispatches": dispatches,
            "needs_agents": needs_agents,
            "queued_runs": queued_runs,
            "error": error,
        }

    @app.get("/api/inez/brief")
    async def inez_morning_brief(current_user: dict = Depends(get_current_user)):
        """Generate a morning briefing from Inez."""
        del current_user
        import asyncio
        try:
            from inez_agent import generate_morning_brief
        except ImportError:
            raise HTTPException(503, "Inez agent module not available")

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            hub._executor,
            lambda: generate_morning_brief(),
        )
        return result


    @app.get("/api/briefs")
    async def list_briefs(current_user: dict = Depends(get_current_user)):
        del current_user
        briefs = _list_records("daily_briefs", order_by="created_at DESC")
        for brief in briefs:
            brief["content"] = _json_loads(brief.get("content"))
        return briefs


    @app.post("/api/briefs")
    async def create_brief(body: dict, current_user: dict = Depends(get_current_user)):
        del current_user
        content = body.get("content", body)
        brief = _create_record(
            "daily_briefs",
            {"id": uuid.uuid4().hex, "content": _json_dumps(content), "created_at": _now_iso()},
        )
        brief["content"] = _json_loads(brief.get("content"))
        return brief


    @app.delete("/api/briefs/{id}")
    async def delete_brief(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if not _delete_record("daily_briefs", id):
            raise HTTPException(404, "Brief not found")
        return {"id": id, "deleted": True}


    @app.get("/api/skills")
    async def list_skills(current_user: dict = Depends(get_current_user)):
        del current_user
        skills = _list_records("skills", order_by="id DESC")
        if skills:
            return skills
        result = []
        if SKILLS_ROOT.exists():
            for skill_file in SKILLS_ROOT.rglob("*.md"):
                result.append({"agent_id": skill_file.stem, "path": str(skill_file), "content": skill_file.read_text(encoding="utf-8")})
        return result


    @app.get("/api/skills/{agent_id}")
    async def get_skill(agent_id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        return _latest_skill(agent_id)


    @app.put("/api/skills/{agent_id}")
    async def update_skill(agent_id: str, body: dict, current_user: dict = Depends(get_current_user)):
        del current_user
        content = str(body.get("content", ""))
        version = body.get("version")
        return _save_skill(agent_id, content, version=version)


    @app.get("/api/scheduler")
    async def list_scheduler(current_user: dict = Depends(get_current_user)):
        del current_user
        jobs = []
        if hub._scheduler:
            try:
                jobs.extend(_serialize_scheduler_job(job) for job in hub._scheduler.get_jobs())
            except Exception:
                pass
        return jobs


    @app.post("/api/scheduler")
    async def create_scheduler_job(body: SchedulerJobCreate, current_user: dict = Depends(get_current_user)):
        del current_user
        if not hub._scheduler:
            raise HTTPException(500, "Scheduler is not available")
        job_id = uuid.uuid4().hex
        payload = body.model_dump()
        trigger = _scheduler_trigger(body)

        async def _runner():
            await _fire_scheduled_job(job_id, payload)

        try:
            hub._scheduler.add_job(_runner, trigger=trigger, id=job_id, name=f"{body.agent_id}:{body.project}", replace_existing=True)
        except Exception as exc:
            raise HTTPException(500, f"Unable to create job: {exc}") from exc
        job = hub._scheduler.get_job(job_id)
        _create_record(
            "scheduled_jobs",
            {
                "id": job_id,
                "agent_id": body.agent_id,
                "project": body.project,
                "graph": body.graph,
                "task": body.task,
                "run_type": body.run_type,
                "cron_expr": body.cron_expr,
                "interval_sec": body.interval_sec,
                "scheduled_at": "",
                "next_fire": job.next_run_time.isoformat() if job and job.next_run_time else "",
                "status": "active",
                "created_at": _now_iso(),
                "job_data": payload,
            },
            json_fields={"job_data"},
        )
        return {"id": job_id, "status": "scheduled", "next_fire": job.next_run_time.isoformat() if job and job.next_run_time else None}


    @app.delete("/api/scheduler/{id}")
    async def delete_scheduler_job(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if hub._scheduler:
            try:
                hub._scheduler.remove_job(id)
            except Exception:
                pass
        job = _update_record("scheduled_jobs", id, {"status": "cancelled"})
        if not job and not _get_record("scheduled_jobs", id):
            raise HTTPException(404, "Scheduled job not found")
        return {"id": id, "deleted": True}


    @app.post("/api/scheduler/{id}/trigger")
    async def trigger_scheduler_job(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        job = _get_record("scheduled_jobs", id, json_fields={"job_data"})
        if not job:
            raise HTTPException(404, "Scheduled job not found")
        payload = job.get("job_data") if isinstance(job.get("job_data"), dict) else job
        run_id = await _fire_scheduled_job(id, payload)
        return {"id": id, "run_id": run_id, "status": "triggered"}


    @app.get("/api/config")
    async def get_config(admin_user: dict = Depends(get_admin_user)):
        del admin_user
        return _all_config()


    @app.put("/api/config")
    async def update_config(body: ConfigUpdate, admin_user: dict = Depends(get_admin_user)):
        del admin_user
        updated = _update_config_values(body.data)
        if "thread_pool_size" in body.data:
            old_executor = hub._executor
            hub._executor = ThreadPoolExecutor(max_workers=max(1, int(body.data["thread_pool_size"])))
            old_executor.shutdown(wait=False)
        return updated


    @app.get("/api/stats")
    async def get_stats(current_user: dict = Depends(get_current_user)):
        del current_user
        return _agent_stats()


    @app.get("/api/briefing")
    async def get_briefing(current_user: dict = Depends(get_current_user)):
        del current_user
        return _briefing_cache()


    @app.get("/api/users")
    async def list_users(admin_user: dict = Depends(get_admin_user)):
        del admin_user
        conn = _db_connection()
        try:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at ASC").fetchall()
            return [_user_public(dict(row)) for row in rows]
        finally:
            conn.close()


    @app.post("/api/users")
    async def create_user_endpoint(body: RegisterRequest, admin_user: dict = Depends(get_admin_user)):
        del admin_user
        if _user_by_username(body.username):
            raise HTTPException(400, "Username already exists")
        return _create_user(body.username, body.email, body.password, role=body.role)


    @app.get("/api/users/{id}")
    async def get_user(id: int, admin_user: dict = Depends(get_admin_user)):
        del admin_user
        user = _user_public(_user_by_id(id))
        if not user:
            raise HTTPException(404, "User not found")
        return user


    @app.put("/api/users/{id}")
    async def update_user(id: int, body: UserUpdate, admin_user: dict = Depends(get_admin_user)):
        del admin_user
        updates = {key: value for key, value in body.model_dump().items() if value is not None}
        if "is_active" in updates:
            updates["is_active"] = 1 if updates["is_active"] else 0
        user = _update_record("users", id, updates)
        if not user:
            raise HTTPException(404, "User not found")
        return _user_public(user)


    @app.delete("/api/users/{id}")
    async def delete_user(id: int, admin_user: dict = Depends(get_admin_user)):
        del admin_user
        if not _delete_record("users", id):
            raise HTTPException(404, "User not found")
        return {"id": id, "deleted": True}


    # ── Agent Registry ────────────────────────────────────────────────────────

    _AGENT_JSON = {"capabilities", "integrations", "config", "metadata"}

    @app.get("/api/agents")
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

    @app.post("/api/agents")
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

    @app.get("/api/agents/{agent_id}")
    async def get_agent_endpoint(agent_id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        rec = _list_records("agent_registry", where=["agent_id = ?"], params=[agent_id],
                             json_fields=_AGENT_JSON)
        if not rec:
            raise HTTPException(404, "Agent not found")
        return rec[0]

    @app.put("/api/agents/{agent_id}")
    async def update_agent_endpoint(agent_id: str, body: AgentUpdate, current_user: dict = Depends(get_current_user)):
        del current_user
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
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

    @app.delete("/api/agents/{agent_id}")
    async def delete_agent_endpoint(agent_id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        conn = _db_connection()
        try:
            cur = conn.execute("DELETE FROM agent_registry WHERE agent_id = ?", (agent_id,))
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(404, "Agent not found")
        finally:
            conn.close()
        return {"agent_id": agent_id, "deleted": True}


    # ── Automations ────────────────────────────────────────────────────────────

    _AUTO_JSON = {"trigger_config", "steps", "metadata"}

    @app.get("/api/automations")
    async def list_automations(
        project_slug: Optional[str] = None,
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user),
    ):
        del current_user
        where, params = [], []
        if project_slug:
            where.append("project_slug = ?"); params.append(project_slug)
        if status:
            where.append("status = ?"); params.append(status)
        return _list_records("automations", where=where or None, params=params or None,
                              order_by="updated_at DESC", json_fields=_AUTO_JSON)

    @app.post("/api/automations")
    async def create_automation(body: AutomationCreate, current_user: dict = Depends(get_current_user)):
        del current_user
        now = _now_iso()
        return _create_record("automations", {
            "id": uuid.uuid4().hex,
            "slug": body.slug, "name": body.name,
            "description": body.description, "project_slug": body.project_slug,
            "agent_id": body.agent_id, "trigger_type": body.trigger_type,
            "trigger_config": body.trigger_config, "steps": body.steps,
            "status": body.status, "run_count": 0,
            "created_at": now, "updated_at": now,
        }, json_fields=_AUTO_JSON)

    @app.get("/api/automations/{id}")
    async def get_automation(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        rec = _get_record("automations", id, json_fields=_AUTO_JSON)
        if not rec:
            raise HTTPException(404, "Automation not found")
        return rec

    @app.put("/api/automations/{id}")
    async def update_automation(id: str, body: AutomationUpdate, current_user: dict = Depends(get_current_user)):
        del current_user
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        updates["updated_at"] = _now_iso()
        rec = _update_record("automations", id, updates, json_fields=_AUTO_JSON)
        if not rec:
            raise HTTPException(404, "Automation not found")
        return rec

    @app.delete("/api/automations/{id}")
    async def delete_automation(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if not _delete_record("automations", id):
            raise HTTPException(404, "Automation not found")
        return {"id": id, "deleted": True}

    @app.post("/api/automations/{id}/trigger")
    async def trigger_automation(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        auto = _get_record("automations", id, json_fields=_AUTO_JSON)
        if not auto:
            raise HTTPException(404, "Automation not found")
        run_id = uuid.uuid4().hex
        now = _now_iso()
        _create_record("automation_runs", {
            "id": run_id, "automation_id": id,
            "automation_slug": auto.get("slug", ""),
            "triggered_by": "manual", "status": "running",
            "started_at": now,
        })
        _update_record("automations", id, {"last_run_at": now, "last_run_status": "running"})
        return {"run_id": run_id, "automation_id": id, "status": "running"}

    @app.get("/api/automations/{id}/runs")
    async def list_automation_runs(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        return _list_records("automation_runs", where=["automation_id = ?"], params=[id],
                              order_by="started_at DESC", json_fields={"metadata"})

    @app.get("/api/automations/{id}/documents")
    async def list_automation_docs(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        return _list_records("automation_documents", where=["automation_id = ?"], params=[id],
                              order_by="created_at DESC")

    @app.post("/api/automations/{id}/documents")
    async def create_automation_doc(id: str, body: AutomationDocCreate, current_user: dict = Depends(get_current_user)):
        del current_user
        now = _now_iso()
        return _create_record("automation_documents", {
            "id": uuid.uuid4().hex,
            "automation_id": id,
            "run_id": body.run_id, "title": body.title,
            "doc_type": body.doc_type, "content": body.content,
            "status": body.status, "reviewed_by": body.reviewed_by,
            "review_notes": body.review_notes,
            "created_at": now, "updated_at": now,
        })


    # ── Knowledge Base ─────────────────────────────────────────────────────────

    _KB_JSON = {"tags"}

    @app.get("/api/knowledge")
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

    @app.post("/api/knowledge")
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

    @app.get("/api/knowledge/{id}")
    async def get_knowledge(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        rec = _get_record("knowledge_base", id, json_fields=_KB_JSON)
        if not rec:
            raise HTTPException(404, "Knowledge entry not found")
        return rec

    @app.put("/api/knowledge/{id}")
    async def update_knowledge(id: str, body: KnowledgeUpdate, current_user: dict = Depends(get_current_user)):
        del current_user
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        updates["updated_at"] = _now_iso()
        if "is_active" in updates:
            updates["is_active"] = 1 if updates["is_active"] else 0
        rec = _update_record("knowledge_base", id, updates, json_fields=_KB_JSON)
        if not rec:
            raise HTTPException(404, "Knowledge entry not found")
        return rec

    @app.delete("/api/knowledge/{id}")
    async def delete_knowledge(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if not _delete_record("knowledge_base", id):
            raise HTTPException(404, "Knowledge entry not found")
        return {"id": id, "deleted": True}


    # ── Documents ──────────────────────────────────────────────────────────────

    _DOC_JSON = {"tags"}

    @app.get("/api/documents")
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

    @app.post("/api/documents")
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

    @app.get("/api/documents/{id}")
    async def get_document(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        rec = _get_record("documents", id, json_fields=_DOC_JSON)
        if not rec:
            raise HTTPException(404, "Document not found")
        return rec

    @app.put("/api/documents/{id}")
    async def update_document(id: str, body: DocumentUpdate, current_user: dict = Depends(get_current_user)):
        del current_user
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        updates["updated_at"] = _now_iso()
        rec = _update_record("documents", id, updates, json_fields=_DOC_JSON)
        if not rec:
            raise HTTPException(404, "Document not found")
        return rec

    @app.delete("/api/documents/{id}")
    async def delete_document_ep(id: str, current_user: dict = Depends(get_current_user)):
        del current_user
        if not _delete_record("documents", id):
            raise HTTPException(404, "Document not found")
        return {"id": id, "deleted": True}


    # ── Integrations ───────────────────────────────────────────────────────────

    _INT_JSON = {"credentials", "metadata"}

    @app.get("/api/integrations")
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

    @app.post("/api/integrations")
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

    @app.get("/api/integrations/{id}")
    async def get_integration(id: str, admin_user: dict = Depends(get_admin_user)):
        del admin_user
        rec = _get_record("integrations", id, json_fields=_INT_JSON)
        if not rec:
            raise HTTPException(404, "Integration not found")
        return rec

    @app.delete("/api/integrations/{id}")
    async def delete_integration(id: str, admin_user: dict = Depends(get_admin_user)):
        del admin_user
        if not _delete_record("integrations", id):
            raise HTTPException(404, "Integration not found")
        return {"id": id, "deleted": True}


    # ── Events Log ─────────────────────────────────────────────────────────────

    @app.get("/api/events")
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

    @app.get("/api/context")
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


    # ── Reports ────────────────────────────────────────────────────────────────

    class ReportRunRequest(BaseModel):
        job_id: str
        extra_context: str = ""

    @app.get("/api/reports")
    async def list_reports_endpoint(
        report_type: Optional[str] = None,
        project_slug: Optional[str] = None,
        job_id: Optional[str] = None,
        limit: int = 100,
        current_user: dict = Depends(get_current_user),
    ):
        del current_user
        return hub_db.list_reports(
            report_type=report_type,
            project_slug=project_slug,
            job_id=job_id,
            limit=limit,
        )

    @app.get("/api/reports/{report_id}")
    async def get_report_endpoint(
        report_id: str,
        current_user: dict = Depends(get_current_user),
    ):
        del current_user
        report = hub_db.get_report(report_id)
        if not report:
            raise HTTPException(404, "Report not found")
        return report

    @app.delete("/api/reports/{report_id}")
    async def delete_report_endpoint(
        report_id: str,
        admin_user: dict = Depends(get_admin_user),
    ):
        del admin_user
        if not hub_db.delete_report(report_id):
            raise HTTPException(404, "Report not found")
        return {"status": "deleted"}

    @app.post("/api/reports/run")
    async def run_report_endpoint(
        req: ReportRunRequest,
        background_tasks,
        admin_user: dict = Depends(get_admin_user),
    ):
        """Manually trigger a report job immediately."""
        del admin_user
        async def _run():
            try:
                from report_monitor import run_report_job
                await run_report_job(req.job_id, extra_context=req.extra_context)
            except Exception as exc:
                logger.error("Manual report run failed: %s", exc)
        background_tasks.add_task(_run)
        return {"status": "queued", "job_id": req.job_id}

    @app.get("/api/reports/types/summary")
    async def report_types_summary(current_user: dict = Depends(get_current_user)):
        """Return count of reports per type for the Reports tab header."""
        del current_user
        with hub_db.get_conn() as conn:
            rows = conn.execute(
                "SELECT report_type, COUNT(*) as cnt FROM reports GROUP BY report_type ORDER BY cnt DESC"
            ).fetchall()
        return [{"report_type": r["report_type"], "count": r["cnt"]} for r in rows]

    # ── Data Import ────────────────────────────────────────────────────────────

    @app.post("/api/import")
    async def run_data_import(admin_user: dict = Depends(get_admin_user)):
        """Trigger a full re-import of all markdown/JSON source files into the DB."""
        del admin_user
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "data_import", str(HERE / "data_import.py")
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            result = mod.import_all()
            return {"status": "ok", "imported": result}
        except Exception as exc:
            raise HTTPException(500, f"Import failed: {exc}") from exc



    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        try:
            first_message = await websocket.receive_json()
        except Exception:
            await websocket.close(code=1008)
            return
        token = None
        if isinstance(first_message, dict) and first_message.get("type") == "auth":
            token = first_message.get("token")
            api_token = first_message.get("api_token")
            if api_token:
                configured = _config_value("api_token")
                if configured and hmac.compare_digest(str(api_token), str(configured)):
                    token = create_access_token({"sub": "api-token", "username": "api-token", "user_id": 0, "role": "admin"})
        if not token or not verify_token(token):
            await websocket.close(code=1008)
            return
        hub._clients.add(websocket)
        await websocket.send_json(
            {
                "type": "connected",
                "queue_depth": hub._queue.qsize() if hub._queue else 0,
                "active_runs": list(hub._active_runs.keys()),
            }
        )
        try:
            while True:
                message = await websocket.receive_json()
                if not isinstance(message, dict):
                    continue
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass
        except Exception:
            await websocket.close(code=1008)
        finally:
            hub._clients.discard(websocket)

else:
    app = None


if __name__ == "__main__":
    if not FASTAPI_OK:
        raise SystemExit("FastAPI is not installed")
    uvicorn.run("hub_server:app", host="0.0.0.0", port=8765, reload=False)
