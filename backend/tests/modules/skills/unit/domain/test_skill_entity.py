"""Skill 领域实体测试。"""

import pytest

from src.modules.skills.domain.entities.skill import Skill
from src.modules.skills.domain.value_objects.skill_category import SkillCategory
from src.modules.skills.domain.value_objects.skill_status import SkillStatus
from src.shared.domain.exceptions import InvalidStateTransitionError


def make_skill(
    *,
    skill_id: int = 1,
    name: str = "退货处理",
    description: str = "处理客户退货咨询",
    category: SkillCategory = SkillCategory.CUSTOMER_SERVICE,
    trigger_description: str = "客户提到退货、退款时使用",
    status: SkillStatus = SkillStatus.DRAFT,
    creator_id: int = 1,
    version: int = 1,
    file_path: str = "drafts/return-processing",
) -> Skill:
    """Skill 工厂函数。"""
    skill = Skill(
        name=name,
        description=description,
        category=category,
        trigger_description=trigger_description,
        status=status,
        creator_id=creator_id,
        version=version,
        file_path=file_path,
    )
    # 模拟已持久化
    object.__setattr__(skill, "id", skill_id)
    return skill


class TestSkillCreation:
    """Skill 创建测试。"""

    def test_create_skill_with_defaults(self) -> None:
        """默认创建 DRAFT 状态。"""
        skill = Skill(name="测试技能", creator_id=1)
        assert skill.name == "测试技能"
        assert skill.status == SkillStatus.DRAFT
        assert skill.category == SkillCategory.GENERAL
        assert skill.version == 1
        assert skill.usage_count == 0
        assert skill.file_path == ""

    def test_create_skill_with_all_fields(self) -> None:
        """全字段创建。"""
        skill = make_skill()
        assert skill.name == "退货处理"
        assert skill.category == SkillCategory.CUSTOMER_SERVICE
        assert skill.trigger_description == "客户提到退货、退款时使用"
        assert skill.file_path == "drafts/return-processing"


class TestSkillStateMachine:
    """Skill 状态机测试: DRAFT → PUBLISHED → ARCHIVED。"""

    def test_publish_from_draft(self) -> None:
        """DRAFT → PUBLISHED。"""
        skill = make_skill(status=SkillStatus.DRAFT)
        skill.publish()
        assert skill.status == SkillStatus.PUBLISHED

    def test_publish_requires_draft(self) -> None:
        """只有 DRAFT 可以发布。"""
        skill = make_skill(status=SkillStatus.PUBLISHED)
        with pytest.raises(InvalidStateTransitionError):
            skill.publish()

    def test_archive_from_published(self) -> None:
        """PUBLISHED → ARCHIVED。"""
        skill = make_skill(status=SkillStatus.PUBLISHED)
        skill.archive()
        assert skill.status == SkillStatus.ARCHIVED

    def test_archive_from_draft(self) -> None:
        """DRAFT → ARCHIVED。"""
        skill = make_skill(status=SkillStatus.DRAFT)
        skill.archive()
        assert skill.status == SkillStatus.ARCHIVED

    def test_archive_from_archived_raises(self) -> None:
        """ARCHIVED 不能再归档。"""
        skill = make_skill(status=SkillStatus.ARCHIVED)
        with pytest.raises(InvalidStateTransitionError):
            skill.archive()

    def test_publish_from_archived_raises(self) -> None:
        """ARCHIVED 不能发布。"""
        skill = make_skill(status=SkillStatus.ARCHIVED)
        with pytest.raises(InvalidStateTransitionError):
            skill.publish()


class TestSkillPublishValidation:
    """发布校验测试。"""

    def test_publish_requires_file_path(self) -> None:
        """发布时必须有 file_path。"""
        skill = make_skill(file_path="")
        with pytest.raises(Exception, match="file_path"):
            skill.publish()

    def test_publish_requires_trigger_description(self) -> None:
        """发布时必须有 trigger_description (SKILL.md frontmatter 的 description)。"""
        skill = make_skill(trigger_description="")
        with pytest.raises(Exception, match="trigger"):
            skill.publish()


class TestSkillVersioning:
    """Skill 版本测试。"""

    def test_increment_version(self) -> None:
        """版本号递增。"""
        skill = make_skill(version=1)
        skill.increment_version()
        assert skill.version == 2

    def test_increment_usage_count(self) -> None:
        """使用次数递增。"""
        skill = make_skill()
        assert skill.usage_count == 0
        skill.increment_usage_count()
        assert skill.usage_count == 1


class TestSkillFilePathUpdate:
    """file_path 更新测试。"""

    def test_update_file_path_on_publish(self) -> None:
        """发布时更新 file_path。"""
        skill = make_skill(file_path="drafts/return-processing")
        skill.update_file_path("published/return-processing/v1")
        assert skill.file_path == "published/return-processing/v1"
