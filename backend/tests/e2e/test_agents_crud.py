"""E2E: Agent CRUD 完整生命周期 — 创建→查询→更新→激活→归档 + 独立删除测试。"""

import httpx
import pytest


pytestmark = pytest.mark.e2e


class TestAgentCRUDLifecycle:
    """Agent 完整状态机: draft → active → archived。"""

    _agent_id: int | None = None

    def test_01_create_agent(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.post(
            "/api/v1/agents",
            headers=admin_headers,
            json={
                "name": "E2E 测试 Agent",
                "description": "E2E 自动化测试创建",
                "system_prompt": "你是一个测试助手。",
                "model_id": "us.anthropic.claude-haiku-4-20250514-v1:0",
            },
        )
        assert resp.status_code == 201, f"创建 Agent 失败: {resp.text}"
        body = resp.json()
        assert body["name"] == "E2E 测试 Agent"
        assert body["status"] == "draft"
        TestAgentCRUDLifecycle._agent_id = body["id"]

    def test_02_get_agent(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        agent_id = TestAgentCRUDLifecycle._agent_id
        assert agent_id is not None, "前置测试失败，无 agent_id"

        resp = http.get(f"/api/v1/agents/{agent_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == agent_id

    def test_03_list_agents(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        resp = http.get("/api/v1/agents", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert body["total"] >= 1

    def test_04_update_agent(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        agent_id = TestAgentCRUDLifecycle._agent_id
        assert agent_id is not None

        resp = http.put(
            f"/api/v1/agents/{agent_id}",
            headers=admin_headers,
            json={"description": "E2E 更新后的描述"},
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "E2E 更新后的描述"

    def test_05_activate_agent(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        agent_id = TestAgentCRUDLifecycle._agent_id
        assert agent_id is not None

        resp = http.post(f"/api/v1/agents/{agent_id}/activate", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    def test_06_archive_agent(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        agent_id = TestAgentCRUDLifecycle._agent_id
        assert agent_id is not None

        resp = http.post(f"/api/v1/agents/{agent_id}/archive", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"

    def test_07_archived_agent_cannot_be_deleted(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """仅 DRAFT 状态可删除，归档状态返回 409。"""
        agent_id = TestAgentCRUDLifecycle._agent_id
        assert agent_id is not None

        resp = http.delete(f"/api/v1/agents/{agent_id}", headers=admin_headers)
        assert resp.status_code == 409


class TestAgentDeleteDraft:
    """独立测试: DRAFT 状态的 Agent 可以直接删除。"""

    def test_create_and_delete_draft(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        # 创建
        create_resp = http.post(
            "/api/v1/agents",
            headers=admin_headers,
            json={
                "name": "E2E 待删除 Agent",
                "description": "创建后立即删除",
                "system_prompt": "test",
                "model_id": "us.anthropic.claude-haiku-4-20250514-v1:0",
            },
        )
        assert create_resp.status_code == 201
        agent_id = create_resp.json()["id"]

        # 删除 (draft 状态)
        del_resp = http.delete(f"/api/v1/agents/{agent_id}", headers=admin_headers)
        assert del_resp.status_code == 204

        # 验证已删除
        get_resp = http.get(f"/api/v1/agents/{agent_id}", headers=admin_headers)
        assert get_resp.status_code == 404
