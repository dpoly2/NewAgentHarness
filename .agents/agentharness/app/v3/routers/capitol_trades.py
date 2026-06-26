from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.auth import get_current_user
from core.database import _db_connection, _now_iso, _json_dumps, _json_loads
from core import alpaca_client
from core import capitol_trades_client

router = APIRouter(prefix="/capitol-trades", tags=["capitol-trades"])

ALLOWED_CHAMBERS = {"house", "senate", "both"}
ALLOWED_REVIEW_ACTIONS = {"approve", "reject"}
ALLOWED_ORDER_TYPES = {"market", "limit"}
ALLOWED_TIFS = {"day", "gtc", "ioc", "fok"}


class AddPoliticianRequest(BaseModel):
    name: str
    chamber: str = "both"
    tracking_reason: str
    party: str = ""
    state: str = ""


class UpdatePoliticianRequest(BaseModel):
    tracking_reason: Optional[str] = None
    performance_note: Optional[str] = None
    is_active: Optional[bool] = None


class ReviewSignalRequest(BaseModel):
    action: str
    cro_notes: str = ""
    qty: Optional[float] = None
    time_in_force: str = "day"
    order_type: str = "market"
    limit_price: Optional[float] = None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        try:
            return datetime.fromisoformat(text.replace('Z', '+00:00')).date()
        except Exception:
            return None


def _normalize_chamber(value: str) -> str:
    chamber = str(value or 'both').strip().lower()
    if chamber not in ALLOWED_CHAMBERS:
        raise HTTPException(status_code=400, detail='chamber must be one of: house, senate, both')
    return chamber


def _serialize_politician_row(row) -> dict[str, Any]:
    item = dict(row)
    item['is_active'] = bool(item.get('is_active'))
    total = int(item.get('total_signals') or 0)
    approved = int(item.get('approved_signals') or 0)
    profitable = int(item.get('profitable_signals') or 0)
    item['signal_counts'] = {
        'total': total,
        'approved': approved,
        'profitable': profitable,
    }
    item['win_rate'] = (profitable / approved) if approved else 0.0
    return item


def _serialize_trade_row(row) -> dict[str, Any]:
    item = dict(row)
    item['raw'] = _json_loads(item.pop('raw_json', None), {})
    return item


def _serialize_signal_row(row) -> dict[str, Any]:
    item = dict(row)
    item['estimated_qty'] = float(item.get('estimated_qty') or 0)
    return item


def _politician_or_404(conn, politician_id: str) -> dict[str, Any]:
    row = conn.execute('SELECT * FROM tracked_politicians WHERE id = ?', (politician_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Tracked politician not found')
    return _serialize_politician_row(row)


def _signal_or_404(conn, signal_id: str) -> dict[str, Any]:
    row = conn.execute(
        '''
        SELECT s.*, t.trade_type, t.asset_name, t.amount_range, t.amount_midpoint, t.transaction_date, t.disclosure_date
        FROM copy_trade_signals s
        LEFT JOIN politician_trades t ON t.id = s.politician_trade_id
        WHERE s.id = ?
        ''',
        (signal_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Copy trade signal not found')
    return _serialize_signal_row(row)


def _signal_strength(amount_midpoint: float) -> str:
    if amount_midpoint > 50000:
        return 'strong'
    if amount_midpoint > 10000:
        return 'moderate'
    return 'weak'


def _signal_side(trade_type: str) -> str:
    normalized = str(trade_type or '').lower()
    if normalized == 'sale':
        return 'sell'
    return 'buy'


def _within_last_days(value: str | None, days: int) -> bool:
    parsed = _parse_date(value)
    if not parsed:
        return False
    return parsed >= (date.today() - timedelta(days=days))


def _make_copy_reason(politician_name: str, party: str, chamber: str, tracking_reason: str, trade: dict[str, Any]) -> str:
    return (
        f"Copying {politician_name} ({party}, {chamber.title()}) — {tracking_reason}. "
        f"Trade: {str(trade.get('trade_type') or '').upper()} {trade.get('ticker') or ''} ({trade.get('asset_name') or ''}), "
        f"disclosed {trade.get('disclosure_date') or 'unknown'}, transaction {trade.get('transaction_date') or 'unknown'}. "
        f"Amount range: {trade.get('amount_range') or 'unknown'} (midpoint ~${float(trade.get('amount_midpoint') or 0):,.0f})."
    )


def _quote_price(quote: dict[str, Any] | None) -> float | None:
    if not isinstance(quote, dict):
        return None
    bid = quote.get('bid_price')
    ask = quote.get('ask_price')
    try:
        if bid is not None and ask is not None:
            bid_f = float(bid)
            ask_f = float(ask)
            if bid_f > 0 and ask_f > 0:
                return (bid_f + ask_f) / 2
        if ask is not None and float(ask) > 0:
            return float(ask)
        if bid is not None and float(bid) > 0:
            return float(bid)
    except Exception:
        return None
    return None


def _coerce_float(value: Any) -> float | None:
    if value in (None, ''):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _ensure_alpaca_ready() -> None:
    if not alpaca_client.ALPACA_OK:
        raise HTTPException(status_code=503, detail='alpaca-py is not installed. Run: pip install alpaca-py')
    if not alpaca_client.is_configured():
        raise HTTPException(status_code=422, detail='ALPACA_API_KEY and ALPACA_API_SECRET must be set in .env')


def _sync_politician_stats(conn, politician_id: str) -> None:
    total = int(conn.execute('SELECT COUNT(*) FROM copy_trade_signals WHERE politician_id = ?', (politician_id,)).fetchone()[0])
    approved = int(conn.execute("SELECT COUNT(*) FROM copy_trade_signals WHERE politician_id = ? AND status = 'executed'", (politician_id,)).fetchone()[0])
    conn.execute(
        '''
        UPDATE tracked_politicians
        SET total_signals = ?, approved_signals = ?, updated_at = ?
        WHERE id = ?
        ''',
        (total, approved, _now_iso(), politician_id),
    )


def _recalculate_performance(conn, politician_id: str | None = None) -> None:
    if not (alpaca_client.ALPACA_OK and alpaca_client.is_configured()):
        return
    where = '' if politician_id is None else 'WHERE tp.id = ?'
    rows = conn.execute(
        f'''
        SELECT tp.id AS politician_id, s.id AS signal_id, s.signal_side, s.ticker, s.alpaca_order_id, ao.alpaca_response
        FROM tracked_politicians tp
        LEFT JOIN copy_trade_signals s ON s.politician_id = tp.id AND s.status = 'executed'
        LEFT JOIN alpaca_orders ao ON ao.id = s.alpaca_order_id
        {where}
        ''',
        (() if politician_id is None else (politician_id,)),
    ).fetchall()
    metrics: dict[str, dict[str, float]] = {}
    quote_cache: dict[str, float | None] = {}
    for row in rows:
        pid = str(row['politician_id'])
        metrics.setdefault(pid, {'profitable': 0.0, 'total_return_pct': 0.0})
        if not row['signal_id'] or not row['alpaca_response']:
            continue
        response = _json_loads(row['alpaca_response'], {}) or {}
        entry_price = _coerce_float(response.get('filled_avg_price')) or _coerce_float(response.get('limit_price'))
        ticker = str(row['ticker'] or '').upper()
        if not entry_price or entry_price <= 0 or not ticker:
            continue
        if ticker not in quote_cache:
            try:
                quote_cache[ticker] = _quote_price(alpaca_client.get_latest_quote(ticker))
            except Exception:
                quote_cache[ticker] = None
        current_price = quote_cache.get(ticker)
        if not current_price or current_price <= 0:
            continue
        if str(row['signal_side'] or '').lower() == 'sell':
            return_pct = ((entry_price - current_price) / entry_price) * 100
        else:
            return_pct = ((current_price - entry_price) / entry_price) * 100
        metrics[pid]['total_return_pct'] += return_pct
        if return_pct > 0:
            metrics[pid]['profitable'] += 1
    if politician_id is not None:
        metrics.setdefault(politician_id, {'profitable': 0.0, 'total_return_pct': 0.0})
    for pid, values in metrics.items():
        conn.execute(
            '''
            UPDATE tracked_politicians
            SET profitable_signals = ?, total_return_pct = ?, updated_at = ?
            WHERE id = ?
            ''',
            (int(values['profitable']), float(values['total_return_pct']), _now_iso(), pid),
        )


def _ingest_trade(conn, politician: dict[str, Any], trade: dict[str, Any]) -> tuple[bool, bool]:
    exists = conn.execute('SELECT 1 FROM politician_trades WHERE id = ?', (trade['id'],)).fetchone()
    if exists:
        return (False, False)
    conn.execute(
        '''
        INSERT INTO politician_trades (
            id, politician_id, politician_name, chamber, ticker, asset_name, trade_type,
            amount_range, amount_min, amount_max, amount_midpoint, transaction_date,
            disclosure_date, raw_json, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            trade['id'],
            politician['id'],
            trade.get('politician_name') or politician['name'],
            trade.get('chamber') or politician['chamber'],
            trade.get('ticker') or '',
            trade.get('asset_name') or '',
            trade.get('trade_type') or 'other',
            trade.get('amount_range') or '',
            float(trade.get('amount_min') or 0),
            float(trade.get('amount_max') or 0),
            float(trade.get('amount_midpoint') or 0),
            trade.get('transaction_date') or '',
            trade.get('disclosure_date') or '',
            _json_dumps(trade.get('raw') or {}),
            _now_iso(),
        ),
    )
    signal_created = False
    if politician.get('is_active') and trade.get('ticker') and _within_last_days(trade.get('transaction_date'), 60):
        signal_id = f"{trade['id']}-signal"
        existed_before = conn.execute('SELECT 1 FROM copy_trade_signals WHERE id = ?', (signal_id,)).fetchone() is not None
        copy_reason = _make_copy_reason(
            politician['name'],
            politician.get('party') or trade.get('party') or '',
            trade.get('chamber') or politician.get('chamber') or 'house',
            politician.get('tracking_reason') or '',
            trade,
        )
        conn.execute(
            '''
            INSERT OR IGNORE INTO copy_trade_signals (
                id, politician_trade_id, politician_id, politician_name, tracking_reason,
                ticker, signal_side, signal_strength, copy_reason, estimated_qty, status,
                cro_notes, alpaca_order_id, created_at, reviewed_at, executed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', '', '', ?, '', '')
            ''',
            (
                signal_id,
                trade['id'],
                politician['id'],
                politician['name'],
                politician.get('tracking_reason') or '',
                trade.get('ticker') or '',
                _signal_side(str(trade.get('trade_type') or '')),
                _signal_strength(float(trade.get('amount_midpoint') or 0)),
                copy_reason,
                0.0,
                _now_iso(),
            ),
        )
        signal_created = not existed_before and conn.execute('SELECT 1 FROM copy_trade_signals WHERE id = ?', (signal_id,)).fetchone() is not None
    return (True, signal_created)


def _refresh_politician(conn, politician: dict[str, Any]) -> dict[str, int]:
    chamber = _normalize_chamber(str(politician.get('chamber') or 'both'))
    if chamber == 'house':
        trades = capitol_trades_client.fetch_house_trades(name_filter=politician['name'])
    elif chamber == 'senate':
        trades = capitol_trades_client.fetch_senate_trades(name_filter=politician['name'])
    else:
        trades = capitol_trades_client.fetch_all_trades(name_filter=politician['name'])
    new_trades = 0
    new_signals = 0
    for trade in trades:
        created_trade, created_signal = _ingest_trade(conn, politician, trade)
        if created_trade:
            new_trades += 1
        if created_signal:
            new_signals += 1
            if not politician.get('party') and trade.get('party'):
                politician['party'] = trade.get('party')
            if not politician.get('state') and trade.get('state'):
                politician['state'] = trade.get('state')
    if politician.get('party') or politician.get('state'):
        conn.execute(
            'UPDATE tracked_politicians SET party = ?, state = ?, updated_at = ? WHERE id = ?',
            (politician.get('party') or '', politician.get('state') or '', _now_iso(), politician['id']),
        )
    _sync_politician_stats(conn, politician['id'])
    _recalculate_performance(conn, politician['id'])
    return {'new_trades': new_trades, 'new_signals': new_signals}


@router.get('/status')
async def capitol_trades_status():
    return {
        'sources': ['housestockwatcher.com', 'senatestockwatcher.com'],
        'alpaca_ok': bool(alpaca_client.ALPACA_OK and alpaca_client.is_configured()),
    }


@router.get('/politicians')
async def list_politicians(current_user: dict = Depends(get_current_user)):
    del current_user
    conn = _db_connection()
    try:
        _recalculate_performance(conn)
        rows = conn.execute('SELECT * FROM tracked_politicians ORDER BY created_at DESC').fetchall()
        return [_serialize_politician_row(row) for row in rows]
    finally:
        conn.close()


@router.post('/politicians')
async def add_politician(body: AddPoliticianRequest, current_user: dict = Depends(get_current_user)):
    del current_user
    tracking_reason = body.tracking_reason.strip()
    if not tracking_reason:
        raise HTTPException(status_code=400, detail='tracking_reason is required')
    chamber = _normalize_chamber(body.chamber)
    now = _now_iso()
    politician_id = uuid.uuid4().hex
    conn = _db_connection()
    try:
        conn.execute(
            '''
            INSERT INTO tracked_politicians (
                id, name, chamber, party, state, tracking_reason, performance_note,
                track_since, is_active, total_signals, approved_signals, profitable_signals,
                total_return_pct, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, '', ?, 1, 0, 0, 0, 0.0, ?, ?)
            ''',
            (
                politician_id,
                body.name.strip(),
                chamber,
                body.party.strip(),
                body.state.strip(),
                tracking_reason,
                now,
                now,
                now,
            ),
        )
        politician = _politician_or_404(conn, politician_id)
        summary = _refresh_politician(conn, politician)
        conn.commit()
        result = _politician_or_404(conn, politician_id)
        result.update(summary)
        return result
    finally:
        conn.close()


@router.get('/politicians/{politician_id}')
async def get_politician(politician_id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    conn = _db_connection()
    try:
        _recalculate_performance(conn, politician_id)
        return _politician_or_404(conn, politician_id)
    finally:
        conn.close()


@router.patch('/politicians/{politician_id}')
async def update_politician(politician_id: str, body: UpdatePoliticianRequest, current_user: dict = Depends(get_current_user)):
    del current_user
    updates: list[str] = []
    params: list[Any] = []
    if body.tracking_reason is not None:
        reason = body.tracking_reason.strip()
        if not reason:
            raise HTTPException(status_code=400, detail='tracking_reason cannot be empty')
        updates.append('tracking_reason = ?')
        params.append(reason)
    if body.performance_note is not None:
        updates.append('performance_note = ?')
        params.append(body.performance_note.strip())
    if body.is_active is not None:
        updates.append('is_active = ?')
        params.append(1 if body.is_active else 0)
    if not updates:
        raise HTTPException(status_code=400, detail='No updates provided')
    updates.append('updated_at = ?')
    params.append(_now_iso())
    params.append(politician_id)
    conn = _db_connection()
    try:
        cur = conn.execute(f"UPDATE tracked_politicians SET {', '.join(updates)} WHERE id = ?", params)
        if cur.rowcount <= 0:
            raise HTTPException(status_code=404, detail='Tracked politician not found')
        conn.commit()
        return _politician_or_404(conn, politician_id)
    finally:
        conn.close()


@router.delete('/politicians/{politician_id}')
async def delete_politician(politician_id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    conn = _db_connection()
    try:
        cur = conn.execute('UPDATE tracked_politicians SET is_active = 0, updated_at = ? WHERE id = ?', (_now_iso(), politician_id))
        if cur.rowcount <= 0:
            raise HTTPException(status_code=404, detail='Tracked politician not found')
        conn.commit()
        return {'ok': True, 'id': politician_id, 'is_active': False}
    finally:
        conn.close()


@router.get('/politicians/{politician_id}/trades')
async def get_politician_trades(politician_id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    conn = _db_connection()
    try:
        _politician_or_404(conn, politician_id)
        rows = conn.execute(
            'SELECT * FROM politician_trades WHERE politician_id = ? ORDER BY transaction_date DESC, disclosure_date DESC LIMIT 100',
            (politician_id,),
        ).fetchall()
        return [_serialize_trade_row(row) for row in rows]
    finally:
        conn.close()


@router.get('/politicians/{politician_id}/signals')
async def get_politician_signals(politician_id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    conn = _db_connection()
    try:
        _politician_or_404(conn, politician_id)
        rows = conn.execute(
            '''
            SELECT s.*, t.trade_type, t.asset_name, t.amount_range, t.amount_midpoint, t.transaction_date, t.disclosure_date
            FROM copy_trade_signals s
            LEFT JOIN politician_trades t ON t.id = s.politician_trade_id
            WHERE s.politician_id = ?
            ORDER BY s.created_at DESC
            ''',
            (politician_id,),
        ).fetchall()
        return [_serialize_signal_row(row) for row in rows]
    finally:
        conn.close()


@router.post('/politicians/{politician_id}/refresh')
async def refresh_politician(politician_id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    conn = _db_connection()
    try:
        politician = _politician_or_404(conn, politician_id)
        summary = _refresh_politician(conn, politician)
        conn.commit()
        return summary
    finally:
        conn.close()


@router.get('/trades')
async def list_trades(
    ticker: Optional[str] = Query(None),
    politician_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=3650),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
):
    del current_user
    filters = ['transaction_date >= ?']
    params: list[Any] = [(date.today() - timedelta(days=days)).isoformat()]
    if ticker:
        filters.append('ticker = ?')
        params.append(ticker.strip().upper())
    if politician_id:
        filters.append('politician_id = ?')
        params.append(politician_id)
    conn = _db_connection()
    try:
        rows = conn.execute(
            f"SELECT * FROM politician_trades WHERE {' AND '.join(filters)} ORDER BY transaction_date DESC, disclosure_date DESC LIMIT ?",
            params + [limit],
        ).fetchall()
        return [_serialize_trade_row(row) for row in rows]
    finally:
        conn.close()


@router.get('/signals')
async def list_signals(
    status: Optional[str] = Query('pending'),
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
):
    del current_user
    where = ''
    params: list[Any] = []
    if status:
        where = 'WHERE s.status = ?'
        params.append(status.strip().lower())
    conn = _db_connection()
    try:
        rows = conn.execute(
            f'''
            SELECT s.*, t.trade_type, t.asset_name, t.amount_range, t.amount_midpoint, t.transaction_date, t.disclosure_date
            FROM copy_trade_signals s
            LEFT JOIN politician_trades t ON t.id = s.politician_trade_id
            {where}
            ORDER BY COALESCE(s.executed_at, s.reviewed_at, s.created_at) DESC
            LIMIT ?
            ''',
            params + [limit],
        ).fetchall()
        return [_serialize_signal_row(row) for row in rows]
    finally:
        conn.close()


@router.post('/signals/{signal_id}/review')
async def review_signal(signal_id: str, body: ReviewSignalRequest, current_user: dict = Depends(get_current_user)):
    action = body.action.strip().lower()
    if action not in ALLOWED_REVIEW_ACTIONS:
        raise HTTPException(status_code=400, detail='action must be one of: approve, reject')
    order_type = body.order_type.strip().lower()
    tif = body.time_in_force.strip().lower()
    if order_type not in ALLOWED_ORDER_TYPES:
        raise HTTPException(status_code=400, detail='order_type must be one of: market, limit')
    if tif not in ALLOWED_TIFS:
        raise HTTPException(status_code=400, detail='time_in_force must be one of: day, gtc, ioc, fok')
    conn = _db_connection()
    try:
        signal = _signal_or_404(conn, signal_id)
        if signal.get('status') != 'pending':
            raise HTTPException(status_code=400, detail='Signal has already been reviewed')
        reviewed_at = _now_iso()
        if action == 'reject':
            conn.execute(
                '''
                UPDATE copy_trade_signals
                SET status = 'rejected', cro_notes = ?, reviewed_at = ?
                WHERE id = ?
                ''',
                (body.cro_notes.strip(), reviewed_at, signal_id),
            )
            _sync_politician_stats(conn, str(signal['politician_id']))
            _recalculate_performance(conn, str(signal['politician_id']))
            conn.commit()
            return {'signal': _signal_or_404(conn, signal_id), 'order': None}

        _ensure_alpaca_ready()
        qty = float(body.qty) if body.qty is not None else 0.0
        quote = None
        if qty <= 0:
            try:
                quote = alpaca_client.get_latest_quote(str(signal.get('ticker') or '').upper())
            except Exception:
                quote = None
            current_price = _quote_price(quote)
            amount_midpoint = float(signal.get('amount_midpoint') or 0)
            if current_price and current_price > 0:
                qty = max(1, round(min(amount_midpoint, 5000) / current_price, 0))
            else:
                qty = 1
        order = alpaca_client.place_order(
            symbol=str(signal.get('ticker') or '').upper(),
            qty=qty,
            side=str(signal.get('signal_side') or 'buy').lower(),
            order_type=order_type,
            time_in_force=tif,
            limit_price=body.limit_price,
        )
        order_id = str(order.get('id') or order.get('order_id') or uuid.uuid4())
        now = _now_iso()
        conn.execute(
            '''
            INSERT INTO alpaca_orders (
                id, symbol, side, order_type, qty, limit_price, stop_price,
                time_in_force, status, agent_reason, submitted_by, alpaca_response,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status,
                qty = excluded.qty,
                limit_price = excluded.limit_price,
                time_in_force = excluded.time_in_force,
                alpaca_response = excluded.alpaca_response,
                updated_at = excluded.updated_at
            ''',
            (
                order_id,
                str(signal.get('ticker') or '').upper(),
                str(signal.get('signal_side') or 'buy').lower(),
                order_type,
                float(qty),
                body.limit_price,
                None,
                tif,
                str(order.get('status') or 'submitted'),
                str(signal.get('copy_reason') or ''),
                current_user.get('username', ''),
                _json_dumps(order),
                str(order.get('created_at') or now),
                str(order.get('updated_at') or now),
            ),
        )
        conn.execute(
            '''
            UPDATE copy_trade_signals
            SET status = 'executed', cro_notes = ?, reviewed_at = ?, executed_at = ?, alpaca_order_id = ?, estimated_qty = ?
            WHERE id = ?
            ''',
            (body.cro_notes.strip(), reviewed_at, now, order_id, float(qty), signal_id),
        )
        _sync_politician_stats(conn, str(signal['politician_id']))
        _recalculate_performance(conn, str(signal['politician_id']))
        conn.commit()
        return {'signal': _signal_or_404(conn, signal_id), 'order': order, 'quote': quote}
    finally:
        conn.close()


@router.post('/refresh-all')
async def refresh_all_politicians(current_user: dict = Depends(get_current_user)):
    del current_user
    conn = _db_connection()
    try:
        rows = conn.execute('SELECT * FROM tracked_politicians WHERE is_active = 1 ORDER BY created_at DESC').fetchall()
        summary = {'politicians': 0, 'new_trades': 0, 'new_signals': 0, 'results': []}
        for row in rows:
            politician = _serialize_politician_row(row)
            result = _refresh_politician(conn, politician)
            summary['politicians'] += 1
            summary['new_trades'] += result['new_trades']
            summary['new_signals'] += result['new_signals']
            summary['results'].append({'id': politician['id'], 'name': politician['name'], **result})
        conn.commit()
        return summary
    finally:
        conn.close()


@router.get('/leaderboard')
async def copy_trading_leaderboard(current_user: dict = Depends(get_current_user)):
    del current_user
    conn = _db_connection()
    try:
        _recalculate_performance(conn)
        rows = conn.execute(
            '''
            SELECT *
            FROM tracked_politicians
            ORDER BY
                CASE WHEN approved_signals > 0 THEN CAST(profitable_signals AS REAL) / approved_signals ELSE 0 END DESC,
                total_return_pct DESC,
                approved_signals DESC,
                created_at DESC
            '''
        ).fetchall()
        leaderboard = []
        for row in rows:
            item = _serialize_politician_row(row)
            leaderboard.append(
                {
                    'id': item['id'],
                    'name': item['name'],
                    'chamber': item.get('chamber') or 'both',
                    'party': item.get('party') or '',
                    'tracking_reason': item.get('tracking_reason') or '',
                    'signals': item['signal_counts']['approved'],
                    'approved_signals': item['signal_counts']['approved'],
                    'profitable_signals': item['signal_counts']['profitable'],
                    'win_rate': item['win_rate'],
                    'total_return_pct': float(item.get('total_return_pct') or 0),
                }
            )
        return leaderboard
    finally:
        conn.close()
