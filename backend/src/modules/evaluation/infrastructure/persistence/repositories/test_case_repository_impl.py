"""TestCase 仓库实现。"""

from sqlalchemy import delete

from src.modules.evaluation.domain.entities.test_case import TestCase
from src.modules.evaluation.domain.repositories.test_case_repository import ITestCaseRepository
from src.modules.evaluation.infrastructure.persistence.models.test_case_model import TestCaseModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class TestCaseRepositoryImpl(
    PydanticRepository[TestCase, TestCaseModel, int],
    ITestCaseRepository,
):
    """TestCase 仓库的 SQLAlchemy 实现。"""

    entity_class = TestCase
    model_class = TestCaseModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "input_prompt",
            "expected_output",
            "evaluation_criteria",
            "order_index",
            "updated_at",
        },
    )

    async def list_by_suite(
        self,
        suite_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TestCase]:
        """按测试集 ID 查询测试用例列表。"""
        return await self._list_where(
            TestCaseModel.suite_id == suite_id,
            offset=offset,
            limit=limit,
        )

    async def count_by_suite(self, suite_id: int) -> int:
        """按测试集 ID 统计测试用例数量。"""
        return await self._count_where(TestCaseModel.suite_id == suite_id)

    async def delete_by_suite(self, suite_id: int) -> None:
        """删除测试集下所有测试用例。"""
        stmt = delete(TestCaseModel).where(TestCaseModel.suite_id == suite_id)
        await self._session.execute(stmt)
        await self._session.flush()
