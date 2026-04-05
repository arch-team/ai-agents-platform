"""E2E: Skill 完整生命周期 — 创建 → 更新 → 发布 → 查询 → 详情 → 归档。

覆盖 M17 Skills 模块的 8 个 API 端点。
测试有序执行（test_01 ~ test_12），通过类变量在步骤间传递状态。
"""

import time

import httpx
import pytest

from tests.e2e.conftest import ResourceTracker


pytestmark = pytest.mark.e2e

# 时间戳后缀，确保 Skill 名称在 Dev 环境唯一
_UNIQUE_SUFFIX = str(int(time.time()))
_SKILL_NAME = f"E2E-退货处理-{_UNIQUE_SUFFIX}"


class TestSkillLifecycle:
    """Skill 完整生命周期: DRAFT → PUBLISHED → ARCHIVED。"""

    _skill_id: int = 0

    def test_01_create_skill(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
        resource_tracker: ResourceTracker,
    ) -> None:
        """创建 Skill，初始状态为 DRAFT（不发送 skill_md，避免 EFS 写入 500）。"""
        resp = http.post(
            "/api/v1/skills",
            json={
                "name": _SKILL_NAME,
                "description": "处理客户退货、退款咨询的标准操作流程",
                "category": "customer_service",
                "trigger_description": "当客户提到退货、退款、换货时使用",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201, f"创建 Skill 失败: {resp.text}"
        body = resp.json()
        assert body["name"] == _SKILL_NAME
        assert body["status"] == "draft"
        assert body["category"] == "customer_service"
        TestSkillLifecycle._skill_id = body["id"]
        resource_tracker.track("skill", body["id"])

    def test_02_get_skill_detail(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """获取 Skill 详情（纯 DB CRUD，无 skill_md 文件内容）。"""
        resp = http.get(f"/api/v1/skills/{self._skill_id}", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == self._skill_id
        assert body["name"] == _SKILL_NAME

    def test_03_list_my_skills(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """获取当前用户的 Skill 列表 (mine 端点)。"""
        resp = http.get("/api/v1/skills/mine", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        ids = [s["id"] for s in body["items"]]
        assert self._skill_id in ids

    def test_04_update_skill(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """更新 DRAFT Skill 的描述和触发条件。"""
        resp = http.put(
            f"/api/v1/skills/{self._skill_id}",
            json={
                "description": "处理客户退货、退款、换货咨询的完整 SOP",
                "trigger_description": "客户提到退货、退款、换货、质量问题时使用",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "换货" in body["description"]
        assert "质量问题" in body["trigger_description"]

    def test_05_publish_skill(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """发布 Skill: DRAFT → PUBLISHED。"""
        resp = http.post(f"/api/v1/skills/{self._skill_id}/publish", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "published"

    def test_06_update_published_skill_rejected(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """已发布的 Skill 不可更新。"""
        resp = http.put(
            f"/api/v1/skills/{self._skill_id}",
            json={"description": "尝试修改已发布 Skill"},
            headers=admin_headers,
        )
        assert resp.status_code == 409

    def test_07_list_published_skills(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """公开列表只返回已发布的 Skill。"""
        resp = http.get("/api/v1/skills", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        statuses = {s["status"] for s in body["items"]}
        # 公开列表应只包含 published
        assert statuses <= {"published"}

    def test_08_search_by_category(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """按分类筛选 Skill。"""
        resp = http.get(
            "/api/v1/skills",
            params={"category": "customer_service"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        categories = {s["category"] for s in body["items"]}
        if body["total"] > 0:
            assert categories == {"customer_service"}

    def test_09_search_by_keyword(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """按关键词搜索 Skill（使用时间戳前缀 E2E 匹配）。"""
        resp = http.get(
            "/api/v1/skills",
            params={"keyword": "E2E"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert any("E2E" in s["name"] for s in body["items"])

    def test_10_archive_skill(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """归档 Skill: PUBLISHED → ARCHIVED。"""
        resp = http.post(f"/api/v1/skills/{self._skill_id}/archive", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "archived"

    def test_11_archived_not_in_public_list(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """归档后的 Skill 不出现在公开列表中。"""
        resp = http.get("/api/v1/skills", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        ids = [s["id"] for s in body["items"]]
        assert self._skill_id not in ids

    def test_12_delete_archived_rejected(self, http: httpx.Client, admin_headers: dict[str, str]) -> None:
        """已归档的 Skill 不可删除 (只有 DRAFT 可删)。"""
        resp = http.delete(f"/api/v1/skills/{self._skill_id}", headers=admin_headers)
        assert resp.status_code == 409


class TestSkillDeleteDraft:
    """DRAFT 状态的 Skill 可以被删除。"""

    def test_create_and_delete_draft(
        self,
        http: httpx.Client,
        admin_headers: dict[str, str],
    ) -> None:
        # 创建
        resp = http.post(
            "/api/v1/skills",
            json={"name": "E2E 临时 Skill (待删除)", "category": "general"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        skill_id = resp.json()["id"]

        # 删除
        resp = http.delete(f"/api/v1/skills/{skill_id}", headers=admin_headers)
        assert resp.status_code == 204

        # 确认已删除
        resp = http.get(f"/api/v1/skills/{skill_id}", headers=admin_headers)
        assert resp.status_code == 404


class TestSkillAuth:
    """Skill 端点认证校验。"""

    def test_create_without_token(self, http: httpx.Client) -> None:
        resp = http.post("/api/v1/skills", json={"name": "无 Token"})
        assert resp.status_code == 401

    def test_list_without_token(self, http: httpx.Client) -> None:
        resp = http.get("/api/v1/skills")
        assert resp.status_code == 401
