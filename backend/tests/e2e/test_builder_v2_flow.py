"""E2E: Builder V2 完整流程 — 会话创建 → Blueprint 生成 → 迭代优化 → 确认创建 → 上线。

覆盖 M17 Builder V2 的核心用户旅程:
1. 创建 Builder 会话
2. SSE 流式生成 Blueprint (SOP 引导式)
3. SSE 流式迭代优化 Blueprint (多轮 refine)
4. 确认创建 Agent (含 auto_start_testing)
5. 查询可用工具和 Skill 列表
6. 会话取消流程
"""

import time

import httpx
import pytest

from tests.e2e.conftest import BASE_URL, ResourceTracker, collect_sse_events


pytestmark = pytest.mark.e2e


class TestBuilderV2GenerateFlow:
    """Builder V2 核心流程: 创建会话 → 生成 Blueprint → 迭代 → 确认。"""

    _session_id: int = 0
    _agent_id: int = 0

    def test_01_create_session(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
    ) -> None:
        """创建 Builder 会话，状态为 PENDING。"""
        resp = http.post(
            "/api/v1/builder/sessions",
            json={"prompt": "创建一个客户退货处理 Agent，需要查询订单信息和生成退货单"},
            headers=admin_headers,
        )
        assert resp.status_code == 201, f"创建会话失败: {resp.text}"
        body = resp.json()
        assert body["status"] == "pending"
        assert body["id"] > 0
        TestBuilderV2GenerateFlow._session_id = body["id"]

    def test_02_generate_blueprint_sse(self, admin_headers: dict[str, str]) -> None:
        """SSE 流式生成 Blueprint，验证流式数据结构。"""
        events = collect_sse_events(
            base_url=BASE_URL,
            path=f"/api/v1/builder/sessions/{self._session_id}/generate",
            headers=admin_headers,
            json_body={"prompt": "创建一个客户退货处理 Agent，需要查询订单信息和生成退货单"},
            timeout=90.0,
        )
        assert len(events) > 0, "未收到任何 SSE 事件"

        # 最后一个事件应标记 done=True
        last_event = events[-1]
        assert last_event.get("done") is True, f"最后事件未标记 done: {last_event}"

        # 应有 content 流式块 (中间过程)
        content_events = [e for e in events if e.get("content")]
        assert len(content_events) > 0, "未收到任何 content 流式块"

        # 应有 blueprint 数据块
        blueprint_events = [e for e in events if e.get("blueprint")]
        assert len(blueprint_events) > 0, "未收到 blueprint 数据块"

        # 验证 blueprint 结构
        blueprint = blueprint_events[-1]["blueprint"]
        assert isinstance(blueprint, dict)
        # Blueprint 应包含核心字段
        assert "persona" in blueprint or "skills" in blueprint

    def test_03_query_session_after_generate(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """生成后查询会话，状态应为 CONFIRMED 且 generated_blueprint 非空。"""
        resp = http.get(
            f"/api/v1/builder/sessions/{self._session_id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "confirmed"
        assert body.get("generated_blueprint") is not None

    def test_04_refine_blueprint_sse(self, admin_headers: dict[str, str]) -> None:
        """SSE 流式迭代优化 Blueprint (多轮 refine)。"""
        events = collect_sse_events(
            base_url=BASE_URL,
            path=f"/api/v1/builder/sessions/{self._session_id}/refine",
            headers=admin_headers,
            json_body={"message": "请增加一个处理换货的步骤，并加强语气的专业性"},
            timeout=90.0,
        )
        assert len(events) > 0, "refine 未收到任何 SSE 事件"

        last_event = events[-1]
        assert last_event.get("done") is True

        # refine 后应有更新的 blueprint
        blueprint_events = [e for e in events if e.get("blueprint")]
        assert len(blueprint_events) > 0, "refine 未返回更新后的 blueprint"

    def test_05_confirm_and_create_agent(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
        resource_tracker: ResourceTracker,
    ) -> None:
        """确认创建 Agent (auto_start_testing=false 先验证基础创建)。"""
        resp = http.post(
            f"/api/v1/builder/sessions/{self._session_id}/confirm",
            json={"auto_start_testing": False},
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"确认创建失败: {resp.text}"
        body = resp.json()
        assert body.get("created_agent_id") is not None
        TestBuilderV2GenerateFlow._agent_id = body["created_agent_id"]
        resource_tracker.track("agent", body["created_agent_id"])

    def test_06_verify_created_agent(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """验证 Builder 创建的 Agent 存在且为 DRAFT 状态。"""
        resp = http.get(f"/api/v1/agents/{self._agent_id}", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "draft"
        assert body["id"] == self._agent_id


class TestBuilderV2AutoTest:
    """Builder V2: confirm 时 auto_start_testing=true 触发自动测试。"""

    _session_id: int = 0
    _agent_id: int = 0

    def test_01_create_and_generate(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
    ) -> None:
        """创建会话并生成 Blueprint。"""
        # 创建会话
        resp = http.post(
            "/api/v1/builder/sessions",
            json={"prompt": "创建一个数据分析 Agent，能生成报表和可视化"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        TestBuilderV2AutoTest._session_id = resp.json()["id"]

        # 生成 Blueprint
        events = collect_sse_events(
            base_url=BASE_URL,
            path=f"/api/v1/builder/sessions/{self._session_id}/generate",
            headers=admin_headers,
            json_body={"prompt": "创建一个数据分析 Agent，能生成报表和可视化"},
            timeout=90.0,
        )
        assert any(e.get("done") for e in events)

    def test_02_confirm_with_auto_test(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
        resource_tracker: ResourceTracker,
    ) -> None:
        """confirm(auto_start_testing=true) 应自动创建 Agent 并触发 start-testing。"""
        resp = http.post(
            f"/api/v1/builder/sessions/{self._session_id}/confirm",
            json={"auto_start_testing": True},
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"auto_start_testing 失败: {resp.text}"
        body = resp.json()
        agent_id = body.get("created_agent_id")
        assert agent_id is not None
        TestBuilderV2AutoTest._agent_id = agent_id
        resource_tracker.track("agent", agent_id)

    def test_03_verify_agent_in_testing(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """auto_start_testing 后 Agent 应进入 TESTING 状态。"""
        # 等待异步操作完成
        for _ in range(5):
            resp = http.get(f"/api/v1/agents/{self._agent_id}", headers=admin_headers)
            if resp.status_code == 200 and resp.json()["status"] == "testing":
                break
            time.sleep(2)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "testing", f"期望 testing，实际: {body['status']}"


class TestBuilderV2Cancel:
    """Builder V2 会话取消流程。"""

    def test_cancel_pending_session(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """取消 PENDING 状态的会话。"""
        # 创建
        resp = http.post(
            "/api/v1/builder/sessions",
            json={"prompt": "临时会话 (待取消)"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        session_id = resp.json()["id"]

        # 取消
        resp = http.post(
            f"/api/v1/builder/sessions/{session_id}/cancel",
            headers=admin_headers,
        )
        assert resp.status_code == 200

        # 验证状态
        resp = http.get(f"/api/v1/builder/sessions/{session_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"


class TestBuilderAvailableResources:
    """Builder 可用资源查询端点。"""

    def test_available_tools(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """查询可用工具列表。"""
        resp = http.get("/api/v1/builder/available-tools", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_available_skills(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """查询可用 Skill 列表 (M17 新增端点)。"""
        resp = http.get("/api/v1/builder/available-skills", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
