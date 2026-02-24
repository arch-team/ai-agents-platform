"""Billing 模块测试配置。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.modules.billing.application.services.billing_service import BillingService
from src.modules.billing.domain.entities.budget import Budget
from src.modules.billing.domain.repositories.budget_repository import IBudgetRepository
from src.modules.billing.domain.repositories.department_repository import IDepartmentRepository
from src.shared.domain.entities.department import Department


@pytest.fixture
def mock_department_repo() -> AsyncMock:
    """Mock Department Repository。"""
    return AsyncMock(spec=IDepartmentRepository)


@pytest.fixture
def mock_budget_repo() -> AsyncMock:
    """Mock Budget Repository。"""
    return AsyncMock(spec=IBudgetRepository)


@pytest.fixture
def billing_service(mock_department_repo: AsyncMock, mock_budget_repo: AsyncMock) -> BillingService:
    """BillingService 实例（注入 Mock Repo）。"""
    return BillingService(
        department_repo=mock_department_repo,
        budget_repo=mock_budget_repo,
    )


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    """Mock event_bus，避免事件副作用。"""
    with patch("src.modules.billing.application.services.billing_service.event_bus") as mock:
        mock.publish_async = AsyncMock()
        yield mock


def make_department(
    *,
    dept_id: int = 1,
    name: str = "工程部",
    code: str = "engineering",
    description: str = "工程研发部门",
    is_active: bool = True,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Department:
    """Factory: 创建 Department 实体。"""
    now = datetime.now(UTC)
    return Department(
        id=dept_id,
        name=name,
        code=code,
        description=description,
        is_active=is_active,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


def make_budget(
    *,
    budget_id: int = 1,
    department_id: int = 1,
    year: int = 2024,
    month: int = 2,
    budget_amount: float = 10000.0,
    used_amount: float = 0.0,
    alert_threshold: float = 0.8,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Budget:
    """Factory: 创建 Budget 实体。"""
    now = datetime.now(UTC)
    return Budget(
        id=budget_id,
        department_id=department_id,
        year=year,
        month=month,
        budget_amount=budget_amount,
        used_amount=used_amount,
        alert_threshold=alert_threshold,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )
