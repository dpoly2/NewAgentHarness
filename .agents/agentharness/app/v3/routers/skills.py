from __future__ import annotations

from fastapi import APIRouter, Depends

from core.auth import get_current_user
from core.config import SKILLS_ROOT
from core.database import _latest_skill, _list_records, _save_skill

router = APIRouter()

@router.get("/skills")
async def list_skills(current_user: dict = Depends(get_current_user)):
    del current_user
    skills = _list_records("skills", order_by="id DESC")
    if skills:
        return skills
    result = []
    if SKILLS_ROOT.exists():
        for skill_file in SKILLS_ROOT.rglob("*.md"):
            result.append({"agent_id": skill_file.stem, "path": str(skill_file), "content": skill_file.read_text(encoding="utf-8")})
    return result


@router.get("/skills/{agent_id}")
async def get_skill(agent_id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    return _latest_skill(agent_id)


@router.put("/skills/{agent_id}")
async def update_skill(agent_id: str, body: dict, current_user: dict = Depends(get_current_user)):
    del current_user
    content = str(body.get("content", ""))
    version = body.get("version")
    return _save_skill(agent_id, content, version=version)
