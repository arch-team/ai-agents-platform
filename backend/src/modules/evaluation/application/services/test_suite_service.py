"""TestSuite 应用服务。"""

from src.modules.evaluation.application.dto.evaluation_dto import (
    CreateTestCaseDTO,
    CreateTestSuiteDTO,
    TestCaseDTO,
    TestSuiteDTO,
    UpdateTestSuiteDTO,
)
from src.modules.evaluation.domain.entities.test_case import TestCase
from src.modules.evaluation.domain.entities.test_suite import TestSuite
from src.modules.evaluation.domain.events import (
    TestSuiteActivatedEvent,
    TestSuiteArchivedEvent,
    TestSuiteCreatedEvent,
)
from src.modules.evaluation.domain.exceptions import (
    TestCaseNotFoundError,
    TestSuiteEmptyError,
    TestSuiteNotDeletableError,
    TestSuiteNotFoundError,
)
from src.modules.evaluation.domain.repositories.test_case_repository import ITestCaseRepository
from src.modules.evaluation.domain.repositories.test_suite_repository import ITestSuiteRepository
from src.shared.application.dtos import PagedResult
from src.shared.application.ownership import check_ownership, get_or_raise
from src.shared.domain.event_bus import event_bus


class TestSuiteService:
    """TestSuite 业务服务，编排测试集 CRUD、激活、归档用例。"""

    def __init__(
        self,
        suite_repo: ITestSuiteRepository,
        case_repo: ITestCaseRepository,
    ) -> None:
        self._suite_repo = suite_repo
        self._case_repo = case_repo

    # -- 辅助方法 --

    @staticmethod
    def _to_suite_dto(suite: TestSuite) -> TestSuiteDTO:
        id_, created_at, updated_at = suite.require_persisted()
        return TestSuiteDTO(
            id=id_,
            name=suite.name,
            description=suite.description,
            agent_id=suite.agent_id,
            status=suite.status.value,
            owner_id=suite.owner_id,
            created_at=created_at,
            updated_at=updated_at,
        )

    @staticmethod
    def _to_case_dto(case: TestCase) -> TestCaseDTO:
        id_, created_at, updated_at = case.require_persisted()
        return TestCaseDTO(
            id=id_,
            suite_id=case.suite_id,
            input_prompt=case.input_prompt,
            expected_output=case.expected_output,
            evaluation_criteria=case.evaluation_criteria,
            order_index=case.order_index,
            created_at=created_at,
            updated_at=updated_at,
        )

    # -- 测试集 CRUD --

    async def create_suite(
        self,
        dto: CreateTestSuiteDTO,
        current_user_id: int,
    ) -> TestSuiteDTO:
        """创建测试集。"""
        suite = TestSuite(
            name=dto.name,
            description=dto.description,
            agent_id=dto.agent_id,
            owner_id=current_user_id,
        )
        created = await self._suite_repo.create(suite)
        if created.id is None:
            msg = "TestSuite 创建后 ID 不能为空"
            raise ValueError(msg)
        await event_bus.publish_async(
            TestSuiteCreatedEvent(suite_id=created.id, owner_id=current_user_id),
        )
        return self._to_suite_dto(created)

    async def get_suite(self, suite_id: int, current_user_id: int) -> TestSuiteDTO:
        """获取测试集详情。"""
        suite = await get_or_raise(self._suite_repo, suite_id, TestSuiteNotFoundError, suite_id)
        check_ownership(suite, current_user_id)
        return self._to_suite_dto(suite)

    async def list_suites(
        self,
        current_user_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[TestSuiteDTO]:
        """获取当前用户的测试集列表（分页）。"""
        offset = (page - 1) * page_size
        suites = await self._suite_repo.list_by_owner(current_user_id, offset=offset, limit=page_size)
        total = await self._suite_repo.count_by_owner(current_user_id)
        return PagedResult(
            items=[self._to_suite_dto(s) for s in suites],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_suite(
        self,
        suite_id: int,
        dto: UpdateTestSuiteDTO,
        current_user_id: int,
    ) -> TestSuiteDTO:
        """更新测试集。"""
        suite = await get_or_raise(self._suite_repo, suite_id, TestSuiteNotFoundError, suite_id)
        check_ownership(suite, current_user_id)
        if dto.name is not None:
            suite.name = dto.name
        if dto.description is not None:
            suite.description = dto.description
        suite.touch()
        updated = await self._suite_repo.update(suite)
        return self._to_suite_dto(updated)

    async def delete_suite(self, suite_id: int, current_user_id: int) -> None:
        """删除测试集（仅 DRAFT 状态）。"""
        suite = await get_or_raise(self._suite_repo, suite_id, TestSuiteNotFoundError, suite_id)
        check_ownership(suite, current_user_id)
        if not suite.can_delete():
            raise TestSuiteNotDeletableError(suite_id)
        await self._case_repo.delete_by_suite(suite_id)
        await self._suite_repo.delete(suite_id)

    async def activate_suite(self, suite_id: int, current_user_id: int) -> TestSuiteDTO:
        """激活测试集。"""
        suite = await get_or_raise(self._suite_repo, suite_id, TestSuiteNotFoundError, suite_id)
        check_ownership(suite, current_user_id)
        # 校验是否有测试用例
        case_count = await self._case_repo.count_by_suite(suite_id)
        if case_count == 0:
            raise TestSuiteEmptyError(suite_id)
        suite.activate()
        updated = await self._suite_repo.update(suite)
        await event_bus.publish_async(TestSuiteActivatedEvent(suite_id=suite_id))
        return self._to_suite_dto(updated)

    async def archive_suite(self, suite_id: int, current_user_id: int) -> TestSuiteDTO:
        """归档测试集。"""
        suite = await get_or_raise(self._suite_repo, suite_id, TestSuiteNotFoundError, suite_id)
        check_ownership(suite, current_user_id)
        suite.archive()
        updated = await self._suite_repo.update(suite)
        await event_bus.publish_async(TestSuiteArchivedEvent(suite_id=suite_id))
        return self._to_suite_dto(updated)

    # -- 测试用例 CRUD --

    async def add_test_case(
        self,
        suite_id: int,
        dto: CreateTestCaseDTO,
        current_user_id: int,
    ) -> TestCaseDTO:
        """添加测试用例到测试集。"""
        suite = await get_or_raise(self._suite_repo, suite_id, TestSuiteNotFoundError, suite_id)
        check_ownership(suite, current_user_id)
        case = TestCase(
            suite_id=suite_id,
            input_prompt=dto.input_prompt,
            expected_output=dto.expected_output,
            evaluation_criteria=dto.evaluation_criteria,
            order_index=dto.order_index,
        )
        created = await self._case_repo.create(case)
        return self._to_case_dto(created)

    async def list_test_cases(
        self,
        suite_id: int,
        current_user_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[TestCaseDTO]:
        """列出测试集的测试用例。"""
        suite = await get_or_raise(self._suite_repo, suite_id, TestSuiteNotFoundError, suite_id)
        check_ownership(suite, current_user_id)
        offset = (page - 1) * page_size
        cases = await self._case_repo.list_by_suite(suite_id, offset=offset, limit=page_size)
        total = await self._case_repo.count_by_suite(suite_id)
        return PagedResult(
            items=[self._to_case_dto(c) for c in cases],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def delete_test_case(
        self,
        suite_id: int,
        case_id: int,
        current_user_id: int,
    ) -> None:
        """删除测试用例。"""
        suite = await get_or_raise(self._suite_repo, suite_id, TestSuiteNotFoundError, suite_id)
        check_ownership(suite, current_user_id)
        case = await self._case_repo.get_by_id(case_id)
        if case is None or case.suite_id != suite_id:
            raise TestCaseNotFoundError(case_id)
        await self._case_repo.delete(case_id)
