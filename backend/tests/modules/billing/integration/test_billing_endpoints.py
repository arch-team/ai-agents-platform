"""Billing API 端点集成测试。"""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.billing.api.dependencies import get_billing_service
from src.modules.billing.application.dto.budget_dto import BudgetDTO
from src.modules.billing.application.dto.department_dto import DepartmentDTO
from src.modules.billing.application.interfaces.cost_service import DepartmentCostPoint, DepartmentCostReport
from src.modules.billing.domain.exceptions import DepartmentNotFoundError
from src.presentation.api.main import create_app
from src.shared.application.dtos import PagedResult


def _make_user(role: str = "developer", user_id: int = 1) -> UserDTO:
    return UserDTO(id=user_id, email="test@example.com", name="Test", role=role, is_active=True)


def _make_department_dto(dept_id: int = 1) -> DepartmentDTO:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    return DepartmentDTO(
        id=dept_id,
        name="工程部",
        code="engineering",
        description="研发部门",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _make_budget_dto(budget_id: int = 1) -> BudgetDTO:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    return BudgetDTO(
        id=budget_id,
        department_id=1,
        year=2024,
        month=2,
        budget_amount=10000.0,
        used_amount=500.0,
        alert_threshold=0.8,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_service() -> AsyncMock:
    """Mock BillingService。"""
    return AsyncMock()


@pytest.fixture
def client(mock_service: AsyncMock) -> TestClient:
    """普通用户 TestClient。"""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    app.dependency_overrides[get_billing_service] = lambda: mock_service
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(mock_service: AsyncMock) -> TestClient:
    """Admin 用户 TestClient。"""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _make_user(role="admin")
    app.dependency_overrides[get_billing_service] = lambda: mock_service
    yield TestClient(app)
    app.dependency_overrides.clear()


# ── Department 端点 ──


@pytest.mark.integration
class TestDepartmentEndpoints:
    """Department API 端点测试。"""

    def test_create_department_as_admin_returns_201(self, admin_client: TestClient, mock_service: AsyncMock) -> None:
        """测试：ADMIN 创建部门返回 201。"""
        mock_service.create_department.return_value = _make_department_dto()

        resp = admin_client.post(
            "/api/v1/billing/departments",
            json={
                "name": "工程部",
                "code": "engineering",
                "description": "研发部门",
            },
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "工程部"
        assert data["code"] == "engineering"

    def test_list_departments_returns_200(self, client: TestClient, mock_service: AsyncMock) -> None:
        """测试：列出部门返回 200。"""
        mock_service.list_departments.return_value = PagedResult(
            items=[_make_department_dto()],
            total=1,
            page=1,
            page_size=20,
        )

        resp = client.get("/api/v1/billing/departments")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_get_department_returns_200(self, client: TestClient, mock_service: AsyncMock) -> None:
        """测试：获取部门详情返回 200。"""
        mock_service.get_department.return_value = _make_department_dto()

        resp = client.get("/api/v1/billing/departments/1")

        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_get_department_not_found_returns_404(self, client: TestClient, mock_service: AsyncMock) -> None:
        """测试：部门不存在返回 404。"""
        mock_service.get_department.side_effect = DepartmentNotFoundError(department_id=999)

        resp = client.get("/api/v1/billing/departments/999")

        assert resp.status_code == 404

    def test_update_department_as_admin_returns_200(self, admin_client: TestClient, mock_service: AsyncMock) -> None:
        """测试：ADMIN 更新部门返回 200。"""
        mock_service.update_department.return_value = _make_department_dto()

        resp = admin_client.put("/api/v1/billing/departments/1", json={"name": "新名称"})

        assert resp.status_code == 200

    def test_delete_department_as_admin_returns_204(self, admin_client: TestClient, mock_service: AsyncMock) -> None:
        """测试：ADMIN 删除部门返回 204。"""
        mock_service.delete_department.return_value = None

        resp = admin_client.delete("/api/v1/billing/departments/1")

        assert resp.status_code == 204


# ── Budget 端点 ──


@pytest.mark.integration
class TestBudgetEndpoints:
    """Budget API 端点测试。"""

    def test_create_budget_as_admin_returns_201(self, admin_client: TestClient, mock_service: AsyncMock) -> None:
        """测试：ADMIN 创建预算返回 201。"""
        mock_service.create_budget.return_value = _make_budget_dto()

        resp = admin_client.post(
            "/api/v1/billing/budgets",
            json={
                "department_id": 1,
                "year": 2024,
                "month": 2,
                "budget_amount": 10000.0,
            },
        )

        assert resp.status_code == 201
        assert resp.json()["budget_amount"] == 10000.0

    def test_list_budgets_returns_200(self, client: TestClient, mock_service: AsyncMock) -> None:
        """测试：列出预算返回 200。"""
        mock_service.list_budgets_by_department.return_value = PagedResult(
            items=[_make_budget_dto()],
            total=1,
            page=1,
            page_size=20,
        )

        resp = client.get("/api/v1/billing/budgets?department_id=1")

        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_get_current_budget_returns_200(self, client: TestClient, mock_service: AsyncMock) -> None:
        """测试：获取当前月预算返回 200。"""
        mock_service.get_current_budget.return_value = _make_budget_dto()

        resp = client.get("/api/v1/billing/departments/1/budgets/current?year=2024&month=2")

        assert resp.status_code == 200
        assert resp.json()["year"] == 2024

    def test_update_budget_as_admin_returns_200(self, admin_client: TestClient, mock_service: AsyncMock) -> None:
        """测试：ADMIN 更新预算返回 200。"""
        mock_service.update_budget.return_value = _make_budget_dto()

        resp = admin_client.put("/api/v1/billing/budgets/1", json={"budget_amount": 20000.0})

        assert resp.status_code == 200


# ── Cost Report 端点 ──


@pytest.mark.integration
class TestCostReportEndpoints:
    """Cost Report API 端点测试。"""

    def test_get_cost_report_returns_200(self, client: TestClient, mock_service: AsyncMock) -> None:
        """测试：获取成本报告返回 200。"""
        mock_service.get_department_cost_report.return_value = DepartmentCostReport(
            department_id=1,
            department_code="engineering",
            department_name="工程部",
            total_cost=123.45,
            budget_amount=10000.0,
            used_percentage=1.23,
            daily_costs=(
                DepartmentCostPoint(date="2024-01-01", department_code="engineering", amount=60.0),
                DepartmentCostPoint(date="2024-01-02", department_code="engineering", amount=63.45),
            ),
            start_date="2024-01-01",
            end_date="2024-01-03",
            currency="USD",
        )

        resp = client.get("/api/v1/billing/departments/1/cost-report?start_date=2024-01-01&end_date=2024-01-03")

        assert resp.status_code == 200
        data = resp.json()
        assert data["department_id"] == 1
        assert data["total_cost"] == 123.45
        assert data["used_percentage"] == 1.23
        assert len(data["daily_costs"]) == 2
        assert data["daily_costs"][0]["date"] == "2024-01-01"
        assert data["currency"] == "USD"

    def test_get_cost_report_department_not_found_returns_404(
        self,
        client: TestClient,
        mock_service: AsyncMock,
    ) -> None:
        """测试：部门不存在时返回 404。"""
        mock_service.get_department_cost_report.side_effect = DepartmentNotFoundError(department_id=999)

        resp = client.get("/api/v1/billing/departments/999/cost-report?start_date=2024-01-01&end_date=2024-01-31")

        assert resp.status_code == 404

    def test_get_cost_report_invalid_date_format_returns_422(self, client: TestClient) -> None:
        """测试：日期格式错误时返回 422。"""
        resp = client.get("/api/v1/billing/departments/1/cost-report?start_date=invalid&end_date=2024-01-31")

        assert resp.status_code == 422
