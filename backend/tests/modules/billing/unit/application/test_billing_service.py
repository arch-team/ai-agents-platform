"""BillingService 测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.billing.application.dto.budget_dto import CreateBudgetDTO, UpdateBudgetDTO
from src.modules.billing.application.dto.department_dto import CreateDepartmentDTO, UpdateDepartmentDTO
from src.modules.billing.application.interfaces.cost_service import DepartmentCostReport
from src.modules.billing.application.services.billing_service import BillingService
from src.modules.billing.domain.exceptions import (
    BudgetNotFoundError,
    DepartmentNotFoundError,
    DuplicateDepartmentCodeError,
)
from src.shared.domain.exceptions import AuthorizationError
from src.shared.domain.value_objects.role import Role
from tests.modules.billing.conftest import make_budget, make_department


@pytest.mark.unit
@pytest.mark.asyncio
class TestDepartmentCRUD:
    """Department CRUD 测试。"""

    async def test_create_department_as_admin_succeeds(
        self,
        billing_service: BillingService,
        mock_department_repo: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """测试：ADMIN 创建部门成功。"""
        dto = CreateDepartmentDTO(name="工程部", code="engineering", description="研发部门")
        dept = make_department()
        mock_department_repo.get_by_code.return_value = None
        mock_department_repo.create.return_value = dept

        result = await billing_service.create_department(dto, Role.ADMIN.value)

        assert result.name == "工程部"
        mock_department_repo.get_by_code.assert_called_once_with("engineering")
        mock_department_repo.create.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    async def test_create_department_with_duplicate_code_raises(
        self,
        billing_service: BillingService,
        mock_department_repo: AsyncMock,
    ) -> None:
        """测试：重复部门编码抛出异常。"""
        dto = CreateDepartmentDTO(name="工程部", code="engineering")
        mock_department_repo.get_by_code.return_value = make_department()

        with pytest.raises(DuplicateDepartmentCodeError):
            await billing_service.create_department(dto, Role.ADMIN.value)

    async def test_create_department_as_developer_raises(
        self,
        billing_service: BillingService,
    ) -> None:
        """测试：非 ADMIN 创建部门抛出权限异常。"""
        dto = CreateDepartmentDTO(name="工程部", code="engineering")

        with pytest.raises(AuthorizationError):
            await billing_service.create_department(dto, Role.DEVELOPER.value)

    async def test_get_department_succeeds(
        self,
        billing_service: BillingService,
        mock_department_repo: AsyncMock,
    ) -> None:
        """测试：获取部门详情成功。"""
        dept = make_department()
        mock_department_repo.get_by_id.return_value = dept

        result = await billing_service.get_department(1)

        assert result.id == 1
        assert result.name == "工程部"
        mock_department_repo.get_by_id.assert_called_once_with(1)

    async def test_get_department_not_found_raises(
        self,
        billing_service: BillingService,
        mock_department_repo: AsyncMock,
    ) -> None:
        """测试：部门不存在抛出异常。"""
        mock_department_repo.get_by_id.return_value = None

        with pytest.raises(DepartmentNotFoundError):
            await billing_service.get_department(999)

    async def test_list_departments_returns_paged_result(
        self,
        billing_service: BillingService,
        mock_department_repo: AsyncMock,
    ) -> None:
        """测试：列出部门返回分页结果。"""
        depts = [make_department(dept_id=1), make_department(dept_id=2)]
        mock_department_repo.list_all.return_value = (depts, 2)

        result = await billing_service.list_departments(page=1, page_size=20)

        assert len(result.items) == 2
        assert result.total == 2
        assert result.page == 1
        mock_department_repo.list_all.assert_called_once_with(offset=0, limit=20)

    async def test_update_department_as_admin_succeeds(
        self,
        billing_service: BillingService,
        mock_department_repo: AsyncMock,
    ) -> None:
        """测试：ADMIN 更新部门成功。"""
        dept = make_department()
        mock_department_repo.get_by_id.return_value = dept
        mock_department_repo.update.return_value = dept

        dto = UpdateDepartmentDTO(name="新名称", description="新描述")
        result = await billing_service.update_department(1, dto, Role.ADMIN.value)

        assert result.name == "新名称"
        mock_department_repo.update.assert_called_once()

    async def test_update_department_as_developer_raises(
        self,
        billing_service: BillingService,
    ) -> None:
        """测试：非 ADMIN 更新部门抛出权限异常。"""
        dto = UpdateDepartmentDTO(name="新名称")

        with pytest.raises(AuthorizationError):
            await billing_service.update_department(1, dto, Role.DEVELOPER.value)

    async def test_delete_department_as_admin_succeeds(
        self,
        billing_service: BillingService,
        mock_department_repo: AsyncMock,
    ) -> None:
        """测试：ADMIN 删除部门成功。"""
        dept = make_department()
        mock_department_repo.get_by_id.return_value = dept

        await billing_service.delete_department(1, Role.ADMIN.value)

        mock_department_repo.delete.assert_called_once_with(1)


@pytest.mark.unit
@pytest.mark.asyncio
class TestBudgetCRUD:
    """Budget CRUD 测试。"""

    async def test_create_budget_as_admin_succeeds(
        self,
        billing_service: BillingService,
        mock_department_repo: AsyncMock,
        mock_budget_repo: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """测试：ADMIN 创建预算成功。"""
        dept = make_department()
        budget = make_budget()
        mock_department_repo.get_by_id.return_value = dept
        mock_budget_repo.create.return_value = budget

        dto = CreateBudgetDTO(department_id=1, year=2024, month=2, budget_amount=10000.0)
        result = await billing_service.create_budget(dto, Role.ADMIN.value)

        assert result.department_id == 1
        assert result.budget_amount == 10000.0
        mock_budget_repo.create.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    async def test_create_budget_with_invalid_department_raises(
        self,
        billing_service: BillingService,
        mock_department_repo: AsyncMock,
    ) -> None:
        """测试：部门不存在时抛出异常。"""
        mock_department_repo.get_by_id.return_value = None

        dto = CreateBudgetDTO(department_id=999, year=2024, month=2, budget_amount=10000.0)
        with pytest.raises(DepartmentNotFoundError):
            await billing_service.create_budget(dto, Role.ADMIN.value)

    async def test_get_budget_succeeds(
        self,
        billing_service: BillingService,
        mock_budget_repo: AsyncMock,
    ) -> None:
        """测试：获取预算详情成功。"""
        budget = make_budget()
        mock_budget_repo.get_by_id.return_value = budget

        result = await billing_service.get_budget(1)

        assert result.id == 1
        assert result.budget_amount == 10000.0
        mock_budget_repo.get_by_id.assert_called_once_with(1)

    async def test_get_current_budget_succeeds(
        self,
        billing_service: BillingService,
        mock_budget_repo: AsyncMock,
    ) -> None:
        """测试：获取当前月预算成功。"""
        budget = make_budget()
        mock_budget_repo.get_by_department_month.return_value = budget

        result = await billing_service.get_current_budget(1, 2024, 2)

        assert result.year == 2024
        assert result.month == 2
        mock_budget_repo.get_by_department_month.assert_called_once_with(1, 2024, 2)

    async def test_get_current_budget_not_found_raises(
        self,
        billing_service: BillingService,
        mock_budget_repo: AsyncMock,
    ) -> None:
        """测试：预算不存在抛出异常。"""
        mock_budget_repo.get_by_department_month.return_value = None

        with pytest.raises(BudgetNotFoundError):
            await billing_service.get_current_budget(1, 2024, 2)

    async def test_list_budgets_by_department_returns_paged_result(
        self,
        billing_service: BillingService,
        mock_budget_repo: AsyncMock,
    ) -> None:
        """测试：列出部门预算返回分页结果。"""
        budgets = [make_budget(budget_id=1), make_budget(budget_id=2)]
        mock_budget_repo.list_by_department.return_value = (budgets, 2)

        result = await billing_service.list_budgets_by_department(1, page=1, page_size=20)

        assert len(result.items) == 2
        assert result.total == 2
        mock_budget_repo.list_by_department.assert_called_once_with(1, offset=0, limit=20)

    async def test_update_budget_as_admin_succeeds(
        self,
        billing_service: BillingService,
        mock_budget_repo: AsyncMock,
    ) -> None:
        """测试：ADMIN 更新预算成功。"""
        budget = make_budget()
        mock_budget_repo.get_by_id.return_value = budget
        mock_budget_repo.update.return_value = budget

        dto = UpdateBudgetDTO(budget_amount=20000.0)
        result = await billing_service.update_budget(1, dto, Role.ADMIN.value)

        assert result.budget_amount == 20000.0
        mock_budget_repo.update.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestDepartmentCostReport:
    """Department Cost Report 测试。"""

    async def test_get_department_cost_report_returns_report(
        self,
        billing_service_with_cost: BillingService,
        mock_cost_service: AsyncMock,
    ) -> None:
        """测试：获取部门成本报告成功。"""
        mock_report = DepartmentCostReport(
            department_id=1,
            department_code="engineering",
            department_name="工程部",
            total_cost=1234.56,
            budget_amount=10000.0,
            used_percentage=12.35,
            daily_costs=(),
            start_date="2024-01-01",
            end_date="2024-01-31",
            currency="USD",
        )
        mock_cost_service.get_department_cost_report.return_value = mock_report

        result = await billing_service_with_cost.get_department_cost_report(1, "2024-01-01", "2024-01-31")

        assert result.department_id == 1
        assert result.total_cost == 1234.56
        mock_cost_service.get_department_cost_report.assert_called_once_with(1, "2024-01-01", "2024-01-31")

    async def test_get_department_cost_report_raises_when_cost_service_not_injected(
        self,
        billing_service: BillingService,
    ) -> None:
        """测试：未注入 cost_service 时抛出异常。"""
        with pytest.raises(ValueError, match="IDepartmentCostService 未注入"):
            await billing_service.get_department_cost_report(1, "2024-01-01", "2024-01-31")

    async def test_get_department_cost_report_raises_when_department_not_found(
        self,
        billing_service_with_cost: BillingService,
        mock_cost_service: AsyncMock,
    ) -> None:
        """测试：部门不存在时抛出 DepartmentNotFoundError。"""
        mock_cost_service.get_department_cost_report.side_effect = DepartmentNotFoundError(department_id=999)

        with pytest.raises(DepartmentNotFoundError):
            await billing_service_with_cost.get_department_cost_report(999, "2024-01-01", "2024-01-31")
