"""E2E: 认证流程 — 登录、当前用户、Token 刷新、注册。

注意: 登录端点有频率限制 (5 次失败/30 分钟)，测试需最小化登录调用。
"""

import httpx
import pytest


pytestmark = pytest.mark.e2e

# 测试用一次性用户
_TEST_USER = {
    "email": "e2e-test-runner@example.com",
    "password": "E2eTest@2026!",
    "name": "E2E 测试用户",
}


class TestAuthLogin:
    """登录端点验证。"""

    def test_login_success(self, http: httpx.Client, admin_token: str) -> None:
        """复用 conftest 中的 admin_token，验证 token 非空即可。"""
        assert len(admin_token) > 0

    def test_login_wrong_password(self, http: httpx.Client) -> None:
        resp = http.post(
            "/api/v1/auth/login",
            json={"email": "admin@company.com", "password": "WrongPassword!"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, http: httpx.Client) -> None:
        resp = http.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "Whatever@123"},
        )
        assert resp.status_code == 401


class TestAuthMe:
    """当前用户端点验证。"""

    def test_me_with_token(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/auth/me", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "admin@company.com"
        assert body["role"] == "admin"

    def test_me_without_token(self, http: httpx.Client) -> None:
        resp = http.get("/api/v1/auth/me")
        assert resp.status_code == 401


class TestAuthRegister:
    """注册新用户。"""

    def test_register_new_user(self, http: httpx.Client) -> None:
        resp = http.post("/api/v1/auth/register", json=_TEST_USER)
        # 201 = 新建成功, 409 = 已存在（幂等）
        assert resp.status_code in (201, 409)

    def test_register_duplicate_email(self, http: httpx.Client) -> None:
        """重复注册相同邮箱返回 409。"""
        # 先确保用户存在
        http.post("/api/v1/auth/register", json=_TEST_USER)
        # 再次注册
        resp = http.post("/api/v1/auth/register", json=_TEST_USER)
        assert resp.status_code == 409
