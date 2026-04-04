"""SkillService 单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.skills.application.dto.skill_dto import CreateSkillDTO, UpdateSkillDTO
from src.modules.skills.application.services.skill_service import SkillService
from src.modules.skills.domain.exceptions import SkillNotFoundError
from src.modules.skills.domain.value_objects.skill_status import SkillStatus
from src.shared.domain.exceptions import ForbiddenError, InvalidStateTransitionError
from tests.modules.skills.conftest import make_skill


@pytest.mark.unit
class TestCreateSkill:
    """创建 Skill。"""

    @pytest.mark.asyncio
    async def test_create_skill_saves_draft_file(
        self,
        skill_service: SkillService,
        mock_skill_repo: AsyncMock,
        mock_file_manager: AsyncMock,
    ) -> None:
        """创建时应保存 SKILL.md 草稿并将 file_path 写入实体。"""
        mock_file_manager.save_draft.return_value = "drafts/return-processing"
        mock_skill_repo.get_by_name.return_value = None
        mock_skill_repo.create.side_effect = lambda s: _with_id(s, 1)

        dto = CreateSkillDTO(name="return-processing", description="退货处理", skill_md="# 退货流程")
        result = await skill_service.create_skill(dto, creator_id=1)

        mock_file_manager.save_draft.assert_called_once()
        assert result.file_path == "drafts/return-processing"
        assert result.status == SkillStatus.DRAFT.value

    @pytest.mark.asyncio
    async def test_create_skill_without_skill_md(
        self,
        skill_service: SkillService,
        mock_skill_repo: AsyncMock,
        mock_file_manager: AsyncMock,
    ) -> None:
        """不提供 skill_md 时不应调用 file_manager。"""
        mock_skill_repo.get_by_name.return_value = None
        mock_skill_repo.create.side_effect = lambda s: _with_id(s, 1)

        dto = CreateSkillDTO(name="test-skill")
        result = await skill_service.create_skill(dto, creator_id=1)

        mock_file_manager.save_draft.assert_not_called()
        assert result.file_path == ""


@pytest.mark.unit
class TestGetSkill:
    """获取 Skill。"""

    @pytest.mark.asyncio
    async def test_get_skill_returns_dto(self, skill_service: SkillService, mock_skill_repo: AsyncMock) -> None:
        mock_skill_repo.get_by_id.return_value = make_skill()
        result = await skill_service.get_skill(1)
        assert result.id == 1
        assert result.name == "退货处理"

    @pytest.mark.asyncio
    async def test_get_nonexistent_skill_raises(self, skill_service: SkillService, mock_skill_repo: AsyncMock) -> None:
        mock_skill_repo.get_by_id.return_value = None
        with pytest.raises(SkillNotFoundError):
            await skill_service.get_skill(999)


@pytest.mark.unit
class TestUpdateSkill:
    """更新 Skill。"""

    @pytest.mark.asyncio
    async def test_update_draft_skill(
        self,
        skill_service: SkillService,
        mock_skill_repo: AsyncMock,
        mock_file_manager: AsyncMock,
    ) -> None:
        """更新 DRAFT Skill 应更新文件。"""
        skill = make_skill(status=SkillStatus.DRAFT)
        mock_skill_repo.get_by_id.return_value = skill
        mock_skill_repo.update.side_effect = lambda s: s

        dto = UpdateSkillDTO(description="更新后的描述", skill_md="# 新流程")
        result = await skill_service.update_skill(1, dto, operator_id=1)

        assert result.description == "更新后的描述"
        mock_file_manager.update_draft.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_published_skill_raises(
        self,
        skill_service: SkillService,
        mock_skill_repo: AsyncMock,
    ) -> None:
        """已发布的 Skill 不能直接更新。"""
        skill = make_skill(status=SkillStatus.PUBLISHED)
        mock_skill_repo.get_by_id.return_value = skill

        dto = UpdateSkillDTO(description="尝试修改")
        with pytest.raises(InvalidStateTransitionError):
            await skill_service.update_skill(1, dto, operator_id=1)

    @pytest.mark.asyncio
    async def test_update_others_skill_raises(
        self,
        skill_service: SkillService,
        mock_skill_repo: AsyncMock,
    ) -> None:
        """非创建者不能更新 Skill。"""
        skill = make_skill(creator_id=1)
        mock_skill_repo.get_by_id.return_value = skill

        dto = UpdateSkillDTO(description="尝试修改")
        with pytest.raises(ForbiddenError):
            await skill_service.update_skill(1, dto, operator_id=999)


@pytest.mark.unit
class TestDeleteSkill:
    """删除 Skill。"""

    @pytest.mark.asyncio
    async def test_delete_draft_skill(
        self,
        skill_service: SkillService,
        mock_skill_repo: AsyncMock,
        mock_file_manager: AsyncMock,
    ) -> None:
        """删除 DRAFT Skill 应同时清理文件。"""
        skill = make_skill(status=SkillStatus.DRAFT, file_path="drafts/test")
        mock_skill_repo.get_by_id.return_value = skill

        await skill_service.delete_skill(1, operator_id=1)

        mock_skill_repo.delete.assert_called_once_with(1)
        mock_file_manager.delete_draft.assert_called_once_with("drafts/test")

    @pytest.mark.asyncio
    async def test_delete_published_skill_raises(
        self,
        skill_service: SkillService,
        mock_skill_repo: AsyncMock,
    ) -> None:
        """已发布的 Skill 不能直接删除。"""
        skill = make_skill(status=SkillStatus.PUBLISHED)
        mock_skill_repo.get_by_id.return_value = skill

        with pytest.raises(InvalidStateTransitionError):
            await skill_service.delete_skill(1, operator_id=1)


@pytest.mark.unit
class TestPublishSkill:
    """发布 Skill。"""

    @pytest.mark.asyncio
    async def test_publish_skill_copies_to_published(
        self,
        skill_service: SkillService,
        mock_skill_repo: AsyncMock,
        mock_file_manager: AsyncMock,
    ) -> None:
        """发布应调用 file_manager.publish 并更新 file_path。"""
        skill = make_skill(status=SkillStatus.DRAFT, file_path="drafts/return-processing")
        mock_skill_repo.get_by_id.return_value = skill
        mock_file_manager.publish.return_value = "published/return-processing/v1"
        mock_skill_repo.update.side_effect = lambda s: s

        result = await skill_service.publish_skill(1, operator_id=1)

        mock_file_manager.publish.assert_called_once_with("drafts/return-processing", "退货处理", version=1)
        assert result.status == SkillStatus.PUBLISHED.value
        assert result.file_path == "published/return-processing/v1"


@pytest.mark.unit
class TestArchiveSkill:
    """归档 Skill。"""

    @pytest.mark.asyncio
    async def test_archive_published_skill(
        self,
        skill_service: SkillService,
        mock_skill_repo: AsyncMock,
    ) -> None:
        skill = make_skill(status=SkillStatus.PUBLISHED)
        mock_skill_repo.get_by_id.return_value = skill
        mock_skill_repo.update.side_effect = lambda s: s

        result = await skill_service.archive_skill(1, operator_id=1)
        assert result.status == SkillStatus.ARCHIVED.value


@pytest.mark.unit
class TestListSkills:
    """列表查询。"""

    @pytest.mark.asyncio
    async def test_list_published_skills(self, skill_service: SkillService, mock_skill_repo: AsyncMock) -> None:
        mock_skill_repo.list_published.return_value = [make_skill(status=SkillStatus.PUBLISHED)]
        mock_skill_repo.count.return_value = 1

        result = await skill_service.list_published_skills()
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_list_my_skills(self, skill_service: SkillService, mock_skill_repo: AsyncMock) -> None:
        mock_skill_repo.list_by_creator.return_value = [make_skill()]
        mock_skill_repo.count_by_creator.return_value = 1

        result = await skill_service.list_my_skills(creator_id=1)
        assert len(result.items) == 1


# ── 辅助函数 ──


def _with_id(skill: object, skill_id: int) -> object:
    """模拟持久化后设置 ID。"""
    object.__setattr__(skill, "id", skill_id)
    return skill
