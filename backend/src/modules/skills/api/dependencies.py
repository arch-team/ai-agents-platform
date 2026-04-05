"""Skills API 依赖注入。"""

from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.skills.application.services.skill_service import SkillService
from src.modules.skills.infrastructure.external.skill_file_manager_impl import SkillFileManagerImpl
from src.modules.skills.infrastructure.persistence.repositories.skill_repository_impl import (
    SkillRepositoryImpl,
)
from src.shared.infrastructure.database import get_db
from src.shared.infrastructure.settings import get_settings


async def get_skill_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SkillService:
    """创建 SkillService 实例。"""
    settings = get_settings()
    import tempfile

    skill_root = (
        Path(settings.SKILL_LIBRARY_ROOT)
        if settings.SKILL_LIBRARY_ROOT
        else Path(tempfile.gettempdir()) / "skill-library"
    )
    return SkillService(
        repository=SkillRepositoryImpl(session=session),
        file_manager=SkillFileManagerImpl(workspace_root=skill_root),
    )
