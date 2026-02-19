"""E2E: 健康检查端点。"""

import httpx
import pytest


pytestmark = pytest.mark.e2e


class TestHealthEndpoints:
    """验证服务存活和就绪状态。"""

    def test_liveness(self, http: httpx.Client) -> None:
        resp = http.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_readiness(self, http: httpx.Client) -> None:
        resp = http.get("/health/ready")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["checks"]["database"] == "ok"

    def test_openapi_spec(self, http: httpx.Client) -> None:
        resp = http.get("/openapi.json")
        assert resp.status_code == 200
        spec = resp.json()
        assert spec["info"]["title"] == "AI Agents Platform"
