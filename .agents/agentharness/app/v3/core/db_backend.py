"""core/db_backend.py — backend-selectable connection layer (T1).

Single seam that returns either a real ``sqlite3.Connection`` (default) or a
psycopg3-backed adapter presenting the *same* surface, so the ~31 call sites that
already use the four connection seams (``get_conn``, ``_db_connection``,
``_thread_conn``; ``get_db`` never existed) do not change.

The surface the codebase relies on (and this adapter reproduces for Postgres):

    conn.execute(sql, params) -> cursor with .fetchone()/.fetchall()/.rowcount
    conn.executescript(script)
    conn.commit() / conn.rollback() / conn.close()
    with conn: ...            # commit on success, rollback on error, NO close
    rows support row[int], row["col"], dict(row), and iteration-as-values
        (so ``dict(zip(cols, row))`` yields column->value), matching sqlite3.Row.

Selection: ``DB_BACKEND`` / ``DATABASE_URL`` in core.config (env-driven).
See docs/POSTGRES_MIGRATION.md (§4) and docs/DB_ACCESS_CONTRACT.md.

Transaction semantics (deliberate — read before changing):
  * Short-lived pooled connections (``get_connection``) run with
    ``autocommit=False`` and rely on the existing explicit ``commit()`` /
    ``with conn:`` calls — identical to sqlite CRUD. The pool resets (rolls back)
    a connection when it is returned, so a read-only path that forgets to commit
    cannot leak an open transaction.
  * The long-lived per-thread hot-path connection (``get_thread_connection``)
    runs with ``autocommit=True``. Two of the four hot pollers
    (``_count_queued_jobs``, ``_check_job_cancel_flag``) never commit; under a
    held transaction they would pin a stale MVCC snapshot and never see new
    rows. Autocommit keeps every poll fresh. ``commit()``/``rollback()`` are
    no-ops in autocommit (guarded below) so the writer pollers still work.

Known T3 follow-ups (this module intentionally does NOT paper over them):
  * 3 ``cursor.lastrowid`` sites -> must become ``RETURNING id`` (psycopg has no
    lastrowid; accessing it raises, which is the correct signal to fix them).
  * Dialect-specific SQL that is not just placeholders — ``sqlite_master``,
    ``date('now')`` (morning_brief.py) — needs per-query porting, not translation.
"""
from __future__ import annotations

import sqlite3
import threading
from typing import Any, Iterable, Optional, Sequence

from core.config import (
    DB_BACKEND,
    DB_PATH,
    DATABASE_URL,
    DB_POOL_MIN,
    DB_POOL_MAX,
)

_IS_PG = DB_BACKEND == "postgres"


# ── SQLite path (default, unchanged behavior) ────────────────────────────────

def _sqlite_connect() -> sqlite3.Connection:
    """Open a SQLite connection with the project's standard pragmas.

    Superset of the pragmas previously set in both _db_connection and
    hub_db.get_conn — strictly additive (WAL/foreign_keys were already there;
    synchronous/cache_size/temp_store are performance-only and safe).
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


# ── SQL translation (validated offline; see POSTGRES_MIGRATION §4) ────────────

def translate_query(sql: str) -> str:
    """Translate SQLite SQL to psycopg's paramstyle.

    Order matters: escape literal ``%`` to ``%%`` FIRST (so ``LIKE 'run_%'``
    survives), THEN convert ``?`` placeholders to ``%s`` (whose single ``%`` must
    stay single). Assumes no ``?`` appears inside a string literal and no
    pre-existing ``%s`` placeholders — both verified across the codebase; a unit
    test must keep them true (DB_ACCESS_CONTRACT / POSTGRES_MIGRATION §4.1).
    """
    return sql.replace("%", "%%").replace("?", "%s")


# ── DDL type translation (T2 — see POSTGRES_MIGRATION §5) ─────────────────────
#
# The schema *shape* is identical across backends — only column-type tokens
# differ. ``translate_ddl`` rewrites the handful of SQLite-only type tokens to
# their Postgres equivalents mechanically, per the §5 table. It is a no-op on the
# SQLite backend (returns the DDL unchanged). Applied to the schema strings in
# ``core/database.py`` and the ``init_schema`` statement list in ``hub_db.py`` so
# both backends emit correct DDL from one source string.
#
# Deliberately NOT translated (deferred to §9 hardening, per §5):
#   * boolean-as-INTEGER columns stay INTEGER (``_row_to_dict`` bool-coerces)
#   * JSON-in-TEXT stays TEXT (``_json_dumps``/``_json_loads`` are dialect-free)
#   * ISO-TEXT timestamps stay TEXT (``_reap_stale_jobs`` needs lexicographic <)
import re as _re

# ``INTEGER PRIMARY KEY AUTOINCREMENT`` -> ``BIGINT GENERATED ALWAYS AS IDENTITY
# PRIMARY KEY``. Case-insensitive, whitespace-tolerant. Must run before the bare
# ``\bREAL\b`` swap (it does not contain REAL, so order is only relative to other
# INTEGER rules — of which there are none).
_AUTOINC_RE = _re.compile(
    r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b", _re.IGNORECASE
)
# Standalone ``REAL`` type token -> ``DOUBLE PRECISION``. ``\b`` keeps it from
# touching identifiers/substrings; in this schema REAL only ever appears as a
# type keyword.
_REAL_RE = _re.compile(r"\bREAL\b", _re.IGNORECASE)


def translate_ddl(ddl: str) -> str:
    """Rewrite SQLite column-type tokens to Postgres. No-op on SQLite backend."""
    if not _IS_PG:
        return ddl
    ddl = _AUTOINC_RE.sub("BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY", ddl)
    ddl = _REAL_RE.sub("DOUBLE PRECISION", ddl)
    return ddl


# ── Postgres path ────────────────────────────────────────────────────────────

_pool = None
_pool_lock = threading.Lock()


def _pg_row_factory(cursor):
    """psycopg3 row factory producing sqlite3.Row-compatible rows."""
    cols = [c.name for c in cursor.description] if cursor.description else []

    def make_row(values: Sequence[Any]) -> "_PgRow":
        return _PgRow(cols, values)

    return make_row


class _PgRow:
    """Row that mimics sqlite3.Row: int + str indexing, dict()-able, iterates
    as values (so ``dict(zip(cols, row))`` and ``for r in rows`` both work)."""

    __slots__ = ("_cols", "_vals", "_idx")

    def __init__(self, cols: Sequence[str], vals: Sequence[Any]):
        self._cols = cols
        self._vals = vals
        self._idx: Optional[dict[str, int]] = None

    def keys(self) -> list[str]:
        return list(self._cols)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._vals[key]
        if self._idx is None:
            self._idx = {c: i for i, c in enumerate(self._cols)}
        try:
            return self._vals[self._idx[key]]
        except KeyError:
            raise IndexError(f"No column named {key!r}") from None

    def __iter__(self):
        return iter(self._vals)          # values, matching sqlite3.Row

    def __len__(self):
        return len(self._vals)

    def __contains__(self, key):
        return key in self._cols

    def get(self, key, default=None):
        try:
            return self[key]
        except (IndexError, KeyError):
            return default


def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                if not DATABASE_URL:
                    raise RuntimeError(
                        "DB_BACKEND=postgres but DATABASE_URL is empty "
                        "(set postgresql://user:pw@host:5432/archonhub)"
                    )
                from psycopg_pool import ConnectionPool
                _pool = ConnectionPool(
                    conninfo=DATABASE_URL,
                    min_size=DB_POOL_MIN,
                    max_size=DB_POOL_MAX,
                    kwargs={"autocommit": False},
                    open=True,
                )
    return _pool


class _PgConn:
    """sqlite3.Connection-compatible facade over a psycopg3 connection.

    Reuses a single cursor per connection (the codebase never holds two open
    cursors from one connection simultaneously), avoiding cursor accumulation on
    the long-lived thread connection.
    """

    def __init__(self, raw, pool=None):
        self._raw = raw
        self._pool = pool
        self._cur = None
        self._closed = False
        self.row_factory = None  # accepted + ignored; rows are always _PgRow

    def _cursor(self):
        if self._cur is None or getattr(self._cur, "closed", False):
            self._cur = self._raw.cursor(row_factory=_pg_row_factory)
        return self._cur

    def execute(self, sql: str, params: Iterable[Any] = ()):
        cur = self._cursor()
        cur.execute(translate_query(sql), list(params) if params else [])
        return cur

    def executescript(self, script: str):
        for stmt in _split_statements(script):
            self.execute(stmt)
        self.commit()

    def commit(self):
        if not self._raw.autocommit:
            self._raw.commit()

    def rollback(self):
        if not self._raw.autocommit:
            self._raw.rollback()

    def close(self):
        # Idempotent: a no-op after the first call. This lets the two idioms in
        # the codebase coexist on the pooled backend:
        #   * hub_db.py:            ``with get_conn() as conn: ...``   (no finally)
        #   * core/database.py:     ``with conn: ...`` inside ``try/finally:
        #                             conn.close()``
        # Both must return the pooled connection *exactly once*. __exit__ now
        # closes (see below), so the redundant ``finally: conn.close()`` in the
        # core/database.py idiom becomes a harmless second no-op.
        if self._closed:
            return
        self._closed = True
        # Return to pool if pooled; else close the dedicated (thread) connection.
        if self._pool is not None:
            try:
                self._pool.putconn(self._raw)
            except Exception:
                self._raw.close()
        else:
            self._raw.close()

    # Context manager: commit/rollback like sqlite3, then RETURN THE CONNECTION.
    # Rationale (PG-path leak fix, T5): unlike sqlite3.Connection.__exit__ (which
    # commits but does not close — harmless for a file DB that is GC'd), a pooled
    # psycopg connection MUST be handed back or the pool depletes. The ~141
    # ``with get_conn() as conn:`` sites in hub_db.py have no ``finally:
    # conn.close()``, so without closing here every one of them leaked a pooled
    # connection (observed: psycopg_pool.PoolTimeout after DB_POOL_MAX calls).
    # ``close()`` is idempotent, so the core/database.py idiom (``with conn:``
    # nested in ``try/finally: conn.close()``) still returns exactly once.
    # Thread connections (_pool is None) are not closed on __exit__ — the C4
    # "do not close the thread connection" contract is preserved because the hot
    # pollers never use ``with conn:``; they call execute()/commit() directly.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        if self._pool is not None:
            self.close()
        return False


def _split_statements(script: str) -> list[str]:
    """Split a multi-statement DDL script on ';'. Safe here because ArchonHub's
    schema scripts contain no ';' inside string literals."""
    return [s.strip() for s in script.split(";") if s.strip()]


# ── Public seam API ──────────────────────────────────────────────────────────

def get_connection():
    """Short-lived connection for per-call CRUD. Caller closes it (finally)."""
    if _IS_PG:
        pool = _get_pool()
        raw = pool.getconn()
        return _PgConn(raw, pool=pool)
    return _sqlite_connect()


_tls = threading.local()


def get_thread_connection():
    """Long-lived per-thread connection for the hot-path pollers. NEVER closed
    by callers (DB_ACCESS_CONTRACT C4)."""
    if _IS_PG:
        conn = getattr(_tls, "pgconn", None)
        if conn is None:
            import psycopg
            raw = psycopg.connect(DATABASE_URL, autocommit=True)
            conn = _PgConn(raw, pool=None)
            _tls.pgconn = conn
        return conn
    conn = getattr(_tls, "sqconn", None)
    if conn is None:
        conn = _sqlite_connect()
        _tls.sqconn = conn
    return conn


def table_columns(table: str) -> set[str]:
    """Backend-agnostic column introspection (replaces PRAGMA table_info)."""
    conn = get_connection()
    try:
        if _IS_PG:
            rows = conn.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
                (table,),
            ).fetchall()
            return {r[0] for r in rows}
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {r[1] for r in rows}
    except Exception:
        return set()
    finally:
        conn.close()


if __name__ == "__main__":
    # Offline self-test of the translator (no DB required).
    checks = [
        ("SELECT * FROM runs WHERE agent_id = ?",
         "SELECT * FROM runs WHERE agent_id = %s"),
        ("SELECT * FROM agent_memory WHERE agent_id = ? AND key LIKE 'run_%'",
         "SELECT * FROM agent_memory WHERE agent_id = %s AND key LIKE 'run_%%'"),
        ("INSERT INTO ws_events (payload_json, created_at) VALUES (?, ?)",
         "INSERT INTO ws_events (payload_json, created_at) VALUES (%s, %s)"),
    ]
    for sql, want in checks:
        got = translate_query(sql)
        assert got == want, f"{got!r} != {want!r}"
    print("translate_query: all checks pass")

    # translate_ddl is backend-gated; exercise the PG rewrites directly so the
    # self-test is meaningful even when running on the SQLite default.
    import core.db_backend as _self
    _prev = _self._IS_PG
    try:
        _self._IS_PG = True
        ddl_checks = [
            ("id INTEGER PRIMARY KEY AUTOINCREMENT,",
             "id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,"),
            ("score REAL DEFAULT 0.0,", "score DOUBLE PRECISION DEFAULT 0.0,"),
            ("qty REAL,", "qty DOUBLE PRECISION,"),
            # untouched tokens
            ("created_at TEXT", "created_at TEXT"),
            ("is_active INTEGER DEFAULT 1", "is_active INTEGER DEFAULT 1"),
            ("job_data TEXT DEFAULT '{}'", "job_data TEXT DEFAULT '{}'"),
        ]
        for ddl, want in ddl_checks:
            got = _self.translate_ddl(ddl)
            assert got == want, f"{got!r} != {want!r}"
    finally:
        _self._IS_PG = _prev
    # SQLite backend must leave DDL untouched.
    assert translate_ddl("id INTEGER PRIMARY KEY AUTOINCREMENT") == \
        "id INTEGER PRIMARY KEY AUTOINCREMENT"
    print("translate_ddl: all checks pass")
