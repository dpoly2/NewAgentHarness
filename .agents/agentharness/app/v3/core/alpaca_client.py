"""alpaca_client.py — Thin wrapper around alpaca-py for ArchonHub markets team."""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

ALPACA_OK = False
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import (
        CancelOrderResponse,
        GetCalendarRequest,
        GetOrdersRequest,
        GetPortfolioHistoryRequest,
        LimitOrderRequest,
        MarketOrderRequest,
        StopLimitOrderRequest,
        StopOrderRequest,
    )
    from alpaca.trading.enums import OrderClass, OrderSide, QueryOrderStatus, TimeInForce
    try:
        from alpaca.data.historical import StockHistoricalDataClient
    except ImportError:
        from alpaca.data.historical.stock import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

    ALPACA_OK = True
except ImportError:
    pass

_trading_client: Any = None
_data_client: Any = None


def _api_key() -> str:
    return os.environ.get("ALPACA_API_KEY", "")


def _api_secret() -> str:
    return os.environ.get("ALPACA_API_SECRET", "")


def is_paper() -> bool:
    return os.environ.get("ALPACA_PAPER", "true").lower() != "false"


def is_configured() -> bool:
    return bool(_api_key() and _api_secret())


def get_trading_client() -> Any:
    global _trading_client
    if not ALPACA_OK:
        raise RuntimeError("alpaca-py is not installed. Run: pip install alpaca-py")
    if not is_configured():
        raise RuntimeError("ALPACA_API_KEY and ALPACA_API_SECRET must be set in .env")
    if _trading_client is None:
        _trading_client = TradingClient(
            api_key=_api_key(),
            secret_key=_api_secret(),
            paper=is_paper(),
        )
    return _trading_client


def get_data_client() -> Any:
    global _data_client
    if not ALPACA_OK:
        raise RuntimeError("alpaca-py is not installed. Run: pip install alpaca-py")
    if not is_configured():
        raise RuntimeError("ALPACA_API_KEY and ALPACA_API_SECRET must be set in .env")
    if _data_client is None:
        _data_client = StockHistoricalDataClient(
            api_key=_api_key(),
            secret_key=_api_secret(),
        )
    return _data_client


def _serialize(obj: Any) -> Any:
    """Recursively convert Alpaca SDK objects / enums / datetimes to JSON-safe types."""
    if obj is None:
        return None
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "value") and not isinstance(obj, dict):
        return obj.value
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_serialize(i) for i in obj]
    if hasattr(obj, "__dict__"):
        return {k: _serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return str(obj)


def reset_clients() -> None:
    """Force re-init of clients (e.g. after key rotation)."""
    global _trading_client, _data_client
    _trading_client = None
    _data_client = None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.fromisoformat(f"{value}T00:00:00")


def _parse_timeframe(value: str) -> Any:
    normalized = str(value or "1D").strip()
    presets = {
        "1MIN": TimeFrame.Minute,
        "1H": TimeFrame.Hour,
        "1D": TimeFrame.Day,
        "1W": TimeFrame.Week,
        "1M": TimeFrame.Month,
    }
    if normalized.upper() in presets:
        return presets[normalized.upper()]
    digits = ""
    letters = ""
    for char in normalized:
        if char.isdigit() and not letters:
            digits += char
        elif char.isalpha():
            letters += char
    amount = int(digits or "1")
    unit_map = {
        "MIN": TimeFrameUnit.Minute,
        "M": TimeFrameUnit.Minute,
        "H": TimeFrameUnit.Hour,
        "HR": TimeFrameUnit.Hour,
        "HOUR": TimeFrameUnit.Hour,
        "D": TimeFrameUnit.Day,
        "DAY": TimeFrameUnit.Day,
        "W": TimeFrameUnit.Week,
        "WK": TimeFrameUnit.Week,
        "WEEK": TimeFrameUnit.Week,
        "MO": TimeFrameUnit.Month,
        "MON": TimeFrameUnit.Month,
        "MONTH": TimeFrameUnit.Month,
    }
    unit = unit_map.get(letters.upper())
    if unit is None:
        raise ValueError(f"Unsupported timeframe: {value}")
    return TimeFrame(amount, unit)


def get_account() -> dict:
    client = get_trading_client()
    return _serialize(client.get_account())


def get_positions() -> list[dict]:
    client = get_trading_client()
    return _serialize(client.get_all_positions())


def get_position(symbol: str) -> dict:
    client = get_trading_client()
    return _serialize(client.get_open_position(symbol))


def get_orders(status: str = "open", limit: int = 50, symbols: list[str] | None = None) -> list[dict]:
    client = get_trading_client()
    request = GetOrdersRequest(
        status=QueryOrderStatus(status),
        limit=limit,
        symbols=symbols,
    )
    return _serialize(client.get_orders(filter=request))


def place_order(
    symbol: str,
    qty: float,
    side: str,
    order_type: str,
    time_in_force: str,
    limit_price: float | None = None,
    stop_price: float | None = None,
    extended_hours: bool = False,
    client_order_id: str | None = None,
    order_class: str = "simple",
) -> dict:
    client = get_trading_client()
    side_enum = OrderSide(side)
    tif_enum = TimeInForce(time_in_force)
    order_class_enum = OrderClass(order_class) if order_class else None
    common = {
        "symbol": symbol,
        "qty": qty,
        "side": side_enum,
        "time_in_force": tif_enum,
        "extended_hours": extended_hours,
        "client_order_id": client_order_id,
        "order_class": order_class_enum,
    }
    order_kind = str(order_type or "market").lower()
    if order_kind == "market":
        request = MarketOrderRequest(**common)
    elif order_kind == "limit":
        if limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        request = LimitOrderRequest(**common, limit_price=limit_price)
    elif order_kind == "stop":
        if stop_price is None:
            raise ValueError("stop_price is required for stop orders")
        request = StopOrderRequest(**common, stop_price=stop_price)
    elif order_kind == "stop_limit":
        if limit_price is None or stop_price is None:
            raise ValueError("limit_price and stop_price are required for stop_limit orders")
        request = StopLimitOrderRequest(**common, limit_price=limit_price, stop_price=stop_price)
    else:
        raise ValueError(f"Unsupported order type: {order_type}")
    return _serialize(client.submit_order(order_data=request))


def cancel_order(order_id: str) -> dict:
    client = get_trading_client()
    client.cancel_order_by_id(order_id)
    return {"id": order_id, "cancelled": True}


def cancel_all_orders() -> list[dict]:
    client = get_trading_client()
    result: list[CancelOrderResponse] = client.cancel_orders()
    return _serialize(result)


def get_portfolio_history(period: str = "1W", timeframe: str = "1D") -> dict:
    client = get_trading_client()
    request = GetPortfolioHistoryRequest(period=period, timeframe=timeframe)
    return _serialize(client.get_portfolio_history(request))


def get_asset(symbol: str) -> dict:
    client = get_trading_client()
    return _serialize(client.get_asset(symbol))


def get_clock() -> dict:
    client = get_trading_client()
    return _serialize(client.get_clock())


def get_calendar(start: str | None = None, end: str | None = None) -> list[dict]:
    client = get_trading_client()
    request = GetCalendarRequest(start=_parse_date(start), end=_parse_date(end))
    return _serialize(client.get_calendar(request))


def get_latest_quote(symbol: str) -> dict:
    client = get_data_client()
    request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
    result = _serialize(client.get_stock_latest_quote(request))
    if isinstance(result, dict):
        by_symbol = result.get(symbol) or result.get(symbol.upper())
        if isinstance(by_symbol, dict):
            return by_symbol
    return result


def get_bars(
    symbol: str,
    timeframe: str = "1D",
    limit: int = 30,
    start: str | None = None,
    end: str | None = None,
) -> list[dict]:
    client = get_data_client()
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=_parse_timeframe(timeframe),
        limit=limit,
        start=_parse_datetime(start),
        end=_parse_datetime(end),
    )
    result = _serialize(client.get_stock_bars(request))
    if isinstance(result, dict):
        bars = result.get(symbol) or result.get(symbol.upper())
        if isinstance(bars, list):
            return bars
    return result if isinstance(result, list) else [result]
