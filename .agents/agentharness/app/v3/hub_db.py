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
        """
        CREATE TABLE IF NOT EXISTS agent_registry (
            id TEXT PRIMARY KEY,
            agent_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'specialist',
            role TEXT DEFAULT '',
            description TEXT DEFAULT '',
            project_slug TEXT DEFAULT '',
            capabilities TEXT DEFAULT '[]',
            integrations TEXT DEFAULT '[]',
            status TEXT DEFAULT 'active',
            system_prompt TEXT DEFAULT '',
            config TEXT DEFAULT '{}',
            metadata TEXT DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS automations (
            id TEXT PRIMARY KEY,
            slug TEXT UNIQUE,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            project_slug TEXT DEFAULT '',
            agent_id TEXT DEFAULT '',
            trigger_type TEXT DEFAULT 'manual',
            trigger_config TEXT DEFAULT '{}',
            steps TEXT DEFAULT '[]',
            status TEXT DEFAULT 'active',
            last_run_at TEXT,
            last_run_status TEXT DEFAULT '',
            run_count INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS automation_runs (
            id TEXT PRIMARY KEY,
            automation_id TEXT NOT NULL,
            automation_slug TEXT DEFAULT '',
            triggered_by TEXT DEFAULT 'manual',
            status TEXT DEFAULT 'running',
            output TEXT DEFAULT '',
            error TEXT DEFAULT '',
            duration_sec REAL DEFAULT 0,
            metadata TEXT DEFAULT '{}',
            started_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (automation_id) REFERENCES automations(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS automation_documents (
            id TEXT PRIMARY KEY,
            automation_id TEXT DEFAULT '',
            run_id TEXT DEFAULT '',
            title TEXT DEFAULT '',
            doc_type TEXT DEFAULT 'report',
            content TEXT DEFAULT '',
            file_path TEXT DEFAULT '',
            status TEXT DEFAULT 'draft',
            reviewed_by TEXT DEFAULT '',
            review_notes TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT DEFAULT '',
            source_type TEXT DEFAULT 'manual',
            category TEXT DEFAULT 'general',
            tags TEXT DEFAULT '[]',
            project_slug TEXT DEFAULT '',
            agent_id TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS attachments (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            filename TEXT DEFAULT '',
            original_name TEXT DEFAULT '',
            file_path TEXT DEFAULT '',
            mime_type TEXT DEFAULT '',
            file_size INTEGER DEFAULT 0,
            uploaded_by TEXT DEFAULT '',
            created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS integrations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            provider TEXT NOT NULL,
            entity_type TEXT DEFAULT 'global',
            entity_id TEXT DEFAULT '',
            auth_type TEXT DEFAULT 'oauth2',
            credentials TEXT DEFAULT '{}',
            scope TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            expires_at TEXT,
            last_used_at TEXT,
            metadata TEXT DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            doc_type TEXT DEFAULT 'general',
            content TEXT DEFAULT '',
            format TEXT DEFAULT 'markdown',
            project_slug TEXT DEFAULT '',
            client_id TEXT DEFAULT '',
            entity_type TEXT DEFAULT '',
            entity_id TEXT DEFAULT '',
            version INTEGER DEFAULT 1,
            status TEXT DEFAULT 'draft',
            tags TEXT DEFAULT '[]',
            created_by TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            key TEXT NOT NULL,
            value TEXT,
            updated_at TEXT,
            UNIQUE(user_id, key)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS events_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            entity_type TEXT DEFAULT '',
            entity_id TEXT DEFAULT '',
            actor TEXT DEFAULT 'system',
            summary TEXT DEFAULT '',
            detail TEXT DEFAULT '{}',
            level TEXT DEFAULT 'info',
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
        "CREATE INDEX IF NOT EXISTS idx_agent_registry_agent_id ON agent_registry(agent_id)",
        "CREATE INDEX IF NOT EXISTS idx_agent_registry_project_slug ON agent_registry(project_slug)",
        "CREATE INDEX IF NOT EXISTS idx_automations_slug ON automations(slug)",
        "CREATE INDEX IF NOT EXISTS idx_automations_project_slug ON automations(project_slug)",
        "CREATE INDEX IF NOT EXISTS idx_automation_runs_automation_id ON automation_runs(automation_id)",
        "CREATE INDEX IF NOT EXISTS idx_automation_runs_status ON automation_runs(status)",
        "CREATE INDEX IF NOT EXISTS idx_automation_documents_automation_id ON automation_documents(automation_id)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base(category)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_base_project_slug ON knowledge_base(project_slug)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_base_active ON knowledge_base(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_attachments_entity ON attachments(entity_type, entity_id)",
        "CREATE INDEX IF NOT EXISTS idx_integrations_provider ON integrations(provider)",
        "CREATE INDEX IF NOT EXISTS idx_integrations_entity ON integrations(entity_type, entity_id)",
        "CREATE INDEX IF NOT EXISTS idx_documents_project_slug ON documents(project_slug)",
        "CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type)",
        "CREATE INDEX IF NOT EXISTS idx_events_log_event_type ON events_log(event_type)",
        "CREATE INDEX IF NOT EXISTS idx_events_log_created_at ON events_log(created_at)",
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

    # Migrate existing tables — add new columns (ignore if already exist)
    _migrations = [
        "ALTER TABLE projects ADD COLUMN client_id TEXT DEFAULT ''",
        "ALTER TABLE projects ADD COLUMN sprint TEXT DEFAULT ''",
        "ALTER TABLE projects ADD COLUMN milestone TEXT DEFAULT ''",
        "ALTER TABLE projects ADD COLUMN url TEXT DEFAULT ''",
        "ALTER TABLE projects ADD COLUMN platform TEXT DEFAULT ''",
        "ALTER TABLE projects ADD COLUMN metadata TEXT DEFAULT '{}'",
        "ALTER TABLE clients ADD COLUMN phone TEXT DEFAULT ''",
        "ALTER TABLE clients ADD COLUMN website TEXT DEFAULT ''",
        "ALTER TABLE clients ADD COLUMN contact_role TEXT DEFAULT ''",
        "ALTER TABLE clients ADD COLUMN address TEXT DEFAULT ''",
        "ALTER TABLE clients ADD COLUMN tags TEXT DEFAULT '[]'",
        "ALTER TABLE clients ADD COLUMN metadata TEXT DEFAULT '{}'",
        "ALTER TABLE todos ADD COLUMN assigned_agent TEXT DEFAULT ''",
        "ALTER TABLE todos ADD COLUMN parent_id TEXT DEFAULT ''",
        "ALTER TABLE conversations ADD COLUMN project_id TEXT DEFAULT ''",
        "ALTER TABLE conversations ADD COLUMN client_id TEXT DEFAULT ''",
        "ALTER TABLE conversations ADD COLUMN summary TEXT DEFAULT ''",
        "ALTER TABLE conversations ADD COLUMN tags TEXT DEFAULT '[]'",
        "ALTER TABLE messages ADD COLUMN metadata TEXT DEFAULT '{}'",
        "ALTER TABLE messages ADD COLUMN tokens_used INTEGER DEFAULT 0",
        "ALTER TABLE messages ADD COLUMN model_used TEXT DEFAULT ''",
    ]
    with get_conn() as conn:
        for _mig in _migrations:
            try:
                conn.execute(_mig)
            except Exception:
                pass  # column already exists


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
    assigned_agent: str = "",
    parent_id: str = "",
) -> dict[str, Any]:
    todo_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO todos (
                id, title, description, priority, status, project,
                due_date, tags, source, assigned_agent, parent_id, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                assigned_agent,
                parent_id,
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
    allowed = {
        "title",
        "description",
        "priority",
        "status",
        "project",
        "due_date",
        "tags",
        "source",
        "assigned_agent",
        "parent_id",
    }
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
    return _rows_to_dicts(rows, {"tags", "metadata"})


def get_project(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row, {"tags", "metadata"})


def update_project(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {
        "slug",
        "name",
        "description",
        "status",
        "lead_agent",
        "tags",
        "client_id",
        "sprint",
        "milestone",
        "url",
        "platform",
        "metadata",
    }
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        if key == "tags":
            params.append(_normalize_json_text(value, "[]"))
        elif key == "metadata":
            params.append(_normalize_json_text(value, "{}"))
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
    return _rows_to_dicts(rows, {"tags", "metadata"})


def get_client(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM clients WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row, {"tags", "metadata"})


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
        "phone",
        "website",
        "contact_role",
        "address",
        "tags",
        "metadata",
    }
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        if key == "tags":
            params.append(_normalize_json_text(value, "[]"))
        elif key == "metadata":
            params.append(_normalize_json_text(value, "{}"))
        else:
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


def upsert_agent(
    agent_id: str,
    name: str,
    type: str = "specialist",
    role: str = "",
    description: str = "",
    project_slug: str = "",
    capabilities: list[str] | str | None = None,
    integrations: list[str] | str | None = None,
    status: str = "active",
    system_prompt: str = "",
    config: dict[str, Any] | str | None = None,
    metadata: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    agent = get_agent(agent_id)
    registry_id = agent["id"] if agent else str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO agent_registry (
                id, agent_id, name, type, role, description, project_slug,
                capabilities, integrations, status, system_prompt, config,
                metadata, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET
                name = excluded.name,
                type = excluded.type,
                role = excluded.role,
                description = excluded.description,
                project_slug = excluded.project_slug,
                capabilities = excluded.capabilities,
                integrations = excluded.integrations,
                status = excluded.status,
                system_prompt = excluded.system_prompt,
                config = excluded.config,
                metadata = excluded.metadata,
                updated_at = excluded.updated_at
            """,
            (
                registry_id,
                agent_id,
                name,
                type,
                role,
                description,
                project_slug,
                _normalize_json_text(capabilities, "[]"),
                _normalize_json_text(integrations, "[]"),
                status,
                system_prompt,
                _normalize_json_text(config, "{}"),
                _normalize_json_text(metadata, "{}"),
                agent["created_at"] if agent else now,
                now,
            ),
        )
    return get_agent(agent_id) or {}


def list_agents(
    project_slug: str | None = None,
    type: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if project_slug:
        clauses.append("project_slug = ?")
        params.append(project_slug)
    if type:
        clauses.append("type = ?")
        params.append(type)
    if status:
        clauses.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM agent_registry {where} ORDER BY name ASC, agent_id ASC",
            params,
        ).fetchall()
    return _rows_to_dicts(rows, {"capabilities", "integrations", "config", "metadata"})


def get_agent(agent_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM agent_registry WHERE agent_id = ?", (agent_id,)).fetchone()
    return _row_to_dict(row, {"capabilities", "integrations", "config", "metadata"})


def update_agent(agent_id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {
        "name",
        "type",
        "role",
        "description",
        "project_slug",
        "capabilities",
        "integrations",
        "status",
        "system_prompt",
        "config",
        "metadata",
    }
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        if key in {"capabilities", "integrations"}:
            params.append(_normalize_json_text(value, "[]"))
        elif key in {"config", "metadata"}:
            params.append(_normalize_json_text(value, "{}"))
        else:
            params.append(value)
    if not assignments:
        return get_agent(agent_id)
    assignments.append("updated_at = ?")
    params.append(_now_iso())
    params.append(agent_id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE agent_registry SET {', '.join(assignments)} WHERE agent_id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_agent(agent_id)


def delete_agent(agent_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM agent_registry WHERE agent_id = ?", (agent_id,))
    return cur.rowcount > 0


def create_automation(
    id: str | None = None,
    slug: str = "",
    name: str = "",
    description: str = "",
    project_slug: str = "",
    agent_id: str = "",
    trigger_type: str = "manual",
    trigger_config: dict[str, Any] | str | None = None,
    steps: list[dict[str, Any]] | list[Any] | str | None = None,
    status: str = "active",
) -> dict[str, Any]:
    automation_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO automations (
                id, slug, name, description, project_slug, agent_id,
                trigger_type, trigger_config, steps, status, last_run_at,
                last_run_status, run_count, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, '', 0, ?, ?)
            """,
            (
                automation_id,
                slug,
                name,
                description,
                project_slug,
                agent_id,
                trigger_type,
                _normalize_json_text(trigger_config, "{}"),
                _normalize_json_text(steps, "[]"),
                status,
                now,
                now,
            ),
        )
    return get_automation(automation_id) or {}


def list_automations(project_slug: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if project_slug:
        clauses.append("project_slug = ?")
        params.append(project_slug)
    if status:
        clauses.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM automations {where} ORDER BY name ASC, slug ASC, created_at DESC",
            params,
        ).fetchall()
    return _rows_to_dicts(rows, {"trigger_config", "steps"})


def get_automation(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM automations WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row, {"trigger_config", "steps"})


def get_automation_by_slug(slug: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM automations WHERE slug = ?", (slug,)).fetchone()
    return _row_to_dict(row, {"trigger_config", "steps"})


def update_automation(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {
        "slug",
        "name",
        "description",
        "project_slug",
        "agent_id",
        "trigger_type",
        "trigger_config",
        "steps",
        "status",
        "last_run_at",
        "last_run_status",
        "run_count",
    }
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        if key == "trigger_config":
            params.append(_normalize_json_text(value, "{}"))
        elif key == "steps":
            params.append(_normalize_json_text(value, "[]"))
        else:
            params.append(value)
    if not assignments:
        return get_automation(id)
    assignments.append("updated_at = ?")
    params.append(_now_iso())
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE automations SET {', '.join(assignments)} WHERE id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_automation(id)


def delete_automation(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM automations WHERE id = ?", (id,))
    return cur.rowcount > 0


def record_automation_run(automation_id: str, slug: str, triggered_by: str) -> str:
    run_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO automation_runs (
                id, automation_id, automation_slug, triggered_by, status,
                output, error, duration_sec, metadata, started_at, completed_at
            )
            VALUES (?, ?, ?, ?, 'running', '', '', 0, '{}', ?, NULL)
            """,
            (run_id, automation_id, slug, triggered_by, _now_iso()),
        )
    return run_id


def complete_automation_run(
    run_id: str,
    status: str,
    output: str,
    error: str,
    duration_sec: float,
) -> None:
    completed_at = _now_iso()
    with get_conn() as conn:
        row = conn.execute("SELECT automation_id FROM automation_runs WHERE id = ?", (run_id,)).fetchone()
        conn.execute(
            """
            UPDATE automation_runs
            SET status = ?, output = ?, error = ?, duration_sec = ?, completed_at = ?
            WHERE id = ?
            """,
            (status, output, error, duration_sec, completed_at, run_id),
        )
        if row:
            conn.execute(
                """
                UPDATE automations
                SET last_run_at = ?, last_run_status = ?, run_count = run_count + 1, updated_at = ?
                WHERE id = ?
                """,
                (completed_at, status, completed_at, row["automation_id"]),
            )


def create_automation_document(
    id: str | None = None,
    automation_id: str = "",
    run_id: str = "",
    title: str = "",
    doc_type: str = "report",
    content: str = "",
    file_path: str = "",
    status: str = "draft",
    reviewed_by: str = "",
    review_notes: str = "",
) -> dict[str, Any]:
    document_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO automation_documents (
                id, automation_id, run_id, title, doc_type, content,
                file_path, status, reviewed_by, review_notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                automation_id,
                run_id,
                title,
                doc_type,
                content,
                file_path,
                status,
                reviewed_by,
                review_notes,
                now,
                now,
            ),
        )
    return get_automation_document(document_id) or {}


def list_automation_documents(
    automation_id: str | None = None,
    run_id: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if automation_id:
        clauses.append("automation_id = ?")
        params.append(automation_id)
    if run_id:
        clauses.append("run_id = ?")
        params.append(run_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM automation_documents
            {where}
            ORDER BY updated_at DESC, created_at DESC, id DESC
            """,
            params,
        ).fetchall()
    return _rows_to_dicts(rows)


def get_automation_document(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM automation_documents WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row)


def update_automation_document(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {
        "automation_id",
        "run_id",
        "title",
        "doc_type",
        "content",
        "file_path",
        "status",
        "reviewed_by",
        "review_notes",
    }
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        params.append(value)
    if not assignments:
        return get_automation_document(id)
    assignments.append("updated_at = ?")
    params.append(_now_iso())
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE automation_documents SET {', '.join(assignments)} WHERE id = ?",
            params,
        )
    if cur.rowcount == 0:
        return None
    return get_automation_document(id)


def delete_automation_document(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM automation_documents WHERE id = ?", (id,))
    return cur.rowcount > 0


def upsert_knowledge(
    id: str | None = None,
    title: str = "",
    content: str = "",
    source: str = "",
    source_type: str = "manual",
    category: str = "general",
    tags: list[str] | str | None = None,
    project_slug: str = "",
    agent_id: str = "",
) -> dict[str, Any]:
    knowledge_id = id or str(uuid.uuid4())
    existing = get_knowledge(knowledge_id)
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO knowledge_base (
                id, title, content, source, source_type, category, tags,
                project_slug, agent_id, is_active, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                content = excluded.content,
                source = excluded.source,
                source_type = excluded.source_type,
                category = excluded.category,
                tags = excluded.tags,
                project_slug = excluded.project_slug,
                agent_id = excluded.agent_id,
                updated_at = excluded.updated_at
            """,
            (
                knowledge_id,
                title,
                content,
                source,
                source_type,
                category,
                _normalize_json_text(tags, "[]"),
                project_slug,
                agent_id,
                existing["created_at"] if existing else now,
                now,
            ),
        )
    return get_knowledge(knowledge_id) or {}


def list_knowledge(
    category: str | None = None,
    project_slug: str | None = None,
    agent_id: str | None = None,
    is_active: bool | None = True,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if category:
        clauses.append("category = ?")
        params.append(category)
    if project_slug:
        clauses.append("project_slug = ?")
        params.append(project_slug)
    if agent_id:
        clauses.append("agent_id = ?")
        params.append(agent_id)
    if is_active is not None:
        clauses.append("is_active = ?")
        params.append(1 if is_active else 0)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM knowledge_base
            {where}
            ORDER BY updated_at DESC, created_at DESC, title ASC
            """,
            params,
        ).fetchall()
    return _rows_to_dicts(rows, {"tags"})


def get_knowledge(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM knowledge_base WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row, {"tags"})


def search_knowledge(
    query: str,
    category: str | None = None,
    project_slug: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    clauses = ["(content LIKE ? OR title LIKE ?)"]
    params: list[Any] = [f"%{query}%", f"%{query}%"]
    if category:
        clauses.append("category = ?")
        params.append(category)
    if project_slug:
        clauses.append("project_slug = ?")
        params.append(project_slug)
    clauses.append("is_active = 1")
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM knowledge_base
            WHERE {' AND '.join(clauses)}
            ORDER BY updated_at DESC, created_at DESC, title ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return _rows_to_dicts(rows, {"tags"})


def update_knowledge(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {
        "title",
        "content",
        "source",
        "source_type",
        "category",
        "tags",
        "project_slug",
        "agent_id",
        "is_active",
    }
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
        return get_knowledge(id)
    assignments.append("updated_at = ?")
    params.append(_now_iso())
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE knowledge_base SET {', '.join(assignments)} WHERE id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_knowledge(id)


def delete_knowledge(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM knowledge_base WHERE id = ?", (id,))
    return cur.rowcount > 0


def create_attachment(
    id: str | None = None,
    entity_type: str = "",
    entity_id: str = "",
    filename: str = "",
    original_name: str = "",
    file_path: str = "",
    mime_type: str = "",
    file_size: int = 0,
    uploaded_by: str = "",
) -> dict[str, Any]:
    attachment_id = id or str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO attachments (
                id, entity_type, entity_id, filename, original_name,
                file_path, mime_type, file_size, uploaded_by, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attachment_id,
                entity_type,
                entity_id,
                filename,
                original_name,
                file_path,
                mime_type,
                file_size,
                uploaded_by,
                _now_iso(),
            ),
        )
    return get_attachment(attachment_id) or {}


def list_attachments(
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if entity_type:
        clauses.append("entity_type = ?")
        params.append(entity_type)
    if entity_id:
        clauses.append("entity_id = ?")
        params.append(entity_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM attachments {where} ORDER BY created_at DESC, id DESC",
            params,
        ).fetchall()
    return _rows_to_dicts(rows)


def get_attachment(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM attachments WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row)


def update_attachment(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {
        "entity_type",
        "entity_id",
        "filename",
        "original_name",
        "file_path",
        "mime_type",
        "file_size",
        "uploaded_by",
    }
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        params.append(value)
    if not assignments:
        return get_attachment(id)
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE attachments SET {', '.join(assignments)} WHERE id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_attachment(id)


def delete_attachment(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM attachments WHERE id = ?", (id,))
    return cur.rowcount > 0


def upsert_integration(
    id: str | None = None,
    name: str = "",
    provider: str = "",
    entity_type: str = "global",
    entity_id: str = "",
    auth_type: str = "oauth2",
    credentials: dict[str, Any] | str | None = None,
    scope: str = "",
    status: str = "pending",
    expires_at: str | None = None,
    metadata: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    integration_id = id or str(uuid.uuid4())
    existing = get_integration(integration_id)
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO integrations (
                id, name, provider, entity_type, entity_id, auth_type,
                credentials, scope, status, expires_at, last_used_at,
                metadata, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                provider = excluded.provider,
                entity_type = excluded.entity_type,
                entity_id = excluded.entity_id,
                auth_type = excluded.auth_type,
                credentials = excluded.credentials,
                scope = excluded.scope,
                status = excluded.status,
                expires_at = excluded.expires_at,
                metadata = excluded.metadata,
                updated_at = excluded.updated_at
            """,
            (
                integration_id,
                name,
                provider,
                entity_type,
                entity_id,
                auth_type,
                _normalize_json_text(credentials, "{}"),
                scope,
                status,
                expires_at,
                existing["last_used_at"] if existing else None,
                _normalize_json_text(metadata, "{}"),
                existing["created_at"] if existing else now,
                now,
            ),
        )
    return get_integration(integration_id) or {}


def list_integrations(
    provider: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if provider:
        clauses.append("provider = ?")
        params.append(provider)
    if entity_type:
        clauses.append("entity_type = ?")
        params.append(entity_type)
    if entity_id:
        clauses.append("entity_id = ?")
        params.append(entity_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM integrations
            {where}
            ORDER BY provider ASC, name ASC, created_at DESC
            """,
            params,
        ).fetchall()
    return _rows_to_dicts(rows, {"credentials", "metadata"})


def get_integration(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM integrations WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row, {"credentials", "metadata"})


def update_integration(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {
        "name",
        "provider",
        "entity_type",
        "entity_id",
        "auth_type",
        "credentials",
        "scope",
        "status",
        "expires_at",
        "last_used_at",
        "metadata",
    }
    assignments: list[str] = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        if key in {"credentials", "metadata"}:
            params.append(_normalize_json_text(value, "{}"))
        else:
            params.append(value)
    if not assignments:
        return get_integration(id)
    assignments.append("updated_at = ?")
    params.append(_now_iso())
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE integrations SET {', '.join(assignments)} WHERE id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_integration(id)


def delete_integration(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM integrations WHERE id = ?", (id,))
    return cur.rowcount > 0


def create_document(
    id: str | None = None,
    title: str = "",
    doc_type: str = "general",
    content: str = "",
    format: str = "markdown",
    project_slug: str = "",
    client_id: str = "",
    entity_type: str = "",
    entity_id: str = "",
    tags: list[str] | str | None = None,
    created_by: str = "",
) -> dict[str, Any]:
    document_id = id or str(uuid.uuid4())
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO documents (
                id, title, doc_type, content, format, project_slug, client_id,
                entity_type, entity_id, version, status, tags, created_by,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'draft', ?, ?, ?, ?)
            """,
            (
                document_id,
                title,
                doc_type,
                content,
                format,
                project_slug,
                client_id,
                entity_type,
                entity_id,
                _normalize_json_text(tags, "[]"),
                created_by,
                now,
                now,
            ),
        )
    return get_document(document_id) or {}


def list_documents(
    project_slug: str | None = None,
    doc_type: str | None = None,
    client_id: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if project_slug:
        clauses.append("project_slug = ?")
        params.append(project_slug)
    if doc_type:
        clauses.append("doc_type = ?")
        params.append(doc_type)
    if client_id:
        clauses.append("client_id = ?")
        params.append(client_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM documents
            {where}
            ORDER BY updated_at DESC, created_at DESC, title ASC
            """,
            params,
        ).fetchall()
    return _rows_to_dicts(rows, {"tags"})


def get_document(id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row, {"tags"})


def update_document(id: str, **kwargs: Any) -> dict[str, Any] | None:
    allowed = {
        "title",
        "doc_type",
        "content",
        "format",
        "project_slug",
        "client_id",
        "entity_type",
        "entity_id",
        "version",
        "status",
        "tags",
        "created_by",
    }
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
        return get_document(id)
    assignments.append("updated_at = ?")
    params.append(_now_iso())
    params.append(id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE documents SET {', '.join(assignments)} WHERE id = ?", params)
    if cur.rowcount == 0:
        return None
    return get_document(id)


def delete_document(id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM documents WHERE id = ?", (id,))
    return cur.rowcount > 0


def log_event(
    event_type: str,
    entity_type: str,
    entity_id: str,
    actor: str,
    summary: str,
    detail: dict[str, Any] | str,
    level: str,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO events_log (
                event_type, entity_type, entity_id, actor, summary, detail, level, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_type,
                entity_type,
                entity_id,
                actor,
                summary,
                _normalize_json_text(detail, "{}"),
                level,
                _now_iso(),
            ),
        )


def list_events(
    event_type: str | None = None,
    entity_type: str | None = None,
    level: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if event_type:
        clauses.append("event_type = ?")
        params.append(event_type)
    if entity_type:
        clauses.append("entity_type = ?")
        params.append(entity_type)
    if level:
        clauses.append("level = ?")
        params.append(level)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM events_log
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return _rows_to_dicts(rows, {"detail"})


def get_pref(user_id: int, key: str) -> Any:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM user_preferences WHERE user_id = ? AND key = ?",
            (user_id, key),
        ).fetchone()
    return _maybe_json_loads(row["value"]) if row else None


def set_pref(user_id: int, key: str, value: Any) -> None:
    stored = value if isinstance(value, str) else _json_dumps(value)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO user_preferences (user_id, key, value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (user_id, key, stored, _now_iso()),
        )


def get_all_prefs(user_id: int) -> dict[str, Any]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT key, value FROM user_preferences WHERE user_id = ? ORDER BY key ASC",
            (user_id,),
        ).fetchall()
    return {row["key"]: _maybe_json_loads(row["value"]) for row in rows}


def get_full_context() -> dict[str, Any]:
    """Return a comprehensive context snapshot for Inez — all active data."""
    return {
        "projects": list_projects(),
        "clients": list_clients(),
        "agents": list_agents(status="active"),
        "automations": list_automations(status="active"),
        "todos": list_todos(status="pending") + list_todos(status="in_progress"),
        "recent_events": list_events(limit=20),
    }


if __name__ == "__main__":
    init_schema()
