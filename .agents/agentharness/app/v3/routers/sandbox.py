from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.models import SandboxExecuteRequest

router = APIRouter()


@router.get("/sandbox/status")
async def sandbox_status(_: dict = Depends(get_current_user)):
    try:
        from code_sandbox import get_sandbox_status
        return {"success": True, **get_sandbox_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sandbox/execute")
async def sandbox_execute(body: SandboxExecuteRequest, _: dict = Depends(get_current_user)):
    if not body.code.strip():
        raise HTTPException(status_code=400, detail="code is required")
    if len(body.code) > 50_000:
        raise HTTPException(status_code=400, detail="Code too large (max 50KB)")
    try:
        from code_sandbox import execute_code
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: execute_code(code=body.code, language=body.language, data_files=body.data_files or []),
        )
        return {
            "success": result.success,
            "execution_id": result.execution_id,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "execution_time_ms": result.execution_time_ms,
            "generated_files": result.generated_files,
            "error": result.error,
            "blocked_reason": result.blocked_reason,
            "mode": result.mode,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


