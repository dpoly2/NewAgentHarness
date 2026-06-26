"""capitol_trades_client.py — Fetches politician trade disclosures from public APIs."""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import date, datetime

import httpx

logger = logging.getLogger(__name__)

HOUSE_URL = "https://housestockwatcher.com/api"
SENATE_URL = "https://senatestockwatcher.com/api"
_TIMEOUT = 15.0
_AMOUNT_RE = re.compile(r"\$?([\d,]+(?:\.\d+)?)\s*-\s*\$?([\d,]+(?:\.\d+)?)")


def parse_amount_range(amount_str: str) -> tuple[float, float]:
    text = str(amount_str or "").strip()
    if not text:
        return (0.0, 0.0)
    match = _AMOUNT_RE.search(text)
    if not match:
        return (0.0, 0.0)
    try:
        low = float(match.group(1).replace(',', ''))
        high = float(match.group(2).replace(',', ''))
        return (low, high)
    except Exception:
        return (0.0, 0.0)


def _normalize_date(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if 'T' in text:
        text = text.split('T', 1)[0]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return date.fromisoformat(text).isoformat()
    except Exception:
        return text


def _normalize_ticker(value: object) -> str:
    ticker = str(value or '').strip().upper()
    if ticker in {'--', 'N/A', 'NA', 'NONE', 'NULL'}:
        return ''
    return ticker


def _normalize_trade_type(value: object) -> str:
    trade_type = str(value or '').strip().lower()
    if trade_type in {'purchase', 'sale', 'exchange'}:
        return trade_type
    return 'other'


def _make_id(politician_name: str, ticker: str, transaction_date: str, trade_type: str) -> str:
    payload = f"{politician_name}|{ticker}|{transaction_date}|{trade_type}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]


def _normalize_house_trade(row: dict) -> dict:
    politician_name = str(row.get('representative') or '').strip()
    ticker = _normalize_ticker(row.get('ticker'))
    amount_range = str(row.get('amount') or '').strip()
    amount_min, amount_max = parse_amount_range(amount_range)
    transaction_date = _normalize_date(row.get('transaction_date'))
    disclosure_date = _normalize_date(row.get('disclosure_date'))
    trade_type = _normalize_trade_type(row.get('type'))
    return {
        'id': _make_id(politician_name, ticker, transaction_date, trade_type),
        'politician_name': politician_name,
        'chamber': 'house',
        'party': str(row.get('party') or '').strip(),
        'state': str(row.get('district') or row.get('state') or '').strip(),
        'ticker': ticker,
        'asset_name': str(row.get('asset_description') or '').strip(),
        'trade_type': trade_type,
        'amount_range': amount_range,
        'amount_min': amount_min,
        'amount_max': amount_max,
        'amount_midpoint': (amount_min + amount_max) / 2 if amount_min or amount_max else 0.0,
        'transaction_date': transaction_date,
        'disclosure_date': disclosure_date,
        'raw': row,
    }


def _normalize_senate_trade(row: dict) -> dict:
    politician_name = str(row.get('senator') or '').strip()
    ticker = _normalize_ticker(row.get('ticker'))
    amount_range = str(row.get('amount') or '').strip()
    amount_min, amount_max = parse_amount_range(amount_range)
    transaction_date = _normalize_date(row.get('transaction_date'))
    disclosure_date = _normalize_date(row.get('disclosure_date'))
    trade_type = _normalize_trade_type(row.get('type'))
    return {
        'id': _make_id(politician_name, ticker, transaction_date, trade_type),
        'politician_name': politician_name,
        'chamber': 'senate',
        'party': str(row.get('party') or '').strip(),
        'state': str(row.get('state') or '').strip(),
        'ticker': ticker,
        'asset_name': str(row.get('asset_type') or row.get('asset_description') or '').strip(),
        'trade_type': trade_type,
        'amount_range': amount_range,
        'amount_min': amount_min,
        'amount_max': amount_max,
        'amount_midpoint': (amount_min + amount_max) / 2 if amount_min or amount_max else 0.0,
        'transaction_date': transaction_date,
        'disclosure_date': disclosure_date,
        'raw': row,
    }


def _fetch_rows(url: str) -> list[dict]:
    try:
        with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, list):
                return [row for row in payload if isinstance(row, dict)]
    except Exception:
        logger.exception('Failed to fetch Capitol trades from %s', url)
    return []


def _filter_by_name(rows: list[dict], key: str, name_filter: str | None) -> list[dict]:
    if not name_filter:
        return rows
    needle = name_filter.strip().lower()
    if not needle:
        return rows
    return [row for row in rows if needle in str(row.get(key) or '').lower()]


def fetch_house_trades(name_filter: str | None = None) -> list[dict]:
    rows = _filter_by_name(_fetch_rows(HOUSE_URL), 'representative', name_filter)
    return [_normalize_house_trade(row) for row in rows]


def fetch_senate_trades(name_filter: str | None = None) -> list[dict]:
    rows = _filter_by_name(_fetch_rows(SENATE_URL), 'senator', name_filter)
    return [_normalize_senate_trade(row) for row in rows]


def fetch_all_trades(name_filter: str | None = None) -> list[dict]:
    trades = fetch_house_trades(name_filter=name_filter) + fetch_senate_trades(name_filter=name_filter)
    return sorted(trades, key=lambda item: item.get('transaction_date') or '', reverse=True)
