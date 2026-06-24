from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_admin_user, get_current_user
from core.models import ModelRouteRequest, ModelToggle

try:
    from model_catalog import (
        get_catalog as _mc_get_catalog,
        set_model_enabled as _mc_set_enabled,
        route_for_task as _mc_route,
        CATALOG as _MC_CATALOG,
    )
    MODEL_CATALOG_OK = True
except ImportError:
    MODEL_CATALOG_OK = False

router = APIRouter()

@router.get("/models")
async def list_models(current_user: dict = Depends(get_current_user)):
    """Return full model catalog with enabled state and key status."""
    del current_user
    if not MODEL_CATALOG_OK:
        raise HTTPException(503, "Model catalog not available")
    return _mc_get_catalog()

@router.put("/models/toggle")
async def toggle_model(body: ModelToggle, admin_user: dict = Depends(get_admin_user)):
    """Enable or disable a specific model."""
    del admin_user
    if not MODEL_CATALOG_OK:
        raise HTTPException(503, "Model catalog not available")
    _mc_set_enabled(body.provider, body.model_id, body.enabled)
    return {"provider": body.provider, "model_id": body.model_id, "enabled": body.enabled}

@router.post("/models/route")
async def route_model(body: ModelRouteRequest, current_user: dict = Depends(get_current_user)):
    """
    Perplexity-style routing: given a task_type and optional agent_id,
    return the best available enabled model for that task.
    """
    del current_user
    if not MODEL_CATALOG_OK:
        raise HTTPException(503, "Model catalog not available")
    result = _mc_route(body.task_type, body.agent_id)
    if not result:
        raise HTTPException(503, "No enabled model available for this task type")
    return result

@router.get("/models/providers")
async def list_providers(current_user: dict = Depends(get_current_user)):
    """Return distinct providers with their key status and model counts."""
    del current_user
    if not MODEL_CATALOG_OK:
        raise HTTPException(503, "Model catalog not available")
    from model_catalog import PROVIDER_ENV_KEYS, provider_has_key
    catalog = _mc_get_catalog()
    providers: dict[str, dict] = {}
    for m in catalog:
        p = m["provider"]
        if p not in providers:
            providers[p] = {
                "provider":       p,
                "key_configured": m["key_configured"],
                "env_key":        PROVIDER_ENV_KEYS.get(p, ""),
                "total_models":   0,
                "enabled_models": 0,
            }
        providers[p]["total_models"] += 1
        if m["enabled"]:
            providers[p]["enabled_models"] += 1
    return list(providers.values())
