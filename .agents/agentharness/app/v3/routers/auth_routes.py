from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from pydantic import BaseModel

from core.auth import _check_login_rate_limit, create_access_token, get_current_user, security
from core.database import _authenticate_user, _count_rows, _create_user, _update_user_password, _user_by_username, _verify_password, _user_by_id
from core.models import LoginRequest, RegisterRequest

router = APIRouter()

async def _require_admin_for_registration(
    credentials: Optional[HTTPAuthorizationCredentials],
    x_api_token: Optional[str],
) -> None:
    if _count_rows("users") == 0:
        return
    user = await get_current_user(credentials, x_api_token)
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

@router.post("/auth/login")
async def login(body: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    _check_login_rate_limit(client_ip)
    user = _authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(
        {
            "sub": user["username"],
            "username": user["username"],
            "user_id": user["id"],
            "role": user["role"],
        }
    )
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/auth/register")
async def register(
    body: RegisterRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_token: Optional[str] = Header(default=None),
):
    await _require_admin_for_registration(credentials, x_api_token)
    if _user_by_username(body.username):
        raise HTTPException(400, "Username already exists")
    role = "admin" if _count_rows("users") == 0 else body.role
    user = _create_user(body.username, body.email, body.password, role=role)
    return user


@router.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    return current_user


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/auth/change-password")
async def change_password(body: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    # get_current_user returns _user_public(), whose primary key is "id"
    # (the JWT payload uses "user_id", but that payload is not what is injected here).
    raw_id = current_user.get("id", current_user.get("user_id"))
    if raw_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = int(raw_id)
    full_user = _user_by_id(user_id)
    if not full_user or not _verify_password(body.current_password, full_user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    _update_user_password(user_id, body.new_password)
    return {"ok": True}
