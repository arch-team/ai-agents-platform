"""Billing API 依赖注入。"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.billing.application.services.billing_service import BillingService
from src.modules.billing.infrastructure.external.department_cost_adapter import DepartmentCostAdapter
from src.modules.billing.infrastructure.persistence.repositories.budget_repository_impl import BudgetRepositoryImpl
from src.modules.billing.infrastructure.persistence.repositories.department_repository_impl import (
    DepartmentRepositoryImpl,
)
from src.shared.infrastructure.database import get_db


async def get_billing_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BillingService:
    """创建 BillingService 实例。"""
    department_repo = DepartmentRepositoryImpl(session=session)
    budget_repo = BudgetRepositoryImpl(session=session)
    cost_service = DepartmentCostAdapter(
        department_repo=department_repo,
        budget_repo=budget_repo,
    )
    return BillingService(
        department_repo=department_repo,
        budget_repo=budget_repo,
        cost_service=cost_service,
    )
