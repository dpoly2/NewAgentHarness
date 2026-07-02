"""Unit tests for the FK topological-ordering in scripts/migrate_sqlite_to_pg.py.

Covers: parent-before-child ordering, multi-level chains, deterministic
tie-break, self-reference handling, ignoring edges to excluded tables, and
cycle detection. Pure function -- no DB, no Postgres required.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make app/v3 importable so `scripts.migrate_sqlite_to_pg` resolves.
_APP_ROOT = Path(__file__).resolve().parent.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from scripts.migrate_sqlite_to_pg import topological_order  # noqa: E402


def _before(order, parent, child):
    return order.index(parent) < order.index(child)


def test_simple_parent_before_child():
    deps = {"conversations": set(), "messages": {"conversations"}}
    order = topological_order(deps)
    assert set(order) == {"conversations", "messages"}
    assert _before(order, "conversations", "messages")


def test_multi_level_chain():
    # users -> uploaded_files -> file_chunks (matches real ArchonHub chain)
    deps = {
        "users": set(),
        "uploaded_files": {"users"},
        "file_chunks": {"uploaded_files"},
    }
    order = topological_order(deps)
    assert _before(order, "users", "uploaded_files")
    assert _before(order, "uploaded_files", "file_chunks")


def test_diamond_fanout():
    # tracked_politicians -> {politician_trades, copy_trade_signals}
    deps = {
        "tracked_politicians": set(),
        "politician_trades": {"tracked_politicians"},
        "copy_trade_signals": {"tracked_politicians"},
    }
    order = topological_order(deps)
    assert _before(order, "tracked_politicians", "politician_trades")
    assert _before(order, "tracked_politicians", "copy_trade_signals")


def test_deterministic_alphabetical_tiebreak():
    deps = {"zebra": set(), "apple": set(), "mango": set()}
    assert topological_order(deps) == ["apple", "mango", "zebra"]


def test_self_reference_is_ignored():
    # A table whose FK points at itself must not deadlock ordering.
    deps = {"nodes": {"nodes"}, "edges": {"nodes"}}
    order = topological_order(deps)
    assert _before(order, "nodes", "edges")


def test_edge_to_unknown_table_ignored():
    # FK to a table not in the migration set (e.g. an excluded FTS table)
    # should not raise or reorder.
    deps = {"messages": {"conversations_fts_missing"}}
    order = topological_order(deps)
    assert order == ["messages"]


def test_cycle_detection():
    deps = {"a": {"b"}, "b": {"a"}}
    with pytest.raises(ValueError, match="[Cc]yclic"):
        topological_order(deps)


def test_three_node_cycle_detection():
    deps = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
    with pytest.raises(ValueError):
        topological_order(deps)


def test_empty_graph():
    assert topological_order({}) == []


def test_all_tables_present_in_output():
    deps = {
        "clients": set(),
        "projects": set(),
        "conversations": set(),
        "messages": {"conversations"},
        "corrections": {"messages"},
        "message_feedback": {"messages"},
        "automations": set(),
        "automation_runs": {"automations"},
    }
    order = topological_order(deps)
    assert set(order) == set(deps)
    assert _before(order, "messages", "corrections")
    assert _before(order, "messages", "message_feedback")
    assert _before(order, "automations", "automation_runs")
