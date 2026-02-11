"""Template 实体单元测试。"""

import pytest
from pydantic import ValidationError

from src.modules.templates.domain.entities.template import Template
from src.modules.templates.domain.value_objects.template_category import (
    TemplateCategory,
)
from src.modules.templates.domain.value_objects.template_config import TemplateConfig
from src.modules.templates.domain.value_objects.template_status import TemplateStatus
from src.shared.domain.exceptions import InvalidStateTransitionError


def _make_config(**overrides: object) -> TemplateConfig:
    """创建默认 TemplateConfig 的辅助函数。"""
    defaults: dict[str, object] = {
        "system_prompt": "你是一个 AI 助手",
        "model_id": "anthropic.claude-v3",
    }
    defaults.update(overrides)
    return TemplateConfig(**defaults)  # type: ignore[arg-type]


@pytest.mark.unit
class TestTemplateCreation:
    """创建 Template 实体测试。"""

    def test_create_with_required_fields(self) -> None:
        config = _make_config()
        template = Template(
            name="客服助手模板",
            description="通用客服场景模板",
            category=TemplateCategory.CUSTOMER_SERVICE,
            creator_id=1,
            config=config,
        )
        assert template.name == "客服助手模板"
        assert template.description == "通用客服场景模板"
        assert template.category == TemplateCategory.CUSTOMER_SERVICE
        assert template.status == TemplateStatus.DRAFT
        assert template.creator_id == 1
        assert template.config == config
        assert template.tags == []
        assert template.usage_count == 0
        assert template.is_featured is False

    def test_create_with_all_fields(self) -> None:
        config = _make_config(tool_ids=[1, 2], knowledge_base_ids=[10])
        template = Template(
            name="数据分析模板",
            description="数据分析场景",
            category=TemplateCategory.DATA_ANALYSIS,
            creator_id=2,
            config=config,
            tags=["数据", "分析"],
            is_featured=True,
        )
        assert template.tags == ["数据", "分析"]
        assert template.is_featured is True
        assert template.config.tool_ids == [1, 2]

    def test_inherits_pydantic_entity(self) -> None:
        template = Template(
            name="测试",
            description="测试描述",
            category=TemplateCategory.GENERAL,
            creator_id=1,
            config=_make_config(),
        )
        assert template.id is None
        assert template.created_at is not None
        assert template.updated_at is not None

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            Template(
                name="",
                description="描述",
                category=TemplateCategory.GENERAL,
                creator_id=1,
                config=_make_config(),
            )

    def test_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            Template(
                name="A" * 101,
                description="描述",
                category=TemplateCategory.GENERAL,
                creator_id=1,
                config=_make_config(),
            )


@pytest.mark.unit
class TestTemplatePublish:
    """publish() 状态转换测试。"""

    @pytest.fixture
    def draft_template(self) -> Template:
        return Template(
            name="测试模板",
            description="测试描述",
            category=TemplateCategory.GENERAL,
            creator_id=1,
            config=_make_config(),
        )

    def test_publish_from_draft_succeeds(self, draft_template: Template) -> None:
        draft_template.publish()
        assert draft_template.status == TemplateStatus.PUBLISHED

    def test_publish_updates_timestamp(self, draft_template: Template) -> None:
        original = draft_template.updated_at
        draft_template.publish()
        assert draft_template.updated_at is not None
        assert original is not None
        assert draft_template.updated_at >= original

    @pytest.mark.parametrize(
        "status",
        [TemplateStatus.PUBLISHED, TemplateStatus.ARCHIVED],
    )
    def test_publish_from_invalid_state_raises(self, status: TemplateStatus) -> None:
        template = Template(
            name="测试",
            description="描述",
            category=TemplateCategory.GENERAL,
            creator_id=1,
            config=_make_config(),
        )
        object.__setattr__(template, "status", status)
        with pytest.raises(InvalidStateTransitionError, match="published"):
            template.publish()


@pytest.mark.unit
class TestTemplateArchive:
    """archive() 状态转换测试。"""

    @pytest.fixture
    def published_template(self) -> Template:
        template = Template(
            name="测试模板",
            description="测试描述",
            category=TemplateCategory.GENERAL,
            creator_id=1,
            config=_make_config(),
        )
        template.publish()
        return template

    def test_archive_from_published_succeeds(self, published_template: Template) -> None:
        published_template.archive()
        assert published_template.status == TemplateStatus.ARCHIVED

    def test_archive_updates_timestamp(self, published_template: Template) -> None:
        original = published_template.updated_at
        published_template.archive()
        assert published_template.updated_at is not None
        assert original is not None
        assert published_template.updated_at >= original

    @pytest.mark.parametrize(
        "status",
        [TemplateStatus.DRAFT, TemplateStatus.ARCHIVED],
    )
    def test_archive_from_invalid_state_raises(self, status: TemplateStatus) -> None:
        template = Template(
            name="测试",
            description="描述",
            category=TemplateCategory.GENERAL,
            creator_id=1,
            config=_make_config(),
        )
        object.__setattr__(template, "status", status)
        with pytest.raises(InvalidStateTransitionError, match="archived"):
            template.archive()


@pytest.mark.unit
class TestTemplateCanDelete:
    """can_delete() 测试 — 仅 DRAFT 可物理删除。"""

    def test_draft_can_delete(self) -> None:
        template = Template(
            name="测试",
            description="描述",
            category=TemplateCategory.GENERAL,
            creator_id=1,
            config=_make_config(),
        )
        assert template.can_delete() is True

    def test_published_cannot_delete(self) -> None:
        template = Template(
            name="测试",
            description="描述",
            category=TemplateCategory.GENERAL,
            creator_id=1,
            config=_make_config(),
        )
        template.publish()
        assert template.can_delete() is False

    def test_archived_cannot_delete(self) -> None:
        template = Template(
            name="测试",
            description="描述",
            category=TemplateCategory.GENERAL,
            creator_id=1,
            config=_make_config(),
        )
        template.publish()
        template.archive()
        assert template.can_delete() is False


@pytest.mark.unit
class TestTemplateIncrementUsage:
    """increment_usage_count() 测试。"""

    def test_increment_usage_count(self) -> None:
        template = Template(
            name="测试",
            description="描述",
            category=TemplateCategory.GENERAL,
            creator_id=1,
            config=_make_config(),
        )
        assert template.usage_count == 0
        template.increment_usage_count()
        assert template.usage_count == 1
        template.increment_usage_count()
        assert template.usage_count == 2
