from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.alpaca_client import (
    ALPACA_OK,
    cancel_all_orders,
    cancel_order,
    get_account,
    get_asset,
    get_bars,
    get_calendar,
    get_clock,
    get_latest_quote,
    get_orders,
    get_portfolio_history,
    get_position,
    get_positions,
    is_configured,
    is_paper,
    place_order,
)
from core.auth import get_current_user
from core.database import _create_record, _json_dumps, _list_records, _now_iso, _update_record

router = APIRouter(prefix="/alpaca", tags=["alpaca"])


class PlaceOrderRequest(BaseModel):
    symbol: str
    qty: float
    side: str
    order_type: str = "market"
    time_in_force: str = "day"
    limit_price: float | None = None
    stop_price: float | None = None
    extended_hours: bool = False
    client_order_id: str | None = None
    order_class: str = "simple"
    agent_reason: str = ""


class SyncPositionsRequest(BaseModel):
    overwrite: bool = True


ALLOWED_SIDES = {"buy", "sell"}
ALLOWED_ORDER_TYPES = {"market", "limit", "stop", "stop_limit"}
ALLOWED_TIFS = {"day", "gtc", "ioc", "fok"}


def _raise_ready_error(exc: Exception) -> None:
    message = str(exc)
    if "not installed" in message:
        raise HTTPException(status_code=503, detail=message)
    if "must be set" in message:
        raise HTTPException(status_code=422, detail=message)
    raise HTTPException(status_code=400, detail=message)


def _ensure_ready() -> None:
    if not ALPACA_OK:
        raise HTTPException(status_code=503, detail="alpaca-py is not installed. Run: pip install alpaca-py")
    if not is_configured():
        raise HTTPException(status_code=422, detail="ALPACA_API_KEY and ALPACA_API_SECRET must be set in .env")


@router.get("/status")
async def alpaca_status():
    return {"configured": is_configured(), "paper": is_paper(), "alpaca_ok": ALPACA_OK}


@router.get("/account")
async def alpaca_account(_: dict = Depends(get_current_user)):
    _ensure_ready()
    try:
        return get_account()
    except Exception as exc:
        _raise_ready_error(exc)


@router.get("/positions")
async def alpaca_positions(_: dict = Depends(get_current_user)):
    _ensure_ready()
    try:
        return get_positions()
    except Exception as exc:
        _raise_ready_error(exc)


@router.get("/positions/{symbol}")
async def alpaca_position(symbol: str, _: dict = Depends(get_current_user)):
    _ensure_ready()
    try:
        return get_position(symbol)
    except Exception as exc:
        _raise_ready_error(exc)


@router.get("/orders")
async def alpaca_orders(
    status: str = Query("open"),
    limit: int = Query(50, ge=1, le=500),
    symbols: str | None = Query(None),
    _: dict = Depends(get_current_user),
):
    _ensure_ready()
    try:
        symbol_list = [item.strip().upper() for item in (symbols or "").split(",") if item.strip()] or None
        return get_orders(status=status, limit=limit, symbols=symbol_list)
    except Exception as exc:
        _raise_ready_error(exc)


@router.post("/orders")
async def alpaca_place_order(body: PlaceOrderRequest, current_user: dict = Depends(get_current_user)):
    _ensure_ready()
    side = body.side.lower().strip()
    order_type = body.order_type.lower().strip()
    tif = body.time_in_force.lower().strip()
    if side not in ALLOWED_SIDES:
        raise HTTPException(status_code=400, detail="side must be one of: buy, sell")
    if order_type not in ALLOWED_ORDER_TYPES:
        raise HTTPException(status_code=400, detail="order_type must be one of: market, limit, stop, stop_limit")
    if tif not in ALLOWED_TIFS:
        raise HTTPException(status_code=400, detail="time_in_force must be one of: day, gtc, ioc, fok")
    try:
        order = place_order(
            symbol=body.symbol.upper().strip(),
            qty=body.qty,
            side=side,
            order_type=order_type,
            time_in_force=tif,
            limit_price=body.limit_price,
            stop_price=body.stop_price,
            extended_hours=body.extended_hours,
            client_order_id=body.client_order_id,
            order_class=body.order_class,
        )
        now = _now_iso()
        order_id = str(order.get("id") or order.get("order_id") or body.client_order_id or uuid.uuid4())
        _create_record(
            "alpaca_orders",
            {
                "id": order_id,
                "symbol": body.symbol.upper().strip(),
                "side": side,
                "order_type": order_type,
                "qty": body.qty,
                "limit_price": body.limit_price,
                "stop_price": body.stop_price,
                "time_in_force": tif,
                "status": str(order.get("status") or "submitted"),
                "agent_reason": body.agent_reason or "",
                "submitted_by": current_user.get("username", ""),
                "alpaca_response": _json_dumps(order),
                "created_at": str(order.get("created_at") or now),
                "updated_at": str(order.get("updated_at") or now),
            },
        )
        return order
    except Exception as exc:
        _raise_ready_error(exc)


@router.delete("/orders/{order_id}")
async def alpaca_cancel_order(order_id: str, _: dict = Depends(get_current_user)):
    _ensure_ready()
    try:
        result = cancel_order(order_id)
        _update_record("alpaca_orders", order_id, {"status": "cancelled", "updated_at": _now_iso(), "alpaca_response": _json_dumps(result)})
        return result
    except Exception as exc:
        _raise_ready_error(exc)


@router.delete("/orders")
async def alpaca_cancel_all_orders(_: dict = Depends(get_current_user)):
    _ensure_ready()
    try:
        results = cancel_all_orders()
        now = _now_iso()
        for item in results:
            order_id = str(item.get("id") or item.get("order_id") or "")
            if order_id:
                _update_record("alpaca_orders", order_id, {"status": "cancelled", "updated_at": now, "alpaca_response": _json_dumps(item)})
        return results
    except Exception as exc:
        _raise_ready_error(exc)


@router.get("/portfolio/history")
async def alpaca_portfolio_history(
    period: str = Query("1W"),
    timeframe: str = Query("1D"),
    _: dict = Depends(get_current_user),
):
    _ensure_ready()
    try:
        return get_portfolio_history(period=period, timeframe=timeframe)
    except Exception as exc:
        _raise_ready_error(exc)


@router.get("/assets/{symbol}")
async def alpaca_asset(symbol: str, _: dict = Depends(get_current_user)):
    _ensure_ready()
    try:
        return get_asset(symbol.upper().strip())
    except Exception as exc:
        _raise_ready_error(exc)


@router.get("/quotes/{symbol}")
async def alpaca_quote(symbol: str, _: dict = Depends(get_current_user)):
    _ensure_ready()
    try:
        return get_latest_quote(symbol.upper().strip())
    except Exception as exc:
        _raise_ready_error(exc)


@router.get("/bars/{symbol}")
async def alpaca_bars(
    symbol: str,
    timeframe: str = Query("1D"),
    limit: int = Query(30, ge=1, le=1000),
    start: str | None = Query(None),
    end: str | None = Query(None),
    _: dict = Depends(get_current_user),
):
    _ensure_ready()
    try:
        return get_bars(symbol.upper().strip(), timeframe=timeframe, limit=limit, start=start, end=end)
    except Exception as exc:
        _raise_ready_error(exc)


@router.get("/clock")
async def alpaca_clock(_: dict = Depends(get_current_user)):
    _ensure_ready()
    try:
        return get_clock()
    except Exception as exc:
        _raise_ready_error(exc)


@router.get("/calendar")
async def alpaca_calendar(
    start: str | None = Query(None),
    end: str | None = Query(None),
    _: dict = Depends(get_current_user),
):
    _ensure_ready()
    try:
        return get_calendar(start=start, end=end)
    except Exception as exc:
        _raise_ready_error(exc)


@router.post("/sync-positions")
async def alpaca_sync_positions(body: SyncPositionsRequest, _: dict = Depends(get_current_user)):
    _ensure_ready()
    try:
        alpaca_positions = get_positions()
        existing = _list_records("market_positions")
        by_symbol = {str(item.get("ticker") or "").upper(): item for item in existing if item.get("ticker")}
        now = _now_iso()
        synced: list[dict] = []
        for position in alpaca_positions:
            symbol = str(position.get("symbol") or "").upper()
            if not symbol:
                continue
            qty = float(position.get("qty") or 0)
            current_price = float(position.get("current_price") or 0)
            market_value = float(position.get("market_value") or 0)
            cost_basis = float(position.get("cost_basis") or 0)
            unrealized_pnl = float(position.get("unrealized_pl") or 0)
            side = str(position.get("side") or ("short" if qty < 0 else "long"))
            entry_price = float(position.get("avg_entry_price") or ((cost_basis / abs(qty)) if qty else 0))
            payload = {
                "ticker": symbol,
                "name": str(position.get("symbol") or symbol),
                "position_type": "equity",
                "action": "short" if side.lower() == "short" else "long",
                "shares": abs(qty),
                "entry_price": entry_price,
                "current_price": current_price,
                "pnl": unrealized_pnl,
                "qty": qty,
                "market_value": market_value,
                "cost_basis": cost_basis,
                "side": side,
                "unrealized_pnl": unrealized_pnl,
                "status": "open",
                "updated_at": now,
            }
            existing_row = by_symbol.get(symbol)
            if existing_row:
                if body.overwrite:
                    synced.append(_update_record("market_positions", existing_row["id"], payload) or existing_row)
                else:
                    synced.append(existing_row)
                continue
            payload.update({"id": str(uuid.uuid4()), "created_at": now, "notes": "Synced from Alpaca"})
            synced.append(_create_record("market_positions", payload))
        return {"synced": len(synced), "positions": synced}
    except Exception as exc:
        _raise_ready_error(exc)
