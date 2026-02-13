"""审计中间件单元测试。"""

import pytest

from src.modules.audit.api.middleware.audit_middleware import _should_exclude


@pytest.mark.unit
class TestAuditMiddlewareExclusion:
    """验证中间件路径排除逻辑。"""

    def test_exclude_health_endpoint(self) -> None:
        """排除 /health 端点。"""
        assert _should_exclude("/health") is True

    def test_exclude_health_ready_endpoint(self) -> None:
        """排除 /health/ready 端点。"""
        assert _should_exclude("/health/ready") is True

    def test_exclude_docs_endpoint(self) -> None:
        """排除 /docs 端点。"""
        assert _should_exclude("/docs") is True

    def test_exclude_redoc_endpoint(self) -> None:
        """排除 /redoc 端点。"""
        assert _should_exclude("/redoc") is True

    def test_exclude_openapi_endpoint(self) -> None:
        """排除 /openapi.json 端点。"""
        assert _should_exclude("/openapi.json") is True

    def test_include_api_endpoint(self) -> None:
        """不排除 API 业务端点。"""
        assert _should_exclude("/api/v1/agents") is False

    def test_include_audit_endpoint(self) -> None:
        """不排除审计端点。"""
        assert _should_exclude("/api/v1/audit-logs") is False

    def test_include_auth_endpoint(self) -> None:
        """不排除认证端点。"""
        assert _should_exclude("/api/v1/auth/login") is False
