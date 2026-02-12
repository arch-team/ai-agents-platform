"""Tool Catalog API 依赖注入。"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.tool_catalog.application.services.tool_service import ToolCatalogService
from src.modules.tool_catalog.infrastructure.persistence.repositories.tool_repository_impl import (
    ToolRepositoryImpl,
)
from src.shared.infrastructure.database import get_db


async def get_tool_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ToolCatalogService:
    """创建 ToolCatalogService 实例。"""
    # 延迟导入避免循环依赖 (providers ↔ tool_catalog)
    from src.presentation.api.providers import get_gateway_sync

    return ToolCatalogService(
        repository=ToolRepositoryImpl(session=session),
        gateway_sync=get_gateway_sync(),  # type: ignore[arg-type]
    )
