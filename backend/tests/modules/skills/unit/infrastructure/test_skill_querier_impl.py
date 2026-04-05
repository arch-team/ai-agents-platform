"""SkillQuerierImpl 单元测试 — 跨模块查询接口的实现。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.skills.domain.repositories.skill_repository import ISkillRepository
from src.modules.skills.domain.value_objects.skill_status import SkillStatus
from src.modules.skills.infrastructure.services.skill_querier_impl import SkillQuerierImpl
from tests.modules.skills.conftest import make_skill


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=ISkillRepository)


@pytest.fixture
def querier(mock_repo: AsyncMock) -> SkillQuerierImpl:
    return SkillQuerierImpl(skill_repository=mock_repo)


@pytest.mark.unit
class TestGetPublishedSkills:
    """get_published_skills 测试 — 批量按 ID 查询已发布 Skill。"""

    @pytest.mark.asyncio
    async def test_returns_published_skills_only(self, querier: SkillQuerierImpl, mock_repo: AsyncMock) -> None:
        published = make_skill(skill_id=1, name="已发布", status=SkillStatus.PUBLISHED, file_path="published/s1/v1")
        draft = make_skill(skill_id=2, name="草稿", status=SkillStatus.DRAFT, file_path="drafts/s2")
        mock_repo.get_by_ids.return_value = [published, draft]

        result = await querier.get_published_skills([1, 2])

        assert len(result) == 1
        assert result[0].name == "已发布"
        mock_repo.get_by_ids.assert_awaited_once_with([1, 2])

    @pytest.mark.asyncio
    async def test_empty_ids_returns_empty(self, querier: SkillQuerierImpl, mock_repo: AsyncMock) -> None:
        result = await querier.get_published_skills([])

        assert result == []
        mock_repo.get_by_ids.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_maps_skill_info_fields(self, querier: SkillQuerierImpl, mock_repo: AsyncMock) -> None:
        skill = make_skill(
            skill_id=5,
            name="测试 Skill",
            description="描述",
            trigger_description="触发条件",
            version=3,
            file_path="published/test/v3",
            status=SkillStatus.PUBLISHED,
        )
        mock_repo.get_by_ids.return_value = [skill]

        result = await querier.get_published_skills([5])

        assert len(result) == 1
        info = result[0]
        assert info.id == 5
        assert info.name == "测试 Skill"
        assert info.description == "描述"
        assert info.trigger_description == "触发条件"
        assert info.version == 3
        assert info.file_path == "published/test/v3"


@pytest.mark.unit
class TestListPublishedSkills:
    """list_published_skills 测试 — 按分类或全量列出已发布 Skill。"""

    @pytest.mark.asyncio
    async def test_list_without_category(self, querier: SkillQuerierImpl, mock_repo: AsyncMock) -> None:
        skill = make_skill(skill_id=1, status=SkillStatus.PUBLISHED)
        mock_repo.list_published.return_value = [skill]

        result = await querier.list_published_skills(limit=10)

        assert len(result) == 1
        assert result[0].name == skill.name
        mock_repo.list_published.assert_awaited_once_with(limit=10)

    @pytest.mark.asyncio
    async def test_list_with_category(self, querier: SkillQuerierImpl, mock_repo: AsyncMock) -> None:
        from src.modules.skills.domain.value_objects.skill_category import SkillCategory

        skill = make_skill(skill_id=1, status=SkillStatus.PUBLISHED, category=SkillCategory.CUSTOMER_SERVICE)
        mock_repo.list_by_category.return_value = [skill]

        result = await querier.list_published_skills(category="customer_service", limit=5)

        assert len(result) == 1
        mock_repo.list_by_category.assert_awaited_once_with(SkillCategory.CUSTOMER_SERVICE, limit=5)
