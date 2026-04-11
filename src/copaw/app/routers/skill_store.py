# -*- coding: utf-8 -*-
"""
Enterprise Skill Store API.
Allows users to discover and install enterprise-grade skills.
"""
from __future__ import annotations

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from ...agents.skills_manager import SkillPoolService, SkillInfo, get_workspace_skills_dir
from ...db.postgresql import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/skill-store", tags=["skill-store"])

class SkillStoreItem(BaseModel):
    name: str
    description: str
    emoji: str
    version: str
    source: str

class InstallSkillRequest(BaseModel):
    skill_name: str
    workspace_dir: str  # The physical path of the agent's workspace

@router.get("", response_model=List[SkillStoreItem])
async def list_store_skills():
    """List all skills available in the enterprise pool."""
    pool_service = SkillPoolService()
    skills = pool_service.list_all_skills()
    
    return [
        SkillStoreItem(
            name=s.name,
            description=s.description,
            emoji=s.emoji or "🔧",
            version=s.version_text or "1.0.0",
            source=s.source
        )
        for s in skills
    ]

@router.post("/install")
async def install_skill(request: InstallSkillRequest):
    """Install a skill from the pool into a specific workspace."""
    pool_service = SkillPoolService()
    workspace_path = Path(request.workspace_dir).expanduser()
    
    if not workspace_path.exists():
        raise HTTPException(status_code=400, detail="Workspace directory not found.")

    try:
        result = pool_service.download_to_workspace(
            skill_name=request.skill_name,
            workspace_dir=workspace_path,
            overwrite=True
        )
        
        if result.get("success"):
            return {"success": True, "message": f"Skill {request.skill_name} installed successfully."}
        else:
            raise HTTPException(status_code=500, detail=result.get("reason", "Installation failed."))
            
    except Exception as e:
        logger.error(f"Failed to install skill: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Installation error: {str(e)}")
