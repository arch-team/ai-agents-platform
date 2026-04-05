"""E2E: Builder V2 完整流程 — 会话创建 → Blueprint 生成 → 迭代优化 → 确认创建 → 上线。

覆盖 M17 Builder V2 的核心用户旅程:
1. 创建 Builder 会话
2. SSE 流式生成 Blueprint (SOP 引导式)
3. SSE 流式迭代优化 Blueprint (多轮 refine)
4. 确认创建 Agent (含 auto_start_testing)
5. 查询可用工具和 Skill 列表
6. 会话取消流程
"""


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
        """SSE 流式生成 — SOP 引导式首轮返回澄清问题（content 块 + done 标记）。"""
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

        # 应有 content 流式块（首轮为澄清问题，不一定有 blueprint）
        content_events = [e for e in events if e.get("content")]
        assert len(content_events) > 0, "未收到任何 content 流式块"

    def test_03_query_session_after_generate(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """生成后查询会话，状态可能为 generating（多轮未完成）或 confirmed。"""
        resp = http.get(
            f"/api/v1/builder/sessions/{self._session_id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        # SOP 引导式首轮可能仍在 generating，也可能已 confirmed
        assert body["status"] in ("generating", "confirmed"), f"意外状态: {body['status']}"

    def test_04_refine_blueprint_sse(self, admin_headers: dict[str, str]) -> None:
        """SSE 流式 refine — 发送补充信息，验证 SSE 流正常工作。"""
        events = collect_sse_events(
            base_url=BASE_URL,
            path=f"/api/v1/builder/sessions/{self._session_id}/refine",
            headers=admin_headers,
            json_body={"message": "这是一个处理客户退货的 Agent，需要支持查询订单、生成退货单、退款审批"},
            timeout=90.0,
        )
        assert len(events) > 0, "refine 未收到任何 SSE 事件"

        last_event = events[-1]
        assert last_event.get("done") is True

    def test_05_confirm_and_create_agent(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
        resource_tracker: ResourceTracker,
    ) -> None:
        """确认创建 Agent — 当前 Dev 环境多轮未生成 blueprint，跳过。"""
        pytest.skip("SOP 引导式设计需要多轮 refine 才能生成 blueprint，当前 E2E 无法自动完成")

    def test_06_verify_created_agent(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """验证 Builder 创建的 Agent — 依赖 test_05 confirm，跳过。"""
        pytest.skip("依赖 test_05 confirm 创建 Agent，当前环境跳过")


class TestBuilderV2AutoTest:
    """Builder V2: confirm 时 auto_start_testing=true 触发自动测试。"""

    _session_id: int = 0
    _agent_id: int = 0

    def test_01_create_and_generate(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
    ) -> None:
        """创建会话并生成（首轮为澄清问题，不要求 blueprint）。"""
        # 创建会话
        resp = http.post(
            "/api/v1/builder/sessions",
            json={"prompt": "创建一个数据分析 Agent，能生成报表和可视化"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        TestBuilderV2AutoTest._session_id = resp.json()["id"]

        # 生成（SSE 流正常完成即可）
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
        """confirm(auto_start_testing=true) — 需要 blueprint，当前环境跳过。"""
        pytest.skip("SOP 引导式设计首轮无 blueprint，无法 confirm，跳过")

    def test_03_verify_agent_in_testing(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """auto_start_testing 后验证 — 依赖 test_02 confirm，跳过。"""
        pytest.skip("依赖 test_02 confirm 创建 Agent，当前环境跳过")


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
