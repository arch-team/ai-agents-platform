"""E2E: Agent Blueprint 生命周期 — start-testing → go-live → take-offline。

覆盖 M17 Blueprint 三个生命周期端点及其边界条件:
- DRAFT → TESTING (start-testing): workspace 上传 + Runtime 创建
- TESTING → ACTIVE (go-live): 复用同一 Runtime
- ACTIVE → ARCHIVED (take-offline): Runtime 销毁

同时覆盖 V1 兼容路径 (DRAFT → ACTIVE → ARCHIVED) 和错误边界。
"""

import time

import httpx
import pytest

from tests.e2e.conftest import BASE_URL, ResourceTracker, collect_sse_events


pytestmark = pytest.mark.e2e

# ── 辅助: 通过 Builder V2 创建带 Blueprint 的 Agent ──


def _create_agent_with_blueprint(
    http: httpx.Client,
    headers: dict[str, str],
    name_hint: str = "Blueprint 测试",
) -> int:
    """通过 Builder V2 流程创建一个 DRAFT Agent (带 Blueprint)。返回 agent_id。"""
    # 1. 创建 Builder 会话
    resp = http.post(
        "/api/v1/builder/sessions",
        json={"prompt": f"{name_hint}: 需要回答技术问题的 Agent"},
        headers=headers,
    )
    assert resp.status_code == 201
    session_id = resp.json()["id"]

    # 2. 生成 Blueprint (SSE)
    events = collect_sse_events(
        base_url=BASE_URL,
        path=f"/api/v1/builder/sessions/{session_id}/generate",
        headers=headers,
        json_body={"prompt": f"{name_hint}: 需要回答技术问题的 Agent"},
        timeout=90.0,
    )
    assert any(e.get("done") for e in events), "Blueprint 生成未完成"

    # 3. 确认创建 (不自动 start-testing)
    resp = http.post(
        f"/api/v1/builder/sessions/{session_id}/confirm",
        json={"auto_start_testing": False},
        headers=headers,
    )
    assert resp.status_code == 200, f"confirm 失败: {resp.text}"
    agent_id: int = resp.json()["created_agent_id"]
    assert agent_id is not None
    return agent_id


class TestBlueprintFullLifecycle:
    """Blueprint 完整生命周期: DRAFT → TESTING → ACTIVE → ARCHIVED。"""

    _agent_id: int = 0

    def test_01_create_agent_with_blueprint(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
        resource_tracker: ResourceTracker,
    ) -> None:
        """通过 Builder V2 创建带 Blueprint 的 Agent。"""
        agent_id = _create_agent_with_blueprint(http, admin_headers, "生命周期测试")
        TestBlueprintFullLifecycle._agent_id = agent_id
        resource_tracker.track("agent", agent_id)

        # 验证初始状态
        resp = http.get(f"/api/v1/agents/{agent_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "draft"

    def test_02_start_testing(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """DRAFT → TESTING: workspace 上传 + Runtime provision。"""
        resp = http.post(
            f"/api/v1/agents/{self._agent_id}/start-testing",
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"start-testing 失败: {resp.text}"
        body = resp.json()
        assert body["status"] == "testing"

    def test_03_start_testing_idempotent_rejected(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """已经 TESTING 的 Agent 不能再次 start-testing (状态冲突)。"""
        resp = http.post(
            f"/api/v1/agents/{self._agent_id}/start-testing",
            headers=admin_headers,
        )
        assert resp.status_code == 409

    def test_04_go_live(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """TESTING → ACTIVE: 复用同一 Runtime 上线。"""
        # 等待 Runtime 就绪 (异步 provision 可能需要时间)
        for _ in range(10):
            resp = http.get(f"/api/v1/agents/{self._agent_id}", headers=admin_headers)
            if resp.status_code == 200 and resp.json()["status"] == "testing":
                break
            time.sleep(3)

        resp = http.post(
            f"/api/v1/agents/{self._agent_id}/go-live",
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"go-live 失败: {resp.text}"
        body = resp.json()
        assert body["status"] == "active"

    def test_05_go_live_idempotent_rejected(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """已经 ACTIVE 的 Agent 不能再次 go-live。"""
        resp = http.post(
            f"/api/v1/agents/{self._agent_id}/go-live",
            headers=admin_headers,
        )
        assert resp.status_code == 409

    def test_06_take_offline(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """ACTIVE → ARCHIVED: Runtime 销毁 + 归档。"""
        resp = http.post(
            f"/api/v1/agents/{self._agent_id}/take-offline",
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"take-offline 失败: {resp.text}"
        body = resp.json()
        assert body["status"] == "archived"

    def test_07_take_offline_archived_rejected(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """已归档 Agent 不能再次 take-offline。"""
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
                "name": "E2E V1 Agent (无 Blueprint)",
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
        # 期望 404 (Blueprint 不存在) 或 409 (状态不允许)
        assert resp.status_code in (404, 409), f"意外状态码: {resp.status_code}"

    def test_go_live_from_draft(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
        resource_tracker: ResourceTracker,
    ) -> None:
        """DRAFT Agent 直接 go-live 应被拒绝 (必须先 start-testing)。"""
        agent_id = _create_agent_with_blueprint(http, admin_headers, "跳过测试")
        resource_tracker.track("agent", agent_id)

        resp = http.post(
            f"/api/v1/agents/{agent_id}/go-live",
            headers=admin_headers,
        )
        assert resp.status_code == 409

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
        # 创建 V1 Agent
        resp = http.post(
            "/api/v1/agents",
            json={
                "name": "E2E V1 兼容测试 Agent",
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
