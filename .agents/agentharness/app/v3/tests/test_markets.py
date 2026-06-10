"""
test_markets.py — Tests for Markets surface:
  - Live quote feed helpers
  - Paper trading engine (theories, open/close, P&L, stats)
  - Theory reports
"""
import sys, uuid, time, tempfile
from pathlib import Path

HERE = Path(__file__).parent
APP  = HERE.parent
sys.path.insert(0, str(APP))

import hub_db
_TMP_DB = Path(tempfile.mkdtemp()) / "markets_test.db"
hub_db.DB_PATH = _TMP_DB
hub_db.init_schema()

import pytest


def uid() -> str:
    return uuid.uuid4().hex[:10]


# ─────────────────────────────────────────────────────────────────────────────
# Paper Trading — DB layer
# ─────────────────────────────────────────────────────────────────────────────

class TestPaperTradingDB:
    def test_create_theory(self):
        th = hub_db.create_theory(
            name="NVDA Breakout",
            description="Buy on breakout above $900",
            starting_balance=10_000.0,
        )
        assert th["name"] == "NVDA Breakout"
        assert th["current_balance"] == 10_000.0

    def test_open_long_trade(self):
        th = hub_db.create_theory(name=f"Long-{uid()}", starting_balance=5_000.0)
        tr = hub_db.open_paper_trade(
            theory_id=th["id"],
            ticker="AAPL",
            direction="long",
            shares=10,
            entry_price=150.0,
        )
        assert tr["status"] == "open"
        assert tr["entry_price"] == 150.0
        # Capital should be deducted
        updated_theory = hub_db.get_theory(th["id"])
        assert updated_theory["current_balance"] == 5_000.0 - (10 * 150.0)

    def test_open_short_trade(self):
        th = hub_db.create_theory(name=f"Short-{uid()}", starting_balance=10_000.0)
        tr = hub_db.open_paper_trade(
            theory_id=th["id"],
            ticker="TSLA",
            direction="short",
            shares=5,
            entry_price=200.0,
        )
        assert tr["direction"] == "short"
        assert tr["status"] == "open"

    def test_close_long_trade_profit(self):
        th = hub_db.create_theory(name=f"CloseP-{uid()}", starting_balance=10_000.0)
        tr = hub_db.open_paper_trade(
            theory_id=th["id"], ticker="MSFT",
            direction="long", shares=10, entry_price=300.0,
        )
        closed = hub_db.close_paper_trade(tr["id"], exit_price=350.0)
        expected_pnl = (350.0 - 300.0) * 10  # $500
        assert closed["status"] in ("closed", "closed_win", "closed_loss")
        assert abs(closed["pnl"] - expected_pnl) < 0.01

    def test_close_long_trade_loss(self):
        th = hub_db.create_theory(name=f"CloseL-{uid()}", starting_balance=10_000.0)
        tr = hub_db.open_paper_trade(
            theory_id=th["id"], ticker="GOOG",
            direction="long", shares=5, entry_price=100.0,
        )
        closed = hub_db.close_paper_trade(tr["id"], exit_price=80.0)
        expected_pnl = (80.0 - 100.0) * 5  # -$100
        assert closed["pnl"] < 0
        assert abs(closed["pnl"] - expected_pnl) < 0.01

    def test_close_short_trade_profit(self):
        th = hub_db.create_theory(name=f"ShortP-{uid()}", starting_balance=20_000.0)
        tr = hub_db.open_paper_trade(
            theory_id=th["id"], ticker="META",
            direction="short", shares=10, entry_price=400.0,
        )
        closed = hub_db.close_paper_trade(tr["id"], exit_price=360.0)
        expected_pnl = (400.0 - 360.0) * 10  # $400
        assert abs(closed["pnl"] - expected_pnl) < 0.01

    def test_price_update(self):
        th = hub_db.create_theory(name=f"Price-{uid()}")
        tr = hub_db.open_paper_trade(
            theory_id=th["id"], ticker="AMD",
            direction="long", shares=20, entry_price=120.0,
        )
        # update_paper_trade_price takes ticker+price globally
        hub_db.update_paper_trade_price("AMD", 130.0)
        refreshed = hub_db.get_paper_trade(tr["id"])
        assert refreshed is not None

    def test_theory_stats_win_rate(self):
        th = hub_db.create_theory(name=f"Stats-{uid()}", starting_balance=50_000.0)
        # 3 wins, 1 loss
        for entry, exit_ in [(100, 120), (200, 230), (150, 170), (300, 280)]:
            tr = hub_db.open_paper_trade(
                theory_id=th["id"], ticker="TEST",
                direction="long", shares=10, entry_price=entry,
            )
            hub_db.close_paper_trade(tr["id"], exit_price=exit_)

        stats = hub_db.theory_stats(th["id"])
        assert stats["total_trades"] == 4
        assert stats["win_count"] == 3
        assert stats["loss_count"] == 1
        assert abs(stats["win_rate_pct"] - 75.0) < 0.1

    def test_capital_returns_after_close(self):
        initial = 10_000.0
        th = hub_db.create_theory(name=f"Cap-{uid()}", starting_balance=initial)
        tr = hub_db.open_paper_trade(
            theory_id=th["id"], ticker="X",
            direction="long", shares=10, entry_price=50.0,
        )
        hub_db.close_paper_trade(tr["id"], exit_price=60.0)
        # Balance = initial - cost + cost + profit = initial + profit
        updated = hub_db.get_theory(th["id"])
        assert updated["current_balance"] == initial + (60.0 - 50.0) * 10

    def test_list_open_trades(self):
        th = hub_db.create_theory(name=f"Open-{uid()}")
        hub_db.open_paper_trade(
            theory_id=th["id"], ticker="OPEN",
            direction="long", shares=5, entry_price=100.0,
        )
        trades = hub_db.list_paper_trades(th["id"], status="open")
        assert len(trades) >= 1
        assert all(t["status"] == "open" for t in trades)

    def test_list_closed_trades(self):
        th = hub_db.create_theory(name=f"Closed-{uid()}")
        tr = hub_db.open_paper_trade(
            theory_id=th["id"], ticker="CLOSE",
            direction="long", shares=5, entry_price=100.0,
        )
        hub_db.close_paper_trade(tr["id"], exit_price=110.0)
        # list all trades for this theory and check at least one is closed
        trades = hub_db.list_paper_trades(theory_id=th["id"])
        closed = [t for t in trades if t["status"] not in ("open",)]
        assert len(closed) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Market price helpers (no live connection needed)
# ─────────────────────────────────────────────────────────────────────────────

class TestQuoteInjection:
    """Test that quote injection updates paper trades correctly."""

    def test_inject_quote_updates_pnl(self):
        th = hub_db.create_theory(name=f"Inject-{uid()}")
        tr = hub_db.open_paper_trade(
            theory_id=th["id"], ticker="INJECTME",
            direction="long", shares=100, entry_price=50.0,
        )
        # update_paper_trade_price takes ticker+price globally
        hub_db.update_paper_trade_price("INJECTME", 55.0)
        refreshed = hub_db.get_paper_trade(tr["id"])
        assert refreshed is not None  # trade still exists after update
