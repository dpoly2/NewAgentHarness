from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.database import _create_record, _get_record, _list_records, _now_iso, _update_record
from core.models import ConversationCreate, MessageCreate

router = APIRouter()

@router.get("/conversations")
async def list_conversations(current_user: dict = Depends(get_current_user)):
    del current_user
    return _list_records("conversations", order_by="updated_at DESC")


@router.post("/conversations")
async def create_conversation(body: ConversationCreate, current_user: dict = Depends(get_current_user)):
    del current_user
    return _create_record(
        "conversations",
        {
            "id": uuid.uuid4().hex,
            "title": body.title,
            "slug": body.slug,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        },
    )


@router.get("/conversations/{id}/messages")
async def list_messages(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    if not _get_record("conversations", id):
        raise HTTPException(404, "Conversation not found")
    return _list_records("messages", where=["conversation_id = ?"], params=[id], order_by="created_at ASC")


@router.post("/conversations/{id}/messages")
async def create_message(id: str, body: MessageCreate, current_user: dict = Depends(get_current_user)):
    del current_user
    conversation = _get_record("conversations", id)
    if not conversation:
        raise HTTPException(404, "Conversation not found")
    message = _create_record(
        "messages",
        {
            "id": uuid.uuid4().hex,
            "conversation_id": id,
            "role": body.role,
            "content": body.content,
            "agent_id": body.agent_id,
            "created_at": _now_iso(),
        },
    )
    _update_record("conversations", id, {"updated_at": _now_iso()})
    return message
