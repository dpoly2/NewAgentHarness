from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_admin_user
from core.database import _create_user, _db_connection, _delete_record, _update_record, _user_by_id, _user_by_username, _user_public
from core.models import RegisterRequest, UserUpdate

router = APIRouter()

@router.get("/users")
async def list_users(admin_user: dict = Depends(get_admin_user)):
    del admin_user
    conn = _db_connection()
    try:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at ASC").fetchall()
        return [_user_public(dict(row)) for row in rows]
    finally:
        conn.close()


@router.post("/users")
async def create_user_endpoint(body: RegisterRequest, admin_user: dict = Depends(get_admin_user)):
    del admin_user
    if _user_by_username(body.username):
        raise HTTPException(400, "Username already exists")
    return _create_user(body.username, body.email, body.password, role=body.role)


@router.get("/users/{id}")
async def get_user(id: int, admin_user: dict = Depends(get_admin_user)):
    del admin_user
    user = _user_public(_user_by_id(id))
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.put("/users/{id}")
async def update_user(id: int, body: UserUpdate, admin_user: dict = Depends(get_admin_user)):
    del admin_user
    updates = {key: value for key, value in body.model_dump(exclude_unset=True).items()}
    if "is_active" in updates:
        updates["is_active"] = 1 if updates["is_active"] else 0
    user = _update_record("users", id, updates)
    if not user:
        raise HTTPException(404, "User not found")
    return _user_public(user)


@router.delete("/users/{id}")
async def delete_user(id: int, admin_user: dict = Depends(get_admin_user)):
    del admin_user
    if not _delete_record("users", id):
        raise HTTPException(404, "User not found")
    return {"id": id, "deleted": True}
