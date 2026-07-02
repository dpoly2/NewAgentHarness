#!/usr/bin/env python
"""One-time SQLite -> Postgres data migration for ArchonHub (task T4).

Implements docs/POSTGRES_MIGRATION.md §8 and obeys docs/DB_ACCESS_CONTRACT.md.

What it does
------------
1. Creates the Postgres schema by calling the app's *existing* schema init
   (``core.database._init_schema`` -> ``hub_db.init_schema`` + the ``_ensure_*``
   path) with ``DB_BACKEND=postgres``. The schema is NOT re-declared here; the
   app remains the single source of truth (contract C10, §8.1).
2. Reads every ordinary table from a *copy* of the SQLite DB, enumerated from
   ``sqlite_master`` and topologically ordered by the FK graph read via
   ``PRAGMA foreign_key_list`` (parents before children, §8.2/§8.3).
3. Inserts into Postgres preserving primary keys (including integer ids) with
   batched ``executemany`` (§8.4).
4. Resets IDENTITY sequences with ``setval(pg_get_serial_sequence(...))`` (§8.5).
5. Validates row counts per table and spot-checks ``hub_config``, ``users``
   (admin row) and the newest 10 ``runs`` / ``job_queue`` rows (§8.6). Prints a
   PASS/FAIL summary and exits non-zero on any mismatch.
6. ``--dry-run`` does all of the read side against SQLite only (enumerate,
   order, count, plan) WITHOUT requiring a live Postgres or psycopg (§8.7).

Safety
------
* Never touches the live DB file: ``--sqlite <path>`` is required, and the
  default live path (``memory/runs_v3.db``) is refused unless ``--force`` is
  also given. Always run against a snapshot/copy.
* Parameterized queries only; table/column identifiers come from the DB's own
  catalog (never user input) and are quoted with the driver's quoting
  (contract C2). psycopg is imported lazily so ``--dry-run`` runs on stdlib
  ``sqlite3`` alone.

Usage
-----
    python scripts/migrate_sqlite_to_pg.py --sqlite copy.db --dry-run
    DB_BACKEND=postgres DATABASE_URL=postgresql://... \
        python scripts/migrate_sqlite_to_pg.py --sqlite snapshot.db
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# --- Locate the app package (app/v3) so we can import the schema init. --------
# scripts/ lives at app/v3/scripts/, so the app root is the parent directory.
_APP_ROOT = Path(__file__).resolve().parent.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

# Default *live* DB path (the one written by the ArchonHub Windows service).
# Refused unless --force. Mirrors core.config.DB_PATH without importing config
# (config import must not be required for --dry-run).
_LIVE_DB_PATH = (_APP_ROOT.parent.parent / "memory" / "runs_v3.db").resolve()

# SQLite FTS5 virtual table + its shadow tables. These are engine-internal and
# are NOT part of the Postgres schema (POSTGRES_MIGRATION §9 defers FTS to a
# tsvector/pg_trgm rebuild, task T13). Never copy them.
_FTS_SUFFIXES = ("_fts", "_fts_data", "_fts_idx", "_fts_docsize", "_fts_config")

_BATCH = 500


# =========================================================================
# FK-dependency (topological) ordering  --  pure, unit-tested in tests/
# =========================================================================
def topological_order(deps: Dict[str, Set[str]]) -> List[str]:
    """Return tables ordered parents-before-children given a FK dependency map.

    ``deps[t]`` is the set of tables ``t`` references via a foreign key (i.e.
    ``t`` must be inserted *after* those). Self-references are ignored (a row's
    parent is in the same table; PK preservation + deferred-free single-table
    insert order is handled by inserting the whole table at once). References to
    tables not present in ``deps`` are ignored (e.g. an already-excluded FTS
    table).

    Deterministic (alphabetical tie-break) so the plan is stable/reviewable.
    Raises ValueError if the FK graph contains a cycle among distinct tables.
    """
    all_tables = set(deps)
    # Normalize: drop self-refs and edges to unknown tables.
    clean: Dict[str, Set[str]] = {
        t: {d for d in ds if d != t and d in all_tables} for t, ds in deps.items()
    }

    ordered: List[str] = []
    placed: Set[str] = set()
    # Kahn-style: repeatedly emit tables whose deps are all already placed.
    while len(placed) < len(all_tables):
        ready = sorted(
            t for t in all_tables
            if t not in placed and clean[t] <= placed
        )
        if not ready:
            remaining = sorted(all_tables - placed)
            raise ValueError(
                "Cyclic foreign-key dependency among tables: "
                + ", ".join(remaining)
            )
        ordered.extend(ready)
        placed.update(ready)
    return ordered


# =========================================================================
# SQLite introspection
# =========================================================================
def _is_fts_table(name: str) -> bool:
    return any(name.endswith(s) for s in _FTS_SUFFIXES) or name.endswith("_fts")


def enumerate_tables(conn: sqlite3.Connection) -> List[str]:
    """Ordinary user tables from sqlite_master, excluding sqlite_* and FTS."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    out = []
    for (name,) in rows:
        if _is_fts_table(name):
            continue
        out.append(name)
    return out


def read_fk_deps(conn: sqlite3.Connection, tables: List[str]) -> Dict[str, Set[str]]:
    """Build ``{table: {referenced tables}}`` via PRAGMA foreign_key_list."""
    tset = set(tables)
    deps: Dict[str, Set[str]] = {t: set() for t in tables}
    for t in tables:
        # PRAGMA cannot be parameterized; identifier comes from the DB catalog,
        # never user input, and is quoted -> contract C2 compliant.
        for row in conn.execute(f'PRAGMA foreign_key_list("{t}")').fetchall():
            parent = row[2]  # "table" column of foreign_key_list
            if parent in tset:
                deps[t].add(parent)
    return deps


def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [row[1] for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]


def identity_tables(conn: sqlite3.Connection, tables: List[str]) -> List[str]:
    """Tables whose ``id`` is INTEGER PRIMARY KEY AUTOINCREMENT.

    In Postgres these become ``BIGINT GENERATED ALWAYS AS IDENTITY`` (§5) and
    their sequence must be re-set after a PK-preserving load (§8.5).
    """
    out = []
    for name, sql in conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'"
    ).fetchall():
        if name not in tables:
            continue
        if sql and "AUTOINCREMENT" in sql.upper() and "id" in table_columns(conn, name):
            out.append(name)
    return sorted(out)


def row_count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]


# =========================================================================
# Dry-run
# =========================================================================
def build_plan(sqlite_path: Path) -> dict:
    conn = sqlite3.connect(str(sqlite_path))
    try:
        conn.row_factory = sqlite3.Row
        tables = enumerate_tables(conn)
        deps = read_fk_deps(conn, tables)
        order = topological_order(deps)
        counts = {t: row_count(conn, t) for t in order}
        ident = identity_tables(conn, order)
        # Which FTS/shadow tables did we deliberately skip?
        all_raw = [
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        skipped = [n for n in all_raw if _is_fts_table(n)]
        return {
            "order": order,
            "deps": {t: sorted(deps[t]) for t in order},
            "counts": counts,
            "identity_tables": ident,
            "skipped_fts": skipped,
        }
    finally:
        conn.close()


def print_plan(plan: dict) -> None:
    order = plan["order"]
    counts = plan["counts"]
    deps = plan["deps"]
    total = sum(counts.values())
    print("=" * 70)
    print("MIGRATION PLAN (dry-run)")
    print("=" * 70)
    print(f"Tables to migrate: {len(order)}   Total rows: {total}")
    if plan["skipped_fts"]:
        print(f"Skipped (SQLite FTS shadow/virtual, rebuilt on PG later): "
              f"{', '.join(plan['skipped_fts'])}")
    print("-" * 70)
    print(f"{'#':>3}  {'table':40s} {'rows':>7}  fk-> parents")
    print("-" * 70)
    for i, t in enumerate(order, 1):
        d = deps[t]
        dtxt = ", ".join(d) if d else "-"
        print(f"{i:>3}  {t:40s} {counts[t]:>7}  {dtxt}")
    print("-" * 70)
    print(f"IDENTITY tables (sequence reset after load): "
          f"{', '.join(plan['identity_tables'])}")
    print("=" * 70)


# =========================================================================
# Live Postgres load
# =========================================================================
def _init_pg_schema() -> None:
    """Create the PG schema by calling the app's own init. Single source of
    truth (§8.1) -- we do not declare any DDL here."""
    if os.environ.get("DB_BACKEND", "").strip().lower() != "postgres":
        raise SystemExit(
            "Live migration requires DB_BACKEND=postgres (and DATABASE_URL). "
            "For a no-Postgres validation run, use --dry-run."
        )
    from core import database  # imported lazily; pulls in the PG adapter
    database._init_schema()


def _pg_quote_ident(name: str) -> str:
    # Table/column names come from the SQLite catalog, not user input. Quote
    # for Postgres (double-quote, escape embedded quotes) so mixed-case /
    # reserved names survive. Values always go through %s params (C2).
    return '"' + name.replace('"', '""') + '"'


def load_into_pg(sqlite_path: Path, only_tables: List[str] | None = None) -> int:
    """Full load path. Returns process exit code (0 = PASS)."""
    _init_pg_schema()

    # Lazy imports: psycopg is only needed on the live path.
    from core import db_backend

    src = sqlite3.connect(str(sqlite_path))
    src.row_factory = sqlite3.Row
    try:
        tables = enumerate_tables(src)
        deps = read_fk_deps(src, tables)
        order = topological_order(deps)
        if only_tables:
            order = [t for t in order if t in set(only_tables)]
        ident = identity_tables(src, order)

        pg = db_backend.get_connection()
        try:
            # ---- Insert in FK order, preserving PKs, batched. ---------------
            for t in order:
                cols = table_columns(src, t)
                if not cols:
                    continue
                rows = src.execute(f'SELECT * FROM "{t}"').fetchall()
                if not rows:
                    print(f"  [{t}] 0 rows")
                    continue
                collist = ", ".join(_pg_quote_ident(c) for c in cols)
                placeholders = ", ".join(["%s"] * len(cols))
                sql = (f'INSERT INTO {_pg_quote_ident(t)} ({collist}) '
                       f'VALUES ({placeholders})')
                data = [tuple(r[c] for c in cols) for r in rows]
                cur = pg.cursor()
                for i in range(0, len(data), _BATCH):
                    cur.executemany(sql, data[i:i + _BATCH])
                print(f"  [{t}] inserted {len(data)} rows")
            pg.commit()

            # ---- Reset IDENTITY sequences (§8.5). --------------------------
            for t in ident:
                # pg_get_serial_sequence takes the table name as a *value*, so
                # this is fully parameterized. Returns NULL if no sequence ->
                # setval is skipped by the guard below.
                pg.execute(
                    "SELECT setval("
                    "  pg_get_serial_sequence(%s, 'id'),"
                    "  (SELECT COALESCE(MAX(id), 1) FROM " + _pg_quote_ident(t) + "),"
                    "  (SELECT COUNT(*) > 0 FROM " + _pg_quote_ident(t) + ")"
                    ") WHERE pg_get_serial_sequence(%s, 'id') IS NOT NULL",
                    (t, t),
                )
            pg.commit()

            # ---- Validate (§8.6). ------------------------------------------
            ok = _validate(src, pg, order)
            return 0 if ok else 1
        finally:
            pg.close()
    finally:
        src.close()


def _validate(src: sqlite3.Connection, pg, order: List[str]) -> bool:
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)
    ok = True

    # Per-table COUNT(*) parity.
    for t in order:
        s = row_count(src, t)
        p = pg.execute(f"SELECT COUNT(*) AS c FROM {_pg_quote_ident(t)}").fetchone()
        pcount = p["c"] if hasattr(p, "__getitem__") else p[0]
        status = "PASS" if s == pcount else "FAIL"
        if s != pcount:
            ok = False
        print(f"  count {t:40s} sqlite={s:>7} pg={pcount:>7}  {status}")

    # Spot-check hub_config total.
    if "hub_config" in order:
        s = row_count(src, "hub_config")
        p = pg.execute("SELECT COUNT(*) AS c FROM hub_config").fetchone()
        pc = p["c"] if hasattr(p, "__getitem__") else p[0]
        st = "PASS" if s == pc else "FAIL"
        ok = ok and (s == pc)
        print(f"  spot  hub_config keys sqlite={s} pg={pc}  {st}")

    # Spot-check admin user present.
    if "users" in order:
        row = pg.execute(
            "SELECT id, username FROM users WHERE username = %s", ("admin",)
        ).fetchone()
        st = "PASS" if row else "FAIL"
        ok = ok and bool(row)
        print(f"  spot  users admin row present: {'yes' if row else 'NO'}  {st}")

    # Spot-check newest 10 runs / job_queue ids match.
    for t in ("runs", "job_queue"):
        if t not in order:
            continue
        s_ids = [r[0] for r in src.execute(
            f'SELECT id FROM "{t}" ORDER BY id DESC LIMIT 10').fetchall()]
        p_rows = pg.execute(
            f"SELECT id FROM {_pg_quote_ident(t)} ORDER BY id DESC LIMIT 10"
        ).fetchall()
        p_ids = [(r["id"] if hasattr(r, "__getitem__") else r[0]) for r in p_rows]
        st = "PASS" if s_ids == p_ids else "FAIL"
        ok = ok and (s_ids == p_ids)
        print(f"  spot  newest-10 {t} ids match: {st}")

    print("=" * 70)
    print("RESULT:", "PASS" if ok else "FAIL")
    print("=" * 70)
    return ok


# =========================================================================
# CLI
# =========================================================================
def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SQLite -> Postgres data migration (T4)")
    ap.add_argument("--sqlite", required=True,
                    help="Path to the SQLite DB COPY to read from.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Read-side only: enumerate, FK-order, count. No Postgres.")
    ap.add_argument("--force", action="store_true",
                    help="Permit pointing --sqlite at the default live DB path.")
    ap.add_argument("--table", action="append", dest="tables",
                    help="Limit to this table (repeatable). Live path only.")
    args = ap.parse_args(argv)

    sqlite_path = Path(args.sqlite).resolve()
    if not sqlite_path.exists():
        print(f"ERROR: SQLite file not found: {sqlite_path}", file=sys.stderr)
        return 2

    if sqlite_path == _LIVE_DB_PATH and not args.force:
        print(
            f"REFUSING to read the live DB at {sqlite_path} without --force.\n"
            f"Copy it to a snapshot first and pass that copy to --sqlite.",
            file=sys.stderr,
        )
        return 2

    if args.dry_run:
        plan = build_plan(sqlite_path)
        print_plan(plan)
        return 0

    return load_into_pg(sqlite_path, only_tables=args.tables)


if __name__ == "__main__":
    raise SystemExit(main())
