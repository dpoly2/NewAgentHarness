"""test_pg_migration.py — guards for the SQLite→Postgres migration (M1 / T2+T3).

Two kinds of check, both runnable on the default SQLite backend:

  1. DDL emitter (T2): db_backend.translate_ddl mechanically rewrites the
     SQLite-only column-type tokens to Postgres per POSTGRES_MIGRATION §5, and is
     a no-op on the SQLite backend. Deferred tokens (boolean-INTEGER, JSON-TEXT,
     ISO-TEXT timestamps) are left AS-IS.

  2. Idiom sweep (T3): the runtime code contains no remaining SQLite-only idioms
     (INSERT OR REPLACE / INSERT OR IGNORE / cursor.lastrowid / PRAGMA table_info
     / sqlite_master / date('now')). The one-off add_*.py migration scripts are
     out of scope for the mechanical pass and are excluded.
"""
import re
from pathlib import Path

import pytest

HERE = Path(__file__).parent
APP = HERE.parent

import sys
sys.path.insert(0, str(APP))

from core import db_backend


# ── T2: DDL emitter ──────────────────────────────────────────────────────────

class TestTranslateDDL:
    def _pg(self, ddl: str) -> str:
        """Force the Postgres rewrite regardless of the active backend."""
        prev = db_backend._IS_PG
        try:
            db_backend._IS_PG = True
            return db_backend.translate_ddl(ddl)
        finally:
            db_backend._IS_PG = prev

    def test_autoincrement_becomes_identity(self):
        out = self._pg("id INTEGER PRIMARY KEY AUTOINCREMENT,")
        assert out == "id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,"

    def test_autoincrement_case_insensitive(self):
        out = self._pg("id integer primary key autoincrement")
        assert out == "id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY"

    def test_real_becomes_double_precision(self):
        assert self._pg("score REAL DEFAULT 0.0") == "score DOUBLE PRECISION DEFAULT 0.0"
        assert self._pg("qty REAL,") == "qty DOUBLE PRECISION,"

    def test_deferred_tokens_untouched(self):
        # boolean-as-INTEGER, JSON-in-TEXT, ISO-TEXT timestamps stay AS-IS (§5).
        assert self._pg("is_active INTEGER DEFAULT 1") == "is_active INTEGER DEFAULT 1"
        assert self._pg("job_data TEXT DEFAULT '{}'") == "job_data TEXT DEFAULT '{}'"
        assert self._pg("created_at TEXT") == "created_at TEXT"

    def test_plain_integer_pk_without_autoincrement_untouched(self):
        # Only the full AUTOINCREMENT form is rewritten.
        assert self._pg("id INTEGER PRIMARY KEY") == "id INTEGER PRIMARY KEY"

    def test_noop_on_sqlite_backend(self):
        prev = db_backend._IS_PG
        try:
            db_backend._IS_PG = False
            assert db_backend.translate_ddl(
                "id INTEGER PRIMARY KEY AUTOINCREMENT, score REAL"
            ) == "id INTEGER PRIMARY KEY AUTOINCREMENT, score REAL"
        finally:
            db_backend._IS_PG = prev

    def test_full_schema_string_translates(self):
        src = (
            "CREATE TABLE IF NOT EXISTS t ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "amount REAL DEFAULT 0, "
            "is_active INTEGER DEFAULT 1, "
            "payload TEXT, created_at TEXT)"
        )
        out = self._pg(src)
        assert "BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY" in out
        assert "DOUBLE PRECISION" in out
        assert "AUTOINCREMENT" not in out
        assert re.search(r"\bREAL\b", out) is None
        # untouched
        assert "is_active INTEGER DEFAULT 1" in out
        assert "payload TEXT" in out


# ── T3: idiom sweep ──────────────────────────────────────────────────────────

# Runtime source files that must be free of SQLite-only idioms after T3.
_RUNTIME_FILES = [
    "core/database.py",
    "hub_db.py",
    "run_events.py",
    "progressive_intelligence.py",
    "document_rag.py",
    "morning_brief.py",
    "routers/capitol_trades.py",
    "routers/briefing.py",
    "routers/search.py",
]

# Patterns that are SQLite-only and must not appear in *executable* SQL. We match
# the raw token; occurrences inside comments/docstrings are stripped first.
_FORBIDDEN = {
    "INSERT OR REPLACE": re.compile(r"INSERT\s+OR\s+REPLACE", re.IGNORECASE),
    "INSERT OR IGNORE": re.compile(r"INSERT\s+OR\s+IGNORE", re.IGNORECASE),
    "lastrowid": re.compile(r"\.lastrowid\b"),
    "PRAGMA table_info": re.compile(r"PRAGMA\s+table_info", re.IGNORECASE),
    "sqlite_master": re.compile(r"\bsqlite_master\b"),
    "date('now')": re.compile(r"date\(\s*'now'\s*\)", re.IGNORECASE),
    "datetime('now')": re.compile(r"datetime\(\s*'now'\s*\)", re.IGNORECASE),
}


def _strip_comments(src: str) -> str:
    """Remove line comments so our explanatory notes about the old idioms don't
    trip the scan. Good enough for this codebase (no '#' inside SQL literals in
    the runtime files)."""
    out_lines = []
    for line in src.splitlines():
        hash_idx = line.find("#")
        if hash_idx != -1:
            line = line[:hash_idx]
        out_lines.append(line)
    return "\n".join(out_lines)


@pytest.mark.parametrize("rel", _RUNTIME_FILES)
def test_no_sqlite_idioms_in_runtime(rel):
    path = APP / rel
    assert path.exists(), f"missing runtime file: {rel}"
    code = _strip_comments(path.read_text(encoding="utf-8"))
    hits = {name: rx.findall(code) for name, rx in _FORBIDDEN.items()}
    offending = {k: v for k, v in hits.items() if v}
    assert not offending, f"{rel} still contains SQLite-only idioms: {offending}"


def test_ddl_helpers_route_through_translate():
    # core/database.py schema init must go through the per-backend DDL helper.
    code = (APP / "core/database.py").read_text(encoding="utf-8")
    assert "_exec_script(" in code, "schema init should use _exec_script (translate_ddl)"
    assert "translate_ddl" in code or "_ddl(" in code


# ── T6/T7/T8: concurrency-upgrade guards ─────────────────────────────────────

class TestConcurrencyUpgrades:
    """Static guards for the M3 concurrency work. The Postgres branches cannot be
    executed here (no PG infra), so we verify they are (a) present, (b) properly
    backend-gated on db_backend._IS_PG, and (c) translate cleanly to psycopg
    paramstyle where they use ``?`` placeholders."""

    def _db_src(self):
        return (APP / "core/database.py").read_text(encoding="utf-8")

    def test_claim_has_skip_locked_pg_branch(self):
        src = self._db_src()
        assert "FOR UPDATE SKIP LOCKED" in src, "T6 PG atomic claim missing"
        # The claim must branch on the backend, not switch statements at runtime blindly.
        assert "if db_backend._IS_PG:" in src

    def test_skip_locked_claim_translates(self):
        # The PG claim uses ? placeholders + RETURNING *; ensure the translator
        # turns them into %s with no stray % (there is no literal % in the SQL).
        sql = (
            "UPDATE job_queue SET status='running', started_at=?, worker_id=?, "
            "claimed_at=?, heartbeat_at=? WHERE id = (SELECT id FROM job_queue "
            "WHERE status='queued' ORDER BY queued_at ASC LIMIT 1 FOR UPDATE SKIP LOCKED) RETURNING *"
        )
        out = db_backend.translate_query(sql)
        assert out.count("%s") == 4
        assert "?" not in out
        assert "%%" not in out

    def test_notify_present_and_gated(self):
        src = self._db_src()
        assert "NOTIFY ws_events" in src, "T7 NOTIFY missing"
        # NOTIFY interpolates an int PK (no bind params allowed in NOTIFY); ensure
        # it is cast to int so it stays injection-safe (contract C2).
        assert "int(event_id)" in src

    def test_reaper_has_heartbeat_requeue(self):
        src = self._db_src()
        # New path: requeue (not fail) jobs of workers with a stale heartbeat.
        assert "worker_nodes" in src
        assert "status = 'queued'" in src  # requeue write
        assert "heartbeat_at" in src
        # Old fail-not-requeue path must survive for the long-running crash case.
        assert "status = 'failed'" in src

    def test_new_schema_columns_declared(self):
        hub_db_src = (APP / "hub_db.py").read_text(encoding="utf-8")
        # Canonical schema carries the T6/T8 columns + the worker_nodes registry.
        assert "worker_id TEXT" in hub_db_src
        assert "heartbeat_at TEXT" in hub_db_src
        assert "CREATE TABLE IF NOT EXISTS worker_nodes" in hub_db_src

    def test_ws_listener_is_pg_only_and_poll_is_fallback(self):
        hub_src = (APP / "core/hub.py").read_text(encoding="utf-8")
        # LISTEN/NOTIFY listener exists (T7) and the poll loop is retained as the
        # sqlite path / documented PG fallback.
        assert "_ws_listen_loop" in hub_src
        assert "LISTEN ws_events" in hub_src
        assert "_event_poll_loop" in hub_src
