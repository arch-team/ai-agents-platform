"""E2E: 只读端点验证 — 不创建/修改数据，仅验证 API 可用性和响应格式。"""

import httpx
import pytest


pytestmark = pytest.mark.e2e


class TestConversationEndpoints:
    """对话模块只读验证。"""

    def test_list_conversations(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/conversations", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body


class TestInsightsEndpoints:
    """数据洞察模块只读验证。"""

    def test_summary(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get(
            "/api/v1/insights/summary",
            params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_usage_trends(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get(
            "/api/v1/insights/usage-trends",
            params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_cost_breakdown(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get(
            "/api/v1/insights/cost-breakdown",
            params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_usage_summary(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get(
            "/api/v1/insights/usage-summary",
            params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=admin_headers,
        )
        assert resp.status_code == 200


class TestAuditLogEndpoints:
    """审计日志模块只读验证 (Admin 权限)。"""

    def test_list_audit_logs(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/audit-logs", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    def test_audit_stats(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/audit-logs/stats", headers=admin_headers)
        assert resp.status_code == 200


class TestAdminUserEndpoints:
    """Admin 用户管理端点 (新功能)。"""

    def test_list_users(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert body["total"] >= 1

    def test_list_users_without_admin(self, http: httpx.Client) -> None:
        resp = http.get("/api/v1/admin/users")
        assert resp.status_code == 401


class TestTemplateEndpoints:
    """模板模块只读验证。"""

    def test_list_templates(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/templates", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    def test_list_my_templates(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/templates/mine", headers=admin_headers)
        assert resp.status_code == 200


class TestToolCatalogEndpoints:
    """工具目录只读验证。"""

    def test_list_tools(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/tools", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    def test_list_approved_tools(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/tools/approved", headers=admin_headers)
        assert resp.status_code == 200


class TestKnowledgeBaseEndpoints:
    """知识库只读验证。"""

    def test_list_knowledge_bases(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/knowledge-bases", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body


class TestEvaluationEndpoints:
    """Eval 框架只读验证。"""

    def test_list_test_suites(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/test-suites", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    def test_list_evaluation_runs(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/evaluation-runs", headers=admin_headers)
        assert resp.status_code == 200


class TestDashboardEndpoints:
    """Dashboard 摘要。"""

    def test_stats_summary(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/stats/summary", headers=admin_headers)
        assert resp.status_code == 200
