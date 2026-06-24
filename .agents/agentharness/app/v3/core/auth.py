from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time as _time
from datetime import timedelta
from typing import Any, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import ACCESS_TOKEN_EXPIRE_HOURS, ALGORITHM, SECRET_KEY, _JWT_SECRET_DEFAULT
from core.database import (
    _b64url_decode,
    _b64url_encode,
    _config_value,
    _json_dumps,
    _user_by_id,
    _user_by_username,
    _user_public,
    _utcnow,
)

try:
    from jose import JWTError, jwt

    JWT_OK = True
except ImportError:
    JWT_OK = False

    class JWTError(Exception):
        pass

try:
    from ah_logging import get_logger
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

    def get_logger(name: str):
        return logging.getLogger(f'archonhub.{name}')

logger = get_logger('auth')
security = HTTPBearer(auto_error=False)

def create_access_token(data: dict) -> str:
    payload = dict(data)
    payload["exp"] = int((_utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)).timestamp())
    if JWT_OK:
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    header = {"alg": ALGORITHM, "typ": "JWT"}
    encoded_header = _b64url_encode(_json_dumps(header).encode("utf-8"))
    encoded_payload = _b64url_encode(_json_dumps(payload).encode("utf-8"))
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        f"{encoded_header}.{encoded_payload}".encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{encoded_header}.{encoded_payload}.{_b64url_encode(signature)}"


def verify_token(token: str) -> dict | None:
    try:
        if JWT_OK:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        header, payload, signature = token.split(".")
        expected = hmac.new(
            SECRET_KEY.encode("utf-8"),
            f"{header}.{payload}".encode("utf-8"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(expected, _b64url_decode(signature)):
            return None
        data = json.loads(_b64url_decode(payload).decode("utf-8"))
        if int(data.get("exp", 0)) < int(_utcnow().timestamp()):
            return None
        return data
    except (ValueError, JWTError, json.JSONDecodeError):
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_token: Optional[str] = Header(default=None),
) -> dict:
    api_token = _config_value("api_token")
    if x_api_token and api_token and hmac.compare_digest(str(x_api_token), str(api_token)):
        return {
            "id": 0,
            "username": "api-token",
            "email": "",
            "role": "admin",
            "is_active": True,
        }
    if not credentials or getattr(credentials, "scheme", "").lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("user_id")
    user = _user_by_id(int(user_id)) if user_id is not None else _user_by_username(payload.get("username", ""))
    public_user = _user_public(user)
    if not public_user or not public_user.get("is_active", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")
    return public_user


async def get_admin_user(user: dict = Depends(get_current_user)) -> dict:
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user

# ── Simple IP-based rate limiter for login endpoint ──────────────────────────
import time as _time
_login_attempts: dict[str, list[float]] = {}
_LOGIN_MAX_ATTEMPTS = 10
_LOGIN_WINDOW_SECONDS = 300  # 5 minutes


def _check_login_rate_limit(client_ip: str) -> None:
    """Raise 429 if too many login attempts from this IP in the window."""
    now = _time.monotonic()
    window_start = now - _LOGIN_WINDOW_SECONDS
    attempts = _login_attempts.get(client_ip, [])
    # Prune old attempts
    attempts = [t for t in attempts if t > window_start]
    if len(attempts) >= _LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Try again in {_LOGIN_WINDOW_SECONDS // 60} minutes.",
        )
    attempts.append(now)
    _login_attempts[client_ip] = attempts


def make_emit(run_id: str):
    async def _emit(event_type: str, **kwargs: Any):
        await hub.broadcast({"type": event_type, "run_id": run_id, **kwargs})

    def emit(event_type: str, **kwargs: Any):
        loop = hub._loop
        if loop is None:
            return
        asyncio.run_coroutine_threadsafe(_emit(event_type, **kwargs), loop)

    return emit


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    try:
        from core.hub import hub
        hub.logger.exception('Unhandled exception for %s %s', request.method, request.url.path)
    except Exception:
        logger.exception('Unhandled exception for %s %s', request.method, request.url.path)
    return JSONResponse(status_code=500, content={'detail': 'Internal server error'})
