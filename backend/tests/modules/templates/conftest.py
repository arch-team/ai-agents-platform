"""Templates 模块测试配置和 Fixture。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.templates.application.services.template_service import TemplateService
from src.modules.templates.domain.entities.template import Template
from src.modules.templates.domain.repositories.template_repository import (
    ITemplateRepository,
)
from src.modules.templates.domain.value_objects.template_category import (
    TemplateCategory,
)
from src.modules.templates.domain.value_objects.template_config import TemplateConfig
from src.modules.templates.domain.value_objects.template_status import TemplateStatus


def make_template(
    *,
    template_id: int = 1,
    name: str = "测试模板",
    description: str = "测试描述",
    category: TemplateCategory = TemplateCategory.GENERAL,
    status: TemplateStatus = TemplateStatus.DRAFT,
    creator_id: int = 1,
    system_prompt: str = "你是一个助手",
    model_id: str = "anthropic.claude-v3",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    tool_ids: list[int] | None = None,
    knowledge_base_ids: list[int] | None = None,
    tags: list[str] | None = None,
    usage_count: int = 0,
    is_featured: bool = False,
) -> Template:
    """创建测试用 Template 实体。"""
    config = TemplateConfig(
        system_prompt=system_prompt,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        tool_ids=tool_ids or [],
        knowledge_base_ids=knowledge_base_ids or [],
    )
    t = Template(
        name=name,
        description=description,
        category=category,
        creator_id=creator_id,
        config=config,
        tags=tags or [],
        usage_count=usage_count,
        is_featured=is_featured,
    )
    object.__setattr__(t, "id", template_id)
    if status != TemplateStatus.DRAFT:
        object.__setattr__(t, "status", status)
    return t


@pytest.fixture
def mock_template_repo() -> AsyncMock:
    """Template 仓库 Mock。"""
    return AsyncMock(spec=ITemplateRepository)


@pytest.fixture
def template_service(mock_template_repo: AsyncMock) -> TemplateService:
    """TemplateService 实例 (注入 mock 依赖)。"""
    return TemplateService(template_repo=mock_template_repo)
