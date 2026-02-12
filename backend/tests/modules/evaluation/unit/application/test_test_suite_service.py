"""TestSuiteService 应用服务单元测试。"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.evaluation.application.dto.evaluation_dto import (
    CreateTestCaseDTO,
    CreateTestSuiteDTO,
    TestCaseDTO,
    TestSuiteDTO,
    UpdateTestSuiteDTO,
)
from src.modules.evaluation.application.services.test_suite_service import TestSuiteService
from src.modules.evaluation.domain.exceptions import (
    TestCaseNotFoundError,
    TestSuiteEmptyError,
    TestSuiteNotDeletableError,
    TestSuiteNotFoundError,
)
from src.modules.evaluation.domain.value_objects.test_suite_status import TestSuiteStatus
from src.shared.domain.exceptions import ForbiddenError

from tests.modules.evaluation.conftest import make_test_case, make_test_suite


@pytest.mark.unit
class TestCreateSuite:
    """create_suite 测试。"""

    @pytest.mark.asyncio
    async def test_creates_suite_and_returns_dto(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.create.return_value = make_test_suite()
        dto = CreateTestSuiteDTO(name="测试集A", description="描述", agent_id=10)

        with patch("src.modules.evaluation.application.services.test_suite_service.event_bus") as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await suite_service.create_suite(dto, current_user_id=100)

        assert isinstance(result, TestSuiteDTO)
        assert result.name == "测试集A"
        mock_suite_repo.create.assert_called_once()


@pytest.mark.unit
class TestGetSuite:
    """get_suite 测试。"""

    @pytest.mark.asyncio
    async def test_returns_suite_dto(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite()
        result = await suite_service.get_suite(1, current_user_id=100)
        assert isinstance(result, TestSuiteDTO)
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_not_found_raises(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = None
        with pytest.raises(TestSuiteNotFoundError):
            await suite_service.get_suite(999, current_user_id=100)

    @pytest.mark.asyncio
    async def test_wrong_owner_raises(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite(owner_id=200)
        with pytest.raises(ForbiddenError):
            await suite_service.get_suite(1, current_user_id=100)


@pytest.mark.unit
class TestUpdateSuite:
    """update_suite 测试。"""

    @pytest.mark.asyncio
    async def test_updates_name(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
    ) -> None:
        suite = make_test_suite()
        mock_suite_repo.get_by_id.return_value = suite
        mock_suite_repo.update.return_value = make_test_suite(name="新名称")

        result = await suite_service.update_suite(
            1, UpdateTestSuiteDTO(name="新名称"), current_user_id=100,
        )
        assert result.name == "新名称"
        mock_suite_repo.update.assert_called_once()


@pytest.mark.unit
class TestDeleteSuite:
    """delete_suite 测试。"""

    @pytest.mark.asyncio
    async def test_deletes_draft_suite(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
        mock_case_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite()
        await suite_service.delete_suite(1, current_user_id=100)
        mock_case_repo.delete_by_suite.assert_called_once_with(1)
        mock_suite_repo.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_active_suite_raises(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite(status=TestSuiteStatus.ACTIVE)
        with pytest.raises(TestSuiteNotDeletableError):
            await suite_service.delete_suite(1, current_user_id=100)


@pytest.mark.unit
class TestActivateSuite:
    """activate_suite 测试。"""

    @pytest.mark.asyncio
    async def test_activates_suite_with_cases(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
        mock_case_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite()
        mock_case_repo.count_by_suite.return_value = 3
        mock_suite_repo.update.return_value = make_test_suite(status=TestSuiteStatus.ACTIVE)

        with patch("src.modules.evaluation.application.services.test_suite_service.event_bus") as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await suite_service.activate_suite(1, current_user_id=100)

        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_activate_empty_suite_raises(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
        mock_case_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite()
        mock_case_repo.count_by_suite.return_value = 0
        with pytest.raises(TestSuiteEmptyError):
            await suite_service.activate_suite(1, current_user_id=100)


@pytest.mark.unit
class TestArchiveSuite:
    """archive_suite 测试。"""

    @pytest.mark.asyncio
    async def test_archives_suite(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite()
        mock_suite_repo.update.return_value = make_test_suite(status=TestSuiteStatus.ARCHIVED)

        with patch("src.modules.evaluation.application.services.test_suite_service.event_bus") as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await suite_service.archive_suite(1, current_user_id=100)

        assert result.status == "archived"


@pytest.mark.unit
class TestAddTestCase:
    """add_test_case 测试。"""

    @pytest.mark.asyncio
    async def test_adds_case(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
        mock_case_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite()
        mock_case_repo.create.return_value = make_test_case()
        dto = CreateTestCaseDTO(input_prompt="问题", expected_output="答案")
        result = await suite_service.add_test_case(1, dto, current_user_id=100)
        assert isinstance(result, TestCaseDTO)
        assert result.input_prompt == "请回答以下问题"


@pytest.mark.unit
class TestDeleteTestCase:
    """delete_test_case 测试。"""

    @pytest.mark.asyncio
    async def test_deletes_case(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
        mock_case_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite()
        mock_case_repo.get_by_id.return_value = make_test_case(suite_id=1)
        await suite_service.delete_test_case(1, 1, current_user_id=100)
        mock_case_repo.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_case_wrong_suite_raises(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
        mock_case_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite()
        mock_case_repo.get_by_id.return_value = make_test_case(suite_id=99)
        with pytest.raises(TestCaseNotFoundError):
            await suite_service.delete_test_case(1, 1, current_user_id=100)

    @pytest.mark.asyncio
    async def test_delete_case_not_found_raises(
        self,
        suite_service: TestSuiteService,
        mock_suite_repo: AsyncMock,
        mock_case_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite()
        mock_case_repo.get_by_id.return_value = None
        with pytest.raises(TestCaseNotFoundError):
            await suite_service.delete_test_case(1, 999, current_user_id=100)
