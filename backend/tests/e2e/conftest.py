"""E2E 测试配置 — 针对运行中的服务器执行真实 HTTP 请求。"""

import os

import httpx
import pytest


BASE_URL = os.getenv(
    "E2E_BASE_URL",
    "http://ai-agents-dev-546356512.us-east-1.elb.amazonaws.com",
)
ADMIN_EMAIL = os.getenv("E2E_ADMIN_EMAIL", "admin@company.com")
ADMIN_PASSWORD = os.getenv("E2E_ADMIN_PASSWORD", "Admin@2026!")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def http() -> httpx.Client:
    """共享的 HTTP 客户端，带超时和 base_url。"""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def admin_token(http: httpx.Client) -> str:
    """Admin JWT token — 整个测试会话复用。"""
    resp = http.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"Admin 登录失败: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token: str) -> dict[str, str]:
    """带 Bearer token 的请求头。"""
    return {"Authorization": f"Bearer {admin_token}"}
