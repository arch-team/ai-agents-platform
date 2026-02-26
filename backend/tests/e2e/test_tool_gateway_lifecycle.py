"""E2E: MCP_SERVER 工具完整 Gateway 生命周期 — 创建→提交→审批(Gateway注册)→废弃(Gateway注销)。

需要运行中的 Dev 环境:
    E2E_BASE_URL=http://ai-agents-dev-546356512.us-east-1.elb.amazonaws.com \
    uv run pytest tests/e2e/test_tool_gateway_lifecycle.py -v
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    import httpx

    from tests.e2e.conftest import ResourceTracker


pytestmark = pytest.mark.e2e

_SUFFIX = str(int(time.time()))


def _expect_gateway_sync() -> bool:
    """根据环境变量决定是否强制断言 Gateway 同步成功。"""
    import os

    return os.getenv("E2E_GATEWAY_ENABLED", "").lower() in ("1", "true", "yes")


class TestToolGatewayLifecycle:
    """MCP_SERVER 工具: 创建→提交→审批(Gateway注册)→验证持久化→列表→废弃(Gateway注销)。"""

    _tool_id: int | None = None
    _gateway_target_id: str = ""

    def test_01_create_mcp_server_tool(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
        resource_tracker: ResourceTracker,
    ) -> None:
        """创建 MCP_SERVER DRAFT 工具 → gateway_target_id 为空。"""
        resp = http.post(
            "/api/v1/tools",
            headers=admin_headers,
            json={
                "name": f"E2E Gateway Tool {_SUFFIX}",
                "description": "E2E Gateway 生命周期测试工具",
                "tool_type": "mcp_server",
                "version": "1.0.0",
                "server_url": "http://mcp-test-server.example.com:3000",
                "transport": "sse",
            },
        )
        assert resp.status_code == 201, f"创建工具失败: {resp.text}"
        body = resp.json()
        assert body["status"] == "draft"
        assert body["tool_type"] == "mcp_server"
        assert body["gateway_target_id"] == ""

        TestToolGatewayLifecycle._tool_id = body["id"]
        resource_tracker.track("tool", body["id"])

    def test_02_submit_for_review(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
    ) -> None:
        """提交审批 → 状态变为 pending_review，gateway_target_id 仍为空。"""
        tool_id = TestToolGatewayLifecycle._tool_id
        assert tool_id is not None, "前置测试失败, 无 tool_id"

        resp = http.post(
            f"/api/v1/tools/{tool_id}/submit",
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"提交审批失败: {resp.text}"
        body = resp.json()
        assert body["status"] == "pending_review"
        assert body["gateway_target_id"] == ""

    def test_03_approve_syncs_to_gateway(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
    ) -> None:
        """审批通过 → Gateway 注册，gateway_target_id 非空。"""
        tool_id = TestToolGatewayLifecycle._tool_id
        assert tool_id is not None

        resp = http.post(
            f"/api/v1/tools/{tool_id}/approve",
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"审批失败: {resp.text}"
        body = resp.json()
        assert body["status"] == "approved"
        # Gateway 注册成功后 target_id 非空 (如 Gateway 未配置则可能为空)
        TestToolGatewayLifecycle._gateway_target_id = body.get("gateway_target_id", "")
        # E2E_GATEWAY_ENABLED=true 时强制断言; 未设置时宽松放过
        if _expect_gateway_sync():
            assert body["gateway_target_id"], "Gateway 已启用但 target_id 为空"

    def test_04_target_id_persisted(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
    ) -> None:
        """GET 验证 gateway_target_id 持久化一致。"""
        tool_id = TestToolGatewayLifecycle._tool_id
        assert tool_id is not None

        resp = http.get(f"/api/v1/tools/{tool_id}", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()

        expected_target_id = TestToolGatewayLifecycle._gateway_target_id
        assert body["gateway_target_id"] == expected_target_id

    def test_05_in_approved_list(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
    ) -> None:
        """已审批工具出现在审批列表中。"""
        tool_id = TestToolGatewayLifecycle._tool_id

        # 使用大 page_size 并遍历分页，确保找到新创建的工具
        ids: list[int] = []
        page = 1
        while True:
            resp = http.get(
                "/api/v1/tools/approved",
                headers=admin_headers,
                params={"page": page, "page_size": 100},
            )
            assert resp.status_code == 200
            body = resp.json()
            ids.extend(item["id"] for item in body["items"])
            if tool_id in ids or page >= body.get("total_pages", 1):
                break
            page += 1

        assert tool_id in ids, f"tool {tool_id} 不在审批列表中 (共 {len(ids)} 个: {ids[:10]}...)"

    def test_06_deprecate_clears_gateway(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
    ) -> None:
        """废弃工具 → Gateway 注销，gateway_target_id 清空。"""
        tool_id = TestToolGatewayLifecycle._tool_id
        assert tool_id is not None

        resp = http.post(
            f"/api/v1/tools/{tool_id}/deprecate",
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"废弃失败: {resp.text}"
        body = resp.json()
        assert body["status"] == "deprecated"
        assert body["gateway_target_id"] == ""


class TestNonMcpToolNoGatewaySync:
    """非 MCP_SERVER 工具: 审批不触发 Gateway 同步。"""

    _tool_id: int | None = None

    def test_01_create_api_tool(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
        resource_tracker: ResourceTracker,
    ) -> None:
        """创建 API 类型工具。"""
        resp = http.post(
            "/api/v1/tools",
            headers=admin_headers,
            json={
                "name": f"E2E API Tool {_SUFFIX}",
                "description": "E2E API 类型测试工具",
                "tool_type": "api",
                "version": "1.0.0",
                "endpoint_url": "http://api-test.example.com/v1",
                "method": "POST",
            },
        )
        assert resp.status_code == 201, f"创建 API 工具失败: {resp.text}"
        body = resp.json()
        assert body["tool_type"] == "api"
        TestNonMcpToolNoGatewaySync._tool_id = body["id"]
        resource_tracker.track("tool", body["id"])

    def test_02_approve_no_gateway_sync(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
    ) -> None:
        """审批 API 工具 → 不触发 Gateway 同步，gateway_target_id 为空。"""
        tool_id = TestNonMcpToolNoGatewaySync._tool_id
        assert tool_id is not None, "前置测试失败, 无 tool_id"

        # 先提交审批
        resp = http.post(f"/api/v1/tools/{tool_id}/submit", headers=admin_headers)
        assert resp.status_code == 200

        # 审批
        resp = http.post(f"/api/v1/tools/{tool_id}/approve", headers=admin_headers)
        assert resp.status_code == 200, f"审批 API 工具失败: {resp.text}"
        body = resp.json()
        assert body["status"] == "approved"
        assert body["gateway_target_id"] == ""
