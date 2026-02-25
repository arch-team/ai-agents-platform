"""TemplateService 单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.templates.application.dto.template_dto import (
    CreateTemplateDTO,
    UpdateTemplateDTO,
)
from src.modules.templates.application.services.template_service import TemplateService
from src.modules.templates.domain.exceptions import (
    DuplicateTemplateNameError,
    TemplateNotFoundError,
)
from src.modules.templates.domain.value_objects.template_status import TemplateStatus
from src.shared.domain.exceptions import DomainError, InvalidStateTransitionError
from tests.modules.templates.conftest import make_template


def _make_service(
    repo: AsyncMock | None = None,
) -> tuple[TemplateService, AsyncMock]:
    """创建 TemplateService 及其 Mock 依赖。"""
    mock_repo = repo or AsyncMock()
    return TemplateService(template_repo=mock_repo), mock_repo


@pytest.mark.unit
class TestCreateTemplate:
    """create_template 测试。"""

    @pytest.mark.asyncio
    async def test_create_template_succeeds(self) -> None:
        service, mock_repo = _make_service()
        mock_repo.get_by_name.return_value = None
        created = make_template(template_id=1)
        mock_repo.create.return_value = created

        dto = CreateTemplateDTO(
            name="测试模板",
            description="测试描述",
            category="general",
            system_prompt="你是助手",
            model_id="model-1",
            tags=["测试"],
        )
        result = await service.create_template(dto, current_user_id=10)

        assert result.id == 1
        assert result.name == "测试模板"
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_template_duplicate_name_raises(self) -> None:
        service, mock_repo = _make_service()
        existing = make_template(name="已存在")
        mock_repo.get_by_name.return_value = existing

        dto = CreateTemplateDTO(
            name="已存在",
            description="描述",
            category="general",
            system_prompt="提示",
            model_id="model-1",
        )
        with pytest.raises(DuplicateTemplateNameError):
            await service.create_template(dto, current_user_id=10)


@pytest.mark.unit
class TestGetTemplate:
    """get_template 测试。"""

    @pytest.mark.asyncio
    async def test_get_template_succeeds(self) -> None:
        service, mock_repo = _make_service()
        template = make_template()
        mock_repo.get_by_id.return_value = template

        result = await service.get_template(1)
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_template_not_found_raises(self) -> None:
        service, mock_repo = _make_service()
        mock_repo.get_by_id.return_value = None

        with pytest.raises(TemplateNotFoundError):
            await service.get_template(999)


@pytest.mark.unit
class TestUpdateTemplate:
    """update_template 测试。"""

    @pytest.mark.asyncio
    async def test_update_template_succeeds(self) -> None:
        service, mock_repo = _make_service()
        template = make_template(creator_id=10)
        mock_repo.get_by_id.return_value = template
        mock_repo.get_by_name.return_value = None
        mock_repo.update.return_value = template

        dto = UpdateTemplateDTO(name="新名称")
        result = await service.update_template(1, dto, current_user_id=10)
        assert result.name == "新名称"

    @pytest.mark.asyncio
    async def test_update_non_draft_raises(self) -> None:
        service, mock_repo = _make_service()
        template = make_template(creator_id=10, status=TemplateStatus.PUBLISHED)
        mock_repo.get_by_id.return_value = template

        dto = UpdateTemplateDTO(name="新名称")
        with pytest.raises(InvalidStateTransitionError):
            await service.update_template(1, dto, current_user_id=10)

    @pytest.mark.asyncio
    async def test_update_other_user_template_raises(self) -> None:
        service, mock_repo = _make_service()
        template = make_template(creator_id=10)
        mock_repo.get_by_id.return_value = template

        dto = UpdateTemplateDTO(name="新名称")
        with pytest.raises(DomainError, match="无权"):
            await service.update_template(1, dto, current_user_id=999)


@pytest.mark.unit
class TestDeleteTemplate:
    """delete_template 测试。"""

    @pytest.mark.asyncio
    async def test_delete_draft_template_succeeds(self) -> None:
        service, mock_repo = _make_service()
        template = make_template(creator_id=10)
        mock_repo.get_by_id.return_value = template

        await service.delete_template(1, current_user_id=10)
        mock_repo.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_published_template_raises(self) -> None:
        service, mock_repo = _make_service()
        template = make_template(creator_id=10, status=TemplateStatus.PUBLISHED)
        mock_repo.get_by_id.return_value = template

        with pytest.raises(DomainError, match="仅 DRAFT"):
            await service.delete_template(1, current_user_id=10)


@pytest.mark.unit
class TestPublishTemplate:
    """publish_template 测试。"""

    @pytest.mark.asyncio
    async def test_publish_template_succeeds(self) -> None:
        service, mock_repo = _make_service()
        template = make_template(creator_id=10)
        mock_repo.get_by_id.return_value = template
        mock_repo.update.return_value = template

        result = await service.publish_template(1, current_user_id=10)
        assert result.status == "published"

    @pytest.mark.asyncio
    async def test_publish_already_published_raises(self) -> None:
        service, mock_repo = _make_service()
        template = make_template(creator_id=10, status=TemplateStatus.PUBLISHED)
        mock_repo.get_by_id.return_value = template

        with pytest.raises(InvalidStateTransitionError):
            await service.publish_template(1, current_user_id=10)


@pytest.mark.unit
class TestArchiveTemplate:
    """archive_template 测试。"""

    @pytest.mark.asyncio
    async def test_archive_template_succeeds(self) -> None:
        service, mock_repo = _make_service()
        template = make_template(creator_id=10, status=TemplateStatus.PUBLISHED)
        mock_repo.get_by_id.return_value = template
        mock_repo.update.return_value = template

        result = await service.archive_template(1, current_user_id=10)
        assert result.status == "archived"


@pytest.mark.unit
class TestListTemplates:
    """list_templates 测试。"""

    @pytest.mark.asyncio
    async def test_list_templates_succeeds(self) -> None:
        service, mock_repo = _make_service()
        templates = [make_template(template_id=i) for i in range(3)]
        mock_repo.search_with_total.return_value = (templates, 3)

        result = await service.list_templates(page=1, page_size=20)
        assert result.total == 3
        assert len(result.items) == 3
        mock_repo.search_with_total.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_my_templates_succeeds(self) -> None:
        service, mock_repo = _make_service()
        templates = [make_template(template_id=1, creator_id=10)]
        mock_repo.list_by_creator.return_value = templates
        mock_repo.count_by_creator.return_value = 1

        result = await service.list_my_templates(current_user_id=10, page=1, page_size=20)
        assert result.total == 1
        mock_repo.count_by_creator.assert_called_once_with(10)
