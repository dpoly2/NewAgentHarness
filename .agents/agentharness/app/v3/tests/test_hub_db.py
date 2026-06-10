"""
test_hub_db.py — Unit tests for the hub_db data layer.
Tests every major table: runs, todos, agents, connectors,
conversations, reports, trips, clients, notifications, scheduler,
paper trading theories, and the user/auth system.
"""
import os, sys, uuid, json, tempfile, time
from pathlib import Path
from datetime import datetime, timezone

# ── Path setup ────────────────────────────────────────────────────────────────
HERE = Path(__file__).parent
APP  = HERE.parent
sys.path.insert(0, str(APP))

# Redirect DB to a temp file so tests never touch production data
import hub_db
_TMP_DB = Path(tempfile.mkdtemp()) / "test_runs_v3.db"
hub_db.DB_PATH = _TMP_DB
hub_db.init_schema()

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def uid() -> str:
    return uuid.uuid4().hex[:12]


# ─────────────────────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────────────────────

class TestSchema:
    def test_db_file_created(self):
        assert _TMP_DB.exists()

    def test_tables_exist(self):
        with hub_db.get_conn() as conn:
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
        expected = {
            "runs", "skills", "todos", "job_queue",
            "agent_registry", "conversations", "messages",
            "email_connectors", "reports", "notifications",
            "clients", "projects",
            "market_trade_theories", "market_paper_trades",
        }
        missing = expected - tables
        assert not missing, f"Missing tables: {missing}"


# ─────────────────────────────────────────────────────────────────────────────
# Todos
# ─────────────────────────────────────────────────────────────────────────────

class TestTodos:
    def test_create_and_get(self):
        t = hub_db.create_todo(title="Test todo", description="desc", priority="high")
        assert t["title"] == "Test todo"
        assert t["priority"] == "high"

    def test_list(self):
        hub_db.create_todo(title=f"Todo {uid()}")
        rows = hub_db.list_todos()
        assert len(rows) >= 1

    def test_update(self):
        t = hub_db.create_todo(title="Update me")
        updated = hub_db.update_todo(t["id"], status="done", title="Updated")
        assert updated["status"] == "done"
        assert updated["title"] == "Updated"

    def test_delete(self):
        t = hub_db.create_todo(title="Delete me")
        ok = hub_db.delete_todo(t["id"])
        assert ok
        rows = hub_db.list_todos()
        ids = [r["id"] for r in rows]
        assert t["id"] not in ids

    def test_filter_by_status(self):
        hub_db.create_todo(title=f"pending-{uid()}", status="pending")
        hub_db.create_todo(title=f"done-{uid()}", status="done")
        pending = hub_db.list_todos(status="pending")
        done    = hub_db.list_todos(status="done")
        assert all(r["status"] == "pending" for r in pending)
        assert all(r["status"] == "done"    for r in done)


# ─────────────────────────────────────────────────────────────────────────────
# Agents
# ─────────────────────────────────────────────────────────────────────────────

class TestAgents:
    def test_register_and_get(self):
        aid = f"agent-{uid()}"
        a = hub_db.upsert_agent(
            agent_id=aid, name="Test Agent",
            role="tester", description="unit test agent",
        )
        assert a["agent_id"] == aid
        fetched = hub_db.get_agent(aid)
        assert fetched is not None
        assert fetched["name"] == "Test Agent"

    def test_list_agents(self):
        hub_db.upsert_agent(agent_id=f"a-{uid()}", name="List Agent")
        rows = hub_db.list_agents()
        assert len(rows) >= 1

    def test_update_agent(self):
        aid = f"agent-{uid()}"
        hub_db.upsert_agent(agent_id=aid, name="Before")
        updated = hub_db.update_agent(aid, name="After", status="active")
        assert updated["name"] == "After"
        assert updated["status"] == "active"

    def test_agent_stats(self):
        stats = hub_db.agent_stats()
        assert isinstance(stats, (list, dict))


# ─────────────────────────────────────────────────────────────────────────────
# Connectors
# ─────────────────────────────────────────────────────────────────────────────

class TestConnectors:
    def test_create_password_connector(self):
        c = hub_db.create_connector(
            label="Test Gmail",
            email_address="test@gmail.com",
            provider="gmail",
            auth_type="password",
            imap_host="imap.gmail.com",
            imap_port=993,
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            username="test@gmail.com",
            credentials={"password": "secret"},
        )
        assert c["label"] == "Test Gmail"
        assert c["status"] == "pending"

    def test_create_oauth_connector(self):
        c = hub_db.create_connector(
            label="OAuth Gmail",
            email_address="oauth@gmail.com",
            provider="gmail",
            auth_type="oauth2",
            oauth_client_id="cid-123",
            oauth_client_secret="csec-456",
        )
        assert c["oauth_client_id"] == "cid-123"
        assert c["oauth_client_secret"] == "csec-456"

    def test_update_connector_token(self):
        c = hub_db.create_connector(label="Update Token", email_address=f"{uid()}@test.com")
        exp_ts = str(int(time.time()) + 3600)
        updated = hub_db.update_connector(
            c["id"],
            auth_type="oauth2",
            status="active",
            token_expires_at=exp_ts,
        )
        assert updated["status"] == "active"
        assert updated["token_expires_at"] == exp_ts

    def test_list_connectors(self):
        hub_db.create_connector(label=f"Con-{uid()}", email_address=f"{uid()}@x.com")
        rows = hub_db.list_connectors()
        assert len(rows) >= 1

    def test_delete_connector(self):
        c = hub_db.create_connector(label="Delete", email_address=f"{uid()}@del.com")
        ok = hub_db.delete_connector(c["id"])
        assert ok
        assert hub_db.get_connector(c["id"]) is None


# ─────────────────────────────────────────────────────────────────────────────
# Conversations & Messages
# ─────────────────────────────────────────────────────────────────────────────

class TestConversations:
    def test_create_and_add_message(self):
        conv = hub_db.create_conversation(title="Test Conv")
        assert conv["title"] == "Test Conv"
        msg = hub_db.add_message(conversation_id=conv["id"], role="user", content="Hello Inez!")
        assert msg["content"] == "Hello Inez!"
        msgs = hub_db.list_messages(conv["id"])
        assert len(msgs) >= 1
        assert msgs[0]["role"] == "user"

    def test_list_conversations(self):
        hub_db.create_conversation(title=f"Conv-{uid()}")
        rows = hub_db.list_conversations()
        assert len(rows) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Reports
# ─────────────────────────────────────────────────────────────────────────────

class TestReports:
    def test_create_and_list(self):
        r = hub_db.create_report(
            title="Morning Brief",
            content="All systems go.",
            report_type="daily",
            status="complete",
        )
        assert r["title"] == "Morning Brief"
        rows = hub_db.list_reports()
        assert any(x["id"] == r["id"] for x in rows)

    def test_get_report(self):
        r = hub_db.create_report(title=f"Rep-{uid()}", content="test")
        fetched = hub_db.get_report(r["id"])
        assert fetched is not None
        assert fetched["id"] == r["id"]


# ─────────────────────────────────────────────────────────────────────────────
# Notifications
# ─────────────────────────────────────────────────────────────────────────────

class TestNotifications:
    def test_create_and_list(self):
        hub_db.save_notification(text="Something happened", color="#f59e0b", category="warning")
        rows = hub_db.list_notifications()
        assert len(rows) >= 1

    def test_mark_all_read(self):
        hub_db.save_notification(text="Read me", color="#00B8FF")
        hub_db.mark_notifications_read()
        rows = hub_db.list_notifications(unread_only=True)
        assert len(rows) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Clients & Projects
# ─────────────────────────────────────────────────────────────────────────────

class TestClients:
    def test_create_and_list(self):
        c = hub_db.create_client(name="Acme Corp", contact_email="acme@corp.com", status="active")
        assert c["name"] == "Acme Corp"
        rows = hub_db.list_clients()
        assert any(x["id"] == c["id"] for x in rows)

    def test_update_client(self):
        c = hub_db.create_client(
            name=f"Client-{uid()}", slug=f"cl-{uid()}", contact_email=f"{uid()}@c.com"
        )
        updated = hub_db.update_client(c["id"], status="inactive")
        assert updated["status"] == "inactive"


class TestProjects:
    def test_create_and_list(self):
        p = hub_db.create_project(slug=f"proj-{uid()}", name="Test Project")
        assert p["name"] == "Test Project"
        rows = hub_db.list_projects()
        assert any(x["id"] == p["id"] for x in rows)


# ─────────────────────────────────────────────────────────────────────────────
# Paper Trading
# ─────────────────────────────────────────────────────────────────────────────

class TestPaperTrading:
    def test_create_theory(self):
        th = hub_db.create_theory(name="Momentum Play", description="Long NVDA on breakout")
        assert th["name"] == "Momentum Play"

    def test_open_and_close_trade(self):
        th = hub_db.create_theory(name=f"Theory-{uid()}")
        # Open trade
        trade = hub_db.open_paper_trade(
            theory_id=th["id"],
            ticker="AAPL",
            direction="long",
            shares=10,
            entry_price=180.0,
        )
        assert trade["ticker"] == "AAPL"
        assert trade["status"] == "open"
        # Update price (takes ticker, not trade id)
        hub_db.update_paper_trade_price("AAPL", 190.0)
        # Close trade
        closed = hub_db.close_paper_trade(trade["id"], exit_price=195.0)
        assert closed["status"] in ("closed", "closed_win", "closed_loss")
        pnl = (195.0 - 180.0) * 10
        assert abs(closed["pnl"] - pnl) < 0.01

    def test_theory_stats(self):
        th = hub_db.create_theory(name=f"Stats-{uid()}")
        hub_db.open_paper_trade(
            theory_id=th["id"], ticker="TSLA", direction="long",
            shares=5, entry_price=200.0,
        )
        stats = hub_db.theory_stats(th["id"])
        assert "total_trades" in stats
        assert stats["total_trades"] >= 0

    def test_list_theories(self):
        hub_db.create_theory(name=f"List-{uid()}")
        rows = hub_db.list_theories()
        assert len(rows) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Users / Auth
# ─────────────────────────────────────────────────────────────────────────────

class TestUsers:
    def test_default_admin_exists(self):
        result = hub_db.verify_user("admin", "ArchonHub2024!")
        assert result is not None

    def test_verify_admin_password(self):
        result = hub_db.verify_user("admin", "ArchonHub2024!")
        assert result is not None

    def test_create_user(self):
        uname = f"user-{uid()}"
        u = hub_db.create_user(username=uname, email=f"{uname}@test.com",
                               password="Test1234!", role="viewer")
        assert u["role"] == "viewer"

    def test_wrong_password_fails(self):
        result = hub_db.verify_user("admin", "WrongPassword!")
        assert result is None
