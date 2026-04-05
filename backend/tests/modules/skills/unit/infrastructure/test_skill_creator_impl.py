"""SkillCreatorImpl 单元测试 — 跨模块 Skill 创建适配器。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.skills.application.dto.skill_dto import SkillDTO
from src.modules.skills.application.services.skill_service import SkillService
from src.modules.skills.infrastructure.services.skill_creator_impl import SkillCreatorImpl
from src.shared.domain.interfaces.skill_creator import CreateSkillRequest


def _make_skill_dto(*, skill_id: int = 10, name: str = "test-skill", file_path: str = "drafts/test-skill") -> SkillDTO:
    from datetime import datetime

    return SkillDTO(
        id=skill_id,
        name=name,
        description="desc",
        category="general",
        trigger_description="trigger",
        status="draft",
        creator_id=1,
        version=1,
        usage_count=0,
        file_path=file_path,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.mark.unit
class TestSkillCreatorImpl:
    """SkillCreatorImpl 测试。"""

    @pytest.fixture
    def mock_skill_service(self) -> AsyncMock:
        return AsyncMock(spec=SkillService)

    @pytest.fixture
    def skill_creator(self, mock_skill_service: AsyncMock) -> SkillCreatorImpl:
        return SkillCreatorImpl(skill_service=mock_skill_service)

    @pytest.mark.asyncio
    async def test_create_skill_delegates_to_service(
        self,
        skill_creator: SkillCreatorImpl,
        mock_skill_service: AsyncMock,
    ) -> None:
        mock_skill_service.create_skill.return_value = _make_skill_dto()

        request = CreateSkillRequest(
            name="return-processing",
            description="处理退货",
            skill_md="---\nname: return-processing\n---\n",
            category="售后",
            trigger_description="客户提到退货",
        )
        result = await skill_creator.create_skill(request, creator_id=100)

        assert result.id == 10
        assert result.name == "test-skill"
        assert result.file_path == "drafts/test-skill"
        mock_skill_service.create_skill.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_skill_delegates_to_service(
        self,
        skill_creator: SkillCreatorImpl,
        mock_skill_service: AsyncMock,
    ) -> None:
        published_dto = _make_skill_dto(file_path="published/test-skill/v1")
        published_dto.status = "published"
        published_dto.version = 1
        mock_skill_service.publish_skill.return_value = published_dto

        result = await skill_creator.publish_skill(skill_id=10, operator_id=100)

        assert result.id == 10
        assert result.file_path == "published/test-skill/v1"
        mock_skill_service.publish_skill.assert_called_once_with(10, 100)
