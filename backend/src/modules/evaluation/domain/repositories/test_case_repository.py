"""测试用例仓库接口。"""

from abc import abstractmethod

from src.modules.evaluation.domain.entities.test_case import TestCase
from src.shared.domain.repositories import IRepository


class ITestCaseRepository(IRepository[TestCase, int]):
    """测试用例仓库接口。"""

    @abstractmethod
    async def list_by_suite(
        self,
        suite_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TestCase]:
        """按测试集 ID 查询测试用例列表。"""

    @abstractmethod
    async def count_by_suite(self, suite_id: int) -> int:
        """按测试集 ID 统计测试用例数量。"""

    @abstractmethod
    async def delete_by_suite(self, suite_id: int) -> None:
        """删除测试集下所有测试用例。"""
