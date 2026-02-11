"""Template API 依赖注入。"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.templates.application.services.template_service import TemplateService
from src.modules.templates.infrastructure.persistence.repositories.template_repository_impl import (
    TemplateRepositoryImpl,
)
from src.shared.infrastructure.database import get_db


async def get_template_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TemplateService:
    """创建 TemplateService 实例。"""
    return TemplateService(
        template_repo=TemplateRepositoryImpl(session=session),
    )
