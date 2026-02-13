"""审计模块 API 依赖注入。"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audit.application.services.audit_service import AuditService
from src.modules.audit.infrastructure.persistence.repositories.audit_log_repository_impl import (
    AuditLogRepositoryImpl,
)
from src.shared.infrastructure.database import get_db


async def get_audit_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AuditService:
    """创建 AuditService 实例。"""
    return AuditService(repository=AuditLogRepositoryImpl(session=session))
