"""DepartmentCostAdapter 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.billing.application.interfaces.cost_service import DepartmentCostPoint, DepartmentCostReport
from src.modules.billing.domain.exceptions import BudgetNotFoundError, DepartmentNotFoundError
from src.modules.billing.infrastructure.external.department_cost_adapter import DepartmentCostAdapter
from tests.modules.billing.conftest import make_budget, make_department


_PATCH_TARGET = "src.modules.billing.infrastructure.external.department_cost_adapter._get_ce_client"


def _make_ce_response(department_code: str = "engineering") -> dict:
    """构造 Cost Explorer API 标准响应。"""
    return {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2024-01-01", "End": "2024-01-02"},
                "Groups": [
                    {
                        "Keys": [department_code],
                        "Metrics": {"UnblendedCost": {"Amount": "5.25", "Unit": "USD"}},
                    },
                ],
            },
            {
                "TimePeriod": {"Start": "2024-01-02", "End": "2024-01-03"},
                "Groups": [
                    {
                        "Keys": [department_code],
                        "Metrics": {"UnblendedCost": {"Amount": "3.75", "Unit": "USD"}},
                    },
                ],
            },
        ],
    }


@pytest.mark.unit
@pytest.mark.asyncio
class TestDepartmentCostAdapter:
    """DepartmentCostAdapter 测试。"""

    async def test_get_department_cost_report_returns_report(self) -> None:
        """测试：正常响应返回成本报告。"""
        mock_dept_repo = AsyncMock()
        mock_budget_repo = AsyncMock()
        dept = make_department(code="engineering")
        budget = make_budget(budget_amount=10000.0)
        mock_dept_repo.get_by_id.return_value = dept
        mock_budget_repo.get_by_department_month.return_value = budget

        mock_client = MagicMock()
        mock_client.get_cost_and_usage.return_value = _make_ce_response("engineering")

        adapter = DepartmentCostAdapter(department_repo=mock_dept_repo, budget_repo=mock_budget_repo)

        with patch(_PATCH_TARGET, return_value=mock_client):
            result = await adapter.get_department_cost_report(1, "2024-01-01", "2024-01-03")

        assert isinstance(result, DepartmentCostReport)
        assert result.department_id == 1
        assert result.department_code == "engineering"
        assert result.total_cost == round(5.25 + 3.75, 4)
        assert result.budget_amount == 10000.0
        assert result.used_percentage == round(9.0 / 10000.0 * 100, 2)
        assert len(result.daily_costs) == 2
        assert isinstance(result.daily_costs[0], DepartmentCostPoint)
        assert result.daily_costs[0].date == "2024-01-01"
        assert result.daily_costs[0].amount == 5.25

    async def test_get_department_cost_report_empty_response(self) -> None:
        """测试：Cost Explorer 无数据时返回零成本。"""
        mock_dept_repo = AsyncMock()
        mock_budget_repo = AsyncMock()
        mock_dept_repo.get_by_id.return_value = make_department()
        mock_budget_repo.get_by_department_month.return_value = make_budget()

        mock_client = MagicMock()
        mock_client.get_cost_and_usage.return_value = {"ResultsByTime": []}

        adapter = DepartmentCostAdapter(department_repo=mock_dept_repo, budget_repo=mock_budget_repo)

        with patch(_PATCH_TARGET, return_value=mock_client):
            result = await adapter.get_department_cost_report(1, "2024-01-01", "2024-01-31")

        assert result.total_cost == 0.0
        assert result.used_percentage == 0.0
        assert len(result.daily_costs) == 0

    async def test_get_department_cost_report_api_failure_returns_degraded_report(self) -> None:
        """测试：Cost Explorer API 失败时降级返回零成本报告。"""
        mock_dept_repo = AsyncMock()
        mock_budget_repo = AsyncMock()
        mock_dept_repo.get_by_id.return_value = make_department()
        mock_budget_repo.get_by_department_month.return_value = make_budget(budget_amount=5000.0)

        mock_client = MagicMock()
        mock_client.get_cost_and_usage.side_effect = RuntimeError("AWS API error")

        adapter = DepartmentCostAdapter(department_repo=mock_dept_repo, budget_repo=mock_budget_repo)

        with patch(_PATCH_TARGET, return_value=mock_client):
            result = await adapter.get_department_cost_report(1, "2024-01-01", "2024-01-31")

        # 降级: 返回零成本报告, 不抛异常
        assert result.total_cost == 0.0
        assert result.budget_amount == 5000.0
        assert result.used_percentage == 0.0
        assert len(result.daily_costs) == 0

    async def test_get_department_cost_report_department_not_found_raises(self) -> None:
        """测试：部门不存在时抛出 DepartmentNotFoundError。"""
        mock_dept_repo = AsyncMock()
        mock_budget_repo = AsyncMock()
        mock_dept_repo.get_by_id.return_value = None

        adapter = DepartmentCostAdapter(department_repo=mock_dept_repo, budget_repo=mock_budget_repo)

        with pytest.raises(DepartmentNotFoundError):
            await adapter.get_department_cost_report(999, "2024-01-01", "2024-01-31")

    async def test_get_department_cost_report_budget_not_found_raises(self) -> None:
        """测试：预算不存在时抛出 BudgetNotFoundError。"""
        mock_dept_repo = AsyncMock()
        mock_budget_repo = AsyncMock()
        mock_dept_repo.get_by_id.return_value = make_department()
        mock_budget_repo.get_by_department_month.return_value = None

        adapter = DepartmentCostAdapter(department_repo=mock_dept_repo, budget_repo=mock_budget_repo)

        with pytest.raises(BudgetNotFoundError):
            await adapter.get_department_cost_report(1, "2024-01-01", "2024-01-31")

    async def test_get_department_cost_report_verifies_date_parsing(self) -> None:
        """测试：不同月份的日期正确解析年月用于预算查询。"""
        mock_dept_repo = AsyncMock()
        mock_budget_repo = AsyncMock()
        mock_dept_repo.get_by_id.return_value = make_department()
        mock_budget_repo.get_by_department_month.return_value = make_budget()

        mock_client = MagicMock()
        mock_client.get_cost_and_usage.return_value = {"ResultsByTime": []}

        adapter = DepartmentCostAdapter(department_repo=mock_dept_repo, budget_repo=mock_budget_repo)

        with patch(_PATCH_TARGET, return_value=mock_client):
            await adapter.get_department_cost_report(1, "2024-03-15", "2024-03-31")

        # 验证预算查询使用了 start_date 解析出的年月 (2024, 3)
        mock_budget_repo.get_by_department_month.assert_called_once_with(1, 2024, 3)

    async def test_get_department_cost_report_with_zero_budget_returns_zero_percentage(self) -> None:
        """测试：预算金额为零时 used_percentage 为 0（避免除零错误）。"""
        mock_dept_repo = AsyncMock()
        mock_budget_repo = AsyncMock()
        mock_dept_repo.get_by_id.return_value = make_department()
        mock_budget_repo.get_by_department_month.return_value = make_budget(budget_amount=0.0)

        mock_client = MagicMock()
        mock_client.get_cost_and_usage.return_value = _make_ce_response("engineering")

        adapter = DepartmentCostAdapter(department_repo=mock_dept_repo, budget_repo=mock_budget_repo)

        with patch(_PATCH_TARGET, return_value=mock_client):
            result = await adapter.get_department_cost_report(1, "2024-01-01", "2024-01-03")

        assert result.used_percentage == 0.0
