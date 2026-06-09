from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import bcrypt as _bcrypt
except ImportError:  # pragma: no cover - fallback for environments without bcrypt
    _bcrypt = None
    from passlib.hash import bcrypt as _passlib_bcrypt
else:
    _passlib_bcrypt = None


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "ArchonHub2024!"

DB_PATH = Path(__file__).resolve().parent.parent.parent / "memory" / "runs_v3.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _maybe_json_loads(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    if text[0] not in '[{"' and text not in {"true", "false", "null"}:
        return value
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return value


def _normalize_json_text(value: Any, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return _json_dumps(value)


def _memory_value_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return _json_dumps(value)


def _row_to_dict(row: sqlite3.Row | None, json_fields: set[str] | None = None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    for field in json_fields or set():
        if field in data and data[field] is not None:
            data[field] = _maybe_json_loads(data[field])
    return data


def _rows_to_dicts(rows: list[sqlite3.Row], json_fields: set[str] | None = None) -> list[dict[str, Any]]:
    return [_row_to_dict(row, json_fields) for row in rows if row is not None]


def _sanitize_user(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not data:
        return None
    clean = dict(data)
    clean.pop("hashed_password", None)
    return clean


def _priority_case_sql(column: str) -> str:
    return (
        f"CASE {column} "
        "WHEN 'urgent' THEN 0 "
        "WHEN 'high' THEN 1 "
        "WHEN 'normal' THEN 2 "
        "WHEN 'medium' THEN 2 "
        "WHEN 'low' THEN 3 "
        "ELSE 4 END"
    )


def _hash_pw(password: str) -> str:
    if _bcrypt is not None:
        return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")
    return _passlib_bcrypt.hash(password)


def _verify_pw(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    if _bcrypt is not None:
        try:
            return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except ValueError:
            return False
    return _passlib_bcrypt.verify(plain, hashed)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_schema() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    statements = [
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT UNIQUE,
            agent_id TEXT,
            project TEXT,
            graph TEXT,
            task TEXT,
            score REAL DEFAULT 0.0,
            critique TEXT DEFAULT '',
            revision_count INTEGER DEFAULT 0,
            output TEXT DEFAULT '',
            skill_version INTEGER DEFAULT 1,
            status TEXT DEFAULT 'running',
            created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            skill_name TEXT,
            version INTEGER DEFAULT 1,
            content TEXT,
            avg_score REAL DEFAULT 0.0,
            last_critique TEXT DEFAULT '',
            created_at TEXT,
            UNIQUE(agent_id)
        )
        """,
        """
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
            job_data TEXT DEFAULT '{}'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS todos (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            project TEXT DEFAULT '',
            due_date TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            source TEXT DEFAULT 'user',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            color TEXT DEFAULT '#00B8FF',
            category TEXT DEFAULT 'system',
            created_at TEXT,
            read INTEGER DEFAULT 0
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hub_config (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            hashed_password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            last_login TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
            id TEXT PRIMARY KEY,
            agent_id TEXT,
            project TEXT,
            graph TEXT DEFAULT 'reflexion',
            task TEXT,
            run_type TEXT DEFAULT 'cron',
            cron_expr TEXT,
            interval_sec INTEGER,
            scheduled_at TEXT,
            next_fire TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            job_data TEXT DEFAULT '{}'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS travel_trips (
            id TEXT PRIMARY KEY,
            name TEXT,
            destination TEXT,
            depart_date TEXT,
            return_date TEXT,
            status TEXT DEFAULT 'planning',
            budget REAL DEFAULT 0,
            spent REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS email_connectors (
            id TEXT PRIMARY KEY,
            label TEXT,
            email_address TEXT,
            provider TEXT DEFAULT 'imap',
            auth_type TEXT DEFAULT 'password',
            imap_host TEXT,
            imap_port INTEGER DEFAULT 993,
            smtp_host TEXT,
            smtp_port INTEGER DEFAULT 587,
            username TEXT,
            credentials TEXT DEFAULT '{}',
            status TEXT DEFAULT 'pending',
            last_error TEXT,
            last_synced TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
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
        )
        """,
        """
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
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            slug TEXT DEFAULT 'global',
            title TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            agent_id TEXT DEFAULT '',
            created_at TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS agent_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            key TEXT,
            value TEXT,
            updated_at TEXT,
            UNIQUE(agent_id, key)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS daily_briefs (
            id TEXT PRIMARY KEY,
            content TEXT,
            created_at TEXT
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_runs_agent_id ON runs(agent_id)",
        "CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status)",
        "CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status)",
        "CREATE INDEX IF NOT EXISTS idx_todos_status ON todos(status)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)",
        "CREATE INDEX IF NOT EXISTS idx_travel_trips_status ON travel_trips(status)",
        "CREATE INDEX IF NOT EXISTS idx_travel_trips_depart_date ON travel_trips(depart_date)",
        "CREATE INDEX IF NOT EXISTS idx_email_connectors_status ON email_connectors(status)",
        "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)",
        "CREATE INDEX IF NOT EXISTS idx_agent_memory_agent_id ON agent_memory(agent_id)",
        "CREATE INDEX IF NOT EXISTS idx_projects_slug ON projects(slug)",
        "CREATE INDEX IF NOT EXISTS idx_clients_slug ON clients(slug)",
    ]

    default_config = {
        "api_token": "",
        "llm_model": "gpt-4o-mini",
        "thread_pool_size": 3,
        "queue_paused": False,
    }

    with get_conn() as conn:
        for statement in statements:
            conn.execute(statement)

        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count == 0:
            now = _now_iso()
            conn.execute(
                """
                INSERT INTO users (username, email, hashed_password, role, is_active, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    DEFAULT_ADMIN_USERNAME,
                    None,
                    _hash_pw(DEFAULT_ADMIN_PASSWORD),
                    "admin",
                    1,
                    now,
                    None,
                ),
            )

        now = _now_iso()
        for key, value in default_config.items():
            conn.execute(
                """
                INSERT INTO hub_config (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO NOTHING
                """,
                (key, _json_dumps(value), now),
            )


def save_run(
    run_id: str,
    agent_id: str,
    project: str,
    graph: str,
    task: str,
    score: float,
    critique: str,
    revision_count: int,
    output: str,
    skill_version: int,
    status: str,
) -> None:
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO runs (
                run_id, agent_id, project, graph, task, score, critique,
                revision_count, output, skill_version, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                agent_id = excluded.agent_id,
                project = excluded.project,
                graph = excluded.graph,
                task = excluded.task,
                score = excluded.score,
                critique = excluded.critique,
                revision_count = excluded.revision_count,
                output = excluded.output,
                skill_version = excluded.skill_version,
                status = excluded.status
            """,
            (
                run_id,
                agent_id,
                project,
                graph,
                task,
                score,
                critique,
                revision_count,
                output,
                skill_version,
                status,
                now,
            ),
        )


def load_runs(
    limit: int = 50,
    agent_id: str | None = None,
    project: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if agent_id:
        clauses.append("agent_id = ?")
        params.append(agent_id)
    if project:
        clauses.append("project = ?")
        params.append(project)
    if status:
        clauses.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM runs {where} ORDER BY created_at DESC, id DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
    return _rows_to_dicts(rows)


def update_run_status(
    run_id: str,
    status: str,
    output: str | None = None,
    score: float | None = None,
    critique: str | None = None,
) -> None:
    assignments = ["status = ?"]
    params: list[Any] = [status]
    if output is not None:
        assignments.append("output = ?")
        params.append(output)
    if score is not None:
        assignments.append("score = ?")
        params.append(score)
    if critique is not None:
        assignments.append("critique = ?")
        params.append(critique)
    params.append(run_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE runs SET {', '.join(assignments)} WHERE run_id = ?", params)


def agent_stats() -> dict[str, Any]:
    with get_conn() as conn:
        totals = conn.execute("SELECT COUNT(*) AS total_runs, AVG(score) AS avg_score FROM runs").fetchone()
        project_rows = conn.execute(
            """
            SELECT project, COUNT(*) AS run_count, AVG(score) AS avg_score
            FROM runs
            GROUP BY project
            ORDER BY project
            """
        ).fetchall()
    return {
        "total_runs": totals["total_runs"] or 0,
        "avg_score": float(totals["avg_score"] or 0.0),
        "by_project": {
            (row["project"] or ""): {
                "count": row["run_count"],
                "avg_score": float(row["avg_score"] or 0.0),
            }
            for row in project_rows
        },
    }


def enqueue_job(
    job_id: str | None,
    agent_id: str,
    project: str,
    graph: str,
    task: str,
    priority: str,
    max_revisions: int,
    job_data: dict[str, Any] | str | None,
) -> None:
    job_id = job_id or str(uuid.uuid4())
    now = _now_iso()
    payload = _normalize_json_text(job_data, "{}")
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO job_queue (
                id, agent_id, project, graph, task, priority, status,
                max_revisions, queued_at, started_at, completed_at, job_data
            )
            VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?, NULL, NULL, ?)
            ON CONFLICT(id) DO UPDATE SET
                agent_id = excluded.agent_id,
                project = excluded.project,
                graph = excluded.graph,
                task = excluded.task,
                priority = excluded.priority,
                status = excluded.status,
                max_revisions = excluded.max_revisions,
                queued_at = excluded.queued_at,
                started_at = NULL,
                completed_at = NULL,
                job_data = excluded.job_data
            """,
            (job_id, agent_id, project, graph, task, priority, max_revisions, now, payload),
        )


def update_job_status(
    job_id: str,
    status: str,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> None:
    assignments = ["status = ?"]
    params: list[Any] = [status]
    if started_at is not None or status == "running":
        assignments.append("started_at = ?")
        params.append(started_at or _now_iso())
    if completed_at is not None or status in {"completed", "failed", "cancelled"}:
        assignments.append("completed_at = ?")
        params.append(completed_at or _now_iso())
    params.append(job_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE job_queue SET {', '.join(assignments)} WHERE id = ?", params)


def load_pending_jobs() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM job_queue
            WHERE status = 'queued'
            ORDER BY {_priority_case_sql('priority')}, queued_at ASC
            """
        ).fetchall()
    return _rows_to_dicts(rows, {"job_data"})


def get_job(job_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM job_queue WHERE id = ?", (job_id,)).fetchone()
    return _row_to_dict(row, {"job_data"})


def list_jobs(status: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM job_queue"
    params: list[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY queued_at DESC, id DESC"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return _rows_to_dicts(rows, {"job_data"})


def save_skill(
    agent_id: str,
    skill_name: str,
    version: int,
    content: str,
    avg_score: float,
    last_critique: str,
) -> None:
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO skills (agent_id, skill_name, version, content, avg_score, last_critique, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET
                skill_name = excluded.skill_name,
                version = excluded.version,
                content = excluded.content,
                avg_score = excluded.avg_score,
                last_critique = excluded.last_critique,
                created_at = excluded.created_at
            """,
            (agent_id, skill_name, version, content, avg_score, last_critique, now),
        )


def load_skill(skill_name: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM skills WHERE skill_name = ? ORDER BY version DESC, id DESC LIMIT 1",
            (skill_name,),
        ).fetchone()
    return _row_to_dict(row)


def list_skills() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM skills ORDER BY skill_name ASC, agent_id ASC").fetchall()
    return _rows_to_dicts(rows)


def get_skill_by_agent(agent_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM skills WHERE agent_id = ?", (agent_id,)).fetchone()
    return _row_to_dict(row)


def create_todo(
    id: str | None = None,
    title: str = "",
    description: str = "",
    priority: str = "medium",
    status: str = "pending",
    project: str = "",
    due_date: str = "",
    tags: list[str] | str | None = None,
    source: str = "user",
) -> dict[str, Any]:
    todo_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO todos (
                id, title, description, priority, status, project,
                due_date, tags, source, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                todo_id,
                title,
                description,
                priority,
                status,
                project,
                due_date,
                _normalize_json_text(tags, "[]"),
                source,
                now,
                now,
            ),
        )
    return get_todo(todo_id) or {}


def list_todos(status: str | None = None, project: str | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if project:
        clauses.append("project = ?")
        params.append(project)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM todos
            {where}
            ORDER BY {_priority_case_sql('priority')}, updated_at DESC, created_at DESC
            """,
            params,
        ).fetchall()
    return _rows_to_dicts(rows, {"tags"})


def get_todo(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row, {"tags"})


def update_todo(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {"title", "description", "priority", "status", "project", "due_date", "tags", "source"}
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        if key == "tags":
            params.append(_normalize_json_text(value, "[]"))
        else:
            params.append(value)
    if not assignments:
        return get_todo(id)
    assignments.append("updated_at = ?")
    params.append(_now_iso())
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE todos SET {', '.join(assignments)} WHERE id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_todo(id)


def delete_todo(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM todos WHERE id = ?", (id,))
    return cur.rowcount > 0


def migrate_todos_json() -> None:
    return None


def save_notification(text: str, color: str = "#00B8FF", category: str = "system") -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO notifications (text, color, category, created_at, read) VALUES (?, ?, ?, ?, 0)",
            (text, color, category, _now_iso()),
        )


def list_notifications(unread_only: bool = False) -> list[dict[str, Any]]:
    query = "SELECT * FROM notifications"
    params: list[Any] = []
    if unread_only:
        query += " WHERE read = 0"
    query += " ORDER BY created_at DESC, id DESC"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return _rows_to_dicts(rows)


def mark_notifications_read() -> None:
    with get_conn() as conn:
        conn.execute("UPDATE notifications SET read = 1 WHERE read = 0")


def clear_notifications() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM notifications")


def get_config(key: str | None = None) -> dict[str, Any] | str | None:
    with get_conn() as conn:
        if key is not None:
            row = conn.execute("SELECT value FROM hub_config WHERE key = ?", (key,)).fetchone()
            return _maybe_json_loads(row["value"]) if row else None
        rows = conn.execute("SELECT key, value FROM hub_config ORDER BY key").fetchall()
    return {row["key"]: _maybe_json_loads(row["value"]) for row in rows}


def set_config(key: str, value: Any) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO hub_config (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, _json_dumps(value), _now_iso()),
        )


def update_config(data: dict[str, Any]) -> None:
    now = _now_iso()
    with get_conn() as conn:
        conn.executemany(
            """
            INSERT INTO hub_config (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            [(key, _json_dumps(value), now) for key, value in data.items()],
        )


def create_trip(
    id: str | None = None,
    name: str = "",
    destination: str = "",
    depart_date: str = "",
    return_date: str = "",
    status: str = "planning",
    budget: float = 0.0,
    notes: str = "",
) -> dict[str, Any]:
    trip_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO travel_trips (
                id, name, destination, depart_date, return_date, status,
                budget, spent, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (trip_id, name, destination, depart_date, return_date, status, budget, notes, now, now),
        )
    return get_trip(trip_id) or {}


def list_trips() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM travel_trips ORDER BY depart_date ASC, created_at DESC"
        ).fetchall()
    return _rows_to_dicts(rows)


def get_trip(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM travel_trips WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row)


def update_trip(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {"name", "destination", "depart_date", "return_date", "status", "budget", "spent", "notes"}
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key in allowed:
            assignments.append(f"{key} = ?")
            params.append(value)
    if not assignments:
        return get_trip(id)
    assignments.append("updated_at = ?")
    params.append(_now_iso())
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE travel_trips SET {', '.join(assignments)} WHERE id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_trip(id)


def delete_trip(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM travel_trips WHERE id = ?", (id,))
    return cur.rowcount > 0


def create_connector(
    id: str | None = None,
    label: str = "",
    email_address: str = "",
    provider: str = "imap",
    auth_type: str = "password",
    imap_host: str | None = None,
    imap_port: int = 993,
    smtp_host: str | None = None,
    smtp_port: int = 587,
    username: str | None = None,
    credentials: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    connector_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO email_connectors (
                id, label, email_address, provider, auth_type, imap_host, imap_port,
                smtp_host, smtp_port, username, credentials, status,
                last_error, last_synced, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, NULL, ?, ?)
            """,
            (
                connector_id,
                label,
                email_address,
                provider,
                auth_type,
                imap_host,
                imap_port,
                smtp_host,
                smtp_port,
                username,
                _normalize_json_text(credentials, "{}"),
                now,
                now,
            ),
        )
    return get_connector(connector_id) or {}


def list_connectors() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM email_connectors ORDER BY created_at DESC").fetchall()
    return _rows_to_dicts(rows, {"credentials"})


def get_connector(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM email_connectors WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row, {"credentials"})


def update_connector(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {
        "label",
        "email_address",
        "provider",
        "auth_type",
        "imap_host",
        "imap_port",
        "smtp_host",
        "smtp_port",
        "username",
        "credentials",
        "status",
        "last_error",
        "last_synced",
    }
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        if key == "credentials":
            params.append(_normalize_json_text(value, "{}"))
        else:
            params.append(value)
    if not assignments:
        return get_connector(id)
    assignments.append("updated_at = ?")
    params.append(_now_iso())
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE email_connectors SET {', '.join(assignments)} WHERE id = ?",
            params,
        )
    if cur.rowcount == 0:
        return None
    return get_connector(id)


def delete_connector(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM email_connectors WHERE id = ?", (id,))
    return cur.rowcount > 0


def create_project(
    id: str | None = None,
    slug: str = "",
    name: str = "",
    description: str = "",
    status: str = "active",
    lead_agent: str = "",
    tags: list[str] | str | None = None,
) -> dict[str, Any]:
    project_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO projects (
                id, slug, name, description, status, lead_agent, tags, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, slug, name, description, status, lead_agent, _normalize_json_text(tags, "[]"), now, now),
        )
    return get_project(project_id) or {}


def list_projects() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY name ASC, slug ASC").fetchall()
    return _rows_to_dicts(rows, {"tags"})


def get_project(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row, {"tags"})


def update_project(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {"slug", "name", "description", "status", "lead_agent", "tags"}
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        if key == "tags":
            params.append(_normalize_json_text(value, "[]"))
        else:
            params.append(value)
    if not assignments:
        return get_project(id)
    assignments.append("updated_at = ?")
    params.append(_now_iso())
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE projects SET {', '.join(assignments)} WHERE id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_project(id)


def delete_project(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM projects WHERE id = ?", (id,))
    return cur.rowcount > 0


def create_client(
    id: str | None = None,
    slug: str = "",
    name: str = "",
    business_type: str = "",
    service: str = "",
    contact_name: str = "",
    contact_email: str = "",
    engagement: str = "retainer",
    status: str = "active",
    project_slug: str = "",
    notes: str = "",
) -> dict[str, Any]:
    client_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO clients (
                id, slug, name, business_type, service, contact_name,
                contact_email, engagement, status, project_slug, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                slug,
                name,
                business_type,
                service,
                contact_name,
                contact_email,
                engagement,
                status,
                project_slug,
                notes,
                now,
                now,
            ),
        )
    return get_client(client_id) or {}


def list_clients() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM clients ORDER BY name ASC, slug ASC").fetchall()
    return _rows_to_dicts(rows)


def get_client(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM clients WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row)


def update_client(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {
        "slug",
        "name",
        "business_type",
        "service",
        "contact_name",
        "contact_email",
        "engagement",
        "status",
        "project_slug",
        "notes",
    }
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key in allowed:
            assignments.append(f"{key} = ?")
            params.append(value)
    if not assignments:
        return get_client(id)
    assignments.append("updated_at = ?")
    params.append(_now_iso())
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE clients SET {', '.join(assignments)} WHERE id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_client(id)


def delete_client(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM clients WHERE id = ?", (id,))
    return cur.rowcount > 0


def create_conversation(id: str | None = None, slug: str = "global", title: str = "") -> dict[str, Any]:
    conversation_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO conversations (id, slug, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, slug, title, now, now),
        )
    return get_conversation(conversation_id) or {}


def list_conversations() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC, created_at DESC"
        ).fetchall()
    return _rows_to_dicts(rows)


def get_conversation(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM conversations WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row)


def add_message(
    id: str | None = None,
    conversation_id: str = "",
    role: str = "",
    content: str = "",
    agent_id: str = "",
) -> dict[str, Any]:
    message_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, agent_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (message_id, conversation_id, role, content, agent_id, now),
        )
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    return _row_to_dict(row) or {}


def list_messages(conversation_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC, id ASC",
            (conversation_id,),
        ).fetchall()
    return _rows_to_dicts(rows)


def load_memory_context(agent_id: str) -> str:
    memories = get_memory(agent_id)
    if not memories:
        return "No saved memory."
    return "\n".join(f"- {memory['key']}: {memory['value']}" for memory in memories)


def save_memory(agent_id: str, key: str, value: Any) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO agent_memory (agent_id, key, value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(agent_id, key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (agent_id, key, _memory_value_text(value), _now_iso()),
        )


def get_memory(agent_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_memory WHERE agent_id = ? ORDER BY updated_at DESC, key ASC",
            (agent_id,),
        ).fetchall()
    return _rows_to_dicts(rows)


def update_memory(agent_id: str, data: dict[str, Any]) -> None:
    now = _now_iso()
    with get_conn() as conn:
        conn.executemany(
            """
            INSERT INTO agent_memory (agent_id, key, value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(agent_id, key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            [(agent_id, key, _memory_value_text(value), now) for key, value in data.items()],
        )


def cache_briefing(data: dict[str, Any]) -> None:
    brief_id = _today_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO daily_briefs (id, content, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                content = excluded.content,
                created_at = excluded.created_at
            """,
            (brief_id, _json_dumps(data), _now_iso()),
        )


def get_briefing_cache() -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT content FROM daily_briefs WHERE id = ?", (_today_iso(),)).fetchone()
    if not row:
        return None
    return _maybe_json_loads(row["content"])


def list_briefs() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM daily_briefs ORDER BY id DESC").fetchall()
    return _rows_to_dicts(rows, {"content"})


def delete_brief(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM daily_briefs WHERE id = ?", (id,))
    return cur.rowcount > 0


def create_user(username: str, email: str | None, password: str, role: str = "user") -> dict[str, Any]:
    now = _now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO users (username, email, hashed_password, role, is_active, created_at, last_login)
            VALUES (?, ?, ?, ?, 1, ?, NULL)
            """,
            (username, email, _hash_pw(password), role, now),
        )
        user_id = cur.lastrowid
    return get_user(id=user_id) or {}


def list_users() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, username, email, role, is_active, created_at, last_login FROM users ORDER BY username ASC"
        ).fetchall()
    return _rows_to_dicts(rows)


def get_user(id: int | None = None, username: str | None = None) -> dict[str, Any] | None:
    if id is None and username is None:
        return None
    with get_conn() as conn:
        if id is not None:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return _sanitize_user(_row_to_dict(row))


def update_user(id: int, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {"username", "email", "password", "role", "is_active", "last_login"}
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        column = "hashed_password" if key == "password" else key
        assignments.append(f"{column} = ?")
        params.append(_hash_pw(value) if key == "password" else value)
    if not assignments:
        return get_user(id=id)
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE users SET {', '.join(assignments)} WHERE id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_user(id=id)


def delete_user(id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM users WHERE id = ?", (id,))
    return cur.rowcount > 0


def verify_user(username: str, password: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    user = _row_to_dict(row)
    if not user or not user.get("is_active"):
        return None
    if not _verify_pw(password, user["hashed_password"]):
        return None
    return _sanitize_user(user)


def update_last_login(username: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE users SET last_login = ? WHERE username = ?", (_now_iso(), username))


def create_scheduled_job(
    id: str | None = None,
    agent_id: str = "",
    project: str = "",
    graph: str = "reflexion",
    task: str = "",
    run_type: str = "cron",
    cron_expr: str | None = None,
    interval_sec: int | None = None,
    next_fire: str | None = None,
) -> dict[str, Any]:
    job_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO scheduled_jobs (
                id, agent_id, project, graph, task, run_type, cron_expr,
                interval_sec, scheduled_at, next_fire, status, created_at, job_data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, '{}')
            """,
            (job_id, agent_id, project, graph, task, run_type, cron_expr, interval_sec, now, next_fire, now),
        )
    return get_scheduled_job(job_id) or {}


def list_scheduled_jobs() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM scheduled_jobs ORDER BY next_fire ASC, created_at DESC"
        ).fetchall()
    return _rows_to_dicts(rows, {"job_data"})


def get_scheduled_job(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM scheduled_jobs WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row, {"job_data"})


def update_scheduled_job(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {
        "agent_id",
        "project",
        "graph",
        "task",
        "run_type",
        "cron_expr",
        "interval_sec",
        "scheduled_at",
        "next_fire",
        "status",
        "job_data",
    }
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        if key == "job_data":
            params.append(_normalize_json_text(value, "{}"))
        else:
            params.append(value)
    if not assignments:
        return get_scheduled_job(id)
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE scheduled_jobs SET {', '.join(assignments)} WHERE id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_scheduled_job(id)


def delete_scheduled_job(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM scheduled_jobs WHERE id = ?", (id,))
    return cur.rowcount > 0


if __name__ == "__main__":
    init_schema()
