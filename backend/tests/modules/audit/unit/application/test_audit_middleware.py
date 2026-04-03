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

    def test_exclude_docs_subpath(self) -> None:
        """排除 /docs 子路径（前缀匹配）。"""
        assert _should_exclude("/docs/oauth2-redirect") is True

    def test_exclude_redoc_subpath(self) -> None:
        """排除 /redoc 子路径（前缀匹配）。"""
        assert _should_exclude("/redoc/something") is True


@pytest.mark.unit
class TestExtractActorId:
    """_extract_actor_id 测试。"""

    def test_extracts_from_state(self) -> None:
        """从 request.state 中提取 audit_user_id。"""
        from unittest.mock import MagicMock

        from src.modules.audit.api.middleware.audit_middleware import _extract_actor_id

        request = MagicMock()
        request.state.audit_user_id = 42
        assert _extract_actor_id(request) == 42

    def test_returns_none_when_not_set(self) -> None:
        """request.state 无 audit_user_id 时返回 None。"""
        from unittest.mock import MagicMock

        from src.modules.audit.api.middleware.audit_middleware import _extract_actor_id

        request = MagicMock(spec=["state"])
        request.state = MagicMock(spec=[])
        assert _extract_actor_id(request) is None


@pytest.mark.unit
class TestAuditMiddlewareAsgi:
    """AuditMiddleware ASGI 行为测试。"""

    @pytest.mark.anyio
    async def test_non_http_scope_passes_through(self) -> None:
        """非 HTTP scope 直接透传。"""
        from unittest.mock import AsyncMock

        from src.modules.audit.api.middleware.audit_middleware import AuditMiddleware

        mock_app = AsyncMock()
        middleware = AuditMiddleware(mock_app)

        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        mock_app.assert_awaited_once_with(scope, receive, send)

    @pytest.mark.anyio
    async def test_excluded_path_passes_through(self) -> None:
        """排除路径直接透传，不记录审计。"""
        from unittest.mock import AsyncMock

        from src.modules.audit.api.middleware.audit_middleware import AuditMiddleware

        mock_app = AsyncMock()
        middleware = AuditMiddleware(mock_app)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("localhost", 8000),
        }
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        mock_app.assert_awaited_once()

    @pytest.mark.anyio
    async def test_api_path_calls_app_with_send_wrapper(self) -> None:
        """API 路径调用 app 时使用 send_wrapper 包装。"""
        from unittest.mock import AsyncMock, patch

        from src.modules.audit.api.middleware.audit_middleware import AuditMiddleware

        mock_app = AsyncMock()
        middleware = AuditMiddleware(mock_app)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/agents",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("localhost", 8000),
        }
        receive = AsyncMock()
        send = AsyncMock()

        with patch.object(middleware, "_record_audit", new_callable=AsyncMock):
            await middleware(scope, receive, send)

        # app 应被调用（参数为 scope, receive, send_wrapper）
        mock_app.assert_awaited_once()
