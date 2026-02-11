"""Rate Limiting 中间件集成测试。"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from src.shared.api.middleware.rate_limit import _custom_rate_limit_handler


def _create_test_app() -> FastAPI:
    """创建带独立 Limiter 的测试应用（避免测试间状态共享）。"""
    test_limiter = Limiter(key_func=get_remote_address)
    app = FastAPI()

    @app.get("/test-endpoint")
    async def _test_endpoint() -> dict[str, str]:
        return {"message": "ok"}

    @app.post("/api/v1/auth/login")
    @test_limiter.limit("5/minute")
    async def _login(request: Request) -> dict[str, str]:
        return {"message": "login"}

    @app.post("/api/v1/auth/register")
    @test_limiter.limit("3/hour")
    async def _register(request: Request) -> dict[str, str]:
        return {"message": "register"}

    app.state.limiter = test_limiter
    app.add_exception_handler(RateLimitExceeded, _custom_rate_limit_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)
    return app


@pytest.mark.integration
class TestRateLimitingSetup:
    """Rate Limiting 注册和全局异常处理测试。"""

    def test_normal_request_succeeds(self) -> None:
        """正常请求应返回 200。"""
        app = _create_test_app()
        client = TestClient(app)
        response = client.get("/test-endpoint")
        assert response.status_code == 200

    def test_login_endpoint_allows_requests_within_limit(self) -> None:
        """登录端点在限制内应允许请求（5 次/分钟）。"""
        app = _create_test_app()
        client = TestClient(app)
        for i in range(5):
            response = client.post("/api/v1/auth/login")
            assert response.status_code == 200, f"第 {i + 1} 次请求失败: {response.status_code}"

    def test_login_endpoint_rate_limited_after_exceed(self) -> None:
        """登录端点超出 5 次/分钟限制后应返回 429。"""
        app = _create_test_app()
        client = TestClient(app)
        responses = []
        for _ in range(8):
            response = client.post("/api/v1/auth/login")
            responses.append(response.status_code)

        # 前 5 次应成功，后续应被限流
        assert responses[:5] == [200] * 5
        assert 429 in responses[5:]

    def test_rate_limit_response_format(self) -> None:
        """Rate Limit 错误响应应符合标准 ErrorResponse 格式。"""
        app = _create_test_app()
        client = TestClient(app)
        # 先耗尽限额
        for _ in range(5):
            client.post("/api/v1/auth/login")

        # 第 6 次应被限流
        response = client.post("/api/v1/auth/login")
        assert response.status_code == 429
        data = response.json()
        assert data["code"] == "RATE_LIMIT_EXCEEDED"
        assert "请求频率超限" in data["message"]

    def test_register_endpoint_stricter_limit(self) -> None:
        """注册端点应有更严格的限制（3 次/小时）。"""
        app = _create_test_app()
        client = TestClient(app)
        responses = []
        for _ in range(5):
            response = client.post("/api/v1/auth/register")
            responses.append(response.status_code)

        # 前 3 次应成功
        assert responses[:3] == [200] * 3
        # 第 4+ 次应被限流
        assert 429 in responses[3:]
