"""模板领域实体。"""

from pydantic import Field

from src.modules.templates.domain.value_objects.template_category import (
    TemplateCategory,
)
from src.modules.templates.domain.value_objects.template_config import TemplateConfig
from src.modules.templates.domain.value_objects.template_status import TemplateStatus
from src.shared.domain.base_entity import PydanticEntity


class Template(PydanticEntity):
    """模板实体。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    category: TemplateCategory = TemplateCategory.GENERAL
    status: TemplateStatus = TemplateStatus.DRAFT
    creator_id: int
    config: TemplateConfig
    tags: list[str] = Field(default_factory=list)
    usage_count: int = 0
    is_featured: bool = False

    def publish(self) -> None:
        """发布模板。DRAFT -> PUBLISHED。"""
        self._require_status(self.status, TemplateStatus.DRAFT, TemplateStatus.PUBLISHED.value)
        self.status = TemplateStatus.PUBLISHED
        self.touch()

    def archive(self) -> None:
        """归档模板。PUBLISHED -> ARCHIVED（不可逆）。"""
        self._require_status(self.status, TemplateStatus.PUBLISHED, TemplateStatus.ARCHIVED.value)
        self.status = TemplateStatus.ARCHIVED
        self.touch()

    def can_delete(self) -> bool:
        """仅 DRAFT 状态可物理删除。"""
        return self.status == TemplateStatus.DRAFT

    def increment_usage_count(self) -> None:
        """增加使用次数。"""
        self.usage_count += 1
        self.touch()
