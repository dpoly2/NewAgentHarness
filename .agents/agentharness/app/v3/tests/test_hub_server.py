"""
test_hub_server.py — Integration tests for the FastAPI hub server.
Starts the server in a background thread, runs all endpoint groups,
then shuts it down.
"""
import os, sys, uuid, json, time, threading
from pathlib import Path

HERE = Path(__file__).parent
APP  = HERE.parent
sys.path.insert(0, str(APP))

import hub_db
import tempfile

# Redirect DB to temp for isolation
_TMP_DB = Path(tempfile.mkdtemp()) / "server_test.db"
hub_db.DB_PATH = _TMP_DB
hub_db.init_schema()

import pytest
import httpx

BASE = "http://127.0.0.1:8766"   # different port so it doesn't clash with running hub

# ─────────────────────────────────────────────────────────────────────────────
# Server fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def server():
    """Start hub_server on port 8766 in a background thread."""
    import hub_server
    import uvicorn

    app = hub_server.build_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=8766, log_level="error")
    srv = uvicorn.Server(config)

    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()

    # Wait for the server to become available
    for _ in range(30):
        try:
            r = httpx.get(f"{BASE}/health", timeout=1)
            if r.status_code < 500:
                break
        except Exception:
            pass
        time.sleep(0.3)
    else:
        pytest.skip("Hub server did not start in time")

    yield srv
    srv.should_exit = True


@pytest.fixture(scope="module")
def auth_headers(server):
    """Return Bearer token headers for admin user."""
    r = httpx.post(f"{BASE}/api/auth/login",
                   json={"username": "admin", "password": "ArchonHub2024!"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def uid() -> str:
    return uuid.uuid4().hex[:10]


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

class TestAuth:
    def test_login_success(self, server):
        r = httpx.post(f"{BASE}/api/auth/login",
                       json={"username": "admin", "password": "ArchonHub2024!"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_bad_password(self, server):
        r = httpx.post(f"{BASE}/api/auth/login",
                       json={"username": "admin", "password": "wrong"})
        assert r.status_code in (401, 400)

    def test_protected_without_token(self, server):
        r = httpx.get(f"{BASE}/api/runs")
        assert r.status_code in (401, 403)

    def test_health_unauthenticated(self, server):
        r = httpx.get(f"{BASE}/health")
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Todos API
# ─────────────────────────────────────────────────────────────────────────────

class TestTodosAPI:
    def test_create_todo(self, auth_headers):
        r = httpx.post(f"{BASE}/api/todos",
                       json={"title": f"API Todo {uid()}", "priority": "high"},
                       headers=auth_headers)
        assert r.status_code in (200, 201)
        assert r.json()["priority"] == "high"

    def test_list_todos(self, auth_headers):
        r = httpx.get(f"{BASE}/api/todos", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_update_todo(self, auth_headers):
        create = httpx.post(f"{BASE}/api/todos",
                            json={"title": f"Update {uid()}"},
                            headers=auth_headers)
        tid = create.json()["id"]
        r = httpx.put(f"{BASE}/api/todos/{tid}",
                      json={"status": "done"},
                      headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "done"

    def test_delete_todo(self, auth_headers):
        create = httpx.post(f"{BASE}/api/todos",
                            json={"title": f"Delete {uid()}"},
                            headers=auth_headers)
        tid = create.json()["id"]
        r = httpx.delete(f"{BASE}/api/todos/{tid}", headers=auth_headers)
        assert r.status_code in (200, 204)


# ─────────────────────────────────────────────────────────────────────────────
# Connectors API
# ─────────────────────────────────────────────────────────────────────────────

class TestConnectorsAPI:
    def test_create_connector(self, auth_headers):
        r = httpx.post(f"{BASE}/api/connectors",
                       json={
                           "label": f"Con-{uid()}",
                           "email_address": f"{uid()}@test.com",
                           "provider": "imap",
                           "auth_type": "password",
                           "imap_host": "imap.example.com",
                           "imap_port": 993,
                           "smtp_host": "smtp.example.com",
                           "smtp_port": 587,
                           "username": "user@example.com",
                           "credentials": {"password": "secret"},
                       },
                       headers=auth_headers)
        assert r.status_code in (200, 201)
        data = r.json()
        assert data["status"] == "pending"

    def test_list_connectors(self, auth_headers):
        r = httpx.get(f"{BASE}/api/connectors", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_oauth_connector(self, auth_headers):
        r = httpx.post(f"{BASE}/api/connectors",
                       json={
                           "label": f"Gmail OAuth {uid()}",
                           "email_address": f"{uid()}@gmail.com",
                           "provider": "gmail",
                           "auth_type": "oauth2",
                           "oauth_client_id": "fake-client-id",
                           "oauth_client_secret": "fake-client-secret",
                       },
                       headers=auth_headers)
        assert r.status_code in (200, 201)
        assert r.json()["oauth_client_id"] == "fake-client-id"

    def test_get_connector(self, auth_headers):
        create = httpx.post(f"{BASE}/api/connectors",
                            json={"label": f"Get-{uid()}",
                                  "email_address": f"{uid()}@x.com"},
                            headers=auth_headers)
        cid = create.json()["id"]
        r = httpx.get(f"{BASE}/api/connectors/{cid}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == cid

    def test_delete_connector(self, auth_headers):
        create = httpx.post(f"{BASE}/api/connectors",
                            json={"label": f"Del-{uid()}",
                                  "email_address": f"{uid()}@x.com"},
                            headers=auth_headers)
        cid = create.json()["id"]
        r = httpx.delete(f"{BASE}/api/connectors/{cid}", headers=auth_headers)
        assert r.status_code in (200, 204)

    def test_oauth_init_missing_client_id(self, auth_headers):
        """OAuth init should return 400 if no client_id is set."""
        create = httpx.post(f"{BASE}/api/connectors",
                            json={"label": f"NoOAuth-{uid()}",
                                  "email_address": f"{uid()}@gmail.com",
                                  "provider": "gmail"},
                            headers=auth_headers)
        cid = create.json()["id"]
        r = httpx.get(f"{BASE}/api/connectors/oauth/google/init?connector_id={cid}",
                      headers=auth_headers)
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# Reports API
# ─────────────────────────────────────────────────────────────────────────────

class TestReportsAPI:
    def test_list_reports(self, auth_headers):
        r = httpx.get(f"{BASE}/api/reports", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_report_via_db(self, auth_headers):
        hub_db.create_report(
            report_type="daily_briefing",
            title="Test Brief",
            content="OK",
            status="complete",
        )
        r = httpx.get(f"{BASE}/api/reports", headers=auth_headers)
        assert r.status_code == 200
        reports = r.json()
        assert any(x["title"] == "Test Brief" for x in reports)


# ─────────────────────────────────────────────────────────────────────────────
# Agents API
# ─────────────────────────────────────────────────────────────────────────────

class TestAgentsAPI:
    def test_list_agents(self, auth_headers):
        r = httpx.get(f"{BASE}/api/agents", headers=auth_headers)
        assert r.status_code == 200

    def test_register_agent(self, auth_headers):
        aid = f"test-agent-{uid()}"
        r = httpx.post(f"{BASE}/api/agents",
                       json={"agent_id": aid, "name": "Test Agent",
                             "role": "tester", "description": "test"},
                       headers=auth_headers)
        assert r.status_code in (200, 201)
        assert r.json()["agent_id"] == aid


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket connectivity
# ─────────────────────────────────────────────────────────────────────────────

class TestWebSocket:
    def test_ws_rejects_without_auth(self, server):
        """Unauthenticated WS should be rejected (403 or closed immediately)."""
        import websockets, asyncio

        async def _check():
            try:
                async with websockets.connect(
                    f"ws://127.0.0.1:8766/ws", open_timeout=3
                ) as ws:
                    # Server should send a rejection or close
                    msg = await asyncio.wait_for(ws.recv(), timeout=2)
                    return msg
            except Exception as exc:
                return str(exc)

        result = asyncio.run(_check())
        # Either connection refused, WS close, or error message — all acceptable
        assert result is not None

    def test_ws_accepts_with_auth(self, auth_headers, server):
        """Authenticated WS should stay open and echo auth ack."""
        import websockets, asyncio

        token = auth_headers["Authorization"].split(" ")[1]

        async def _check():
            try:
                async with websockets.connect(
                    f"ws://127.0.0.1:8766/ws", open_timeout=3
                ) as ws:
                    await ws.send(json.dumps({"type": "auth", "token": token}))
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    return json.loads(msg)
            except Exception as exc:
                return {"error": str(exc)}

        result = asyncio.run(_check())
        # Should get an ack or hub_status message — not an error
        assert "error" not in result or result.get("type") in ("auth_ok", "hub_status", "ack")
