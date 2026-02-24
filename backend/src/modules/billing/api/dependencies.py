"""Billing API 依赖注入。"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.billing.application.services.billing_service import BillingService
from src.modules.billing.infrastructure.persistence.repositories.budget_repository_impl import BudgetRepositoryImpl
from src.modules.billing.infrastructure.persistence.repositories.department_repository_impl import (
    DepartmentRepositoryImpl,
)
from src.shared.infrastructure.database import get_db


async def get_billing_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BillingService:
    """创建 BillingService 实例。"""
    return BillingService(
        department_repo=DepartmentRepositoryImpl(session=session),
        budget_repo=BudgetRepositoryImpl(session=session),
    )
