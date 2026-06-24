from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from core.auth import get_current_user
from core.database import (
    _create_record, _delete_record, _get_record, _list_records,
    _now_iso, _update_record,
)
from core.models import ConnectorCreate, ConnectorUpdate

try:
    import hub_db as db
except ImportError:
    db = None  # type: ignore

try:
    from ah_logging import get_logger
except ImportError:
    import logging

    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("connectors")
router = APIRouter()


@router.get("/connectors")
async def list_connectors(_: dict = Depends(get_current_user)):
    return _list_records("email_connectors", order_by="updated_at DESC", json_fields={"credentials"})


@router.post("/connectors")
async def create_connector(body: ConnectorCreate, _: dict = Depends(get_current_user)):
    return _create_record(
        "email_connectors",
        {
            "id": uuid.uuid4().hex,
            "label": body.label,
            "email_address": body.email_address,
            "provider": body.provider,
            "auth_type": body.auth_type,
            "imap_host": body.imap_host,
            "imap_port": body.imap_port,
            "smtp_host": body.smtp_host,
            "smtp_port": body.smtp_port,
            "username": body.username,
            "credentials": body.credentials,
            "oauth_client_id": body.oauth_client_id,
            "oauth_client_secret": body.oauth_client_secret,
            "token_expires_at": "",
            "status": "pending",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        },
        json_fields={"credentials"},
    )


@router.get("/connectors/{id}")
async def get_connector(id: str, _: dict = Depends(get_current_user)):
    connector = _get_record("email_connectors", id, json_fields={"credentials"})
    if not connector:
        raise HTTPException(404, "Connector not found")
    return connector


@router.put("/connectors/{id}")
async def update_connector(id: str, body: ConnectorUpdate, _: dict = Depends(get_current_user)):
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    updates["updated_at"] = _now_iso()
    connector = _update_record("email_connectors", id, updates, json_fields={"credentials"})
    if not connector:
        raise HTTPException(404, "Connector not found")
    return connector


@router.delete("/connectors/{id}")
async def delete_connector(id: str, _: dict = Depends(get_current_user)):
    if not _delete_record("email_connectors", id):
        raise HTTPException(404, "Connector not found")
    return {"id": id, "deleted": True}


@router.post("/connectors/{id}/test")
async def test_connector_endpoint(id: str, _: dict = Depends(get_current_user)):
    connector = _get_record("email_connectors", id, json_fields={"credentials"})
    if not connector:
        raise HTTPException(404, "Connector not found")
    try:
        from oauth_connector import test_connector as _test
        ok, msg = _test(connector)
    except Exception as exc:
        ok, msg = False, str(exc)
    _update_record(
        "email_connectors", id,
        {
            "status": "active" if ok else "error",
            "last_error": "" if ok else msg,
            "last_synced": _now_iso() if ok else None,
        },
    )
    return {"ok": ok, "message": msg, "connector_id": id}


# ── OAuth endpoints ───────────────────────────────────────────────────────────

@router.get("/connectors/oauth/google/init")
async def google_oauth_init(connector_id: str):
    connector = _get_record("email_connectors", connector_id, json_fields={"credentials"})
    if not connector:
        raise HTTPException(404, "Connector not found")
    client_id = connector.get("oauth_client_id", "")
    client_sec = connector.get("oauth_client_secret", "")
    if not client_id:
        raise HTTPException(400, "oauth_client_id not set on this connector")
    try:
        from oauth_connector import GoogleOAuth, store_pending_state
        g = GoogleOAuth(client_id, client_sec, connector_id)
        url, state, verifier = g.get_authorization_url()
        store_pending_state(state, connector_id, "google", verifier)
        return {"auth_url": url, "state": state}
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@router.get("/connectors/oauth/google/callback")
async def google_oauth_callback(code: str, state: str):
    try:
        from oauth_connector import GoogleOAuth, consume_pending_state
        import time as _time
        pending = consume_pending_state(state)
        if not pending:
            return HTMLResponse("<h3>OAuth Error</h3><p>Invalid or expired state. Please retry from the app.</p>", status_code=400)
        connector_id = pending["connector_id"]
        verifier = pending["verifier"]
        connector = _get_record("email_connectors", connector_id, json_fields={"credentials"})
        if not connector:
            return HTMLResponse("<h3>OAuth Error</h3><p>Connector not found.</p>", status_code=404)
        client_id = connector.get("oauth_client_id", "")
        client_sec = connector.get("oauth_client_secret", "")
        g = GoogleOAuth(client_id, client_sec, connector_id)
        token = g.exchange_code(code, verifier)
        _update_record(
            "email_connectors", connector_id,
            {
                "auth_type": "oauth2",
                "status": "active",
                "token_expires_at": str(int(token.get("expires_at", _time.time() + 3600))),
                "last_error": "",
                "last_synced": _now_iso(),
            },
        )
        email = token.get("email", connector.get("email_address", ""))
        return HTMLResponse(
            f"<html><body style='font-family:sans-serif;background:#0d1117;color:#e8eaf0;"
            f"display:flex;align-items:center;justify-content:center;height:100vh'>"
            f"<div style='text-align:center'><h2 style='color:#00c864'>✅ Gmail Connected</h2>"
            f"<p>{email}</p><p style='color:#6b7a99'>You can close this tab.</p>"
            f"<script>setTimeout(()=>window.close(),3000)</script></div></body></html>"
        )
    except Exception as exc:
        logger.error("Google OAuth callback error: %s", exc)
        return HTMLResponse(
            f"<html><body style='background:#0d1117;color:#ff4444;"
            f"display:flex;align-items:center;justify-content:center;height:100vh'>"
            f"<div><h2>❌ OAuth Failed</h2><p>{exc}</p></div></body></html>",
            status_code=500,
        )


@router.get("/connectors/oauth/gmail/init")
async def gmail_oauth_init(connector_id: str):
    return await google_oauth_init(connector_id=connector_id)


@router.get("/connectors/oauth/gmail/callback")
async def gmail_oauth_callback(code: str, state: str):
    return await google_oauth_callback(code=code, state=state)


@router.get("/connectors/oauth/microsoft/init")
async def microsoft_oauth_init(connector_id: str):
    connector = _get_record("email_connectors", connector_id, json_fields={"credentials"})
    if not connector:
        raise HTTPException(404, "Connector not found")
    client_id = connector.get("oauth_client_id", "")
    client_sec = connector.get("oauth_client_secret", "")
    if not client_id:
        raise HTTPException(400, "oauth_client_id not set on this connector")
    try:
        from oauth_connector import MicrosoftOAuth, store_pending_state
        m = MicrosoftOAuth(client_id, client_sec, connector_id)
        url, state = m.get_authorization_url()
        store_pending_state(state, connector_id, "microsoft")
        return {"auth_url": url, "state": state}
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@router.get("/connectors/oauth/microsoft/callback")
async def microsoft_oauth_callback(code: str, state: str):
    try:
        from oauth_connector import MicrosoftOAuth, consume_pending_state
        import time as _time
        pending = consume_pending_state(state)
        if not pending:
            return HTMLResponse("<h3>OAuth Error</h3><p>Invalid or expired state.</p>", status_code=400)
        connector_id = pending["connector_id"]
        connector = _get_record("email_connectors", connector_id, json_fields={"credentials"})
        if not connector:
            return HTMLResponse("<h3>OAuth Error</h3><p>Connector not found.</p>", status_code=404)
        client_id = connector.get("oauth_client_id", "")
        client_sec = connector.get("oauth_client_secret", "")
        m = MicrosoftOAuth(client_id, client_sec, connector_id)
        token = m.exchange_code(code)
        _update_record(
            "email_connectors", connector_id,
            {
                "auth_type": "oauth2",
                "status": "active",
                "token_expires_at": str(int(token.get("expires_at", _time.time() + 3600))),
                "last_error": "",
                "last_synced": _now_iso(),
            },
        )
        email = token.get("email", connector.get("email_address", ""))
        return HTMLResponse(
            f"<html><body style='font-family:sans-serif;background:#0d1117;color:#e8eaf0;"
            f"display:flex;align-items:center;justify-content:center;height:100vh'>"
            f"<div style='text-align:center'><h2 style='color:#00c864'>✅ Outlook Connected</h2>"
            f"<p>{email}</p><p style='color:#6b7a99'>You can close this tab.</p>"
            f"<script>setTimeout(()=>window.close(),3000)</script></div></body></html>"
        )
    except Exception as exc:
        logger.error("Microsoft OAuth callback error: %s", exc)
        return HTMLResponse(
            f"<html><body style='background:#0d1117;color:#ff4444;"
            f"display:flex;align-items:center;justify-content:center;height:100vh'>"
            f"<div><h2>❌ OAuth Failed</h2><p>{exc}</p></div></body></html>",
            status_code=500,
        )


