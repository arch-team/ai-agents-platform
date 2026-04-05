"""Skill 领域实体 — 元信息 (SKILL.md 内容在文件系统中)。"""

from pydantic import ConfigDict, Field

from src.modules.skills.domain.value_objects.skill_category import SkillCategory
from src.modules.skills.domain.value_objects.skill_status import SkillStatus
from src.shared.domain.base_entity import PydanticEntity
from src.shared.domain.exceptions import ValidationError


_ARCHIVABLE = frozenset({SkillStatus.DRAFT, SkillStatus.PUBLISHED})


class Skill(PydanticEntity):
    """Skill 元信息实体。SKILL.md 内容存储在文件系统中，此实体只管理元信息。"""

    model_config = ConfigDict(validate_assignment=True)

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500, default="")
    category: SkillCategory = SkillCategory.GENERAL
    trigger_description: str = Field(max_length=500, default="")
    status: SkillStatus = SkillStatus.DRAFT
    creator_id: int
    version: int = 1
    usage_count: int = 0
    file_path: str = ""

    def publish(self) -> None:
        """发布 Skill。DRAFT -> PUBLISHED。需要 file_path 和 trigger_description 非空。"""
        self._require_status(self.status, SkillStatus.DRAFT, SkillStatus.PUBLISHED.value)
        if not self.file_path.strip():
            raise ValidationError(message="发布 Skill 需要设置 file_path", field="file_path")
        if not self.trigger_description.strip():
            raise ValidationError(message="发布 Skill 需要设置 trigger_description", field="trigger_description")
        self.status = SkillStatus.PUBLISHED
        self.touch()

    def archive(self) -> None:
        """归档 Skill。DRAFT/PUBLISHED -> ARCHIVED。"""
        self._require_status(self.status, _ARCHIVABLE, SkillStatus.ARCHIVED.value)
        self.status = SkillStatus.ARCHIVED
        self.touch()

    def increment_version(self) -> None:
        """版本号递增。"""
        self.version += 1
        self.touch()

    def increment_usage_count(self) -> None:
        """使用次数递增（被 Agent 引用时）。"""
        self.usage_count += 1

    def update_file_path(self, new_path: str) -> None:
        """更新文件系统路径。"""
        self.file_path = new_path
        self.touch()
