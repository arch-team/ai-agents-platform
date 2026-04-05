"""E2E: Agent Blueprint 生命周期 — start-testing → go-live → take-offline。

覆盖 M17 Blueprint 三个生命周期端点及其边界条件:
- DRAFT → TESTING (start-testing): workspace 上传 + Runtime 创建
- TESTING → ACTIVE (go-live): 复用同一 Runtime
- ACTIVE → ARCHIVED (take-offline): Runtime 销毁

同时覆盖 V1 兼容路径 (DRAFT → ACTIVE → ARCHIVED) 和错误边界。

注意: 当前 Dev 环境 Builder 采用 SOP 引导式设计，无法单轮生成 blueprint，
因此 Blueprint 完整生命周期测试改为通过 V1 API 创建 Agent 后测试端点错误响应。
"""

import time

import httpx
import pytest

from tests.e2e.conftest import ResourceTracker


pytestmark = pytest.mark.e2e

# 时间戳后缀，确保 Agent 名称在 Dev 环境唯一
_UNIQUE_SUFFIX = str(int(time.time()))


class TestBlueprintFullLifecycle:
    """Blueprint 生命周期: 用 V1 API 创建 Agent，测试 start-testing 端点的错误响应。

    当前 Dev 环境 Builder V2 采用 SOP 引导式设计，无法单轮生成 blueprint，
    因此无法通过 Builder 创建带 Blueprint 的 Agent。
    改为验证 V1 Agent（无 Blueprint）调用 start-testing 时返回正确错误。
    """

    _agent_id: int = 0

    def test_01_create_v1_agent(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
        resource_tracker: ResourceTracker,
    ) -> None:
        """通过 V1 API 创建 DRAFT Agent（无 Blueprint）。"""
        resp = http.post(
            "/api/v1/agents",
            json={
                "name": f"E2E-Blueprint-生命周期-{_UNIQUE_SUFFIX}",
                "description": "用于 Blueprint 生命周期端点测试",
                "system_prompt": "你是一个测试 Agent",
                "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201, f"创建 Agent 失败: {resp.text}"
        agent_id = resp.json()["id"]
        TestBlueprintFullLifecycle._agent_id = agent_id
        resource_tracker.track("agent", agent_id)

        # 验证初始状态
        assert resp.json()["status"] == "draft"

    def test_02_start_testing_without_blueprint(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """V1 Agent (无 Blueprint) 调用 start-testing 应返回错误。"""
        resp = http.post(
            f"/api/v1/agents/{self._agent_id}/start-testing",
            headers=admin_headers,
        )
        # 无 Blueprint 时期望 400/404/409
        assert resp.status_code in (400, 404, 409), f"意外状态码: {resp.status_code}, body: {resp.text}"

    def test_03_go_live_from_draft_rejected(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """DRAFT Agent 直接 go-live 应被拒绝 (必须先 start-testing)。"""
        resp = http.post(
            f"/api/v1/agents/{self._agent_id}/go-live",
            headers=admin_headers,
        )
        assert resp.status_code == 409

    def test_04_take_offline_from_draft_rejected(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """DRAFT Agent 直接 take-offline 应被拒绝。"""
        resp = http.post(
            f"/api/v1/agents/{self._agent_id}/take-offline",
            headers=admin_headers,
        )
        assert resp.status_code == 409


class TestBlueprintErrorBoundary:
    """Blueprint 生命周期的错误边界测试。"""

    def test_start_testing_without_blueprint(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
        resource_tracker: ResourceTracker,
    ) -> None:
        """V1 Agent (无 Blueprint) 调用 start-testing 应返回错误。"""
        # 通过传统 API 创建 V1 Agent (无 Blueprint)
        resp = http.post(
            "/api/v1/agents",
            json={
                "name": f"E2E-V1-无Blueprint-{_UNIQUE_SUFFIX}",
                "description": "用于测试 start-testing 边界",
                "system_prompt": "你是一个测试 Agent",
                "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        v1_agent_id = resp.json()["id"]
        resource_tracker.track("agent", v1_agent_id)

        # V1 Agent 没有 Blueprint，start-testing 应失败
        resp = http.post(
            f"/api/v1/agents/{v1_agent_id}/start-testing",
            headers=admin_headers,
        )
        # 期望 400 (参数错误) / 404 (Blueprint 不存在) / 409 (状态不允许)
        assert resp.status_code in (400, 404, 409), f"意外状态码: {resp.status_code}"

    def test_nonexistent_agent(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """不存在的 Agent ID 返回 404。"""
        fake_id = 999999
        for endpoint in ["start-testing", "go-live", "take-offline"]:
            resp = http.post(
                f"/api/v1/agents/{fake_id}/{endpoint}",
                headers=admin_headers,
            )
            assert resp.status_code == 404, f"{endpoint} 对不存在的 Agent 应返回 404"


class TestV1CompatibilityPath:
    """V1 兼容路径: DRAFT → ACTIVE → ARCHIVED (传统 activate/archive)。"""

    def test_v1_activate_and_archive(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
        resource_tracker: ResourceTracker,
    ) -> None:
        """V1 Agent 仍可通过传统 activate/archive 端点操作。"""
        # 创建 V1 Agent（名称加时间戳避免冲突）
        resp = http.post(
            "/api/v1/agents",
            json={
                "name": f"E2E-V1-兼容测试-{_UNIQUE_SUFFIX}",
                "description": "验证 V1 路径仍然可用",
                "system_prompt": "你是一个测试 Agent",
                "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        agent_id = resp.json()["id"]
        resource_tracker.track("agent", agent_id)

        # V1 activate: DRAFT → ACTIVE
        resp = http.post(f"/api/v1/agents/{agent_id}/activate", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

        # V1 archive: ACTIVE → ARCHIVED
        resp = http.post(f"/api/v1/agents/{agent_id}/archive", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"
