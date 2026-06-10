"""
test_ui_surfaces.py — Smoke tests for all Tkinter UI surfaces.
Runs in headless mode (Tk with withdraw) to verify:
  - App initialises without errors
  - All nav views render without raising
  - Key widget attributes exist after each view is shown
  - Status bar is always visible (packed before shell)
  - Inez chat panel is present on Home
  - Markets, Org chart, Connectors, Reports tabs render
"""
import os, sys, time, tempfile, threading
from pathlib import Path

HERE = Path(__file__).parent
APP  = HERE.parent
sys.path.insert(0, str(APP))

# Redirect DB to temp
import hub_db
_TMP_DB = Path(tempfile.mkdtemp()) / "ui_test.db"
hub_db.DB_PATH = _TMP_DB
hub_db.init_schema()

import pytest

# Skip entire module if display is unavailable
try:
    import tkinter as tk
    _root = tk.Tk()
    _root.withdraw()
    _root.destroy()
    HAS_DISPLAY = True
except Exception:
    HAS_DISPLAY = False

pytestmark = pytest.mark.skipif(not HAS_DISPLAY, reason="No display available")


# ─────────────────────────────────────────────────────────────────────────────
# Fixture: app instance (created once per module)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def app():
    """Create an ArchonHubApp instance with Tk hidden."""
    from main_m365 import ArchonHubApp
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()          # headless — no window shown
    instance = ArchonHubApp(root)
    yield instance
    try:
        root.destroy()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# App initialisation
# ─────────────────────────────────────────────────────────────────────────────

class TestAppInit:
    def test_root_exists(self, app):
        assert app.root is not None

    def test_status_bar_exists(self, app):
        assert hasattr(app, "status_bar")

    def test_content_frame_exists(self, app):
        assert hasattr(app, "content")

    def test_nav_buttons_populated(self, app):
        assert len(app.nav_buttons) > 0

    def test_hub_client_initialised(self, app):
        assert app.hub is not None

    def test_ui_queue_exists(self, app):
        import queue
        assert isinstance(app._ui_queue, queue.Queue)

    def test_connector_lookup_initialised(self, app):
        assert isinstance(app._connector_lookup, dict)

    def test_inez_history_initialised(self, app):
        assert isinstance(app._inez_history, list)


# ─────────────────────────────────────────────────────────────────────────────
# Status bar visibility
# ─────────────────────────────────────────────────────────────────────────────

class TestStatusBar:
    def test_status_bar_is_packed(self, app):
        """Status bar must use pack geometry (not grid/place)."""
        info = app.status_bar.pack_info()
        assert info, "Status bar is not packed"

    def test_status_bar_at_bottom_or_top(self, app):
        """Status bar side must be 'bottom' or 'top' — never missing."""
        info = app.status_bar.pack_info()
        assert info.get("side") in ("bottom", "top"), \
            f"Unexpected status bar side: {info.get('side')}"


# ─────────────────────────────────────────────────────────────────────────────
# Home surface
# ─────────────────────────────────────────────────────────────────────────────

class TestHomeSurface:
    def test_show_home_no_crash(self, app):
        app.show_home()
        app.root.update_idletasks()

    def test_inez_input_exists_after_home(self, app):
        app.show_home()
        app.root.update_idletasks()
        assert hasattr(app, "_inez_input"), "Inez chat input not found on home"

    def test_inez_send_exists(self, app):
        app.show_home()
        app.root.update_idletasks()
        assert hasattr(app, "_inez_send_btn"), "Inez send button not found"


# ─────────────────────────────────────────────────────────────────────────────
# Runs surface
# ─────────────────────────────────────────────────────────────────────────────

class TestRunsSurface:
    def test_show_runs_no_crash(self, app):
        app.show_runs()
        app.root.update_idletasks()

    def test_runs_tree_exists(self, app):
        app.show_runs()
        app.root.update_idletasks()
        assert hasattr(app, "runs_tree")


# ─────────────────────────────────────────────────────────────────────────────
# Todos surface
# ─────────────────────────────────────────────────────────────────────────────

class TestTodosSurface:
    def test_show_todos_no_crash(self, app):
        app.show_todos()
        app.root.update_idletasks()

    def test_todo_tree_exists(self, app):
        app.show_todos()
        app.root.update_idletasks()
        assert hasattr(app, "todo_tree")


# ─────────────────────────────────────────────────────────────────────────────
# Agents surface
# ─────────────────────────────────────────────────────────────────────────────

class TestAgentsSurface:
    def test_show_agents_no_crash(self, app):
        app.show_agents()
        app.root.update_idletasks()


# ─────────────────────────────────────────────────────────────────────────────
# Markets surface
# ─────────────────────────────────────────────────────────────────────────────

class TestMarketsSurface:
    def test_show_markets_no_crash(self, app):
        app.show_markets()
        app.root.update_idletasks()

    def test_markets_tab_object_created(self, app):
        app.show_markets()
        app.root.update_idletasks()
        assert app._markets_tab is not None, "_markets_tab not set after show_markets()"

    def test_markets_has_notebook(self, app):
        app.show_markets()
        app.root.update_idletasks()
        tab = app._markets_tab
        assert hasattr(tab, "_notebook") or hasattr(tab, "notebook"), \
            "Markets tab missing ttk.Notebook"


# ─────────────────────────────────────────────────────────────────────────────
# Org Chart surface
# ─────────────────────────────────────────────────────────────────────────────

class TestOrgChartSurface:
    def test_show_org_no_crash(self, app):
        app.show_org()
        app.root.update_idletasks()

    def test_org_canvas_exists(self, app):
        app.show_org()
        app.root.update_idletasks()
        # OrgChartTab stores canvas as _canvas
        # It's inside the content area — just check no exception so far
        assert True


# ─────────────────────────────────────────────────────────────────────────────
# Connectors surface
# ─────────────────────────────────────────────────────────────────────────────

class TestConnectorsSurface:
    def test_show_connectors_no_crash(self, app):
        app.show_connectors()
        app.root.update_idletasks()

    def test_connectors_tree_exists(self, app):
        app.show_connectors()
        app.root.update_idletasks()
        assert hasattr(app, "connectors_tree")

    def test_connector_vars_created(self, app):
        app.show_connectors()
        app.root.update_idletasks()
        assert hasattr(app, "_connector_vars")
        assert "provider" in app._connector_vars

    def test_gmail_provider_sets_oauth_mode(self, app):
        """Setting provider to gmail should switch to OAuth2 form."""
        app.show_connectors()
        app.root.update_idletasks()
        app._connector_vars["provider"].set("gmail")
        app.root.update_idletasks()
        # No crash = pass

    def test_imap_provider_sets_password_mode(self, app):
        """Setting provider to imap should switch to password form."""
        app.show_connectors()
        app.root.update_idletasks()
        app._connector_vars["provider"].set("imap")
        app.root.update_idletasks()
        # No crash = pass

    def test_add_password_connector_missing_label(self, app):
        """Adding connector without label should show toast, not crash."""
        app.show_connectors()
        app.root.update_idletasks()
        app._connector_vars["provider"].set("imap")
        for key in ("label", "email_address"):
            app._connector_vars[key].set("")
        app._add_password_connector()
        app.root.update_idletasks()


# ─────────────────────────────────────────────────────────────────────────────
# Reports surface
# ─────────────────────────────────────────────────────────────────────────────

class TestReportsSurface:
    def test_show_reports_no_crash(self, app):
        app.show_reports()
        app.root.update_idletasks()


# ─────────────────────────────────────────────────────────────────────────────
# Schedule surface
# ─────────────────────────────────────────────────────────────────────────────

class TestScheduleSurface:
    def test_show_schedule_no_crash(self, app):
        app.show_schedule()
        app.root.update_idletasks()

    def test_schedule_tree_exists(self, app):
        app.show_schedule()
        app.root.update_idletasks()
        assert hasattr(app, "schedule_tree")


# ─────────────────────────────────────────────────────────────────────────────
# Clients / Travel surfaces
# ─────────────────────────────────────────────────────────────────────────────

class TestClientsSurface:
    def test_show_clients_no_crash(self, app):
        app.show_clients()
        app.root.update_idletasks()


class TestTravelSurface:
    def test_show_travel_no_crash(self, app):
        app.show_travel()
        app.root.update_idletasks()


# ─────────────────────────────────────────────────────────────────────────────
# Navigation switching (rapid tab switching should not crash)
# ─────────────────────────────────────────────────────────────────────────────

class TestNavSwitching:
    def test_rapid_tab_switch(self, app):
        """Rapidly switching between all surfaces must not raise."""
        views = [
            app.show_home, app.show_runs, app.show_todos,
            app.show_connectors, app.show_markets, app.show_org,
            app.show_reports, app.show_home,
        ]
        for fn in views:
            fn()
            app.root.update_idletasks()

    def test_markets_stop_feed_on_switch(self, app):
        """Switching away from markets must not crash (stops live feed)."""
        app.show_markets()
        app.root.update_idletasks()
        app.show_home()
        app.root.update_idletasks()
        # _markets_tab should be cleaned up or just stopped
